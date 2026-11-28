"""Exits by fuel: split the total net exits (src/total.py) across fuels.

Usage:
    python src/exits.py          # history + forecast settings -> Data/fits/exits.json

History (annual, 2013-): exits_f(y) = stock_f(Dec y-1) + reg_f(y) - stock_f(Dec y), net of
imports and exports. Relative rate m_f(y) = r_f(y) / r_total(y), r = exits / start stock.

Forecast rule (agreed 2026-11-27):
  * BEV: scrappage at the fleet rate, m_BEV * r_total * stock_BEV with m_BEV ~ Normal(1,
    BEV_SCRAP_SD), minus net used imports. Imports are a VOLUME from abroad (they depend on
    taxes and uptake in neighbouring markets, not on the Danish BEV fleet): they start at the
    last observed year's level and fade linearly to zero in BEV_CONVERGE_YEAR. Volatile, so the
    starting level is drawn wide: Normal(last level, sd of the last N_RECENT years), >= 0.
    (A first rule, BEV rate relative to the fleet rate drifting to 1, made imports scale with
    the BEV fleet: ~140k/yr by 2030 and petrol/diesel exit rates of 17%/27%. Rejected.)
  * PHEV, petrol, diesel, other: share what is left of the total, E_total - E_BEV, in
    proportion to m_f * stock_f, with m_f held at its latest value. The total stock is pinned
    by the market-size layer, so an extra imported BEV pushes out a combustion car.
  * Uncertainty: per draw, starting levels ~ Normal(level, sd of the last N_RECENT years),
    BEV scrappage factor ~ Normal(1, BEV_SCRAP_SD), import level as above.
Annual or monthly units both work in allocate(): it only needs exits and stocks in the same unit.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FUELS = ["BEV", "PHEV", "petrol", "diesel", "other"]
FIRST_YEAR = 2013            # 2012 would use the glitched 2011-12 stock (DESIGN.md)
N_RECENT = 3
BEV_CONVERGE_YEAR = 2035
BEV_SCRAP_SD = 0.25
MIN_STOCK = 500              # relative rates of tiny fleets are noise
MAX_RATE = 0.30              # cap on a non-BEV fuel's annual exit rate (compounded per period)
MIN_RATE_TOTAL = 0.01        # relative rates are not defined when the total rate is near zero
MIN_RATE = -0.10             # floor on a non-BEV annual exit rate (negative = net used imports)
LINK_FIRST = {"petrol": 2016, "diesel": 2016}   # share-linked exit rates; PHEV stays flat
LINK_MIN_YEARS = 4
DAMP = 0.8                   # damped-trend benchmark, per year
YOUNG_MONTHS = 60            # rolling registration buffer for the forecast (scaled to BIL21 by phi)
YOUNG_AGES = 5               # observed young share: cars aged 0-4 at 1 January (BIL21)
BIL21_DRIV = {"BEV": "20225", "PHEV": "20232", "petrol": "20205", "diesel": "20210"}


def bil21_young(path: Path) -> dict:
    """{fuel: {year: share of the 1 January stock aged 0..YOUNG_AGES-1}} from age_fuel.csv (BIL21)."""
    if not path.exists():
        return {}
    tot, yng = defaultdict(float), defaultdict(float)
    code = {v: k for k, v in BIL21_DRIV.items()}
    for r in csv.DictReader(path.open(encoding="utf-8")):
        f = code.get(r["driv"])
        if f is None or r["age"] == "IALT":          # IALT = all ages; single ages + 24OV add up to it
            continue
        key = (f, int(r["year"]))
        tot[key] += float(r["stock"])
        if r["age"].isdigit() and int(r["age"]) < YOUNG_AGES:
            yng[key] += float(r["stock"])
    out = defaultdict(dict)
    for (f, y), t in tot.items():
        if t >= MIN_STOCK:
            out[f][y] = yng[(f, y)] / t
    return dict(out)


def history(path: Path = ROOT / "Data" / "panels" / "fuel4_monthly.csv") -> dict:
    """Annual exits, start stocks and relative rates by fuel."""
    S, R, RM = {}, defaultdict(int), {}
    for r in csv.DictReader(path.open(encoding="utf-8")):
        key = (r["month"], r["fuel4"])
        if key in S:
            raise ValueError(f"duplicate row {key}")
        S[key] = int(r["stock"])
        RM[key] = int(r["new_reg"])
        R[(int(r["month"][:4]), r["fuel4"])] += int(r["new_reg"])
    last_dec = max(int(m[:4]) for (m, _) in S if m.endswith("-12"))
    years = list(range(FIRST_YEAR, last_dec + 1))
    for y in years:                       # every fuel: Dec y-1 and all 12 months of y
        for f in FUELS:
            need = [f"{y - 1}-12"] + [f"{y}-{k:02d}" for k in range(1, 13)]
            miss = [mo for mo in need if (mo, f) not in S]
            if miss:
                raise ValueError(f"missing months for {f}: {miss}")
    out = {"years": years, "stock0": {}, "exits": {}, "rate": {}, "m": {}, "sales": {}}
    for f in FUELS:
        out["sales"][f] = [R[(y, f)] for y in years]
        out["stock0"][f] = [S[(f"{y - 1}-12", f)] for y in years]
        out["exits"][f] = [S[(f"{y - 1}-12", f)] + R[(y, f)] - S[(f"{y}-12", f)] for y in years]
    tot_s = np.sum([out["stock0"][f] for f in FUELS], axis=0)
    tot_e = np.sum([out["exits"][f] for f in FUELS], axis=0)
    rt = tot_e / tot_s
    out["rate_total"] = rt.tolist()
    tot_r = np.sum([out["sales"][f] for f in FUELS], axis=0)
    out["bev_share"] = (np.array(out["sales"]["BEV"]) / tot_r).tolist()
    # Young share at the start of year y (2026-11-28, Codex #4): OBSERVED share of the 1 January stock
    # aged 0-4 (BIL21). The registration proxy (60-month registrations / stock) overstates it, because
    # exported young cars stay in the numerator (Jan 2026 diesel 13.6% vs 5.6% observed); it is kept as
    # young_reg and, scaled by phi = observed / proxy in the latest BIL21 year, rolls the share forward.
    months = sorted({mo for mo, _ in S})

    def reg_proxy(f, dec):                                    # registrations to month `dec` / stock then
        if dec not in months:
            return float("nan")
        end = months.index(dec)
        st0 = S[(dec, f)]
        if end - YOUNG_MONTHS + 1 < 0 or st0 < MIN_STOCK:
            return float("nan")
        return sum(RM[(months[j], f)] for j in range(end - YOUNG_MONTHS + 1, end + 1)) / st0

    b21 = bil21_young(path.parent / "age_fuel.csv")
    out["young_reg"], out["young"], out["young_phi"], out["young_source"] = {}, {}, {}, {}
    for f in FUELS:
        out["young_reg"][f] = [reg_proxy(f, f"{y - 1}-12") for y in years]
        obs = b21.get(f, {})
        if obs:
            out["young"][f] = [obs.get(y, float("nan")) for y in years]
            yb = max(y for y in obs if f"{y - 1}-12" in months)       # latest BIL21 year inside the panel
            px = reg_proxy(f, f"{yb - 1}-12")
            out["young_phi"][f] = obs[yb] / px if np.isfinite(px) and px > 0 else 1.0
            out["young_source"][f] = f"BIL21 ages 0-{YOUNG_AGES - 1}; phi from {yb}"
        else:                                                     # no age table: fall back to the proxy
            out["young"][f] = out["young_reg"][f]
            out["young_phi"][f] = 1.0
            out["young_source"][f] = "registration proxy (no BIL21 in the panel)"
    ok = rt >= MIN_RATE_TOTAL
    for f in FUELS:
        s0, e = np.array(out["stock0"][f], float), np.array(out["exits"][f], float)
        rate = np.where(s0 >= MIN_STOCK, e / np.maximum(s0, 1), np.nan)
        out["rate"][f] = rate.tolist()
        out["m"][f] = np.where(ok, rate / np.where(ok, rt, 1), np.nan).tolist()
    return out


def settings(h: dict) -> dict:
    """Starting levels and spreads for the forecast, from the last N_RECENT years."""
    st = {"last_year": h["years"][-1], "converge_year": BEV_CONVERGE_YEAR, "m": {}}
    for f in FUELS:
        recent = np.array(h["m"][f][-N_RECENT:], float)
        recent = np.where(np.isfinite(recent), recent, np.nan)
        if np.all(np.isnan(recent)):
            st["m"][f] = {"level": 1.0, "sd": 0.0}           # too small to estimate: fleet rate
            continue
        level = float(recent[~np.isnan(recent)][-1])
        st["m"][f] = {"level": level, "sd": float(np.nanstd(recent, ddof=1)) if np.sum(~np.isnan(recent)) > 1 else 0.0}
    st["m"]["BEV"] = {"level": 1.0, "sd": BEV_SCRAP_SD}     # scrappage only; imports separate
    # Net imports consistent with the forecast rule: observed BEV net exits = scrappage - imports,
    # with scrappage at the fleet rate (m_BEV = 1), so imports = scrappage - net exits.
    # (-net exits alone understates imports by the scrappage: ~70k vs ~86k in 2025; Codex #4.)
    scrap = (np.array(h["rate_total"][-N_RECENT:]) * np.array(h["stock0"]["BEV"][-N_RECENT:], float))
    imports = scrap - np.array(h["exits"]["BEV"][-N_RECENT:], float)
    if not np.all(np.isfinite(imports)):
        raise ValueError("non-finite BEV net exits in the calibration window")
    # one year only: no spread estimate, fall back to a third of the level
    sd = float(np.std(imports, ddof=1)) if len(imports) > 1 else abs(float(imports[-1])) / 3
    st["bev_imports"] = {"level": float(imports[-1]), "sd": sd,
                         "recent": dict(zip(map(str, h["years"][-N_RECENT:]), imports.tolist()))}
    # Residual rule (2026-11-27c): absolute annual exit rates of the non-BEV fuels, latest year
    st["rate"] = {}
    for f in FUELS:
        if f == "BEV":
            continue
        recent = np.array(h["rate"][f][-N_RECENT:], float)
        recent = recent[np.isfinite(recent)]
        if len(recent) == 0:                                # too small to estimate: fleet rate
            st["rate"][f] = {"level": float(h["rate_total"][-1]), "sd": 0.0}
        else:
            st["rate"][f] = {"level": float(recent[-1]),
                             "sd": float(np.std(recent, ddof=1)) if len(recent) > 1 else 0.0}
    st["link"] = rate_links(h, st)
    st["s0"] = float(h["bev_share"][-1])     # simulate.py resets it to the trailing 12 months
    # Imports proportional to new BEV sales (2026-11-27d, with Codex): kappa = imports / BEV sales,
    # 0.45-0.73 in 2021-2025. Lognormal per path: mean = latest ratio, sd = sd of the last 3.
    bs = np.array(h["sales"]["BEV"][-N_RECENT:], float)
    ratio = np.where(bs > 0, imports / np.maximum(bs, 1), 0.0)
    st["kappa"] = {"mean": max(float(ratio[-1]), 0.0),
                   "sd": float(np.std(ratio, ddof=1)) if len(ratio) > 1 else max(float(ratio[-1]), 0.0) / 3,
                   "recent": dict(zip(map(str, h["years"][-N_RECENT:]), np.round(ratio, 3).tolist()))}
    return st


def rate_links(h: dict, st: dict) -> dict:
    """Exit-rate dynamics of the non-BEV fuels (2026-11-27d, with Codex).

    share rule: r_f(t) = r_f0 + shift_f + b_f (s(t) - s0); s = trailing 12-month BEV share of
      new sales; b_f >= 0 from OLS of the annual rate on the annual BEV share, years >= LINK_FIRST[f];
      shift_f ~ N(0, residual sd), drawn once per path (persistent).
    damped rule (benchmark): r_f(h) = r_f0 + shift_f + g_f sum_{j=1..h} DAMP^j, g_f = recent
      annual slope (last 3 years).
    age rule (2026-11-27e): r_f(t) = r_f0 + shift_f + a_f (y0_f - y_f(t)); y_f = young share,
      new registrations of fuel f in the last YOUNG_MONTHS months / stock of f (an age proxy:
      a fleet without new cars ages and is scrapped faster). a_f >= 0 from OLS of the annual rate
      on the young share at the start of the year, years >= LINK_FIRST[f]. Saturates at y_f = 0.
    Fuels without LINK_FIRST, or with fewer than LINK_MIN_YEARS usable years, stay flat.
    """
    years = np.array(h["years"])
    s = np.array(h["bev_share"], float)
    out = {}
    for f, v in st["rate"].items():
        r = np.array(h["rate"][f], float)
        first = LINK_FIRST.get(f)
        use = np.isfinite(r) & (years >= (first if first else 9999))
        res = {"r0": v["level"], "b": 0.0, "b_se": 0.0, "resid_sd": v["sd"], "g": 0.0, "n_years": int(use.sum()),
               "a": 0.0, "a_se": 0.0, "resid_sd_age": v["sd"], "y0": float("nan"),
               "y_rate": float(h.get("young", {}).get(f, [np.nan])[-1]),          # young share in r0's year
               "phi": float(h.get("young_phi", {}).get(f, 1.0))}
        yg = np.array(h.get("young", {}).get(f, [np.nan] * len(years)), float)
        use_a = use & np.isfinite(yg)
        if first and use_a.sum() >= LINK_MIN_YEARS:
            X = np.column_stack([np.ones(use_a.sum()), yg[use_a]])
            coef, *_ = np.linalg.lstsq(X, r[use_a], rcond=None)
            resid = r[use_a] - X @ coef
            sig2 = float(resid @ resid / max(use_a.sum() - 2, 1))
            cov = sig2 * np.linalg.inv(X.T @ X)
            res.update(a=max(-float(coef[1]), 0.0), a_se=float(np.sqrt(cov[1, 1])),
                       resid_sd_age=float(np.sqrt(sig2)), n_years_age=int(use_a.sum()))
        if first and use.sum() >= LINK_MIN_YEARS:
            X = np.column_stack([np.ones(use.sum()), s[use]])
            coef, *_ = np.linalg.lstsq(X, r[use], rcond=None)
            resid = r[use] - X @ coef
            dof = max(use.sum() - 2, 1)
            sig2 = float(resid @ resid / dof)
            cov = sig2 * np.linalg.inv(X.T @ X)
            res.update(b=max(float(coef[1]), 0.0), b_se=float(np.sqrt(cov[1, 1])), resid_sd=float(np.sqrt(sig2)))
            rr = r[np.isfinite(r)][-N_RECENT:]
            res["g"] = float((rr[-1] - rr[0]) / (len(rr) - 1)) if len(rr) > 1 else 0.0
        out[f] = res
    return out


def exit_rate(d: dict, st: dict, f: str, rule: str, s12=None, h_years=0.0, young=None) -> np.ndarray:
    """Annual exit rate of non-BEV fuel f under `rule` ("flat", "share", "damped", "age").
    young: current young share of fuel f (age rule; st["link"][f]["y0"] is its start value)."""
    if rule == "flat":
        return d[f"rate_{f}"]
    lk = st["link"][f]
    if rule == "age":
        if not np.isfinite(lk["y0"]):
            return np.clip(lk["r0"] + d[f"shiftage_{f}"], MIN_RATE, MAX_RATE)
        r = lk["r0"] + d[f"shiftage_{f}"] + d[f"a_{f}"] * (lk["y0"] - np.asarray(young, float))
        return np.clip(r, MIN_RATE, MAX_RATE)
    base = lk["r0"] + d[f"shift_{f}"]
    if rule == "share":
        r = base + d[f"b_{f}"] * (np.asarray(s12, float) - st["s0"])
    elif rule == "damped":
        r = base + lk["g"] * DAMP * (1 - DAMP ** h_years) / (1 - DAMP)
    else:
        raise ValueError(rule)
    return np.clip(r, MIN_RATE, MAX_RATE)


def draw_m(st: dict, n: int, rng: np.random.Generator) -> dict:
    """Per-draw parameters: m for every fuel (BEV = scrappage factor), the import level and,
    for the residual rule, the non-BEV annual exit rates ``rate_<fuel>`` in [0, MAX_RATE]."""
    d = {f: rng.normal(v["level"], v["sd"], n) for f, v in st["m"].items()}
    d["BEV"] = np.maximum(d["BEV"], 0.0)       # scrappage factor: no artificial inflows
    for f, v in st.get("rate", {}).items():
        # negative allowed: net used imports of that fuel (PHEV until 2021)
        d[f"rate_{f}"] = np.clip(rng.normal(v["level"], v["sd"], n), MIN_RATE, MAX_RATE)
    for f, lk in st.get("link", {}).items():
        d[f"b_{f}"] = np.maximum(rng.normal(lk["b"], lk["b_se"], n), 0.0)
        d[f"shift_{f}"] = rng.normal(0.0, lk["resid_sd"], n)
        d[f"a_{f}"] = np.maximum(rng.normal(lk["a"], lk["a_se"], n), 0.0)
        d[f"shiftage_{f}"] = rng.normal(0.0, lk["resid_sd_age"], n)
    d["bev_imports0"] = np.maximum(rng.normal(st["bev_imports"]["level"], st["bev_imports"]["sd"], n), 0.0)
    if "kappa" in st:
        d["kappa"] = lognormal_mean_sd(st["kappa"]["mean"], st["kappa"]["sd"], n, rng)
    return d


def lognormal_mean_sd(mean: float, sd: float, n: int, rng: np.random.Generator) -> np.ndarray:
    """Lognormal draws with the given arithmetic mean and sd (zeros if mean <= 0)."""
    if mean <= 0:
        return np.zeros(n)
    s2 = np.log1p((sd / mean) ** 2)
    return rng.lognormal(np.log(mean) - s2 / 2, np.sqrt(s2), n)


def fade(year: float, st: dict) -> float:
    """Linear weight 1 -> 0 from the middle of the last observed year to converge_year."""
    y0, y1 = st["last_year"] + 0.5, st["converge_year"]
    if year >= y1 or y0 >= y1:
        return 0.0
    return float(np.clip(1 - (year - y0) / (y1 - y0), 0.0, 1.0))


def bev_imports(d: dict, year: float, st: dict) -> np.ndarray:
    """Annual net used-BEV imports in (fractional) year: linear fade to 0 at converge_year.

    ``year`` is the midpoint of the period (2026.5 for calendar 2026); for monthly steps divide
    the result by 12.
    """
    y0, y1 = st["last_year"] + 0.5, st["converge_year"]
    if year >= y1 or y0 >= y1:
        return np.zeros_like(np.asarray(d["bev_imports0"], float))
    w = np.clip((year - y0) / (y1 - y0), 0.0, 1.0)
    return (1 - w) * d["bev_imports0"]


def allocate(e_total, stock: dict, m: dict, bev_imports=0.0, period: float = 1.0) -> dict:
    """Split total exits across fuels. Arrays broadcast over draws.

    ``period`` is the step length in years (1/12 for monthly steps); e_total and bev_imports
    are flows over that step. BEV scrappage = max(m_BEV, 0) * (e_total / total stock) *
    stock_BEV, bounded by e_total + bev_imports so no other fuel gets negative exits; BEV exits
    = scrappage - bev_imports. The rest goes to the other fuels in proportion to
    max(m_f, 0) * stock_f (stock_f if every weight is zero), each capped at
    1 - (1 - MAX_RATE)^period of its stock; the overflow is re-spread over the uncapped fuels
    and, once all are capped, falls back on BEV scrappage (up to the BEV stock). Raises if even
    that cannot absorb e_total. The fuels always sum to e_total.
    """
    s_tot = sum(np.asarray(stock[f], float) for f in FUELS)
    e_total = np.asarray(e_total, float)
    imp = np.asarray(bev_imports, float)
    s_bev = np.asarray(stock["BEV"], float)
    scrap = np.maximum(np.asarray(m["BEV"], float), 0.0) * (e_total / s_tot) * s_bev
    scrap = np.minimum(scrap, np.maximum(e_total + imp, 0.0))
    rest = e_total + imp - scrap
    others = [f for f in FUELS if f != "BEV"]
    w = {f: np.maximum(np.asarray(m[f], float), 0.0) * np.asarray(stock[f], float) for f in others}
    zero = sum(w.values()) <= 0                 # every weight zero: split by stock
    w = {f: np.where(zero, np.asarray(stock[f], float), w[f]) for f in others}
    rate_cap = 1 - (1 - MAX_RATE) ** period
    cap = {f: rate_cap * np.asarray(stock[f], float) for f in others}
    alloc = {f: np.zeros_like(rest) for f in others}
    free = {f: np.ones_like(rest, dtype=bool) for f in others}
    left = rest.copy()
    for _ in range(len(others)):
        wsum = sum(np.where(free[f], w[f], 0.0) for f in others)
        for f in others:
            share = np.where(free[f] & (wsum > 0), w[f] / np.where(wsum > 0, wsum, 1), 0.0)
            alloc[f] = alloc[f] + share * left
        over = {f: np.maximum(alloc[f] - cap[f], 0.0) for f in others}
        # nothing free to take it: the remainder stays unplaced (not dropped)
        left = sum(over.values()) + np.where(wsum > 0, 0.0, left)
        for f in others:
            hit = over[f] > 0
            alloc[f] = np.where(hit, cap[f], alloc[f])
            free[f] = free[f] & ~hit
        if np.all(left <= 1e-9):
            break
    # every other fuel at its cap: the remainder is scrapped BEVs, up to the BEV stock
    extra = np.minimum(left, np.maximum(s_bev - scrap, 0.0))
    scrap, left = scrap + extra, left - extra
    if np.any(left > 1e-6 * np.maximum(np.abs(e_total), 1.0)):
        raise ValueError("total exits exceed what the fleet can supply under the caps")
    return {"BEV": scrap - imp, **alloc}


def allocate_residual(e_total, stock: dict, d: dict, bev_imports=0.0, period: float = 1.0) -> dict:
    """Residual rule (agreed 2026-11-27c; replaces allocate() in the simulation).

    Non-BEV fuel f exits at its own annual rate, compounded over the step:
    (1 - (1 - rate_f)^period) * stock_f, rate_f = d["rate_<f>"]. BEV scrappage is what is left
    of the total: e_total + bev_imports - sum of the others, so BEV net exits = scrappage -
    imports. If the remainder is negative, the other fuels are scaled down until BEV scrappage
    is 0 (never artificial BEV inflows). If BEV scrappage would exceed the BEV stock, the
    excess goes back to the others (up to their stock). Raises if the fleet cannot supply
    e_total. The fuels always sum to e_total. Arrays broadcast over draws.
    """
    e_total = np.asarray(e_total, float)
    imp = np.asarray(bev_imports, float)
    others = [f for f in FUELS if f != "BEV"]
    s = {f: np.asarray(stock[f], float) for f in FUELS}
    ex = {f: (1 - (1 - np.asarray(d[f"rate_{f}"], float)) ** period) * s[f] for f in others}
    pool = np.maximum(e_total + imp, 0.0)          # what scrappage + other exits must add up to
    tot_o = sum(ex.values())
    scale = np.where(tot_o > pool, pool / np.where(tot_o > 0, tot_o, 1), 1.0)
    ex = {f: ex[f] * scale for f in others}
    scrap = pool - sum(ex.values())
    over = np.maximum(scrap - s["BEV"], 0.0)       # BEV stock exhausted: back to the others
    scrap = scrap - over
    room = {f: s[f] - ex[f] for f in others}
    room_tot = sum(room.values())
    for f in others:
        ex[f] = ex[f] + over * np.where(room_tot > 0, room[f] / np.where(room_tot > 0, room_tot, 1), 0.0)
    left = over - np.minimum(over, room_tot)
    if np.any(left > 1e-6 * np.maximum(np.abs(e_total), 1.0)):
        raise ValueError("total exits exceed the fleet")
    out = {"BEV": scrap - imp, **ex}
    if np.any(e_total + imp < 0):                  # pool floored: BEV absorbs the shortfall as imports
        out["BEV"] = out["BEV"] + np.minimum(e_total + imp, 0.0)
    return out


def _nan_to_none(x):
    """Standard JSON: NaN / inf become null (browsers reject the NaN token)."""
    if isinstance(x, dict):
        return {k: _nan_to_none(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_nan_to_none(v) for v in x]
    if isinstance(x, float) and not np.isfinite(x):
        return None
    return x


def main() -> int:
    h = history()
    st = settings(h)
    out = {"history": h, "settings": st}
    path = ROOT / "Data" / "fits" / "exits.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.stem + ".tmp" + path.suffix)
    tmp.write_text(json.dumps(_nan_to_none(out), indent=2, allow_nan=False), "utf-8")
    tmp.replace(path)
    print(json.dumps(st, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
