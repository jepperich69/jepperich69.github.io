/* Elbil-tælleren (EV fleet forecast). Reads data/forecast.json (written by src/export.py). */
"use strict";

const T = {
  da: {
    kicker: "Elbiler i den danske bilpark", beta: "BETA · v0.1", auto: "Opdateres automatisk hver måned, når Danmarks Statistik offentliggør nye tal.", updated: "Senest opdateret", title: "Elbil-tælleren", subtitle: "Månedlig prognose fra Danmarks Statistiks data",
    vintage: "Data til og med", bev_now: "Elbiler i bilparken nu", expected_1m: "1 million elbiler ventes",
    since: "siden", of_way: "af vejen til 1 million", left: "mangler", kpis: "Nøgletal", milestones: "Milepæle",
    ms_note: "Median og 90%-interval. Ændring mod sidste måneds prognose.",
    c1: "Bilparken efter drivmiddel", c1_note: "Faktisk bestand og prognosens median. Prognosen starter ved den lodrette linje.",
    c2: "Antal elbiler med usikkerhed", c2_note: "Median med 80%-interval. Stiplet linje: 1 million.",
    c3: "Elbilers andel af salget og af bilparken",
    c3_note: "Salget skifter hurtigt; bilparken følger efter, fordi biler holder 15–18 år. Faktisk salg vist som 12-måneders gennemsnit.",
    table: "Vis tal som tabel", how: "Sådan virker prognosen",
    how_text: "Bilparkens samlede størrelse følger antallet af voksne og en mætningskurve for biler pr. voksen. Nye biler fordeles på drivmidler med en S-kurve for elbilers andel af salget, med et loft omkring 97%. Benzin- og dieselbiler forsvinder hurtigere fra bilparken, efterhånden som der ikke kommer nye til, og de tilbageværende bliver ældre. Brugte elbiler importeres i forhold til salget af nye elbiler. Alle tal er medianer af 500 simulerede forløb.",
    source: "Kilde", local: "Lokal forhåndsvisning – ikke offentliggjort.",
    fuel: { BEV: "Elbiler", PHEV: "Plugin-hybrider", petrol: "Benzin", diesel: "Diesel" },
    k_sales_m: "Elbilers andel af salget i", k_fleet: "Elbilers andel af bilparken", k_petrol: "Benzinbiler", k_diesel: "Dieselbiler",
    ms: { bev_1m: "1 million elbiler", bev_above_petrol: "Flere elbiler end benzinbiler", bev_half_fleet: "Halvdelen af bilparken er elbiler",
          diesel_below_100k: "Under 100.000 dieselbiler", plugin_90pct_fleet: "90% af bilparken er elbiler eller plugin-hybrider" },
    p_by: "Sandsynlighed inden 2041", after: "efter", later: "senere", earlier: "tidligere", same: "uændret", months: "mdr.", month: "md.",
    vs_fc: "mod sidste prognose", no_prev: "første måned i arkivet", methods: "Metodenotat (PDF, engelsk)", forecast: "Prognose", actual: "Faktisk",
    share_sales: "Andel af salget", share_fleet: "Andel af bilparken",
    band80: "80%-interval", year: "1. januar", fc: "prognose", pp: "procentpoint", mio: "1 mio.",
    mon: ["jan.", "feb.", "mar.", "apr.", "maj", "jun.", "jul.", "aug.", "sep.", "okt.", "nov.", "dec."], lang: "English",
    f_title: "Statens afgifter og CO2", f_params: "Ret forudsætningerne", f_reset: "Nulstil",
    f_note: "Hvad staten ikke får i afgift, fordi elbiler erstatter benzinbiler, og hvor meget CO2 det sparer. Sammenligning: samme bilpark uden elbiler. Op til i dag med de faktiske elbiler; derefter et regneeksempel, hvor 2026-reglerne fastholdes.",
    f_caveat: "Budgetomkostningen pr. ton er en overførsel fra staten til bilejerne, ikke en samfundsøkonomisk omkostning. Afgiftsreglerne ændres løbende, så tallene efter i dag er et regneeksempel, ikke en prognose.",
    f_gap_y: "Afgift staten ikke fik i", f_gap_cum: "I alt", f_co2_y: "CO2 sparet i", f_kr_t: "Budgetomkostning pr. ton CO2",
    f_kr_t_note: "elbiler solgt i {y}, over 15 år", f_scn_y: "Regneeksempel {y}", f_scn_cum: "Regneeksempel i alt",
    f_scn_note: "hvis 2026-reglerne fastholdes", bn: "mia. kr.", mt: "mio. t", kt: "tusind t", kr: "kr.",
    f_reg: "Registreringsafgift", f_run: "Brændstof- og ejerafgift", f_obs: "faktisk", f_scn: "regneeksempel (2026-regler)",
    f_phys: "medregnet CO2 fra elnettet",
    p: { km: "Kørsel pr. bil (km/år)", km_per_l: "Benzinbil: km pr. liter", kwh_per_km: "Elbil: kWh pr. km",
         co2_per_l: "CO2 pr. liter benzin (kg)", fuel_tax_petrol: "Benzinafgift (kr./l ekskl. moms)",
         reg_ice: "Registreringsafgift, benzinbil (kr.)", reg_bev_obs: "Registreringsafgift, elbil til 2025 (kr.)",
         reg_bev_2026: "Registreringsafgift, elbil 2026 (kr.)", owner_ice: "Ejerafgift, benzinbil (kr./år)",
         owner_bev: "Ejerafgift, elbil (kr./år)", el_tax: "Elafgift ved opladning (kr./kWh)",
         grid_g_per_kWh: "CO2 i elnettet (g/kWh), regneeksempel", life: "Bilens levetid (år)" },
  },
  en: {
    kicker: "Electric cars in the Danish car fleet", beta: "BETA · v0.1", auto: "Updated automatically every month when Statistics Denmark publishes new figures.", updated: "Last updated", title: "EV Adaptation model Denmark", subtitle: "Monthly forecast from Statistics Denmark data",
    vintage: "Data up to", bev_now: "Electric cars in the fleet now", expected_1m: "1 million electric cars expected",
    since: "since", of_way: "of the way to 1 million", left: "to go", kpis: "Key figures", milestones: "Milestones",
    ms_note: "Median and 90% interval. Change against last month's forecast.",
    c1: "The car fleet by fuel", c1_note: "Actual stock and the forecast median. The forecast starts at the vertical line.",
    c2: "Number of electric cars, with uncertainty", c2_note: "Median with 80% interval. Dashed line: 1 million.",
    c3: "Electric cars' share of sales and of the fleet",
    c3_note: "Sales switch fast; the fleet follows because cars last 15-18 years. Actual sales shown as a 12-month average.",
    table: "Show numbers as a table", how: "How the forecast works",
    how_text: "The size of the fleet follows the number of adults and a saturation curve for cars per adult. New cars are split by fuel with an S-curve for the electric share of sales, with a ceiling near 97%. Petrol and diesel cars leave the fleet faster as no new ones are added and the remaining cars get older. Used electric cars are imported in proportion to new electric-car sales. All figures are medians of 500 simulated paths.",
    source: "Source", local: "Local preview, not published.",
    fuel: { BEV: "Electric", PHEV: "Plug-in hybrid", petrol: "Petrol", diesel: "Diesel" },
    k_sales_m: "Electric share of sales in", k_fleet: "Electric share of the fleet", k_petrol: "Petrol cars", k_diesel: "Diesel cars",
    ms: { bev_1m: "1 million electric cars", bev_above_petrol: "More electric than petrol cars", bev_half_fleet: "Half the fleet electric",
          diesel_below_100k: "Fewer than 100,000 diesel cars", plugin_90pct_fleet: "90% of the fleet electric or plug-in hybrid" },
    p_by: "Probability before 2041", after: "after", later: "later", earlier: "earlier", same: "unchanged", months: "months", month: "month",
    vs_fc: "vs last forecast", no_prev: "first month in the archive", methods: "Methods note (PDF)", forecast: "Forecast", actual: "Actual",
    share_sales: "Share of sales", share_fleet: "Share of the fleet",
    band80: "80% interval", year: "1 January", fc: "forecast", pp: "percentage points", mio: "1 million",
    mon: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], lang: "Dansk",
    f_title: "Tax revenue and CO2", f_params: "Change the assumptions", f_reset: "Reset",
    f_note: "The tax the state does not collect because electric cars replace petrol cars, and the CO2 this saves. Comparison: the same fleet without electric cars. Up to today with the actual electric cars; after that an illustration with the 2026 rules kept unchanged.",
    f_caveat: "The budget cost per tonne is a transfer from the state to car owners, not a social cost. Tax rules change often, so figures after today are an illustration, not a forecast.",
    f_gap_y: "Tax not collected in", f_gap_cum: "Total", f_co2_y: "CO2 saved in", f_kr_t: "Budget cost per tonne of CO2",
    f_kr_t_note: "electric cars sold in {y}, over 15 years", f_scn_y: "Illustration {y}", f_scn_cum: "Illustration, total",
    f_scn_note: "if the 2026 rules are kept", bn: "bn DKK", mt: "Mt", kt: "kt", kr: "DKK",
    f_reg: "Registration tax", f_run: "Fuel and ownership tax", f_obs: "actual", f_scn: "illustration (2026 rules)",
    f_phys: "counting CO2 from the grid",
    p: { km: "Driving per car (km/year)", km_per_l: "Petrol car: km per litre", kwh_per_km: "Electric car: kWh per km",
         co2_per_l: "CO2 per litre of petrol (kg)", fuel_tax_petrol: "Petrol tax (DKK/l excl. VAT)",
         reg_ice: "Registration tax, petrol car (DKK)", reg_bev_obs: "Registration tax, electric car to 2025 (DKK)",
         reg_bev_2026: "Registration tax, electric car 2026 (DKK)", owner_ice: "Ownership tax, petrol car (DKK/year)",
         owner_bev: "Ownership tax, electric car (DKK/year)", el_tax: "Electricity tax on charging (DKK/kWh)",
         grid_g_per_kWh: "Grid CO2 (g/kWh), illustration", life: "Car life (years)" },
  },
};
let lang = new URLSearchParams(location.search).get("lang") || localStorage.getItem("evlang") || "da";
if (!T[lang]) lang = "da";
let D = null;
const FUELS_STACK = ["BEV", "PHEV", "petrol", "diesel"];
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const loc = () => (lang === "da" ? "da-DK" : "en-GB");
const nf = () => new Intl.NumberFormat(loc());
const fmt = (x) => nf().format(Math.round(x));
const num = (x, d = 1) => x.toLocaleString(loc(), { maximumFractionDigits: d, minimumFractionDigits: d });
const pct = (x, d = 0) => num(100 * x, d) + "%";
const mlabel = (m) => { if (!m) return "–"; if (m.startsWith("after")) return `${T[lang].after} 2040`; const [y, mo] = m.split("-"); return `${T[lang].mon[+mo - 1]} ${y}`; };
const midx = (m) => +m.slice(0, 4) * 12 + (+m.slice(5, 7) - 1);

