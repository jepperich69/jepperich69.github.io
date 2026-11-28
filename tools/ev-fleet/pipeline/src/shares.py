"""Fuel shares of new registrations (BIL51): BEV diffusion curve with a ceiling, plus the split
of the non-BEV remainder.

Usage:
    python src/shares.py                 # fit, write Data/fits/shares.{json,npz}
    python src/shares.py --end 2022-12   # fit on data up to a month (backtests)

Data: monthly new registrations by fuel from START (BIL51, brand-new cars only). "other" has
no sales and is left out. Sample from 2019-01: before that BEV and PHEV sell a few hundred cars
a month and the 2015-16 tax swings dominate (trial fits from 2012, 2026-11-27c).

Layer 1, BEV share s_t (agreed 2026-11-27c; trend models in log-odds had unbounded long-run
bands, BEV 2035 0.3-100%):
    logit(s_t) = logit(c * L(t)) + gamma_B . x_t + u_t + eps_t,  L(t) = 1 / (1 + exp(-k (t - t0)))
    u_t = rho u_{t-1} + eta_t (AR(1), persistent deviations from the curve)
    eps_t ~ N(0, s_obs^2 + 1/n_BEV + 1/n_nonBEV)   (month noise + sampling variance)
    ceiling c ~ TruncatedNormal(0.97, 0.03, 0.80, 1.00): Norway's BEV share of new sales is
    about 97%; c is re-estimated every month.
Layer 2, the non-BEV remainder: log(n_PHEV / n_petrol) and log(n_diesel / n_petrol), each a
local linear trend with a damped drift (level a, drift b: a += b + shock, b = phi b + shock),
with sampling covariance from the counts. Its long-run spread is wide but it only splits a
share that shrinks to 1 - c.
x_t: December pull-forward and January slump dummies from Data/events.csv (both layers).
The latent terms (u, a, b) are integrated out with a Kalman filter; NUTS sees the parameters.

Forecast: per posterior draw, the latent state at the last month is drawn from its filtered
distribution and run forward with fresh shocks; month noise eps is left out.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from total import _next_month, _write_atomic, diagnostics, q, run  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
START = "2019-01"
T_REF = 2020.0
ALL = ["BEV", "PHEV", "petrol", "diesel"]
REST = ["PHEV", "diesel"]                  # modelled against petrol inside the remainder
C_PRIOR = (0.97, 0.03, 0.80, 1.00)         # mean, sd, low, high


# ---------------------------------------------------------------- data

def load_events(path: Path = ROOT / "Data" / "events.csv") -> dict:
    ev = {}
    for r in csv.DictReader(path.open(encoding="utf-8")):
        if "shares" in r["applies_to"].split(";"):
            ev[r["event"]] = (r["first_month"], r["last_month"] or "9999-12", int(r["months"]))
    return ev


def dummies(months, events: dict) -> np.ndarray:
    """(T, n_events) 0/1: the `months` field of events.csv is the calendar month (12 = Dec)."""
    D = np.zeros((len(months), len(events)))
    for j, (first, last, mo) in enumerate(events.values()):
        for i, m in enumerate(months):
            D[i, j] = float(first <= m <= last and int(m[5:]) == mo)
    return D


def month_time(months) -> np.ndarray:
    """Mid-month in years minus T_REF."""
    return np.array([int(m[:4]) + (int(m[5:]) - 0.5) / 12 - T_REF for m in months])


def load_counts(path: Path = ROOT / "Data" / "panels" / "fuel4_monthly.csv", start: str = START,
                end: str | None = None) -> dict:
    """Monthly counts by fuel in [start, end]; raises on gaps, missing fuels or empty months."""
    n = {}
    for r in csv.DictReader(path.open(encoding="utf-8")):
        m = r["month"]
        if m >= start and (end is None or m <= end) and r["fuel4"] in ALL:
            if r["fuel4"] in n.get(m, {}):
                raise ValueError(f"duplicate row {m} {r['fuel4']}")
            n.setdefault(m, {})[r["fuel4"]] = int(r["new_reg"])
    months = sorted(n)
    for a, b in zip(months, months[1:]):
        if _next_month(a) != b:
            raise ValueError(f"gap in monthly panel between {a} and {b}")
    for m in months:
        if set(n[m]) != set(ALL):
            raise ValueError(f"missing fuel in {m}: {sorted(set(ALL) - set(n[m]))}")
    N = np.array([[n[m][f] for f in ALL] for m in months], float)
    nb, nn = N[:, 0], N[:, 1:].sum(1)
    yB = np.log((nb + 0.5) / (nn + 0.5))[:, None]
    VB = (1 / (nb + 0.5) + 1 / (nn + 0.5))[:, None, None]
    ip, idx = ALL.index("petrol"), [ALL.index(f) for f in REST]
    yR = np.log((N[:, idx] + 0.5) / (N[:, [ip]] + 0.5))
    VR = np.zeros((len(months), len(REST), len(REST))) + (1 / (N[:, ip] + 0.5))[:, None, None]
    VR[:, np.arange(len(REST)), np.arange(len(REST))] += 1 / (N[:, idx] + 0.5)
    return {"months": months, "t": month_time(months), "N": N, "yB": yB, "VB": VB, "yR": yR, "VR": VR}


# ---------------------------------------------------------------- curve and filter

def bev_curve(xp, t, c, k, t0):
    """c * logistic(k (t - t0)): BEV share on the diffusion curve."""
    return c / (1 + xp.exp(-k * (t - t0)))


def bev_curve_logit(xp, t, c, k, t0):
    """logit(c L): log(c L / (1 - c L)) = log c - log(1 + e^{-z} - c), z = k (t - t0); stable."""
    z = k * (t - t0)
    return xp.log(c) - xp.log1p(xp.exp(-z) - c)


def kalman(y, V, offset, F, Q, H, R0, m0, P0):
    """Gaussian state space: s_t = F s_{t-1} + w, y_t = H s_t + offset_t + e,
    e ~ N(0, V_t + R0). Returns the log-likelihood and the last filtered mean and cov (JAX)."""
    import jax
    import jax.numpy as jnp
    K = y.shape[1]

    def step(carry, inp):
        m, P, ll = carry
        yt, Vt, ot = inp
        m, P = F @ m, F @ P @ F.T + Q
        S = H @ P @ H.T + Vt + R0
        L = jnp.linalg.cholesky(S)
        r = yt - H @ m - ot
        a = jax.scipy.linalg.cho_solve((L, True), r)
        ll = ll - 0.5 * (r @ a) - jnp.sum(jnp.log(jnp.diag(L))) - 0.5 * K * jnp.log(2 * jnp.pi)
        G = jax.scipy.linalg.cho_solve((L, True), H @ P).T
        m = m + G @ r
        P = P - G @ S @ G.T
        return (m, 0.5 * (P + P.T), ll), None

    (m, P, ll), _ = jax.lax.scan(step, (m0, P0, 0.0), (y, V, offset))
    return ll, m, P


def llt_system(xp, K, phi, s_level, s_drift):
    """Stacked (levels, drifts) transition and noise for K damped local linear trends."""
    I, Z = xp.eye(K), xp.zeros((K, K))
    F = xp.concatenate([xp.concatenate([I, I], 1), xp.concatenate([Z, phi * I], 1)], 0)
    Q = xp.diag(xp.concatenate([s_level ** 2, s_drift ** 2]))
    H = xp.concatenate([I, Z], 1)
    return F, Q, H


def llt_init(y):
    K = y.shape[1]
    return np.concatenate([y[0], np.zeros(K)]), np.diag(np.concatenate([np.full(K, 4.0), np.full(K, 0.1 ** 2)]))


def _bev_parts(jnp, t, X, c, k, t0, gamma_b, rho, s_ar, s_obs):
    off = (bev_curve_logit(jnp, jnp.asarray(t), c, k, t0) + jnp.asarray(X) @ gamma_b)[:, None]
    F, Q, H = rho.reshape(1, 1), (s_ar ** 2).reshape(1, 1), jnp.ones((1, 1))
    R0 = (s_obs ** 2).reshape(1, 1)
    return off, F, Q, H, R0, jnp.zeros(1), (s_ar ** 2 / (1 - rho ** 2)).reshape(1, 1)


# ---------------------------------------------------------------- models

def model_bev(t, y, V, X, c_prior=C_PRIOR):
    import jax.numpy as jnp
    import numpyro
    import numpyro.distributions as dist
    c = numpyro.sample("c", dist.TruncatedNormal(c_prior[0], c_prior[1], low=c_prior[2], high=c_prior[3]))
    k = numpyro.sample("k", dist.LogNormal(jnp.log(0.8), 0.5))          # per year
    t0 = numpyro.sample("t0", dist.Normal(4.0, 3.0))                    # midpoint, years after 2020
    gamma = numpyro.sample("gamma", dist.Normal(0, 0.5).expand([X.shape[1]]).to_event(1))
    rho = numpyro.sample("rho", dist.Uniform(0.0, 0.99))
    s_ar = numpyro.sample("s_ar", dist.HalfNormal(0.2))
    s_obs = numpyro.sample("s_obs", dist.HalfNormal(0.2))
    off, F, Q, H, R0, m0, P0 = _bev_parts(jnp, t, X, c, k, t0, gamma, rho, s_ar, s_obs)
    ll, _, _ = kalman(jnp.asarray(y), jnp.asarray(V), off, F, Q, H, R0, m0, P0)
    numpyro.factor("ll", ll)


def model_rest(y, V, X):
    import jax.numpy as jnp
    import numpyro
    import numpyro.distributions as dist
    K = y.shape[1]
    s_level = numpyro.sample("s_level", dist.HalfNormal(0.05).expand([K]).to_event(1))
    s_drift = numpyro.sample("s_drift", dist.HalfNormal(0.02).expand([K]).to_event(1))
    s_obs = numpyro.sample("s_obs", dist.HalfNormal(0.3))
    phi = numpyro.sample("phi", dist.Beta(20, 1.5))
    gamma = numpyro.sample("gamma", dist.Normal(0, 0.5).expand([K, X.shape[1]]).to_event(2))
    F, Q, H = llt_system(jnp, K, phi, s_level, s_drift)
    m0, P0 = llt_init(np.asarray(y))
    ll, _, _ = kalman(jnp.asarray(y), jnp.asarray(V), jnp.asarray(X) @ gamma.T, F, Q, H,
                      s_obs ** 2 * jnp.eye(K), jnp.asarray(m0), jnp.asarray(P0))
    numpyro.factor("ll", ll)


# ---------------------------------------------------------------- forecast

def final_states_bev(post, d, X):
    import jax
    import jax.numpy as jnp

    def one(c, k, t0, g, rho, s_ar, s_obs):
        parts = _bev_parts(jnp, d["t"], X, c, k, t0, g, rho, s_ar, s_obs)
        return kalman(jnp.asarray(d["yB"]), jnp.asarray(d["VB"]), *parts)[1:]
    m, P = jax.jit(jax.vmap(one))(*(jnp.asarray(post[k]) for k in ("c", "k", "t0", "gamma", "rho", "s_ar", "s_obs")))
    return np.asarray(m)[:, 0], np.asarray(P)[:, 0, 0]


def final_states_rest(post, d, X):
    import jax
    import jax.numpy as jnp
    K = d["yR"].shape[1]
    m0, P0 = llt_init(d["yR"])

    def one(phi, sl, sd, so, g):
        F, Q, H = llt_system(jnp, K, phi, sl, sd)
        return kalman(jnp.asarray(d["yR"]), jnp.asarray(d["VR"]), jnp.asarray(X) @ g.T, F, Q, H,
                      so ** 2 * jnp.eye(K), jnp.asarray(m0), jnp.asarray(P0))[1:]
    m, P = jax.jit(jax.vmap(one))(*(jnp.asarray(post[k]) for k in ("phi", "s_level", "s_drift", "s_obs", "gamma")))
    return np.asarray(m), np.asarray(P)


def _sigmoid(x):
    return 1 / (1 + np.exp(-x))


def forecast_bev(pb, uT, PuT, t_future, X_future, rng) -> np.ndarray:
    """BEV share draws (draws, H): curve + AR deviation (from the filtered last state) + dummies."""
    c, k, t0, rho, s_ar = (np.asarray(pb[x]) for x in ("c", "k", "t0", "rho", "s_ar"))
    u = uT + np.sqrt(np.maximum(PuT, 0)) * rng.standard_normal(len(c))
    out = np.empty((len(c), len(t_future)))
    for h, (tf, xh) in enumerate(zip(t_future, X_future)):
        u = rho * u + s_ar * rng.standard_normal(len(c))
        out[:, h] = _sigmoid(bev_curve_logit(np, tf, c, k, t0) + np.asarray(pb["gamma"]) @ xh + u)
    return out


def forecast_rest(pr, mT, PT, X_future, rng) -> np.ndarray:
    """Shares within the non-BEV remainder (draws, H, 3) in order PHEV, petrol, diesel."""
    n, K2 = mT.shape
    K = K2 // 2
    phi, sl, sd, g = (np.asarray(pr[x]) for x in ("phi", "s_level", "s_drift", "gamma"))
    Lc = np.linalg.cholesky(PT + 1e-12 * np.eye(K2))
    s = mT + np.einsum("nij,nj->ni", Lc, rng.standard_normal((n, K2)))
    a, b = s[:, :K], s[:, K:]
    out = np.empty((n, len(X_future), 3))
    for h, xh in enumerate(X_future):
        a = a + b + sl * rng.standard_normal((n, K))
        b = phi[:, None] * b + sd * rng.standard_normal((n, K))
        lg = a + np.einsum("nke,e->nk", g, xh)              # PHEV, diesel vs petrol
        z = np.stack([lg[:, 0], np.zeros(n), lg[:, 1]], -1)
        z = z - z.max(-1, keepdims=True)
        e = np.exp(z)
        out[:, h] = e / e.sum(-1, keepdims=True)
    return out


def combine(bev: np.ndarray, rest: np.ndarray) -> np.ndarray:
    """(draws, H, 4) shares in ALL order: BEV, PHEV, petrol, diesel."""
    return np.concatenate([bev[..., None], (1 - bev)[..., None] * rest], -1)


def future_months(last: str, H: int) -> list[str]:
    out, m = [], last
    for _ in range(H):
        m = _next_month(m)
        out.append(m)
    return out


# ---------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "Data" / "fits")
    ap.add_argument("--start", default=START)
    ap.add_argument("--panels", type=Path, default=ROOT / "Data" / "panels", help="panel folder (backtests)")
    ap.add_argument("--end", default=None, help="last month used (backtests), e.g. 2022-12")
    ap.add_argument("--c-prior", type=float, nargs=2, default=C_PRIOR[:2], metavar=("MEAN", "SD"))
    a = ap.parse_args(argv)
    d = load_counts(a.panels / "fuel4_monthly.csv", start=a.start, end=a.end)
    ev = load_events()
    X = dummies(d["months"], ev)
    c_prior = (a.c_prior[0], a.c_prior[1], C_PRIOR[2], C_PRIOR[3])
    # 0.99 and longer warmup: the 2024-12 backtest fit had 1 divergence at 0.95, then R-hat 1.0103
    mb = run(model_bev, d["t"], d["yB"], d["VB"], X, c_prior=c_prior, target_accept=0.99,
             warmup=2000, samples=1500)
    mr = run(model_rest, d["yR"], d["VR"], X, target_accept=0.99)
    pb = {k: np.asarray(v) for k, v in mb.get_samples().items()}
    pr = {k: np.asarray(v) for k, v in mr.get_samples().items()}
    diag = {"bev": diagnostics(mb), "rest": diagnostics(mr)}

    n_draw = 500
    sb = {k: v[np.random.default_rng(1).choice(len(pb["c"]), n_draw, replace=False)] for k, v in pb.items()}
    sr = {k: v[np.random.default_rng(2).choice(len(pr["phi"]), n_draw, replace=False)] for k, v in pr.items()}
    uT, PuT = final_states_bev(sb, d, X)
    mT, PT = final_states_rest(sr, d, X)
    last = d["months"][-1]
    fm = future_months(last, 12 * (2040 - int(last[:4])) + 12 - int(last[5:]))
    Xf, tf = dummies(fm, ev), month_time(fm)
    rng = np.random.default_rng(3)
    sh = combine(forecast_bev(sb, uT, PuT, tf, Xf, rng), forecast_rest(sr, mT, PT, Xf, rng))

    proj = {}
    for yr in range(int(fm[0][:4]), 2041):
        j = [i for i, m in enumerate(fm) if m.startswith(str(yr))]
        if len(j) == 12:
            proj[str(yr)] = {f: q(sh[:, j, i].mean(1)) for i, f in enumerate(ALL)}
    obs = {}
    for yr in sorted({m[:4] for m in d["months"]}):
        j = [i for i, m in enumerate(d["months"]) if m.startswith(yr)]
        tot = d["N"][j].sum()
        obs[yr] = {f: round(float(d["N"][j, i].sum() / tot), 4) for i, f in enumerate(ALL)}
    out = {"diagnostics": diag, "sample": [d["months"][0], last], "events": list(ev),
           "bev": {"c_prior": list(c_prior), **{k: q(pb[k]) for k in ("c", "k", "t0", "rho", "s_ar", "s_obs")},
                   "gamma": {e: q(pb["gamma"][:, j]) for j, e in enumerate(ev)}},
           "rest": {"phi": q(pr["phi"]), "s_obs": q(pr["s_obs"]),
                    "s_level": {f: q(pr["s_level"][:, i]) for i, f in enumerate(REST)},
                    "s_drift": {f: q(pr["s_drift"][:, i]) for i, f in enumerate(REST)}},
           "observed_annual": obs, "projection_annual_mean_share": proj}
    print(json.dumps({k: v for k, v in out.items() if k != "observed_annual"}, indent=1))
    if not (diag["bev"]["ok"] and diag["rest"]["ok"]):
        print("convergence gate failed; previous outputs kept", file=sys.stderr)
        return 1
    a.out.mkdir(parents=True, exist_ok=True)
    npz = {**{f"bev_{k}": v for k, v in pb.items()}, **{f"rest_{k}": v for k, v in pr.items()}}
    _write_atomic(a.out / "shares.npz", lambda f: np.savez_compressed(f, **npz))
    _write_atomic(a.out / "shares.json", lambda f: f.write_text(json.dumps(out, indent=2), "utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
