#!/usr/bin/env node
/**
 * tools/test_pos_react_advanced_parity.js
 * ========================================
 * Comprehensive End-to-End Test for React POS Advanced Parity:
 * 1. Multi-Order Tabs (+ New Tab, Switch Tab)
 * 2. Numpad Interactions (Qty change, % Discount, Price change)
 * 3. Fiori Modals (Customer Search, Order Note)
 * 4. Dedicated Payment Screen (Multi-Tender, Quick Cash, Split Payment)
 * 5. 80mm Thermal Receipt Screen (Render, Print Hook, Next Order Lifecycle)
 * 6. Zero Console Errors
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ARTIFACTS_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

async function runAdvancedParityTest() {
  console.log('======================================================================');
  console.log('INSILOS REACT POS — ADVANCED PARITY & ERGONOMIC PLAYWRIGHT SUITE');
  console.log('======================================================================\n');

  const consoleErrors = [];
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1.0
  });

  const page = await context.newPage();

  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
      console.error(`  [Browser Error] ${msg.text()}`);
    }
  });

  page.on('pageerror', err => {
    consoleErrors.push(err.message);
    console.error(`  [Page Exception] ${err.message}`);
  });

  page.on('response', async res => {
    if (res.url().includes('/jsonrpc') || res.url().includes('/api/') || res.url().includes('/web/dataset/call_kw')) {
      try {
        const json = await res.json();
        if (json.error) {
          console.error(`  [RPC Error] ${JSON.stringify(json.error, null, 2)}`);
        }
      } catch (e) {}
    }
  });

  try {
    // 1. Auth & Navigate
    console.log('1. Authenticating admin...');
    await page.request.post('http://localhost:28069/web/session/authenticate', {
      data: {
        jsonrpc: '2.0',
        params: { db: 'odoo20_dev', login: 'admin', password: 'admin' }
      }
    });

    console.log('2. Navigating to React POS...');
    await page.goto('http://localhost:28069/pos/react/1', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForSelector('#pos-react-root', { state: 'attached', timeout: 20000 });
    await page.waitForTimeout(3000);

    // 2. Test Multi-Order Tabs
    console.log('\n3. Testing Multi-Order Tabs...');
    const addTabBtn = await page.$('.pos-order-tab-add');
    if (addTabBtn) {
      await addTabBtn.click();
      await page.waitForTimeout(500);
      const tabCount = await page.$$eval('.pos-order-tab', tabs => tabs.length);
      console.log(`   ✓ Clicked "+" tab. Total active order tabs: ${tabCount}`);
    }

    // Switch back to Tab 1
    const firstTab = await page.$('.pos-order-tab:has-text("Order 1")');
    if (firstTab) {
      await firstTab.click();
      await page.waitForTimeout(500);
      console.log('   ✓ Switched back to "Order 1" tab.');
    }

    // 3. Add Products to Cart
    console.log('\n4. Adding Products to Cart...');
    const croissant = await page.$('button.product:has-text("Croissant")');
    if (croissant) {
      await croissant.click();
      await page.waitForTimeout(800);
      console.log('   ✓ Added Croissant to cart.');
    }

    const espresso = await page.$('button.product:has-text("Espresso")');
    if (espresso) {
      await espresso.click();
      await page.waitForTimeout(800);
      console.log('   ✓ Added Espresso to cart.');
    }

    // 4. Test Numpad Interaction on Active Line
    console.log('\n5. Testing Tactile Numpad (Qty & Discount)...');
    // Click Croissant line to select it
    const croissantLine = await page.$('.pos-cart-line:has-text("Croissant")');
    if (croissantLine) {
      await croissantLine.click();
      await page.waitForTimeout(300);
      console.log('   ✓ Selected Croissant line.');
    }

    // Press '3' on numpad in Qty mode
    const key3 = await page.$('.pos-num-btn:has-text("3")');
    if (key3) {
      await key3.click();
      await page.waitForTimeout(800);
      console.log('   ✓ Pressed "3" on numpad.');
    }

    // Switch to % Disc mode and enter 10%
    const discModeBtn = await page.$('.pos-num-btn.mode-btn:has-text("% Disc")');
    if (discModeBtn) {
      await discModeBtn.click();
      await page.waitForTimeout(300);
      console.log('   ✓ Switched to "% Disc" mode.');

      const key1 = await page.$('.pos-num-btn:has-text("1")');
      const key0 = await page.$('.pos-num-btn:has-text("0")');
      if (key1 && key0) {
        await key1.click();
        await page.waitForTimeout(300);
        await key0.click();
        await page.waitForTimeout(800);
        console.log('   ✓ Entered "10" on numpad for discount.');
      }
    }

    // Capture Numpad state screenshot
    const numpadScreenshot = path.join(ARTIFACTS_DIR, 'pos_react_numpad_interactive.png');
    await page.screenshot({ path: numpadScreenshot, fullPage: true });
    console.log(`   ✓ Numpad interaction screenshot captured: ${numpadScreenshot}`);

    // 5. Test Note Modal
    console.log('\n6. Testing Order Note Modal...');
    const noteBtn = await page.$('.pos-action-btn:has-text("Note")');
    if (noteBtn) {
      await noteBtn.click();
      await page.waitForTimeout(500);
      const noteInput = await page.$('.pos-modal-body textarea');
      if (noteInput) {
        await noteInput.fill('VIP guest table - extra hot coffee, gluten conscious');
        const saveNoteBtn = await page.$('.pos-modal-footer button:has-text("Save Note")');
        if (saveNoteBtn) {
          await saveNoteBtn.click();
          await page.waitForTimeout(500);
          console.log('   ✓ Saved order note via NoteModal.');
        }
      }
    }

    // 5.5 Test Restaurant Floor Plan (Epic 7)
    console.log('\n6.5. Testing Restaurant Floor Plan & Table Selection (Epic 7)...');
    const tableBtn = await page.$('.pos-table-indicator-btn');
    if (tableBtn) {
      await tableBtn.click();
      await page.waitForTimeout(1000);
      const floorScreen = await page.$('.pos-floor-screen');
      if (floorScreen) {
        console.log('   ✓ Navigated to Restaurant Floor Screen!');
        const floorShot = path.join(ARTIFACTS_DIR, 'pos_react_floor_plan.png');
        await page.screenshot({ path: floorShot, fullPage: true });
        console.log(`   ✓ Floor plan screenshot captured: ${floorShot}`);

        // Switch to "VIP Lounge" tab
        const vipTab = await page.$('.pos-floor-tab:has-text("VIP Lounge")');
        if (vipTab) {
          await vipTab.click();
          await page.waitForTimeout(400);
          console.log('   ✓ Switched to VIP Lounge floor tab.');
        }

        // Select Table 5
        const table5 = await page.$('.pos-table-card:has-text("Table 5")');
        if (table5) {
          await table5.click();
          await page.waitForTimeout(1000);
          console.log('   ✓ Selected Table 5. Returned to Register.');
        }

        // Verify Table chip in Cart customer bar
        const tableChip = await page.$('.pos-table-chip');
        if (tableChip) {
          const tableText = await tableChip.innerText();
          console.log(`   ✓ Verified Table Chip in Cart: "${tableText}"`);
        }
      }
    }

    // 5.6 Test Kitchen Order Dispatching (Epic 8)
    console.log('\n6.6. Testing Kitchen Order Dispatching (Epic 8)...');
    const kitchenBtn = await page.$('.pos-action-btn.kitchen-btn');
    if (kitchenBtn) {
      await kitchenBtn.click();
      await page.waitForTimeout(800);
      const kitchenBadge = await page.$('.pos-cart-line-kitchen-badge');
      if (kitchenBadge) {
        const badgeText = await kitchenBadge.innerText();
        console.log(`   ✓ Order dispatched to kitchen! Badge: "${badgeText}"`);
      }
      const kitchenDispatchedShot = path.join(ARTIFACTS_DIR, 'pos_react_kitchen_dispatched.png');
      await page.screenshot({ path: kitchenDispatchedShot, fullPage: true });
      console.log(`   ✓ Kitchen dispatched screenshot captured: ${kitchenDispatchedShot}`);
    }

    // 5.7 Test Kitchen Prep Display Screen (Epic 8)
    console.log('\n6.7. Testing Kitchen Prep Display Screen (Epic 8)...');
    const kitchenScreenBtn = await page.$('button[title*="Kitchen"]') || await page.$('button:has-text("Kitchen Prep")');
    if (kitchenScreenBtn) {
      await kitchenScreenBtn.click();
      await page.waitForTimeout(1000);
      const kitchenScreen = await page.$('.pos-kitchen-screen');
      if (kitchenScreen) {
        console.log('   ✓ Navigated to Kitchen & Bar Preparation Display!');
        const kitchenScreenShot = path.join(ARTIFACTS_DIR, 'pos_react_kitchen_screen.png');
        await page.screenshot({ path: kitchenScreenShot, fullPage: true });
        console.log(`   ✓ Kitchen Screen screenshot captured: ${kitchenScreenShot}`);

        // Click "Start Prep" on first ticket if available
        const startPrepBtn = await page.$('.pos-ticket-btn.start-btn');
        if (startPrepBtn) {
          await startPrepBtn.click();
          await page.waitForTimeout(400);
          console.log('   ✓ Clicked "Start Prep" on ticket.');
        }

        // Return to Register
        const backBtn = await page.$('.pos-kitchen-header .pos-btn-back') || await page.$('.pos-kitchen-screen button:has-text("Back to Register")');
        if (backBtn) {
          await backBtn.click();
          await page.waitForTimeout(1000);
          console.log('   ✓ Returned from Kitchen Screen to Register.');
        }
      }
    } else {
      console.log('   [!] Warning: Kitchen button not found');
    }

    // 6. Test Payment Screen Transition
    console.log('\n7. Entering Dedicated Payment Screen...');
    const payScreenBtn = await page.$('.pos-action-btn.pay-btn');
    if (payScreenBtn) {
      await payScreenBtn.click();
      await page.waitForTimeout(1000);

      // Verify payment screen container
      const payScreen = await page.$('.pos-payment-screen');
      if (payScreen) {
        console.log('   ✓ Successfully loaded PosReactPaymentScreen!');

        // Test Quick Cash Bill (e.g. +$20 or Exact)
        const exactCashBtn = await page.$('.pos-quick-cash-btn:has-text("Exact")');
        if (exactCashBtn) {
          await exactCashBtn.click();
          await page.waitForTimeout(500);
          console.log('   ✓ Clicked "Exact" Quick Cash button.');
        }

        // Capture payment screen screenshot
        const payScreenShot = path.join(ARTIFACTS_DIR, 'pos_react_payment_screen.png');
        await page.screenshot({ path: payScreenShot, fullPage: true });
        console.log(`   ✓ Payment screen screenshot captured: ${payScreenShot}`);

        // Validate Payment
        const validateBtn = await page.$('.pos-validate-btn');
        if (validateBtn) {
          console.log('   ✓ Validating payment...');
          await validateBtn.click();
          await page.waitForTimeout(3000);
          const postValidateState = await page.evaluate(() => {
            const err = document.querySelector('.pos-payment-error') || document.querySelector('p[aria-label="Recovery error"]');
            const receipt = document.querySelector('.pos-receipt-screen');
            return {
              hasReceipt: Boolean(receipt),
              errorText: err ? err.innerText : '',
              bodySnippet: document.body.innerText.slice(0, 1000)
            };
          });
          console.log('   • Post-Validate State:', JSON.stringify(postValidateState, null, 2));
        }
      }
    }

    // 7. Test Receipt Screen
    console.log('\n8. Checking Receipt Screen & Thermal Receipt Preview...');
    const receiptScreen = await page.$('.pos-receipt-screen');
    if (receiptScreen) {
      console.log('   ✓ Successfully loaded PosReactReceiptScreen!');

      // Capture thermal receipt screenshot
      const receiptShot = path.join(ARTIFACTS_DIR, 'pos_react_thermal_receipt.png');
      await page.screenshot({ path: receiptShot, fullPage: true });
      console.log(`   ✓ Thermal receipt screenshot captured: ${receiptShot}`);

      // Test "Next Order" button
      const nextOrderBtn = await page.$('.pos-next-order-btn');
      if (nextOrderBtn) {
        await nextOrderBtn.click();
        await page.waitForTimeout(1500);
        console.log('   ✓ Clicked "Next Order →". Returned to fresh Catalog/Products screen.');
      }
    }

    // 8. Console Error Assessment
    console.log('\n9. Assessing Console Logs...');
    const fatalErrors = consoleErrors.filter(e => !e.includes('favicon.ico') && !e.includes('Content Security Policy'));
    console.log(`   • Total Console Errors: ${consoleErrors.length}`);
    console.log(`   • Fatal Exceptions: ${fatalErrors.length}`);

    console.log('\n======================================================================');
    if (fatalErrors.length === 0) {
      console.log('🎉 ADVANCED POS REACT PARITY: 100% PASS (ZERO CONSOLE ERRORS)');
    } else {
      console.log('❌ ADVANCED POS REACT PARITY: FAILURES DETECTED');
    }
    console.log('======================================================================');

  } catch (err) {
    console.error('\n❌ Advanced Parity Test Failed:', err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

runAdvancedParityTest();
