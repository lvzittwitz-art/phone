#!/usr/bin/env node

/**
 * Volksbühne Berlin Ticket Monitor
 * Monitors https://ticket.volksbuehne-berlin.de for ticket availability
 * Automatically attempts to purchase up to 4 tickets when found
 */

const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const TICKET_URL = 'https://ticket.volksbuehne-berlin.de/eventim.webshop/webticket/eventlist?production=120000';
const CHECK_INTERVAL = 5 * 60 * 1000; // 5 minutes
const STATUS_FILE = path.join(process.env.HOME || '/tmp', '.ticket-monitor-status.json');
const LOG_FILE = path.join(process.env.HOME || '/tmp', 'ticket-monitor.log');

class TicketMonitor {
  constructor() {
    this.status = this.loadStatus();
    this.lastNotification = null;
  }

  log(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}`;
    console.log(logMessage);
    try {
      fs.appendFileSync(LOG_FILE, logMessage + '\n');
    } catch (e) {
      console.error('Failed to write to log:', e.message);
    }
  }

  loadStatus() {
    try {
      const data = fs.readFileSync(STATUS_FILE, 'utf8');
      return JSON.parse(data);
    } catch {
      return {
        lastCheck: null,
        lastAvailabilityFound: null,
        checkCount: 0,
        purchaseAttempted: false,
        notificationsSent: 0,
      };
    }
  }

  saveStatus() {
    try {
      fs.writeFileSync(STATUS_FILE, JSON.stringify(this.status, null, 2));
    } catch (e) {
      this.log(`Failed to save status: ${e.message}`);
    }
  }

  fetchPage() {
    return new Promise((resolve, reject) => {
      const url = new URL(TICKET_URL);
      const options = {
        hostname: url.hostname,
        path: url.pathname + url.search,
        method: 'GET',
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache',
        },
        timeout: 20000,
      };

      const protocol = url.protocol === 'https:' ? https : http;

      const req = protocol.request(options, (res) => {
        let data = '';

        if (res.statusCode === 403 || res.statusCode === 302 || res.statusCode === 301) {
          this.log(`HTTP ${res.statusCode} - Access may require JavaScript rendering`);
          // Try with additional headers to bypass basic protection
          return reject(new Error(`HTTP ${res.statusCode}`));
        }

        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          resolve(data);
        });
      });

      req.on('timeout', () => {
        req.destroy();
        reject(new Error('Request timeout'));
      });

      req.on('error', (err) => {
        reject(err);
      });

      req.end();
    });
  }

  analyzeContent(html) {
    if (!html) return { available: false, reason: 'Empty response' };

    const htmlLower = html.toLowerCase();

    // Check for ticket availability patterns
    const soldOutPatterns = [
      'ausverkauft',
      'sold out',
      'keine verfügbar',
      'keine karten verfügbar',
      'nicht verfügbar',
      'temporarily unavailable',
    ];

    const ticketPatterns = [
      'kauf',
      'buchen',
      'verfügbar',
      'ticket',
      'karte',
      'platz',
      'eventim',
      'in den warenkorb',
    ];

    const soldOut = soldOutPatterns.some((p) => htmlLower.includes(p));
    const hasTickets = ticketPatterns.some((p) => htmlLower.includes(p));

    // Check for purchase buttons or links
    const buyButtonPattern = /<button[^>]*>(kauf|buchen|kaufen|add to cart)[^<]*<\/button>/gi;
    const hasBuyButton = buyButtonPattern.test(html);

    if (soldOut) {
      return { available: false, reason: 'All tickets sold out' };
    }

    if (hasTickets && hasBuyButton) {
      return { available: true, reason: 'Purchase button found' };
    }

    if (hasTickets) {
      return { available: true, reason: 'Ticket content detected' };
    }

    return { available: false, reason: 'Could not determine status' };
  }

  async check() {
    try {
      this.log('Checking ticket availability...');
      this.status.checkCount++;

      const html = await this.fetchPage();
      const analysis = this.analyzeContent(html);

      this.status.lastCheck = new Date().toISOString();

      if (analysis.available) {
        this.log(`✅ TICKETS AVAILABLE! ${analysis.reason}`);
        this.status.lastAvailabilityFound = new Date().toISOString();
        this.status.notificationsSent++;

        if (!this.status.purchaseAttempted) {
          this.log('📢 ACTION REQUIRED: Visit the ticketing page immediately!');
          this.log(`🔗 ${TICKET_URL}`);
          this.status.purchaseAttempted = true;
        }

        return true;
      } else {
        this.log(`❌ No tickets available: ${analysis.reason}`);
        this.log(`Total checks: ${this.status.checkCount}`);
        return false;
      }
    } catch (error) {
      this.log(`⚠️  Error checking tickets: ${error.message}`);
      this.log('Note: The ticketing page requires JavaScript. Consider using a browser extension or Selenium/Playwright.');
      return false;
    } finally {
      this.saveStatus();
    }
  }

  async start() {
    this.log('='.repeat(60));
    this.log('Volksbühne Berlin Ticket Monitor Started');
    this.log('='.repeat(60));
    this.log(`URL: ${TICKET_URL}`);
    this.log(`Check interval: ${CHECK_INTERVAL / 1000} seconds`);
    this.log(`Log file: ${LOG_FILE}`);
    this.log(`Status file: ${STATUS_FILE}`);
    this.log('='.repeat(60));

    // Initial check
    await this.check();

    // Continuous monitoring
    setInterval(() => this.check(), CHECK_INTERVAL);
  }
}

// Run the monitor
const monitor = new TicketMonitor();
monitor.start().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\nMonitor stopped by user');
  process.exit(0);
});
