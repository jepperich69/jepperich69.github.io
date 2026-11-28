# Math check report: ev_fleet_methods

- Source: `Methods/ev_fleet_methods.tex` (EVadaptation project)
- Timestamp: 2026-11-28_12-18-02
- **138 checked: 136 passed, 2 failed, 0 errored; 19 not-checkable**

## Results

Label | Type | Result | What was checked | Got vs stated
---|---|---|---|---
eq:exits-solve-stock | SOLVE | PASS | solve(E = Xprev + R - X, X) vs Xprev + R - E | -E + R + X_prev vs -E + R + X_prev
sales-identity (Sec.3.1 total exit rate, 4 fuels) | IDENTITY | PASS | sum_f R_f - [(sum X_f - sum Xprev_f) + sum E_f] with E_f from eq:exits, f=1..4 | 0 vs 0
residual-rule BEV=total-others | IDENTITY | PASS | X_bev(update with E_bev=E_tot - sum E_other) - (X_tot - sum X_other) | 0 vs 0
floor-imports-effect | IDENTITY | PASS | d/dI[max(0,A+I)-I]: branch A+I>0 and branch A+I<=0 | 0 and -1 vs 0 (floor slack), nonzero (floor binds)
eq:gompertz-log-split | IDENTITY | PASS | log(S exp(-b e^{-rt})) - (log S - b e^{-rt}) | 0 vs 0
eq:gompertz-start-level | IDENTITY | PASS | S*exp(-b e^{-r*0}) with b=log(S/c0) equals c0 | c0 vs c0
eq:gompertz-ceiling | IDENTITY | PASS | lim_{t->oo} S exp(-b e^{-rt}) = S (saturation level) | S vs S
eq:share-ceiling | IDENTITY | PASS | lim_{t->oo} cbar/(1+e^{-k(t-t0)}) = cbar | cbar vs cbar
eq:share-midpoint | IDENTITY | PASS | curve at t=t0 equals cbar/2 | cbar/2 vs cbar/2
eq:share-monotone | IDENTITY | PASS | d/dt curve = cbar k e^{-k(t-t0)}/(1+e^{-k(t-t0)})^2 > 0 (positive for k,cbar>0) | 2*cosh(k*(t - t0)/2)**2/(cosh(k*(t - t0)) + 1) vs 1
remainder-shrinks-to-1-cbar | IDENTITY | PASS | lim 1 - s_t = 1 - cbar (Remaining fuels) | 1 - cbar vs 1 - cbar
eq:share-obs-variance | MOMENT | PASS | delta-method Var(logit phat)=1/(n p(1-p)) vs 1/n_BEV+1/n_other | 0 vs 0
eq:rate-start | IDENTITY | PASS | r at y_t=y_0 equals r0+delta ('starts at observed rate') | 0 vs 0
eq:rate-max-rise | IDENTITY | PASS | r(y=0)-r(y=y0) = alpha*y0 and dr/dy = -alpha<=0 so rise bounded by alpha*y0 | alpha*y0; dr/dy=-alpha vs alpha*y0
eq:rateshare-start | IDENTITY | PASS | share-link rate at sbar_t=sbar_0 equals r0+delta | 0 vs 0
eq:imports-lognormal | MOMENT | PASS | LogNormal(mu=log(m^2/sqrt(m^2+s^2)), sigma^2=log(1+s^2/m^2): mean=m, sd=s; sympy.stats at m=0.68,s=0.13 | mean=0.680000, sd=0.130000 vs mean 0.68, sd 0.13
prior-S-center | NUMERIC | PASS | mean(Sweden .60, NL .64, Norway .65, Germany .71) | mean=0.6500 (sample sd 0.0455; prior sd stated 0.04) vs 0.65
rMax-diesel | NUMERIC | PASS | 100*(r0+alpha*y0) with unrounded json r0,a,y0 (diesel); also from rounded macros = 13.490 | 13.5256 -> 13.5 vs 13.5
rMax-petrol | NUMERIC | PASS | 100*(r0+alpha*y0) with unrounded json r0,a,y0 (petrol); also from rounded macros = 8.150 | 8.1500 -> 8.2 vs 8.2
macro:Smed | NUMERIC | PASS | round(json value*1.0, 2) | 0.67622 -> 0.68 vs 0.68
macro:Slo | NUMERIC | PASS | round(json value*1.0, 2) | 0.63670 -> 0.64 vs 0.64
macro:Shi | NUMERIC | PASS | round(json value*1.0, 2) | 0.72519 -> 0.73 vs 0.73
macro:rGomp | NUMERIC | PASS | round(json value*1.0, 3) | 0.06453 -> 0.065 vs 0.065
macro:rhoCpa | NUMERIC | PASS | round(json value*1.0, 3) | 0.99095 -> 0.991 vs 0.991
macro:exitLR(%) | NUMERIC | PASS | round(json value*100, 1) | 5.49500 -> 5.5 vs 5.5
macro:exitPhi | NUMERIC | PASS | round(json value*1.0, 2) | 0.70213 -> 0.7 vs 0.7
macro:cMed | NUMERIC | PASS | round(json value*1.0, 3) | 0.97097 -> 0.971 vs 0.971
macro:cLo | NUMERIC | PASS | round(json value*1.0, 3) | 0.93290 -> 0.933 vs 0.933
macro:cHi | NUMERIC | PASS | round(json value*1.0, 3) | 0.99644 -> 0.996 vs 0.996
macro:kMed | NUMERIC | PASS | round(json value*1.0, 2) | 0.76581 -> 0.77 vs 0.77
macro:rhoBev | NUMERIC | PASS | round(json value*1.0, 2) | 0.33284 -> 0.33 vs 0.33
macro:gPull | NUMERIC | PASS | round(json value*1.0, 2) | 0.46430 -> 0.46 vs 0.46
macro:shareTwoThirty | NUMERIC | PASS | round(json value*1.0, 2) | 0.96315 -> 0.96 vs 0.96
macro:shareTwoThirtyLo | NUMERIC | PASS | round(json value*1.0, 2) | 0.92837 -> 0.93 vs 0.93
macro:shareTwoThirtyHi | NUMERIC | PASS | round(json value*1.0, 2) | 0.98566 -> 0.99 vs 0.99
macro:aDiesel | NUMERIC | PASS | round(json value*1.0, 3) | 0.19892 -> 0.199 vs 0.199
macro:aDieselSe | NUMERIC | PASS | round(json value*1.0, 3) | 0.01986 -> 0.02 vs 0.02
macro:aPetrol | NUMERIC | PASS | round(json value*1.0, 3) | 0.04959 -> 0.05 vs 0.05
macro:aPetrolSe | NUMERIC | PASS | round(json value*1.0, 3) | 0.03834 -> 0.038 vs 0.038
macro:bDiesel | NUMERIC | PASS | round(json value*1.0, 3) | 0.09104 -> 0.091 vs 0.091
macro:bPetrol | NUMERIC | PASS | round(json value*1.0, 3) | 0.01023 -> 0.01 vs 0.01
macro:yDiesel | NUMERIC | PASS | round(json value*1.0, 2) | 0.09948 -> 0.1 vs 0.1
macro:yPetrol | NUMERIC | PASS | round(json value*1.0, 2) | 0.17405 -> 0.17 vs 0.17
macro:phiDiesel | NUMERIC | PASS | round(json value*1.0, 2) | 0.40905 -> 0.41 vs 0.41
macro:phiPetrol | NUMERIC | PASS | round(json value*1.0, 2) | 0.57576 -> 0.58 vs 0.58
macro:rDiesel(%) | NUMERIC | PASS | round(json value*100, 1) | 11.54682 -> 11.5 vs 11.5
macro:rPetrol(%) | NUMERIC | PASS | round(json value*100, 1) | 7.28694 -> 7.3 vs 7.3
macro:rPHEV(%) | NUMERIC | PASS | round(json value*100, 1) | 3.55665 -> 3.6 vs 3.6
macro:pDiesel(%) | NUMERIC | PASS | round(json value*100, 0) | 79.40000 -> 79.0 vs 79.0
macro:pNinety(%) | NUMERIC | PASS | round(json value*100, 0) | 0.00000 -> 0.0 vs 0.0
macro:bevFortyK | NUMERIC | PASS | round(json value*1.0, 0) | 2508.09227 -> 2508.0 vs 2508.0
macro:petrolFortyK | NUMERIC | PASS | round(json value*1.0, 0) | 563.37632 -> 563.0 vs 563.0
macro:dieselFortyK | NUMERIC | PASS | round(json value*1.0, 0) | 95.08502 -> 95.0 vs 95.0
macro:totalFortyK | NUMERIC | PASS | round(json value*1.0, 0) | 3259.12020 -> 3259.0 vs 3259.0
macro:tzero | NUMERIC | PASS | 2020 + t0 (assumes t counted in years from 2020; assumption) | 2024.306 vs 2024.3
macro:msOneM | NUMERIC | PASS | simulation.json milestones.bev_1m.median | March 2028 vs March 2028
macro:msOneMLo | NUMERIC | PASS | simulation.json milestones.bev_1m.q05 | January 2028 vs January 2028
macro:msOneMHi | NUMERIC | PASS | simulation.json milestones.bev_1m.q95 | June 2028 vs June 2028
macro:msAbovePetrol | NUMERIC | PASS | simulation.json milestones.bev_above_petrol.median | September 2029 vs September 2029
macro:msAbovePetrolLo | NUMERIC | PASS | simulation.json milestones.bev_above_petrol.q05 | May 2029 vs May 2029
macro:msAbovePetrolHi | NUMERIC | PASS | simulation.json milestones.bev_above_petrol.q95 | April 2030 vs April 2030
macro:msHalf | NUMERIC | PASS | simulation.json milestones.bev_half_fleet.median | April 2031 vs April 2031
macro:msHalfLo | NUMERIC | PASS | simulation.json milestones.bev_half_fleet.q05 | October 2030 vs October 2030
macro:msHalfHi | NUMERIC | PASS | simulation.json milestones.bev_half_fleet.q95 | December 2031 vs December 2031
sim-meta | NUMERIC | PASS | draws==500, horizon 2040-12, last_obs 2026-10 == Vintage | 500, 2040-12, October 2026 vs 500, December 2040, October 2026
medians-2040-add-up (info) | NUMERIC | PASS | sum of fuel medians vs median total (1% tolerance; medians need not add exactly) | 3251.7 vs 3259.1 vs text implies composition within the total
exit-rate:petrol 2020 5.0% | NUMERIC | PASS | 100*exits/stock0 (petrol, 2020) from exits.json | 5.004 -> 5.0 vs 5.0
exit-rate:diesel 2020 4.9% | NUMERIC | PASS | 100*exits/stock0 (diesel, 2020) from exits.json | 4.939 -> 4.9 vs 4.9
exit-rate:petrol 2025 | NUMERIC | PASS | 100*exits/stock0 (petrol, 2025) from exits.json | 7.287 -> 7.3 vs 7.3
exit-rate:diesel 2025 | NUMERIC | PASS | 100*exits/stock0 (diesel, 2025) from exits.json | 11.547 -> 11.5 vs 11.5
exit-rate:petrol 2019 6.7% | NUMERIC | PASS | 100*exits/stock0 (petrol, 2019) from exits.json | 6.703 -> 6.7 vs 6.7
exit-rate:petrol 2020-22 'about 5%' | NUMERIC | PASS | petrol exit rate 2020,2021,2022 in [4.5,5.5] | [5.0, 4.89, 5.19] vs about 5%
petrol-slope-SE>half | NUMERIC | PASS | a_se/a > 0.5 | 0.773 vs > 0.5 ('more than half its value')
ten-annual-observations | NUMERIC | PASS | n_years_age (2016..2025) | 10 vs 10
imports-2025 | NUMERIC | PASS | imports = fleet-rate*BEV stock0 - BEV net exits, 2025 (k cars) | 86515 vs 87k
imports-share-range-2021-25 | NUMERIC | PASS | min/max of imports/new BEV registrations over 2021..2025 | {2021: 0.454, 2022: 0.601, 2023: 0.492, 2024: 0.729, 2025: 0.684} min=0.454 max=0.729 vs between 45% and 73%
kappa-latest-ratio | NUMERIC | PASS | imports_2025 / R_BEV_2025 | 0.684 vs 0.68
kappa-sd-last-3y | NUMERIC | PASS | sample sd of ratio 2023-2025 | 0.126 vs 0.13
BEV-share-2026>80% | NUMERIC | PASS | observed_annual 2026 BEV share (partial year) | 0.8204 vs > 80%
residual-class<100 | NUMERIC | PASS | stock of 'other' in last month 2026-10 (max since 2012: 317) | 97.0 vs fewer than 100 cars
glitch-Dec2011 | NUMERIC | PASS | total(2011-12) - mean(total 2011-11, 2012-01) | 38438 vs about 38,000
tab:backtest 2020-12 h12 observed | NUMERIC | PASS | BEV actual in backtest.json | 66610.0 vs 66610.0
tab:backtest 2020-12 h12 Model | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model] and star==in80 | -20.780 -> -20.8, in80=True vs -20.8*
tab:backtest 2020-12 h12 Share link | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model_share+sales] | -25.500 -> -25.5 vs -25.5
tab:backtest 2020-12 h12 Earlier model | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model_flat+level] | -30.590 -> -30.6 vs -30.6
tab:backtest 2020-12 h12 Frozen shares | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[frozen_shares] | -35.530 -> -35.5 vs -35.5
tab:backtest 2020-12 h12 Linear | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[linear] | -27.530 -> -27.5 vs -27.5
tab:backtest 2020-12 h24 observed | NUMERIC | PASS | BEV actual in backtest.json | 112675.0 vs 112675.0
tab:backtest 2020-12 h24 Model | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model] and star==in80 | -8.720 -> -8.7, in80=True vs -8.7*
tab:backtest 2020-12 h24 Share link | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model_share+sales] | -19.390 -> -19.4 vs -19.4
tab:backtest 2020-12 h24 Earlier model | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model_flat+level] | -31.470 -> -31.5 vs -31.5
tab:backtest 2020-12 h24 Frozen shares | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[frozen_shares] | -59.820 -> -59.8 vs -59.8
tab:backtest 2020-12 h24 Linear | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[linear] | -42.620 -> -42.6 vs -42.6
tab:backtest 2020-12 h36 observed | NUMERIC | PASS | BEV actual in backtest.json | 200114.0 vs 200114.0
tab:backtest 2020-12 h36 Model | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model] and star==in80 | -7.020 -> -7.0, in80=True vs -7.0*
tab:backtest 2020-12 h36 Share link | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model_share+sales] | -17.880 -> -17.9 vs -17.9
tab:backtest 2020-12 h36 Earlier model | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model_flat+level] | -33.090 -> -33.1 vs -33.1
tab:backtest 2020-12 h36 Frozen shares | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[frozen_shares] | -75.740 -> -75.7 vs -75.7
tab:backtest 2020-12 h36 Linear | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[linear] | -59.500 -> -59.5 vs -59.5
tab:backtest 2022-12 h12 observed | NUMERIC | PASS | BEV actual in backtest.json | 200114.0 vs 200114.0
tab:backtest 2022-12 h12 Model | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model] and star==in80 | -1.140 -> -1.1, in80=True vs -1.1*
tab:backtest 2022-12 h12 Share link | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model_share+sales] | -4.500 -> -4.5 vs -4.5
tab:backtest 2022-12 h12 Earlier model | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model_flat+level] | -6.510 -> -6.5 vs -6.5
tab:backtest 2022-12 h12 Frozen shares | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[frozen_shares] | -18.140 -> -18.1 vs -18.1
tab:backtest 2022-12 h12 Linear | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[linear] | -20.680 -> -20.7 vs -20.7
tab:backtest 2022-12 h24 observed | NUMERIC | PASS | BEV actual in backtest.json | 344442.0 vs 344442.0
tab:backtest 2022-12 h24 Model | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model] and star==in80 | -6.780 -> -6.8, in80=True vs -6.8*
tab:backtest 2022-12 h24 Share link | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model_share+sales] | -11.470 -> -11.5 vs -11.5
tab:backtest 2022-12 h24 Earlier model | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model_flat+level] | -16.260 -> -16.3 vs -16.3
tab:backtest 2022-12 h24 Frozen shares | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[frozen_shares] | -38.220 -> -38.2 vs -38.2
tab:backtest 2022-12 h24 Linear | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[linear] | -40.540 -> -40.5 vs -40.5
tab:backtest 2022-12 h36 observed | NUMERIC | PASS | BEV actual in backtest.json | 540981.0 vs 540981.0
tab:backtest 2022-12 h36 Model | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model] and star==in80 | -12.190 -> -12.2, in80=True vs -12.2*
tab:backtest 2022-12 h36 Share link | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model_share+sales] | -16.660 -> -16.7 vs -16.7
tab:backtest 2022-12 h36 Earlier model | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model_flat+level] | -23.850 -> -23.8 vs -23.8
tab:backtest 2022-12 h36 Frozen shares | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[frozen_shares] | -51.780 -> -51.8 vs -51.8
tab:backtest 2022-12 h36 Linear | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[linear] | -53.630 -> -53.6 vs -53.6
tab:backtest 2024-12 h12 observed | NUMERIC | PASS | BEV actual in backtest.json | 540981.0 vs 540981.0
tab:backtest 2024-12 h12 Model | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model] and star==in80 | -3.300 -> -3.3, in80=True vs -3.3*
tab:backtest 2024-12 h12 Share link | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model_share+sales] | -4.970 -> -5.0 vs -5.0
tab:backtest 2024-12 h12 Earlier model | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[model_flat+level] | -6.550 -> -6.6 vs -6.6
tab:backtest 2024-12 h12 Frozen shares | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[frozen_shares] | -9.750 -> -9.8 vs -9.8
tab:backtest 2024-12 h12 Linear | NUMERIC | PASS | round(100*pct_err, 1) from backtest.json[linear] | -9.650 -> -9.7 vs -9.7
bt:model-beats-both-baselines | NUMERIC | PASS | /err model/ < /err frozen/ and < /err linear/ in all 7 cells | True vs True
bt:age<=share-everywhere | NUMERIC | PASS | /err model/ <= /err share link/ in all cells | True vs True
bt:largest-gain-2020-36 | NUMERIC | PASS | argmax of /share/-/model/ and its rounded errors (7 vs 18) | argmax=('2020-12', '36'); gains={'2020-12/12': 4.7, '2020-12/24': 10.7, '2020-12/36': 10.9, '2022-12/12': 3.4, '2022-12/24': 4.7, '2022-12/36': 4.5, '2024-12/12': 1.7}; 2020/36 errors 7.0 vs 17.9 vs 2020 origin, 3 years, 7% vs 18%
bt:seven-comparisons | NUMERIC | PASS | number of table cells | 7 vs seven / covN=7
bt:covModel | NUMERIC | PASS | count of in80==True for Model | 7 vs 7
bt:covShare | NUMERIC | PASS | count of in80==True for Share link | 4 vs 4
bt:covEarlier | NUMERIC | PASS | count of in80==True for Earlier model | 3 vs 3
prose:err 2022-12 h12 | NUMERIC | PASS | round(/pct_err/,0) (abstract / Sec. Validation) | 1.14 vs 1%
prose:err 2022-12 h36 | NUMERIC | PASS | round(/pct_err/,0) (abstract / Sec. Validation) | 12.19 vs 12%
prose:err 2020-12 h12 | NUMERIC | PASS | round(/pct_err/,0) (abstract / Sec. Validation) | 20.78 vs 21%
prose:err 2020-12 h36 | NUMERIC | PASS | round(/pct_err/,0) (abstract / Sec. Validation) | 7.02 vs 7%
prose:err 2024-12 h12 | NUMERIC | PASS | round(/pct_err/,0) (abstract / Sec. Validation) | 3.30 vs 3%
prose:total-within-2% | NUMERIC | PASS | max /pct_err/ of total stock over the 7 cells | 1.64% vs <= 2%
prose:BEV-2%-of-fleet-at-2020-origin | NUMERIC | FAIL | BEV stock / total stock at the 2020-12 origin (panel) | 1.17% at origin 2020-12 (and 2.39% at 2021-12, the 12-month target) vs 2%
prose:floor-binds-8-21% | NUMERIC | FAIL | range of floor_share_age+sales over the 3 origins (age link = forecast model) | 11.3%..24.3%; all variants: {'floor_share_age+sales': [0.243, 0.186, 0.113], 'floor_share_share+sales': [0.131, 0.082, 0.078], 'floor_share_flat+level': [0.058, 0.105, 0.112], 'floor_share_share+level': [0.191, 0.245, 0.193], 'floor_share_flat+sales': [0.042, 0.033, 0.05], 'floor_share_damped+sales': [0.012, 0.071, 0.137]} vs 8--21%