/* year-over-year change: arrow + sign + value, green up / red down, so colour is never alone */
function yoy(cur, prev, prevMonth, kind = "count") {
  const t = T[lang], d = cur - prev;
  const eps = kind === "share" ? 0.00005 : 0.5;
  const cls = Math.abs(d) < eps ? "flat" : d > 0 ? "up" : "down";
  const arrow = cls === "up" ? "▲" : cls === "down" ? "▼" : "●";
  const sign = d > 0 ? "+" : d < 0 ? "−" : "±";
  const val = kind === "share" ? `${num(Math.abs(100 * d))} ${t.pp}` : fmt(Math.abs(d));
  const was = kind === "share" ? pct(prev, 1) : fmt(prev);
  return `<span class="delta ${cls}">${arrow} ${sign}${val}</span> <span class="muted">${t.since} ${mlabel(prevMonth)} (${was})</span>`;
}
/* milestone dates: change in months vs last month's forecast (neutral colour) */
function mdelta(cur, prev) {
  const t = T[lang];
  if (!prev) return `<span class="delta flat">${t.no_prev}</span>`;
  if (!prev.median && !cur.median) return `<span class="delta flat">● ${t.same}</span> ${t.vs_fc}`;
  if (!prev.median || !cur.median) return "";
  if (cur.median.startsWith("after") || prev.median.startsWith("after")) return cur.median === prev.median ? `<span class="delta flat">● ${t.same}</span> ${t.vs_fc}` : "";
  const d = midx(cur.median) - midx(prev.median);
  if (d === 0) return `<span class="delta flat">● ${t.same}</span> ${t.vs_fc}`;
  const n = Math.abs(d), unit = n === 1 ? t.month : t.months;
  return `<span class="delta flat">${d > 0 ? "▶" : "◀"} ${n} ${unit} ${d > 0 ? t.later : t.earlier}</span> ${t.vs_fc}`;
}
/* sparkline of the last n observed months; the dot marks the latest value */
function spark(arr, color) {
  const w = 200, h = 34, lo = Math.min(...arr), hi = Math.max(...arr), r = hi - lo || 1;
  const pts = arr.map((v, i) => [i / (arr.length - 1) * (w - 6) + 3, h - 4 - (v - lo) / r * (h - 8)]);
  const last = pts[pts.length - 1];
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">
    <path d="${pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join("")}" fill="none" stroke="${color}" stroke-width="2" vector-effect="non-scaling-stroke"/>
    <circle cx="${last[0]}" cy="${last[1]}" r="3" fill="${color}"/></svg>`;
}

function render() {
  const t = T[lang], o = D.observed, h = D.headline;
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => { const k = el.dataset.i18n; if (typeof t[k] === "string") el.textContent = t[k]; });
  document.getElementById("lang").textContent = t.lang;
  document.title = `${t.title} ${t.beta} – ${t.kicker.toLowerCase()}`;
  document.getElementById("vintage").textContent = mlabel(D.vintage);
  document.getElementById("source").textContent = D.source;
  const gd = new Date(D.generated);
  document.getElementById("updated").textContent = gd.toLocaleDateString(loc(), { day: "numeric", month: "long", year: "numeric" });
  document.getElementById("cyear").textContent = gd.getFullYear();

  const n = o.months.length, i = n - 1, j = n - 13, pm = o.months[j];
  const tot = (k) => FUELS_STACK.reduce((a, f) => a + o[f][k], 0) + o.other[k];
  const fleetShare = (k) => o.BEV[k] / tot(k), salesShare = (k) => o.sales_BEV[k] / o.sales_total[k];

  document.getElementById("bev-now").textContent = fmt(o.BEV[i]);
  document.getElementById("bev-delta").innerHTML = yoy(o.BEV[i], o.BEV[j], pm);
  const m1 = D.milestones.bev_1m;
  document.getElementById("m1m").textContent = mlabel(m1.median);
  document.getElementById("m1m-band").textContent = `${mlabel(m1.q05)} – ${mlabel(m1.q95)}`;
  const share1m = Math.min(o.BEV[i] / 1e6, 1);
  document.getElementById("progress-fill").style.width = (100 * share1m).toFixed(1) + "%";
  document.getElementById("progress-pct").textContent = `${pct(share1m)} ${t.of_way}`;
  document.getElementById("progress-left").textContent = `${fmt(h.to_1m)} ${t.left}`;
  document.getElementById("progress-aria").setAttribute("aria-label", `${pct(share1m)} ${t.of_way}`);

  const last = (f, k = 25) => Array.from({ length: k }, (_, q) => f(n - k + q));
  const kp = [
    [`${t.k_sales_m} ${mlabel(o.months[i])}`, pct(salesShare(i)), yoy(salesShare(i), salesShare(j), pm, "share"), last(salesShare), css("--salesshare")],
    [t.k_fleet, pct(fleetShare(i), 1), yoy(fleetShare(i), fleetShare(j), pm, "share"), last(fleetShare), css("--BEV")],
    [t.k_petrol, fmt(o.petrol[i]), yoy(o.petrol[i], o.petrol[j], pm), last((k) => o.petrol[k]), css("--petrol")],
    [t.k_diesel, fmt(o.diesel[i]), yoy(o.diesel[i], o.diesel[j], pm), last((k) => o.diesel[k]), css("--diesel")],
  ];
  document.getElementById("kpis").innerHTML = kp.map(([l, v, d, s, c]) =>
    `<div class="kpi" style="--c:${c}"><p class="label">${l}</p><p class="v">${v}</p>${spark(s, c)}<p class="muted">${d}</p></div>`).join("");

  const pmil = D.previous ? D.previous.milestones : {};
  const mcol = { bev_1m: "--BEV", bev_above_petrol: "--petrol", bev_half_fleet: "--BEV", diesel_below_100k: "--diesel", plugin_90pct_fleet: "--PHEV" };
  document.getElementById("milestones").innerHTML = Object.entries(D.milestones).map(([k, v]) => {
    const band = v.q05 ? `${mlabel(v.q05)} – ${mlabel(v.q95)}` : "";
    return `<div class="tile" style="--c:${css(mcol[k] || "--BEV")}"><p class="label">${t.ms[k] || k}</p><p class="v">${v.median ? mlabel(v.median) : `${t.after} 2040`}</p>
      <p class="muted">${band}</p><p class="muted">${t.p_by}: ${pct(v.p_by_horizon)}</p><p class="muted">${mdelta(v, pmil[k])}</p></div>`;
  }).join("");

  chartStack(); chartBEV(); chartShares(); table(); fiscal();
}

/* ---------- SVG helpers ---------- */
const W = 1000, H = 360, M = { l: 70, r: 20, t: 12, b: 34 };
function scales(x0, x1, y0, y1) {
  const sx = (x) => M.l + (x - x0) / (x1 - x0) * (W - M.l - M.r);
  const sy = (y) => H - M.b - (y - y0) / (y1 - y0) * (H - M.t - M.b);
  return { sx, sy, inv: (px) => x0 + (px - M.l) / (W - M.l - M.r) * (x1 - x0) };
}
function axes(s, x0, x1, yTicks, yfmt) {
  let g = `<g class="grid">`;
  yTicks.forEach((y) => { g += `<line x1="${M.l}" x2="${W - M.r}" y1="${s.sy(y)}" y2="${s.sy(y)}"/>`; });
  g += `</g><g class="axis">`;
  yTicks.forEach((y) => { g += `<text x="${M.l - 8}" y="${s.sy(y) + 4}" text-anchor="end">${yfmt(y)}</text>`; });
  for (let yr = Math.ceil(x0 / 12 / 4) * 4; yr * 12 <= x1; yr += 4) {
    const x = s.sx(yr * 12);
    g += `<line x1="${x}" x2="${x}" y1="${H - M.b}" y2="${H - M.b + 5}"/><text x="${x}" y="${H - M.b + 20}" text-anchor="middle">${yr}</text>`;
  }
  g += `<line x1="${M.l}" x2="${W - M.r}" y1="${H - M.b}" y2="${H - M.b}"/></g>`;
  return g;
}
const path = (pts) => pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join("");
function niceTicks(max, n = 5) {
  const raw = max / n, mag = 10 ** Math.floor(Math.log10(raw)), step = [1, 2, 2.5, 5, 10].map((k) => k * mag).find((s) => s >= raw);
  const out = []; for (let v = 0; v <= max + 1e-9; v += step) out.push(v); return out;
}
function legend(id, items) {
  document.getElementById(id).innerHTML = items.map(([c, l]) => `<span style="--c:${c}">${l}</span>`).join("");
}
/* crosshair + tooltip; rows(i) returns [[colour, label, value], ...] for month index i */
function hover(el, s, months, rows) {
  const svg = el.querySelector("svg"), cross = svg.querySelector(".cross"), tip = document.getElementById("tip");
  const move = (ev) => {
    const r = svg.getBoundingClientRect(), px = (ev.clientX - r.left) / r.width * W;
    const mi = Math.round(s.inv(px)), first = midx(months[0]);
    const i = Math.max(0, Math.min(months.length - 1, mi - first));
    const x = s.sx(first + i);
    cross.setAttribute("x1", x); cross.setAttribute("x2", x); cross.style.display = "";
    tip.innerHTML = `<strong>${mlabel(months[i])}</strong>` + rows(i).map(([c, l, v]) =>
      `<div><span class="sw" style="background:${c}"></span>${l}: ${v}</div>`).join("");
    tip.hidden = false;
    const tx = Math.min(ev.clientX + 14, window.innerWidth - tip.offsetWidth - 8);
    tip.style.left = tx + "px"; tip.style.top = (ev.clientY + 14) + "px";
  };
  svg.addEventListener("pointermove", move);
  svg.addEventListener("pointerleave", () => { tip.hidden = true; cross.style.display = "none"; });
}
function series() {
  const o = D.observed, f = D.forecast;
  const months = o.months.concat(f.months);
  const val = (fu, q = "q50") => o[fu].concat(f[fu][q]);
  return { months, nObs: o.months.length, val };
}

/* ---------- charts ---------- */
function chartStack() {
  const t = T[lang], { months, nObs, val } = series();
  const x0 = midx(months[0]), x1 = midx(months[months.length - 1]);
  const v = Object.fromEntries(FUELS_STACK.map((f) => [f, val(f)]));
  const cum = months.map((_, i) => { let c = 0; return FUELS_STACK.map((f) => (c += v[f][i])); });
  const ymax = Math.max(...cum.map((c) => c[c.length - 1])) * 1.05;
  const s = scales(x0, x1, 0, ymax), ticks = niceTicks(ymax);
  let g = axes(s, x0, x1, ticks, (y) => (y / 1e6).toLocaleString(lang === "da" ? "da-DK" : "en-GB") + (lang === "da" ? " mio." : "M"));
  FUELS_STACK.forEach((f, k) => {
    const top = months.map((m, i) => [s.sx(midx(m)), s.sy(cum[i][k])]);
    const bot = months.map((m, i) => [s.sx(midx(m)), s.sy(k ? cum[i][k - 1] : 0)]).reverse();
    g += `<path d="${path(top.concat(bot))}Z" fill="${css("--" + f)}" stroke="${css("--surface")}" stroke-width="2"/>`;
  });
  const xf = s.sx(midx(months[nObs - 1]));
  g += `<line x1="${xf}" x2="${xf}" y1="${M.t}" y2="${H - M.b}" stroke="${css("--ink")}" stroke-dasharray="4 4"/>
        <text x="${xf + 6}" y="${M.t + 14}" style="fill:${css("--ink")}">${t.forecast} →</text>
        <line class="cross" y1="${M.t}" y2="${H - M.b}" stroke="${css("--ink")}" style="display:none"/>`;
  const el = document.getElementById("chart1");
  el.innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${t.c1}">${g}</svg>`;
  legend("legend1", FUELS_STACK.map((f) => [css("--" + f), t.fuel[f]]));
  hover(el, s, months, (i) => FUELS_STACK.slice().reverse().map((f) => [css("--" + f), t.fuel[f], fmt(v[f][i])]).concat(
    [["transparent", i >= nObs ? t.forecast : t.actual, ""]]));
}

