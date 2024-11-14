import time

def check_internet_connection(self) -> bool:
    """Check internet connectivity with multiple fallback hosts"""
    test_hosts = [
        "8.8.8.8",      # Google DNS
        "1.1.1.1",      # Cloudflare DNS
        "208.67.222.222" # OpenDNS
    ]
    
    for host in test_hosts:
        try:
            subprocess.run(
                ["ping", "-c", "1", "-W", "2", host],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            if self.audio_manager:
                self.audio_manager.play_sound('success.wav')
            return True
        except subprocess.CalledProcessError:
            continue
    
    if self.audio_manager:
        self.audio_manager.play_sound('error.wav')
    
    self.logger.error("Failed to connect to any test hosts")
    return False 

def check_and_setup_network(self) -> bool:
    """Check and setup network connection with retry mechanism"""
    retry_count = 0
    max_retries = 10
    delay = 5
    
    while True:  # Changed to infinite loop with explicit breaks
        # Check retry count first
        if retry_count >= max_retries:
            self.logger.error("Max retries reached")
            return False
            
        saved_networks = self.wifi_manager.get_saved_networks()
        if not saved_networks:
            self.logger.error("No saved networks found")
            return False
        
        # Try network setup
        if (self.wifi_manager.connect_to_network(saved_networks[0], None) and 
            self.wifi_manager.configure_dns() and 
            self.wifi_manager.check_dns_resolution()):
            
            self.logger.info("Network setup complete with DNS")
            
            # Check internet connection
            if self.check_internet_connection():
                self.logger.info("Internet connection verified")
                return True
                
            self.logger.warning("Internet check failed, will retry")
        else:
            self.logger.warning("Network setup failed, will retry")
        
        # Apply delay and increment retry count
        delay = 60 if retry_count >= 5 else 5
        self.logger.warning(f"Retrying in {delay} seconds (attempt {retry_count + 1}/{max_retries})")
        time.sleep(delay)
        retry_count += 1 