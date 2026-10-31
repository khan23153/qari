# aiquranic.com

The landing site for Safha (formerly Qari): static HTML, CSS and JavaScript in `public/`,
with no build step. The edge Caddy (`infra/Caddyfile.edge`) serves
`public/` at the site root; `/v1/*`, `/ws/*` and `/health` still go to the
API, and `/download` redirects to `/v1/app/download`.

## Deploy

1. Pull this branch into the checkout the edge Caddy reads
   (default `/home/innocent/qari/website/public`; set `QARI_WEBSITE_DIR`
   in Caddy's environment if the checkout, or a container mount, is
   elsewhere).
2. Reload Caddy: `caddy reload --adapter caddyfile --config infra/Caddyfile.edge`
   (or restart the `qari-edge` service).

## What is in it

- `public/assets/mushaf.js` draws Mushaf pages from `public/data/pages.json`
  the way the app does: words on their printed lines, KFGQPC ayah
  medallions, surah banners and basmala, tajweed colours from the app's
  own maps, and Hifz mode that hides words but keeps every marker.
- `public/assets/img/page-*.webp` are renders of that same engine.
- Fonts are self-hosted: STIX Two Text (OFL, from @fontsource) and the
  app's KFGQPC Uthmanic Hafs file, served unmodified as its licence
  requires.
- GSAP, ScrollTrigger and Lenis are vendored in `public/assets/vendor/`.
  With `prefers-reduced-motion` none of the motion runs.

## Rebuilding the data and pictures

```bash
python3 website/tools/build_site_data.py           # pages.json from mobile/assets
python3 -m http.server 8765 --directory website &  # serve website/ locally
node website/tools/render_pages.mjs                # page renders (Playwright)
```

## Look

The site follows the app's own "Serene Path" theme
(`mobile/lib/core/theme/serene_decorations.dart` and `app_theme.dart`):
warm cream, bronze ink and amber, the soft radial glow and mosque
silhouette, with an eight-point star as the ornament between sections.
