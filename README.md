# Smashed Burgers & Co.

Website for Smashed Burgers & Co., Kaloor Kadavanthra Road, Kochi.
Live: https://smashed-burgers-co.vercel.app

Plain static site. No build step, no framework, no npm install.

## Deploy on Vercel

1. Vercel → the `smashed-burgers-co` project → Settings → Git → connect `maheshkadangod-oss/smashed`
2. Settings → Build & Development:
   - Framework Preset: **Other**
   - Build Command: leave empty
   - Output Directory: leave empty (the repo root is the site)
3. Every push to `main` deploys automatically.

`vercel.json` sets caching and security headers. `404.html` is picked up by Vercel on its own.

## What's where

| Path | What it is |
|---|---|
| `index.html` | The whole page: markup, styles and scripts |
| `assets/seq/` | 168 frames of the smash, scrubbed by scroll at the top |
| `assets/fseq/` | 90 frames of their fryer footage for the tallow fries section |
| `assets/xseq/` | 82 frames of the exploded burger (generated with Gemini) |
| `assets/reel/` | 8 short loops for the sideways reel |
| `assets/video/` | Smoke behind the opening SMASHED, and the section loops |
| `assets/img/` | Menu photos, share image, icon |
| `llms.txt` | Plain fact sheet for AI search (ChatGPT, Perplexity, Claude) |
| `robots.txt`, `sitemap.xml` | Search engine files |

## Facts to keep in sync

Hours, address and menu appear in three places. Change all three together:
1. The visible text in `index.html`
2. The JSON-LD block in the `<head>` of `index.html` (the FAQ answers there must match the page word for word)
3. `llms.txt`

## Still to confirm with the owner

- Opening time: the poster says 6 PM, Zomato says 5:30 PM. The site says 6 PM.
- Which poster photos are Jammin' Bacon and The Alchemy.
- Whether to show prices.