function chartBEV() {
  const t = T[lang], o = D.observed, f = D.forecast, { months, nObs } = series();
  const start = months.indexOf("2018-01"), ms = months.slice(start);
  const x0 = midx(ms[0]), x1 = midx(ms[ms.length - 1]);
  const ymax = Math.max(...f.BEV.q90) * 1.05, s = scales(x0, x1, 0, ymax);
  let g = axes(s, x0, x1, niceTicks(ymax), (y) => (y / 1e6).toLocaleString(lang === "da" ? "da-DK" : "en-GB") + (lang === "da" ? " mio." : "M"));
  const fx = f.months.map((m) => s.sx(midx(m)));
  const lastObs = [s.sx(midx(o.months[nObs - 1])), s.sy(o.BEV[nObs - 1])];
  const up = [lastObs].concat(fx.map((x, i) => [x, s.sy(f.BEV.q90[i])]));
  const lo = [lastObs].concat(fx.map((x, i) => [x, s.sy(f.BEV.q10[i])])).reverse();
  g += `<path d="${path(up.concat(lo))}Z" fill="${css("--fan")}" stroke="none"/>`;
  g += `<line x1="${M.l}" x2="${W - M.r}" y1="${s.sy(1e6)}" y2="${s.sy(1e6)}" stroke="${css("--muted")}" stroke-dasharray="6 5"/>
        <text x="${M.l + 6}" y="${s.sy(1e6) - 6}">${t.mio}</text>`;
  const obsPts = o.months.slice(start).map((m, i) => [s.sx(midx(m)), s.sy(o.BEV[start + i])]);
  g += `<path d="${path(obsPts)}" fill="none" stroke="${css("--BEV")}" stroke-width="2.5"/>`;
  g += `<path d="${path([lastObs].concat(fx.map((x, i) => [x, s.sy(f.BEV.q50[i])])))}" fill="none" stroke="${css("--BEV")}" stroke-width="2" stroke-dasharray="7 4"/>`;
  g += `<line class="cross" y1="${M.t}" y2="${H - M.b}" stroke="${css("--ink")}" style="display:none"/>`;
  const el = document.getElementById("chart2");
  el.innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${t.c2}">${g}</svg>`;
  hover(el, s, ms, (i) => {
    const j = start + i;
    if (j < nObs) return [[css("--BEV"), t.actual, fmt(o.BEV[j])]];
    const k = j - nObs;
    return [[css("--BEV"), t.forecast, fmt(f.BEV.q50[k])], [css("--fan"), t.band80, `${fmt(f.BEV.q10[k])} – ${fmt(f.BEV.q90[k])}`]];
  });
}

