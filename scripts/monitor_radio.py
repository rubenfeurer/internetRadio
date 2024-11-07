import subprocess
import time
from datetime import datetime
import re

def get_current_station():
    try:
        # Load config to get station names
        with open('/home/radio/internetRadio/config.toml', 'r') as f:
            config = f.read()
            links = re.findall(r'name = "(.*?)"', config)
            urls = re.findall(r'url = "(.*?)"', config)
            stations = dict(zip(urls, links))

        # Get currently playing URL from service status
        status = subprocess.check_output(['systemctl', 'status', 'internetradio']).decode()
        for url in stations.keys():
            if url in status:
                # Check if stream is playing or paused
                vlc_status = subprocess.check_output(['ps', 'aux']).decode()
                is_playing = 'vlc' in vlc_status and url in vlc_status
                state = "Playing" if is_playing else "Paused"
                return f"{stations[url]} ({state})"
        return "No station playing"
    except:
        return "Unable to determine current station"

def get_service_status():
    try:
        status = subprocess.check_output(['systemctl', 'is-active', 'internetradio']).decode().strip()
        return "✓ Running" if status == "active" else "✗ Stopped"
    except:
        return "✗ Error"

def get_recent_logs(num_lines=10):
    try:
        # Get logs in reverse order, limit to 10 lines
        logs = subprocess.check_output(['journalctl', '-u', 'internetradio', '-n', str(num_lines), '-r']).decode()
        return logs.strip()
    except:
        return "Unable to fetch logs"

def clear_screen():
    print("\033c", end="")

def main():
    while True:
        clear_screen()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("Internet Radio Monitor")
        print("=" * 50)
        print(f"Last Updated: {now}")
        print("-" * 50)
        
        # Service Status
        status = get_service_status()
        print(f"Service Status: {status}")
        
        # Current Station
        current = get_current_station()
        print(f"Current Station: {current}")
        print("-" * 50)
        
        # Recent Logs (last 10 entries, newest first)
        print("Recent Logs:")
        print(get_recent_logs())
        
        time.sleep(5)

if __name__ == "__main__":
    main() 