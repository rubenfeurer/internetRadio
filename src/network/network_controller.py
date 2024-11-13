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
            return True
        except subprocess.CalledProcessError:
            continue
    
    self.logger.error("Failed to connect to any test hosts")
    return False 