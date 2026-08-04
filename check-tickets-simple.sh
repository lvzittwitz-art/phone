#!/bin/bash

TICKETS_URL="https://ticket.volksbuehne-berlin.de/eventim.webshop/webticket/eventlist?production=120000"
TIMEOUT=10
LOG_FILE="$HOME/ticket-monitor.log"

log_message() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_message "Checking ticket availability..."

# Try to fetch the page
RESPONSE=$(curl -s -w "\n%{http_code}" -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  --connect-timeout $TIMEOUT --max-time 20 \
  "$TICKETS_URL" 2>&1 || echo "error")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

log_message "HTTP Status: $HTTP_CODE"

# Check for common ticket indicators
if echo "$BODY" | grep -iq "kauf\|buchen\|verfügbar\|verfugbar"; then
  log_message "✅ Page contains ticket-related content"

  # Check for sold out patterns
  if echo "$BODY" | grep -iq "ausverkauft\|sold out"; then
    log_message "❌ All tickets appear to be sold out"
    exit 1
  else
    log_message "🎉 Tickets might be available! Check the website:"
    log_message "$TICKETS_URL"
    exit 0
  fi
else
  log_message "⚠️  Could not parse ticket information from page"
  exit 2
fi
