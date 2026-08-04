#!/usr/bin/env node

const playwright = require('playwright');
const fs = require('fs');
const path = require('path');

const TICKET_URL = 'https://ticket.volksbuehne-berlin.de/eventim.webshop/webticket/eventlist?production=120000';
const CHECK_INTERVAL = 30000; // 30 seconds
const STATUS_FILE = path.join(__dirname, 'ticket-status.json');
const LOG_FILE = path.join(__dirname, 'ticket-monitor.log');

function log(message) {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${message}`;
  console.log(logMessage);
  fs.appendFileSync(LOG_FILE, logMessage + '\n');
}

function loadStatus() {
  try {
    return JSON.parse(fs.readFileSync(STATUS_FILE, 'utf8'));
  } catch {
    return { lastCheck: null, ticketsFound: false, purchaseAttempted: false };
  }
}

function saveStatus(status) {
  fs.writeFileSync(STATUS_FILE, JSON.stringify(status, null, 2));
}

async function checkTickets() {
  let browser;
  try {
    browser = await playwright.chromium.launch({
      executablePath: '/opt/pw-browsers/chromium',
      headless: true,
    });

    const context = await browser.createBrowserContext();
    const page = await context.newPage();

    log('Fetching ticket page...');
    await page.goto(TICKET_URL, { waitUntil: 'networkidle', timeout: 30000 });

    // Look for ticket availability indicators
    const ticketElements = await page.locator('[data-qa*="ticket"], .ticket, .event-item, button:has-text("Kauf"), button:has-text("Buchen")').all();

    // Check for "Sold Out" or similar text
    const pageContent = await page.content();
    const soldOutPattern = /ausverkauft|sold out|keine.*verf[ü|ue]gbar|nicht.*verf[ü|ue]gbar/gi;
    const ticketPattern = /ticket|karte|platz/gi;

    const hasSoldOut = soldOutPattern.test(pageContent);
    const hasTickets = ticketPattern.test(pageContent) && !hasSoldOut;

    // Look for purchase buttons
    const buyButtons = await page.locator('button:has-text("Kauf"), button:has-text("Buchen"), a:has-text("Kauf"), a:has-text("Buchen")').all();
    const hasAvailableTickets = buyButtons.length > 0 || hasTickets;

    log(`Page loaded. Tickets available: ${hasAvailableTickets}, Sold out: ${hasSoldOut}`);
    log(`Found ${buyButtons.length} purchase buttons`);

    const status = loadStatus();
    status.lastCheck = new Date().toISOString();
    status.ticketsAvailable = hasAvailableTickets;

    if (hasAvailableTickets && !status.purchaseAttempted) {
      log('🎉 TICKETS FOUND! Attempting to purchase...');
      status.ticketsFound = true;

      // Try to click purchase button
      if (buyButtons.length > 0) {
        log(`Clicking first purchase button...`);
        await buyButtons[0].click();
        await page.waitForLoadState('networkidle');

        // Check if we're in the purchase flow
        const quantityInput = await page.locator('input[name*="quantity"], input[aria-label*="Anzahl"], input[placeholder*="Anzahl"]').first();

        if (quantityInput) {
          log('Purchase flow initiated. Entering quantity: 4');
          await quantityInput.fill('4');
          status.purchaseAttempted = true;

          // Look for confirm button
          const confirmButton = await page.locator('button:has-text("Weiter"), button:has-text("Bestätigen"), button:has-text("In den Warenkorb")').first();
          if (confirmButton) {
            log('Clicking confirm button...');
            await confirmButton.click();
            await page.waitForLoadState('networkidle');
            log('✅ Successfully attempted to add 4 tickets to cart!');
          }
        }
      }
    }

    saveStatus(status);
    await context.close();
    return hasAvailableTickets;

  } catch (error) {
    log(`❌ Error checking tickets: ${error.message}`);
    return false;
  } finally {
    if (browser) await browser.close();
  }
}

async function startMonitoring() {
  log('Starting ticket monitor for Volksbühne Berlin');
  log(`URL: ${TICKET_URL}`);
  log(`Check interval: ${CHECK_INTERVAL}ms`);

  // Initial check
  await checkTickets();

  // Continuous monitoring
  setInterval(async () => {
    await checkTickets();
  }, CHECK_INTERVAL);
}

startMonitoring().catch(err => {
  log(`Fatal error: ${err.message}`);
  process.exit(1);
});
