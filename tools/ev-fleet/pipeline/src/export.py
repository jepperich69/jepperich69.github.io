"""Export one forecast vintage as the app's JSON, and archive it.

Usage:
    python src/export.py                                  # current panels + fits
    python src/export.py --panels DIR --fits DIR          # e.g. a past vintage rebuilt for comparison

Writes app/data/vintages/<YYYY-MM>.json (the archive, DESIGN.md decision 10) and
app/data/forecast.json = the newest vintage plus a "previous" block from the vintage before it,
which the app uses for the month-over-month +/- (DESIGN.md "Later" item 4).
Never writes if the simulation fails; writes are atomic.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fiscal  # noqa: E402
import simulate  # noqa: E402
from total import _write_atomic  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
APP_DATA = ROOT / "app" / "data"
FUELS = ["BEV", "PHEV", "petrol", "diesel"]
OBS_START = "2012-01"


def _r(x, k=0):
    return [round(float(v), k) if k else int(round(float(v))) for v in x]


def observed(panels: Path) -> dict:
    S, R = {}, {}
    for r in csv.DictReader((panels / "fuel4_monthly.csv").open(encoding="utf-8")):
        if r["month"] >= OBS_START:
            S.setdefault(r["month"], {})[r["fuel4"]] = int(r["stock"])
            R.setdefault(r["month"], {})[r["fuel4"]] = int(r["new_reg"])
    months = sorted(S)
    out = {"months": months, **{f: [S[m][f] for m in months] for f in FUELS + ["other"]}}
    out["sales_total"] = [sum(R[m].values()) for m in months]
    out["sales_BEV"] = [R[m]["BEV"] for m in months]
    return out


def build(panels: Path, fits: Path, n: int = 500) -> dict:
    sim = simulate.simulate(n=n, panels=panels, fits=fits)
    obs = observed(panels)
    last = obs["months"][-1]
    if sim["months"][0] <= last:
        raise ValueError("simulation does not start after the last observation")
    tot = sum(sim["stock"][f] for f in simulate.FUELS)
    fc = {"months": sim["months"]}
    for f in FUELS:
        q = np.percentile(sim["stock"][f], [10, 50, 90], axis=0)
        fc[f] = {"q10": _r(q[0]), "q50": _r(q[1]), "q90": _r(q[2])}
    q = np.percentile(sim["stock"]["BEV"] / tot, [10, 50, 90], axis=0)
    fc["bev_fleet_share"] = {k: _r(v, 4) for k, v in zip(("q10", "q50", "q90"), q)}
    # BEV share of sales as a trailing 12-month share (display; same smoothing as the observed line)
    R_tot = sum(sim["sales"][f] for f in simulate.FUELS)
    nd = R_tot.shape[0]
    b = np.hstack([np.tile(obs["sales_BEV"][-11:], (nd, 1)), sim["sales"]["BEV"]])
    t_ = np.hstack([np.tile(obs["sales_total"][-11:], (nd, 1)), R_tot])
    cb, ct = np.cumsum(b, 1), np.cumsum(t_, 1)
    roll_b = cb[:, 11:] - np.hstack([np.zeros((nd, 1)), cb[:, :-12]])
    roll_t = ct[:, 11:] - np.hstack([np.zeros((nd, 1)), ct[:, :-12]])
    q = np.percentile(roll_b / np.maximum(roll_t, 1), [10, 50, 90], axis=0)
    fc["bev_sales_share"] = {k: _r(v, 4) for k, v in zip(("q10", "q50", "q90"), q)}

    i12 = len(obs["months"]) - 13
    bev = obs["BEV"][-1]
    head = {
        "bev_stock": bev,
        "bev_change_12m": bev - obs["BEV"][i12],
        "bev_change_1m": bev - obs["BEV"][-2],
        "bev_share_of_fleet": round(bev / sum(obs[f][-1] for f in FUELS + ["other"]), 4),
        "bev_share_of_sales_month": round(obs["sales_BEV"][-1] / obs["sales_total"][-1], 4),
        "bev_share_of_sales_12m": round(sum(obs["sales_BEV"][-12:]) / sum(obs["sales_total"][-12:]), 4),
        "to_1m": max(1_000_000 - bev, 0),
        "petrol_stock": obs["petrol"][-1], "diesel_stock": obs["diesel"][-1], "phev_stock": obs["PHEV"][-1],
    }
    mfit = json.loads((fits / "shares.json").read_text("utf-8"))
    try:                                         # optional: a failed CPI fetch must not block the forecast
        fisc = fiscal.app_block(sim, panels)
    except Exception as e:                       # noqa: BLE001
        print(f"fiscal block skipped: {e}")
        fisc = None
    return {
        "vintage": last,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Danmarks Statistik (BIL51, BIL52, BIL54, BEF5, FRDK)",
        "draws": n,
        "headline": head,
        "milestones": simulate.milestones(sim),
        "observed": obs,
        "forecast": fc,
        "fiscal": fisc,
        "assumptions": {"bev_ceiling": mfit["bev"]["c"], "import_ratio": sim["kappa"],
                        "exit_rule": sim["exit_rule"], "import_rule": sim["import_rule"]},
    }


def previous_block(vintage: str) -> dict | None:
    vdir = APP_DATA / "vintages"
    older = sorted(p.stem for p in vdir.glob("*.json") if p.stem < vintage)
    if not older:
        return None
    prev = json.loads((vdir / f"{older[-1]}.json").read_text("utf-8"))
    return {"vintage": prev["vintage"], "headline": prev["headline"], "milestones": prev["milestones"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--panels", type=Path, default=ROOT / "Data" / "panels")
    ap.add_argument("--fits", type=Path, default=ROOT / "Data" / "fits")
    ap.add_argument("--app-data", type=Path, default=None, help="app data folder (default: app/data)")
    a = ap.parse_args(argv)
    global APP_DATA
    if a.app_data is not None:
        APP_DATA = a.app_data
    out = build(a.panels, a.fits)
    if out.get("fiscal") is None and (APP_DATA / "forecast.json").exists():
        # keep last month's tax/CO2 block rather than let the section disappear; flag it as stale
        old = json.loads((APP_DATA / "forecast.json").read_text("utf-8")).get("fiscal")
        if old:
            old["stale_from"] = old.get("stale_from") or json.loads((APP_DATA / "forecast.json").read_text("utf-8"))["vintage"]
            out["fiscal"] = old
            print(f"fiscal block carried over from {old['stale_from']} (stale)")
    (APP_DATA / "vintages").mkdir(parents=True, exist_ok=True)
    text = json.dumps(out, separators=(",", ":"), allow_nan=False)
    _write_atomic(APP_DATA / "vintages" / f"{out['vintage']}.json", lambda f: f.write_text(text, "utf-8"))
    newest = sorted(p.stem for p in (APP_DATA / "vintages").glob("*.json"))[-1]
    cur = json.loads((APP_DATA / "vintages" / f"{newest}.json").read_text("utf-8"))
    cur["previous"] = previous_block(newest)
    _write_atomic(APP_DATA / "forecast.json",
                  lambda f: f.write_text(json.dumps(cur, separators=(",", ":"), allow_nan=False), "utf-8"))
    print(f"vintage {out['vintage']} written; forecast.json = {newest}, previous = "
          f"{cur['previous']['vintage'] if cur['previous'] else None}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
