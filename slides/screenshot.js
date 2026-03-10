const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 2 });
  const filePath = 'file://' + path.resolve(__dirname, 'why-aws.html');
  await page.goto(filePath, { waitUntil: 'networkidle0', timeout: 15000 });
  await page.screenshot({ path: path.resolve(__dirname, 'why-aws.png'), fullPage: false });
  await browser.close();
  console.log('Done: why-aws.png');
})();
