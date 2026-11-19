#!/bin/bash
# Custom health check script

echo "=== Custom Health Check ==="
echo "Timestamp: $(date)"
echo "Hostname: $(hostname)"
echo "Uptime: $(uptime)"
echo "Disk Usage: $(df -h / | tail -1 | awk '{print $5}')"
echo "Memory Usage: $(free -h | grep Mem | awk '{print $3/$2 * 100.0}')%"
echo "Load Average: $(cat /proc/loadavg)"

# Check critical processes
for service in sshd nginx; do
    if pgrep -x "$service" > /dev/null; then
        echo "✓ $service is running"
    else
        echo "✗ $service is NOT running"
        exit 1
    fi
done

echo "=== Health Check PASSED ==="
exit 0