## Rendered equations

**eq:exits-solve-stock**

```
  eq:exits-solve-stock
  X_y = -E + R + Xₚᵣₑᵥ
```

**sales-identity (Sec.3.1 total exit rate, 4 fuels)**

```
  sales-identity (Sec.3.1 total exit rate, 4 fuels)
  R₁ + R₂ + R₃ + R₄ = R₁ + R₂ + R₃ + R₄
```

**residual-rule BEV=total-others**

```
  residual-rule BEV=total-others
  Eₒ₁ + Eₒ₂ + Eₒ₃ - Eₜₒₜ + R_bev + Xp_bev = Eₒ₁ + Eₒ₂ + Eₒ₃ - Eₜₒₜ + R_bev + ↪
  
  ↪  Xp_bev
```

**floor-imports-effect**

```
  floor-imports-effect
                       ⎧A   for A + I > 0
  -I + Max(0, A + I) = ⎨                 
                       ⎩-I    otherwise  
```

**eq:gompertz-log-split**

```
  eq:gompertz-log-split
     ⎛       -r⋅t⎞                     
     ⎜   -b⋅ℯ    ⎟        -r⋅t         
  log⎝S⋅ℯ        ⎠ = - b⋅ℯ     + log(S)
```

**eq:gompertz-start-level**

