import subprocess
import logging
import time
import os
from typing import Dict, Optional

class APManager:
    def __init__(self):
        self.logger = logging.getLogger('network')
        self.ap_ssid = "InternetRadio"
        self.ap_password = "raspberry"
        self.hostapd_conf_path = "/etc/hostapd/hostapd.conf"
        self.dnsmasq_conf_path = "/etc/dnsmasq.conf"
    
    def setup_ap_mode(self) -> bool:
        """Set up Access Point mode"""
        try:
            self.logger.info("Starting AP mode setup...")
            
            # Stop potentially interfering services
            self._stop_network_services()
            
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
        self.logger.info("Stopping network services...")
        services = ["NetworkManager", "wpa_supplicant"]
        
        for service in services:
            subprocess.run(["sudo", "systemctl", "stop", service])
            time.sleep(1)
    
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