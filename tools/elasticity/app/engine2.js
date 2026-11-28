/* Elasticity engine v2 (workbook schema elasticity-inputs/2; SPEC.md).
 *
 * Input: workbook sheets as arrays of row objects (SheetJS sheet_to_json in the browser, or the
 * JSON dump written by data_prep/build_workbook.py in Node).
 *
 * Demand per purpose: IPDL (Fosgerau, Monardo and de Palma, 2024) over walk, bike, SOV, HOV,
 * car passenger and PT plus a no-trip option,
 *   delta_j = (1 - sum_d mu_d) ln s_j + sum_d mu_d ln s_{d(j)} - ln s_0.
 * Shocks enter through generalized time GT = T + s_m C / VoT. For an affected mode j,
 *   d delta_j = beta_j ln(1 + sC_j x_cost + (1 - sC_j) x_time),
 * with sC_j the money share of GT. Cost sharing is structural: the money-to-time odds of HOV and
 * car passenger are the SOV odds times their cost shares s_m (Rich, 2022, Table 5.8).
 *
 * Calibration (per purpose): on the TU 2009-11 cells (income quintile x cars, each with its own
 * shares and relative VoT), so that the cells aggregated reproduce the Rich (2022) primary-tour trip
 * elasticities; this matches the disaggregate model behind the targets and avoids the aggregation
 * bias of a representative-traveller fit. Free: nest weights mu_d, a common share tilt (alternative-
 * specific shifts, penalised toward 0), betas, SOV and PT money shares (penalised toward priors from
 * TOEE fuel + tyres cost, TERESA VoT and the PT fare).
 * Rebasing (per purpose x income quintile x cars cell): shares replaced by the cell's TU 2023
 * shares; money-to-time odds scaled by the 2010-2023 update ratio r and by the cell's VoT relative
 * to the average traveller (Rich, 2022, Table 5.7). mu, beta and cost shares are kept.
 * Average tour length: log-linear pivot on the Rich (2022) length elasticities.
 *
 * Three models (calibrate(inp, onProgress, model)):
 *   "nl"   (default) two-level nested logit over mode x tour length: the LTM 2.3 mode-destination
 *          structure with destinations represented by tour length (section "NL mode x length").
 *          Calibrated to trip, average-length and band elasticities; bands and mileage are model output.
 *   "mnl"  the same model with theta = 1 (multinomial logit over mode x length).
 *   "ipdl" the IPDL over modes described above, with the length pivot and the band split.
 * Works in the browser (window.ElastEngine2) and in Node (module.exports).
 */