function chartShares() {
  const t = T[lang], o = D.observed, f = D.forecast, { months, nObs } = series();
  const start = months.indexOf("2016-01"), ms = months.slice(start);
  const x0 = midx(ms[0]), x1 = midx(ms[ms.length - 1]), s = scales(x0, x1, 0, 1);
  let g = axes(s, x0, x1, [0, .25, .5, .75, 1], (y) => pct(y));
  const tot = o.months.map((_, i) => FUELS_STACK.reduce((a, fu) => a + o[fu][i], 0) + o.other[i]);
  const fleetObs = o.BEV.map((b, i) => b / tot[i]);
  const roll = o.sales_BEV.map((_, i) => { const a = Math.max(0, i - 11); let b = 0, n = 0;
    for (let k = a; k <= i; k++) { b += o.sales_BEV[k]; n += o.sales_total[k]; } return b / n; });   // display only
  const line = (arr, c, w, dash = "") => `<path d="${path(arr)}" fill="none" stroke="${c}" stroke-width="${w}" ${dash ? `stroke-dasharray="${dash}"` : ""}/>`;
  const fx = f.months.map((m) => s.sx(midx(m)));
  const band = (q, c) => {
    const up = fx.map((x, i) => [x, s.sy(q.q90[i])]), lo = fx.map((x, i) => [x, s.sy(q.q10[i])]).reverse();
    return `<path d="${path(up.concat(lo))}Z" fill="${c}" opacity=".18"/>`;
  };
  const sSales = css("--salesshare"), sFleet = css("--fleetshare");
  // forecast sales share: 12-month rolling of the median for comparability with the observed line
  g += band(f.bev_sales_share, sSales) + band(f.bev_fleet_share, sFleet);
  const obsX = o.months.slice(start).map((m) => s.sx(midx(m)));
  g += line(obsX.map((x, i) => [x, s.sy(roll[start + i])]), sSales, 2.5);
  g += line(obsX.map((x, i) => [x, s.sy(fleetObs[start + i])]), sFleet, 2.5);
  g += line(fx.map((x, i) => [x, s.sy(f.bev_sales_share.q50[i])]), sSales, 2, "7 4");
  g += line(fx.map((x, i) => [x, s.sy(f.bev_fleet_share.q50[i])]), sFleet, 2, "7 4");
  g += `<line class="cross" y1="${M.t}" y2="${H - M.b}" stroke="${css("--ink")}" style="display:none"/>`;
  const el = document.getElementById("chart3");
  el.innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${t.c3}">${g}</svg>`;
  legend("legend3", [[sSales, t.share_sales], [sFleet, t.share_fleet]]);
  hover(el, s, ms, (i) => {
    const j = start + i;
    if (j < nObs) return [[sSales, t.share_sales, pct(roll[j], 1)], [sFleet, t.share_fleet, pct(fleetObs[j], 1)]];
    const k = j - nObs;
    return [[sSales, `${t.share_sales} (${t.fc})`, pct(f.bev_sales_share.q50[k], 1)], [sFleet, `${t.share_fleet} (${t.fc})`, pct(f.bev_fleet_share.q50[k], 1)]];
  });
}

