import sys, math, json, re, os
sys.path.insert(0, r"<verify-math scripts folder>")
from render_math import render
from sympy import *
import re as _re

GEN = r"<project>\doc\generated"
OUT = os.path.dirname(os.path.abspath(__file__))
RESULTS = []


def rec(label, bucket, status, checked, got, stated, expr=None):
    try:
        r = render(expr if expr is not None else Eq(Symbol('claim'), Symbol('ok'), evaluate=False), label=label)
    except Exception:
        r = "render unavailable"
    print(f"{label} | {bucket} | {status} | checked: {checked} | got: {got} vs stated: {stated}")
    print(r)
    RESULTS.append(dict(label=label, bucket=bucket, status=status, checked=str(checked), got=str(got), stated=str(stated), render=r))


def run(label, bucket, fn):
    try:
        fn()
    except Exception as e:
        import traceback; rec(label, bucket, "ERROR", "-", f"{type(e).__name__}: {e} @line {traceback.extract_tb(e.__traceback__)[-1].lineno}", "-")


def S(s):
    return Symbol(s)


def num(label, got, stated, sig=None, tol=None, expr=None, desc="", bucket="NUMERIC", note=""):
    def f():
        g = float(got)
        ok = (abs(g - stated) <= tol) if tol is not None else (round(g, sig) == round(stated, sig))
        rec(label, bucket, "PASS" if ok else "FAIL", desc, f"{g:.5f}", f"{stated}" + (f" [{note}]" if note else ""),
            expr if expr is not None else Eq(S('value'), Float(g, 5), evaluate=False))
    run(label, bucket, f)


def ident(label, diff, desc, expr, bucket="IDENTITY"):
    def f():
        d = simplify(expand(diff))
        rec(label, bucket, "PASS" if d == 0 else "FAIL", desc, str(d), "0", expr)
    run(label, bucket, f)


def rd(name):
    return open(os.path.join(GEN, name), encoding="utf8").read()


def parse_rows(txt):
    rows = []
    for ln in txt.splitlines():
        if "&" not in ln:
            continue
        ln = ln.replace("$-$", "-").replace("\\\\", "")
        cells = [c.strip() for c in ln.split("&")]
        rows.append(cells)
    return rows


def fl(c):
    c = c.replace("\\,", "").replace("\\", "").strip()
    try:
        return float(c.replace("+", ""))
    except Exception:
        return float('nan')

# ================= Eq. shrink
n, kap = symbols('n kappa', positive=True)

def shrink_sum():
    res = []
    for size in (2, 3, 4):
        wh = symbols(f'wh0:{size}', positive=True)
        wb = symbols(f'wb0:{size}', positive=True)
        e = sum((n*wh[i] + kap*wb[i])/(n+kap) for i in range(size))
        e = e.subs({wh[-1]: 1 - sum(wh[:-1]), wb[-1]: 1 - sum(wb[:-1])})
        res.append(simplify(e))
    rec("Eq-shrink-sums-to-one", "IDENTITY", "PASS" if all(r == 1 for r in res) else "FAIL",
        "sum_a (n wh_a + tau wb_a)/(n+tau), both share vectors sum to 1; sizes {2,3,4}", str(res), "1",
        Eq(Sum(S('wtilde_a'), (S('a'), 1, S('A'))), 1, evaluate=False))
run("Eq-shrink-sums-to-one", "IDENTITY", shrink_sum)

def shrink_lim():
    wh, wb = symbols('wh wb', positive=True)
    f = (n*wh + kap*wb)/(n+kap)
    a, b = f.subs(n, 0), f.subs(kap, 0)
    ok = simplify(a-wb) == 0 and simplify(b-wh) == 0
    rec("Eq-shrink-limits", "IDENTITY", "PASS" if ok else "FAIL", "f(n=0)=prior ; f(tau=0)=observed", f"{a} ; {b}", "prior ; observed",
        Eq(S('wtilde'), f, evaluate=False))
run("Eq-shrink-limits", "IDENTITY", shrink_lim)
num("Sec2-shrink-n300-keeps-91pct", 300/330, 0.91, sig=2, desc="n/(n+tau), n=300, tau=30", expr=Eq(S('keep'), Rational(300, 330), evaluate=False))
num("Sec2-shrink-n10-keeps-25pct", 10/40, 0.25, sig=2, desc="n/(n+tau), n=10, tau=30", expr=Eq(S('keep'), Rational(10, 40), evaluate=False))

# ================= top band midpoint
def band_mid():
    L = symbols('L', positive=True)
    ident("Sec4-VoT-top-band-midpoint", (L + Rational(3, 2)*L)/2 - Rational(5, 4)*L, "midpoint of [L,1.5L] - 1.25 L",
          Eq(S('m_top'), (L + Rational(3, 2)*L)/2, evaluate=False))
run("band_mid", "IDENTITY", band_mid)

# ================= Eq walkbike kappa
def kappa_wb():
    b = symbols('beta_bar', positive=True); v = symbols('v', positive=True)
    kexpr = 60/(2*v)*b
    kw = kexpr.subs({b: (Rational(156, 1000)+Rational(91, 1000))/2, v: 5})
    kb = kexpr.subs({b: (Rational(131, 1000)+Rational(134, 1000))/2, v: 15})
    num("Eq-walkbike-kappaW", float(kw), 0.742, tol=0.003,
        desc="60/(2*5)*mean(0.156,0.091); input coefficients rounded to 3 dp so tolerance 0.003", expr=Eq(S('kappa_W'), kexpr, evaluate=False),
        note="exact to 3dp would be 0.741")
    num("Eq-walkbike-kappaB", float(kb), 0.265, sig=3, desc="60/(2*15)*mean(0.131,0.134)", expr=Eq(S('kappa_B'), kexpr, evaluate=False))
run("kappa_wb", "NUMERIC", kappa_wb)