```
  eq:gompertz-start-level
  c₀ = c₀
```

**eq:gompertz-ceiling**

```
  eq:gompertz-ceiling
      ⎛       -r⋅t⎞    
      ⎜   -b⋅ℯ    ⎟    
  lim ⎝S⋅ℯ        ⎠ = S
  t─→∞                 
```

**eq:share-ceiling**

```
  eq:share-ceiling
      ⎛       c̅        ⎞    
  lim ⎜────────────────⎟ = c̅
  t─→∞⎜     -k⋅(t - t₀)⎟    
      ⎝1 + ℯ           ⎠    
```

**eq:share-midpoint**

```
  eq:share-midpoint
  c̅   c̅
  ─ = ─
  2   2
```

**eq:share-monotone**

```
  eq:share-monotone
  ∂ ⎛       c̅        ⎞           c̅⋅k        
  ──⎜────────────────⎟ = ───────────────────
  ∂t⎜     -k⋅(t - t₀)⎟         2⎛k⋅(t - t₀)⎞
    ⎝1 + ℯ           ⎠   4⋅cosh ⎜──────────⎟
                                ⎝    2     ⎠
```

**remainder-shrinks-to-1-cbar**

```
  remainder-shrinks-to-1-cbar
      ⎛         c̅            ⎞        
  lim ⎜- ──────────────── + 1⎟ = 1 - c̅
  t─→∞⎜       -k⋅(t - t₀)    ⎟        
      ⎝  1 + ℯ               ⎠        
```

