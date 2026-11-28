"""Tax revenue forgone and CO2 avoided by BEVs, against a counterfactual with no BEVs.

Usage: python src/fiscal.py      -> Data/fits/fiscal.json

Counterfactual: every BEV sold and on the road is a petrol car instead, driven the same km.
Gap per BEV, all in 2026 kr., state taxes excl. VAT:
  one-off, per BEV sold in year y:  reg_ice - reg_bev(y)                      (registration tax)
  annual, per BEV on the road:      km * fuel_tax / km_per_l                  (petrol energy + CO2 + NOx tax)
                                    + owner_ice - owner_bev                   (CO2 ownership tax)
                                    - km * kwh_per_km * el_tax                (tax on charging power)
CO2 avoided per BEV and year, tonnes:
  national basis (Danish non-ETS target): km / km_per_l * co2_per_l           (tailpipe)
  physical basis: tailpipe - km * kwh_per_km * grid_g_per_kWh                 (grid CO2 counted)
Budget cost per tonne = tax gap / CO2 avoided (a transfer to car owners, not an abatement cost),
per sales cohort over the car life, as SKM does: (reg gap + life * annual gap) / (life * annual CO2),
undiscounted. Dividing the gap to date by the CO2 to date would overstate it, because the one-off
registration tax covers savings over the whole life.

Two blocks (user decision 2026-11-28):
  observed  2015..last full year: actual BEV sales and stocks (BIL51/BIL52 panel), rates below.
  scenario  next year..2040: the fleet forecast (Data/fits/simulation.npz) under rules frozen at
            2026 law; an illustration of size, not a forecast (rules change, e.g. FL26, the
            November 2026 fuel-tax proposal). Bands = fleet uncertainty only.
Every parameter carries its source or is marked as an assumption (PARAMS[...]["src"]).
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dst  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIRST, HORIZON = 2015, 2040
RULE_YEAR = 2026     # the frozen rules; observed years from here on use the RULE_YEAR BEV registration tax


def rule_year_sales(b: dict, sales: np.ndarray, yrs: np.ndarray) -> np.ndarray:
    """BEV sales in RULE_YEAR per draw: observed if the year is complete, else observed months +
    forecast months. (Before 2026-11-28 a complete 2026 gave 0 -> division error -> no fiscal block.)"""
    if RULE_YEAR in b["years"]:
        return np.full(sales.shape[0], float(b["sales"][b["years"].index(RULE_YEAR)]))
    part = b["partial"].get(RULE_YEAR, {"months": 0, "sales": 0})
    s = part["sales"] + sales[:, yrs == RULE_YEAR].sum(1)
    if part["months"] + int((yrs == RULE_YEAR).sum()) != 12:
        raise ValueError(f"{RULE_YEAR} is neither complete nor covered by observed + forecast months")
    return s

PARAMS = {
    "km": {"v": 13_600, "src": "SKM (Dec 2025) Regnemetode ved afgiftsaendringer for personbiler, p.5: "
           "13,600 km/yr for non-diesel cars (DST traffic work / stock)"},
    "fuel_tax_petrol": {"v": 5.363, "src": "SKM (Dec 2025) p.4: petrol 2026 energy 349.2 + CO2 186.1 + NOx 1.0 "
                        "oere/l = 536.3 oere/l excl. VAT; indexed to net prices"},
    "owner_ice": {"v": 1_520, "src": "SKM (Dec 2025) p.3: petrol car at 130 g/km pays 760 kr per half-year (2026)"},
    "owner_bev": {"v": 920, "src": "SKM (Dec 2025) p.3: BEV pays the lowest rate, 460 kr per half-year (2026)"},
    "el_tax": {"v": 0.004, "src": "SKM (Dec 2025) p.4: 0.4 oere/kWh with the charging refund scheme (to 2030); "
               "home charging without an operator subscription pays full electricity tax (ignored)"},
    "reg_ice_2020": {"v": 97_500, "src": "UNVERIFIED (search snippet; ft.dk blocks automated fetch) Folketing SAU alm.del 2019-20 spm. 734: average registration tax of "
                     "conventional cars 97,500 kr (2020 rules, 2020 kr.)"},
    "reg_bev_2020": {"v": 3_000, "src": "same answer: average for BEVs about 3,000 kr; used for 2015-2025 "
                     "(BEV sales before 2020 were small)"},
    "reg_bev_2026_total": {"v": 2.6e9, "src": "Skatteministeren via DR: abolishing BEV registration tax costs "
                           "about 2.6 bn kr in 2026 -> per BEV = 2.6 bn / BEV sales 2026 (date of answer unverified)"},
    "km_per_l": {"v": 16.0, "src": "ASSUMPTION: real-world petrol car, 6.25 l/100 km; range 14-19"},
    "kwh_per_km": {"v": 0.18, "src": "ASSUMPTION: BEV incl. charging losses; range 0.15-0.21"},
    "life": {"v": 15, "src": "SKM (Dec 2025) p.4: assumed car life of 15 years (cohort calculations)"},
    "co2_per_l": {"v": 2.25, "src": "ASSUMPTION: petrol E10, ~2.37 kg/l fossil petrol less ~5% bio share"},
}
P = {k: v["v"] for k, v in PARAMS.items()}


def bev_by_year(path: Path = ROOT / "Data" / "panels" / "fuel4_monthly.csv") -> dict:
    """Annual BEV sales and mean stock (average of the monthly end-of-month stocks)."""
    sales, stock = defaultdict(int), defaultdict(list)
    for r in csv.DictReader(path.open(encoding="utf-8")):
        if r["fuel4"] != "BEV":
            continue
        y = int(r["month"][:4])
        sales[y] += int(r["new_reg"])
        stock[y].append(int(r["stock"]))
    full = sorted(y for y in stock if len(stock[y]) == 12)
    return {"years": full, "sales": [sales[y] for y in full], "stock": [float(np.mean(stock[y])) for y in full],
            "partial": {y: {"months": len(stock[y]), "sales": sales[y]} for y in stock if len(stock[y]) < 12}}


def cpi_annual() -> dict:
    rows = dst.fetch("PRIS113", {"TYPE": ["INDEKS"], "Tid": ["*"]})
    acc = defaultdict(list)
    for r in rows:
        if r["INDHOLD"] is not None:
            acc[int(r["TID"][:4])].append(r["INDHOLD"])
    return {y: float(np.mean(v)) for y, v in acc.items() if len(v) == 12}


def grid() -> dict:
    p = ROOT / "Data" / "raw" / "grid_co2_annual.json"
    d = json.loads(p.read_text("utf-8")) if p.exists() else {}
    return {int(k): v["g_per_kWh"] for k, v in d.items()}


def per_bev(p: dict, reg_bev: float, g_kwh: float) -> dict:
    """Gap and CO2 per BEV: one-off registration gap, annual tax gap, annual tonnes CO2."""
    litres = p["km"] / p["km_per_l"]
    kwh = p["km"] * p["kwh_per_km"]
    fuel = litres * p["fuel_tax_petrol"]
    owner = p["owner_ice"] - p["owner_bev"]
    el = kwh * p["el_tax"]
    tail = litres * p["co2_per_l"] / 1000
    return {"reg": p["reg_ice"] - reg_bev, "fuel": fuel, "owner": owner, "el": -el,
            "annual": fuel + owner - el, "co2_national": tail, "co2_physical": tail - kwh * g_kwh / 1e6}


def run(panels: Path = ROOT / "Data" / "panels", fits: Path = ROOT / "Data" / "fits", p: dict | None = None) -> dict:
    p = dict(P if p is None else p)
    cpi = cpi_annual()
    base = max(cpi)                                   # latest full CPI year (2026 rates are close to it)
    p["reg_ice"] = p["reg_ice_2020"] * cpi[base] / cpi[2020]
    reg_bev_obs = p["reg_bev_2020"] * cpi[base] / cpi[2020]
    g = grid()
    b = bev_by_year(panels / "fuel4_monthly.csv")
    out = {"params": PARAMS, "price_base": f"{base} CPI (2026 tax rates)", "reg_ice": round(p["reg_ice"]),
           "grid_g_per_kWh": g, "observed": [], "scenario": []}
    cum = defaultdict(float)
    z = np.load(fits / "simulation.npz")
    months = [str(m) for m in z["months"]]
    yrs = np.array([int(m[:4]) for m in months])
    stock, sales = z["stock_BEV"].astype(float), z["sales_BEV"].astype(float)
    reg_bev_26 = p["reg_bev_2026_total"] / float(np.median(rule_year_sales(b, sales, yrs)))
    reg_bev_y = lambda y: reg_bev_obs if y < RULE_YEAR else reg_bev_26
    for y, n_s, n_x in zip(b["years"], b["sales"], b["stock"]):
        if y < FIRST:
            continue
        gy = g.get(y, g[min(g)] if g and y < min(g) else (g[max(g)] if g else 0.0))
        e = per_bev(p, reg_bev_y(y), gy)
        row = {"year": y, "bev_sales": n_s, "bev_stock_mean": round(n_x),
               "reg_gap_mkr": n_s * e["reg"] / 1e6, "fuel_gap_mkr": n_x * e["fuel"] / 1e6,
               "owner_gap_mkr": n_x * e["owner"] / 1e6, "el_tax_mkr": n_x * e["el"] / 1e6,
               "co2_national_kt": n_x * e["co2_national"] / 1e3, "co2_physical_kt": n_x * e["co2_physical"] / 1e3,
               "grid_g_per_kWh": gy}
        row["total_gap_mkr"] = row["reg_gap_mkr"] + row["fuel_gap_mkr"] + row["owner_gap_mkr"] + row["el_tax_mkr"]
        for k in ("total_gap_mkr", "co2_national_kt", "co2_physical_kt"):
            cum[k] += row[k]
        out["observed"].append({k: (round(v, 1) if isinstance(v, float) else v) for k, v in row.items()})
    for r in out["observed"]:                      # lifetime cost per tonne for the year's sales cohort
        e = per_bev(p, reg_bev_y(r["year"]), r["grid_g_per_kWh"])
        L = p["life"]
        r["cohort_kr_per_t_national"] = round((e["reg"] + L * e["annual"]) / (L * e["co2_national"]))
        r["cohort_kr_per_t_physical"] = round((e["reg"] + L * e["annual"]) / (L * e["co2_physical"]))
    out["observed_cumulative"] = {
        "years": f"{FIRST}-{b['years'][-1]}", "gap_bn_kr": round(cum["total_gap_mkr"] / 1e3, 2),
        "co2_national_mt": round(cum["co2_national_kt"] / 1e3, 3), "co2_physical_mt": round(cum["co2_physical_kt"] / 1e3, 3),
        "to_date_kr_per_t_national_not_comparable": round(cum["total_gap_mkr"] * 1e6 / (cum["co2_national_kt"] * 1e3)),
        "to_date_kr_per_t_physical_not_comparable": round(cum["total_gap_mkr"] * 1e6 / (cum["co2_physical_kt"] * 1e3))}

    # scenario: frozen 2026 rules on the fleet forecast
    g_frozen = g[max(g)] if g else 0.0
    e = per_bev(p, reg_bev_26, g_frozen)
    out["scenario_reg_bev_2026"] = round(reg_bev_26)
    L = p["life"]
    out["scenario_cohort_kr_per_t"] = {
        "national": round((e["reg"] + L * e["annual"]) / (L * e["co2_national"])),
        "physical": round((e["reg"] + L * e["annual"]) / (L * e["co2_physical"]))}
    cum_gap, cum_co2n, cum_co2p = 0.0, 0.0, 0.0
    for y in range(max(b["years"][-1], RULE_YEAR) + 1, HORIZON + 1):
        m = yrs == y
        if m.sum() != 12:
            continue
        gap = (sales[:, m].sum(1) * e["reg"] + stock[:, m].mean(1) * e["annual"]) / 1e9
        co2n = stock[:, m].mean(1) * e["co2_national"] / 1e6
        co2p = stock[:, m].mean(1) * e["co2_physical"] / 1e6
        cum_gap, cum_co2n, cum_co2p = cum_gap + gap, cum_co2n + co2n, cum_co2p + co2p
        q = lambda x: [round(float(v), 3) for v in np.quantile(x, [0.05, 0.5, 0.95])]
        out["scenario"].append({"year": y, "gap_bn_kr": q(gap), "co2_national_mt": q(co2n), "co2_physical_mt": q(co2p),
                                "cum_gap_bn_kr": q(cum_gap), "cum_co2_national_mt": q(cum_co2n)})
    return out


def app_block(sim: dict, panels: Path, n_draws: int = 200) -> dict:
    """Inputs for the app's adjustable tax/CO2 panel: defaults, observed BEV sales and mean
    stock by year, and per-draw scenario paths (sales, mean stock) for the frozen-rules years."""
    cpi = cpi_annual()
    base = max(cpi)
    g = grid()
    b = bev_by_year(panels / "fuel4_monthly.csv")
    yrs_obs = [y for y in b["years"] if y >= FIRST]
    months = sim["months"]
    yrs = np.array([int(m[:4]) for m in months])
    stock, sales = sim["stock"]["BEV"][:n_draws], sim["sales"]["BEV"][:n_draws]
    s26 = rule_year_sales(b, sales, yrs)
    sc_years = [y for y in range(max(b["years"][-1], RULE_YEAR) + 1, HORIZON + 1) if (yrs == y).sum() == 12]
    defaults = {k: v["v"] for k, v in PARAMS.items()}
    defaults["reg_ice"] = round(P["reg_ice_2020"] * cpi[base] / cpi[2020], -2)
    defaults["reg_bev_obs"] = round(P["reg_bev_2020"] * cpi[base] / cpi[2020], -2)
    defaults["reg_bev_2026"] = round(P["reg_bev_2026_total"] / float(np.median(s26)), -2)
    defaults["grid_g_per_kWh"] = g[max(g)] if g else None
    return {
        "price_base": base, "rule_year": RULE_YEAR,
        "defaults": {k: v for k, v in defaults.items() if k not in ("reg_ice_2020", "reg_bev_2020", "reg_bev_2026_total")},
        "sources": {k: v["src"] for k, v in PARAMS.items()},
        "observed": {"years": yrs_obs,
                     "sales": [s_ for y, s_ in zip(b["years"], b["sales"]) if y >= FIRST],
                     "stock": [round(x) for y, x in zip(b["years"], b["stock"]) if y >= FIRST],
                     "grid": [g.get(y, g[min(g)] if y < min(g) else g[max(g)]) if g else None for y in yrs_obs]},
        "scenario": {"years": sc_years,
                     "sales": [[int(round(float(v))) for v in sales[:, yrs == y].sum(1)] for y in sc_years],
                     "stock": [[int(round(float(v))) for v in stock[:, yrs == y].mean(1)] for y in sc_years]},
    }


def main() -> int:
    out = run()
    path = ROOT / "Data" / "fits" / "fiscal.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, indent=1, allow_nan=False), "utf-8")
    tmp.replace(path)
    for r in out["observed"]:
        print(r["year"], f"gap {r['total_gap_mkr']:8.0f} mkr (reg {r['reg_gap_mkr']:7.0f}, fuel {r['fuel_gap_mkr']:6.0f}, "
              f"owner {r['owner_gap_mkr']:4.0f})  CO2 nat {r['co2_national_kt']:6.0f} kt, phys {r['co2_physical_kt']:6.0f} kt  "
              f"cohort kr/t {r['cohort_kr_per_t_national']:6d} / {r['cohort_kr_per_t_physical']:6d}  grid {r['grid_g_per_kWh']}")
    print(out["observed_cumulative"])
    print("scenario: reg tax per BEV 2026", out["scenario_reg_bev_2026"], "cohort kr/t", out["scenario_cohort_kr_per_t"])
    for r in out["scenario"][::3]:
        print(r["year"], r["gap_bn_kr"], r["co2_national_mt"], r["cum_gap_bn_kr"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
