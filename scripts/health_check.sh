#!/bin/bash

# Set up error handling
set -e

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

# Check pigpiod
if systemctl is-active --quiet pigpiod; then
    echo_ok "pigpiod service is running"
else
    echo_error "pigpiod service is not running"
    echo_info "Try: sudo systemctl restart pigpiod"
fi

# Check internetradio service
if systemctl is-active --quiet internetradio; then
    echo_ok "internetradio service is running"
    uptime=$(systemctl show internetradio --property=ActiveEnterTimestamp | cut -d'=' -f2)
    echo_info "Service uptime since: $uptime"
else
    echo_error "internetradio service is not running"
    echo_info "Check: sudo systemctl status internetradio"
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
if amixer sget 'Master' >/dev/null 2>&1; then
    echo_ok "Audio system is working"
    volume=$(amixer sget 'Master' | grep 'Right:' | awk -F'[][]' '{ print $2 }')
    echo_info "Current volume: $volume"
    
    # Check sound files
    if [ ! -f "$PROJECT_DIR/sounds/boot.wav" ]; then
        echo_error "Missing sound file: boot.wav"
        echo_info "Run: sudo cp $PROJECT_DIR/sounds/default/boot.wav $PROJECT_DIR/sounds/"
    fi
else
    echo_error "Audio system not responding"
    echo_info "Try: sudo alsactl restore"
fi

# Check log files and permissions
echo -e "\n=== Log Status ==="
log_dir="$PROJECT_DIR/logs"
if [ -d "$log_dir" ]; then
    log_size=$(du -sh "$log_dir" | cut -f1)
    echo_ok "Log directory size: $log_size"
    
    # Check permissions
    log_perms=$(stat -c "%a" "$log_dir")
    if [ "$log_perms" != "755" ]; then
        echo_warn "Incorrect log directory permissions: $log_perms (should be 755)"
        echo_info "Fix with: sudo chmod 755 $log_dir"
    fi
    
    # Check for recent errors in logs
    recent_errors=$(grep -i "error" "$log_dir/radio.log" "$log_dir/app.log" 2>/dev/null | tail -n 5)
    if [ ! -z "$recent_errors" ]; then
        echo_warn "Recent errors found in logs:"
        echo "$recent_errors"
    else
        echo_ok "No recent errors in logs"
    fi
else
    echo_error "Log directory not found"
fi

# Final summary
echo -e "\n=== Summary ==="
echo "System health check completed at $(date)" 