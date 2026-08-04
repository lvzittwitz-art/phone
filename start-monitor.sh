#!/bin/bash

# Volksbühne Ticket Monitor - Quick Start

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$HOME/ticket-monitor.log"

echo ""
echo "🎭 Volksbühne Berlin Ticket Monitor"
echo "===================================="
echo ""
echo "Available options:"
echo ""
echo "1️⃣  Start Node.js Monitor (5-min checks, recommended)"
echo "2️⃣  Start Python Monitor (60-sec checks)"
echo "3️⃣  Quick one-time check"
echo "4️⃣  View logs"
echo "5️⃣  View status"
echo "6️⃣  Stop all monitors"
echo "7️⃣  Read guide"
echo ""

read -p "Choose option (1-7): " choice

case $choice in
  1)
    echo ""
    echo "Starting Node.js monitor (checks every 5 minutes)..."
    echo "Logs will be saved to: $LOG_FILE"
    echo "Press Ctrl+C to stop"
    echo ""
    cd "$SCRIPT_DIR"
    node ticket-monitor-advanced.js
    ;;
  2)
    echo ""
    echo "Starting Python monitor (checks every 60 seconds)..."
    echo "Logs will be saved to: $LOG_FILE"
    echo "Press Ctrl+C to stop"
    echo ""
    python3 "$SCRIPT_DIR/ticket-monitor.py"
    ;;
  3)
    echo ""
    bash "$SCRIPT_DIR/check-tickets-simple.sh"
    ;;
  4)
    echo ""
    echo "📋 Recent logs (last 50 lines):"
    echo "==============================="
    if [ -f "$LOG_FILE" ]; then
      tail -50 "$LOG_FILE"
    else
      echo "No logs found yet. Start monitoring first!"
    fi
    ;;
  5)
    echo ""
    echo "📊 Current Status:"
    echo "=================="
    if [ -f "$HOME/.ticket-monitor-status.json" ]; then
      cat "$HOME/.ticket-monitor-status.json" | python3 -m json.tool 2>/dev/null || cat "$HOME/.ticket-monitor-status.json"
    else
      echo "No status file found yet. Start monitoring first!"
    fi
    ;;
  6)
    echo ""
    echo "Stopping all monitors..."
    pkill -f "node.*ticket-monitor" || true
    pkill -f "python3.*ticket-monitor" || true
    echo "✅ Done"
    ;;
  7)
    echo ""
    if command -v less &> /dev/null; then
      less "$SCRIPT_DIR/TICKET_MONITOR_GUIDE.md"
    else
      cat "$SCRIPT_DIR/TICKET_MONITOR_GUIDE.md"
    fi
    ;;
  *)
    echo "Invalid option"
    exit 1
    ;;
esac