**eq:share-obs-variance**

```
  eq:share-obs-variance
       1            1        1 
  ─────────── = ───────── + ───
  n⋅p⋅(1 - p)   n⋅(1 - p)   n⋅p
```

**eq:rate-start**

```
  eq:rate-start
  δ + r₀ = δ + r₀
```

**eq:rate-max-rise**

```
  eq:rate-max-rise
  α⋅y₀ = α⋅y₀
```

**eq:rateshare-start**

```
  eq:rateshare-start
  δ + r₀ = δ + r₀
```

**eq:imports-lognormal**

```
  eq:imports-lognormal
  E[kappa] = m
```

**prior-S-center**

```
  prior-S-center
  mean(0.60,0.64,0.65,0.71) = 0.65
```

**rMax-diesel**

```
  rMax-diesel
  α⋅y₀ + r₀ = 13.526
```

**rMax-petrol**

```
  rMax-petrol
  α⋅y₀ + r₀ = 8.1501
```

**macro:Smed**

```
  macro:Smed
  macro:Smed = 0.68
```

**macro:Slo**

```
  macro:Slo
  macro:Slo = 0.64
```

**macro:Shi**

```
  macro:Shi
  macro:Shi = 0.73
```

**macro:rGomp**

```
  macro:rGomp
  macro:rGomp = 0.065
```