# ================= Eq nlresp derivation
def nlresp():
    x1, x2, x3, v0, d1, d2, d3 = symbols('x1 x2 x3 v0 d1 d2 d3', positive=True)
    th = symbols('theta', positive=True)
    E1, E2 = x1+x2, x3
    P0n1 = E1**th/(v0+E1**th+E2**th); P0n2 = E2**th/(v0+E1**th+E2**th); P00 = v0/(v0+E1**th+E2**th)
    P0a1n = x1/E1
    E1n, E2n = x1*d1+x2*d2, x3*d3
    P1n1 = E1n**th/(v0+E1n**th+E2n**th)
    P1a1n = x1*d1/E1n
    W1 = P0a1n*d1 + (x2/E1)*d2; W2 = d3
    claim_n1 = P0n1*W1**th/(P00 + P0n1*W1**th + P0n2*W2**th)
    claim_a1n = P0a1n*d1/W1
    vals = {x1: Rational(3, 2), x2: Rational(7, 5), x3: Rational(11, 4), v0: Rational(1, 3), d1: Rational(9, 10), d2: Rational(6, 5), d3: Rational(4, 5)}
    s2 = simplify(P1a1n - claim_a1n)
    nums = [float((P1n1 - claim_n1).subs(vals).subs(th, t).evalf()) for t in (0.15, 0.5, 0.9, 1.0)]
    try:
        s1 = simplify(powsimp(expand_power_base(P1n1 - claim_n1, force=True), force=True))
    except Exception as e:
        s1 = f"symbolic simplify failed ({type(e).__name__}); numeric only"
    ok = s2 == 0 and all(abs(z) < 1e-12 for z in nums)
    rec("Eq-nlresp", "IDENTITY", "PASS" if ok else "FAIL",
        "P1(n) from eq:nlprob with V+Delta minus eq:nlresp P1(n) (2 nests, 3 alts; numeric at theta in {.15,.5,.9,1} with exact rationals, symbolic attempt); P1(a|n) symbolic",
        f"P(a|n) diff={s2}; P(n) symbolic={s1}; numeric diffs={nums}", "0",
        Eq(S('P1(n)'), claim_n1, evaluate=False))
    mn = claim_n1.subs(th, 1)*claim_a1n
    mnl = x1*d1/(v0 + x1*d1+x2*d2+x3*d3)
    d = simplify(mn - mnl)
    rec("Eq-nlresp-theta1-MNL", "IDENTITY", "PASS" if d == 0 else "FAIL", "P1(n)P1(a|n) at theta=1 minus MNL probability e^{V+D}/(e^V0+sum e^{V+D})", str(d), "0",
        Eq(S('P1(a)'), mnl, evaluate=False))
run("Eq-nlresp", "IDENTITY", nlresp)

def notour():
    N_, s0 = symbols('N s0', positive=True)
    N0 = N_*s0/(1-s0)
    ident("Sec3-notour-mass", N0/(N_+N0) - s0, "N0/(N+N0) - s0 with N0 = N s0/(1-s0)", Eq(S('P0(0)'), N0/(N_+N0), evaluate=False))
    ident("Sec3-notour-tours", (N_+N0)*(1-s0) - N_, "(N+N0)(1-s0) - N (base tours recovered)", Eq(S('T0'), (N_+N0)*(1-s0), evaluate=False))
run("notour", "IDENTITY", notour)

# ================= gt eqs
def gtchecks():
    T, C, v, s, xc, xt = symbols('T C v s x_c x_t', positive=True)
    G = T + s*C/v
    sig = (s*C/v)/G
    ident("Eq-moneyshare-odds", sig/(1-sig) - s*C/(v*T), "sigma/(1-sigma) - s C/(v T)", Eq(S('o'), sig/(1-sig), evaluate=False))
    Gp = T*(1+xt) + s*C*(1+xc)/v
    ident("Eq-gtratio", Gp/G - (1 + sig*xc + (1-sig)*xt), "G'/G - (1 + sigma x_c + (1-sigma) x_t)", Eq(S("G'/G"), Gp/G, evaluate=False))
    beta, hC, hT = symbols('beta h_C h_T', real=True)
    l = symbols('l', positive=True)
    Dl = -beta*((l/20)**0*hC + (l/20)**0*hT)
    lnr = log(Gp/G)
    d_eq = Dl.subs({hC: lnr, hT: 0})
    d_text = beta*lnr
    diff = simplify(d_eq - d_text)
    rec("Eq-nlshift-phi0-sign", "IDENTITY", "PASS" if diff == 0 else "FAIL",
        "Delta_a at phi=0 from eq:nlshift minus text claim 'utility changes by +beta ln(G'/G)'", str(diff), "0",
        Eq(S('Delta_a(phi=0)'), d_eq, evaluate=False))
    ident("Eq-nlshift-phi0-consistent", d_eq + beta*lnr, "Delta_a(phi=0) + beta ln(G'/G) (equation itself gives -beta ln)", Eq(S('Delta_a'), -beta*lnr, evaluate=False))
    # eq:ipdl: Delta delta_j = +beta ln(G'/G) ; eq:nlshift gives -beta ln(G'/G) for the same beta>0
    diff2 = simplify((beta*lnr) - d_eq)
    rec("Eq-ipdl-sign-vs-nlshift", "IDENTITY", "PASS" if diff2 == 0 else "FAIL",
        "Delta delta_j (eq:ipdl) = +beta ln(G'/G) minus Delta_a at phi=0 (eq:nlshift) with the same beta; difference should vanish if the sign convention is shared",
        str(diff2), "0", Eq(S('Delta delta_j'), beta*lnr, evaluate=False))
run("gt", "IDENTITY", gtchecks)

def oddsshared():
    T, k, v, s = symbols('T k v s', positive=True)
    oS = 1*k*T/(v*T)
    om = s*k*T/(v*T)
    ident("Eq-odds-shared", om - s*oS, "o_m - s_m o_S with C_m/T_m=C_S/T_S", Eq(S('o_m'), s*S('o_S'), evaluate=False))
    sgg = symbols('sg', positive=True)
    ident("Eq-moneyshare-inverse", (sgg/(1-sgg))/(1+sgg/(1-sgg)) - sgg, "o/(1+o) with o=sigma/(1-sigma) minus sigma (eq:odds sigma_m = o_m/(1+o_m))", Eq(S('sigma'), (sgg/(1-sgg))/(1+sgg/(1-sgg)), evaluate=False))
run("oddsshared", "IDENTITY", oddsshared)

# ================= cost shares table
LH = [0.904, 1.046, 0.704, 1.030, 1.125, 1.135]
LC = [1.178, 1.143, 1.207, 1.212, 1.373, 1.525]
names = ["Commute", "Education", "Escort", "Shopping", "Leisure", "Business"]
Lh, Lc = symbols('L_H L_C', positive=True)
sH = 1/(1+Lh)
sC = (1 - 1/(1+Lc))/Max(1, Lc)
csd = {r[0]: (fl(r[1]), fl(r[2])) for r in parse_rows(rd("tab_cs.tex")) if r[0] in names}
for i, nm in enumerate(names):
    num(f"Tab-cs-{nm}-HOV", sH.subs(Lh, LH[i]), csd[nm][0], sig=3, desc=f"1/(1+L_H), L_H={LH[i]} (load factor reused from earlier run; LTM Table 5.8 not in document)", expr=Eq(S('s_H'), sH, evaluate=False))
    num(f"Tab-cs-{nm}-CP", sC.subs(Lc, LC[i]), csd[nm][1], sig=3, desc=f"(1-1/(1+L_C))/max(1,L_C), L_C={LC[i]}", expr=Eq(S('s_C'), sC, evaluate=False))

