// Renders the Mushaf pages shown on the site to WebP, using the site's own
// page engine (public/assets/mushaf.js) in the preinstalled Chromium.
//
//   python3 -m http.server 8765 --directory website &
//   node website/tools/render_pages.mjs
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { mkdirSync, rmSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
// CommonJS resolution finds a globally installed Playwright too.
const { chromium } = createRequire(import.meta.url)('playwright');
const out = join(here, '..', 'public', 'assets', 'img');
const base = process.env.SITE_ORIGIN || 'http://127.0.0.1:8765';

// [page, theme, tajweed]
const RENDERS = [
  [293, 'classic', true], [604, 'parchment', true],
  [1, 'classic', true], [2, 'parchment', true], [293, 'night', true], [604, 'minimal', false],
  [2, 'night', true], [1, 'parchment', false], [604, 'classic', true],
];

mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1000, height: 1700 }, deviceScaleFactor: 1 });
for (const [n, theme, tajweed] of RENDERS) {
  await page.goto(`${base}/tools/render.html?page=${n}&theme=${theme}&tajweed=${tajweed ? 1 : 0}`);
  await page.waitForSelector('body[data-ready="1"]');
  const png = join(out, `page-${n}-${theme}.png`);
  await page.locator('#page').screenshot({ path: png });
  const webp = png.replace(/\.png$/, '.webp');
  execFileSync('python3', ['-c', `from PIL import Image; Image.open(${JSON.stringify(png)}).convert('RGB').save(${JSON.stringify(webp)}, 'WEBP', quality=82, method=6)`]);
  rmSync(png);
  console.log('wrote', webp);
}
await browser.close();
