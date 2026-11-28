"""Monthly fleet simulation: market size + total exits + fuel shares + exits by fuel.

Usage:
    python src/simulate.py               # Data/fits/{total,shares}.npz -> Data/fits/simulation.{json,npz}

Per posterior draw and month t after the last observation (stock-flow identity, by fuel f):
    total stock  T_t = cars-per-adult draw (Gompertz + AR gap, total.cpa_predictive) x adults_t
    total exits  E_t = r_y / 12 x T_{t-1}     r_y: annual net exit rate of year y (total.exit_forecast)
    new sales    R_t = T_t - T_{t-1} + E_t    (if negative: R_t = 0 and E_t = T_{t-1} - T_t)
    sales by f   R_ft = R_t x share_ft        (shares.forecast_bev / forecast_rest, dummies on)
    exits by f   E_ft = exits.allocate_residual(E_t, stock_{t-1}, ...): non-BEV fuels at their latest annual
                 exit rates, BEV scrappage = the rest of E_t + imports_t / 12 (>= 0)
    stock        X_ft = X_f,t-1 + R_ft - E_ft    (sums to T_t by construction)
Draws are independent across layers (each layer's posterior is sampled separately).

Milestones (DESIGN.md decision 7), first month reached: 1M BEVs; BEV >= 50% of the fleet;
BEV > petrol; diesel < 100k; BEV + PHEV >= 90% of the fleet ("90% electric", plug-ins
counted). A draw that has not reached a milestone by the horizon counts as "not by 2040".
"""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exits  # noqa: E402
import shares  # noqa: E402
import total  # noqa: E402
from total import _write_atomic, q  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FUELS = exits.FUELS                        # BEV, PHEV, petrol, diesel, other
HORIZON = "2040-12"
N_DRAWS = 500


def _sub(post: dict, prefix: str, n: int, seed: int) -> dict:
    keys = [k for k in post if k.startswith(prefix)]
    idx = np.random.default_rng(seed).choice(len(post[keys[0]]), n, replace=False)
    return {k[len(prefix):]: np.asarray(post[k])[idx] for k in keys}


def last_stock(path: Path = ROOT / "Data" / "panels" / "fuel4_monthly.csv") -> tuple[str, dict]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    last = max(r["month"] for r in rows)
    return last, {r["fuel4"]: float(r["stock"]) for r in rows if r["month"] == last}


def step(stock: dict, T_prev, T_new, rate_annual, sh: np.ndarray, m: dict, import_ratio=0.0,
         import_volume=0.0) -> tuple[dict, dict, dict]:
    """One month of the identity. sh: (n, 4) shares in shares.ALL order. Net used-BEV imports
    this month = import_ratio x new BEV sales + import_volume. Returns stock, sales, exits."""
    E = rate_annual / 12 * T_prev
    R = T_new - T_prev + E
    neg = R < 0
    R = np.where(neg, 0.0, R)
    E = np.where(neg, T_prev - T_new, E)
    sales = {f: R * sh[:, shares.ALL.index(f)] for f in shares.ALL}
    sales["other"] = np.zeros_like(R)
    imp = import_ratio * sales["BEV"] + import_volume
    ex = exits.allocate_residual(E, stock, m, bev_imports=imp, period=1 / 12)
    ex["_imports"] = imp
    new = {f: stock[f] + sales[f] - ex[f] for f in FUELS}
    return new, sales, ex