function table() {
  const t = T[lang], { months, nObs, val } = series();
  const v = Object.fromEntries(FUELS_STACK.map((f) => [f, val(f)]));
  // stock on 1 January = end of December of the year before
  const rows = months.map((m, i) => [m, i]).filter(([m]) => m.endsWith("-12"));
  document.getElementById("table").innerHTML = `<table><thead><tr><th>${t.year}</th>${FUELS_STACK.map((f) => `<th>${t.fuel[f]}</th>`).join("")}</tr></thead><tbody>` +
    rows.map(([m, i]) => `<tr><td>${+m.slice(0, 4) + 1}${i >= nObs ? ` (${t.fc})` : ""}</td>${FUELS_STACK.map((f) => `<td>${fmt(v[f][i])}</td>`).join("")}</tr>`).join("") +
    `</tbody></table>`;
}


/* ---------- tax revenue and CO2 (mirrors src/fiscal.py) ---------- */
const PKEYS = ["km", "km_per_l", "kwh_per_km", "co2_per_l", "fuel_tax_petrol", "reg_ice", "reg_bev_obs",
  "reg_bev_2026", "owner_ice", "owner_bev", "el_tax", "grid_g_per_kWh", "life"];
let FP = null;   // current parameters (defaults overridden by the form)

function perBev(p, regBev, g) {
  const litres = p.km / p.km_per_l, kwh = p.km * p.kwh_per_km;
  const fuel = litres * p.fuel_tax_petrol, owner = p.owner_ice - p.owner_bev, el = kwh * p.el_tax;
  const tail = litres * p.co2_per_l / 1000;
  return { reg: p.reg_ice - regBev, run: fuel + owner - el, co2n: tail, co2p: tail - kwh * g / 1e6 };
}
const quant = (arr, q) => { const s = arr.slice().sort((a, b) => a - b), k = (s.length - 1) * q, f = Math.floor(k);
  return s[f] + (s[Math.min(f + 1, s.length - 1)] - s[f]) * (k - f); };

