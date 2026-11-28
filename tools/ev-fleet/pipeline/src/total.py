"""Market-size layer: cars per adult (Gompertz) and the total net exit rate.

Usage:
    python src/total.py                  # fit both, write Data/fits/total.{json,npz}

Cars per adult, monthly from 2012-01 (2011-12 has a BIL52 glitch, DESIGN.md):
    c(t) = S * exp(-b * exp(-r * t)),  t = years since 2012-01,  b = log(S / c0)
    log(stock_t / adults_t) = log c(t) + u_t,  u_t AR(1)
BIL52 stock is end-of-month (BIL21 1 January = BIL52 December), so adults 18+ (1 January
counts, population.csv) are interpolated linearly to the end of each month.
Saturation S has a default prior that every monthly refit updates with the data:
S ~ TruncatedNormal(S_PRIOR_MEAN, S_PRIOR_SD, low 0.55), from Eurostat 2025 cars per adult
(road_eqs_carhab / adult share from demo_pjan): Sweden 0.60, Netherlands 0.64, Norway 0.65,
Germany 0.71, EU 0.71 (Finland 0.82 left out as a register outlier). Files and log entry in
Literature/. Override with --s-prior MEAN SD.

Total net exit rate, annual 2013-: x_y = (stock_Dec(y-1) + reg_y - stock_Dec(y)) / stock_Dec(y-1),
    log x_y = alpha + e_y,  e_y AR(1) with persistence phi
Mean reversion, not a trend: the 2020-2025 dip is mostly net used-BEV imports netted into exits,
and a trend would carry it to implausible service lives. Forecasts start near the latest rate
and revert to exp(alpha) at rate phi per year.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

# OpenBLAS threads x 4 chains can exhaust memory on this machine (failed allocations seen)
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
START = "2012-01"
T_REF = 2020
S_PRIOR_MEAN, S_PRIOR_SD = 0.65, 0.04


def _next_month(m: str) -> str:
    y, mo = int(m[:4]), int(m[5:])
    return f"{y + mo // 12}-{mo % 12 + 1:02d}"


def load_panel(panels: Path = ROOT / "Data" / "panels"):
    """Monthly total stock and adults; annual total exit rates.

    Raises if a month is missing or a count is blank: the AR(1) terms and the exit identity
    assume consecutive, complete months.
    """
    stock, reg = {}, {}
    for r in csv.DictReader((panels / "monthly_fuel.csv").open(encoding="utf-8")):
        if r["driv"] == "20200":
            if not r["stock"] or not r["new_reg"]:
                raise ValueError(f"missing total stock or registrations in {r['month']}")
            stock[r["month"]] = int(r["stock"])
            reg[r["month"]] = int(r["new_reg"])
    pop = {int(r["year"]): int(r["adults"]) for r in csv.DictReader((panels / "population.csv").open(encoding="utf-8"))}
    all_months = sorted(stock)
    for a, b in zip(all_months, all_months[1:]):
        if _next_month(a) != b:
            raise ValueError(f"gap in monthly panel between {a} and {b}")
    months = [m for m in all_months if m >= START]
    t = np.array([int(m[:4]) - 2012 + (int(m[5:]) - 1) / 12 for m in months])
    adults = np.array([adults_at(pop, int(m[:4]) + int(m[5:]) / 12) for m in months])  # end of month
    s = np.array([stock[m] for m in months], dtype=float)
    years = sorted({int(m[:4]) for m in months if f"{int(m[:4]) - 1}-12" in stock and f"{m[:4]}-12" in stock
                    and int(m[:4]) >= 2013})
    exit_rate = np.array([(stock[f"{y - 1}-12"] + sum(reg[f"{y}-{k:02d}"] for k in range(1, 13))
                           - stock[f"{y}-12"]) / stock[f"{y - 1}-12"] for y in years])
    return {"months": months, "t": t, "stock": s, "adults": adults,
            "exit_years": np.array(years), "exit_rate": exit_rate}


def adults_at(pop: dict[int, int], x: float) -> float:
    """Adults at fractional year x (1 January = integer), linear between 1 Januaries."""
    y0 = int(np.floor(x + 1e-9))
    frac = x - y0
    if abs(frac) < 1e-9:  # exactly 1 January (end of December): no next year needed
        return float(pop[y0])
    return pop[y0] + frac * (pop[y0 + 1] - pop[y0])


def gompertz(xp, t, S, c0, r):
    return S * xp.exp(-xp.log(S / c0) * xp.exp(-r * t))


def model_cpa(t, y=None, s_prior=(S_PRIOR_MEAN, S_PRIOR_SD)):
    import jax.numpy as jnp
    import numpyro
    import numpyro.distributions as dist

    c0 = numpyro.sample("c0", dist.Normal(0.50, 0.05))
    S = numpyro.sample("S", dist.TruncatedNormal(s_prior[0], s_prior[1], low=0.55))
    r = numpyro.sample("r", dist.LogNormal(jnp.log(0.10), 0.7))
    rho = numpyro.sample("rho", dist.Uniform(0.0, 0.999))
    sig = numpyro.sample("sigma", dist.HalfNormal(0.01))
    mu = jnp.log(gompertz(jnp, t, S, c0, r))
    if y is None:
        return
    u = y - mu
    # AR(1): u_0 ~ N(0, sig^2 / (1 - rho^2)), u_t | u_{t-1} ~ N(rho u_{t-1}, sig^2)
    numpyro.sample("u0", dist.Normal(0, sig / jnp.sqrt(1 - rho ** 2)), obs=u[0])
    numpyro.sample("u", dist.Normal(rho * u[:-1], sig), obs=u[1:])


def model_exit(yr, y=None):
    import numpyro
    import numpyro.distributions as dist
    import jax.numpy as jnp
    alpha = numpyro.sample("alpha", dist.Normal(np.log(0.055), 0.3))
    phi = numpyro.sample("phi", dist.Beta(3, 2))
    sig = numpyro.sample("sigma", dist.HalfNormal(0.2))
    if y is None:
        return
    e = y - alpha
    numpyro.sample("e0", dist.Normal(0, sig / jnp.sqrt(1 - phi ** 2)), obs=e[0])
    numpyro.sample("e", dist.Normal(phi * e[:-1], sig), obs=e[1:])


def run(model, *args, chains=4, warmup=1000, samples=1000, seed=0, target_accept=0.95, **kw):
    import jax
    import numpyro
    from numpyro.infer import MCMC, NUTS, init_to_median
    numpyro.set_host_device_count(chains)
    m = MCMC(NUTS(model, target_accept_prob=target_accept, init_strategy=init_to_median(num_samples=50)),
             num_warmup=warmup, num_samples=samples, num_chains=chains, chain_method="parallel",
             progress_bar=False)
    m.run(jax.random.PRNGKey(seed), *args, **kw)
    return m


def diagnostics(m) -> dict:
    from numpyro.diagnostics import summary
    s = summary(m.get_samples(group_by_chain=True))
    rhat = max(float(np.nanmax(v["r_hat"])) for v in s.values())
    ess = min(float(np.nanmin(v["n_eff"])) for v in s.values())
    div = int(np.asarray(m.get_extra_fields()["diverging"]).sum())
    return {"max_rhat": round(rhat, 4), "min_ess": round(ess, 1), "divergences": div,
            "ok": rhat < 1.01 and div == 0 and ess > 400}


def q(x, p=(5, 50, 95)):
    return [round(float(v), 5) for v in np.percentile(np.asarray(x), p)]


def cpa_predictive(post: dict, t_obs, y_obs, t_future, rng, prefix: str = "") -> np.ndarray:
    """Cars-per-adult draws on t_future (the monthly grid right after t_obs): curve x exp(gap).

    The AR gap starts at each draw's last observed residual, decays by rho per month and gets
    N(0, sigma) shocks. Returns (draws, len(t_future)).
    """
    S, c0, r, rho, sig = (np.asarray(post[prefix + k]) for k in ("S", "c0", "r", "rho", "sigma"))
    if round((t_future[0] - t_obs[-1]) * 12) != 1 or not np.allclose(np.diff(t_future), 1 / 12):
        raise ValueError("t_future must be the monthly grid right after the last observation")
    u = y_obs[-1] - np.log(gompertz(np, t_obs[-1], S, c0, r))
    out = np.empty((len(S), len(t_future)))
    for j, tf in enumerate(t_future):
        u = rho * u + rng.normal(0, sig)
        out[:, j] = gompertz(np, tf, S, c0, r) * np.exp(u)
    return out


def exit_forecast(post: dict, last_rate: float, horizons, rng, prefix: str = "") -> dict:
    """Total exit rate h years after the last observed year, per draw, with AR(1) shocks."""
    al, ph, sig = (np.asarray(post[prefix + k]) for k in ("alpha", "phi", "sigma"))
    e = np.log(last_rate) - al
    out = {}
    for h in range(1, max(horizons) + 1):
        e = ph * e + rng.normal(0, sig)
        if h in horizons:
            out[h] = np.exp(al + e)
    return out


def _write_atomic(path: Path, write) -> None:
    tmp = path.with_name(path.stem + ".tmp" + path.suffix)
    write(tmp)
    tmp.replace(path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "Data" / "fits")
    ap.add_argument("--panels", type=Path, default=ROOT / "Data" / "panels", help="panel folder (backtests)")
    ap.add_argument("--s-prior", type=float, nargs=2, default=(S_PRIOR_MEAN, S_PRIOR_SD),
                    metavar=("MEAN", "SD"), help="saturation prior, cars per adult")
    a = ap.parse_args(argv)
    d = load_panel(a.panels)
    y = np.log(d["stock"] / d["adults"])
    m1 = run(model_cpa, d["t"], y=y, s_prior=tuple(a.s_prior))
    m2 = run(model_exit, d["exit_years"].astype(float), y=np.log(d["exit_rate"]))
    p1, p2 = m1.get_samples(), m2.get_samples()

    pop = {int(r["year"]): int(r["adults"]) for r in csv.DictReader((a.panels / "population.csv").open(encoding="utf-8"))}
    rng = np.random.default_rng(0)
    t_f = d["t"][-1] + np.arange(1, 12 * 16) / 12
    pred = cpa_predictive(p1, d["t"], y, t_f, rng)
    proj = {}
    for yr in (2030, 2035, 2040):
        j = int(np.argmin(np.abs(t_f - (yr - 2012 - 1 / 12))))   # December of yr-1 = 1 January yr
        curve = gompertz(np, t_f[j], np.asarray(p1["S"]), np.asarray(p1["c0"]), np.asarray(p1["r"]))
        proj[str(yr)] = {"cars_per_adult_predictive": q(pred[:, j]), "cars_per_adult_curve_only": q(curve),
                         "total_stock_mio_predictive": q(pred[:, j] * pop[yr] / 1e6)}
    al, ph = np.asarray(p2["alpha"]), np.asarray(p2["phi"])
    e_last = np.log(d["exit_rate"][-1]) - al
    y_last = int(d["exit_years"][-1])
    hs = (1, 5, 15)
    fc = exit_forecast(p2, float(d["exit_rate"][-1]), hs, rng)
    rates = {str(y_last + h): {"predictive": q(fc[h]), "median_path": q(np.exp(al + ph ** h * e_last))}
             for h in hs}
    rates["long_run_median"] = q(np.exp(al))
    out = {
        "cars_per_adult": {"diagnostics": diagnostics(m1), "S_prior": list(a.s_prior), "S": q(p1["S"]), "c0": q(p1["c0"]),
                           "r": q(p1["r"]), "rho": q(p1["rho"]), "sigma": q(p1["sigma"]),
                           "last_obs": {"month": d["months"][-1], "value": round(float(np.exp(y[-1])), 4)},
                           "projection": proj},
        "exit_rate": {"diagnostics": diagnostics(m2), "observed": dict(zip(map(str, d["exit_years"]),
                                                                           np.round(d["exit_rate"], 4).tolist())),
                      "phi": q(p2["phi"]), "sigma": q(p2["sigma"]), "rate": rates},
    }
    print(json.dumps(out, indent=1))
    if not (out["cars_per_adult"]["diagnostics"]["ok"] and out["exit_rate"]["diagnostics"]["ok"]):
        print("convergence gate failed; previous outputs kept", file=sys.stderr)
        return 1
    a.out.mkdir(parents=True, exist_ok=True)
    npz = {**{f"cpa_{k}": np.asarray(v) for k, v in p1.items()}, **{f"exit_{k}": np.asarray(v) for k, v in p2.items()}}
    _write_atomic(a.out / "total.npz", lambda f: np.savez_compressed(f, **npz))
    _write_atomic(a.out / "total.json", lambda f: f.write_text(json.dumps(out, indent=2), "utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