def simulate(n: int = N_DRAWS, seed: int = 0, horizon: str = HORIZON,
             panels: Path = ROOT / "Data" / "panels", fits: Path = ROOT / "Data" / "fits",
             freeze_shares: bool = False, exit_rule: str = "age", import_rule: str = "sales") -> dict:
    """freeze_shares: baseline with fuel shares of sales held at the last 12 months' values.
    exit_rule: non-BEV exit rates "age" (linked to the fuel's young share, default since
    2026-11-28), "share" (linked to the BEV sales share), "flat"
    (latest rate) or "damped" (damped recent trend); see exits.rate_links.
    import_rule: net used-BEV imports "sales" (kappa x new BEV sales x fade, default) or
    "level" (the earlier fading volume)."""
    rng = np.random.default_rng(seed)
    tp = dict(np.load(fits / "total.npz"))
    sp = dict(np.load(fits / "shares.npz"))
    cpa, ext = _sub(tp, "cpa_", n, seed + 1), _sub(tp, "exit_", n, seed + 2)
    pb, pr = _sub(sp, "bev_", n, seed + 3), _sub(sp, "rest_", n, seed + 4)

    # starting point and future grid
    d = total.load_panel(panels)
    last, X0 = last_stock(panels / "fuel4_monthly.csv")
    if d["months"][-1] != last:
        raise ValueError(f"total panel ends {d['months'][-1]}, fuel panel {last}")
    fm = shares.future_months(last, 10_000)
    fm = fm[:fm.index(horizon) + 1]
    H = len(fm)
    pop = {int(r["year"]): int(r["adults"]) for r in csv.DictReader((panels / "population.csv").open(encoding="utf-8"))}
    adults = np.array([total.adults_at(pop, int(m[:4]) + int(m[5:]) / 12) for m in fm])
    y = np.log(d["stock"] / d["adults"])
    t_f = d["t"][-1] + np.arange(1, H + 1) / 12
    T = total.cpa_predictive(cpa, d["t"], y, t_f, rng) * adults            # (n, H)
    T_prev0 = float(d["stock"][-1])
    if abs(T_prev0 - sum(X0.values())) > 0.5:
        raise ValueError("fuel stocks do not sum to the total stock in the last month")

    # exit rate by calendar year
    y_last = int(d["exit_years"][-1])
    years = sorted({int(m[:4]) for m in fm})
    fc = total.exit_forecast(ext, float(d["exit_rate"][-1]), [yy - y_last for yy in years], rng)
    rate = {yy: fc[yy - y_last] for yy in years}

    # shares
    ds = shares.load_counts(panels / "fuel4_monthly.csv")
    if ds["months"][-1] != last:
        raise ValueError(f"share panel ends {ds['months'][-1]}, fuel panel {last}")
    ev = shares.load_events()
    Xd = shares.dummies(ds["months"], ev)
    uT, PuT = shares.final_states_bev(pb, ds, Xd)
    mT, PT = shares.final_states_rest(pr, ds, Xd)
    Xf = shares.dummies(fm, ev)
    sh = shares.combine(shares.forecast_bev(pb, uT, PuT, shares.month_time(fm), Xf, rng),
                        shares.forecast_rest(pr, mT, PT, Xf, rng))             # (n, H, 4)
    if freeze_shares:
        N12 = ds["N"][-12:].sum(0)
        sh = np.broadcast_to(N12 / N12.sum(), sh.shape).copy()

    # exits by fuel
    hist = exits.history(panels / "fuel4_monthly.csv")
    st = exits.settings(hist)
    m = exits.draw_m(st, n, rng)
    # trailing 12-month BEV share of sales, started from the observed last 12 months
    buf_bev = np.tile(ds["N"][-12:, 0], (n, 1)).astype(float)
    buf_tot = np.tile(ds["N"][-12:].sum(1), (n, 1)).astype(float)
    st["s0"] = float(buf_bev[0].sum() / buf_tot[0].sum())
    others = [f for f in FUELS if f != "BEV"]
    # age rule: rolling YOUNG_MONTHS-month buffer of new registrations by fuel, from the panel
    K = exits.YOUNG_MONTHS
    rows = [r for r in csv.DictReader((panels / "fuel4_monthly.csv").open(encoding="utf-8"))]
    lastK = sorted({r["month"] for r in rows})[-K:]
    reg = {(r["month"], r["fuel4"]): float(r["new_reg"]) for r in rows}
    buf_young = {f: np.tile([reg.get((mo, f), 0.0) for mo in lastK], (n, 1)) for f in others}
    for f in others:
        st["link"][f]["y0"] = (float(buf_young[f][0].sum() / X0[f]) if X0[f] >= exits.MIN_STOCK
                               else float("nan"))

    stock = {f: np.full(n, X0[f]) for f in FUELS}
    path = {f: np.empty((n, H)) for f in FUELS}
    flows = {"sales": {f: np.empty((n, H)) for f in FUELS}, "exits": {f: np.empty((n, H)) for f in FUELS}}
    floor_hits = 0
    imports = np.empty((n, H))
    T_prev = np.full(n, T_prev0)
    for h, mo in enumerate(fm):
        yr = int(mo[:4])
        t_mid = yr + (int(mo[5:]) - 0.5) / 12
        s12 = buf_bev.sum(1) / np.maximum(buf_tot.sum(1), 1.0)
        dm = {f"rate_{f}": exits.exit_rate(m, st, f, exit_rule, s12=s12, h_years=t_mid - (st["last_year"] + 0.5),
                                           young=buf_young[f].sum(1) / np.maximum(stock[f], 1.0))
              for f in others}
        if import_rule == "sales":
            kw = {"import_ratio": m["kappa"] * exits.fade(t_mid, st)}
        else:                                   # "level": the 2026-11-27c rule, a fading volume
            kw = {"import_volume": exits.bev_imports(m, t_mid, st) / 12}
        stock, sa, ex = step(stock, T_prev, T[:, h], rate[yr], sh[:, h], dm, **kw)
        imp = ex.pop("_imports")
        for f in others:
            buf_young[f][:, h % K] = sa[f]
        floor_hits += int(np.sum(ex["BEV"] + imp <= 1e-6))
        imports[:, h] = imp
        for f in FUELS:
            path[f][:, h] = stock[f]
            flows["sales"][f][:, h] = sa[f]
            flows["exits"][f][:, h] = ex[f]
        R_tot = sum(sa.values())
        buf_bev = np.column_stack([buf_bev[:, 1:], sa["BEV"]])
        buf_tot = np.column_stack([buf_tot[:, 1:], R_tot])
        T_prev = T[:, h]
    return {"months": fm, "last_obs": last, "stock0": X0, "total": T, "stock": path, **flows,
            "imports": imports, "exit_rule": exit_rule, "import_rule": import_rule,
            "floor_share": floor_hits / (n * H), "link": st["link"], "kappa": st["kappa"]}