function fiscalCompute(p) {
  const F = D.fiscal, ob = F.observed, sc = F.scenario;
  const obs = ob.years.map((y, k) => {
    const g = ob.grid[k] ?? p.grid_g_per_kWh ?? 0, e = perBev(p, y < (F.rule_year || 2026) ? p.reg_bev_obs : p.reg_bev_2026, g);
    return { y, reg: ob.sales[k] * e.reg / 1e9, run: ob.stock[k] * e.run / 1e9,
             co2n: ob.stock[k] * e.co2n / 1e6, co2p: ob.stock[k] * e.co2p / 1e6, e };
  });
  const es = perBev(p, p.reg_bev_2026, p.grid_g_per_kWh ?? 0);
  const nd = sc.sales[0].length, cum = new Array(nd).fill(0);
  const scn = sc.years.map((y, k) => {
    const gap = sc.sales[k].map((s, d) => s * es.reg / 1e9 + sc.stock[k][d] * es.run / 1e9);
    gap.forEach((v, d) => { cum[d] += v; });
    const med = (a) => quant(a, 0.5);
    return { y, q05: quant(gap, .05), q50: med(gap), q95: quant(gap, .95), cum50: med(cum), cum05: quant(cum, .05), cum95: quant(cum, .95),
             reg: med(sc.sales[k]) * es.reg / 1e9, run: med(sc.stock[k]) * es.run / 1e9 };
  });
  return { obs, scn };
}