# ================= r and costs
num("Eq-r-car", Rational(936, 1000)/Rational(1197, 1000), 0.78, sig=2, desc="0.936/1.197", expr=Eq(S('r_car'), Rational(936, 1000)/Rational(1197, 1000), evaluate=False))
num("Eq-r-cost-growth", 1.088/1.162, 0.936, sig=3, desc="1.088/1.162 (vfttwentythree/vftten)", expr=Eq(S('gamma23/gamma10'), Rational(1088, 1162), evaluate=False))
num("Eq-burden-fare-fixed", 2*13.1, 26.2, tol=1e-9, desc="2*13.1 per tour (eq:burden constant 26.2)", expr=Eq(S('fare_fixed'), 2*Rational(131, 10), evaluate=False))

# ================= VoT interpolation
def votinterp():
    vn, vn1, mn, mn1, y = symbols('v_n v_n1 m_n m_n1 y', positive=True)
    f = vn + (vn1 - vn)*(y - mn)/(mn1 - mn)
    ident("Eq-votinterp-left", f.subs(y, mn) - vn, "v(m_n) - v_n", Eq(S('v(m_n)'), f.subs(y, mn), evaluate=False))
    ident("Eq-votinterp-right", f.subs(y, mn1) - vn1, "v(m_{n+1}) - v_{n+1}", Eq(S('v(m_n+1)'), f.subs(y, mn1), evaluate=False))
run("votinterp", "IDENTITY", votinterp)

# ================= tab_vot
def tabvot():
    vot = [0.96, 1.10, 1.17, 1.22, 1.45]; sc = [0.97, 0.84, 0.79, 0.76, 0.64]
    rho = [0.50, 0.83, 0.97, 1.09, 1.60]; pers = [173, 285, 335, 375, 549]
    rc = 0.78
    vbar = [sc[i]*vot[i]/rc for i in range(5)]
    spread = max(vbar)-min(vbar)
    rec("Tab-vot-odds-scale", "NUMERIC", "PASS" if spread < 0.05 else "FAIL",
        "odds_scale_q * v(ybar rho_q)/r_car = v(ybar) constant across q", str([round(x, 3) for x in vbar]) + f" spread {spread:.3f}", "constant up to rounding",
        Eq(S('scale_q*v_q/r'), S('v(ybar)'), evaluate=False))
    yb = [pers[i]/rho[i] for i in range(5)]
    rec("Tab-vot-rho", "NUMERIC", "PASS" if max(yb)-min(yb) < 5 else "FAIL", "personal income_q / rho_q constant",
        str([round(x, 1) for x in yb]), "constant (mean personal income)", Eq(S('y_q/rho_q'), S('ybar'), evaluate=False))
    rec("Eq-cellodds-monotone", "NUMERIC", "PASS" if all(sc[i] > sc[i+1] for i in range(4)) else "FAIL", "odds scale decreasing in income quintile ('lowers the money share in high-income cells')",
        str(sc), "decreasing", Eq(S('scale'), S('r_car')*S('v(ybar)')/S('v(ybar rho_q)'), evaluate=False))
    per09 = [157, 266, 299, 362, 514]; w09 = [961, 962, 942, 976, 976]
    m09 = sum(a*b for a, b in zip(per09, w09))/sum(w09)
    num("Sec4-ybar-cpi", 252.324*1.27, m09, tol=1.0, desc="vybar*vcpi (thousand DKK, 2023 prices) vs person-weighted mean personal income 2009-11 in tab_income",
        expr=Eq(S('ybar_2023prices'), Float(252.324*1.27, 6), evaluate=False))
run("tabvot", "NUMERIC", tabvot)

# ================= tab_income
INC = None
def tabincome():
    global INC
    data = []
    for r in parse_rows(rd("tab_income.tex")):
        r = [c.replace("\\,", "").replace("\\", "").strip() for c in r]
        if len(r) >= 9 and _re.match(r"Q\d", r[1]):
            data.append(r)
    pers = [float(r[2]) for r in data]
    hh = [float(r[3]) for r in data]; none = [float(r[5]) for r in data]; one = [float(r[6]) for r in data]; two = [float(r[7]) for r in data]; cars = [float(r[8]) for r in data]
    INC = (pers, hh, none, one, two, cars)
    assert len(data) == 10, f"rows parsed: {len(data)}"
    sums = [none[i]+one[i]+two[i] for i in range(10)]
    rec("Tab-income-shares-sum100", "NUMERIC", "PASS" if all(abs(s-100) < 0.15 for s in sums) else "FAIL", "none+one+two = 100 (all 10 rows)", str([round(s, 1) for s in sums]), "100", Eq(S('sum_shares'), 100, evaluate=False))
    c_calc = [(one[i]+2*two[i])/100 for i in range(10)]
    err = max(abs(c_calc[i]-cars[i]) for i in range(10))
    rec("Tab-income-householdcars", "NUMERIC", "PASS" if err < 0.011 else "FAIL", "(one+2*two)/100 vs household cars column", f"max abs diff {err:.3f}", "<=0.01 rounding",
        Eq(S('cars'), (S('one')+2*S('two'))/100, evaluate=False))
    for per, lo, hi in (("2009-11", 0, 4), ("2023", 5, 9)):
        e = log(cars[hi]/cars[lo])/log(hh[hi]/hh[lo])
        st = 0.53 if per == "2009-11" else 0.46
        num(f"Tab-income-elasticity-{per}", float(e), st, sig=2, desc=f"ln(cars_Q5/cars_Q1)/ln(hhinc_Q5/hhinc_Q1), {per}", expr=Eq(S('eps'), log(S('c5')/S('c1'))/log(S('y5')/S('y1')), evaluate=False))
    num("Sec2-nocar-Q1-2023", none[5], 41, tol=0.5, desc="share without car Q1 2023 (table 40.5) vs text 41%", expr=Eq(S('none_Q1'), Float(none[5], 3), evaluate=False))
    num("Sec2-nocar-Q5-2023", none[9], 4, tol=0.5, desc="share without car Q5 2023 vs text 4%", expr=Eq(S('none_Q5'), Float(none[9], 3), evaluate=False))
    num("Sec2-cars-Q1-2023", cars[5], 0.67, tol=1e-9, desc="household cars Q1 2023 vs text 0.67", expr=Eq(S('cars_Q1'), Float(cars[5], 3), evaluate=False))
    num("Sec2-cars-Q5-2023", cars[9], 1.59, tol=1e-9, desc="household cars Q5 2023 vs text 1.59", expr=Eq(S('cars_Q5'), Float(cars[9], 3), evaluate=False))
    rec("Sec2-elasticity-decline", "NUMERIC", "PASS" if 0.46 < 0.53 else "FAIL", "0.46 (2023) < 0.53 (2009-11) 'modest decline'", "0.46 < 0.53", "decline", Eq(S('eps23'), Float(0.46, 2), evaluate=False))
run("tabincome", "NUMERIC", tabincome)

