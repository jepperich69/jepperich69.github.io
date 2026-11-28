"""Verification of ev_fleet_methods.tex (math + numeric claims). Re-runnable, self-contained."""
import sys, os, re, json
from decimal import Decimal, ROUND_HALF_UP
sys.path.insert(0, r"C:\Users\rich\.claude\skills\verify-math\scripts")
try:
    from render_math import render
except Exception as e:  # presentation only
    def render(expr, label=""):
        return "render unavailable"
import sympy as sp
from sympy import (symbols, Symbol, Eq, exp, log, limit, oo, simplify, expand, Rational, Float,
                   sqrt, diff, Max, Piecewise, solve, Integer)
import sympy.stats as st

EV = r"<path to the model project folder>"  # set before running
DATA = os.path.join(EV, "Data")
OUT = os.path.dirname(os.path.abspath(__file__))
NUMS = os.path.join(EV, "Methods", "numbers.tex")

def jl(*p):
    with open(os.path.join(DATA, *p), encoding="utf-8") as f:
        t = f.read()
    return json.loads(t.replace("NaN", "null"))

def rnd(x, d):
    q = Decimal(1).scaleb(-d)
    return float(Decimal(repr(float(x))).quantize(q, rounding=ROUND_HALF_UP))

RES = []

def rep(label, bucket, ok, checked, got, stated, expr=None, note=""):
    status = "PASS" if ok else "FAIL"
    line = f"{label} | {bucket} | {status} | checked: {checked} | got: {got} vs stated: {stated}"
    print(line)
    try:
        r = render(expr, label=label) if expr is not None else "render unavailable"
    except Exception as e:
        r = "render unavailable"
    print(r)
    RES.append(dict(label=label, bucket=bucket, status=status, checked=str(checked), got=str(got),
                    stated=str(stated), render=r, note=note))

def err(label, bucket, checked, e):
    line = f"{label} | {bucket} | ERROR | checked: {checked} | got: {type(e).__name__}: {e} vs stated: -"
    print(line)
    RES.append(dict(label=label, bucket=bucket, status="ERROR", checked=str(checked),
                    got=f"{type(e).__name__}: {e}", stated="-", render="render unavailable", note=""))

def safe(label, bucket, checked, fn):
    try:
        fn()
    except Exception as e:
        err(label, bucket, checked, e)

# ---------------------------------------------------------------- numbers.tex macros
macros = {}
txt = open(NUMS, encoding="utf-8").read()
for m in re.finditer(r"\\newcommand\{\\(\w+)\}\{(.*?)\}\n(?=\\newcommand|\Z)", txt, flags=re.S):
    macros[m.group(1)] = m.group(2)
def mnum(k):
    return float(macros[k].replace("{,}", "").replace("k", ""))

# ================================================================= IDENTITY / SOLVE / MOMENT (symbolic)
# --- Eq exits: solve for X_y
def c_exits():
    Xy, Xp, R, E = symbols("X_y X_prev R E", real=True)
    sol = solve(Eq(E, Xp + R - Xy), Xy)[0]
    claimed = Xp + R - E
    ok = simplify(sol - claimed) == 0
    rep("eq:exits-solve-stock", "SOLVE", ok, "solve(E = Xprev + R - X, X) vs Xprev + R - E",
        sol, claimed, Eq(Xy, sol, evaluate=False))
safe("eq:exits-solve-stock", "SOLVE", "solve E for X", c_exits)

# --- sales identity: sales = change in total stock + total net exits (sum over 4 fuels)
def c_sales():
    Xp = symbols("Xp1:5", real=True); X = symbols("X1:5", real=True); R = symbols("R1:5", real=True)
    E = [Xp[i] + R[i] - X[i] for i in range(4)]
    sol = sum(R)
    claimed = (sum(X) - sum(Xp)) + sum(E)
    ok = simplify(expand(sol - claimed)) == 0
    rep("sales-identity (Sec.3.1 total exit rate, 4 fuels)", "IDENTITY", ok,
        "sum_f R_f - [(sum X_f - sum Xprev_f) + sum E_f] with E_f from eq:exits, f=1..4", simplify(expand(sol - claimed)), 0,
        Eq(sum(R), (sum(X) - sum(Xp)) + sum(E), evaluate=False))
safe("sales-identity", "IDENTITY", "sales = dStock + exits", c_sales)

