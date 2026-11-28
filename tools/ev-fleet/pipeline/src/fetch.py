"""Build tidy panels for the EV fleet model from Statistics Denmark.

Usage:
    python src/fetch.py                 # refresh cache where DST has updated, rebuild panels
    python src/fetch.py --offline       # rebuild panels from cache only
    python src/fetch.py --out DIR       # panel directory (default: Data/panels)

Outputs (CSV, one row per key):
    monthly_fuel.csv   month, driv, new_reg (BIL51), stock (BIL52)          2011-01 ->
    stock_bil54.csv    month, driv, stock (BIL54, passenger cars, all DK)   2018-01 ->
    age_fuel.csv       year, driv, age, stock (BIL21, stock at 1 January)  2011 ->
    population.csv     year, adults (18+ at 1 January), source  BEF5 1990 -> , then the
                       newest FRDK1yy projection for later years
    fuel4_monthly.csv  month, fuel4, new_reg, stock    (BEV/PHEV/petrol/diesel/other)
    manifest.json      table update stamps, coverage, checks

Fuel codes (DRIV) differ between tables: BIL51/52 code plug-ins as hybrid/petrol (20233)
and hybrid/diesel (20234); BIL21/54 use 'Pluginhybrid' (20232). FUEL4 maps all of them.
Total (20200) is kept in the raw panels and used as a check, never summed into FUEL4.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dst import Cache, latest_table  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TOTAL = "20200"
FUEL4 = {
    "20225": "BEV",
    "20232": "PHEV",   # BIL21/BIL54 'Pluginhybrid'
    "20233": "PHEV",   # BIL51/BIL52 'Hybrid/petrol' (tracks BIL54 plug-ins; see DESIGN.md open items)
    "20234": "PHEV",   # BIL51/BIL52 'Hybrid/diesel'
    "20205": "petrol",
    "20210": "diesel",
}
FUEL4_ORDER = ["BEV", "PHEV", "petrol", "diesel", "other"]
ADULT_AGE = 18
PROJECTION_PATTERN = r"FRDK1\d\d"   # 'Population projections 20yy for the country'


def fuel4(driv: str) -> str:
    return FUEL4.get(driv, "other")


def month_iso(tid: str) -> str:
    """'2026M10' -> '2026-10'."""
    y, m = tid.split("M")
    return f"{y}-{int(m):02d}"


def _age(code: str) -> int:
    """'17' -> 17, '105-' (105 and over) -> 105."""
    return int(code.rstrip("-+"))


def adults_by_year(rows: list[dict]) -> dict[int, int]:
    """Sum persons aged ADULT_AGE+ per year; other variables are eliminated in the query."""
    out: dict[int, int] = defaultdict(int)
    for r in rows:
        if _age(r["ALDER"]) >= ADULT_AGE:
            out[int(r["TID"])] += r["INDHOLD"] or 0
    return dict(out)


def population_panel(cache: Cache, offline: bool = False) -> tuple[list[dict], dict, dict]:
    """Adults 18+ at 1 January: observed (BEF5) then projected (newest FRDK1yy)."""
    obs_rows, m_obs = cache.get("BEF5", {"ALDER": ["*"], "Tid": ["*"]}, offline=offline)
    if offline:
        proj_id = max(p.name.split("_")[0] for p in cache.dir.glob("FRDK1*.meta.json"))
    else:
        proj_id = latest_table(PROJECTION_PATTERN)
    proj_rows, m_proj = cache.get(proj_id, {"ALDER": ["*"], "Tid": ["*"]}, offline=offline)
    obs, proj = adults_by_year(obs_rows), adults_by_year(proj_rows)
    last_obs = max(obs)
    rows = [{"year": y, "adults": obs[y], "source": "BEF5"} for y in sorted(obs)]
    rows += [{"year": y, "adults": proj[y], "source": proj_id} for y in sorted(proj) if y > last_obs]
    check = {"projection_table": proj_id, "last_observed": last_obs}
    if last_obs in proj:  # projection base year vs the observed count (should be ~0)
        check["base_year_rel_diff"] = round(proj[last_obs] / obs[last_obs] - 1, 5)
    return rows, m_obs, m_proj | {"check": check}


def build(cache: Cache, offline: bool = False) -> dict:
    get = lambda t, v: cache.get(t, v, offline=offline)  # noqa: E731
    reg, m51 = get("BIL51", {"EJER": ["1000"], "DRIV": ["*"], "Tid": ["*"]})
    stk, m52 = get("BIL52", {"EJER": ["1000"], "DRIV": ["*"], "Tid": ["*"]})
    s54, m54 = get("BIL54", {"OMRÅDE": ["000"], "BILTYPE": ["4000101002"], "BRUG": ["1000"],
                             "DRIV": ["*"], "Tid": ["*"]})
    age, m21 = get("BIL21", {"ALDER1": ["*"], "DRIV": ["*"], "Tid": ["*"]})
    pop_rows, m_bef, m_fr = population_panel(cache, offline=offline)

    # Duplicate DRIV codes would silently double-count; DST lists 'Ethanol' twice but with
    # distinct codes (20256, 20258), so key on (time, code) and assert uniqueness.
    monthly: dict[tuple[str, str], dict] = {}
    for rows, col in ((reg, "new_reg"), (stk, "stock")):
        seen = set()
        for r in rows:
            k = (month_iso(r["TID"]), r["DRIV"])
            assert k not in seen, f"duplicate {col} key {k}"
            seen.add(k)
            monthly.setdefault(k, {"month": k[0], "driv": k[1], "new_reg": None, "stock": None})[col] = r["INDHOLD"]
    monthly_rows = sorted(monthly.values(), key=lambda r: (r["month"], r["driv"]))

    bil54 = sorted(({"month": month_iso(r["TID"]), "driv": r["DRIV"], "stock": r["INDHOLD"]} for r in s54),
                   key=lambda r: (r["month"], r["driv"]))
    age_rows = sorted(({"year": int(r["TID"]), "driv": r["DRIV"], "age": r["ALDER1"], "stock": r["INDHOLD"]}
                       for r in age), key=lambda r: (r["year"], r["driv"], r["age"]))

    # fuel4 aggregation (excluding the total row) + check against the published total
    agg: dict[tuple[str, str], dict] = defaultdict(lambda: {"new_reg": 0, "stock": 0})
    totals: dict[str, dict] = {}
    for r in monthly_rows:
        if r["driv"] == TOTAL:
            totals[r["month"]] = r
            continue
        a = agg[(r["month"], fuel4(r["driv"]))]
        for c in ("new_reg", "stock"):
            a[c] += r[c] or 0
    fuel4_rows = [{"month": m, "fuel4": f, **v} for (m, f), v in agg.items()]
    fuel4_rows.sort(key=lambda r: (r["month"], FUEL4_ORDER.index(r["fuel4"])))

    checks = {"sum_vs_total_max_abs_diff": {}}
    for c in ("new_reg", "stock"):
        sums = defaultdict(int)
        for r in fuel4_rows:
            sums[r["month"]] += r[c]
        diffs = [abs(sums[m] - (totals[m][c] or 0)) for m in totals]
        checks["sum_vs_total_max_abs_diff"][c] = max(diffs) if diffs else None

    # PHEV coding check: BIL52 (20233+20234) vs BIL54 Pluginhybrid (20232), latest common month
    s52_phev = defaultdict(int)
    for r in monthly_rows:
        if r["driv"] in ("20233", "20234"):
            s52_phev[r["month"]] += r["stock"] or 0
    s54_phev = {r["month"]: r["stock"] for r in bil54 if r["driv"] == "20232"}
    common = sorted(set(s52_phev) & set(s54_phev))
    if common:
        m = common[-1]
        checks["phev_bil52_vs_bil54"] = {"month": m, "bil52_hybrid": s52_phev[m], "bil54_plugin": s54_phev[m]}
    checks["population"] = m_fr["check"]

    # BIL21 (1 January of year y) must equal the BIL52 December stock of y-1
    s21 = defaultdict(int)
    for r in age_rows:
        if r["driv"] == TOTAL and r["age"] != "IALT":
            s21[r["year"]] += r["stock"] or 0
    dec = {int(r["month"][:4]) + 1: r["stock"] for r in monthly_rows
           if r["driv"] == TOTAL and r["month"].endswith("-12")}
    both = sorted(set(s21) & set(dec))
    # Known: 2011-12 BIL52 total spikes +38k and reverts in 2012-01 (data glitch), so the
    # 2012 comparison fails; the model sample starts 2012-01 (DESIGN.md).
    checks["bil21_vs_bil52_dec_rel_diff_gt_0.1pct"] = {
        y: round(s21[y] / dec[y] - 1, 5) for y in both if abs(s21[y] / dec[y] - 1) > 0.001}

    months = [r["month"] for r in monthly_rows]
    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tables": {m["table"]: {"updated": m["updated"], "fetched_at": m["fetched_at"],
                                "from_cache": m.get("from_cache", True), "n_rows": m["n_rows"]}
                   for m in (m51, m52, m54, m21, m_bef, m_fr)},
        "coverage": {"monthly": [months[0], months[-1]],
                     "bil54": [bil54[0]["month"], bil54[-1]["month"]],
                     "age_fuel": [age_rows[0]["year"], age_rows[-1]["year"]],
                     "population": [pop_rows[0]["year"], pop_rows[-1]["year"]]},
        "checks": checks,
    }
    return {"monthly_fuel": monthly_rows, "stock_bil54": bil54, "age_fuel": age_rows,
            "fuel4_monthly": fuel4_rows, "population": pop_rows, "manifest": manifest}


def write_panels(panels: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in panels.items():
        if name == "manifest":
            (out / "manifest.json").write_text(json.dumps(rows, indent=2), "utf-8")
            continue
        with (out / f"{name}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--offline", action="store_true", help="use cache only, no network")
    ap.add_argument("--cache", type=Path, default=ROOT / "Data" / "raw")
    ap.add_argument("--out", type=Path, default=ROOT / "Data" / "panels")
    a = ap.parse_args(argv)
    panels = build(Cache(a.cache), offline=a.offline)
    write_panels(panels, a.out)
    man = panels["manifest"]
    print(json.dumps({"coverage": man["coverage"], "checks": man["checks"],
                      "from_cache": {t: v["from_cache"] for t, v in man["tables"].items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
