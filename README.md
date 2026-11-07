# Smashed Burgers & Co.

Website for Smashed Burgers & Co., Kaloor Kadavanthra Road, Kochi.
Live: https://smashed-zeta.vercel.app

Plain static site. No build step, no framework, no npm install.

## Deploy on Vercel

1. Vercel project `smashed` (team maheshkadangod-1675s-projects) is connected to `maheshkadangod-oss/smashed`. Its public address is https://smashed-zeta.vercel.app
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

## Source of truth

The menu, prices, phone and address come from their own system at https://menu.smashed.in/
(SmashPOS). That page confirms the hours: 6 PM to 4 AM.

## How the menu stays current

Nobody has to edit prices on the website. Change them in SmashPOS and the site follows.

1. **Live, for visitors.** When someone opens the site, the page reads the menu straight from
   SmashPOS: prices, new items, bestsellers (★) and "Sold out tonight". If SmashPOS can't be
   reached, the menu baked into the page stays.
2. **Twice a day, for Google and AI search.** `.github/workflows/sync-menu.yml` runs
   `scripts/sync_menu.py` at 4 PM and midnight IST. It rewrites the baked-in menu, the menu
   and price answer in the structured data, the FAQ price answer and `llms.txt`, and commits
   only if something changed. Vercel redeploys on that commit.
   Run it any time: GitHub → Actions → Sync menu → Run workflow.

**Descriptions** don't exist in SmashPOS, so they live in `menu-notes.json`, keyed by item name
in lower case. New items show name and price until a description is added there. The same file
holds section names and notes.

The browser (`buildMenu` / `renderMenu` in `index.html`) and the script (`build_model` /
`render` in `scripts/sync_menu.py`) follow the same rules. Change both together.

GitHub pauses scheduled jobs in a public repo after 60 days with no commits. The job's own
commits count, but if the menu doesn't change for two months, re-enable it in the Actions tab.

## Still to confirm with the owner

- Which poster photos are Jammin' Bacon and The Alchemy.
- Descriptions for Double Smoke, Double Bacon Cheese Burger, Patty Melt and Cheese Loaded
  (their live menu lists name and price only).
