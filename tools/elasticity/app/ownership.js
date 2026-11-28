/* Sequential, person-weighted household ownership sensitivity; no microdata needed.
 * Baseline-pivoted logit with an income-scaled cost term:
 *   V_qc = ASC_qc - gamma * K * c * (Y_q / Ybar)^(-lambda), so dV_qc = -gamma * dK * c * (Y_q / Ybar)^(-lambda).
 * gamma matches an aggregate fixed-cost elasticity; lambda sets its income gradient.
 * Income effects on ownership would enter through a separate term that a pure cost
 * scenario does not move, so the income elasticity no longer fixes the cost response.
 * The 2+ category is represented by two cars. Transport utilities use LTM's
 * estimated ownership dummies, with a baseline-normalized conditional-demand pivot.
 */
(function (root) {
  "use strict";
  const CARS = ["0", "1", "2+"];
  const sum = a => a.reduce((s, v) => s + v, 0);
  // Rich (2022), LTM 2.3 weekday report, Table 8.24 (primary mode/destination),
  // Table 8.28 (primary frequency). Column order: HW, HE, escort, shopping, leisure, business.
  const PURPOSES = ["commute", "education", "escort", "shopping", "leisure", "business"];
  const COEFFICIENTS = {
    sov1: [1.415631,4.476547,2.599288,4.253396,4.082484,1.209715],
    sov2: [2.737342,6.300248,3.024147,5.255108,4.773839,1.834992],
    hov1: [1.419997,3.474724,2.570894,3.794248,3.390098,.910964],
    hov2: [2.318398,5.313737,3.53915,4.503134,3.964328,1.44836],
    passenger1: [.554978,1.491315,1.540826,2.160578,1.433549,.45949],
    passenger2: [.76215,2.186472,1.603037,2.680684,2.067378,.649174],
    frequency1: [0,0,-.7299,0,-.2306,-.4422],
    frequency2: [0,0,-.7182,0,-.2598,-.4422],
    frequencyLogsum: [-.1143,-.0101,-.0101,-.0959,-.0731,-.0847],
    k1: [-.9920,-.4592,-5.6968,-1.3296,-1.3476,-5.6467],
    k2: [-2.6602,-3.2669,-6.9109,-2.6937,-2.6802,-6.3735],
    k3: [-6.1528,-6.7980,-9.0668,-4.7949,-4.7772,-9.7157],
    k4: [-8.2468,null,-9.8153,-6.2237,-6.4580,-10.7836]
  };
  function modeEffect(purpose, c) {
    const i = PURPOSES.indexOf(purpose);
    if (i < 0 || ![0,1,2].includes(c)) throw new Error("Unknown purpose or ownership state");
    return c === 0 ? [0,0,0,0,0,0] : [0,0,COEFFICIENTS[`sov${c}`][i],COEFFICIENTS[`hov${c}`][i],COEFFICIENTS[`passenger${c}`][i],0];
  }
  function frequencyZero(purpose, mean) {
    const i = PURPOSES.indexOf(purpose), k = [1,2,3,4].map(f=>COEFFICIENTS[`k${f}`][i]);
    const weights = k.map(v=>v === null ? 0 : Math.exp(v));
    const positiveMean = sum(weights.map((w,j)=>w*(j+1))) / sum(weights);
    if (mean > positiveMean) throw new Error(`Observed frequency for ${purpose} exceeds LTM positive-frequency mean; additional frequency calibration required`);
    return Math.max(0, 1 - mean / positiveMean);
  }
  // Defaults: De Jong et al. (2009) fixed-cost ownership elasticity -0.4; lambda 0.37 is the
  // log-log slope of LTM VoT on personal income (Rich, 2022, Table 5.7), i.e. a cost coefficient
  // scaling with income^-lambda at constant time valuation. Transferring a trip-cost gradient to
  // annual fixed costs is an assumption.
  function prepare(inp, baselineCost, opts = {}) {
    const target = opts.target ?? -0.4, lambda = opts.lambda ?? 0.37;
    if (!(baselineCost > 0) || !(target <= 0) || !(lambda >= 0) || !Number.isFinite(lambda))
      throw new Error("Invalid ownership calibration inputs");
    const K = [0, baselineCost, 2 * baselineCost];
    const rows = Object.keys(inp.income).map(q => {
      const n = CARS.map(c => inp.persons[`${q}|${c}`] || 0), N = sum(n);
      const Y = inp.income[q].hh * 1000;
      // calibration-time sanity guard on the reference cost (no effect on scenario continuity)
      if (!(N > 0) || !(Y > K[2]) || n.some(v => v <= 0))
        throw new Error(`Ownership model needs positive populations and income above baseline costs in Q${q}`);
      return { q: +q, n, N, Y, p: n.map(v => v / N) };
    });
    const Ybar = sum(rows.map(r => r.N * r.Y)) / sum(rows.map(r => r.N));
    rows.forEach(r => { r.w = Math.pow(r.Y / Ybar, -lambda); });
    // Local aggregate elasticity of expected cars w.r.t. K at the observed shares:
    // eps = -gamma K sum_q N_q w_q Var_q(c) / sum_q N_q mean_q(c). Calibrated, not estimated.
    const count = sum(rows.map(r => r.N * sum(r.p.map((p, c) => p * c))));
    const slope = sum(rows.map(r => {
      const mean = sum(r.p.map((p, c) => p * c));
      return r.N * r.w * sum(r.p.map((p, c) => p * (c - mean) ** 2));
    }));
    if (!(slope > 0)) throw new Error("Ownership sensitivity cannot be identified from these inputs");
    return { rows, K, gamma: target === 0 ? 0 : -target * count / (baselineCost * slope), target, lambda, Ybar, baselineCost };
  }
  function scenario(model, change = 0) {
    if (!Number.isFinite(change) || change < -1) throw new Error("Invalid ownership cost change");
    const K = model.K.map(k => k * (1 + change));
    const rows = model.rows.map(r => {
      // No affordability cutoff: the documented form is V = ASC - gamma K c w_q. (A cost-above-income
      // cutoff removed whole ownership states in one 1% step; Codex review 2026-11-28 #4.)
      const v = r.p.map((p, c) => Math.log(p) - model.gamma * (K[c] - model.K[c]) * r.w);
      const top = Math.max(...v), w = v.map(x => Math.exp(x - top)), z = sum(w);
      const p1 = change === 0 ? [...r.p] : w.map(x => x / z);
      return { ...r, p1, n1: p1.map(p => p * r.N), ratio: p1.map((p, c) => p / r.p[c]) };
    });
    return { rows, K, change, active: change !== 0 };
  }
  // Direct fixed-cost burden per household (person-weighted, as the ownership shares), per quintile:
  // m = expected cars per household (2+ counted as 2); spending change K1 m1 - K0 m0; money part of the
  // welfare change by the rule of half (K1 - K0)(m0 + m1)/2; that as a share of household income Y.
  // Per household, not per person: household sizes are not in the data.
  function fixedCost(own) {
    const K1 = own.K[1], K0 = own.change > -1 ? K1 / (1 + own.change) : 0, m = p => p[1] + 2 * p[2];
    return own.rows.map(r => {
      const m0 = m(r.p), m1 = m(r.p1), roh = (K1 - K0) * (m0 + m1) / 2;
      return { q: r.q, N: r.N, m0, m1, spend: K1 * m1 - K0 * m0, roh, shareOfHhIncome: roh / r.Y };
    });
  }
  // Quintile elasticity of expected cars w.r.t. K, numerically at a 1% change.
  function quintileElasticities(model, h = 0.01) {
    const s = scenario(model, h), m = p => p[1] + 2 * p[2];
    return model.rows.map((r, i) => ({ q: r.q, elasticity: Math.log(m(s.rows[i].p1) / m(r.p)) / Math.log(1 + h) }));
  }
  function apply(res, own, inp, cal, engine, lam = 1) {
    if (!own.active) return { ...res, ownership: own };
    if (!["nl", "mnl"].includes(res.model)) throw new Error("Ownership scenarios require NL or MNL");
    const byQ = Object.fromEntries(own.rows.map(r => [r.q, r]));
    const cells = res.cells.map(c => {
      const row = byQ[c.quintile], origin = CARS.indexOf(c.cars), i = PURPOSES.indexOf(c.purpose);
      const ref = modeEffect(c.purpose, origin), zero = [0,0,0,0,0,0];
      const atOrigin = engine.ownershipConditional(inp, cal, c, res.x, lam, zero);
      const p0 = frequencyZero(c.purpose, sum(c.trips0) / row.n[origin]);
      const f0 = origin ? COEFFICIENTS[`frequency${origin}`][i] : 0;
      const conditional = CARS.map((_, dest) => {
        const shift = modeEffect(c.purpose, dest).map((v,j)=>v-ref[j]);
        const r = dest === origin ? atOrigin : engine.ownershipConditional(inp, cal, c, res.x, lam, shift);
        const f = dest ? COEFFICIENTS[`frequency${dest}`][i] : 0;
        const dV0 = f - f0 + COEFFICIENTS.frequencyLogsum[i] * (r.logsumChange - atOrigin.logsumChange);
        const freqRatio = 1 / (1 - p0 + p0 * Math.exp(dV0));
        return { ...r, freqRatio };
      });
      // For each original population cell, compare the SAME counterfactual
      // profiles under new vs baseline ownership probabilities. Pivot that ratio
      // onto the existing transport result so zero change preserves all controls.
      const pivotGrid = (actual, key) => actual.map((a,j)=>a.map((v,b)=> {
        const expected = probs => sum(conditional.map((r,d)=>probs[d]*r[key][j][b]*r.freqRatio));
        const base = expected(row.p), next = expected(row.p1);
        return base > 0 ? v * next / base : v;
      }));
      const T1 = pivotGrid(c.band.T1, "T1"), K1 = pivotGrid(c.band.K1, "K1");
      const out = { ...c, trips1: T1.map(sum), km1: K1.map(sum), band: { ...c.band, T1, K1 } };
      return out;
    });
    return { ...res, cells, ownership: own };
  }
  const api = { CARS, COEFFICIENTS, modeEffect, frequencyZero, prepare, scenario, quintileElasticities, apply, fixedCost };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.CarOwnership = api;
})(typeof window !== "undefined" ? window : globalThis);