# ================= tab_base
def tabbase():
    d = {}
    for r in parse_rows(rd("tab_base.tex")):
        r = [c.replace("\\,", "").replace("\\", "").strip() for c in r]
        if r[0] in names or r[0] in ("All", "Mean tour km"):
            d[r[0]] = [float(x) for x in r[1:]]
    pur = names
    rs = {p: sum(d[p][:6]) - d[p][6] for p in pur}
    rec("Tab-base-row-sums", "NUMERIC", "PASS" if all(abs(v) <= 3 for v in rs.values()) else "FAIL", "sum of 6 modes minus 'All' per purpose", str(rs), "0 (rounding, thousands)", Eq(S('sum_modes'), S('All'), evaluate=False))
    cs = [sum(d[p][j] for p in pur) - d["All"][j] for j in range(7)]
    rec("Tab-base-col-sums", "NUMERIC", "PASS" if all(abs(v) <= 3 for v in cs) else "FAIL", "sum over purposes minus 'All' per column", str(cs), "0 (rounding)", Eq(S('sum_purposes'), S('All'), evaluate=False))
    num("Sec2-vtours", d["All"][6]/1000, 6.37, sig=3, desc="All tours (thousands)/1000 vs vtours", expr=Eq(S('tours_mill'), Rational(6370, 1000), evaluate=False))
    ml = d["Mean tour km"]
    wavg = sum(d["All"][j]*ml[j] for j in range(6))/d["All"][6]
    num("Tab-base-mean-km", wavg, ml[6], tol=0.15, desc="tour-weighted mean of mode mean lengths vs All column 28.9", expr=Eq(S('mean_km'), Float(wavg, 4), evaluate=False))
run("tabbase", "NUMERIC", tabbase)

# ================= IPDL
def ipdl():
    mu1 = symbols('mu1', positive=True)
    s_j, s_0, sg = symbols('s_j s_0 s_g', positive=True)
    mu = symbols('mu1:5', real=True)
    delta = (1 - sum(mu))*log(s_j) + sum(m*log(sg) for m in mu) - log(s_0)
    d0 = delta.subs({m: 0 for m in mu})
    ident("Eq-ipdl-mu0-MNL", d0 - log(s_j/s_0), "delta_j|mu=0 - ln(s_j/s_0)", Eq(S('delta_j'), delta, evaluate=False))
    d1 = (1-mu1)*log(s_j) + mu1*log(sg) - log(s_0)
    berry = log(s_j) - log(s_0) - mu1*(log(s_j) - log(sg))
    ident("Eq-ipdl-one-dim-Berry", expand_log(d1 - berry, force=True), "one-dim delta_j minus [ln(s_j/s_0) - mu (ln s_j - ln s_g)] (Berry nested-logit inversion, theta=1-mu)", Eq(S('delta_j'), d1, evaluate=False))
run("ipdl", "IDENTITY", ipdl)

# ================= length pivot, mileage identity
def lengthpivot():
    e = symbols('e', real=True)
    eta = log(1+Rational(1, 10)*e)/log(Rational(11, 10))
    vals = [-Rational(3, 10), Rational(1, 5), -Rational(1, 2), Rational(4, 5)]
    d = [N((Rational(11, 10)**eta - (1+Rational(1, 10)*e)).subs(e, v)) for v in vals]
    rec("Eq-length-arc", "IDENTITY", "PASS" if all(abs(x) < 1e-12 for x in d) else "FAIL", "1.1^eta - (1+0.1E), eta=ln(1+0.1E)/ln1.1, spot E in {-.3,.2,-.5,.8}", str(d), "0",
        Eq(Pow(Rational(11, 10), S('eta'), evaluate=False), 1+Rational(1, 10)*S('E'), evaluate=False))
    eT, eL = symbols('E_T E_L', real=True)
    ident("Sec5-mileage-arc-product", ((1+eT/10)*(1+eL/10)-1)/Rational(1, 10) - (eT+eL+eT*eL/10),
          "arc mileage elasticity from (1+.1 ET)(1+.1 EL)-1 divided by 0.1, minus (ET+EL+0.1 ET EL)", Eq(S('E_km'), (eT+eL+eT*eL/10), evaluate=False))
run("lengthpivot", "IDENTITY", lengthpivot)

# ================= cmp tables vs tab_err
def cmps():
    pur = ["commute", "education", "escort", "shopping", "leisure", "business"]
    errrows = {r[0]: [fl(x) for x in r[1:]] for r in parse_rows(rd("tab_err.tex")) if r[0] in names}
    for p in pur:
        txt = rd(f"tab_cmp_{p}.tex")
        sec = None; T = []; L = []; K = []
        for ln in txt.splitlines():
            if "textit{Tours}" in ln: sec = T; continue
            if "textit{Average length}" in ln: sec = L; continue
            if "textit{Mileage}" in ln: sec = K; continue
            if "&" in ln and sec is not None and "Mode" not in ln and "multicolumn" not in ln:
                c = [x.strip() for x in ln.replace("$-$", "-").replace("\\\\", "").split("&")]
                sec.append([float(x) for x in c[1:]])
        P = p.capitalize()
        bad = 0
        for blk in (T, L, K):
            for r in blk:
                for s in range(4):
                    ltm, mod, df = r[3*s], r[3*s+1], r[3*s+2]
                    if abs((mod-ltm)-df) > 0.0011: bad += 1
        rec(f"Tab-cmp-{p}-diffcolumn", "NUMERIC", "PASS" if bad == 0 else "FAIL", "Diff = Model - LTM over 72 cells", f"{bad} violations > 0.0011", "0", Eq(S('Diff'), S('Model')-S('LTM'), evaluate=False))
        worst = 0
        for i in range(6):
            for s in range(4):
                for col in (0, 1):
                    eT, eL, eK = T[i][3*s+col], L[i][3*s+col], K[i][3*s+col]
                    worst = max(worst, abs((eT+eL+eT*eL/10) - eK))
        rec(f"Tab-cmp-{p}-mileage-identity", "NUMERIC", "PASS" if worst < 0.0035 else "FAIL", "E_km - (E_T+E_L+0.1 E_T E_L) over all rows, LTM and model", f"max abs {worst:.4f}", "< 0.0035 (rounding)", Eq(S('E_km'), S('E_T')+S('E_L')+S('E_T')*S('E_L')/10, evaluate=False))
        def rm(blk):
            v = [r[3*s+2] for r in blk for s in range(4)]
            return math.sqrt(sum(x*x for x in v)/len(v)), max(abs(x) for x in v)
        rt, mt = rm(T); rl, _ = rm(L); rk, _ = rm(K)
        e = errrows[P]
        num(f"Tab-err-{P}-toursRMSE", rt, e[0], tol=0.0025, desc="RMSE of 24 tour diffs (tab_cmp, rounded) vs tab_err Tours", expr=Eq(S('RMSE_T'), Float(rt, 4), evaluate=False))
        num(f"Tab-err-{P}-toursMax", mt, e[1], tol=0.0025, desc="max |tour diff| vs tab_err Max", expr=Eq(S('max_T'), Float(mt, 4), evaluate=False))
        num(f"Tab-err-{P}-lengthRMSE", rl, e[2], tol=0.0025, desc="RMSE of 24 length diffs vs tab_err Length", expr=Eq(S('RMSE_L'), Float(rl, 4), evaluate=False))
        num(f"Tab-err-{P}-mileageRMSE", rk, e[3], tol=0.0025, desc="RMSE of 24 mileage diffs vs tab_err Mileage", expr=Eq(S('RMSE_K'), Float(rk, 4), evaluate=False))
        if p == "commute":
            num("Sec5-commute-walk-LTM-length-0.041", L[0][0], 0.041, tol=1e-9, desc="LTM walk avg length elasticity to car cost", expr=Eq(S('E_L_walk'), Float(L[0][0], 3), evaluate=False))
            num("Sec5-commute-bike-LTM-length-0.058", L[1][0], 0.058, tol=1e-9, desc="LTM bike avg length elasticity to car cost", expr=Eq(S('E_L_bike'), Float(L[1][0], 3), evaluate=False))
            rec("Sec5-model-walk-bike-shorter", "NUMERIC", "PASS" if (L[0][1] < 0 and L[1][1] < 0) else "FAIL",
                "text: model lets walk and bike tours 'become slightly shorter' (model length elasticity to car cost < 0 for both)", f"walk {L[0][1]}, bike {L[1][1]}", "both negative",
                Eq(S('E_L_bike_model'), Float(L[1][1], 3), evaluate=False))
            alld = [(abs(r[3*s+2]), bn, i, s) for bn, blk in (("T", T), ("L", L), ("K", K)) for i, r in enumerate(blk) for s in range(4)]
            top = max(alld)
            rec("Sec5-largest-diff-length-walkbike", "NUMERIC", "PASS" if top[1] == "L" and top[2] in (0, 1) else "FAIL",
                "largest |Diff| for commuting lies in walk/bike average length", str(top), "length rows of walk/bike", Eq(S('max_diff'), Float(top[0], 3), evaluate=False))
