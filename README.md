# Bill Tracker

A personal household bill dashboard that uses Selenium to scrape utility and financial account websites, storing results
in a shared JSON file served by a Next.js + shadcn/ui dashboard.

---

## Architecture

```
scraper/   Python + Selenium scrapers → data/bills.json
dashboard/ Next.js 15 + shadcn/ui    ← reads data/bills.json via API routes
```

The scraper can run as a CLI (one-shot) or as a FastAPI server (triggered by the Refresh button in the UI).

---

## Providers

| Provider                        | Category    | Portal                        | Approach                            |
|---------------------------------|-------------|-------------------------------|-------------------------------------|
| Puget Sound Energy              | Gas         | pse.com                       | Selenium                            |
| Waste Management                | Trash       | wm.com                        | Selenium auth → api.wm.com REST API |
| Snohomish PUD                   | Electric    | my.snopud.com                 | Selenium                            |
| Alderwood Water & Wastewater    | Water       | awwd.com                      | Selenium                            |
| King County Capacity Charge     | Water/Sewer | payment.kingcounty.gov        | Selenium                            |
| Axiom Pest Control              | Pest        | axiom.pestportals.com         | Selenium                            |
| Rocket Loans                    | Mortgage    | servicing.rocketloans.com     | Selenium                            |
| WSECU                           | Car Payment | my.wsecu.org                  | Selenium                            |
| Car & Home Insurance (umbrella) | Insurance   | _(set `INSURANCE_LOGIN_URL`)_ | Selenium                            |

> Adding a new provider: create a new file in `scraper/scrapers/`, register it in both `scraper/api.py` and
`scraper/main.py`, and add its credentials to `.env`.

---

## Setup

### 1. Credentials

```bash
cp .env.example .env
# Open .env and fill in usernames/passwords for each provider
```

**King County** is different — set `KING_COUNTY_USERNAME` to your **account number** and `KING_COUNTY_PASSWORD` to your
**site number** (both found on your invoice).

**Insurance** — set `INSURANCE_LOGIN_URL` to your insurer's login page URL, then update the selectors in
`scraper/scrapers/insurance.py`.

**Waste Management API** (optional) — after logging in to wm.com, open DevTools → Network, find any `/api/` request, and
copy the `ClientId` header value into `WM_CLIENT_ID` in `.env`. Without this, the scraper falls back to reading the
balance from the page directly.

### 2. Python scraper

```bash
cd scraper
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e .
```

Run a single provider (visible browser, good for debugging selectors):

```bash
bill-tracker pse_gas --no-headless
```

Run all providers headlessly and save to `data/bills.json`:

```bash
bill-tracker
```

List available provider IDs:

```bash
bill-tracker --list
```

### 3. Dashboard

```bash
cd dashboard
npm install
cp .env.local.example .env.local
npm run dev   # http://localhost:3000
```

### 4. API server (enables the Refresh button in the UI)

In a separate terminal:

```bash
cd scraper
uvicorn api:app --reload   # http://localhost:8000
```

Click **Refresh All** in the dashboard to trigger scraping and watch the table update automatically.

---

## Updating scrapers

Every scraper ships with `TODO` comments where site-specific CSS selectors need to be set. The sites' HTML may change
over time. To fix a broken scraper:

1. Run it with `--no-headless` so you can see the browser
2. Open Chrome DevTools → Elements and find the correct selector for the login fields, balance, and due date
3. Update the selector strings in the corresponding `scraper/scrapers/*.py` file

---

## Project structure

```
Bill_Tracker/
├── .env.example                  # credential template — copy to .env
├── data/
│   └── bills.json                # scraped bill data (gitignored)
├── scraper/
│   ├── pyproject.toml
│   ├── main.py                   # CLI runner
│   ├── api.py                    # FastAPI server (for UI refresh)
│   └── scrapers/
│       ├── base.py               # Selenium base class + BillData dataclass
│       ├── alderwood.py
│       ├── axiom.py
│       ├── insurance.py
│       ├── king_county.py
│       ├── pse_gas.py
│       ├── rocket_loans.py
│       ├── snohomish_pud.py
│       ├── waste_management.py
│       └── wsecu.py
└── dashboard/
    ├── app/
    │   ├── page.tsx              # main dashboard page
    │   ├── layout.tsx
    │   └── api/
    │       ├── bills/route.ts    # reads data/bills.json
    │       ├── scrape/route.ts   # triggers Python scraper API
    │       └── status/route.ts   # polls scraping progress
    ├── components/
    │   ├── ui/                   # shadcn/ui components
    │   ├── bills-table.tsx
    │   ├── spending-chart.tsx
    │   ├── stat-card.tsx
    │   └── refresh-button.tsx
    ├── types/bill.ts
    └── lib/utils.ts
```

---

## Tech stack

| Layer         | Tech                                              |
|---------------|---------------------------------------------------|
| Scraping      | Python 3, Selenium 4, webdriver-manager           |
| Scraper API   | FastAPI + Uvicorn                                 |
| Frontend      | Next.js 15, React 19, TypeScript                  |
| UI components | shadcn/ui (Tailwind v3 + Radix primitives)        |
| Charts        | Recharts                                          |
| Data store    | `data/bills.json` (flat file, no database needed) |
