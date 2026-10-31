// Renders every app icon from branding/safha-icon.svg with the preinstalled
// Playwright Chromium:  node branding/render_icons.cjs
//
// Writes the Android launcher icons (legacy + adaptive layers), the iOS
// AppIcon set, the Play Store icon and the website icons.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const svg = fs.readFileSync(path.join(__dirname, 'safha-icon.svg'), 'utf8');
const inner = svg.replace(/^[\s\S]*?<svg[^>]*>/, '').replace(/<\/svg>\s*$/, '');
const defs = inner.match(/<defs>[\s\S]*?<\/defs>/)[0];
const mark = inner.match(/<g id="mark">[\s\S]*<\/g>\s*(?=$)/)?.[0] ?? inner.slice(inner.indexOf('<g id="mark">'));

// Adaptive icons crop to a 66dp circle inside 108dp, so the mark is scaled
// into that safe zone; legacy and iOS icons keep it at full size.
// 0.72 keeps the book's corners and the minaret tops inside that circle.
const SAFE = 'translate(54 54) scale(0.72) translate(-54 -50.5)';
const doc = (body, size) =>
  `<!doctype html><html><body style="margin:0;background:transparent">` +
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108" width="${size}" height="${size}">${body}</svg></body></html>`;

const jobs = [];
const dens = { mdpi: 1, hdpi: 1.5, xhdpi: 2, xxhdpi: 3, xxxhdpi: 4 };
const res = path.join(root, 'mobile/android/app/src/main/res');
for (const [d, k] of Object.entries(dens)) {
  // Legacy launcher icon (pre-Android 8): rounded square, transparent corners.
  jobs.push([path.join(res, `mipmap-${d}/ic_launcher.png`), 48 * k,
    `${defs}<rect width="108" height="108" rx="24" fill="url(#glow)"/>${mark}`]);
  // Adaptive layers (Android 8+).
  jobs.push([path.join(res, `mipmap-${d}/ic_launcher_background.png`), 108 * k,
    `${defs}<rect width="108" height="108" fill="url(#glow)"/>`]);
  jobs.push([path.join(res, `mipmap-${d}/ic_launcher_foreground.png`), 108 * k,
    `<g transform="${SAFE}">${mark}</g>`]);
  // Themed (monochrome) layer for Android 13: only the alpha is used.
  jobs.push([path.join(res, `mipmap-${d}/ic_launcher_monochrome.png`), 108 * k,
    `<g transform="${SAFE}"><g fill="#fff"><path d="M41 50 A13 13 0 0 1 67 50 Z"/>` +
    `<rect x="32" y="24" width="5" height="26"/><circle cx="34.5" cy="24" r="4"/>` +
    `<rect x="71" y="24" width="5" height="26"/><circle cx="73.5" cy="24" r="4"/></g>` +
    `<path d="M52.5 52 C45 46.5 35 45.5 25 47.5 V82 C35 80.5 45 81.5 52.5 86.5 Z M55.5 52 C63 46.5 73 45.5 83 47.5 V82 C73 80.5 63 81.5 55.5 86.5 Z" fill="#fff"/></g>`]);
}

// iOS: full bleed, no transparency (iOS applies its own mask).
const ios = path.join(root, 'mobile/ios/Runner/Assets.xcassets/AppIcon.appiconset');
const contents = JSON.parse(fs.readFileSync(path.join(ios, 'Contents.json'), 'utf8'));
for (const img of contents.images) {
  const px = Math.round(parseFloat(img.size) * parseFloat(img.scale));
  jobs.push([path.join(ios, img.filename), px, inner, true]);
}

// Play Store (512, full bleed) and the website.
jobs.push([path.join(__dirname, 'play-store-icon-512.png'), 512, inner, true]);
jobs.push([path.join(__dirname, 'safha-icon-1024.png'), 1024, inner, true]);

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  for (const [out, size, body, opaque] of jobs) {
    await page.setViewportSize({ width: size, height: size });
    await page.setContent(doc(body, size));
    await page.locator('svg').screenshot({ path: out, omitBackground: !opaque });
    console.log(path.relative(root, out), size);
  }
  await browser.close();
})();