function fiscal() {
  const F = D.fiscal, sec = document.getElementById("fiscal");
  if (!F) { sec.hidden = true; return; }
  sec.hidden = false;
  if (!FP) FP = Object.fromEntries(PKEYS.map((k) => [k, F.defaults[k]]));
  const t = T[lang];
  const form = document.getElementById("fparams");
  if (form.dataset.lang !== lang) {
    form.innerHTML = PKEYS.map((k) => `<label title="${(F.sources[k] || "").replace(/"/g, "'")}">${t.p[k]}
      <input type="number" name="${k}" step="any" value="${FP[k] ?? ""}"></label>`).join("");
    form.dataset.lang = lang;
  }
  const r = fiscalCompute(FP), last = r.obs[r.obs.length - 1], y0 = r.obs[0].y;
  const cumObs = r.obs.reduce((a, x) => a + x.reg + x.run, 0);
  const L = FP.life, e = last.e;
  const krt = (e.reg + L * e.run) / (L * e.co2n), krtP = (e.reg + L * e.run) / (L * e.co2p);
  const s30 = r.scn.find((x) => x.y === 2030) || r.scn[0], sEnd = r.scn[r.scn.length - 1];
  const bn = (x) => `${num(x)} ${t.bn}`;
  const tiles = [
    [`${t.f_gap_y} ${last.y}`, bn(last.reg + last.run), `${t.f_reg} ${num(last.reg)} · ${t.f_run} ${num(last.run)}`],
    [`${t.f_gap_cum} ${y0}–${last.y}`, bn(cumObs), ""],
    [`${t.f_co2_y} ${last.y}`, `${fmt(1000 * last.co2n)} ${t.kt}`, `${fmt(1000 * last.co2p)} ${t.kt} ${t.f_phys}`],
    [t.f_kr_t, `${fmt(krt)} ${t.kr}`, `${t.f_kr_t_note.replace("{y}", last.y)}; ${fmt(krtP)} ${t.kr} ${t.f_phys}`],
  ];
  const stiles = [
    [t.f_scn_y.replace("{y}", s30.y), bn(s30.q50), `${num(s30.q05)}–${num(s30.q95)} · ${t.f_scn_note}`],
    [`${t.f_scn_cum} ${r.scn[0].y}–${sEnd.y}`, bn(sEnd.cum50), `${fmt(sEnd.cum05)}–${fmt(sEnd.cum95)} · ${t.f_scn_note}`],
  ];
  const stale = F.stale_from ? `<p class="muted">⚠ ${lang === "da" ? "Afgiftsberegningen kunne ikke opdateres; tallene er fra" : "The tax calculation could not be updated; figures are from"} ${mlabel(F.stale_from)}.</p>` : "";
  document.getElementById("ftiles").innerHTML = stale +
    tiles.map(([l, v, s]) => `<div class="ftile"><p class="label">${l}</p><p class="v">${v}</p><p class="muted">${s}</p></div>`).join("") +
    stiles.map(([l, v, s]) => `<div class="ftile scn"><p class="label">${l}</p><p class="v">${v}</p><p class="muted">${s}</p></div>`).join("");
  chartFiscal(r);
}