**macro:rhoCpa**

```
  macro:rhoCpa
  macro:rhoCpa = 0.991
```

**macro:exitLR(%)**

```
  macro:exitLR(%)
  macro:exitLR(%) = 5.5
```

**macro:exitPhi**

```
  macro:exitPhi
  macro:exitPhi = 0.7
```

**macro:cMed**

```
  macro:cMed
  macro:cMed = 0.971
```

**macro:cLo**

```
  macro:cLo
  macro:cLo = 0.933
```

**macro:cHi**

```
  macro:cHi
  macro:cHi = 0.996
```

**macro:kMed**

```
  macro:kMed
  macro:kMed = 0.77
```

**macro:rhoBev**

```
  macro:rhoBev
  macro:rhoBev = 0.33
```

**macro:gPull**

```
  macro:gPull
  macro:gPull = 0.46
```

**macro:shareTwoThirty**

```
  macro:shareTwoThirty
  macro:shareTwoThirty = 0.96
```

**macro:shareTwoThirtyLo**

```
  macro:shareTwoThirtyLo
  macro:shareTwoThirtyLo = 0.93
```

**macro:shareTwoThirtyHi**

```
  macro:shareTwoThirtyHi
  macro:shareTwoThirtyHi = 0.99
```

**macro:aDiesel**

```
  macro:aDiesel
  macro:aDiesel = 0.199
```

**macro:aDieselSe**

```
  macro:aDieselSe
  macro:aDieselSe = 0.02
```

**macro:aPetrol**

```
  macro:aPetrol
  macro:aPetrol = 0.05
```

**macro:aPetrolSe**

```
  macro:aPetrolSe
  macro:aPetrolSe = 0.038
```

**macro:bDiesel**

```
  macro:bDiesel
  macro:bDiesel = 0.091
```

**macro:bPetrol**

```
  macro:bPetrol
  macro:bPetrol = 0.01
```

**macro:yDiesel**

```
  macro:yDiesel
  macro:yDiesel = 0.1
```

**macro:yPetrol**

```
  macro:yPetrol
  macro:yPetrol = 0.17
```

**macro:phiDiesel**

```
  macro:phiDiesel
  macro:phiDiesel = 0.41
```

**macro:phiPetrol**

```
  macro:phiPetrol
  macro:phiPetrol = 0.58
```

**macro:rDiesel(%)**

```
  macro:rDiesel(%)
  macro:rDiesel(%) = 11.5
```

**macro:rPetrol(%)**

```
  macro:rPetrol(%)
  macro:rPetrol(%) = 7.3
```

**macro:rPHEV(%)**

```
  macro:rPHEV(%)
  macro:rPHEV(%) = 3.6
```

**macro:pDiesel(%)**

```
  macro:pDiesel(%)
  macro:pDiesel(%) = 79.0
```

**macro:pNinety(%)**

```
  macro:pNinety(%)
  macro:pNinety(%) = 0.0
```

**macro:bevFortyK**

```
  macro:bevFortyK
  macro:bevFortyK = 2508.0
```

**macro:petrolFortyK**

```
  macro:petrolFortyK
  macro:petrolFortyK = 563.0
```

**macro:dieselFortyK**

```
  macro:dieselFortyK
  macro:dieselFortyK = 95.0
```

**macro:totalFortyK**

```
  macro:totalFortyK
  macro:totalFortyK = 3259.0
```