(function (root) {
  "use strict";
  const MODES = ["walk", "bike", "sov", "hov", "carp", "pt"];
  const SHOCKS = ["CC", "CT", "PC", "PT"];
  const PURPOSES = ["commute", "education", "escort", "shopping", "leisure", "business"];
  const BANDS = ["0-20", "20-50", "50-100", "100-200", "200-300", "300+"];
  const M = 6, K = 4, REF = 2; // SOV is the reference share logit
  const GT = [ // modes affected by level of service: j, cost shock, time shock, kind
    { j: 2, cost: 0, time: 1, kind: "car" }, { j: 3, cost: 0, time: 1, kind: "car" },
    { j: 4, cost: 0, time: 1, kind: "car" }, { j: 5, cost: 2, time: 3, kind: "pt" }];
  const GROUPINGS = [ // IPDL nesting dimensions; the last one separates walk from bike
    [["walk", "bike"], ["sov", "hov", "carp"], ["pt"]],
    [["walk", "bike"], ["sov", "hov", "carp", "pt"]],
    [["hov", "carp"], ["sov"], ["walk", "bike", "pt"]],
    [["walk"], ["bike", "sov", "hov", "carp", "pt"]]];
  const SHEETS = ["targets", "band_elasticities", "vot_income", "cost_shares", "cell_shares", "tu_persons",
    "tu_income_quintiles", "tu_journeys", "teresa", "costs", "update_2023", "settings"];

  const sum = a => a.reduce((s, v) => s + v, 0);
  const logit = p => Math.log(p / (1 - p)), expit = z => 1 / (1 + Math.exp(-z));
  const z6 = () => new Array(M).fill(0);
  const z64 = () => Array.from({ length: M }, () => new Array(K).fill(0));

  // ---------------------------------------------------------------- input preparation
  function validate(sheets) {
    const err = [];
    SHEETS.forEach(s => { if (!Array.isArray(sheets[s])) err.push(`missing sheet '${s}'`); });
    if (err.length) return err;
    const st = Object.fromEntries(sheets.settings.map(r => [r.key, r.value]));
    if (st.schema !== "elasticity-inputs/2") err.push(`schema must be 'elasticity-inputs/2' (found '${st.schema}')`);
    // all three measures are calibration targets; a missing mileage target used to become a zero target
    PURPOSES.forEach(p => MODES.forEach(m => SHOCKS.forEach(k => ["trips", "avg_length", "mileage"].forEach(me => {
      const rs = sheets.targets.filter(t => t.purpose === p && t.mode === m && t.shock === k && t.measure === me);
      if (!rs.length || !Number.isFinite(rs[0].value)) err.push(`targets: ${p}/${m}/${k}/${me} missing or not a number`);
      else if (rs.length > 1) err.push(`targets: ${p}/${m}/${k}/${me} appears ${rs.length} times`);
    }))));
    ["calibration_period", "base_period"].forEach(k => {
      if (!sheets.cell_shares.some(r => r.period === st[k])) err.push(`cell_shares has no rows for ${k} '${st[k]}'`);
    });
    return err;
  }

  function prepare(sheets) {
    const err = validate(sheets);
    if (err.length) throw new Error("Invalid workbook: " + err.join("; "));
    const warnings = [];
    const st = Object.fromEntries(sheets.settings.map(r => [r.key, isNaN(+r.value) ? r.value : +r.value]));
    const item = (sheet, key) => { const r = sheets[sheet].find(q => q.item === key); return r ? r.value : null; };
    const teresa = (key, y) => sheets.teresa.find(r => r.item === key && r.year === y).value;
    const calP = st.calibration_period, baseP = st.base_period;

    const tgt = {}, avgl = {}, cs = {}, calShares = {}, cells = {}, calCells = {}, vot = {}, bandE = {}, bandBase = {};
    PURPOSES.forEach(p => {
      tgt[p] = z64(); avgl[p] = z64();
      sheets.targets.filter(r => r.purpose === p).forEach(r => {
        const j = MODES.indexOf(r.mode), k = SHOCKS.indexOf(r.shock);
        if (r.measure === "trips") tgt[p][j][k] = r.value;
        if (r.measure === "avg_length") avgl[p][j][k] = r.value;
      });
      const c = m => sheets.cost_shares.find(r => r.purpose === p && r.mode === m).cost_share;
      cs[p] = { sov: 1, hov: c("hov"), carp: c("carp") };

      const cal = z6();
      sheets.cell_shares.filter(r => r.period === calP && r.purpose === p).forEach(r => { cal[MODES.indexOf(r.mode)] += r.journeys; });
      calShares[p] = floorShares(cal.map(v => v / sum(cal)));

      cells[p] = buildCells(sheets.cell_shares.filter(r => r.period === baseP && r.purpose === p));
      calCells[p] = buildCells(sheets.cell_shares.filter(r => r.period === calP && r.purpose === p));


      vot[p] = votSchedule(sheets.vot_income.filter(r => r.purpose === p));
      bandE[p] = {};
      sheets.band_elasticities.filter(r => r.purpose === p).forEach(r => {
        const key = `${r.mode}|${r.shock}`; (bandE[p][key] = bandE[p][key] || {})[r.band] = r.value;
      });
      bandBase[p] = {};
      sheets.tu_journeys.filter(r => r.period === baseP && r.purpose === p && MODES.includes(r.mode) && BANDS.includes(r.band)).forEach(r => {
        const b = (bandBase[p][r.mode] = bandBase[p][r.mode] || Object.fromEntries(BANDS.map(x => [x, { trips: 0, km: 0 }])));
        b[r.band].trips += r.journeys; b[r.band].km += r.tour_km;
      });
    });

    const persons = {};
    sheets.tu_persons.filter(r => r.period === baseP && String(r.cars) !== "unknown").forEach(r => { persons[`${r.quintile}|${r.cars}`] = r.persons; });
    const incRows = q => sheets.tu_income_quintiles.filter(r => r.period === q);
    const avgInc = rows => sum(rows.map(r => r.resp_mean * r.persons)) / sum(rows.map(r => r.persons));
    const incomeOf = q => Object.fromEntries(incRows(q).map(r => [r.quintile, { resp: r.resp_mean, hh: r.hh_mean, rel: r.resp_mean / avgInc(incRows(q)) }]));
    const income = incomeOf(baseP), calIncome = incomeOf(calP);

    let rPt = item("update_2023", "r_pt"), cpi = item("update_2023", "cpi_2023_over_2010");
    if (!Number.isFinite(rPt)) { rPt = 1; warnings.push("r_pt missing: PT money share not updated 2010-2023 (r_pt = 1)"); }
    if (!Number.isFinite(cpi)) { cpi = 1.27; warnings.push("cpi_2023_over_2010 missing: using 1.27"); }
    const rCar = item("update_2023", "r_car");
    // average personal income of the calibration period on the 2010 VoT schedule (DKK, 2010 prices)
    const y2010 = avgInc(incRows(calP)) * 1000 / cpi;

    // money-share priors: TOEE fuel + tyres cost and TERESA VoT (both fixed 2025 prices), assumed speeds
    const priorSC = {};
    PURPOSES.forEach(p => {
      const biz = p === "business";
      const votMin = teresa(biz ? "vot_driving_business" : (p === "commute" ? "vot_driving_commute" : "vot_driving_other"), 2010) / 60;
      const carC = item("costs", "car_variable_cost_per_km_2010"); // TOEE fuel + tyres (LTM definition)
      const carMoney = carC / votMin, carTime = 60 / st.car_speed_kmh;
      const L = sum(cells[p].map(c => c.len[5] * c.base[5])) / Math.max(sum(cells[p].map(c => c.base[5])), 1e-9) || 20;
      const fareKm = (2 * item("costs", "pt_fare_offset_per_trip") + item("costs", "pt_fare_per_km") * L) / L;
      const ptMoney = fareKm / votMin, ptTime = 60 / st.pt_speed_kmh;
      priorSC[p] = { sov: carMoney / (carMoney + carTime), pt: ptMoney / (ptMoney + ptTime) };
    });

    const costs = {
      carPerKm: item("costs", "car_variable_cost_per_km"),
      fareOffset: item("costs", "pt_fare_offset_per_trip"), farePerKm: item("costs", "pt_fare_per_km"),
      fareMaxKm: item("costs", "pt_fare_valid_max_tour_km"),
    };
    if ((sheets.settings.find(r => r.key === "annual_days") || {}).description?.startsWith("PLACEHOLDER"))
      warnings.push("annual_days is a placeholder");

    const kmT = {}, nl = { cells: {}, calCells: {} };
    PURPOSES.forEach(p => {
      kmT[p] = z64();
      sheets.targets.filter(r => r.purpose === p && r.measure === "mileage").forEach(r => { kmT[p][MODES.indexOf(r.mode)][SHOCKS.indexOf(r.shock)] = r.value; });
      nl.cells[p] = nlCells(sheets, st, p, baseP);
      nl.calCells[p] = nlCells(sheets, st, p, calP);
    });

    return { st, tgt, avgl, kmT, cs, calShares, cells, calCells, nl, vot, bandE, bandBase, persons, income, calIncome, rCar, rPt, y2010,
      priorSC, costs, warnings, fp: fingerprint(sheets) };
  }

  // cells (quintile x cars) of one purpose and period from cell_shares rows
  function buildCells(rows) {
    const byCell = {};
    rows.forEach(r => {
      const key = `${r.quintile}|${r.cars}`;
      if (!byCell[key]) byCell[key] = { quintile: r.quintile, cars: String(r.cars), share: z6(), len: z6(), trips: 0 };
      const j = MODES.indexOf(r.mode);
      byCell[key].share[j] = r.share_shrunk; byCell[key].len[j] = r.mean_tour_km || 0; byCell[key].trips += r.journeys;
    });
    // mode lengths missing in a cell (no observations) fall back to the purpose mean
    const pl = z6(), pw = z6();
    Object.values(byCell).forEach(c => c.share.forEach((s, j) => { if (c.len[j] > 0) { pl[j] += c.len[j] * s * c.trips; pw[j] += s * c.trips; } }));
    return Object.values(byCell).filter(c => c.cars !== "unknown").map(c => {
      const share = floorShares(c.share);
      return { ...c, share, len: c.len.map((l, j) => l > 0 ? l : (pw[j] > 0 ? pl[j] / pw[j] : 0)), base: share.map(s => s * c.trips) };
    });
  }

  function floorShares(s, eps = 1e-6) {
    const f = s.map(v => Math.max(Number.isFinite(v) ? v : 0, eps)), t = sum(f);
    return f.map(v => v / t);
  }

  // VoT (DKK/min, 2010) as a piecewise-linear function of personal income through band midpoints
  function votSchedule(rows) {
    // the zero-income group (lower = upper = 0) is skipped; an open top band (upper null/inf) is
    // placed at 1.5 x its lower bound
    const pts = rows.filter(r => !(r.income_lower_dkk === 0 && r.income_upper_dkk === 0)).map(r => {
      const hi = Number.isFinite(r.income_upper_dkk) ? r.income_upper_dkk : r.income_lower_dkk * 1.5;
      return [(r.income_lower_dkk + hi) / 2, r.vot_dkk_per_min];
    }).sort((a, b) => a[0] - b[0]);
    return y => {
      if (y <= pts[0][0]) return pts[0][1];
      for (let i = 1; i < pts.length; i++) if (y <= pts[i][0]) {
        const [x0, v0] = pts[i - 1], [x1, v1] = pts[i];
        return v0 + (v1 - v0) * (y - x0) / (x1 - x0);
      }
      return pts[pts.length - 1][1];
    };
  }

  function fingerprint(sheets) {
    const core = JSON.stringify(SHEETS.map(s => sheets[s]));
    let h = 0x811c9dc5;
    for (let i = 0; i < core.length; i++) { h ^= core.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
    return h.toString(16);
  }

  // ---------------------------------------------------------------- IPDL core
  // G[d][i][j] = 1 when modes i and j share a group in dimension d. setGroupings() replaces the
  // nesting structure (used for the structure comparison in the documentation); each dimension must
  // partition the six modes.
  let G, D;
  function setGroupings(groupings) {
    groupings.forEach((dim, d) => {
      const seen = dim.flat().sort().join(",");
      if (seen !== [...MODES].sort().join(",")) throw new Error(`nesting dimension ${d + 1} is not a partition of the modes`);
    });
    G = groupings.map(dim => {
      const A = Array.from({ length: M }, () => new Array(M).fill(0));
      dim.forEach(g => { const idx = g.map(m => MODES.indexOf(m)); idx.forEach(i => idx.forEach(j => { A[i][j] = 1; })); });
      return A;
    });
    D = G.length;
  }
  setGroupings(GROUPINGS);
  const matvec = (A, v) => A.map(r => r.reduce((s, a, j) => s + a * v[j], 0));
  function invDemand(y, mu) {
    const s = y.map(Math.exp), s0 = 1 - sum(s), ms = sum(mu);
    const out = y.map(v => (1 - ms) * v - Math.log(s0));
    G.forEach((A, d) => { const sg = matvec(A, s); for (let i = 0; i < M; i++) out[i] += mu[d] * Math.log(sg[i]); });
    return out;
  }
  function jacInv(y, mu) {
    const s = y.map(Math.exp), s0 = 1 - sum(s), ms = sum(mu);
    const J = Array.from({ length: M }, (_, i) => s.map((sj, j) => (i === j ? 1 - ms : 0) + sj / s0));
    G.forEach((A, d) => { const sg = matvec(A, s); for (let i = 0; i < M; i++) for (let j = 0; j < M; j++) J[i][j] += mu[d] * A[i][j] * s[j] / sg[i]; });
    return J;
  }
  function solveLin(A, b) {
    const n = b.length, a = A.map((r, i) => [...r, b[i]]);
    for (let c = 0; c < n; c++) {
      let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(a[r][c]) > Math.abs(a[p][c])) p = r;
      [a[c], a[p]] = [a[p], a[c]];
      if (Math.abs(a[c][c]) < 1e-300) a[c][c] = 1e-300;
      for (let r = c + 1; r < n; r++) { const f = a[r][c] / a[c][c]; for (let k = c; k <= n; k++) a[r][k] -= f * a[c][k]; }
    }
    const x = new Array(n).fill(0);
    for (let r = n - 1; r >= 0; r--) { let s = a[r][n]; for (let k = r + 1; k < n; k++) s -= a[r][k] * x[k]; x[r] = s / a[r][r]; }
    return x;
  }
  // Newton with backtracking: a step is accepted only inside the simplex and when the residual norm
  // falls. y.ok is false when the residual did not reach the tolerance.
  function solveShares(delta, y0, mu) {
    let y = y0.slice();
    const res = v => { const F = invDemand(v, mu).map((q, i) => q - delta[i]); return { F, n: Math.max(...F.map(Math.abs)) }; };
    let cur = res(y);
    for (let it = 0; it < 200 && cur.n >= 1e-11; it++) {
      const step = solveLin(jacInv(y, mu), cur.F);
      let t = 1, moved = false;
      while (t > 1e-10) {
        const yn = y.map((v, i) => v - t * step[i]);
        if (yn.every(Number.isFinite) && sum(yn.map(Math.exp)) < 1) {
          const rn = res(yn);
          if (Number.isFinite(rn.n) && rn.n < cur.n) { y = yn; cur = rn; moved = true; break; }
        }
        t /= 2;
      }
      if (!moved) break;
    }
    y.ok = cur.n < 1e-9;
    return y;
  }

  // money share of GT per affected mode, from SOV/PT odds, cost shares and odds scales
  function moneyShares(par, cs, scale = { car: 1, pt: 1 }) {
    const oSov = par.sC.sov / (1 - par.sC.sov) * scale.car, oPt = par.sC.pt / (1 - par.sC.pt) * scale.pt;
    const o = [oSov * cs.sov, oSov * cs.hov, oSov * cs.carp, oPt];
    return o.map(v => v / (1 + v));
  }
  // trip ratios T1/T0 by mode for shares w (sum 1 over modes; s0 added), shocks x (4)
  function tripRatios(par, w, s0, cs, x, scale) {
    const y0 = w.map(v => Math.log((1 - s0) * v));
    const d0 = invDemand(y0, par.mu), sC = moneyShares(par, cs, scale), dv = z6();
    GT.forEach((g, i) => {
      const arg = 1 + sC[i] * x[g.cost] + (1 - sC[i]) * x[g.time];
      dv[g.j] = par.beta[i] * Math.log(Math.max(arg, 1e-6));
    });
    const y1 = solveShares(d0.map((d, j) => d + dv[j]), y0, par.mu);
    const r = y1.map((v, j) => Math.exp(v - y0[j]));
    r.ok = y1.ok;
    return r;
  }
  const logEl = (E, xr) => E.map(r => r.map(e => Math.log1p(xr * e) / Math.log1p(xr)));
  const pivot = (L, x) => L.map(r => r.reduce((p, e, k) => p * Math.pow(1 + x[k], e), 1));

  // ---------------------------------------------------------------- calibration
  function unpack(th) {
    const u = th.slice(0, D), eu = u.map(Math.exp), den = 1 + sum(eu);
    const mu = eu.map(v => 0.97 * v / den);
    const zl = th.slice(D, D + 5), tilt = [...zl.slice(0, REF), 0, ...zl.slice(REF)];
    const b = th.slice(D + 5, D + 9);
    return { mu, tilt, beta: b.map(q => -Math.exp(q)), sC: { sov: expit(th[D + 9]), pt: expit(th[D + 10]) } };
  }
  const applyTilt = (w, tilt) => { const v = w.map((s, j) => Math.log(s) + tilt[j]), mx = Math.max(...v), e = v.map(a => Math.exp(a - mx)); return e.map(a => a / sum(e)); };
  // calibration-period cells with the tilt applied: shares, trip weights and odds scales (no 2010-2023 update)
  function calSetup(inp, p, tilt) {
    return inp.calCells[p].map(c => {
      const w = applyTilt(c.share, tilt), rel = inp.calIncome[c.quintile] ? inp.calIncome[c.quintile].rel : 1;
      const vr = inp.vot[p](inp.y2010) / inp.vot[p](inp.y2010 * rel);
      return { w, T: w.map(s => s * c.trips), scale: { car: vr, pt: vr } };
    });
  }
  // aggregate trip elasticities of the calibration-period cells
  function fittedAggregate(inp, p, par) {
    if (isNL(par.model)) return nlFitted(inp, p, par).trips;
    const setup = calSetup(inp, p, par.tilt), out = z64(), xr = inp.st.x_ref;
    for (let k = 0; k < K; k++) {
      const x = new Array(K).fill(0); x[k] = xr;
      const T0 = z6(), T1 = z6();
      setup.forEach(c => tripRatios(par, c.w, inp.st.s0, inp.cs[p], x, c.scale).forEach((r, j) => { T0[j] += c.T[j]; T1[j] += c.T[j] * r; }));
      for (let j = 0; j < M; j++) out[j][k] = (T1[j] / T0[j] - 1) / xr;
    }
    return out;
  }
  const MODELS = ["nl", "mnl", "ipdl"], VERSION = "engine2/3";
  const aggShares = setup => { const T = z6(); setup.forEach(c => c.T.forEach((v, j) => { T[j] += v; })); return T.map(v => v / sum(T)); };
  function fittedE(par, w, s0, cs, xr, scale) {
    const out = z64();
    for (let k = 0; k < K; k++) {
      const x = new Array(K).fill(0); x[k] = xr;
      tripRatios(par, w, s0, cs, x, scale).forEach((r, j) => { out[j][k] = (r - 1) / xr; });
    }
    return out;
  }
  function residuals(inp, p, th) {
    const par = unpack(th), st = inp.st, f = fittedAggregate(inp, p, par), r = [];
    // inp.targetMask (optional, 24 weights, index j*4+k) drops targets for cross-validation
    for (let j = 0; j < M; j++) for (let k = 0; k < K; k++) r.push((inp.targetMask ? inp.targetMask[j * K + k] : 1) * (f[j][k] - inp.tgt[p][j][k]));
    par.tilt.forEach((a, j) => { if (j !== REF) r.push(st.prior_weight * a); });
    r.push(st.sc_prior_weight * (logit(par.sC.sov) - logit(inp.priorSC[p].sov)));
    r.push(st.sc_prior_weight * (logit(par.sC.pt) - logit(inp.priorSC[p].pt)));
    return r;
  }
  const sq = r => r.reduce((s, v) => s + v * v, 0);
  function lm(fun, th0, maxIt = 200) {
    let th = th0.slice(), r = fun(th), c = sq(r), lam = 1e-2;
    for (let it = 0; it < maxIt; it++) {
      const n = th.length, J = [];
      for (let i = 0; i < n; i++) {
        const h = 1e-6 * Math.max(1, Math.abs(th[i])), t2 = th.slice(); t2[i] += h;
        const r2 = fun(t2); J.push(r2.map((v, q) => (v - r[q]) / h));
      }
      const JtJ = Array.from({ length: n }, (_, a) => Array.from({ length: n }, (_, b) => J[a].reduce((s, v, q) => s + v * J[b][q], 0)));
      const Jtr = J.map(col => col.reduce((s, v, q) => s + v * r[q], 0));
      let improved = false;
      for (let tries = 0; tries < 12; tries++) {
        const A = JtJ.map((row, a) => row.map((v, b) => v + (a === b ? lam * (v + 1e-9) : 0)));
        const step = solveLin(A, Jtr.map(v => -v));
        const tn = th.map((v, i) => v + Math.max(-3, Math.min(3, step[i])));
        const rn = fun(tn), cn = sq(rn);
        if (Number.isFinite(cn) && cn < c) {
          const rel = (c - cn) / Math.max(c, 1e-30);
          th = tn; r = rn; c = cn; lam = Math.max(lam / 3, 1e-9); improved = true;
          if (rel < 1e-10) return { th, cost: c };
          break;
        }
        lam *= 4;
      }
      if (!improved) break;
    }
    return { th, cost: c };
  }
  function calibratePurpose(inp, p, model = "ipdl") {
    if (isNL(model)) return nlCalibratePurpose(inp, p, model);
    let best = null;
    [0.1, 0.5].forEach(tot => {
      const u0 = Math.log(tot / D / (0.97 - tot));
      const th0 = [...new Array(D).fill(u0), 0, 0, 0, 0, 0, 0, 0, 0, 0, logit(inp.priorSC[p].sov), logit(inp.priorSC[p].pt)];
      const res = lm(th => residuals(inp, p, th), th0);
      if (!best || res.cost < best.cost) best = res;
    });
    const par = unpack(best.th), f = fittedAggregate(inp, p, par);
    let se = 0, mx = 0;
    for (let j = 0; j < M; j++) for (let k = 0; k < K; k++) { const e = f[j][k] - inp.tgt[p][j][k]; se += e * e; mx = Math.max(mx, Math.abs(e)); }
    const w = aggShares(calSetup(inp, p, par.tilt)), prior_w = aggShares(calSetup(inp, p, z6()));
    return { ...par, model: "ipdl", w, fitted: f, rmse: Math.sqrt(se / (M * K)), maxerr: mx, prior_w, prior_sC: inp.priorSC[p] };
  }
  function calibrate(inp, onProgress, model = "nl") {
    if (!MODELS.includes(model)) throw new Error(`unknown model '${model}'`);
    const purposes = {};
    PURPOSES.forEach((p, i) => { purposes[p] = calibratePurpose(inp, p, model); if (onProgress) onProgress(i + 1, PURPOSES.length, p); });
    return { model, version: VERSION, fingerprint: inp.fp, at: new Date().toISOString(), purposes };
  }

  // ---------------------------------------------------------------- NL mode x length
  // Alternatives per cell (income quintile x cars): mode j, tour-length band b and a length node q
  // inside the band. Base tours T_jb (TU, shrunk toward the purpose x cars pattern with strength
  // shrink_k) are spread over the nodes of the band: walk and bike by l^a exp(-kappa_j l), with kappa_j
  // from the LTM 2.3 linear time coefficients (Rich, 2022, Table 8.25; mean of the OTM = 1 and OTM = 0
  // values; time one way, l in tour-km) and a matched to the TU band mean; the other modes by a
  // truncated exponential matched to the band mean.
  // Nesting as in LTM 2.3 (Rich, 2022, Tables 5.1 and 8.49): "B" is p(m|d)p(d), destinations (length
  // nodes) on top and modes below; "A" is p(d|m)p(m). The upper level is scaled by theta (PLogsum).
  // With the base shares taken as observed, the alternative constants are implicit and a shock has a
  // closed form (no inversion):
  //   W_n = sum_{i in n} P0(i|n) e^{dV_i},  T1_i = T0_n W_n^theta / Z x P0(i|n) e^{dV_i} / W_n,
  // where Z renormalises over the nests and the no-trip option (share s0).
  // Shock: dV = -beta_j [ (l/20)^phiC hC + (l/20)^phiT hT ], with hC + hT = ln(1 + sC xC + (1 - sC) xT)
  // split in proportion to the cost and time terms; phi spans log GT (0) to roughly linear GT (1).
  const NB = BANDS.length;
  let NL_W_KM = 1; // default weight on the mileage targets (settings key nl_w_mileage overrides)
  const NL_STRUCTURE = { commute: "B", education: "A", escort: "B", shopping: "B", leisure: "B", business: "B" };
  const LTM_WALK = { commute: [-0.15618, -0.09108], education: [-0.32764, -0.23635], escort: [-0.28903, -0.20565],
    shopping: [-0.33218, -0.19997], leisure: [-0.27036, -0.12346], business: [-0.14648, -0.14399] };
  const LTM_BIKE = { commute: [-0.13105, -0.13405], education: [-0.25161, -0.22274], escort: [-0.36525, -0.24838],
    shopping: [-0.3426, -0.19431], leisure: [-0.24225, -0.16063], business: [-0.15335, -0.14003] };
  const BLO = [0.1, 20, 50, 100, 200, 300], BHI = [20, 50, 100, 200, 300, null], NNB = [40, 12, 12, 12, 12, 16];
  const BMID = [8, 32, 70, 135, 230, 450];

  function lengthNodes(b, mean, kappa) {
    const lo = BLO[b], hi = BHI[b] ?? 300 + 8 * Math.max(mean - 300, 20), n = NNB[b];
    const m = Math.min(Math.max(mean, lo + 0.02 * (hi - lo)), hi - 0.02 * (hi - lo));
    const l = Array.from({ length: n }, (_, i) => lo + (i + 0.5) * (hi - lo) / n);
    const norm = w => { const W = sum(w); return w.map(v => v / W); };
    const meanOf = w => sum(w.map((v, i) => v * l[i]));
    if (kappa > 0) { // walk, bike: l^a exp(-kappa l)
      const mk = a => norm(l.map(v => Math.pow(v, a) * Math.exp(-kappa * (v - lo))));
      let a0 = -0.95, a1 = 12;
      if (meanOf(mk(a0)) < m && meanOf(mk(a1)) > m) {
        for (let it = 0; it < 60; it++) { const c = (a0 + a1) / 2; if (meanOf(mk(c)) < m) a0 = c; else a1 = c; }
        return { l, w: mk((a0 + a1) / 2) };
      }
    }
    const mk = r => norm(l.map(v => Math.exp(-r * (v - lo))));
    let r0 = -50 / (hi - lo), r1 = 50 / (hi - lo);
    for (let it = 0; it < 80; it++) { const c = (r0 + r1) / 2; if (meanOf(mk(c)) > m) r0 = c; else r1 = c; }
    return { l, w: mk((r0 + r1) / 2) };
  }

  // NL cells of one purpose and period from tu_journeys (quintile x cars x mode x band)
  function nlCells(sheets, st, p, period) {
    const kS = Number.isFinite(st.shrink_k) ? st.shrink_k : 30;
    const vW = Number.isFinite(st.walk_speed_kmh) ? st.walk_speed_kmh : 5, vB = Number.isFinite(st.bike_speed_kmh) ? st.bike_speed_kmh : 15;
    const kappa = [-(LTM_WALK[p][0] + LTM_WALK[p][1]) / 2 * 60 / vW / 2, -(LTM_BIKE[p][0] + LTM_BIKE[p][1]) / 2 * 60 / vB / 2, 0, 0, 0, 0];
    const grid = () => MODES.map(() => new Array(NB).fill(0));
    const rows = sheets.tu_journeys.filter(r => r.period === period && r.purpose === p && String(r.cars) !== "unknown" && MODES.includes(r.mode) && BANDS.includes(r.band));
    const by = {}, prior = {}, Kp = grid(), Tp = grid();
    rows.forEach(r => {
      const key = `${r.quintile}|${r.cars}`, j = MODES.indexOf(r.mode), b = BANDS.indexOf(r.band), cars = String(r.cars);
      const c = (by[key] = by[key] || { quintile: r.quintile, cars, T: grid(), K: grid(), n: 0 });
      c.T[j][b] += r.journeys; c.K[j][b] += r.tour_km; c.n += r.n || 0;
      (prior[cars] = prior[cars] || grid())[j][b] += r.journeys;
      Kp[j][b] += r.tour_km; Tp[j][b] += r.journeys;
    });
    return Object.values(by).map(c => {
      const tot = sum(c.T.map(sum)), pr = prior[c.cars], prTot = sum(pr.map(sum));
      const T = c.T.map((row, j) => row.map((t, b) => (c.n * t / tot + kS * pr[j][b] / prTot) / (c.n + kS) * tot));
      const L = c.T.map((row, j) => row.map((t, b) => t > 0 ? c.K[j][b] / t : (Tp[j][b] > 0 ? Kp[j][b] / Tp[j][b] : BMID[b])));
      const alt = { j: [], b: [], q: [], l: [], t0: [] };
      for (let j = 0; j < M; j++) for (let b = 0; b < NB; b++) {
        if (T[j][b] <= 0) continue;
        const nd = lengthNodes(b, L[j][b], kappa[j]);
        nd.l.forEach((l, q) => { alt.j.push(j); alt.b.push(b); alt.q.push(q); alt.l.push(l); alt.t0.push(T[j][b] * nd.w[q]); });
      }
      const nestOf = keyf => { const ids = new Map(); return alt.j.map((_, a) => { const k = keyf(a); if (!ids.has(k)) ids.set(k, ids.size); return ids.get(k); }); };
      const nestB = nestOf(a => alt.b[a] * 100 + alt.q[a]), nestA = nestOf(a => alt.j[a]);
      return { quintile: c.quintile, cars: c.cars, trips: tot, T, L, alt, nestB, nestA, nB: Math.max(...nestB) + 1, nA: Math.max(...nestA) + 1 };
    });
  }

  const gl = s => (Math.abs(s) < 1e-12 ? 1 : Math.log(Math.max(1 + s, 1e-6)) / s);
  // response of one NL cell: tours and km by mode x band before and after shocks x
  function nlCellResponse(par, c, x, scale, cs, s0, structure, modeShift = z6()) {
    const sC = moneyShares(par, cs, scale), bj = z6(), pC = z6(), pT = z6(), hC = z6(), hT = z6();
    GT.forEach((g, i) => {
      const a = sC[i] * x[g.cost], b = (1 - sC[i]) * x[g.time], f = gl(a + b), k = g.kind === "pt" ? 1 : 0;
      hC[g.j] = a * f; hT[g.j] = b * f; bj[g.j] = par.beta[i]; pT[g.j] = par.phi[k]; pC[g.j] = par.phi[k] + par.dphiC[k];
    });
    const tilt = par.tilt || z6(), A = c.alt, nA = A.j.length;
    const t0 = new Array(nA);
    let tt = 0;
    for (let a = 0; a < nA; a++) { t0[a] = A.t0[a] * Math.exp(tilt[A.j[a]]); tt += t0[a]; }
    for (let a = 0; a < nA; a++) t0[a] *= c.trips / tt;
    const nest = structure === "A" ? c.nestA : c.nestB, nN = structure === "A" ? c.nA : c.nB;
    const Tn = new Array(nN).fill(0), Wn = new Array(nN).fill(0), te = new Array(nA);
    for (let a = 0; a < nA; a++) {
      const j = A.j[a], u = A.l[a] / 20;
      te[a] = t0[a] * Math.exp(modeShift[j]) * (bj[j] ? Math.exp(-bj[j] * (Math.pow(u, pC[j]) * hC[j] + Math.pow(u, pT[j]) * hT[j])) : 1);
      Tn[nest[a]] += t0[a]; Wn[nest[a]] += te[a];
    }
    const N0 = c.trips / (1 - s0) * s0, Tn1 = Tn.map((t, n) => t > 0 ? t * Math.pow(Wn[n] / t, par.theta) : 0);
    const Z = (N0 + c.trips) / (N0 + sum(Tn1));
    const grid = () => MODES.map(() => new Array(NB).fill(0));
    const T0 = grid(), T1 = grid(), K0 = grid(), K1 = grid();
    for (let a = 0; a < nA; a++) {
      const n = nest[a], t1 = Wn[n] > 0 ? Tn1[n] * Z * te[a] / Wn[n] : 0, j = A.j[a], b = A.b[a];
      T0[j][b] += t0[a]; T1[j][b] += t1; K0[j][b] += t0[a] * A.l[a]; K1[j][b] += t1 * A.l[a];
    }
    return { T0, T1, K0, K1, logsumChange: Math.log(sum(Tn1) / c.trips) };
  }
  // calibration-period cell scale: VoT relative to the average traveller (no 2010-2023 update)
  function calScale(inp, p, quintile) {
    const rel = inp.calIncome[quintile] ? inp.calIncome[quintile].rel : 1, vr = inp.vot[p](inp.y2010) / inp.vot[p](inp.y2010 * rel);
    return { car: vr, pt: vr };
  }
  // fitted trip, length, mileage and band elasticities of the calibration-period cells
  function nlFitted(inp, p, par) {
    const out = { trips: z64(), len: z64(), km: z64(), band: MODES.map(() => BANDS.map(() => new Array(K).fill(NaN))) }, xr = inp.st.x_ref;
    for (let k = 0; k < K; k++) {
      const x = new Array(K).fill(0); x[k] = xr;
      const T0 = MODES.map(() => new Array(NB).fill(0)), T1 = MODES.map(() => new Array(NB).fill(0)), K0 = z6(), K1 = z6();
      inp.nl.calCells[p].forEach(c => {
        const r = nlCellResponse(par, c, x, calScale(inp, p, c.quintile), inp.cs[p], inp.st.s0, par.structure);
        for (let j = 0; j < M; j++) for (let b = 0; b < NB; b++) { T0[j][b] += r.T0[j][b]; T1[j][b] += r.T1[j][b]; K0[j] += r.K0[j][b]; K1[j] += r.K1[j][b]; }
      });
      for (let j = 0; j < M; j++) {
        const t0 = sum(T0[j]), t1 = sum(T1[j]);
        out.trips[j][k] = (t1 / t0 - 1) / xr;
        out.len[j][k] = ((K1[j] / t1) / (K0[j] / t0) - 1) / xr;
        out.km[j][k] = (K1[j] / K0[j] - 1) / xr;
        for (let b = 0; b < NB; b++) if (T0[j][b] > 0) out.band[j][b][k] = (T1[j][b] / T0[j][b] - 1) / xr;
      }
    }
    return out;
  }
  function nlUnpack(th, model, structure) {
    return { model, structure, beta: th.slice(0, 4).map(Math.exp), phi: [th[4], th[5]], sC: { sov: expit(th[6]), pt: expit(th[7]) },
      theta: model === "mnl" ? 1 : 0.05 + 0.95 * expit(th[8]), tilt: [th[9], th[10], 0, th[11], th[12], th[13]], dphiC: [th[14], th[15]] };
  }
  function nlBandTargets(inp, p) {
    const out = [];
    Object.entries(inp.bandE[p]).forEach(([key, prof]) => {
      const [m, s] = key.split("|"); BANDS.forEach((b, i) => { if (Number.isFinite(prof[b])) out.push({ j: MODES.indexOf(m), k: SHOCKS.indexOf(s), b: i, value: prof[b] }); });
    });
    return out;
  }
  function nlResiduals(inp, p, th, model, structure, bandT) {
    const par = nlUnpack(th, model, structure), f = nlFitted(inp, p, par), st = inp.st, r = [];
    const wt = (key, def) => (Number.isFinite(st[key]) ? st[key] : def);
    const wL = wt("nl_w_length", 0.3), wB = wt("nl_w_band", 0.1), wK = wt("nl_w_mileage", NL_W_KM);
    // inp.targetMask (24 weights, index j*4+k) drops all targets of a (mode, shock) for cross-validation:
    // tours, length, mileage and bands together, since mileage = tours x length
    const mk = (j, k) => (inp.targetMask ? inp.targetMask[j * K + k] : 1);
    for (let j = 0; j < M; j++) for (let k = 0; k < K; k++) {
      r.push(mk(j, k) * (f.trips[j][k] - inp.tgt[p][j][k]));
      r.push(mk(j, k) * wL * (f.len[j][k] - inp.avgl[p][j][k]));
      if (wK && Number.isFinite(inp.kmT[p][j][k])) r.push(mk(j, k) * wK * (f.km[j][k] - inp.kmT[p][j][k]));
    }
    bandT.forEach(t => { const v = f.band[t.j][t.b][t.k]; if (Number.isFinite(v)) r.push(mk(t.j, t.k) * wB * (v - t.value)); });
    r.push(st.sc_prior_weight * (logit(par.sC.sov) - logit(inp.priorSC[p].sov)));
    r.push(st.sc_prior_weight * (logit(par.sC.pt) - logit(inp.priorSC[p].pt)));
    r.push(0.05 * th[4], 0.05 * th[5]); // weak pull of phi toward log GT
    par.tilt.forEach((a, j) => { if (j !== REF) r.push(st.prior_weight * a); });
    return r;
  }
  function nlCalibratePurpose(inp, p, model) {
    const structure = (inp.nlStructure && inp.nlStructure[p]) || NL_STRUCTURE[p], bandT = nlBandTargets(inp, p);
    let best = null;
    [[-1, 0], [0, 0.5], [-0.5, 1]].forEach(([b0, ph0]) => {
      const th0 = [b0, b0, b0, b0, ph0, ph0, logit(inp.priorSC[p].sov), logit(inp.priorSC[p].pt), logit(0.75 / 0.95), 0, 0, 0, 0, 0, 0, 0];
      const res = lm(th => nlResiduals(inp, p, th, model, structure, bandT), th0, 150);
      if (!best || res.cost < best.cost) best = res;
    });
    const par = nlUnpack(best.th, model, structure), f = nlFitted(inp, p, par);
    const rm = (F, T) => { let se = 0, n = 0, mx = 0; for (let j = 0; j < M; j++) for (let k = 0; k < K; k++) if (Number.isFinite(T[j][k])) { const e = F[j][k] - T[j][k]; se += e * e; n++; mx = Math.max(mx, Math.abs(e)); } return { rmse: Math.sqrt(se / n), mx }; };
    const be = bandT.map(t => f.band[t.j][t.b][t.k] - t.value).filter(Number.isFinite);
    const shares = tilt => { const T = z6(); inp.nl.calCells[p].forEach(c => c.alt.j.forEach((j, a) => { T[j] += c.alt.t0[a] * Math.exp(tilt[j]); })); return T.map(v => v / sum(T)); };
    const tr = rm(f.trips, inp.tgt[p]);
    return { ...par, fitted: f.trips, fittedLen: f.len, fittedKm: f.km, fittedBand: f.band, rmse: tr.rmse, maxerr: tr.mx,
      rmseLen: rm(f.len, inp.avgl[p]).rmse, rmseKm: rm(f.km, inp.kmT[p]).rmse, rmseBand: Math.sqrt(sum(be.map(v => v * v)) / be.length),
      w: shares(par.tilt), prior_w: shares(z6()), prior_sC: inp.priorSC[p] };
  }
  const isNL = m => m === "nl" || m === "mnl";
  const FARE_TO_2025 = 1.0329;
  // Cost-sharing sensitivity lam scales what PASSENGERS pay; the driver pays the rest of the
  // vehicle cost: driver share = 1 - lam (1 - s0). lam = 1 gives the LTM shares, lam = 0 the
  // driver pays all, and the shares of one shared car still add up to its cost. (Before
  // 2026-11-28 both shares were multiplied by lam, so at lam = 0 nobody paid; Codex review #2.)
  const clamp01 = v => Math.min(1, Math.max(0, v));
  const shareScale = (cs0, lam) => ({ sov: 1, hov: clamp01(1 - lam * (1 - cs0.hov)), carp: clamp01(cs0.carp * lam) });
  function nlRun(inp, cal, x, lam) {
    const cells = [];
    PURPOSES.forEach(p => {
      // rebased: the 2023 TU shares replace the tilted calibration shares (as for the IPDL)
      const par = { ...cal.purposes[p], tilt: null }, cs = shareScale(inp.cs[p], lam);
      inp.nl.cells[p].forEach(c => {
        const r = nlCellResponse(par, c, x, cellScale(inp, p, c.quintile), cs, inp.st.s0, par.structure);
        const trips0 = r.T0.map(sum), trips1 = r.T1.map(sum), km0 = r.K0.map(sum), km1 = r.K1.map(sum);
        cells.push({ purpose: p, quintile: c.quintile, cars: c.cars, trips0, trips1, km0, km1,
          len: km0.map((k, j) => trips0[j] > 0 ? k / trips0[j] : 0), R: trips1.map((t, j) => trips0[j] > 0 ? t / trips0[j] : 1),
          L: km1.map((k, j) => trips1[j] > 0 && km0[j] > 0 ? (k / trips1[j]) / (km0[j] / trips0[j]) : 1),
          band: { T0: r.T0, T1: r.T1, K0: r.K0, K1: r.K1 } });
      });
    });
    return cells;
  }

  // ---------------------------------------------------------------- scenarios
  // Counterfactual mode/length probabilities for the SAME cell under another
  // ownership status. Fixed total tours here; the ownership module applies the
  // separate LTM frequency effect. LTM coefficients use the lower-nest scale.
  function ownershipConditional(inp, cal, cell, x, lam, modeShift) {
    if (!isNL(cal.model)) throw new Error("Ownership scenarios currently require NL or MNL");
    const p = cell.purpose, c = inp.nl.cells[p].find(r => r.quintile === cell.quintile && r.cars === cell.cars);
    const par = { ...cal.purposes[p], tilt: null };
    const cs = shareScale(inp.cs[p], lam);
    return nlCellResponse(par, c, x, cellScale(inp, p, c.quintile), cs, 0, par.structure, modeShift);
  }
  // odds scales for a cell: 2010-2023 update ratio and VoT relative to the average traveller
  function cellScale(inp, p, quintile) {
    const v = inp.vot[p], rel = inp.income[quintile] ? inp.income[quintile].rel : 1;
    const vr = v(inp.y2010) / v(inp.y2010 * rel);
    return { car: inp.rCar * vr, pt: inp.rPt * vr };
  }
  // xo: {CC, CT, PC, PT}; opts.costShareScale scales HOV/passenger cost shares (lambda sensitivity)
  function run(inp, cal, xo, opts = {}) {
    const x = SHOCKS.map(k => xo[k] || 0), lam = opts.costShareScale ?? 1, model = cal.model || "ipdl";
    if (isNL(model)) return { x, model, cells: nlRun(inp, cal, x, lam), warnings: shockWarnings(inp, x) };
    const cells = [];
    let failed = 0;
    PURPOSES.forEach(p => {
      const par = cal.purposes[p], cs = shareScale(inp.cs[p], lam);
      const L = pivot(logEl(inp.avgl[p], inp.st.x_ref), x);
      inp.cells[p].forEach(c => {
        const R = tripRatios(par, c.share, inp.st.s0, cs, x, cellScale(inp, p, c.quintile));
        if (!R.ok) failed++;
        cells.push({ purpose: p, quintile: c.quintile, cars: c.cars, trips0: c.base, km0: c.base.map((t, j) => t * c.len[j]),
          len: c.len, R, L, trips1: c.base.map((t, j) => t * R[j]), km1: c.base.map((t, j) => t * c.len[j] * R[j] * L[j]) });
      });
    });
    const warnings = shockWarnings(inp, x);
    if (failed) warnings.push(`IPDL share solver did not converge in ${failed} cells: results not reliable`);
    return { x, model, cells, warnings, failed };
  }
  function shockWarnings(inp, x) {
    return x.some(v => Math.abs(v) > inp.st.warn_shock + 1e-12)
      ? [`shock beyond +/-${Math.round(inp.st.warn_shock * 100)}%: curvature is the IPDL's, not pinned by LTM runs`] : [];
  }
  // aggregate run cells by keys (e.g. ["purpose"], ["quintile", "cars"], [])
  function aggregate(res, keys) {
    const groups = {};
    res.cells.forEach(c => {
      const k = keys.map(q => c[q]).join("|");
      const g = (groups[k] = groups[k] || { ...Object.fromEntries(keys.map(q => [q, c[q]])), trips0: z6(), trips1: z6(), km0: z6(), km1: z6() });
      for (let j = 0; j < M; j++) { g.trips0[j] += c.trips0[j]; g.trips1[j] += c.trips1[j]; g.km0[j] += c.km0[j]; g.km1[j] += c.km1[j]; }
    });
    return Object.values(groups).map(g => ({ ...g, ...indicators(g) }));
  }
  function indicators(g) {
    const car = [2, 3], drv = [2, 3, 4];
    const vkm0 = sum(car.map(j => g.km0[j])), vkm1 = sum(car.map(j => g.km1[j]));
    const pkmCar0 = sum(drv.map(j => g.km0[j])), pkmCar1 = sum(drv.map(j => g.km1[j]));
    return {
      dTrips: sum(g.trips1) / sum(g.trips0) - 1, dCarTrips: sum(car.map(j => g.trips1[j])) / sum(car.map(j => g.trips0[j])) - 1,
      dVkm: vkm1 / vkm0 - 1, dPtPkm: g.km1[5] / g.km0[5] - 1,
      occupancy0: pkmCar0 / vkm0, occupancy1: pkmCar1 / vkm1,
      byMode: MODES.map((m, j) => ({ mode: m, dTrips: g.trips1[j] / g.trips0[j] - 1, dKm: g.km1[j] / g.km0[j] - 1 })),
    };
  }
  // implied arc elasticities of the rebased 2023 model (aggregate over cells), per purpose
  function rebasedElasticities(inp, cal) {
    const out = {};
    PURPOSES.forEach(p => { out[p] = z64(); });
    SHOCKS.forEach((k, kk) => {
      const xo = { [k]: inp.st.x_ref }, res = run(inp, cal, xo);
      aggregate(res, ["purpose"]).forEach(g => {
        for (let j = 0; j < M; j++) out[g.purpose][j][kk] = (g.trips1[j] / g.trips0[j] - 1) / inp.st.x_ref;
      });
    });
    return out;
  }
  // log-linear pivot on the Rich (2022) targets, as a comparison
  function pivotRun(inp, xo) {
    const x = SHOCKS.map(k => xo[k] || 0);
    return Object.fromEntries(PURPOSES.map(p => [p, MODES.map((m, j) => ({
      mode: m, tripRatio: pivot(logEl(inp.tgt[p], inp.st.x_ref), x)[j], lenRatio: pivot(logEl(inp.avgl[p], inp.st.x_ref), x)[j] }))]));
  }

  // ---------------------------------------------------------------- bands (output only)
  // Split each purpose x mode result over tour-length bands. The log-response in band b is the
  // mode's total log-response times f_b = sum_k a_k e_bk / ebar_k over the active shocks k that have
  // a Rich (2022) band profile e_bk (ebar_k: trip-weighted mean), with weights a_k proportional to
  // |x_k ebar_k|. Band factors are then rescaled so that band totals add up to the engine's result.
  // Modes without an active profiled shock respond uniformly.
  function bands(inp, res) {
    if (isNL(res.model)) { // model output: sum the cells
      const acc = {};
      res.cells.forEach(c => MODES.forEach((m, j) => BANDS.forEach((b, i) => {
        const k = `${c.purpose}|${m}|${b}`, a = (acc[k] = acc[k] || { purpose: c.purpose, mode: m, band: b, trips0: 0, trips1: 0, km0: 0, km1: 0,
          extrapolatedFare: m === "pt" && i >= 3 });
        a.trips0 += c.band.T0[j][i]; a.trips1 += c.band.T1[j][i]; a.km0 += c.band.K0[j][i]; a.km1 += c.band.K1[j][i];
      })));
      return Object.values(acc).filter(a => a.trips0 > 0);
    }
    const agg = aggregate(res, ["purpose"]), out = [];
    agg.forEach(g => {
      const p = g.purpose;
      MODES.forEach((m, j) => {
        const base = inp.bandBase[p][m];
        if (!base) return;
        const T = BANDS.map(b => base[b].trips), Ttot = sum(T);
        if (Ttot <= 0) return;
        const terms = [];
        SHOCKS.forEach((k, kk) => {
          const prof = inp.bandE[p][`${m}|${k}`];
          if (!prof || res.x[kk] === 0) return;
          const e = BANDS.map(b => prof[b]), ebar = sum(e.map((v, i) => v * T[i])) / Ttot;
          if (Math.abs(ebar) < 1e-6) return;
          terms.push({ a: Math.abs(res.x[kk] * ebar), rel: e.map(v => v / ebar) });
        });
        const aTot = sum(terms.map(q => q.a));
        const f = BANDS.map((b, i) => terms.length ? sum(terms.map(q => q.a * q.rel[i])) / aTot : 1);
        const R = g.trips1[j] / g.trips0[j], LR = g.km1[j] / g.km0[j];
        const raw = f.map(fb => Math.exp(Math.log(R) * fb));
        const scaleT = R * Ttot / sum(raw.map((v, i) => v * T[i]));
        BANDS.forEach((b, i) => {
          const r = raw[i] * scaleT;
          out.push({ purpose: p, mode: m, band: b, trips0: T[i], trips1: T[i] * r, km0: base[b].km, km1: base[b].km * r * LR / R,
            extrapolatedFare: m === "pt" && ["100-200", "200-300", "300+"].includes(b) });
        });
      });
    });
    return out;
  }

  // ---------------------------------------------------------------- burden (money)
  // DKK per person (10-84) per year, by quintile x cars; time losses are not monetised here.
  // totalDKK: money part of the consumer-surplus change by the rule of half, price change x
  //   (base + scenario quantity) / 2. NOT a change in spending.
  // spendDKK: change in spending, new price x new quantity - old price x old quantity (Codex #1).
  function burden(inp, res, opts = {}) {
    const x = res.x, lam = opts.costShareScale ?? 1, days = inp.st.annual_days, disc = inp.st.commute_pass_discount;
    const acc = {};
    res.cells.forEach(c => {
      const key = `${c.quintile}|${c.cars}`, a = (acc[key] = acc[key] || { quintile: c.quintile, cars: c.cars, car: 0, pt: 0, carSpend: 0, ptSpend: 0 });
      const cs = inp.cs[c.purpose];
      const sh = shareScale(cs, lam);
      [[2, sh.sov], [3, sh.hov], [4, sh.carp]].forEach(([j, s]) => {
        a.car += inp.costs.carPerKm * s * x[0] * (c.km0[j] + c.km1[j]) / 2;
        a.carSpend += inp.costs.carPerKm * s * ((1 + x[0]) * c.km1[j] - c.km0[j]);
      });
      const paid = c.purpose === "commute" ? 1 - disc : 1;
      // fares are 2023 prices, car costs fixed 2025 prices (TOEE): put fares in 2025 prices (DST PRIS113,
      // CPI 2025/2023 = 121.07/117.21 = 1.0329). Money output only; the PT money-share prior is unchanged.
      const fare = (T, K) => FARE_TO_2025 * (2 * inp.costs.fareOffset * T + inp.costs.farePerKm * K);
      a.pt += paid * x[2] * fare((c.trips0[5] + c.trips1[5]) / 2, (c.km0[5] + c.km1[5]) / 2);
      a.ptSpend += paid * ((1 + x[2]) * fare(c.trips1[5], c.km1[5]) - fare(c.trips0[5], c.km0[5]));
    });
    return Object.values(acc).map(a => {
      const persons = inp.persons[`${a.quintile}|${a.cars}`] || NaN, inc = inp.income[a.quintile];
      const perPerson = (a.car + a.pt) * days / persons;
      const spend = (a.carSpend + a.ptSpend) * days / persons;
      return { quintile: a.quintile, cars: a.cars, persons, carDKK: a.car * days / persons, ptDKK: a.pt * days / persons,
        totalDKK: perPerson, shareOfPersonalIncome: inc ? perPerson / (inc.resp * 1000) : NaN,
        carSpendDKK: a.carSpend * days / persons, ptSpendDKK: a.ptSpend * days / persons, spendDKK: spend };
    }).sort((u, v) => u.quintile - v.quintile || String(u.cars).localeCompare(String(v.cars)));
  }

  const api = { MODES, SHOCKS, PURPOSES, BANDS, GROUPINGS, MODELS, VERSION, NL_STRUCTURE, setGroupings, nlFitted, validate, prepare, calibrate, calibratePurpose, fittedAggregate, run, aggregate,
    rebasedElasticities, pivotRun, bands, burden, tripRatios, moneyShares, cellScale, votSchedule, ownershipConditional };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.ElastEngine2 = api;
})(typeof window !== "undefined" ? window : globalThis);