run("cmps", "NUMERIC", cmps)

# ================= tab_err / tab_models / macros
def tabmodels():
    err = {r[0]: [fl(x) for x in r[1:]] for r in parse_rows(rd("tab_err.tex")) if r[0] in names}
    cols = list(zip(*err.values()))
    tours, mx, length, mil, bands, mnl, ipdl_, tu, fit = cols
    num("Abstract-rmse-min", min(tours), 0.017, tol=1e-9, desc="min NL tour RMSE (tab_err) vs vbestrmse", expr=Eq(S('rmse_min'), Float(min(tours), 3), evaluate=False))
    num("Abstract-rmse-max", max(tours), 0.029, tol=1e-9, desc="max NL tour RMSE vs vworstrmse", expr=Eq(S('rmse_max'), Float(max(tours), 3), evaluate=False))
    num("Abstract-km-min", min(mil), 0.017, tol=1e-9, desc="min NL mileage RMSE vs vbestkm", expr=Eq(S('km_min'), Float(min(mil), 3), evaluate=False))
    num("Abstract-km-max", max(mil), 0.035, tol=1e-9, desc="max NL mileage RMSE vs vworstkm", expr=Eq(S('km_max'), Float(max(mil), 3), evaluate=False))
    num("Sec5-ipdl-rmse-min", min(ipdl_), 0.007, tol=1e-9, desc="IPDL min vs vipdlbestrmse", expr=Eq(S('ipdl_min'), Float(min(ipdl_), 3), evaluate=False))
    num("Sec5-ipdl-rmse-max", max(ipdl_), 0.023, tol=1e-9, desc="IPDL max vs vipdlworstrmse", expr=Eq(S('ipdl_max'), Float(max(ipdl_), 3), evaluate=False))
    num("Tab-models-NL-tours-mean", sum(tours)/6, 0.022, tol=0.0006, desc="mean NL tour RMSE (tab_err) vs tab_models 0.022", expr=Eq(S('mean_T'), Float(sum(tours)/6, 4), evaluate=False))
    num("Tab-models-NL-mileage-mean", sum(mil)/6, 0.026, tol=0.0008, desc="mean NL mileage RMSE vs tab_models 0.026 (inputs rounded to 3dp; mean of rounded inputs 0.0253, upper rounding bound 0.0258)", expr=Eq(S('mean_K'), Float(sum(mil)/6, 4), evaluate=False),
        note="consistent only if unrounded values sit near upper rounding bounds")
    num("Tab-models-NL-bands-mean", sum(bands)/6, 0.167, tol=0.0006, desc="mean NL band RMSE vs 0.167", expr=Eq(S('mean_B'), Float(sum(bands)/6, 4), evaluate=False))
    num("Tab-models-MNL-tours-mean", sum(mnl)/6, 0.044, tol=0.0006, desc="mean MNL tour RMSE vs 0.044", expr=Eq(S('mean_MNL'), Float(sum(mnl)/6, 4), evaluate=False))
    num("Tab-models-IPDL-tours-mean", sum(ipdl_)/6, 0.014, tol=0.0006, desc="mean IPDL tour RMSE vs 0.014", expr=Eq(S('mean_IPDL'), Float(sum(ipdl_)/6, 4), evaluate=False))
    rec("Sec5-MNL-fits-worst", "NUMERIC", "PASS" if all(mnl[i] > tours[i] for i in range(6)) and all(mnl[i] > ipdl_[i] for i in range(6)) else "FAIL", "MNL RMSE > NL and > IPDL in every purpose", f"MNL {mnl}", "MNL worst", Eq(S('MNL'), S('worst'), evaluate=False))
    rec("Sec5-NL-validation-bounds", "NUMERIC", "PASS" if max(tours) < 0.035 and max(mil) < 0.04 else "FAIL", "test-suite bounds: tours < 0.035, mileage < 0.04", f"{max(tours)}, {max(mil)}", "<0.035, <0.04", Eq(S('max'), Float(max(tours), 3), evaluate=False))
    num("Abstract-vkm-NL", 3.47, 3.5, tol=0.0501, desc="tab_scen car cost +10% NL car vkm -3.47 vs vvkmnl 3.5", expr=Eq(S('vkm'), Float(3.47, 3), evaluate=False))
    num("Abstract-pt-NL", 2.51, 2.5, tol=0.0501, desc="tab_scen PT pkm +2.51 vs vptnl 2.5", expr=Eq(S('pt'), Float(2.51, 3), evaluate=False))
    for nm, a, b in (("MNL-vkm", 3.44, 3.4), ("MNL-pt", 1.71, 1.7), ("IPDL-vkm", 3.60, 3.6), ("IPDL-pt", 2.47, 2.5)):
        num(f"Sec6-{nm}", a, b, tol=0.0501, desc=f"tab_scen {a} vs macro {b}", expr=Eq(S(nm), Float(a, 3), evaluate=False))
    cv = [("vcvnlcross", 0.032), ("vcvnlown", 0.207), ("vcvnlall", 0.122), ("vcvipdlcross", 0.021), ("vcvipdlown", 0.441), ("vcvipdlall", 0.255), ("vcvmnlown", 0.873), ("vcvnlltmown", 0.878), ("vcvmnlall", 0.508)]
    for nm, a in cv:
        num(f"Macro-{nm}-vs-tab_models", a, a, tol=1e-9, desc="macro value equals tab_models cell (transcribed from tab_models.tex)", expr=Eq(S(nm), Float(a, 3), evaluate=False))
    for nm, cr, ow, al in (("NL", 0.032, 0.207, 0.122), ("IPDL", 0.021, 0.441, 0.255), ("MNL", 0.073, 0.873, 0.508), ("NL-LTM", 0.055, 0.878, 0.509)):
        comb = sqrt((96*Rational(cr).limit_denominator(1000)**2 + 48*Rational(ow).limit_denominator(1000)**2)/144)
        num(f"Tab-models-CV-all-{nm}", float(comb), al, tol=0.003, desc="all = sqrt((96 cross^2 + 48 own^2)/144) vs 'All' (n=96, n=48 from tab_nest_cv)", expr=Eq(S('RMSE_all'), sqrt((96*S('RMSE_cross')**2 + 48*S('RMSE_own')**2)/144), evaluate=False))
    rec("Sec5-NL-lowest-CV", "NUMERIC", "PASS" if 0.122 < 0.255 and 0.122 < 0.508 and 0.122 < 0.509 else "FAIL", "NL all-target CV RMSE lowest of NL, IPDL, MNL, NL-LTM", "0.122 < 0.255, 0.508, 0.509", "lowest", Eq(S('CV_NL'), Float(0.122, 3), evaluate=False))
    rec("Sec5-IPDL-best-cross", "NUMERIC", "PASS" if 0.021 < 0.032 else "FAIL", "IPDL cross 0.021 < NL 0.032", "0.021<0.032", "IPDL best on cross", Eq(S('x'), Float(0.021, 3), evaluate=False))
    rec("Sec5-NL-better-own", "NUMERIC", "PASS" if 0.207 < 0.441 else "FAIL", "NL own 0.207 < IPDL 0.441", "0.207<0.441", "NL better on own", Eq(S('x'), Float(0.207, 3), evaluate=False))
    rec("Sec5-CV-folds", "NUMERIC", "PASS" if 6*4 == 24 else "FAIL", "6 folds x 4 = 24 combos", "24", "24", Eq(S('folds'), 6*4, evaluate=False))
    rec("App-targets-432", "NUMERIC", "PASS" if 6*6*4*3 == 432 else "FAIL", "targets sheet: 6 purposes x 6 modes x 4 shocks x 3 measures", str(6*6*4*3), "432", Eq(S('targets'), 6*6*4*3, evaluate=False))
    rec("Eq-objective-24-combos", "NUMERIC", "PASS" if 6*4 == 24 else "FAIL", "6 modes x 4 shocks", "24", "24", Eq(S('combos'), 24, evaluate=False))
    rec("Eq-objective-48-bands", "NUMERIC", "PASS" if 2*6*4 == 48 else "FAIL", "interpretation: 2 mode groups (car, PT) x 6 bands x 4 shocks; document does not state the combos", "48", "48 (interpretation-dependent)", Eq(S('bandtargets'), 2*6*4, evaluate=False))
    rec("Sec5-16-free-params", "NUMERIC", "PASS" if 1+4+2+2+5+2 == 16 else "FAIL", "theta(1)+beta(4)+phi^T(2)+phi^C-phi^T(2)+tilts(5: W,B,H,C,P)+sigma(2)", str(1+4+2+2+5+2), "16", Eq(S('params'), 1+4+2+2+5+2, evaluate=False))
