# MarketLink — Multi-Vendor Marketplace E-commerce Application

Coursework project: a Marketplace E-commerce Application built in **Python**
using the **Flet** framework (Flutter-powered), covering the Electronics /
general-goods niche. A single codebase runs on Desktop, Web, and Mobile.

Each product page includes **"Compare on Jumia / Konga / Jiji / Temu"**
buttons. These open that platform's own public search-results page for the
product name in a new browser tab — the app does **not** scrape or pull
live data from those sites (none of them publish a public product API, and
scraping would violate their Terms of Service). This keeps the feature
legal and reliable while still giving buyers a one-click way to
price-compare externally.

## Project structure

```
marketplace_app/
├── main.py             # Flet UI: all screens/views and navigation
├── database.py         # SQLite data-access layer + demo data seeding
├── external_links.py   # Builds Jumia/Konga/Jiji/Temu search-result URLs
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Run

```bash
python main.py                  # Desktop window
flet run --web main.py          # Web (SPA), opens in browser
```

On mobile, install the **Flet app** from the Play Store / App Store and
scan the QR code printed by `flet run`, or package a native build:

```bash
flet build apk       # Android
flet build ipa        # iOS (requires macOS + Xcode)
flet build windows    # Windows desktop
flet build macos       # macOS desktop
flet build linux       # Linux desktop
```

The first run creates `marketplace.db` (SQLite) in the project folder and
seeds it with demo users and 8 sample products.

## Demo accounts

| Role   | Email                     | Password  |
|--------|---------------------------|-----------|
| Buyer  | buyer@marketplace.test    | buyer123  |
| Seller | seller1@marketplace.test  | seller123 |
| Seller | seller2@marketplace.test  | seller123 |
| Admin  | admin@marketplace.test    | admin123  |

## Features implemented

- **Authentication** — register (buyer/seller) and login, salted-hash
  password storage.
- **Product management (seller)** — add, edit, delete listings; per-seller
  product list.
- **Browse & search (buyer)** — search by name, filter by category.
- **Product detail** — description, price, stock, and the four
  external "compare price" links.
- **Cart** — add/remove items, adjust quantity, running total.
- **Checkout** — creates an order, decrements stock, clears the cart.
- **Order management** — buyers see order history; sellers see incoming
  orders for their products and can update status
  (Pending → Processing → Shipped → Delivered / Cancelled).

## Notes for the coursework report

This code corresponds to the **Source Code** and, once run, the
**Screenshots** deliverables in the assignment table. Run the app locally
(`python main.py`) and capture screenshots of each screen listed above for
the report's screenshots section. The `Coursework_Report.docx` in this
submission covers the feasibility study, fact-finding, SRS, algorithms,
flowcharts, pseudocode, system/database design, and the testing evidence
table.
