# Safha brand

- **App name** (under the icon): Safha
- **Play Store name:** Safha: Quran Hifz & Hadith
- **Icon:** `safha-icon.svg`, the "Night" design from the app's Contemplative
  Night theme: an ivory mosque behind an amber open book on an ember glow.

`node branding/render_icons.cjs` renders every size from the SVG (it uses the
Playwright Chromium on the dev machine):

- Android: `mipmap-*/ic_launcher.png` (legacy, rounded) and the adaptive
  layers `ic_launcher_background`, `ic_launcher_foreground`,
  `ic_launcher_monochrome` (themed icons), wired up in
  `mipmap-anydpi-v26/ic_launcher.xml`. The mark is scaled into the 66dp safe
  circle so no launcher mask cuts it.
- iOS: every file in `AppIcon.appiconset`, opaque.
- `play-store-icon-512.png` for the Play Console, `safha-icon-1024.png` as
  the master bitmap.

Package / bundle ID: `com.aiquranic.safha` on Android and iOS (the preview
and mic-test builds add `.uipreview` and `.micpilot`). It changed from
`com.qari.app` before the Play Store launch, so the current test installs
do not update in place: uninstall the old app once.