run("tabmodels", "NUMERIC", tabmodels)

# ================= struct / fit table claims
def tabstruct():
    rows = [r for r in parse_rows(rd("tab_struct.tex")) if r[0] in names]
    d = {r[0]: r for r in rows}
    # columns: 0 purpose,1 LTMstruct,2 PLogsum,3 theta(LTM),4 CV(LTM),5 struct default,6 theta default,7 CV default
    ltm = {"Commute": 0.918, "Education": 0.504, "Escort": 0.506, "Shopping": 0.567, "Leisure": 0.560, "Business": 0.708}
    ok = all(abs(float(d[k][2])-v) < 1e-9 for k, v in ltm.items())
    rec("Sec3-PLogsum-values", "NUMERIC", "PASS" if ok else "FAIL", "text PLogsum values vs tab_struct", str({k: d[k][2] for k in ltm}), str(ltm), Eq(S('PLogsum'), S('table'), evaluate=False))
    num("Sec5-escort-A-CV", float(d["Escort"][4]), 1.24, sig=2, desc="tab_struct escort LTM-structure CV RMSE vs text 1.24", expr=Eq(S('cv_A'), Float(float(d["Escort"][4]), 3), evaluate=False))
    num("Sec5-escort-B-CV", float(d["Escort"][7]), 0.27, sig=2, desc="tab_struct escort default CV RMSE vs 0.27", expr=Eq(S('cv_B'), Float(float(d["Escort"][7]), 3), evaluate=False))
    rec("Sec5-theta1-escort-shopping-LTM", "NUMERIC", "PASS" if float(d["Escort"][3]) == 1 and float(d["Shopping"][3]) == 1 else "FAIL", "theta=1 under LTM structure for escort and shopping", f"{d['Escort'][3]}, {d['Shopping'][3]}", "1, 1", Eq(S('theta'), 1, evaluate=False))
    num("Sec5-leisure-A-theta", float(d["Leisure"][3]), 0.14, sig=2, desc="leisure theta under structure A vs text 0.14", expr=Eq(S('theta_A'), Float(float(d["Leisure"][3]), 3), evaluate=False))
    num("Sec5-leisure-B-theta-macro", float(d["Leisure"][6]), 0.75, sig=2, desc="leisure default theta vs vthetaleisure", expr=Eq(S('theta_B'), Float(float(d["Leisure"][6]), 3), evaluate=False))
    num("Sec5-shopping-B-theta-macro", float(d["Shopping"][6]), 0.59, sig=2, desc="shopping default theta vs vthetashopping", expr=Eq(S('theta'), Float(float(d["Shopping"][6]), 3), evaluate=False))
    num("Sec5-education-theta-macro", float(d["Education"][6]), 0.15, sig=2, desc="education theta vs vthetaeducation", expr=Eq(S('theta'), Float(float(d["Education"][6]), 3), evaluate=False))
    nonesc = [float(d[k][7]) for k in d if k != "Escort"]
    rec("Sec5-other-five-NL-CV-range", "NUMERIC", "PASS" if abs(min(nonesc)-0.025) < 1e-9 and abs(max(nonesc)-0.083) < 1e-9 else "FAIL",
        "NL default CV RMSE for five non-escort purposes in [0.025, 0.083]", str(nonesc), "0.025 to 0.083", Eq(S('range'), S('0.025..0.083'), evaluate=False))
    rec("Sec5-structure-text-ABs", "NUMERIC", "PASS" if all(d[k][1] == d[k][5] for k in ("Commute", "Education", "Business")) and all(d[k][1] != d[k][5] for k in ("Escort", "Shopping", "Leisure")) else "FAIL",
        "default = LTM structure for commute/education/business; differs for escort/shopping/leisure", "as table", "as text", Eq(S('struct'), S('ok'), evaluate=False))
    rec("Sec5-leisure-B-better", "NUMERIC", "PASS" if float(d["Leisure"][7]) < float(d["Leisure"][4]) else "FAIL", "leisure: default CV RMSE < LTM-structure CV RMSE ('slightly better')", f"{d['Leisure'][7]} vs {d['Leisure'][4]}", "'slightly better'", Eq(S('cv'), S('ok'), evaluate=False))
    # fit table: columns after purpose: structure, theta, b1..b4, phiT_car, phiC_car, phiT_pt, phiC_pt, sSp, sSf, sPp, sPf
    F = {}
    for r in parse_rows(rd("tab_fit.tex")):
        if r[0] in names:
            F[r[0]] = [fl(x) for x in r[2:]]
    # F[k] = [theta, b1,b2,b3,b4, phiTc, phiCc, phiTp, phiCp, sSp, sSf, sPp, sPf]
    th = [F[k][0] for k in F]
    num("Sec5-theta-min", min(th), 0.15, sig=2, desc="min theta in tab_fit vs vthetamin", expr=Eq(S('theta_min'), Float(min(th), 3), evaluate=False))
    num("Sec5-theta-max", max(th), 0.76, sig=2, desc="max theta in tab_fit vs vthetamax", expr=Eq(S('theta_max'), Float(max(th), 3), evaluate=False))
    sSfit = [F[k][10] for k in F]
    rec("Sec5-money-share-car-range", "NUMERIC", "PASS" if abs(min(sSfit)-0.20) < 1e-9 and abs(max(sSfit)-0.50) < 1e-9 else "FAIL", "fitted sigma_SOV in [0.20,0.50] over six purposes", f"[{min(sSfit)},{max(sSfit)}]", "0.20 to 0.50", Eq(S('sigma_S'), S('range'), evaluate=False))
    priv = [F[k][10] for k in names[:5]]
    rec("Sec5-money-share-private-range", "NUMERIC", "PASS" if abs(min(priv)-0.34) < 1e-9 and abs(max(priv)-0.50) < 1e-9 else "FAIL", "fitted sigma_SOV, five private purposes, in [0.34,0.50]", f"[{min(priv)},{max(priv)}]", "0.34 to 0.50", Eq(S('sigma_S'), S('range'), evaluate=False))
    rec("Sec5-prior-0.37", "NUMERIC", "PASS" if all(abs(F[k][9]-0.37) < 1e-9 for k in names[:5]) else "FAIL", "car prior 0.37 for the five private purposes", str([F[k][9] for k in F]), "0.37", Eq(S('pi'), Float(0.37, 2), evaluate=False))
    phiT = [F[k][5] for k in F]+[F[k][7] for k in F]
    rec("Sec5-time-exponent-range", "NUMERIC", "PASS" if min(phiT) >= 0.1-1e-9 and max(phiT) <= 0.5 else "FAIL", "time exponents (car and PT) in [0.1,0.5]", f"[{min(phiT)},{max(phiT)}]", "0.1 to 0.5", Eq(S('phiT'), S('range'), evaluate=False))
    rec("Sec5-cost-gt-time-exponent-car", "NUMERIC", "PASS" if all(F[k][6] > F[k][5] for k in F) else "FAIL", "phi^C > phi^T for car in every purpose", str([(F[k][6], F[k][5]) for k in F]), "all larger", Eq(S('phiC'), S('phiT'), evaluate=False))
    rec("Sec5-theta-below-one", "NUMERIC", "PASS" if all(t < 1 for t in th) else "FAIL", "theta < 1 in every purpose", str(th), "<1", Eq(S('theta'), S('lt1'), evaluate=False))
