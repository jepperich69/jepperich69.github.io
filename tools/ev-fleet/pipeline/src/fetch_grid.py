"""Annual CO2 intensity of Danish grid electricity from Energinet's Energi Data Service.

Usage: python src/fetch_grid.py [first_year] [last_year]
Output: Data/raw/grid_co2_annual.json  {year: {"g_per_kWh": mean, "hours": n}}

Dataset DeclarationGridEmission (environmental declaration, average grid mix incl. distribution,
excl. self-consumption), FuelAllocationMethod "125%" (the Danish standard declaration), CO2PerkWh
in g/kWh. Annual value = simple mean over hours and the two price areas DK1, DK2 (not weighted by
consumption). Stdlib only. Energinet rate-limits; a 429 is waited out as the message says.
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Data" / "raw" / "grid_co2_annual.json"
URL = "https://api.energidataservice.dk/dataset/DeclarationGridEmission"


def get(params: dict) -> dict:
    url = URL + "?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code == 429:
                m = re.search(r"(\d+) seconds", body)
                wait = int(m.group(1)) + 5 if m else 300
                print(f"rate limited, waiting {wait}s", flush=True)
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("too many retries")


def annual_means(y0: int, y1: int) -> dict:
    """One request for all years (the API rate-limits per call), then annual means."""
    d = get({"start": f"{y0}-01-01T00:00", "end": f"{y1 + 1}-01-01T00:00", "limit": 0,
             "filter": json.dumps({"FuelAllocationMethod": ["125%"]}),
             "columns": "HourUTC,PriceArea,CO2PerkWh"})
    acc: dict[int, list] = {}
    for r in d.get("records", []):
        if r.get("CO2PerkWh") is not None:
            acc.setdefault(int(r["HourUTC"][:4]), []).append(r["CO2PerkWh"])
    return {y: {"g_per_kWh": round(sum(v) / len(v), 2), "hours": len(v) // 2} for y, v in sorted(acc.items())}


def main(argv=None) -> int:
    a = argv if argv is not None else sys.argv[1:]
    y0, y1 = (int(a[0]), int(a[1])) if len(a) == 2 else (2015, 2025)
    res = annual_means(y0, y1)
    for y, r in res.items():
        print(y, r, flush=True)
    if not res:
        print("no data returned")
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps({str(k): v for k, v in res.items()}, indent=1), "utf-8")
    tmp.replace(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
