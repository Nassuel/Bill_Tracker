import json
import threading
from datetime import datetime
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from scrapers.alderwood import AlderwoodScraper
from scrapers.axiom import AxiomScraper
from scrapers.insurance import InsuranceScraper
from scrapers.king_county import KingCountyScraper
from scrapers.pse_gas import PSEGasScraper
from scrapers.rocket_loans import RocketLoansScraper
from scrapers.snohomish_pud import SnohomishPUDScraper
from scrapers.waste_management import WasteManagementScraper
from scrapers.wsecu import WSECUScraper

app = FastAPI(title="Bill Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SCRIPT_DIR = Path(__file__).parent
DATA_FILE = SCRIPT_DIR.parent / "data" / "bills.json"

SCRAPERS: dict = {
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

# Module-level state — safe for single-worker local use.
_state: dict = {"running": False, "provider": None, "error": None}
_lock = threading.Lock()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/bills")
def get_bills():
    if not DATA_FILE.exists():
        return {"bills": [], "last_scraped": None}
    return json.loads(DATA_FILE.read_text())


@app.get("/status")
def get_status():
    return _state


@app.get("/providers")
def list_providers():
    return {"providers": list(SCRAPERS.keys())}


@app.post("/scrape")
def trigger_scrape_all(background_tasks: BackgroundTasks):
    with _lock:
        if _state["running"]:
            raise HTTPException(409, "A scraping job is already running")
        _state["running"] = True
        _state["provider"] = "all"
        _state["error"] = None
    background_tasks.add_task(_run_all)
    return {"message": "Scraping all providers started in background"}


@app.post("/scrape/{provider_id}")
def trigger_scrape_one(provider_id: str, background_tasks: BackgroundTasks):
    if provider_id not in SCRAPERS:
        raise HTTPException(404, f"Provider '{provider_id}' not found. "
                            f"Available: {list(SCRAPERS.keys())}")
    with _lock:
        if _state["running"]:
            raise HTTPException(409, "A scraping job is already running")
        _state["running"] = True
        _state["provider"] = provider_id
        _state["error"] = None
    background_tasks.add_task(_run_one, provider_id)
    return {"message": f"Scraping {provider_id} started in background"}


# ── Background workers ────────────────────────────────────────────────────────

def _load_existing() -> dict:
    if DATA_FILE.exists():
        data = json.loads(DATA_FILE.read_text())
        return {b["id"]: b for b in data.get("bills", [])}
    return {}


def _save(bills: list) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(
        {"bills": bills, "last_scraped": datetime.now().isoformat()},
        indent=2,
    ))


def _run_all() -> None:
    existing = _load_existing()
    for provider_id, ScraperClass in SCRAPERS.items():
        _state["provider"] = provider_id
        try:
            with ScraperClass() as scraper:
                bill = scraper.scrape()
            existing[bill.id] = bill.to_dict()
        except Exception as e:
            existing[provider_id] = {
                "id": provider_id,
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }
    _save(list(existing.values()))
    _state.update({"running": False, "provider": None, "error": None})


def _run_one(provider_id: str) -> None:
    existing = _load_existing()
    try:
        with SCRAPERS[provider_id]() as scraper:
            bill = scraper.scrape()
        existing[bill.id] = bill.to_dict()
    except Exception as e:
        _state["error"] = str(e)
    _save(list(existing.values()))
    _state.update({"running": False, "provider": None})
