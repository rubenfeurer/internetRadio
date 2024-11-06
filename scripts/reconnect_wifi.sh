#!/bin/bash

# Wait for network to be available
max_attempts=30
attempt=0

echo "Waiting for network..."
while [ $attempt -lt $max_attempts ]; do
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        echo "Network is available"
        exit 0
    fi
    attempt=$((attempt + 1))
    sleep 1
done

echo "Network connection failed after $max_attempts attempts"
exit 1 