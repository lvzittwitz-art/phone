#!/usr/bin/env python3

import urllib.request
import urllib.error
import json
import time
import os
from datetime import datetime
from pathlib import Path

TICKETS_URL = "https://ticket.volksbuehne-berlin.de/eventim.webshop/webticket/eventlist?production=120000"
CHECK_INTERVAL = 60  # seconds
LOG_FILE = Path.home() / "ticket-monitor.log"
STATUS_FILE = Path.home() / ".ticket-monitor-status.json"

def log_message(msg):
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")

def load_status():
    try:
        with open(STATUS_FILE) as f:
            return json.load(f)
    except:
        return {"last_check": None, "tickets_found": False, "notifications_sent": 0}

def save_status(status):
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)

def check_tickets():
    try:
        log_message("Checking ticket availability...")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = urllib.request.Request(TICKETS_URL, headers=headers)

        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')

            # Check for ticket availability indicators
            sold_out_patterns = ['ausverkauft', 'sold out', 'keine verfügbar']
            ticket_patterns = ['kauf', 'buchen', 'verfügbar']

            has_sold_out = any(pattern.lower() in html.lower() for pattern in sold_out_patterns)
            has_tickets = any(pattern.lower() in html.lower() for pattern in ticket_patterns)

            if has_tickets and not has_sold_out:
                log_message("🎉 TICKETS AVAILABLE! Check: " + TICKETS_URL)
                status = load_status()
                status["tickets_found"] = True
                status["notifications_sent"] += 1
                save_status(status)
                return True
            elif has_sold_out:
                log_message("❌ Tickets sold out")
            else:
                log_message("⚠️  Could not determine ticket status")

            status = load_status()
            status["last_check"] = datetime.now().isoformat()
            save_status(status)
            return False

    except urllib.error.HTTPError as e:
        log_message(f"HTTP Error: {e.code}")
        if e.code == 403:
            log_message("Access denied - page may require JavaScript/browser")
    except urllib.error.URLError as e:
        log_message(f"Connection error: {e.reason}")
    except Exception as e:
        log_message(f"Error: {e}")

    return False

def main():
    log_message("Starting Volksbühne Berlin ticket monitor")
    log_message(f"Check interval: {CHECK_INTERVAL} seconds")
    log_message(f"URL: {TICKETS_URL}")

    while True:
        try:
            check_tickets()
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            log_message("Monitor stopped by user")
            break
        except Exception as e:
            log_message(f"Fatal error: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