**macro:tzero**

```
  macro:tzero
  2020+t0 = 2024.3
```

**macro:msOneM**

```
  macro:msOneM
  msOneM = March₂₀₂₈
```

**macro:msOneMLo**

```
  macro:msOneMLo
  msOneMLo = January₂₀₂₈
```

**macro:msOneMHi**

```
  macro:msOneMHi
  msOneMHi = June₂₀₂₈
```

**macro:msAbovePetrol**

```
  macro:msAbovePetrol
  msAbovePetrol = September₂₀₂₉
```

**macro:msAbovePetrolLo**

```
  macro:msAbovePetrolLo
  msAbovePetrolLo = May₂₀₂₉
```

**macro:msAbovePetrolHi**

```
  macro:msAbovePetrolHi
  msAbovePetrolHi = April₂₀₃₀
```

**macro:msHalf**

```
  macro:msHalf
  msHalf = April₂₀₃₁
```

**macro:msHalfLo**

```
  macro:msHalfLo
  msHalfLo = October₂₀₃₀
```

**macro:msHalfHi**

```
  macro:msHalfHi
  msHalfHi = December₂₀₃₁
```

**sim-meta**

```
  sim-meta
  draws = 500
```

**medians-2040-add-up (info)**

```
  medians-2040-add-up (info)
  sum medians = 3251.74
```

**exit-rate:petrol 2020 5.0%**

```
  exit-rate:petrol 2020 5.0%
  E/X[petrol,2020] = 5.0041
```

**exit-rate:diesel 2020 4.9%**

```
  exit-rate:diesel 2020 4.9%
  E/X[diesel,2020] = 4.9393
```

**exit-rate:petrol 2025**

```
  exit-rate:petrol 2025
  E/X[petrol,2025] = 7.2869
```

**exit-rate:diesel 2025**

```
  exit-rate:diesel 2025
  E/X[diesel,2025] = 11.547
```

**exit-rate:petrol 2019 6.7%**

```
  exit-rate:petrol 2019 6.7%
  E/X[petrol,2019] = 6.7034
```

**exit-rate:petrol 2020-22 'about 5%'**

```
  exit-rate:petrol 2020-22 'about 5%'
  mean rate 2020-22 = 5.0266
```

**petrol-slope-SE>half**

```
  petrol-slope-SE>half
  se/a = 0.7732
```

**ten-annual-observations**

```
  ten-annual-observations
  n = 10
```

**imports-2025**

```
  imports-2025
  I₂₀₂₅ = 86515.3
```

**imports-share-range-2021-25**

```
  imports-share-range-2021-25
  range = [0.45,0.73]
```

**kappa-latest-ratio**

```
  kappa-latest-ratio
  κ₂₀₂₅ = 0.6844
```

**kappa-sd-last-3y**

```
  kappa-sd-last-3y
  sd(kappa) = 0.1264
```

**BEV-share-2026>80%**

```
  BEV-share-2026>80%
  s₂₀₂₆ = 0.8204
```

**residual-class<100**

```
  residual-class<100
  other = 97.0
```

**glitch-Dec2011**

```
  glitch-Dec2011
  glitch = 38438.0
```

**tab:backtest 2020-12 h12 observed**

```
  tab:backtest 2020-12 h12 observed
  obs[2020-12,12] = 66610.0
```

**tab:backtest 2020-12 h12 Model**

```
  tab:backtest 2020-12 h12 Model
  err[Model,2020-12,12] = -20.8
```

**tab:backtest 2020-12 h12 Share link**

```
  tab:backtest 2020-12 h12 Share link
  err[Share link,2020-12,12] = -25.5
```

**tab:backtest 2020-12 h12 Earlier model**

```
  tab:backtest 2020-12 h12 Earlier model
  err[Earlier model,2020-12,12] = -30.6
```

**tab:backtest 2020-12 h12 Frozen shares**

```
  tab:backtest 2020-12 h12 Frozen shares
  err[Frozen shares,2020-12,12] = -35.5
```

**tab:backtest 2020-12 h12 Linear**

```
  tab:backtest 2020-12 h12 Linear
  err[Linear,2020-12,12] = -27.5
```

**tab:backtest 2020-12 h24 observed**

```
  tab:backtest 2020-12 h24 observed
  obs[2020-12,24] = 112675.0
```

**tab:backtest 2020-12 h24 Model**

```
  tab:backtest 2020-12 h24 Model
  err[Model,2020-12,24] = -8.7
```

**tab:backtest 2020-12 h24 Share link**

```
  tab:backtest 2020-12 h24 Share link
  err[Share link,2020-12,24] = -19.4
```

**tab:backtest 2020-12 h24 Earlier model**

```
  tab:backtest 2020-12 h24 Earlier model
  err[Earlier model,2020-12,24] = -31.5
```

**tab:backtest 2020-12 h24 Frozen shares**

```
  tab:backtest 2020-12 h24 Frozen shares
  err[Frozen shares,2020-12,24] = -59.8
```

**tab:backtest 2020-12 h24 Linear**

```
  tab:backtest 2020-12 h24 Linear
  err[Linear,2020-12,24] = -42.6
```

**tab:backtest 2020-12 h36 observed**

```
  tab:backtest 2020-12 h36 observed
  obs[2020-12,36] = 200114.0
```

**tab:backtest 2020-12 h36 Model**

```
  tab:backtest 2020-12 h36 Model
  err[Model,2020-12,36] = -7.0
```

**tab:backtest 2020-12 h36 Share link**

```
  tab:backtest 2020-12 h36 Share link
  err[Share link,2020-12,36] = -17.9
```

**tab:backtest 2020-12 h36 Earlier model**

```
  tab:backtest 2020-12 h36 Earlier model
  err[Earlier model,2020-12,36] = -33.1
```