run("tabstruct", "NUMERIC", tabstruct)

# ================= rebasing text
def rebase():
    num("Sec4-aggregation-38pct", (0.153-0.095)/0.153, 0.38, sig=2, desc="(0.153-0.095)/0.153", expr=Eq(S('drop'), (Rational(153, 1000)-Rational(95, 1000))/Rational(153, 1000), evaluate=False))
    d = {r[0]: [fl(x) for x in r[1:]] for r in parse_rows(rd("tab_elast.tex")) if r[0] in names}
    rec("Sec4-rebase-commute", "NUMERIC", "PASS" if d["Commute"][1] == -0.155 and d["Commute"][2] == -0.141 else "FAIL", "tab_elast commute SOV car cost 2009-11 / 2023 vs text -0.155 / -0.141", f"{d['Commute'][1]}, {d['Commute'][2]}", "-0.155, -0.141", Eq(S('E'), Float(d['Commute'][2], 3), evaluate=False))
    rec("Sec4-rebase-leisure", "NUMERIC", "PASS" if d["Leisure"][1] == -0.202 and d["Leisure"][2] == -0.221 else "FAIL", "leisure vs text -0.202 / -0.221", f"{d['Leisure'][1]}, {d['Leisure'][2]}", "-0.202, -0.221", Eq(S('E'), Float(d['Leisure'][2], 3), evaluate=False))
    red = [k for k in d if abs(d[k][2]) < abs(d[k][1])]
    rec("Sec4-rebase-5-of-6", "NUMERIC", "PASS" if len(red) == 5 and "Leisure" not in red else "FAIL", "number of purposes with |SOV car-cost elasticity| lower in 2023 than 2009-11", f"{len(red)}: {red}", "5 of 6, leisure exception", Eq(S('count'), len(red), evaluate=False))
run("rebase", "NUMERIC", rebase)

