#!/bin/bash

# Set up error handling
set -e

# Add check for required commands
for cmd in vcgencmd free df systemctl iwgetid iwconfig ping amixer grep; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: Required command '$cmd' not found"
        exit 1
    fi
done

# Add log rotation check
check_log_rotation() {
    local log_file=$1
    local max_size=$((10*1024*1024))  # 10MB in bytes
    
    if [ -f "$log_file" ]; then
        size=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file")
        if [ "$size" -gt "$max_size" ]; then
            echo_warn "Log file $log_file is larger than 10MB ($((size/1024/1024))MB)"
            echo_info "Consider rotating logs: mv $log_file ${log_file}.old"
        fi
    fi
}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

PROJECT_DIR="/home/radio/internetRadio"

# Check system resources
echo "=== System Resources ==="

# CPU Temperature
cpu_temp=$(vcgencmd measure_temp | cut -d'=' -f2 | cut -d"'" -f1)
if (( $(echo "$cpu_temp > 80" | bc -l) )); then
    echo_error "CPU Temperature: ${cpu_temp}°C (High!)"
elif (( $(echo "$cpu_temp > 70" | bc -l) )); then
    echo_warn "CPU Temperature: ${cpu_temp}°C (Warm)"
else
    echo_ok "CPU Temperature: ${cpu_temp}°C"
fi

# Memory Usage
total_mem=$(free -m | awk '/^Mem:/{print $2}')
used_mem=$(free -m | awk '/^Mem:/{print $3}')
mem_percent=$((used_mem * 100 / total_mem))

if [ $mem_percent -gt 90 ]; then
    echo_error "Memory Usage: ${mem_percent}% (${used_mem}MB/${total_mem}MB)"
elif [ $mem_percent -gt 80 ]; then
    echo_warn "Memory Usage: ${mem_percent}% (${used_mem}MB/${total_mem}MB)"
else
    echo_ok "Memory Usage: ${mem_percent}% (${used_mem}MB/${total_mem}MB)"
fi

# Disk Usage
disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$disk_usage" -gt 90 ]; then
    echo_error "Disk Usage: ${disk_usage}%"
elif [ "$disk_usage" -gt 80 ]; then
    echo_warn "Disk Usage: ${disk_usage}%"
else
    echo_ok "Disk Usage: ${disk_usage}%"
fi

# Check required services
echo -e "\n=== Services Status ==="
if systemctl is-active --quiet internetradio; then
    echo_ok "internetradio service is running"
    uptime=$(systemctl show internetradio --property=ActiveEnterTimestamp | cut -d'=' -f2)
    echo_info "Service uptime since: $uptime"
else
    echo_error "internetradio service is not running"
    echo_info "Try: sudo systemctl restart internetradio"
fi

# Check network
echo -e "\n=== Network Status ==="

# Check WiFi connection
if wifi_name=$(iwgetid -r); then
    echo_ok "WiFi connected to: $wifi_name"
    signal_strength=$(iwconfig wlan0 | grep "Signal level" | awk -F"=" '{print $3}' | cut -d' ' -f1)
    echo_info "Signal strength: $signal_strength dBm"
else
    echo_warn "WiFi not connected"
    echo_info "Available networks: $(iwlist wlan0 scan | grep ESSID | wc -l)"
fi

# Check internet connectivity
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo_ok "Internet connection is working"
    latency=$(ping -c 1 8.8.8.8 | tail -1 | awk '{print $4}' | cut -d '/' -f 2)
    echo_info "Average latency: ${latency}ms"
else
    echo_error "No internet connection"
fi

# Check audio
echo -e "\n=== Audio Status ==="

# Check bcm2835 Headphones (card 2)
if aplay -l | grep -q "bcm2835 Headphones"; then
    echo_ok "Audio hardware detected (bcm2835 Headphones)"
    
    # Check ALSA configuration
    if [ -f "/etc/asound.conf" ]; then
        if grep -q "defaults.pcm.card 2" /etc/asound.conf; then
            echo_ok "ALSA configuration is correct"
            
            # Check PCM volume control
            if amixer -c 2 sget 'PCM' >/dev/null 2>&1; then
                volume=$(amixer -c 2 sget 'PCM' | grep 'Playback' | awk -F'[][]' '{ print $2 }')
                if [ ! -z "$volume" ]; then
                    echo_ok "Volume control working"
                    echo_info "Current volume: $volume"
                else
                    echo_warn "Volume control needs unmuting"
                    echo_info "Run: sudo amixer -c 2 sset 'PCM' unmute && sudo amixer -c 2 sset 'PCM' 100%"
                fi
            else
                echo_warn "Volume control not accessible"
                echo_info "Try: sudo modprobe snd_bcm2835"
            fi
        else
            echo_warn "ALSA configuration needs updating"
        fi
    else
        echo_warn "Missing ALSA configuration"
    fi
    
    # Check VLC
    if command -v vlc >/dev/null 2>&1; then
        echo_ok "VLC is installed"
    else
        echo_error "VLC is not installed"
    fi
    
    # Check sound files
    if [ -d "/home/radio/internetRadio/sounds" ] && [ -f "/home/radio/internetRadio/sounds/boot.wav" ]; then
        echo_ok "Sound files present"
    else
        echo_warn "Missing sound files"
    fi
else
    echo_error "Audio hardware not detected"
    echo_info "Try: sudo modprobe snd_bcm2835"
fi

# Check log files and permissions
echo -e "\n=== Log Status ==="
echo "[OK] Log directory size: $(du -sh /home/radio/internetRadio/logs | cut -f1)"
echo "[WARN] Recent errors found in logs (last 5 minutes):"

# Direct check of app.log and radio.log
for logfile in "/home/radio/internetRadio/logs/app.log" "/home/radio/internetRadio/logs/radio.log"; do
    if [[ -f "$logfile" ]]; then
        filename=$(basename "$logfile")
        # Use tail to get recent entries and grep for errors
        tail -n 100 "$logfile" | grep -i "error\|exception\|fail" | while read -r line; do
            # Get current timestamp
            timestamp=$(date "+%Y-%m-%d %H:%M:%S")
            # Format the output
            echo "  • [$timestamp] ($filename) $line"
        done
    fi
done

# Remove debug output
# find /home/radio/internetRadio/logs -type f -name "*.log" -ls

# Final summary
echo -e "\n=== Summary ==="
echo "System health check completed at $(date)" 