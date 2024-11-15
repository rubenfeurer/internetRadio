import subprocess
import logging
import time
import os
from typing import Dict, Optional

class APManager:
    def __init__(self, ssid: str = "InternetRadio", password: str = "password"):
        self.logger = logging.getLogger('network')
        self.ssid = ssid
        self.password = password
        self.hostapd_conf_path = "/etc/hostapd/hostapd.conf"
        self.dnsmasq_conf_path = "/etc/dnsmasq.conf"
    
    def setup_ap_mode(self) -> bool:
        """Set up Access Point mode"""
        try:
            # Check NetworkManager status first
            nm_active = self._check_networkmanager_status()
            if nm_active:
                self.logger.info("Stopping NetworkManager...")
                self._stop_network_services()
                time.sleep(2)  # Give it time to stop
            
            self.logger.info("Starting AP mode setup...")
            
            # Configure network interface
            if not self._configure_interface():
                return False
            
            # Configure and start services
            if not self._configure_and_start_services():
                return False
            
            self.logger.info("AP mode setup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up AP mode: {str(e)}")
            return False
    
    def is_ap_mode_active(self) -> bool:
        """Check if AP mode is currently active"""
        try:
            # Check hostapd status
            hostapd_status = subprocess.run(
                ["sudo", "systemctl", "is-active", "hostapd"],
                capture_output=True,
                text=True
            )
            
            # Check dnsmasq status
            dnsmasq_status = subprocess.run(
                ["sudo", "systemctl", "is-active", "dnsmasq"],
                capture_output=True,
                text=True
            )
            
            return (hostapd_status.stdout.strip() == "active" and 
                    dnsmasq_status.stdout.strip() == "active")
                    
        except Exception as e:
            self.logger.error(f"Error checking AP mode status: {str(e)}")
            return False
    
    def _stop_network_services(self) -> None:
        """Stop network services that might interfere with AP mode"""
        try:
            self.logger.info("Stopping network services...")
            services = ["NetworkManager", "wpa_supplicant"]
            
            for service in services:
                try:
                    # Check if service is running first
                    status = subprocess.run(
                        ["systemctl", "is-active", service],
                        capture_output=True,
                        text=True
                    )
                    if status.stdout.strip() == "active":
                        subprocess.run(["sudo", "systemctl", "stop", service], check=True)
                        time.sleep(1)
                except subprocess.CalledProcessError:
                    self.logger.debug(f"{service} already stopped")
                except Exception as e:
                    self.logger.warning(f"Error handling {service}: {e}")
        except Exception as e:
            self.logger.error(f"Error stopping network services: {e}")
    
    def _configure_interface(self) -> bool:
        """Configure network interface for AP mode"""
        try:
            self.logger.info("Configuring network interface...")
            
            # Unblock wifi and bring up interface
            subprocess.run(["sudo", "rfkill", "unblock", "wifi"])
            subprocess.run(["sudo", "ifconfig", "wlan0", "down"])
            time.sleep(1)
            
            # Set static IP
            subprocess.run([
                "sudo", "ifconfig", "wlan0",
                "192.168.4.1", "netmask", "255.255.255.0"
            ])
            time.sleep(1)
            
            subprocess.run(["sudo", "ifconfig", "wlan0", "up"])
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring interface: {str(e)}")
            return False
    
    def _configure_and_start_services(self) -> bool:
        """Configure and start required services"""
        try:
            self.logger.info("Configuring and starting services...")
            
            # Start dnsmasq
            subprocess.run(["sudo", "systemctl", "start", "dnsmasq"])
            time.sleep(2)
            
            # Start hostapd
            subprocess.run(["sudo", "systemctl", "start", "hostapd"])
            time.sleep(2)
            
            # Verify services are running
            if not self.is_ap_mode_active():
                self.logger.error("Failed to start AP mode services")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting services: {str(e)}")
            return False
    
    def start(self, ssid: str, password: str) -> bool:
        """Start AP mode with given credentials"""
        self.ssid = ssid
        self.password = password
        return self.setup_ap_mode()
    
    def stop(self) -> bool:
        """Stop AP mode"""
        try:
            subprocess.run(["sudo", "systemctl", "stop", "hostapd"])
            subprocess.run(["sudo", "systemctl", "stop", "dnsmasq"])
            return True
        except Exception as e:
            self.logger.error(f"Error stopping AP mode: {str(e)}")
            return False
    
    def is_active(self) -> bool:
        """Check if AP mode is active"""
        return self.is_ap_mode_active()
    
    def get_ip(self) -> str:
        """Get AP IP address"""
        return "192.168.4.1"
    
    def cleanup(self) -> None:
        """Cleanup AP resources"""
        try:
            self.stop()
            # Don't try to start NetworkManager here, let NetworkController handle it
        except Exception as e:
            self.logger.error(f"Error during AP cleanup: {e}")
    
    def initialize(self) -> bool:
        """Initialize AP Manager"""
        try:
            self.logger.info("Initializing AP Manager...")
            
            # Check if hostapd is installed
            subprocess.run(["which", "hostapd"], check=True, capture_output=True)
            
            # Check if dnsmasq is installed
            subprocess.run(["which", "dnsmasq"], check=True, capture_output=True)
            
            # Check configuration files
            if not os.path.exists(self.hostapd_conf_path):
                self.logger.error("hostapd configuration file missing")
                return False
            
            if not os.path.exists(self.dnsmasq_conf_path):
                self.logger.error("dnsmasq configuration file missing")
                return False
            
            return True
            
        except FileNotFoundError as e:
            self.logger.error(f"Required dependency missing: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error initializing AP Manager: {str(e)}")
            return False
    
    def _check_networkmanager_status(self) -> bool:
        """Check if NetworkManager is running"""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "NetworkManager"],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() == "active"
        except Exception:
            return False