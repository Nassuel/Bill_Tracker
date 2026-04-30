#!/usr/bin/env python3
"""CLI runner — scrapes bills and writes results to data/bills.json."""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SCRIPT_DIR = Path(__file__).parent
DATA_FILE = SCRIPT_DIR.parent / "data" / "bills.json"


def get_scrapers() -> dict:
    from scrapers.alderwood import AlderwoodScraper
    from scrapers.axiom import AxiomScraper
    from scrapers.insurance import InsuranceScraper
    from scrapers.king_county import KingCountyScraper
    from scrapers.pse_gas import PSEGasScraper
    from scrapers.rocket_loans import RocketLoansScraper
    from scrapers.snohomish_pud import SnohomishPUDScraper
    from scrapers.waste_management import WasteManagementScraper
    from scrapers.wsecu import WSECUScraper

    return {
        "pse_gas": PSEGasScraper,
        "waste_management": WasteManagementScraper,
        "snohomish_pud": SnohomishPUDScraper,
        "alderwood_wastewater": AlderwoodScraper,
        "king_county": KingCountyScraper,
        "axiom_pest": AxiomScraper,
        "rocket_loans": RocketLoansScraper,
        "wsecu_car": WSECUScraper,
        "insurance": InsuranceScraper,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bill Tracker Scraper")
    parser.add_argument(
        "provider",
        nargs="?",
        help="Provider ID to scrape (omit to scrape all)",
    )
    parser.add_argument("--list", action="store_true", help="List available provider IDs and exit")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window (useful for debugging)")
    args = parser.parse_args()

    SCRAPERS = get_scrapers()

    if args.list:
        print("\n".join(SCRAPERS.keys()))
        return

    if args.provider and args.provider not in SCRAPERS:
        print(f"Unknown provider: {args.provider}")
        print(f"Available: {', '.join(SCRAPERS.keys())}")
        sys.exit(1)

    headless = not args.no_headless
    providers = {args.provider: SCRAPERS[args.provider]} if args.provider else SCRAPERS

    existing: dict = {}
    if DATA_FILE.exists():
        data = json.loads(DATA_FILE.read_text())
        existing = {b["id"]: b for b in data.get("bills", [])}

    for provider_id, ScraperClass in providers.items():
        print(f"Scraping {provider_id}...", end=" ", flush=True)
        try:
            with ScraperClass(headless=headless) as scraper:
                bill = scraper.scrape()
            existing[bill.id] = bill.to_dict()
            if bill.error:
                print(f"ERROR: {bill.error}")
            elif bill.amount_due is not None:
                print(f"${bill.amount_due:.2f} due {bill.due_date or 'unknown'}")
            else:
                print("no data returned")
        except Exception as e:
            print(f"FAILED: {e}")

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(
        {"bills": list(existing.values()), "last_scraped": datetime.now().isoformat()},
        indent=2,
    ))
    print(f"\nSaved → {DATA_FILE}")


if __name__ == "__main__":
    main()