# --- residual rule: BEV stock = total - others (Sec. exits by fuel / BEV scrappage)
def c_resid():
    Xp_t, R_t, E_t = symbols("Xp_tot R_tot E_tot", real=True)
    Xp_o = symbols("Xp_o1:4", real=True); R_o = symbols("R_o1:4", real=True); E_o = symbols("E_o1:4", real=True)
    Xp_b, R_b = symbols("Xp_bev R_bev", real=True)
    # total identity: Xp_tot = Xp_b + sum Xp_o, R_tot = R_b + sum R_o
    Xp_t_ = Xp_b + sum(Xp_o); R_t_ = R_b + sum(R_o)
    X_tot = Xp_t_ + R_t_ - E_t
    X_o = [Xp_o[i] + R_o[i] - E_o[i] for i in range(3)]
    E_b = E_t - sum(E_o)  # BEV net exits = scrappage - imports = total net exits - other exits
    X_b = Xp_b + R_b - E_b
    diffe = simplify(expand(X_b - (X_tot - sum(X_o))))
    rep("residual-rule BEV=total-others", "IDENTITY", diffe == 0,
        "X_bev(update with E_bev=E_tot - sum E_other) - (X_tot - sum X_other)", diffe, 0,
        Eq(X_b, X_tot - sum(X_o), evaluate=False))
safe("residual-rule BEV=total-others", "IDENTITY", "BEV = total - others", c_resid)

# --- imports affect BEV stock only when floor binds
def c_floor():
    A, I = symbols("A I", real=True)  # A = E_tot - sum E_other
    scrap = Max(0, A + I)
    net = scrap - I
    # unfloored branch (A+I>0): net = A, so d net / dI = 0
    unf = simplify(diff(A + I - I, I))
    # floored branch (A+I<=0): net = -I, d net / dI = -1
    flo = simplify(diff(-I, I))
    ok = (unf == 0) and (flo == -1)
    rep("floor-imports-effect", "IDENTITY", ok, "d/dI[max(0,A+I)-I]: branch A+I>0 and branch A+I<=0",
        f"{unf} and {flo}", "0 (floor slack), nonzero (floor binds)",
        Eq(net, Piecewise((A, A + I > 0), (-I, True)), evaluate=False))
safe("floor-imports-effect", "IDENTITY", "floor", c_floor)

# --- Gompertz
S, b, r, t, c0 = symbols("S b r t c0", positive=True)
def c_g1():
    lhs = log(S * exp(-b * exp(-r * t)))
    rhs = log(S) - b * exp(-r * t)
    d = simplify(expand_l := sp.expand_log(lhs - rhs, force=True))
    rep("eq:gompertz-log-split", "IDENTITY", d == 0, "log(S exp(-b e^{-rt})) - (log S - b e^{-rt})", d, 0,
        Eq(lhs, rhs, evaluate=False))
safe("eq:gompertz-log-split", "IDENTITY", "log split", c_g1)

def c_g2():
    bb = log(S / c0)
    val = simplify(S * exp(-bb * exp(-r * 0)))
    ok = simplify(val - c0) == 0
    rep("eq:gompertz-start-level", "IDENTITY", ok, "S*exp(-b e^{-r*0}) with b=log(S/c0) equals c0", val, c0,
        Eq(S * exp(-bb), c0, evaluate=False))
safe("eq:gompertz-start-level", "IDENTITY", "c(0)=c0", c_g2)

def c_g3():
    lim = limit(S * exp(-b * exp(-r * t)), t, oo)
    rep("eq:gompertz-ceiling", "IDENTITY", simplify(lim - S) == 0, "lim_{t->oo} S exp(-b e^{-rt}) = S (saturation level)", lim, S,
        Eq(sp.Limit(S * exp(-b * exp(-r * t)), t, oo), lim, evaluate=False))
safe("eq:gompertz-ceiling", "IDENTITY", "limit", c_g3)

# --- logistic share curve
cb, k, t0 = symbols("cbar k t0", positive=True)
def c_s1():
    f = cb / (1 + exp(-k * (t - t0)))
    lim = limit(f, t, oo)
    rep("eq:share-ceiling", "IDENTITY", simplify(lim - cb) == 0, "lim_{t->oo} cbar/(1+e^{-k(t-t0)}) = cbar", lim, cb,
        Eq(sp.Limit(f, t, oo), lim, evaluate=False))
    mid = simplify(f.subs(t, t0))
    rep("eq:share-midpoint", "IDENTITY", simplify(mid - cb / 2) == 0, "curve at t=t0 equals cbar/2", mid, cb / 2,
        Eq(f.subs(t, t0), mid, evaluate=False))
    d = simplify(diff(f, t))
    pos = simplify(d * (1 + exp(-k * (t - t0))) ** 2 / (cb * k * exp(-k * (t - t0))))
    rep("eq:share-monotone", "IDENTITY", simplify(pos - 1) == 0,
        "d/dt curve = cbar k e^{-k(t-t0)}/(1+e^{-k(t-t0)})^2 > 0 (positive for k,cbar>0)", pos, 1,
        Eq(sp.Derivative(f, t), d, evaluate=False))
    rem = limit(1 - f, t, oo)
    rep("remainder-shrinks-to-1-cbar", "IDENTITY", simplify(rem - (1 - cb)) == 0, "lim 1 - s_t = 1 - cbar (Remaining fuels)", rem, 1 - cb,
        Eq(sp.Limit(1 - f, t, oo), rem, evaluate=False))