function chartFiscal(r) {
  const t = T[lang], cR = css("--tax-reg"), cU = css("--tax-run");
  const all = r.obs.map((x) => ({ y: x.y, reg: x.reg, run: x.run, obs: true }))
    .concat(r.scn.map((x) => ({ y: x.y, reg: x.reg, run: x.run, lo: x.q05, hi: x.q95, obs: false })));
  const ymax = Math.max(...all.map((x) => Math.max(x.reg + x.run, x.hi || 0))) * 1.08;
  const x0 = all[0].y - 0.6, x1 = all[all.length - 1].y + 0.6;
  const sx = (x) => M.l + (x - x0) / (x1 - x0) * (W - M.l - M.r);
  const sy = (y) => H - M.b - y / ymax * (H - M.t - M.b);
  const bw = (sx(1) - sx(0)) * 0.7;
  let g = `<g class="grid">` + niceTicks(ymax).map((v) => `<line x1="${M.l}" x2="${W - M.r}" y1="${sy(v)}" y2="${sy(v)}"/>`).join("") + `</g><g class="axis">`;
  g += niceTicks(ymax).map((v) => `<text x="${M.l - 8}" y="${sy(v) + 4}" text-anchor="end">${num(v, 0)}</text>`).join("");
  all.forEach((d) => { if (d.y % 5 === 0) g += `<text x="${sx(d.y)}" y="${H - M.b + 20}" text-anchor="middle">${d.y}</text>`; });
  g += `<line x1="${M.l}" x2="${W - M.r}" y1="${H - M.b}" y2="${H - M.b}"/></g>`;
  g += `<text x="${M.l}" y="${M.t - 2}" style="font-size:12px">${t.bn}</text>`;
  all.forEach((d, k) => {
    const op = d.obs ? 1 : 0.45, x = sx(d.y) - bw / 2;
    const yR = sy(d.reg), yT = sy(d.reg + d.run);
    g += `<g class="fb" data-k="${k}" opacity="${op}">
      <rect x="${x}" y="${yR}" width="${bw}" height="${H - M.b - yR}" fill="${cR}" rx="2"/>
      <rect x="${x}" y="${yT}" width="${bw}" height="${Math.max(yR - yT - 1.5, 0)}" fill="${cU}" rx="2"/></g>`;
    if (!d.obs) g += `<line x1="${sx(d.y)}" x2="${sx(d.y)}" y1="${sy(d.lo)}" y2="${sy(d.hi)}" stroke="${css("--ink")}" stroke-width="1.2" opacity=".6"/>`;
  });
  const xs = (sx(r.obs[r.obs.length - 1].y) + sx(r.scn[0].y)) / 2;
  g += `<line x1="${xs}" x2="${xs}" y1="${M.t}" y2="${H - M.b}" stroke="${css("--ink")}" stroke-dasharray="4 4"/>
        <text x="${xs + 6}" y="${M.t + 14}" style="fill:${css("--ink")}">${t.f_scn} →</text>`;
  const el = document.getElementById("chartF");
  el.innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${t.f_title}">${g}</svg>`;
  legend("legendF", [[cR, t.f_reg], [cU, t.f_run]]);
  const tip = document.getElementById("tip");
  el.querySelectorAll(".fb").forEach((b) => {
    b.addEventListener("pointermove", (ev) => {
      const d = all[+b.dataset.k];
      tip.innerHTML = `<strong>${d.y}</strong> (${d.obs ? t.f_obs : t.f_scn})` +
        `<div><span class="sw" style="background:${cR}"></span>${t.f_reg}: ${num(d.reg)} ${t.bn}</div>` +
        `<div><span class="sw" style="background:${cU}"></span>${t.f_run}: ${num(d.run)} ${t.bn}</div>` +
        (d.obs ? "" : `<div>90%: ${num(d.lo)}–${num(d.hi)} ${t.bn}</div>`);
      tip.hidden = false;
      tip.style.left = Math.min(ev.clientX + 14, window.innerWidth - tip.offsetWidth - 8) + "px"; tip.style.top = (ev.clientY + 14) + "px";
    });
    b.addEventListener("pointerleave", () => { tip.hidden = true; });
  });
}

document.getElementById("fparams").addEventListener("input", (ev) => {
  const k = ev.target.name, v = parseFloat(ev.target.value);
  if (k && Number.isFinite(v) && v >= 0 && !(k === "km_per_l" && v === 0) && !(k === "life" && v === 0)) { FP[k] = v; fiscal(); }
});
document.getElementById("freset").addEventListener("click", () => {
  FP = null; document.getElementById("fparams").dataset.lang = ""; fiscal();
});
document.getElementById("lang").addEventListener("click", () => { lang = lang === "da" ? "en" : "da"; localStorage.setItem("evlang", lang); render(); });
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => D && render());
fetch("data/forecast.json", { cache: "no-store" }).then((r) => r.json()).then((d) => { D = d; render(); })
  .catch((e) => { document.querySelector("main").innerHTML = `<p>Could not load data/forecast.json: ${e}</p>`; });
