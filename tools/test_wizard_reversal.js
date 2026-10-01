const { chromium } = require('playwright');

async function testWizardOpening() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage({ viewport: { width: 1600, height: 950 } });

  console.log('Authenticating...');
  await page.request.post('http://localhost:28069/web/session/authenticate', {
    data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
  });

  await page.goto('http://localhost:28069/web#id=12&model=account.move&view_type=form&action=475', {
    waitUntil: 'networkidle',
    timeout: 30000
  });

  await page.waitForSelector('.o_form_view', { timeout: 15000 });
  console.log('Form view loaded. Triggering account.move.reversal wizard...');

  const actionResult = await page.evaluate(async () => {
    try {
      const actionService = odoo.__WOWL_DEBUG__.root.env.services.action;
      const res = await actionService.doAction({
        type: 'ir.actions.act_window',
        res_model: 'account.move.reversal',
        views: [[false, 'form']],
        target: 'new',
        context: { active_model: 'account.move', active_ids: [12], active_id: 12 }
      });
      return { success: true, res };
    } catch (e) {
      return { success: false, error: e.message, stack: e.stack };
    }
  });

  console.log('Action result:', actionResult);

  // Wait for modal to appear
  await page.waitForSelector('.modal.o_technical_modal, .modal-dialog', { timeout: 10000 });
  await page.waitForTimeout(1000);

  const modalMetrics = await page.evaluate(() => {
    const modal = document.querySelector('.modal.show, .o_dialog .modal, .modal');
    const dialog = modal ? modal.querySelector('.modal-dialog') : null;
    const content = dialog ? dialog.querySelector('.modal-content') : null;
    const header = content ? content.querySelector('.modal-header') : null;
    const title = header ? header.querySelector('.modal-title') : null;
    const body = content ? content.querySelector('.modal-body') : null;
    const footer = content ? content.querySelector('.modal-footer') : null;
    const footerBtns = footer ? Array.from(footer.querySelectorAll('.btn')) : [];

    const getMetrics = (el) => {
      if (!el) return null;
      const rect = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);
      return {
        rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height, top: rect.top, bottom: rect.bottom, left: rect.left, right: rect.right },
        styles: {
          height: style.height,
          padding: `${style.paddingTop} ${style.paddingRight} ${style.paddingBottom} ${style.paddingLeft}`,
          paddingTop: style.paddingTop,
          paddingRight: style.paddingRight,
          paddingBottom: style.paddingBottom,
          paddingLeft: style.paddingLeft,
          overflowX: style.overflowX,
          overflowY: style.overflowY,
          position: style.position,
          bottom: style.bottom,
          fontSize: style.fontSize,
          fontWeight: style.fontWeight,
          borderRadius: style.borderRadius
        },
        scrollWidth: el.scrollWidth,
        clientWidth: el.clientWidth,
        scrollHeight: el.scrollHeight,
        clientHeight: el.clientHeight,
        hasHorizontalScrollbar: el.scrollWidth > el.clientWidth
      };
    };

    return {
      hasModal: !!modal,
      header: getMetrics(header),
      title: getMetrics(title),
      body: getMetrics(body),
      footer: getMetrics(footer),
      buttons: footerBtns.map(btn => ({
        text: btn.innerText.trim(),
        ...getMetrics(btn)
      }))
    };
  });

  console.log('Modal metrics:', JSON.stringify(modalMetrics, null, 2));

  await page.screenshot({ path: 'tools/test_artifacts_wizard_reversal.png' });
  console.log('Screenshot saved to tools/test_artifacts_wizard_reversal.png');

  await browser.close();
}

testWizardOpening().catch(err => {
  console.error(err);
  process.exit(1);
});