**tab:backtest 2020-12 h36 Frozen shares**

```
  tab:backtest 2020-12 h36 Frozen shares
  err[Frozen shares,2020-12,36] = -75.7
```

**tab:backtest 2020-12 h36 Linear**

```
  tab:backtest 2020-12 h36 Linear
  err[Linear,2020-12,36] = -59.5
```

**tab:backtest 2022-12 h12 observed**

```
  tab:backtest 2022-12 h12 observed
  obs[2022-12,12] = 200114.0
```

**tab:backtest 2022-12 h12 Model**

```
  tab:backtest 2022-12 h12 Model
  err[Model,2022-12,12] = -1.1
```

**tab:backtest 2022-12 h12 Share link**

```
  tab:backtest 2022-12 h12 Share link
  err[Share link,2022-12,12] = -4.5
```

**tab:backtest 2022-12 h12 Earlier model**

```
  tab:backtest 2022-12 h12 Earlier model
  err[Earlier model,2022-12,12] = -6.5
```

**tab:backtest 2022-12 h12 Frozen shares**

```
  tab:backtest 2022-12 h12 Frozen shares
  err[Frozen shares,2022-12,12] = -18.1
```

**tab:backtest 2022-12 h12 Linear**

```
  tab:backtest 2022-12 h12 Linear
  err[Linear,2022-12,12] = -20.7
```

**tab:backtest 2022-12 h24 observed**

```
  tab:backtest 2022-12 h24 observed
  obs[2022-12,24] = 344442.0
```

**tab:backtest 2022-12 h24 Model**

```
  tab:backtest 2022-12 h24 Model
  err[Model,2022-12,24] = -6.8
```

**tab:backtest 2022-12 h24 Share link**

```
  tab:backtest 2022-12 h24 Share link
  err[Share link,2022-12,24] = -11.5
```

**tab:backtest 2022-12 h24 Earlier model**

```
  tab:backtest 2022-12 h24 Earlier model
  err[Earlier model,2022-12,24] = -16.3
```

**tab:backtest 2022-12 h24 Frozen shares**

```
  tab:backtest 2022-12 h24 Frozen shares
  err[Frozen shares,2022-12,24] = -38.2
```

**tab:backtest 2022-12 h24 Linear**

```
  tab:backtest 2022-12 h24 Linear
  err[Linear,2022-12,24] = -40.5
```

**tab:backtest 2022-12 h36 observed**

```
  tab:backtest 2022-12 h36 observed
  obs[2022-12,36] = 540981.0
```

**tab:backtest 2022-12 h36 Model**

```
  tab:backtest 2022-12 h36 Model
  err[Model,2022-12,36] = -12.2
```

**tab:backtest 2022-12 h36 Share link**

```
  tab:backtest 2022-12 h36 Share link
  err[Share link,2022-12,36] = -16.7
```

**tab:backtest 2022-12 h36 Earlier model**

```
  tab:backtest 2022-12 h36 Earlier model
  err[Earlier model,2022-12,36] = -23.8
```

**tab:backtest 2022-12 h36 Frozen shares**

```
  tab:backtest 2022-12 h36 Frozen shares
  err[Frozen shares,2022-12,36] = -51.8
```

**tab:backtest 2022-12 h36 Linear**

```
  tab:backtest 2022-12 h36 Linear
  err[Linear,2022-12,36] = -53.6
```

**tab:backtest 2024-12 h12 observed**

```
  tab:backtest 2024-12 h12 observed
  obs[2024-12,12] = 540981.0
```

**tab:backtest 2024-12 h12 Model**

```
  tab:backtest 2024-12 h12 Model
  err[Model,2024-12,12] = -3.3
```

**tab:backtest 2024-12 h12 Share link**

```
  tab:backtest 2024-12 h12 Share link
  err[Share link,2024-12,12] = -5.0
```

**tab:backtest 2024-12 h12 Earlier model**

```
  tab:backtest 2024-12 h12 Earlier model
  err[Earlier model,2024-12,12] = -6.6
```

**tab:backtest 2024-12 h12 Frozen shares**

```
  tab:backtest 2024-12 h12 Frozen shares
  err[Frozen shares,2024-12,12] = -9.8
```

**tab:backtest 2024-12 h12 Linear**

```
  tab:backtest 2024-12 h12 Linear
  err[Linear,2024-12,12] = -9.7
```

**bt:model-beats-both-baselines**

```
  bt:model-beats-both-baselines
  all cells = True
```

**bt:age<=share-everywhere**

```
  bt:age<=share-everywhere
  all cells = True
```

**bt:largest-gain-2020-36**

```
  bt:largest-gain-2020-36
  max gain = 10.9
```

**bt:seven-comparisons**

```
  bt:seven-comparisons
  N = 7
```

**bt:covModel**

```
  bt:covModel
  covModel = 7
```

**bt:covShare**

```
  bt:covShare
  covShare = 4
```

**bt:covEarlier**

```
  bt:covEarlier
  covEarlier = 3
```

**prose:err 2022-12 h12**

```
  prose:err 2022-12 h12
  |err|[2022-12,12] = 1.14
```

**prose:err 2022-12 h36**

```
  prose:err 2022-12 h36
  |err|[2022-12,36] = 12.19
```

**prose:err 2020-12 h12**

```
  prose:err 2020-12 h12
  |err|[2020-12,12] = 20.78
```

**prose:err 2020-12 h36**

```
  prose:err 2020-12 h36
  |err|[2020-12,36] = 7.02
```

**prose:err 2024-12 h12**

```
  prose:err 2024-12 h12
  |err|[2024-12,12] = 3.3
```

**prose:total-within-2%**

```
  prose:total-within-2%
  max|err_total| = 1.64
```