safe("eq:share", "IDENTITY", "share limits", c_s1)

# --- sampling variance of logit
def c_var():
    n, p = symbols("n p", positive=True)
    nb = n * p; no = n * (1 - p)
    v_delta = 1 / (n * p * (1 - p))  # delta method for Var(logit(phat)), phat~Bin(n,p)/n
    d = simplify(v_delta - (1 / nb + 1 / no))
    rep("eq:share-obs-variance", "MOMENT", d == 0, "delta-method Var(logit phat)=1/(n p(1-p)) vs 1/n_BEV+1/n_other", d, 0,
        Eq(v_delta, 1 / nb + 1 / no, evaluate=False))
safe("eq:share-obs-variance", "MOMENT", "delta", c_var)

# --- rate link
def c_rate():
    r0, dl, al, y0, y = symbols("r0 delta alpha y0 y", real=True)
    al_ = Symbol("alpha", nonnegative=True)
    rt = r0 + dl + al_ * (y0 - y)
    start = simplify(rt.subs(y, y0) - (r0 + dl))
    rep("eq:rate-start", "IDENTITY", start == 0, "r at y_t=y_0 equals r0+delta ('starts at observed rate')", start, 0,
        Eq(rt.subs(y, y0), r0 + dl, evaluate=False))
    rise = simplify(rt.subs(y, 0) - rt.subs(y, y0))
    dy = diff(rt, y)
    ok = simplify(rise - al_ * y0) == 0 and dy == -al_
    rep("eq:rate-max-rise", "IDENTITY", ok, "r(y=0)-r(y=y0) = alpha*y0 and dr/dy = -alpha<=0 so rise bounded by alpha*y0", f"{rise}; dr/dy={dy}", "alpha*y0",
        Eq(rt.subs(y, 0) - rt.subs(y, y0), rise, evaluate=False))
safe("eq:rate", "IDENTITY", "rate", c_rate)

def c_rate2():
    r0, dl, be, s, s0 = symbols("r0 delta beta sbar sbar0", real=True)
    rt = r0 + dl + be * (s - s0)
    d = simplify(rt.subs(s, s0) - (r0 + dl))
    rep("eq:rateshare-start", "IDENTITY", d == 0, "share-link rate at sbar_t=sbar_0 equals r0+delta", d, 0,
        Eq(rt.subs(s, s0), r0 + dl, evaluate=False))
safe("eq:rateshare", "IDENTITY", "rateshare", c_rate2)

# --- lognormal kappa: mean and sd recovered
def c_lognorm():
    m, s = symbols("m s", positive=True)
    mu = log(m ** 2 / sqrt(m ** 2 + s ** 2)); sg2 = log(1 + s ** 2 / m ** 2)
    mean = simplify(sp.expand_log(exp(mu + sg2 / 2), force=True))
    var = simplify(sp.expand_log((exp(sg2) - 1) * exp(2 * mu + sg2), force=True))
    ok = simplify(mean - m) == 0 and simplify(var - s ** 2) == 0
    mval, sval = Rational(68, 100), Rational(13, 100)
    muv = float(mu.subs({m: mval, s: sval})); sgv = float(sp.sqrt(sg2.subs({m: mval, s: sval})))
    X = st.LogNormal("X", muv, sgv)
    import mpmath as mp
    pdf = sp.lambdify(sp.Symbol("x"), st.density(X)(sp.Symbol("x")), "mpmath")
    em = float(mp.quad(lambda x: x * pdf(x), [0, 1, mp.inf]))
    es = float(mp.sqrt(mp.quad(lambda x: (x - em) ** 2 * pdf(x), [0, 1, mp.inf])))
    ok2 = abs(em - 0.68) < 1e-9 and abs(es - 0.13) < 1e-9
    rep("eq:imports-lognormal", "MOMENT", ok and ok2,
        "LogNormal(mu=log(m^2/sqrt(m^2+s^2)), sigma^2=log(1+s^2/m^2): mean=m, sd=s; sympy.stats at m=0.68,s=0.13",
        f"mean={em:.6f}, sd={es:.6f}", "mean 0.68, sd 0.13", Eq(sp.Symbol("E[kappa]"), mean, evaluate=False))
safe("eq:imports-lognormal", "MOMENT", "lognormal", c_lognorm)