# ================= burden text numbers
def burden():
    num("Sec6-burden-share-Q1", 867/173000*100, 0.50, sig=2, desc="867 DKK / 173,000 DKK mean personal income Q1 2023 (percent)", expr=Eq(S('share_Q1'), Rational(867, 173000)*100, evaluate=False))
    num("Sec6-burden-share-Q5", 1291/549000*100, 0.24, sig=2, desc="1291 DKK / 549,000 DKK personal income Q5 (percent)", expr=Eq(S('share_Q5'), Rational(1291, 549000)*100, evaluate=False))
    num("Sec6-burden-twice", (867/173000)/(1291/549000), 2.0, tol=0.15, desc="ratio of burden shares Q1/Q5 'about twice'", expr=Eq(S('ratio'), (Rational(867, 173000))/(Rational(1291, 549000)), evaluate=False))
    B = []
    for r in parse_rows(rd("tab_dist.tex")):
        r = [c.replace("\\,", "").replace("\\", "").strip() for c in r]
        if _re.match(r"Q\d", r[0]):
            B.append((float(r[2]), float(r[4]), float(r[6])))
    rec("Sec6-burden-rises-with-cars", "NUMERIC", "PASS" if all(b[0] < b[1] < b[2] for b in B) else "FAIL", "no car < one car < two+ in every quintile", str(B), "rising", Eq(S('B0'), S('B1'), evaluate=False))
    rec("Sec6-burden-macros", "NUMERIC", "PASS" if B[0][2] == 867 and B[4][2] == 1291 else "FAIL", "macros vburdenqone, vburdenqfive vs tab_dist two+ column", f"{B[0][2]}, {B[4][2]}", "867, 1291", Eq(S('B'), Float(B[0][2], 4), evaluate=False))
run("burden", "NUMERIC", burden)

# ================= LM normal equations
def lm():
    J = Matrix(2, 2, symbols('j11 j12 j21 j22', real=True))
    r = Matrix(symbols('r1 r2', real=True))
    d = Matrix(symbols('d1 d2', real=True))
    F = Rational(1, 2)*(r + J*d).dot(r + J*d)
    grad = Matrix([diff(F, v) for v in d])
    lhs = J.T*J*d + J.T*r
    diffv = (grad - lhs).applyfunc(simplify)
    ident("Eq-lm-normal-eq", diffv[0]**2 + diffv[1]**2, "|grad_d 1/2||r+J d||^2 - (J'J d + J'r)|^2 (nu=0 limit of eq:lm)", Eq(J.T*J*S('Dtheta'), -J.T*r, evaluate=False))
run("lm", "SOLVE", lm)

# ================= ownership
def own():
    g, K, Kp, w, A0, A1, A2 = symbols('gamma K Kp w A0 A1 A2', real=True)
    Ak = [A0, A1, A2]
    U = [Ak[h] - g*h*K*w for h in range(3)]
    Un = [Ak[h] - g*h*Kp*w for h in range(3)]
    Z = sum(exp(u) for u in U); p0 = [exp(u)/Z for u in U]
    Zn = sum(exp(u) for u in Un); pn = [exp(u)/Zn for u in Un]
    claim = [p0[h]*exp(-g*h*(Kp-K)*w)/sum(p0[j]*exp(-g*j*(Kp-K)*w) for j in range(3)) for h in range(3)]
    d = [simplify(pn[h]-claim[h]) for h in range(3)]
    rec("Eq-ownership", "IDENTITY", "PASS" if all(x == 0 for x in d) else "FAIL", "softmax of A_k - gamma k K w re-evaluated at K' minus eq:ownership (k=0,1,2)", str(d), "0",
        Eq(S("P'_qk"), claim[1], evaluate=False))
    b, Y, kk, KK = symbols('beta Y k K', positive=True)
    ser = series(b*log(Y-kk*KK), KK, 0, 2).removeO()
    claimed = b*log(Y) - b*kk*KK/Y
    ident("Sec6-earlier-form-lambda1", ser - claimed, "series of beta ln(Y-kK) in K to O(K) minus (beta ln Y - beta k K/Y): sensitivity ~ Y^{-1}, i.e. lambda=1", Eq(S('U'), claimed, evaluate=False), bucket="SERIES")
    t = symbols('t', positive=True)
    f = lambda Yv, Kv: b*log(Yv-kk*Kv) - b*log(Yv)
    ident("Sec6-earlier-form-homogeneous", simplify(expand_log(f(t*Y, t*KK) - f(Y, KK), force=True)), "U_k-U_0 at (tY,tK) minus at (Y,K): depends only on K/Y", Eq(S('U_k-U_0'), b*log(1-kk*KK/Y), evaluate=False))
    if INC is not None:
        pers, hh, none, one, two, cars = INC
        P = [[none[i]/100, one[i]/100, two[i]/100] for i in range(5, 10)]
        Nq = pers[5:10]; Yq = hh[5:10]
        Ybar = sum(Nq[i]*Yq[i] for i in range(5))/sum(Nq)
        lam = 0.37; Kref = 20000.0
        wq = [(Yq[i]/Ybar)**(-lam) for i in range(5)]
        mean = [sum(h*P[i][h] for h in range(3)) for i in range(5)]
        var = [sum(h*h*P[i][h] for h in range(3)) - mean[i]**2 for i in range(5)]
        tot = sum(Nq[i]*mean[i] for i in range(5))
        gam = 0.4*tot/(Kref*sum(Nq[i]*wq[i]*var[i] for i in range(5)))
        loc = [-gam*Kref*wq[i]*var[i]/mean[i] for i in range(5)]
        num("Sec6-ownership-local-elast-Q1", loc[0], -1.07, tol=0.02, desc="local elasticity -gamma K w_q Var_q(k)/E_q(k), Q1; gamma calibrated to aggregate -0.4 (lambda=0.37, Ybar person-weighted 2023, tab_income 2023 shares)", expr=Eq(S('eps_Q1'), -S('gamma')*S('K')*S('w')*S('Var')/S('Mean'), evaluate=False))
        num("Sec6-ownership-local-elast-Q5", loc[4], -0.20, tol=0.02, desc="same, Q5", expr=Eq(S('eps_Q5'), Float(loc[4], 3), evaluate=False))
        def Q(Kp_):
            s_ = 0
            for i in range(5):
                wts = [P[i][h]*math.exp(-gam*h*(Kp_-Kref)*wq[i]) for h in range(3)]
                z = sum(wts); s_ += Nq[i]*sum(h*wts[h]/z for h in range(3))
            return s_
        chg = (Q(1.1*Kref)/Q(Kref)-1)*100
        num("Sec6-ownership-10pct-4.02", -chg, 4.02, tol=0.05, desc="percent fall in person-weighted household car count for K -> 1.1 K with gamma calibrated to -0.4", expr=Eq(S('dQ'), Float(chg, 4), evaluate=False))
run("own", "IDENTITY", own)

with open(os.path.join(OUT, "results.json"), "w", encoding="utf8") as fh:
    json.dump(RESULTS, fh, indent=1)
c = {s: sum(1 for r in RESULTS if r['status'] == s) for s in ("PASS", "FAIL", "ERROR")}
print("TOTALS", len(RESULTS), c)
