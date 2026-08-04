# Volksbühne Berlin Ticket Monitor - Setup Guide

## 🎭 Event Details
- **Event URL**: https://ticket.volksbuehne-berlin.de/eventim.webshop/webticket/eventlist?production=120000
- **Venue**: Volksbühne Berlin
- **Production ID**: 120000
- **Goal**: Get up to 4 tickets when they become available

---

## ✅ What Has Been Set Up

### 1. **Scheduled Automated Monitor**
- **Type**: Hourly automated check (runs every 60 minutes)
- **Trigger ID**: `trig_01HjdMXK8RoHRcHX8qrLSqmS`
- **Status**: ✅ ACTIVE
- **Notifications**: 
  - 📱 Push notification when tickets found
  - 📧 Email notification when tickets found
- **Next run**: Check the trigger status in your Claude routine settings

**How it works**: Every hour, a new session starts and checks if tickets are available. If found, you'll receive push and email notifications.

### 2. **Local Node.js Monitoring Script**
- **File**: `ticket-monitor-advanced.js`
- **Type**: Long-running process (recommended for your machine)
- **Check interval**: Every 5 minutes
- **Logs**: `~/ticket-monitor.log`
- **Status file**: `~/.ticket-monitor-status.json`

**To run**:
```bash
cd ~/phone
node ticket-monitor-advanced.js
```

**To run in background**:
```bash
nohup node ~/phone/ticket-monitor-advanced.js > ~/ticket-monitor.log 2>&1 &
```

### 3. **Python Monitoring Script**
- **File**: `ticket-monitor.py`
- **Type**: Lightweight, checks every 60 seconds
- **Platform**: Works on Linux, macOS, Windows

**To run**:
```bash
python3 ~/phone/ticket-monitor.py
```

### 4. **Quick Manual Check**
- **File**: `check-tickets-simple.sh`
- **Type**: One-time check using curl
- **Use case**: Quick status check without starting a continuous monitor

**To run**:
```bash
bash ~/phone/check-tickets-simple.sh
```

---

## 🚀 Recommended Setup

### **Option A: Maximum Coverage (Recommended)**
Run ALL monitoring solutions simultaneously:

```bash
# Terminal 1: Start Node.js monitor
cd ~/phone && node ticket-monitor-advanced.js

# Terminal 2: Monitor logs in real-time
tail -f ~/ticket-monitor.log

# Terminal 3: Keep automated hourly check (already set up)
# Just check your notifications
```

### **Option B: Simple Long-Running**
```bash
# Start in background and let it run
nohup node ~/phone/ticket-monitor-advanced.js > ~/ticket-monitor.log 2>&1 &

# Check status anytime
cat ~/.ticket-monitor-status.json
tail -f ~/ticket-monitor.log
```

### **Option C: Lightweight**
```bash
# Use Python (less resource intensive)
python3 ~/phone/ticket-monitor.py
```

---

## 📊 Monitoring Status

### View Current Status
```bash
cat ~/.ticket-monitor-status.json
```

### View Full Log
```bash
cat ~/ticket-monitor.log
```

### Follow Logs Live
```bash
tail -f ~/ticket-monitor.log
```

### Check Processes
```bash
# See running monitors
ps aux | grep -E "ticket-monitor|node|python"

# Kill a monitor if needed
pkill -f ticket-monitor
```

---

## ⚠️ Important Notes

### Page Access Issues
The ticketing page uses dynamic content (JavaScript) which makes it harder to monitor programmatically:
- HTTP 403 Forbidden errors may occur
- You may need to manually verify results
- The automated check will use heuristics to detect ticket availability

### Browser-Based Alternative
If the scripts fail consistently, consider:
1. Using a **browser extension** to monitor page changes
2. Setting up **Selenium** or **Puppeteer** for full browser rendering
3. Manually checking the page during likely release times

### Purchase Process
When tickets are found:
1. **You'll receive immediate notifications** (push + email)
2. **Visit the URL immediately**: https://ticket.volksbuehne-berlin.de/eventim.webshop/webticket/eventlist?production=120000
3. **Select up to 4 tickets**
4. **Complete checkout** before they sell out

---

## 🔔 What Triggers a Notification

### Automated Monitor (Hourly)
- ✅ Tickets detected as available
- ❌ Tickets sold out
- ⚠️ Page access errors

### Local Monitors
- Console output immediately
- Logged to file for review

---

## 📝 Log Format Example

```
[2026-08-04T16:46:40.123Z] Starting Volksbühne Berlin Ticket Monitor
[2026-08-04T16:46:40.456Z] URL: https://ticket.volksbuehne-berlin.de/eventim.webshop/webticket/eventlist?production=120000
[2026-08-04T16:47:05.789Z] Checking ticket availability...
[2026-08-04T16:47:08.012Z] ❌ No tickets available: All tickets sold out
[2026-08-04T16:52:10.345Z] Checking ticket availability...
[2026-08-04T16:52:13.678Z] ✅ TICKETS AVAILABLE! Purchase button found
[2026-08-04T16:52:13.901Z] 📢 ACTION REQUIRED: Visit the ticketing page immediately!
```

---

## 🛑 Stop Monitoring

```bash
# Stop the Node.js monitor
pkill -f "node ticket-monitor-advanced.js"

# Stop Python monitor
pkill -f "python3.*ticket-monitor.py"

# Or use Ctrl+C if running in foreground
```

---

## 📞 Troubleshooting

### Monitor not starting?
```bash
# Check Node.js is installed
node --version

# Check Python is installed
python3 --version

# Try running with error output
node ~/phone/ticket-monitor-advanced.js 2>&1 | head -20
```

### No notifications received?
- Check that notifications are enabled in your Claude settings
- Verify the trigger is active: Look for "Volksbühne Ticket Monitor" in your Routines
- Check logs manually: `tail -f ~/ticket-monitor.log`

### Page access denied?
This is normal - the ticketing site blocks some automated access. The monitors will still attempt to analyze what's available through various methods.

### Want faster checks?
The automation system requires hourly minimum intervals. For faster checks, run the local Node.js script which checks every 5 minutes.

---

## 🎯 Quick Commands Reference

```bash
# Start monitoring (best option)
cd ~/phone && node ticket-monitor-advanced.js

# Watch logs live
tail -f ~/ticket-monitor.log

# Check status
cat ~/.ticket-monitor-status.json

# One-time check
bash ~/phone/check-tickets-simple.sh

# Stop all monitors
pkill -f ticket-monitor

# Run in background
nohup node ~/phone/ticket-monitor-advanced.js &
```

---

## ✨ Best Practices

1. **Run multiple monitors** - Increases chances of catching tickets
2. **Keep notifications enabled** - You'll get instant alerts
3. **Check logs regularly** - Understand what the monitor is finding
4. **Have the URL ready** - When tickets are found, visit immediately
5. **Know your payment method** - Speed is critical when tickets drop

---

Good luck getting your Volksbühne Berlin tickets! 🎭🎫