# --- Eurostat prior centering
def c_prior():
    vals = [0.60, 0.64, 0.65, 0.71]
    mean = sum(vals) / 4
    sd_s = (sum((v - mean) ** 2 for v in vals) / 3) ** 0.5
    rep("prior-S-center", "NUMERIC", abs(mean - 0.65) < 5e-4,
        "mean(Sweden .60, NL .64, Norway .65, Germany .71)", f"mean={mean:.4f} (sample sd {sd_s:.4f}; prior sd stated 0.04)", "0.65",
        Eq(Symbol("mean(0.60,0.64,0.65,0.71)"), Float(mean, 4), evaluate=False))
safe("prior-S-center", "NUMERIC", "mean", c_prior)

# ================================================================= NUMERIC vs model outputs
sim = jl("fits", "simulation.json"); shr = jl("fits", "shares.json"); tot = jl("fits", "total.json")
exi = jl("fits", "exits.json"); bt = jl("backtest", "backtest.json")
link = sim["link"]

# --- rate cap r0 + alpha*y0
def c_rmax(fuel, mac_r, mac_a, mac_y, stated_key):
    def f():
        L = link[fuel]
        val = 100 * (L["r0"] + L["a"] * L["y0"])
        val_mac = 100 * (mnum(mac_r) / 100 + mnum(mac_a) * mnum(mac_y))
        stated = mnum(stated_key)
        ok = abs(rnd(val, 1) - stated) < 1e-9
        r0s, as_, y0s = symbols("r0 alpha y0")
        rep(f"rMax-{fuel}", "NUMERIC", ok, f"100*(r0+alpha*y0) with unrounded json r0,a,y0 ({fuel}); also from rounded macros = {val_mac:.3f}",
            f"{val:.4f} -> {rnd(val,1)}", stated, Eq(r0s + as_ * y0s, Float(val, 5), evaluate=False))
    safe(f"rMax-{fuel}", "NUMERIC", "rmax", f)
c_rmax("diesel", "rDiesel", "aDiesel", "yDiesel", "rMaxDiesel")
c_rmax("petrol", "rPetrol", "aPetrol", "yPetrol", "rMaxPetrol")

# --- macros vs json
def cm(label, got, dec, key, scale=1.0):
    def f():
        g = rnd(got * scale, dec)
        s = mnum(key)
        rep(label, "NUMERIC", abs(g - s) < 1e-9, f"round(json value*{scale}, {dec})", f"{got*scale:.5f} -> {g}", s,
            Eq(Symbol(label), Float(g, 6), evaluate=False))
    safe(label, "NUMERIC", "macro", f)
cm("macro:Smed", tot["cars_per_adult"]["S"][1], 2, "Smed")
cm("macro:Slo", tot["cars_per_adult"]["S"][0], 2, "Slo")
cm("macro:Shi", tot["cars_per_adult"]["S"][2], 2, "Shi")
cm("macro:rGomp", tot["cars_per_adult"]["r"][1], 3, "rGomp")
cm("macro:rhoCpa", tot["cars_per_adult"]["rho"][1], 3, "rhoCpa")
cm("macro:exitLR(%)", tot["exit_rate"]["rate"]["long_run_median"][1], 1, "exitLR", 100)
cm("macro:exitPhi", tot["exit_rate"]["phi"][1], 2, "exitPhi")
cm("macro:cMed", shr["bev"]["c"][1], 3, "cMed"); cm("macro:cLo", shr["bev"]["c"][0], 3, "cLo"); cm("macro:cHi", shr["bev"]["c"][2], 3, "cHi")
cm("macro:kMed", shr["bev"]["k"][1], 2, "kMed")
cm("macro:rhoBev", shr["bev"]["rho"][1], 2, "rhoBev")
cm("macro:gPull", shr["bev"]["gamma"]["yearend_pull"][1], 2, "gPull")
p30 = shr["projection_annual_mean_share"]["2030"]["BEV"]
cm("macro:shareTwoThirty", p30[1], 2, "shareTwoThirty"); cm("macro:shareTwoThirtyLo", p30[0], 2, "shareTwoThirtyLo"); cm("macro:shareTwoThirtyHi", p30[2], 2, "shareTwoThirtyHi")
cm("macro:aDiesel", link["diesel"]["a"], 3, "aDiesel"); cm("macro:aDieselSe", link["diesel"]["a_se"], 3, "aDieselSe")
cm("macro:aPetrol", link["petrol"]["a"], 3, "aPetrol"); cm("macro:aPetrolSe", link["petrol"]["a_se"], 3, "aPetrolSe")
cm("macro:bDiesel", link["diesel"]["b"], 3, "bDiesel"); cm("macro:bPetrol", link["petrol"]["b"], 3, "bPetrol")
cm("macro:yDiesel", link["diesel"]["y0"], 2, "yDiesel"); cm("macro:yPetrol", link["petrol"]["y0"], 2, "yPetrol")
cm("macro:phiDiesel", link["diesel"]["phi"], 2, "phiDiesel"); cm("macro:phiPetrol", link["petrol"]["phi"], 2, "phiPetrol")
cm("macro:rDiesel(%)", link["diesel"]["r0"], 1, "rDiesel", 100); cm("macro:rPetrol(%)", link["petrol"]["r0"], 1, "rPetrol", 100)
cm("macro:rPHEV(%)", link["PHEV"]["r0"], 1, "rPHEV", 100)
cm("macro:pDiesel(%)", sim["milestones"]["diesel_below_100k"]["p_by_horizon"], 0, "pDiesel", 100)
cm("macro:pNinety(%)", sim["milestones"]["plugin_90pct_fleet"]["p_by_horizon"], 0, "pNinety", 100)
for fuel, key in [("BEV", "bevFortyK"), ("petrol", "petrolFortyK"), ("diesel", "dieselFortyK"), ("total", "totalFortyK")]:
    cm(f"macro:{key}", sim["stock_1jan_thousands"]["2040"][fuel][1], 0, key)