**prose:BEV-2%-of-fleet-at-2020-origin**

```
  prose:BEV-2%-of-fleet-at-2020-origin
  BEV/total[2020-12] = 1.171
```

**prose:floor-binds-8-21%**

```
  prose:floor-binds-8-21%
  floor share range = [11.3,24.3]
```

## Failures

### prose:BEV-2%-of-fleet-at-2020-origin (Abstract and Validation: "from the 2020 origin, when BEVs were 2% of the fleet")
- As written: BEVs were 2% of the fleet at the 2020 origin.
- SymPy/numeric translation: BEV stock / total stock in December 2020 from `Data/backtest/2020-12/panels/fuel4_monthly.csv`, rounded to whole percent.
- Discrepancy: 31,888 / 2,723,612 = 1.17% (rounds to 1%). The 2% matches the target month of the one-year horizon (Dec 2021: 66,610 / 2,787,559 = 2.39%).
- Likely cause: wording, not arithmetic. The sentence attaches the 2% to the origin (Dec 2020) but 2% is the fleet share at the first evaluation date (Dec 2021). The translation is straightforward; I do not suspect it.

### prose:floor-binds-8-21% (Sec. 3.3 BEV scrappage: "This happens in 8--21% of the simulated months in the backtest")
- As written: the floor binds in 8--21% of simulated months in the backtest.
- Translation: range of `floor_share_age+sales` (the age-link model used in the forecast) over the three origins in `Data/backtest/backtest.json`.
- Discrepancy: 11.3%, 18.6%, 24.3% (2024, 2022, 2020 origins), i.e. 11--24%. No other variant gives 8--21% either: share+sales 7.8--13.1%, flat+level 5.8--11.2%, share+level 19.1--24.5%, flat+sales 3.3--5.0%, damped+sales 1.2--13.7%. The current-vintage `floor_share` in simulation.json is 3.2%.
- Likely cause: stale number (from an earlier rule or run) or a different definition (e.g. a subset of horizons). The text claim and `backtest.json` disagree; the translation is plausible but the intended statistic is ambiguous.

## Not machine-checkable

- eq:exits (definition of net exits E): Definition of E; its inversion is checked above (SOLVE).
- eq:gompertz AR(1) term u_t = rho u_{t-1} + eps_t, and the Gompertz form as a modelling choice: Modelling assumption; only the algebra (log split, c0, ceiling) is checked.
- eq:share full form incl. gamma_D, gamma_J, v_t, e_t: Statistical model specification; only the curve algebra is checked.
- Intro: about 25 parameters, runs in a few minutes: Counting/timing claim, not derivable by SymPy.
- Abstract/Sec.3: model beats damped local linear trends; 90% interval 2035 covers almost 0 to 1: Statement about a discarded model; its output is not in the data files.
- Young share diesel 0.37 (1 Jan 2020) -> 0.10 (1 Jan 2025); 60-month measure 0.14 vs observed 0.06 in Jan 2026: BIL21 age table in Data/panels/age_fuel.csv does not reproduce (file is unfiltered by vehicle type: diesel-code values 0.18/0.087/0.062). Only y0=0.0995 -> 0.10 matches via simulation.json.
- Table BIL51 = BIL6 exactly; BIL54 hybrid codes add up to PHEV exactly: Data-source reconciliation claim, needs raw StatBank tables.
- Net exits of BEVs negative since 2021: Not tested symbolically; historical data (exits.json shows negative from 2020: -2,166 in the 2020 slot).
- w_t falls linearly from 1 to 0 in 2035: Underspecified (start date not stated); modelling assumption.
- Eq. rateshare petrol: beta=0.010 'leaves the petrol rate almost unchanged': Qualitative; depends on simulated path of s-bar and units of beta.
- Rate rises 'until the last cars sold new have aged out'; share levels off 'early 2030s': Qualitative reasoning about simulated paths.
- Convergence gate (Rhat<1.01, no divergences, ESS>400): Procedure/definition; diagnostics in total.json/shares.json are consistent (max Rhat 1.002, ESS min 993) but this is not a math identity.
- Prior S ~ N(0.65, 0.04) 'based on' country levels; c-bar ~ TN(0.97,0.03;0.80,1.00) 'centred on Norway': Prior choice; Norway's share is an external fact. Only mean of 0.60/0.64/0.65/0.71 = 0.65 is checked.
- Posterior 'still largely determined by the prior' for c-bar: Interpretation of posterior vs prior.
- Mean reversion vs trend rationale; 'implausibly long service lives': Reasoning.
- Decomposition: BEV share not the cause; forecast share close to or above observed: Reasoning; decomposition output not in the provided files.
- Proofs/consistency 'fuel stocks add up to total in every month and draw': Holds by construction on draws; checked symbolically (residual-rule) but cannot be checked on draw-level output here.
- Sec.5 limitations: backtest not independent, population projection not cut at origins: Methodological statements.
- Kalman likelihood tests vs multivariate normal: Code-test claim, outside this check.

Minor notes on PASS results that sit near a rounding edge: rMax-petrol is 8.1501 from the unrounded json (rounds to 8.2) but would be 8.15 from the rounded macros; imports-2025 is 86.5k (stated 87k); kappa sd 0.126 (stated 0.13); the 'residual class fewer than 100 cars' holds for the latest month (97) but the class peaked at 317 in the sample; macro:tzero assumes t is measured from 2020.

## Caveat

Results are conditional on the LaTeX-to-SymPy translation shown in the "What was checked" column. Numeric checks compare the text to the model-output files under `Data/`, not to an independent re-estimation. NUMERIC checks for 'earlier model' map to `model_flat+level` and 'share link' to `model_share+sales`; these mappings are my reading of the text and matched all 35 table cells.
