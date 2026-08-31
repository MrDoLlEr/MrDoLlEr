import puppeteer from 'puppeteer';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const browser = await puppeteer.launch({
  args: ['--no-sandbox', '--disable-setuid-sandbox'],
});
const page = await browser.newPage();
await page.setViewport({ width: 1080, height: 1350 });
await page.goto('file://' + path.join(__dirname, 'nostalgia-design.html'), { waitUntil: 'domcontentloaded', timeout: 30000 });
await new Promise(r => setTimeout(r, 2000));
await page.screenshot({ path: path.join(__dirname, 'nostalgia-design.png'), fullPage: false });
await browser.close();
console.log('Done');