def c_t0():
    got = 2020 + shr["bev"]["t0"][1]
    rep("macro:tzero", "NUMERIC", abs(rnd(got, 1) - mnum("tzero")) < 1e-9, "2020 + t0 (assumes t counted in years from 2020; assumption)", f"{got:.3f}", mnum("tzero"),
        Eq(Symbol("2020+t0"), Float(got, 5), evaluate=False))
safe("macro:tzero", "NUMERIC", "t0", c_t0)

# milestone macros
MON = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
def fmt(s):
    y, m = s.split("-"); return f"{MON[int(m)-1]} {y}"
for ms, tag in [("bev_1m", "msOneM"), ("bev_above_petrol", "msAbovePetrol"), ("bev_half_fleet", "msHalf")]:
    for fld, suf in [("median", ""), ("q05", "Lo"), ("q95", "Hi")]:
        def f(ms=ms, tag=tag, fld=fld, suf=suf):
            got = fmt(sim["milestones"][ms][fld]); st_ = macros[tag + suf]
            rep(f"macro:{tag}{suf}", "NUMERIC", got == st_, f"simulation.json milestones.{ms}.{fld}", got, st_,
                Eq(Symbol(tag + suf), Symbol(got.replace(" ", "_")), evaluate=False))
        safe(f"macro:{tag}{suf}", "NUMERIC", "milestone", f)

def c_sim_meta():
    ok = sim["draws"] == 500 and sim["horizon"] == "2040-12" and fmt(sim["last_obs"]) == macros["Vintage"]
    rep("sim-meta", "NUMERIC", ok, "draws==500, horizon 2040-12, last_obs 2026-10 == Vintage",
        f"{sim['draws']}, {sim['horizon']}, {fmt(sim['last_obs'])}", f"500, December 2040, {macros['Vintage']}",
        Eq(Symbol("draws"), Integer(sim["draws"]), evaluate=False))
safe("sim-meta", "NUMERIC", "meta", c_sim_meta)

def c_sum40():
    s = sim["stock_1jan_thousands"]["2040"]
    tot_ = s["total"][1]; parts = sum(s[f][1] for f in ["BEV", "PHEV", "petrol", "diesel"])
    rep("medians-2040-add-up (info)", "NUMERIC", abs(parts - tot_) / tot_ < 0.01,
        "sum of fuel medians vs median total (1% tolerance; medians need not add exactly)", f"{parts:.1f} vs {tot_:.1f}",
        "text implies composition within the total", Eq(Symbol("sum medians"), Float(parts, 6), evaluate=False))
safe("medians-2040-add-up", "NUMERIC", "sum", c_sum40)

# --- observed exit rates
yrs = exi["history"]["years"]; s0 = exi["history"]["stock0"]; ex = exi["history"]["exits"]
def rate(f, y):
    i = yrs.index(y); return 100 * ex[f][i] / s0[f][i]
for (f, y, stated, lab) in [("petrol", 2020, 5.0, "petrol 2020 5.0%"), ("diesel", 2020, 4.9, "diesel 2020 4.9%"),
                             ("petrol", 2025, mnum("rPetrol"), "petrol 2025"), ("diesel", 2025, mnum("rDiesel"), "diesel 2025"),
                             ("petrol", 2019, 6.7, "petrol 2019 6.7%")]:
    def fn(f=f, y=y, stated=stated, lab=lab):
        g = rate(f, y)
        rep(f"exit-rate:{lab}", "NUMERIC", abs(rnd(g, 1) - stated) < 1e-9, f"100*exits/stock0 ({f}, {y}) from exits.json", f"{g:.3f} -> {rnd(g,1)}", stated,
            Eq(Symbol(f"E/X[{f},{y}]"), Float(g, 5), evaluate=False))
    safe(f"exit-rate:{lab}", "NUMERIC", "rate", fn)