def first_month(cond: np.ndarray, months: list[str]) -> list:
    """Per draw, the first month where cond holds (None if never)."""
    hit = cond.any(1)
    idx = cond.argmax(1)
    return [months[i] if h else None for i, h in zip(idx, hit)]


def milestones(sim: dict) -> dict:
    S, months = sim["stock"], sim["months"]
    tot = sum(S[f] for f in FUELS)
    conds = {
        "bev_1m": S["BEV"] >= 1_000_000,
        "bev_half_fleet": S["BEV"] >= 0.5 * tot,
        "bev_above_petrol": S["BEV"] > S["petrol"],
        "diesel_below_100k": S["diesel"] < 100_000,
        "plugin_90pct_fleet": S["BEV"] + S["PHEV"] >= 0.9 * tot,
    }
    out = {}
    for k, c in conds.items():
        fmo = first_month(c, months)
        reached = [x for x in fmo if x is not None]
        p = len(reached) / len(fmo)
        res = {"p_by_horizon": round(p, 3)}
        if reached:
            # quantiles over all draws, never-reached counted as after the horizon
            order = sorted(months.index(x) if x is not None else len(months) for x in fmo)
            qs = {}
            for lab, pp in (("q05", 0.05), ("median", 0.5), ("q95", 0.95)):
                i = order[min(int(pp * len(order)), len(order) - 1)]
                qs[lab] = months[i] if i < len(months) else f"after {months[-1]}"
            res.update(qs)
        out[k] = res
    return out


def summary(sim: dict) -> dict:
    out = {}
    for yr in ("2027", "2030", "2035", "2040"):
        j = sim["months"].index(f"{yr}-01") - 1 if f"{yr}-01" in sim["months"] else None
        if j is None or j < 0:
            continue                                   # stock on 1 January = end of December
        out[yr] = {f: q(sim["stock"][f][:, j] / 1e3) for f in ("BEV", "PHEV", "petrol", "diesel")}
        out[yr]["total"] = q(sim["total"][:, j] / 1e3)
    return out


def main() -> int:
    sim = simulate()
    out = {"last_obs": sim["last_obs"], "draws": N_DRAWS, "horizon": HORIZON,
           "milestones": milestones(sim), "stock_1jan_thousands": summary(sim),
           "exit_rule": sim["exit_rule"], "import_rule": sim["import_rule"],
           "floor_share": sim["floor_share"], "link": sim["link"]}
    print(json.dumps(out, indent=1))
    fits = ROOT / "Data" / "fits"
    npz = {f"stock_{f}": v.astype(np.float32) for f, v in sim["stock"].items()}
    npz["total"] = sim["total"].astype(np.float32)
    npz["sales_BEV"] = sim["sales"]["BEV"].astype(np.float32)      # used by src/fiscal.py
    npz["months"] = np.array(sim["months"])
    _write_atomic(fits / "simulation.npz", lambda f: np.savez_compressed(f, **npz))
    _write_atomic(fits / "simulation.json", lambda f: f.write_text(json.dumps(out, indent=2), "utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
