# My LEGO Shop — Client-side MVP

This is a small, client-only web app that lets you load your LEGO inventory from a spreadsheet (CSV or Excel) in the browser, list items, and create an order CSV you can use to process sales manually or import into another system.

What I added
- `index.html` — main single-page app UI
- `styles.css` — small styling overrides
- `app.js` — logic to parse CSV/XLSX, render products, manage cart, and export orders
- `app.js` — logic to parse CSV/XLSX, render products, manage cart, and export orders. Product thumbnails are auto-filled from `rebrickable_cache.json` when available (fetched from Rebrickable earlier).

How it works (quick)
1. Open `index.html` in your browser (double-click or use a local static server).
2. Click the file input and choose your CSV or XLSX file. The page accepts files with these columns (case-insensitive):
   - `id`, `title`, `description`, `price`, `quantity`, `imageUrl`, `condition`
   - Common alternate names like `sku`, `qty`, `img` are also recognized.
3. The app will render your items. Click "Add" to put items in the cart.
4. Click "Export order CSV" to download a CSV containing your order (id, title, unit_price, qty, line_total).

Notes & assumptions
- This is intentionally client-only to keep it simple and to let you try the flow quickly. There is no server, no authentication, and no payment integration.
- Cart is stored in `localStorage` as `lego_cart_v1`.
- Prices are parsed heuristically; make sure your price column contains numbers (e.g. `12.50`).
- If you want to publish this as a real store (accept payments, inventory sync, shipping), see "Next steps" below.

Next steps (recommended)
- Integrate a payment provider (Stripe, PayPal): requires a server to create secure payment intents.
- Move inventory to a small backend (Node/Express + SQLite or a simple headless CMS) so you can update listings and track stock.
- Add product pages, photos hosting (S3 or a CDN), and shipping calculation.

How to run locally (simple)
1. Open `index.html` in your browser.
   - For full browser compatibility you can run a tiny static server (recommended):

```bash
# from the `lego` folder
python3 -m http.server 8000
# then open http://localhost:8000 in your browser
```

Feedback & customization
- If you upload a sample of your spreadsheet (or paste a few rows), I can adapt the importer to your exact column names and add fields (condition mapping, images, etc.).
- I can also add a server-backed checkout and payment wiring if you want to accept payments online.

Enjoy — and send your spreadsheet if you want me to map your columns automatically.