def c_pet2022():
    vals = [rate("petrol", y) for y in (2020, 2021, 2022)]
    rep("exit-rate:petrol 2020-22 'about 5%'", "NUMERIC", all(4.5 <= v <= 5.5 for v in vals), "petrol exit rate 2020,2021,2022 in [4.5,5.5]", [round(v, 2) for v in vals], "about 5%",
        Eq(Symbol("mean rate 2020-22"), Float(sum(vals) / 3, 5), evaluate=False))
safe("exit-rate:petrol 2020-22", "NUMERIC", "rate", c_pet2022)

def c_se():
    a, se = link["petrol"]["a"], link["petrol"]["a_se"]
    rep("petrol-slope-SE>half", "NUMERIC", se > a / 2, "a_se/a > 0.5", f"{se/a:.3f}", "> 0.5 ('more than half its value')",
        Eq(Symbol("se/a"), Float(se / a, 4), evaluate=False))
    n = link["petrol"]["n_years_age"]
    rep("ten-annual-observations", "NUMERIC", n == 10 and link["diesel"]["n_years_age"] == 10, "n_years_age (2016..2025)", n, 10,
        Eq(Symbol("n"), Integer(n), evaluate=False))
safe("petrol-slope-SE", "NUMERIC", "se", c_se)

# --- imports and kappa
def c_imports():
    import csv
    reg = {}
    with open(os.path.join(DATA, "panels", "fuel4_monthly.csv"), encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["fuel4"] == "BEV":
                y = int(row["month"][:4]); reg[y] = reg.get(y, 0) + float(row["new_reg"])
    fuels = ["BEV", "PHEV", "petrol", "diesel", "other"]
    ratios = {}; imps = {}
    for y in range(2021, 2026):
        i = yrs.index(y)
        fr = sum(ex[f][i] for f in fuels) / sum(s0[f][i] for f in fuels)
        scrap = fr * s0["BEV"][i]
        imp = scrap - ex["BEV"][i]
        imps[y] = imp; ratios[y] = imp / reg[y]
    lo, hi = min(ratios.values()), max(ratios.values())
    rep("imports-2025", "NUMERIC", rnd(imps[2025] / 1000, 0) == mnum("impTwoThousandTwentyFive"),
        "imports = fleet-rate*BEV stock0 - BEV net exits, 2025 (k cars)", f"{imps[2025]:.0f}", macros["impTwoThousandTwentyFive"],
        Eq(Symbol("I_2025"), Float(imps[2025], 6), evaluate=False))
    rep("imports-share-range-2021-25", "NUMERIC", rnd(lo, 2) == 0.45 and rnd(hi, 2) == 0.73,
        "min/max of imports/new BEV registrations over 2021..2025", f"{ {y: round(v,3) for y,v in ratios.items()} } min={lo:.3f} max={hi:.3f}", "between 45% and 73%",
        Eq(Symbol("range"), Symbol(f"[{lo:.2f},{hi:.2f}]"), evaluate=False))
    rep("kappa-latest-ratio", "NUMERIC", rnd(ratios[2025], 2) == mnum("kappaVal"), "imports_2025 / R_BEV_2025", f"{ratios[2025]:.3f}", macros["kappaVal"],
        Eq(Symbol("kappa_2025"), Float(ratios[2025], 4), evaluate=False))
    import statistics
    sd3 = statistics.stdev([ratios[y] for y in (2023, 2024, 2025)])
    rep("kappa-sd-last-3y", "NUMERIC", rnd(sd3, 2) == mnum("kappaSd"), "sample sd of ratio 2023-2025", f"{sd3:.3f}", macros["kappaSd"],
        Eq(Symbol("sd(kappa)"), Float(sd3, 4), evaluate=False))
safe("imports", "NUMERIC", "imports", c_imports)

# --- observed 2026 BEV share >80%; residual class < 100; glitch
def c_misc():
    g = shr["observed_annual"]["2026"]["BEV"]
    rep("BEV-share-2026>80%", "NUMERIC", g > 0.8, "observed_annual 2026 BEV share (partial year)", g, "> 80%", Eq(Symbol("s_2026"), Float(g, 4), evaluate=False))
safe("misc", "NUMERIC", "misc", c_misc)

def c_other():
    import csv
    rows = {}
    with open(os.path.join(DATA, "panels", "fuel4_monthly.csv"), encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.setdefault(row["month"], {})[row["fuel4"]] = float(row["stock"])
    last = sorted(rows)[-1]; o = rows[last]["other"]
    mx = max(rows[m]["other"] for m in rows if m >= "2012-01")
    rep("residual-class<100", "NUMERIC", o < 100, f"stock of 'other' in last month {last} (max since 2012: {mx:.0f})", o, "fewer than 100 cars",
        Eq(Symbol("other"), Float(o, 5), evaluate=False))
    tot_ = {m: sum(rows[m].values()) for m in rows}
    gl = tot_["2011-12"] - (tot_["2011-11"] + tot_["2012-01"]) / 2
    rep("glitch-Dec2011", "NUMERIC", abs(gl - 38000) < 3000, "total(2011-12) - mean(total 2011-11, 2012-01)", f"{gl:.0f}", "about 38,000",
        Eq(Symbol("glitch"), Float(gl, 6), evaluate=False))
safe("residual-glitch", "NUMERIC", "panel", c_other)

# --- backtest table
rows = [r_.strip() for r_ in macros["BacktestRows"].split("\\\\") if r_.strip()]
KEYMAP = {3: "model", 4: "model_share+sales", 5: "model_flat+level", 6: "frozen_shares", 7: "linear"}
NAMES = {3: "Model", 4: "Share link", 5: "Earlier model", 6: "Frozen shares", 7: "Linear"}
def parse_cell(c):
    star = "^{*}" in c
    c = c.replace("$^{*}$", "").replace("$-$", "-").replace("{,}", "").replace("$", "").strip()
    return float(c), star
table = {}
for row in rows:
    cells = [c.strip() for c in row.split("&")]
    origin, months = cells[0], cells[1]
    obs = float(cells[2].replace("{,}", ""))
    ent = next(e for e in bt if e["origin"] == origin)
    table[(origin, months)] = {}
    def f_obs(origin=origin, months=months, obs=obs, ent=ent):
        a = ent["model"][months]["BEV"]["actual"]
        rep(f"tab:backtest {origin} h{months} observed", "NUMERIC", a == obs, "BEV actual in backtest.json", a, obs,
            Eq(Symbol(f"obs[{origin},{months}]"), Float(a, 7), evaluate=False))
    safe(f"tab:backtest {origin} h{months} observed", "NUMERIC", "obs", f_obs)
    for j in range(3, 8):
        def f_c(j=j, cells=cells, origin=origin, months=months, ent=ent):
            val, star = parse_cell(cells[j])
            rec = ent[KEYMAP[j]][months]
            rec = rec["BEV"] if "BEV" in rec else dict(rec, in80=None)
            g = rnd(100 * rec["pct_err"], 1)
            ok = abs(g - val) < 1e-9
            if j == 3:
                ok = ok and (star == bool(rec["in80"]))
            rep(f"tab:backtest {origin} h{months} {NAMES[j]}", "NUMERIC", ok, f"round(100*pct_err, 1) from backtest.json[{KEYMAP[j]}]" + (" and star==in80" if j == 3 else ""),
                f"{100*rec['pct_err']:.3f} -> {g}" + (f", in80={rec['in80']}" if j == 3 else ""), f"{val}" + ("*" if star else ""),
                Eq(Symbol(f"err[{NAMES[j]},{origin},{months}]"), Float(g, 4), evaluate=False))
        safe(f"tab:backtest {origin} h{months} {NAMES[j]}", "NUMERIC", "cell", f_c)
        try:
            _r = ent[KEYMAP[j]][months]
            table[(origin, months)][j] = (parse_cell(cells[j])[0], _r["BEV"]["in80"] if "BEV" in _r else None)
        except Exception:
            pass

def c_bt_claims():
    # beats baselines everywhere; age <= share everywhere
    def a(o, m, j): return abs(table[(o, m)][j][0])
    keys = list(table)
    beats = all(a(o, m, 3) < a(o, m, 6) and a(o, m, 3) < a(o, m, 7) for o, m in keys)
    rep("bt:model-beats-both-baselines", "NUMERIC", beats, "|err model| < |err frozen| and < |err linear| in all 7 cells", beats, True,
        Eq(Symbol("all cells"), sp.true if beats else sp.false, evaluate=False))
    ok = all(a(o, m, 3) <= a(o, m, 4) for o, m in keys)
    rep("bt:age<=share-everywhere", "NUMERIC", ok, "|err model| <= |err share link| in all cells", ok, True,
        Eq(Symbol("all cells"), sp.true if ok else sp.false, evaluate=False))
    gains = {k_: a(*k_, 4) - a(*k_, 3) for k_ in keys}
    best = max(gains, key=gains.get)
    rep("bt:largest-gain-2020-36", "NUMERIC", best == ("2020-12", "36") and rnd(a("2020-12", "36", 3), 0) == 7 and rnd(a("2020-12", "36", 4), 0) == 18,
        "argmax of |share|-|model| and its rounded errors (7 vs 18)", f"argmax={best}; gains={ {f'{k_[0]}/{k_[1]}': round(v,1) for k_,v in gains.items()} }; 2020/36 errors {a('2020-12','36',3)} vs {a('2020-12','36',4)}",
        "2020 origin, 3 years, 7% vs 18%", Eq(Symbol("max gain"), Float(max(gains.values()), 4), evaluate=False))
    n = len(keys)
    rep("bt:seven-comparisons", "NUMERIC", n == 7 == int(macros["covN"]), "number of table cells", n, "seven / covN=7",
        Eq(Symbol("N"), Integer(n), evaluate=False))
    cov = {}
    for jj, nm in [(3, "covModel"), (4, "covShare"), (5, "covEarlier")]:
        cov[nm] = sum(1 for k_ in keys if table[k_][jj][1])
        rep(f"bt:{nm}", "NUMERIC", cov[nm] == int(macros[nm]), f"count of in80==True for {NAMES[jj]}", cov[nm], macros[nm],
            Eq(Symbol(nm), Integer(cov[nm]), evaluate=False))
safe("bt-claims", "NUMERIC", "bt", c_bt_claims)

def c_bt_prose():
    g = {(o, m): 100 * next(e for e in bt if e["origin"] == o)["model"][m]["BEV"]["pct_err"] for o, m in [("2022-12", "12"), ("2022-12", "36"), ("2020-12", "12"), ("2020-12", "36"), ("2024-12", "12")]}
    for (o, m), stated in [(("2022-12", "12"), 1), (("2022-12", "36"), 12), (("2020-12", "12"), 21), (("2020-12", "36"), 7), (("2024-12", "12"), 3)]:
        v = abs(g[(o, m)])
        rep(f"prose:err {o} h{m}", "NUMERIC", rnd(v, 0) == stated, "round(|pct_err|,0) (abstract / Sec. Validation)", f"{v:.2f}", f"{stated}%",
            Eq(Symbol(f"|err|[{o},{m}]"), Float(v, 4), evaluate=False))
    # total within 2%
    mx = max(abs(100 * next(e for e in bt if e["origin"] == o)["model"][m]["total"]["pct_err"]) for o, m in table)
    rep("prose:total-within-2%", "NUMERIC", mx <= 2.0, "max |pct_err| of total stock over the 7 cells", f"{mx:.2f}%", "<= 2%",
        Eq(Symbol("max|err_total|"), Float(mx, 4), evaluate=False))
safe("bt-prose", "NUMERIC", "prose", c_bt_prose)

def c_share2pct():
    import csv
    rows_ = {}
    with open(os.path.join(DATA, "backtest", "2020-12", "panels", "fuel4_monthly.csv"), encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows_.setdefault(row["month"], {})[row["fuel4"]] = float(row["stock"])
    orig = 100 * rows_["2020-12"]["BEV"] / sum(rows_["2020-12"].values())
    tgt = 100 * 66610 / 2787559
    rep("prose:BEV-2%-of-fleet-at-2020-origin", "NUMERIC", rnd(orig, 0) == 2,
        "BEV stock / total stock at the 2020-12 origin (panel)", f"{orig:.2f}% at origin 2020-12 (and {tgt:.2f}% at 2021-12, the 12-month target)", "2%",
        Eq(Symbol("BEV/total[2020-12]"), Float(orig, 4), evaluate=False))
safe("share-2pct", "NUMERIC", "share", c_share2pct)

def c_floor_range():
    fl = [e["floor_share_age+sales"] for e in bt]
    lo, hi = min(fl), max(fl)
    allfl = {k_: [round(e[k_], 3) for e in bt] for k_ in bt[0] if k_.startswith("floor_share")}
    ok = rnd(100 * lo, 0) == 8 and rnd(100 * hi, 0) == 21
    rep("prose:floor-binds-8-21%", "NUMERIC", ok, "range of floor_share_age+sales over the 3 origins (age link = forecast model)",
        f"{100*lo:.1f}%..{100*hi:.1f}%; all variants: {allfl}", "8--21%",
        Eq(Symbol("floor share range"), Symbol(f"[{100*lo:.1f},{100*hi:.1f}]"), evaluate=False))
safe("floor-range", "NUMERIC", "floor", c_floor_range)

# ------------------------------------------------------------------ write results
with open(os.path.join(OUT, "results.json"), "w", encoding="utf-8") as fh:
    json.dump(RES, fh, indent=1)
n = len(RES); p = sum(r_["status"] == "PASS" for r_ in RES); f_ = sum(r_["status"] == "FAIL" for r_ in RES); e_ = sum(r_["status"] == "ERROR" for r_ in RES)
print(f"\nTOTAL: {n} checked: {p} passed, {f_} failed, {e_} errored")
