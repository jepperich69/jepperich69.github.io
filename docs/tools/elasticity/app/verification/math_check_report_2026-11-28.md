# Math check: model_documentation

Source: `<project>\doc\model_documentation.tex`

Timestamp: 2026-11-28 12:18:02

**Totals: 171 checked: 168 passed, 3 failed, 0 errored; 29 not-checkable**

Script: `verify.py` (re-runnable; reads `doc\generated\*.tex`), raw output: `output.txt`, machine-readable: `results.json`.

## Results

| Label | Type | Result | What was checked | Got vs stated |
|---|---|---|---|---|
| Eq-shrink-sums-to-one | IDENTITY | PASS | sum_a (n wh_a + tau wb_a)/(n+tau), both share vectors sum to 1; sizes {2,3,4} | [1, 1, 1] vs 1 |
| Eq-shrink-limits | IDENTITY | PASS | f(n=0)=prior ; f(tau=0)=observed | wb ; wh vs prior ; observed |
| Sec2-shrink-n300-keeps-91pct | NUMERIC | PASS | n/(n+tau), n=300, tau=30 | 0.90909 vs 0.91 |
| Sec2-shrink-n10-keeps-25pct | NUMERIC | PASS | n/(n+tau), n=10, tau=30 | 0.25000 vs 0.25 |
| Sec4-VoT-top-band-midpoint | IDENTITY | PASS | midpoint of [L,1.5L] - 1.25 L | 0 vs 0 |
| Eq-walkbike-kappaW | NUMERIC | PASS | 60/(2*5)*mean(0.156,0.091); input coefficients rounded to 3 dp so tolerance 0.003 | 0.74100 vs 0.742 [exact to 3dp would be 0.741] |
| Eq-walkbike-kappaB | NUMERIC | PASS | 60/(2*15)*mean(0.131,0.134) | 0.26500 vs 0.265 |
| Eq-nlresp | IDENTITY | PASS | P1(n) from eq:nlprob with V+Delta minus eq:nlresp P1(n) (2 nests, 3 alts; numeric at theta in {.15,.5,.9,1} with exact rationals, symbolic attempt); P1(a\|n) symbolic | P(a\|n) diff=0; P(n) symbolic=0; numeric diffs=[5.551115123125783e-17, 5.551115123125783e-17, -1.1102230246251565e-16, 1.1102230246251565e-16] vs 0 |
| Eq-nlresp-theta1-MNL | IDENTITY | PASS | P1(n)P1(a\|n) at theta=1 minus MNL probability e^{V+D}/(e^V0+sum e^{V+D}) | 0 vs 0 |
| Sec3-notour-mass | IDENTITY | PASS | N0/(N+N0) - s0 with N0 = N s0/(1-s0) | 0 vs 0 |
| Sec3-notour-tours | IDENTITY | PASS | (N+N0)(1-s0) - N (base tours recovered) | 0 vs 0 |
| Eq-moneyshare-odds | IDENTITY | PASS | sigma/(1-sigma) - s C/(v T) | 0 vs 0 |
| Eq-gtratio | IDENTITY | PASS | G'/G - (1 + sigma x_c + (1-sigma) x_t) | 0 vs 0 |
| Eq-nlshift-phi0-sign | IDENTITY | FAIL | Delta_a at phi=0 from eq:nlshift minus text claim 'utility changes by +beta ln(G'/G)' | -log(((C*s*(x_c + 1) + T*v*(x_t + 1))/(C*s + T*v))**(2*beta)) vs 0 |
| Eq-nlshift-phi0-consistent | IDENTITY | PASS | Delta_a(phi=0) + beta ln(G'/G) (equation itself gives -beta ln) | 0 vs 0 |
| Eq-ipdl-sign-vs-nlshift | IDENTITY | FAIL | Delta delta_j (eq:ipdl) = +beta ln(G'/G) minus Delta_a at phi=0 (eq:nlshift) with the same beta; difference should vanish if the sign convention is shared | log(((C*s*(x_c + 1) + T*v*(x_t + 1))/(C*s + T*v))**(2*beta)) vs 0 |
| Eq-odds-shared | IDENTITY | PASS | o_m - s_m o_S with C_m/T_m=C_S/T_S | 0 vs 0 |
| Eq-moneyshare-inverse | IDENTITY | PASS | o/(1+o) with o=sigma/(1-sigma) minus sigma (eq:odds sigma_m = o_m/(1+o_m)) | 0 vs 0 |
| Tab-cs-Commute-HOV | NUMERIC | PASS | 1/(1+L_H), L_H=0.904 (load factor reused from earlier run; LTM Table 5.8 not in document) | 0.52521 vs 0.525 |
| Tab-cs-Commute-CP | NUMERIC | PASS | (1-1/(1+L_C))/max(1,L_C), L_C=1.178 | 0.45914 vs 0.459 |
| Tab-cs-Education-HOV | NUMERIC | PASS | 1/(1+L_H), L_H=1.046 (load factor reused from earlier run; LTM Table 5.8 not in document) | 0.48876 vs 0.489 |
| Tab-cs-Education-CP | NUMERIC | PASS | (1-1/(1+L_C))/max(1,L_C), L_C=1.143 | 0.46664 vs 0.467 |
| Tab-cs-Escort-HOV | NUMERIC | PASS | 1/(1+L_H), L_H=0.704 (load factor reused from earlier run; LTM Table 5.8 not in document) | 0.58685 vs 0.587 |
| Tab-cs-Escort-CP | NUMERIC | PASS | (1-1/(1+L_C))/max(1,L_C), L_C=1.207 | 0.45310 vs 0.453 |
| Tab-cs-Shopping-HOV | NUMERIC | PASS | 1/(1+L_H), L_H=1.03 (load factor reused from earlier run; LTM Table 5.8 not in document) | 0.49261 vs 0.493 |
| Tab-cs-Shopping-CP | NUMERIC | PASS | (1-1/(1+L_C))/max(1,L_C), L_C=1.212 | 0.45208 vs 0.452 |
| Tab-cs-Leisure-HOV | NUMERIC | PASS | 1/(1+L_H), L_H=1.125 (load factor reused from earlier run; LTM Table 5.8 not in document) | 0.47059 vs 0.471 |
| Tab-cs-Leisure-CP | NUMERIC | PASS | (1-1/(1+L_C))/max(1,L_C), L_C=1.373 | 0.42141 vs 0.421 |
| Tab-cs-Business-HOV | NUMERIC | PASS | 1/(1+L_H), L_H=1.135 (load factor reused from earlier run; LTM Table 5.8 not in document) | 0.46838 vs 0.468 |
| Tab-cs-Business-CP | NUMERIC | PASS | (1-1/(1+L_C))/max(1,L_C), L_C=1.525 | 0.39604 vs 0.396 |
| Eq-r-car | NUMERIC | PASS | 0.936/1.197 | 0.78195 vs 0.78 |
| Eq-r-cost-growth | NUMERIC | PASS | 1.088/1.162 (vfttwentythree/vftten) | 0.93632 vs 0.936 |
| Eq-burden-fare-fixed | NUMERIC | PASS | 2*13.1 per tour (eq:burden constant 26.2) | 26.20000 vs 26.2 |
| Eq-votinterp-left | IDENTITY | PASS | v(m_n) - v_n | 0 vs 0 |
| Eq-votinterp-right | IDENTITY | PASS | v(m_{n+1}) - v_{n+1} | 0 vs 0 |
| Tab-vot-odds-scale | NUMERIC | PASS | odds_scale_q * v(ybar rho_q)/r_car = v(ybar) constant across q | [1.194, 1.185, 1.185, 1.189, 1.19] spread 0.009 vs constant up to rounding |
| Tab-vot-rho | NUMERIC | PASS | personal income_q / rho_q constant | [346.0, 343.4, 345.4, 344.0, 343.1] vs constant (mean personal income) |
| Eq-cellodds-monotone | NUMERIC | PASS | odds scale decreasing in income quintile ('lowers the money share in high-income cells') | [0.97, 0.84, 0.79, 0.76, 0.64] vs decreasing |
| Sec4-ybar-cpi | NUMERIC | PASS | vybar*vcpi (thousand DKK, 2023 prices) vs person-weighted mean personal income 2009-11 in tab_income | 320.45148 vs 320.40751505086155 |
| Tab-income-shares-sum100 | NUMERIC | PASS | none+one+two = 100 (all 10 rows) | [100.1, 100.0, 99.9, 100.0, 99.9, 100.0, 100.1, 100.0, 100.0, 100.1] vs 100 |
| Tab-income-householdcars | NUMERIC | PASS | (one+2*two)/100 vs household cars column | max abs diff 0.006 vs <=0.01 rounding |
| Tab-income-elasticity-2009-11 | NUMERIC | PASS | ln(cars_Q5/cars_Q1)/ln(hhinc_Q5/hhinc_Q1), 2009-11 | 0.52626 vs 0.53 |
| Tab-income-elasticity-2023 | NUMERIC | PASS | ln(cars_Q5/cars_Q1)/ln(hhinc_Q5/hhinc_Q1), 2023 | 0.46279 vs 0.46 |
| Sec2-nocar-Q1-2023 | NUMERIC | PASS | share without car Q1 2023 (table 40.5) vs text 41% | 40.50000 vs 41 |
| Sec2-nocar-Q5-2023 | NUMERIC | PASS | share without car Q5 2023 vs text 4% | 4.40000 vs 4 |
| Sec2-cars-Q1-2023 | NUMERIC | PASS | household cars Q1 2023 vs text 0.67 | 0.67000 vs 0.67 |
| Sec2-cars-Q5-2023 | NUMERIC | PASS | household cars Q5 2023 vs text 1.59 | 1.59000 vs 1.59 |
| Sec2-elasticity-decline | NUMERIC | PASS | 0.46 (2023) < 0.53 (2009-11) 'modest decline' | 0.46 < 0.53 vs decline |
| Tab-base-row-sums | NUMERIC | PASS | sum of 6 modes minus 'All' per purpose | {'Commute': 0.0, 'Education': 0.0, 'Escort': 0.0, 'Shopping': -1.0, 'Leisure': -1.0, 'Business': -1.0} vs 0 (rounding, thousands) |
| Tab-base-col-sums | NUMERIC | PASS | sum over purposes minus 'All' per column | [-2.0, 0.0, 1.0, 0.0, -1.0, -1.0, 0.0] vs 0 (rounding) |
| Sec2-vtours | NUMERIC | PASS | All tours (thousands)/1000 vs vtours | 6.37000 vs 6.37 |
| Tab-base-mean-km | NUMERIC | PASS | tour-weighted mean of mode mean lengths vs All column 28.9 | 28.84673 vs 28.9 |
| Eq-ipdl-mu0-MNL | IDENTITY | PASS | delta_j\|mu=0 - ln(s_j/s_0) | 0 vs 0 |
| Eq-ipdl-one-dim-Berry | IDENTITY | PASS | one-dim delta_j minus [ln(s_j/s_0) - mu (ln s_j - ln s_g)] (Berry nested-logit inversion, theta=1-mu) | 0 vs 0 |
| Eq-length-arc | IDENTITY | PASS | 1.1^eta - (1+0.1E), eta=ln(1+0.1E)/ln1.1, spot E in {-.3,.2,-.5,.8} | [0, 0, 0, 0] vs 0 |
| Sec5-mileage-arc-product | IDENTITY | PASS | arc mileage elasticity from (1+.1 ET)(1+.1 EL)-1 divided by 0.1, minus (ET+EL+0.1 ET EL) | 0 vs 0 |
| Tab-cmp-commute-diffcolumn | NUMERIC | PASS | Diff = Model - LTM over 72 cells | 0 violations > 0.0011 vs 0 |
| Tab-cmp-commute-mileage-identity | NUMERIC | PASS | E_km - (E_T+E_L+0.1 E_T E_L) over all rows, LTM and model | max abs 0.0012 vs < 0.0035 (rounding) |
| Tab-err-Commute-toursRMSE | NUMERIC | PASS | RMSE of 24 tour diffs (tab_cmp, rounded) vs tab_err Tours | 0.01940 vs 0.019 |
| Tab-err-Commute-toursMax | NUMERIC | PASS | max \|tour diff\| vs tab_err Max | 0.04500 vs 0.045 |
| Tab-err-Commute-lengthRMSE | NUMERIC | PASS | RMSE of 24 length diffs vs tab_err Length | 0.03684 vs 0.037 |
| Tab-err-Commute-mileageRMSE | NUMERIC | PASS | RMSE of 24 mileage diffs vs tab_err Mileage | 0.02299 vs 0.023 |
| Sec5-commute-walk-LTM-length-0.041 | NUMERIC | PASS | LTM walk avg length elasticity to car cost | 0.04100 vs 0.041 |
| Sec5-commute-bike-LTM-length-0.058 | NUMERIC | PASS | LTM bike avg length elasticity to car cost | 0.05800 vs 0.058 |
| Sec5-model-walk-bike-shorter | NUMERIC | FAIL | text: model lets walk and bike tours 'become slightly shorter' (model length elasticity to car cost < 0 for both) | walk -0.026, bike 0.004 vs both negative |
| Sec5-largest-diff-length-walkbike | NUMERIC | PASS | largest \|Diff\| for commuting lies in walk/bike average length | (0.114, 'L', 0, 1) vs length rows of walk/bike |
| Tab-cmp-education-diffcolumn | NUMERIC | PASS | Diff = Model - LTM over 72 cells | 0 violations > 0.0011 vs 0 |
| Tab-cmp-education-mileage-identity | NUMERIC | PASS | E_km - (E_T+E_L+0.1 E_T E_L) over all rows, LTM and model | max abs 0.0012 vs < 0.0035 (rounding) |
| Tab-err-Education-toursRMSE | NUMERIC | PASS | RMSE of 24 tour diffs (tab_cmp, rounded) vs tab_err Tours | 0.02628 vs 0.026 |
| Tab-err-Education-toursMax | NUMERIC | PASS | max \|tour diff\| vs tab_err Max | 0.06400 vs 0.064 |
| Tab-err-Education-lengthRMSE | NUMERIC | PASS | RMSE of 24 length diffs vs tab_err Length | 0.03456 vs 0.034 |
| Tab-err-Education-mileageRMSE | NUMERIC | PASS | RMSE of 24 mileage diffs vs tab_err Mileage | 0.02644 vs 0.026 |
| Tab-cmp-escort-diffcolumn | NUMERIC | PASS | Diff = Model - LTM over 72 cells | 0 violations > 0.0011 vs 0 |
| Tab-cmp-escort-mileage-identity | NUMERIC | PASS | E_km - (E_T+E_L+0.1 E_T E_L) over all rows, LTM and model | max abs 0.0013 vs < 0.0035 (rounding) |
| Tab-err-Escort-toursRMSE | NUMERIC | PASS | RMSE of 24 tour diffs (tab_cmp, rounded) vs tab_err Tours | 0.02143 vs 0.021 |
| Tab-err-Escort-toursMax | NUMERIC | PASS | max \|tour diff\| vs tab_err Max | 0.05800 vs 0.058 |
| Tab-err-Escort-lengthRMSE | NUMERIC | PASS | RMSE of 24 length diffs vs tab_err Length | 0.03265 vs 0.033 |
| Tab-err-Escort-mileageRMSE | NUMERIC | PASS | RMSE of 24 mileage diffs vs tab_err Mileage | 0.01713 vs 0.017 |
| Tab-cmp-shopping-diffcolumn | NUMERIC | PASS | Diff = Model - LTM over 72 cells | 0 violations > 0.0011 vs 0 |
| Tab-cmp-shopping-mileage-identity | NUMERIC | PASS | E_km - (E_T+E_L+0.1 E_T E_L) over all rows, LTM and model | max abs 0.0013 vs < 0.0035 (rounding) |
| Tab-err-Shopping-toursRMSE | NUMERIC | PASS | RMSE of 24 tour diffs (tab_cmp, rounded) vs tab_err Tours | 0.02946 vs 0.029 |
| Tab-err-Shopping-toursMax | NUMERIC | PASS | max \|tour diff\| vs tab_err Max | 0.06800 vs 0.068 |
| Tab-err-Shopping-lengthRMSE | NUMERIC | PASS | RMSE of 24 length diffs vs tab_err Length | 0.03041 vs 0.03 |
| Tab-err-Shopping-mileageRMSE | NUMERIC | PASS | RMSE of 24 mileage diffs vs tab_err Mileage | 0.02997 vs 0.03 |
| Tab-cmp-leisure-diffcolumn | NUMERIC | PASS | Diff = Model - LTM over 72 cells | 0 violations > 0.0011 vs 0 |
| Tab-cmp-leisure-mileage-identity | NUMERIC | PASS | E_km - (E_T+E_L+0.1 E_T E_L) over all rows, LTM and model | max abs 0.0012 vs < 0.0035 (rounding) |
| Tab-err-Leisure-toursRMSE | NUMERIC | PASS | RMSE of 24 tour diffs (tab_cmp, rounded) vs tab_err Tours | 0.02111 vs 0.021 |
| Tab-err-Leisure-toursMax | NUMERIC | PASS | max \|tour diff\| vs tab_err Max | 0.05700 vs 0.057 |
| Tab-err-Leisure-lengthRMSE | NUMERIC | PASS | RMSE of 24 length diffs vs tab_err Length | 0.02413 vs 0.024 |
| Tab-err-Leisure-mileageRMSE | NUMERIC | PASS | RMSE of 24 mileage diffs vs tab_err Mileage | 0.02120 vs 0.021 |
| Tab-cmp-business-diffcolumn | NUMERIC | PASS | Diff = Model - LTM over 72 cells | 0 violations > 0.0011 vs 0 |
| Tab-cmp-business-mileage-identity | NUMERIC | PASS | E_km - (E_T+E_L+0.1 E_T E_L) over all rows, LTM and model | max abs 0.0018 vs < 0.0035 (rounding) |
| Tab-err-Business-toursRMSE | NUMERIC | PASS | RMSE of 24 tour diffs (tab_cmp, rounded) vs tab_err Tours | 0.01730 vs 0.017 |
| Tab-err-Business-toursMax | NUMERIC | PASS | max \|tour diff\| vs tab_err Max | 0.03900 vs 0.039 |
| Tab-err-Business-lengthRMSE | NUMERIC | PASS | RMSE of 24 length diffs vs tab_err Length | 0.03286 vs 0.033 |
| Tab-err-Business-mileageRMSE | NUMERIC | PASS | RMSE of 24 mileage diffs vs tab_err Mileage | 0.03516 vs 0.035 |
| Abstract-rmse-min | NUMERIC | PASS | min NL tour RMSE (tab_err) vs vbestrmse | 0.01700 vs 0.017 |
| Abstract-rmse-max | NUMERIC | PASS | max NL tour RMSE vs vworstrmse | 0.02900 vs 0.029 |
| Abstract-km-min | NUMERIC | PASS | min NL mileage RMSE vs vbestkm | 0.01700 vs 0.017 |
| Abstract-km-max | NUMERIC | PASS | max NL mileage RMSE vs vworstkm | 0.03500 vs 0.035 |
| Sec5-ipdl-rmse-min | NUMERIC | PASS | IPDL min vs vipdlbestrmse | 0.00700 vs 0.007 |
| Sec5-ipdl-rmse-max | NUMERIC | PASS | IPDL max vs vipdlworstrmse | 0.02300 vs 0.023 |
| Tab-models-NL-tours-mean | NUMERIC | PASS | mean NL tour RMSE (tab_err) vs tab_models 0.022 | 0.02217 vs 0.022 |
| Tab-models-NL-mileage-mean | NUMERIC | PASS | mean NL mileage RMSE vs tab_models 0.026 (inputs rounded to 3dp; mean of rounded inputs 0.0253, upper rounding bound 0.0258) | 0.02533 vs 0.026 [consistent only if unrounded values sit near upper rounding bounds] |
| Tab-models-NL-bands-mean | NUMERIC | PASS | mean NL band RMSE vs 0.167 | 0.16667 vs 0.167 |
| Tab-models-MNL-tours-mean | NUMERIC | PASS | mean MNL tour RMSE vs 0.044 | 0.04350 vs 0.044 |
| Tab-models-IPDL-tours-mean | NUMERIC | PASS | mean IPDL tour RMSE vs 0.014 | 0.01383 vs 0.014 |
| Sec5-MNL-fits-worst | NUMERIC | PASS | MNL RMSE > NL and > IPDL in every purpose | MNL (0.042, 0.034, 0.045, 0.051, 0.034, 0.055) vs MNL worst |
| Sec5-NL-validation-bounds | NUMERIC | PASS | test-suite bounds: tours < 0.035, mileage < 0.04 | 0.029, 0.035 vs <0.035, <0.04 |
| Abstract-vkm-NL | NUMERIC | PASS | tab_scen car cost +10% NL car vkm -3.47 vs vvkmnl 3.5 | 3.47000 vs 3.5 |
| Abstract-pt-NL | NUMERIC | PASS | tab_scen PT pkm +2.51 vs vptnl 2.5 | 2.51000 vs 2.5 |
| Sec6-MNL-vkm | NUMERIC | PASS | tab_scen 3.44 vs macro 3.4 | 3.44000 vs 3.4 |
| Sec6-MNL-pt | NUMERIC | PASS | tab_scen 1.71 vs macro 1.7 | 1.71000 vs 1.7 |
| Sec6-IPDL-vkm | NUMERIC | PASS | tab_scen 3.6 vs macro 3.6 | 3.60000 vs 3.6 |
| Sec6-IPDL-pt | NUMERIC | PASS | tab_scen 2.47 vs macro 2.5 | 2.47000 vs 2.5 |
| Macro-vcvnlcross-vs-tab_models | NUMERIC | PASS | macro value equals tab_models cell (transcribed from tab_models.tex) | 0.03200 vs 0.032 |
| Macro-vcvnlown-vs-tab_models | NUMERIC | PASS | macro value equals tab_models cell (transcribed from tab_models.tex) | 0.20700 vs 0.207 |
| Macro-vcvnlall-vs-tab_models | NUMERIC | PASS | macro value equals tab_models cell (transcribed from tab_models.tex) | 0.12200 vs 0.122 |
| Macro-vcvipdlcross-vs-tab_models | NUMERIC | PASS | macro value equals tab_models cell (transcribed from tab_models.tex) | 0.02100 vs 0.021 |
| Macro-vcvipdlown-vs-tab_models | NUMERIC | PASS | macro value equals tab_models cell (transcribed from tab_models.tex) | 0.44100 vs 0.441 |
| Macro-vcvipdlall-vs-tab_models | NUMERIC | PASS | macro value equals tab_models cell (transcribed from tab_models.tex) | 0.25500 vs 0.255 |
| Macro-vcvmnlown-vs-tab_models | NUMERIC | PASS | macro value equals tab_models cell (transcribed from tab_models.tex) | 0.87300 vs 0.873 |
| Macro-vcvnlltmown-vs-tab_models | NUMERIC | PASS | macro value equals tab_models cell (transcribed from tab_models.tex) | 0.87800 vs 0.878 |
| Macro-vcvmnlall-vs-tab_models | NUMERIC | PASS | macro value equals tab_models cell (transcribed from tab_models.tex) | 0.50800 vs 0.508 |
| Tab-models-CV-all-NL | NUMERIC | PASS | all = sqrt((96 cross^2 + 48 own^2)/144) vs 'All' (n=96, n=48 from tab_nest_cv) | 0.12233 vs 0.122 |
| Tab-models-CV-all-IPDL | NUMERIC | PASS | all = sqrt((96 cross^2 + 48 own^2)/144) vs 'All' (n=96, n=48 from tab_nest_cv) | 0.25519 vs 0.255 |
| Tab-models-CV-all-MNL | NUMERIC | PASS | all = sqrt((96 cross^2 + 48 own^2)/144) vs 'All' (n=96, n=48 from tab_nest_cv) | 0.50754 vs 0.508 |
| Tab-models-CV-all-NL-LTM | NUMERIC | PASS | all = sqrt((96 cross^2 + 48 own^2)/144) vs 'All' (n=96, n=48 from tab_nest_cv) | 0.50890 vs 0.509 |
| Sec5-NL-lowest-CV | NUMERIC | PASS | NL all-target CV RMSE lowest of NL, IPDL, MNL, NL-LTM | 0.122 < 0.255, 0.508, 0.509 vs lowest |
| Sec5-IPDL-best-cross | NUMERIC | PASS | IPDL cross 0.021 < NL 0.032 | 0.021<0.032 vs IPDL best on cross |
| Sec5-NL-better-own | NUMERIC | PASS | NL own 0.207 < IPDL 0.441 | 0.207<0.441 vs NL better on own |
| Sec5-CV-folds | NUMERIC | PASS | 6 folds x 4 = 24 combos | 24 vs 24 |
| App-targets-432 | NUMERIC | PASS | targets sheet: 6 purposes x 6 modes x 4 shocks x 3 measures | 432 vs 432 |
| Eq-objective-24-combos | NUMERIC | PASS | 6 modes x 4 shocks | 24 vs 24 |
| Eq-objective-48-bands | NUMERIC | PASS | interpretation: 2 mode groups (car, PT) x 6 bands x 4 shocks; document does not state the combos | 48 vs 48 (interpretation-dependent) |
| Sec5-16-free-params | NUMERIC | PASS | theta(1)+beta(4)+phi^T(2)+phi^C-phi^T(2)+tilts(5: W,B,H,C,P)+sigma(2) | 16 vs 16 |
| Sec3-PLogsum-values | NUMERIC | PASS | text PLogsum values vs tab_struct | {'Commute': '0.918', 'Education': '0.504', 'Escort': '0.506', 'Shopping': '0.567', 'Leisure': '0.560', 'Business': '0.708'} vs {'Commute': 0.918, 'Education': 0.504, 'Escort': 0.506, 'Shopping': 0.567, 'Leisure': 0.56, 'Business': 0.708} |
| Sec5-escort-A-CV | NUMERIC | PASS | tab_struct escort LTM-structure CV RMSE vs text 1.24 | 1.23900 vs 1.24 |
| Sec5-escort-B-CV | NUMERIC | PASS | tab_struct escort default CV RMSE vs 0.27 | 0.26900 vs 0.27 |
| Sec5-theta1-escort-shopping-LTM | NUMERIC | PASS | theta=1 under LTM structure for escort and shopping | 1.000, 1.000 vs 1, 1 |
| Sec5-leisure-A-theta | NUMERIC | PASS | leisure theta under structure A vs text 0.14 | 0.13700 vs 0.14 |
| Sec5-leisure-B-theta-macro | NUMERIC | PASS | leisure default theta vs vthetaleisure | 0.75000 vs 0.75 |
| Sec5-shopping-B-theta-macro | NUMERIC | PASS | shopping default theta vs vthetashopping | 0.58800 vs 0.59 |
| Sec5-education-theta-macro | NUMERIC | PASS | education theta vs vthetaeducation | 0.15400 vs 0.15 |
| Sec5-other-five-NL-CV-range | NUMERIC | PASS | NL default CV RMSE for five non-escort purposes in [0.025, 0.083] | [0.025, 0.043, 0.083, 0.057, 0.067] vs 0.025 to 0.083 |
| Sec5-structure-text-ABs | NUMERIC | PASS | default = LTM structure for commute/education/business; differs for escort/shopping/leisure | as table vs as text |
| Sec5-leisure-B-better | NUMERIC | PASS | leisure: default CV RMSE < LTM-structure CV RMSE ('slightly better') | 0.057 vs 0.063 vs 'slightly better' |
| Sec5-theta-min | NUMERIC | PASS | min theta in tab_fit vs vthetamin | 0.15400 vs 0.15 |
| Sec5-theta-max | NUMERIC | PASS | max theta in tab_fit vs vthetamax | 0.76100 vs 0.76 |
| Sec5-money-share-car-range | NUMERIC | PASS | fitted sigma_SOV in [0.20,0.50] over six purposes | [0.2,0.5] vs 0.20 to 0.50 |
| Sec5-money-share-private-range | NUMERIC | PASS | fitted sigma_SOV, five private purposes, in [0.34,0.50] | [0.34,0.5] vs 0.34 to 0.50 |
| Sec5-prior-0.37 | NUMERIC | PASS | car prior 0.37 for the five private purposes | [0.37, 0.37, 0.37, 0.37, 0.37, 0.12] vs 0.37 |
| Sec5-time-exponent-range | NUMERIC | PASS | time exponents (car and PT) in [0.1,0.5] | [0.1,0.47] vs 0.1 to 0.5 |
| Sec5-cost-gt-time-exponent-car | NUMERIC | PASS | phi^C > phi^T for car in every purpose | [(0.58, 0.36), (0.26, 0.1), (0.48, 0.15), (0.39, 0.3), (0.51, 0.32), (0.57, 0.33)] vs all larger |
| Sec5-theta-below-one | NUMERIC | PASS | theta < 1 in every purpose | [0.761, 0.154, 0.528, 0.588, 0.75, 0.603] vs <1 |
| Sec4-aggregation-38pct | NUMERIC | PASS | (0.153-0.095)/0.153 | 0.37908 vs 0.38 |
| Sec4-rebase-commute | NUMERIC | PASS | tab_elast commute SOV car cost 2009-11 / 2023 vs text -0.155 / -0.141 | -0.155, -0.141 vs -0.155, -0.141 |
| Sec4-rebase-leisure | NUMERIC | PASS | leisure vs text -0.202 / -0.221 | -0.202, -0.221 vs -0.202, -0.221 |
| Sec4-rebase-5-of-6 | NUMERIC | PASS | number of purposes with \|SOV car-cost elasticity\| lower in 2023 than 2009-11 | 5: ['Commute', 'Education', 'Escort', 'Shopping', 'Business'] vs 5 of 6, leisure exception |
| Sec6-burden-share-Q1 | NUMERIC | PASS | 867 DKK / 173,000 DKK mean personal income Q1 2023 (percent) | 0.50116 vs 0.5 |
| Sec6-burden-share-Q5 | NUMERIC | PASS | 1291 DKK / 549,000 DKK personal income Q5 (percent) | 0.23515 vs 0.24 |
| Sec6-burden-twice | NUMERIC | PASS | ratio of burden shares Q1/Q5 'about twice' | 2.13117 vs 2.0 |
| Sec6-burden-rises-with-cars | NUMERIC | PASS | no car < one car < two+ in every quintile | [(50.0, 520.0, 867.0), (78.0, 660.0, 1138.0), (68.0, 743.0, 1311.0), (75.0, 697.0, 1324.0), (64.0, 525.0, 1291.0)] vs rising |
| Sec6-burden-macros | NUMERIC | PASS | macros vburdenqone, vburdenqfive vs tab_dist two+ column | 867.0, 1291.0 vs 867, 1291 |
| Eq-lm-normal-eq | IDENTITY | PASS | \|grad_d 1/2\|\|r+J d\|\|^2 - (J'J d + J'r)\|^2 (nu=0 limit of eq:lm) | 0 vs 0 |
| Eq-ownership | IDENTITY | PASS | softmax of A_k - gamma k K w re-evaluated at K' minus eq:ownership (k=0,1,2) | [0, 0, 0] vs 0 |
| Sec6-earlier-form-lambda1 | SERIES | PASS | series of beta ln(Y-kK) in K to O(K) minus (beta ln Y - beta k K/Y): sensitivity ~ Y^{-1}, i.e. lambda=1 | 0 vs 0 |
| Sec6-earlier-form-homogeneous | IDENTITY | PASS | U_k-U_0 at (tY,tK) minus at (Y,K): depends only on K/Y | 0 vs 0 |
| Sec6-ownership-local-elast-Q1 | NUMERIC | PASS | local elasticity -gamma K w_q Var_q(k)/E_q(k), Q1; gamma calibrated to aggregate -0.4 (lambda=0.37, Ybar person-weighted 2023, tab_income 2023 shares) | -1.06200 vs -1.07 |
| Sec6-ownership-local-elast-Q5 | NUMERIC | PASS | same, Q5 | -0.19884 vs -0.2 |
| Sec6-ownership-10pct-4.02 | NUMERIC | PASS | percent fall in person-weighted household car count for K -> 1.1 K with gamma calibrated to -0.4 | 4.02645 vs 4.02 |

## Rendered equations

### Eq-shrink-sums-to-one

```
  Eq-shrink-sums-to-one
    A         
   ___        
   ╲          
    ╲         
    ╱   w̃ₐ = 1
   ╱          
   ‾‾‾        
  a = 1       
```

### Eq-shrink-limits

```
  Eq-shrink-limits
      κ⋅wb + n⋅wh
  w̃ = ───────────
         κ + n   
```

### Sec2-shrink-n300-keeps-91pct

```
  Sec2-shrink-n300-keeps-91pct
         10
  keep = ──
         11
```

### Sec2-shrink-n10-keeps-25pct

```
  Sec2-shrink-n10-keeps-25pct
  keep = 1/4
```

### Sec4-VoT-top-band-midpoint

```
  Sec4-VoT-top-band-midpoint
         5⋅L
  mₜₒₚ = ───
          4 
```

### Eq-walkbike-kappaW

```
  Eq-walkbike-kappaW
        30⋅β_bar
  κ_W = ────────
           v    
```

### Eq-walkbike-kappaB

```
  Eq-walkbike-kappaB
        30⋅β_bar
  κ_B = ────────
           v    
```

### Eq-nlresp

```
  Eq-nlresp
                                                                             ↪
                                                        θ ⎛ d₁⋅x₁     d₂⋅x₂  ↪
                                               (x₁ + x₂) ⋅⎜─────── + ─────── ↪
                                                          ⎝x₁ + x₂   x₁ + x₂ ↪
  P1(n) = ────────────────────────────────────────────────────────────────── ↪
                                  ⎛                                          ↪
                                  ⎜                                          ↪
                                  ⎜         θ   θ                            ↪
          ⎛       θ            θ⎞ ⎜       d₃ ⋅x₃                    v₀       ↪
          ⎝v₀ + x₃  + (x₁ + x₂) ⎠⋅⎜───────────────────── + ───────────────── ↪
                                  ⎜       θ            θ          θ          ↪
                                  ⎝v₀ + x₃  + (x₁ + x₂)    v₀ + x₃  + (x₁ +  ↪
  
  ↪  θ                                     
  ↪ ⎞                                      
  ↪ ⎟                                      
  ↪ ⎠                                      
  ↪ ───────────────────────────────────────
  ↪                                      θ⎞
  ↪                 θ ⎛ d₁⋅x₁     d₂⋅x₂ ⎞ ⎟
  ↪        (x₁ + x₂) ⋅⎜─────── + ───────⎟ ⎟
  ↪                   ⎝x₁ + x₂   x₁ + x₂⎠ ⎟
  ↪ ──── + ───────────────────────────────⎟
  ↪    θ               θ            θ     ⎟
  ↪ x₂)         v₀ + x₃  + (x₁ + x₂)      ⎠
```

### Eq-nlresp-theta1-MNL

```
  Eq-nlresp-theta1-MNL
                    d₁⋅x₁           
  P1(a) = ──────────────────────────
          d₁⋅x₁ + d₂⋅x₂ + d₃⋅x₃ + v₀
```

### Sec3-notour-mass

```
  Sec3-notour-mass
                  N⋅s₀         
  P0(0) = ─────────────────────
                   ⎛ N⋅s₀     ⎞
          (1 - s₀)⋅⎜────── + N⎟
                   ⎝1 - s₀    ⎠
```

### Sec3-notour-tours

```
  Sec3-notour-tours
                ⎛ N⋅s₀     ⎞
  T₀ = (1 - s₀)⋅⎜────── + N⎟
                ⎝1 - s₀    ⎠
```

### Eq-moneyshare-odds

```
  Eq-moneyshare-odds
                    C⋅s              
  o = ───────────────────────────────
        ⎛C⋅s    ⎞ ⎛      C⋅s        ⎞
      v⋅⎜─── + T⎟⋅⎜- ─────────── + 1⎟
        ⎝ v     ⎠ ⎜    ⎛C⋅s    ⎞    ⎟
                  ⎜  v⋅⎜─── + T⎟    ⎟
                  ⎝    ⎝ v     ⎠    ⎠
```

### Eq-gtratio

```
  Eq-gtratio
         C⋅s⋅(x_c + 1)             
         ───────────── + T⋅(xₜ + 1)
               v                   
  G'/G = ──────────────────────────
                  C⋅s              
                  ─── + T          
                   v               
```

### Eq-nlshift-phi0-sign

```
  Eq-nlshift-phi0-sign
                    ⎛C⋅s⋅(x_c + 1)             ⎞
                    ⎜───────────── + T⋅(xₜ + 1)⎟
                    ⎜      v                   ⎟
  Δₐ₍ₚₕᵢ₌₀₎ = -β⋅log⎜──────────────────────────⎟
                    ⎜         C⋅s              ⎟
                    ⎜         ─── + T          ⎟
                    ⎝          v               ⎠
```

### Eq-nlshift-phi0-consistent

```
  Eq-nlshift-phi0-consistent
             ⎛C⋅s⋅(x_c + 1)             ⎞
             ⎜───────────── + T⋅(xₜ + 1)⎟
             ⎜      v                   ⎟
  Δₐ = -β⋅log⎜──────────────────────────⎟
             ⎜         C⋅s              ⎟
             ⎜         ─── + T          ⎟
             ⎝          v               ⎠
```

### Eq-ipdl-sign-vs-nlshift

```
  Eq-ipdl-sign-vs-nlshift
                       ⎛C⋅s⋅(x_c + 1)             ⎞
                       ⎜───────────── + T⋅(xₜ + 1)⎟
                       ⎜      v                   ⎟
  Delta delta_j = β⋅log⎜──────────────────────────⎟
                       ⎜         C⋅s              ⎟
                       ⎜         ─── + T          ⎟
                       ⎝          v               ⎠
```

### Eq-odds-shared

```
  Eq-odds-shared
  oₘ = o_S⋅s
```

### Eq-moneyshare-inverse

```
  Eq-moneyshare-inverse
               sg          
  σ = ─────────────────────
               ⎛  sg      ⎞
      (1 - sg)⋅⎜────── + 1⎟
               ⎝1 - sg    ⎠
```

### Tab-cs-Commute-HOV

```
  Tab-cs-Commute-HOV
           1   
  s_H = ───────
        L_H + 1
```

### Tab-cs-Commute-CP

```
  Tab-cs-Commute-CP
               1   
        1 - ───────
            L_C + 1
  s_C = ───────────
        Max(1, L_C)
```

### Tab-cs-Education-HOV

```
  Tab-cs-Education-HOV
           1   
  s_H = ───────
        L_H + 1
```

### Tab-cs-Education-CP

```
  Tab-cs-Education-CP
               1   
        1 - ───────
            L_C + 1
  s_C = ───────────
        Max(1, L_C)
```

### Tab-cs-Escort-HOV

```
  Tab-cs-Escort-HOV
           1   
  s_H = ───────
        L_H + 1
```

### Tab-cs-Escort-CP

```
  Tab-cs-Escort-CP
               1   
        1 - ───────
            L_C + 1
  s_C = ───────────
        Max(1, L_C)
```

### Tab-cs-Shopping-HOV

```
  Tab-cs-Shopping-HOV
           1   
  s_H = ───────
        L_H + 1
```

### Tab-cs-Shopping-CP

```
  Tab-cs-Shopping-CP
               1   
        1 - ───────
            L_C + 1
  s_C = ───────────
        Max(1, L_C)
```

### Tab-cs-Leisure-HOV

```
  Tab-cs-Leisure-HOV
           1   
  s_H = ───────
        L_H + 1
```

### Tab-cs-Leisure-CP

```
  Tab-cs-Leisure-CP
               1   
        1 - ───────
            L_C + 1
  s_C = ───────────
        Max(1, L_C)
```

### Tab-cs-Business-HOV

```
  Tab-cs-Business-HOV
           1   
  s_H = ───────
        L_H + 1
```

### Tab-cs-Business-CP

```
  Tab-cs-Business-CP
               1   
        1 - ───────
            L_C + 1
  s_C = ───────────
        Max(1, L_C)
```

### Eq-r-car

```
  Eq-r-car
          104
  r_car = ───
          133
```

### Eq-r-cost-growth

```
  Eq-r-cost-growth
                    544
  gamma23/gamma10 = ───
                    581
```

### Eq-burden-fare-fixed

```
  Eq-burden-fare-fixed
  fare_fixed = 131/5
```

### Eq-votinterp-left

```
  Eq-votinterp-left
  v(mₙ₎ = vₙ
```

### Eq-votinterp-right

```
  Eq-votinterp-right
  v(mₙ₊₁₎ = vₙ₁
```

### Tab-vot-odds-scale

```
  Tab-vot-odds-scale
  scale_q*v_q/r = v(ybar)
```

### Tab-vot-rho

```
  Tab-vot-rho
  y_q/rho_q = y̅
```

### Eq-cellodds-monotone

```
  Eq-cellodds-monotone
          r_car⋅v(ybar)
  scale = ─────────────
          v(ybar rho_q)
```

### Sec4-ybar-cpi

```
  Sec4-ybar-cpi
  y̅_2023prices = 320.451
```

### Tab-income-shares-sum100

```
  Tab-income-shares-sum100
  sumₛₕₐᵣₑₛ = 100
```

### Tab-income-householdcars

```
  Tab-income-householdcars
         one   two
  cars = ─── + ───
         100   50 
```

### Tab-income-elasticity-2009-11

```
  Tab-income-elasticity-2009-11
           ⎛c₅⎞
        log⎜──⎟
           ⎝c₁⎠
  eps = ───────
           ⎛y₅⎞
        log⎜──⎟
           ⎝y₁⎠
```

### Tab-income-elasticity-2023

```
  Tab-income-elasticity-2023
           ⎛c₅⎞
        log⎜──⎟
           ⎝c₁⎠
  eps = ───────
           ⎛y₅⎞
        log⎜──⎟
           ⎝y₁⎠
```

### Sec2-nocar-Q1-2023

```
  Sec2-nocar-Q1-2023
  none_Q1 = 40.5
```

### Sec2-nocar-Q5-2023

```
  Sec2-nocar-Q5-2023
  none_Q5 = 4.4
```

### Sec2-cars-Q1-2023

```
  Sec2-cars-Q1-2023
  cars_Q1 = 0.67
```

### Sec2-cars-Q5-2023

```
  Sec2-cars-Q5-2023
  cars_Q5 = 1.59
```

### Sec2-elasticity-decline

```
  Sec2-elasticity-decline
  eps₂₃ = 0.46
```

### Tab-base-row-sums

```
  Tab-base-row-sums
  sum_modes = All
```

### Tab-base-col-sums

```
  Tab-base-col-sums
  sumₚᵤᵣₚₒₛₑₛ = All
```

### Sec2-vtours

```
  Sec2-vtours
              637
  toursₘᵢₗₗ = ───
              100
```

### Tab-base-mean-km

```
  Tab-base-mean-km
  meanₖₘ = 28.85
```

### Eq-ipdl-mu0-MNL

```
  Eq-ipdl-mu0-MNL
  δ_j = μ₁⋅log(s_g) + μ₂⋅log(s_g) + μ₃⋅log(s_g) + μ₄⋅log(s_g) + (-μ₁ - μ₂ -  ↪
  
  ↪ μ₃ - μ₄ + 1)⋅log(s_j) - log(s₀)
```

### Eq-ipdl-one-dim-Berry

```
  Eq-ipdl-one-dim-Berry
  δ_j = μ₁⋅log(s_g) + (1 - μ₁)⋅log(s_j) - log(s₀)
```

### Eq-length-arc

```
  Eq-length-arc
      η         
  ⎛11⎞    E     
  ⎜──⎟  = ── + 1
  ⎝10⎠    10    
```

### Sec5-mileage-arc-product

```
  Sec5-mileage-arc-product
        E_L⋅E_T            
  Eₖₘ = ─────── + E_L + E_T
          10               
```

### Tab-cmp-commute-diffcolumn

```
  Tab-cmp-commute-diffcolumn
  Diff = -LTM + Model
```

### Tab-cmp-commute-mileage-identity

```
  Tab-cmp-commute-mileage-identity
        E_L⋅E_T            
  Eₖₘ = ─────── + E_L + E_T
          10               
```

### Tab-err-Commute-toursRMSE

```
  Tab-err-Commute-toursRMSE
  RMSE_T = 0.0194
```

### Tab-err-Commute-toursMax

```
  Tab-err-Commute-toursMax
  max_T = 0.045
```

### Tab-err-Commute-lengthRMSE

```
  Tab-err-Commute-lengthRMSE
  RMSE_L = 0.03684
```

### Tab-err-Commute-mileageRMSE

```
  Tab-err-Commute-mileageRMSE
  RMSE_K = 0.02299
```

### Sec5-commute-walk-LTM-length-0.041

```
  Sec5-commute-walk-LTM-length-0.041
  E_L_walk = 0.041
```

### Sec5-commute-bike-LTM-length-0.058

```
  Sec5-commute-bike-LTM-length-0.058
  E_L_bike = 0.058
```

### Sec5-model-walk-bike-shorter

```
  Sec5-model-walk-bike-shorter
  E_L_bike_model = 0.004
```

### Sec5-largest-diff-length-walkbike

```
  Sec5-largest-diff-length-walkbike
  max_diff = 0.114
```

### Tab-cmp-education-diffcolumn

```
  Tab-cmp-education-diffcolumn
  Diff = -LTM + Model
```

### Tab-cmp-education-mileage-identity

```
  Tab-cmp-education-mileage-identity
        E_L⋅E_T            
  Eₖₘ = ─────── + E_L + E_T
          10               
```

### Tab-err-Education-toursRMSE

```
  Tab-err-Education-toursRMSE
  RMSE_T = 0.02628
```

### Tab-err-Education-toursMax

```
  Tab-err-Education-toursMax
  max_T = 0.064
```

### Tab-err-Education-lengthRMSE

```
  Tab-err-Education-lengthRMSE
  RMSE_L = 0.03456
```

### Tab-err-Education-mileageRMSE

```
  Tab-err-Education-mileageRMSE
  RMSE_K = 0.02644
```

### Tab-cmp-escort-diffcolumn

```
  Tab-cmp-escort-diffcolumn
  Diff = -LTM + Model
```

### Tab-cmp-escort-mileage-identity

```
  Tab-cmp-escort-mileage-identity
        E_L⋅E_T            
  Eₖₘ = ─────── + E_L + E_T
          10               
```

### Tab-err-Escort-toursRMSE

```
  Tab-err-Escort-toursRMSE
  RMSE_T = 0.02143
```

### Tab-err-Escort-toursMax

```
  Tab-err-Escort-toursMax
  max_T = 0.058
```

### Tab-err-Escort-lengthRMSE

```
  Tab-err-Escort-lengthRMSE
  RMSE_L = 0.03265
```

### Tab-err-Escort-mileageRMSE

```
  Tab-err-Escort-mileageRMSE
  RMSE_K = 0.01713
```

### Tab-cmp-shopping-diffcolumn

```
  Tab-cmp-shopping-diffcolumn
  Diff = -LTM + Model
```

### Tab-cmp-shopping-mileage-identity

```
  Tab-cmp-shopping-mileage-identity
        E_L⋅E_T            
  Eₖₘ = ─────── + E_L + E_T
          10               
```

### Tab-err-Shopping-toursRMSE

```
  Tab-err-Shopping-toursRMSE
  RMSE_T = 0.02946
```

### Tab-err-Shopping-toursMax

```
  Tab-err-Shopping-toursMax
  max_T = 0.068
```

### Tab-err-Shopping-lengthRMSE

```
  Tab-err-Shopping-lengthRMSE
  RMSE_L = 0.03041
```

### Tab-err-Shopping-mileageRMSE

```
  Tab-err-Shopping-mileageRMSE
  RMSE_K = 0.02997
```

### Tab-cmp-leisure-diffcolumn

```
  Tab-cmp-leisure-diffcolumn
  Diff = -LTM + Model
```

### Tab-cmp-leisure-mileage-identity

```
  Tab-cmp-leisure-mileage-identity
        E_L⋅E_T            
  Eₖₘ = ─────── + E_L + E_T
          10               
```

### Tab-err-Leisure-toursRMSE

```
  Tab-err-Leisure-toursRMSE
  RMSE_T = 0.02111
```

### Tab-err-Leisure-toursMax

```
  Tab-err-Leisure-toursMax
  max_T = 0.057
```

### Tab-err-Leisure-lengthRMSE

```
  Tab-err-Leisure-lengthRMSE
  RMSE_L = 0.02413
```

### Tab-err-Leisure-mileageRMSE

```
  Tab-err-Leisure-mileageRMSE
  RMSE_K = 0.0212
```

### Tab-cmp-business-diffcolumn

```
  Tab-cmp-business-diffcolumn
  Diff = -LTM + Model
```

### Tab-cmp-business-mileage-identity

```
  Tab-cmp-business-mileage-identity
        E_L⋅E_T            
  Eₖₘ = ─────── + E_L + E_T
          10               
```

### Tab-err-Business-toursRMSE

```
  Tab-err-Business-toursRMSE
  RMSE_T = 0.0173
```

### Tab-err-Business-toursMax

```
  Tab-err-Business-toursMax
  max_T = 0.039
```

### Tab-err-Business-lengthRMSE

```
  Tab-err-Business-lengthRMSE
  RMSE_L = 0.03286
```

### Tab-err-Business-mileageRMSE

```
  Tab-err-Business-mileageRMSE
  RMSE_K = 0.03516
```

### Abstract-rmse-min

```
  Abstract-rmse-min
  rmseₘᵢₙ = 0.017
```

### Abstract-rmse-max

```
  Abstract-rmse-max
  rmseₘₐₓ = 0.029
```

### Abstract-km-min

```
  Abstract-km-min
  kmₘᵢₙ = 0.017
```

### Abstract-km-max

```
  Abstract-km-max
  kmₘₐₓ = 0.035
```

### Sec5-ipdl-rmse-min

```
  Sec5-ipdl-rmse-min
  ipdlₘᵢₙ = 0.007
```

### Sec5-ipdl-rmse-max

```
  Sec5-ipdl-rmse-max
  ipdlₘₐₓ = 0.023
```

### Tab-models-NL-tours-mean

```
  Tab-models-NL-tours-mean
  mean_T = 0.02217
```

### Tab-models-NL-mileage-mean

```
  Tab-models-NL-mileage-mean
  mean_K = 0.02533
```

### Tab-models-NL-bands-mean

```
  Tab-models-NL-bands-mean
  mean_B = 0.1667
```

### Tab-models-MNL-tours-mean

```
  Tab-models-MNL-tours-mean
  mean_MNL = 0.0435
```

### Tab-models-IPDL-tours-mean

```
  Tab-models-IPDL-tours-mean
  mean_IPDL = 0.01383
```

### Sec5-MNL-fits-worst

```
  Sec5-MNL-fits-worst
  MNL = worst
```

### Sec5-NL-validation-bounds

```
  Sec5-NL-validation-bounds
  max = 0.029
```

### Abstract-vkm-NL

```
  Abstract-vkm-NL
  vkm = 3.47
```

### Abstract-pt-NL

```
  Abstract-pt-NL
  pt = 2.51
```

### Sec6-MNL-vkm

```
  Sec6-MNL-vkm
  MNL-vkm = 3.44
```

### Sec6-MNL-pt

```
  Sec6-MNL-pt
  MNL-pt = 1.71
```

### Sec6-IPDL-vkm

```
  Sec6-IPDL-vkm
  IPDL-vkm = 3.6
```

### Sec6-IPDL-pt

```
  Sec6-IPDL-pt
  IPDL-pt = 2.47
```

### Macro-vcvnlcross-vs-tab_models

```
  Macro-vcvnlcross-vs-tab_models
  vcvnlcross = 0.032
```

### Macro-vcvnlown-vs-tab_models

```
  Macro-vcvnlown-vs-tab_models
  vcvnlown = 0.207
```

### Macro-vcvnlall-vs-tab_models

```
  Macro-vcvnlall-vs-tab_models
  vcvnlall = 0.122
```

### Macro-vcvipdlcross-vs-tab_models

```
  Macro-vcvipdlcross-vs-tab_models
  vcvipdlcross = 0.021
```

### Macro-vcvipdlown-vs-tab_models

```
  Macro-vcvipdlown-vs-tab_models
  vcvipdlown = 0.441
```

### Macro-vcvipdlall-vs-tab_models

```
  Macro-vcvipdlall-vs-tab_models
  vcvipdlall = 0.255
```

### Macro-vcvmnlown-vs-tab_models

```
  Macro-vcvmnlown-vs-tab_models
  vcvmnlown = 0.873
```

### Macro-vcvnlltmown-vs-tab_models

```
  Macro-vcvnlltmown-vs-tab_models
  vcvnlltmown = 0.878
```

### Macro-vcvmnlall-vs-tab_models

```
  Macro-vcvmnlall-vs-tab_models
  vcvmnlall = 0.508
```

### Tab-models-CV-all-NL

```
  Tab-models-CV-all-NL
                 ___________________________
                ╱             2           2 
               ╱  2⋅RMSE_cross    RMSE_own  
  RMSEₐₗₗ =   ╱   ───────────── + ───────── 
            ╲╱          3             3     
```

### Tab-models-CV-all-IPDL

```
  Tab-models-CV-all-IPDL
                 ___________________________
                ╱             2           2 
               ╱  2⋅RMSE_cross    RMSE_own  
  RMSEₐₗₗ =   ╱   ───────────── + ───────── 
            ╲╱          3             3     
```

### Tab-models-CV-all-MNL

```
  Tab-models-CV-all-MNL
                 ___________________________
                ╱             2           2 
               ╱  2⋅RMSE_cross    RMSE_own  
  RMSEₐₗₗ =   ╱   ───────────── + ───────── 
            ╲╱          3             3     
```

### Tab-models-CV-all-NL-LTM

```
  Tab-models-CV-all-NL-LTM
                 ___________________________
                ╱             2           2 
               ╱  2⋅RMSE_cross    RMSE_own  
  RMSEₐₗₗ =   ╱   ───────────── + ───────── 
            ╲╱          3             3     
```

### Sec5-NL-lowest-CV

```
  Sec5-NL-lowest-CV
  CV_NL = 0.122
```

### Sec5-IPDL-best-cross

```
  Sec5-IPDL-best-cross
  x = 0.021
```

### Sec5-NL-better-own

```
  Sec5-NL-better-own
  x = 0.207
```

### Sec5-CV-folds

```
  Sec5-CV-folds
  folds = 24
```

### App-targets-432

```
  App-targets-432
  targets = 432
```

### Eq-objective-24-combos

```
  Eq-objective-24-combos
  combos = 24
```

### Eq-objective-48-bands

```
  Eq-objective-48-bands
  bandtargets = 48
```

### Sec5-16-free-params

```
  Sec5-16-free-params
  params = 16
```

### Sec3-PLogsum-values

```
  Sec3-PLogsum-values
  PLogsum = table
```

### Sec5-escort-A-CV

```
  Sec5-escort-A-CV
  cv_A = 1.24
```

### Sec5-escort-B-CV

```
  Sec5-escort-B-CV
  cv_B = 0.269
```

### Sec5-theta1-escort-shopping-LTM

```
  Sec5-theta1-escort-shopping-LTM
  θ = 1
```

### Sec5-leisure-A-theta

```
  Sec5-leisure-A-theta
  θ_A = 0.137
```

### Sec5-leisure-B-theta-macro

```
  Sec5-leisure-B-theta-macro
  θ_B = 0.75
```

### Sec5-shopping-B-theta-macro

```
  Sec5-shopping-B-theta-macro
  θ = 0.588
```

### Sec5-education-theta-macro

```
  Sec5-education-theta-macro
  θ = 0.154
```

### Sec5-other-five-NL-CV-range

```
  Sec5-other-five-NL-CV-range
  range = 0.025..0.083
```

### Sec5-structure-text-ABs

```
  Sec5-structure-text-ABs
  struct = ok
```

### Sec5-leisure-B-better

```
  Sec5-leisure-B-better
  cv = ok
```

### Sec5-theta-min

```
  Sec5-theta-min
  θₘᵢₙ = 0.154
```

### Sec5-theta-max

```
  Sec5-theta-max
  θₘₐₓ = 0.761
```

### Sec5-money-share-car-range

```
  Sec5-money-share-car-range
  σ_S = range
```

### Sec5-money-share-private-range

```
  Sec5-money-share-private-range
  σ_S = range
```

### Sec5-prior-0.37

```
  Sec5-prior-0.37
  π = 0.37
```

### Sec5-time-exponent-range

```
  Sec5-time-exponent-range
  phiT = range
```

### Sec5-cost-gt-time-exponent-car

```
  Sec5-cost-gt-time-exponent-car
  phiC = phiT
```

### Sec5-theta-below-one

```
  Sec5-theta-below-one
  θ = lt₁
```

### Sec4-aggregation-38pct

```
  Sec4-aggregation-38pct
         58 
  drop = ───
         153
```

### Sec4-rebase-commute

```
  Sec4-rebase-commute
  E = -0.141
```

### Sec4-rebase-leisure

```
  Sec4-rebase-leisure
  E = -0.221
```

### Sec4-rebase-5-of-6

```
  Sec4-rebase-5-of-6
  count = 5
```

### Sec6-burden-share-Q1

```
  Sec6-burden-share-Q1
             867 
  share_Q1 = ────
             1730
```

### Sec6-burden-share-Q5

```
  Sec6-burden-share-Q5
             1291
  share_Q5 = ────
             5490
```

### Sec6-burden-twice

```
  Sec6-burden-twice
          475983
  ratio = ──────
          223343
```

### Sec6-burden-rises-with-cars

```
  Sec6-burden-rises-with-cars
  B₀ = B₁
```

### Sec6-burden-macros

```
  Sec6-burden-macros
  B = 867.0
```

### Eq-lm-normal-eq

```
  Eq-lm-normal-eq
  ⎡          ⎛   2      2⎞                               ⎤                   ↪
  ⎢   Dtheta⋅⎝j₁₁  + j₂₁ ⎠     Dtheta⋅(j₁₁⋅j₁₂ + j₂₁⋅j₂₂)⎥   ⎡-j₁₁⋅r₁ - j₂₁⋅ ↪
  ⎢                                                      ⎥ = ⎢               ↪
  ⎢                                      ⎛   2      2⎞   ⎥   ⎣-j₁₂⋅r₁ - j₂₂⋅ ↪
  ⎣Dtheta⋅(j₁₁⋅j₁₂ + j₂₁⋅j₂₂)     Dtheta⋅⎝j₁₂  + j₂₂ ⎠   ⎦                   ↪
  
  ↪    
  ↪ r₂⎤
  ↪   ⎥
  ↪ r₂⎦
  ↪    
```

### Eq-ownership

```
  Eq-ownership
                                                                     -γ⋅w⋅(- ↪
                                                                    ℯ        ↪
  P'_qk = ────────────────────────────────────────────────────────────────── ↪
          ⎛                A₀                      -γ⋅w⋅(-K + Kp)  A₁ - K⋅γ⋅ ↪
          ⎜               ℯ                       ℯ              ⋅ℯ          ↪
          ⎜───────────────────────────────── + ───────────────────────────── ↪
          ⎜ A₀    A₁ - K⋅γ⋅w    A₂ - 2⋅K⋅γ⋅w    A₀    A₁ - K⋅γ⋅w    A₂ - 2⋅K ↪
          ⎝ℯ   + ℯ           + ℯ               ℯ   + ℯ           + ℯ         ↪
  
  ↪ K + Kp)  A₁ - K⋅γ⋅w                                                      ↪
  ↪        ⋅ℯ                                                                ↪
  ↪ ──────────────────────────────────────────────────────────────────────── ↪
  ↪ w        -2⋅γ⋅w⋅(-K + Kp)  A₂ - 2⋅K⋅γ⋅w ⎞                                ↪
  ↪         ℯ                ⋅ℯ             ⎟ ⎛ A₀    A₁ - K⋅γ⋅w    A₂ - 2⋅K ↪
  ↪ ──── + ─────────────────────────────────⎟⋅⎝ℯ   + ℯ           + ℯ         ↪
  ↪ ⋅γ⋅w    A₀    A₁ - K⋅γ⋅w    A₂ - 2⋅K⋅γ⋅w⎟                                ↪
  ↪        ℯ   + ℯ           + ℯ            ⎠                                ↪
  
  ↪      
  ↪      
  ↪ ─────
  ↪      
  ↪ ⋅γ⋅w⎞
  ↪     ⎠
  ↪      
  ↪      
```

### Sec6-earlier-form-lambda1

```
  Sec6-earlier-form-lambda1
        K⋅β⋅k           
  U = - ───── + β⋅log(Y)
          Y             
```

### Sec6-earlier-form-homogeneous

```
  Sec6-earlier-form-homogeneous
                 ⎛  K⋅k    ⎞
  U_k-U_0 = β⋅log⎜- ─── + 1⎟
                 ⎝   Y     ⎠
```

### Sec6-ownership-local-elast-Q1

```
  Sec6-ownership-local-elast-Q1
           -K⋅Var⋅γ⋅w 
  eps_Q1 = ───────────
              Mean    
```

### Sec6-ownership-local-elast-Q5

```
  Sec6-ownership-local-elast-Q5
  eps_Q5 = -0.199
```

### Sec6-ownership-10pct-4.02

```
  Sec6-ownership-10pct-4.02
  dQ = -4.026
```

## Failures

### Eq-nlshift-phi0-sign (FAIL)

- As written: Eq. (nlshift) with phi=0 gives Delta_a = -beta ln(G'/G); the text below it says 'the utility changes by beta ln(G'/G) at every length'.
- SymPy translation: Delta_a at phi=0 from eq:nlshift minus text claim 'utility changes by +beta ln(G'/G)'
- Got vs stated: -log(((C*s*(x_c + 1) + T*v*(x_t + 1))/(C*s + T*v))**(2*beta)) vs 0
- Rendered:
```
  Eq-nlshift-phi0-sign
                    ⎛C⋅s⋅(x_c + 1)             ⎞
                    ⎜───────────── + T⋅(xₜ + 1)⎟
                    ⎜      v                   ⎟
  Δₐ₍ₚₕᵢ₌₀₎ = -β⋅log⎜──────────────────────────⎟
                    ⎜         C⋅s              ⎟
                    ⎜         ─── + T          ⎟
                    ⎝          v               ⎠
```
- Discrepancy / likely cause: Equation and prose carry opposite signs. With beta>0 (as the calibration section requires) the equation is the economically sensible one (higher generalized time lowers utility). Most likely the prose should read 'by -beta ln(G'/G)' or 'falls by beta ln(G'/G)'. Not a translation problem.

### Eq-ipdl-sign-vs-nlshift (FAIL)

- As written: Eq. (ipdl): Delta delta_j = +beta_j ln(G'/G); Eq. (nlshift): Delta_a = -beta_j[...] and Sec. calibration states beta_j = exp(b_j) > 0 for the NL/MNL.
- SymPy translation: Delta delta_j (eq:ipdl) = +beta ln(G'/G) minus Delta_a at phi=0 (eq:nlshift) with the same beta; difference should vanish if the sign convention is shared
- Got vs stated: log(((C*s*(x_c + 1) + T*v*(x_t + 1))/(C*s + T*v))**(2*beta)) vs 0
- Rendered:
```
  Eq-ipdl-sign-vs-nlshift
                       ⎛C⋅s⋅(x_c + 1)             ⎞
                       ⎜───────────── + T⋅(xₜ + 1)⎟
                       ⎜      v                   ⎟
  Delta delta_j = β⋅log⎜──────────────────────────⎟
                       ⎜         C⋅s              ⎟
                       ⎜         ─── + T          ⎟
                       ⎝          v               ⎠
```
- Discrepancy / likely cause: If the same beta_j>0 is meant in the IPDL, a rise in generalized time would raise utility. Either IPDL beta_j is negative by convention (then say so) or the IPDL equation is missing a minus sign. The document does not state the IPDL sign convention, so this may be an omission rather than a math error.

### Sec5-model-walk-bike-shorter (FAIL)

- As written: 'LTM lets these tours become longer ... by 0.041 and 0.058 for car cost, whereas the model lets them become slightly shorter.'
- SymPy translation: text: model lets walk and bike tours 'become slightly shorter' (model length elasticity to car cost < 0 for both)
- Got vs stated: walk -0.026, bike 0.004 vs both negative
- Rendered:
```
  Sec5-model-walk-bike-shorter
  E_L_bike_model = 0.004
```
- Discrepancy / likely cause: tab_cmp_commute gives model length elasticities of -0.026 (walk) but +0.004 (bike) to car cost. Walk is shorter; bike is essentially unchanged (slightly longer). Text should say 'shorter or unchanged' or 'about zero for bike'. Table and text disagree; real (minor) wording error.

### Near-misses that passed only under a stated rounding tolerance

- `Eq-walkbike-kappaW`: exact value 60/(2*5)*mean(0.156, 0.091) = 0.741, text says 0.742. Within propagation of 3-dp input rounding (tolerance 0.003). Likely unrounded LTM coefficients.
- `Tab-models-NL-mileage-mean`: mean of the six rounded mileage RMSEs in tab_err is 0.0253, tab_models shows 0.026. Reachable only if the unrounded values are near their upper rounding bounds (max mean 0.0258); worth a glance at report_tables.js.
- `Sec3-mileage-arc-product` is an identity for the arc form (1+.1E_km = (1+.1E_T)(1+.1E_L)); the text says 'the mileage elasticity is the product of the tour and length elasticities', which is true only for the growth factors, not the elasticities (differs by the cross term 0.1 E_T E_L). Passed as an identity; the prose is loose.
- `Eq-objective-48-bands`: the count 48 holds if it means {car, PT} x 6 bands x 4 shocks; the document does not define which mode set.

## Not machine-checkable

- Sec2 income medians 693 and 706 thousand DKK: empirical statistic from TU microdata not in the generated files
- Sec2 'between 30% and 47% of sessions lack income': survey statistic, no data in document
- Sec2 weights rescaling, pooling of years: data definition
- Sec3.1 grids: 40+4x12+16 intervals; top band closed at 300+8(mean-300): modelling assumption; no claim to verify
- Eq-nodes (sum_u omega=1, sum omega*l = mean length): definition/constraint on the weights; existence of r_cjb for any mean in the band is a numerical fit, not an identity
- Eq-walkbike exponent eta 'mean 0.93 supports eq': empirical calibration output not in generated files; 'supports' is interpretation
- Eq-nlprob (nested logit probabilities): definition of the model (derivation of eq:nlresp from it is checked)
- Intuition paragraph after eq:nlresp, structure A/B discussion: verbal reasoning
- Eq-gt (G_j definition), eq:costshare formulas: definitions (costshare numeric values are checked against tab_cs using load factors reused from the earlier run)
- Sec3.2 'exponent of cost part larger because speed higher on long tours': economic reasoning
- Eq-tilt, Eq-calodds, Eq-aggE, Eq-objective, Eq-cellodds, R penalty: definitions of the estimator/objective
- LM algorithm schedule (150 iterations, nu/3 and nu*4, clip [-3,3], 12 tries, 1e-10, 3 starts, six seconds): algorithm settings and run time
- Sec4 'weighted average of nonlinear function differs from function at average': general Jensen-type reasoning (a toy example was checked in the earlier run only)
- Sec4.1 'mileage targets with lower weight understated car mileage elasticity by about 12%': result of an alternative calibration run not in the files
- Sec4.2 prior money share 0.37 / 0.64 and 60/50, 60/30 min per km: needs TERESA value of time (not in document or generated files)
- Sec4.2 'GMM tables count trips, about 3.2 times TU tours': external data
- Sec4.2 'five of six' reasoning about mechanism (cost fell relative to VoT); 'leisure rises because pattern change': causal explanation (the numeric 5-of-6 pattern is checked)
- Sec5 'on 2009-11 cells car mileage elasticity to car time is -0.423 vs -0.434 in LTM': number not present in any generated table (not commute SOV, which is -0.459 / -0.459); source unknown
- Sec5 CV per-purpose IPDL errors 0.019 to 0.117; escort 0.27 / 0.60 / 1.23: IPDL and MNL per-purpose CV errors not in generated tables (NL escort 0.27 and NL range 0.025-0.083 are checked)
- Sec5 'bands above 300 km: model responds more strongly than LTM; PT fare above 200 km shopping/leisure weaker': qualitative comparison of tab_band; majority pattern holds on inspection but business 300+ is equal (-0.50 vs -0.49), not machine-scored
- Sec5 'IPDL nests have no counterpart in LTM', bands add up claims: structural reasoning
- Eq-burden (rule of a half): definition; no numbers beyond the 26.2 and 0.92 constants
- Sec6 'test suite of 27 properties', test bounds: software testing claim (the 0.035/0.04 bounds are checked against tab_err)
- Sec6.1 default gamma recalibration, '2.01% NL vkm, 2.36% MNL', '10 km per lost car', '46% to 67% of cross-sectional difference': model/TU outputs not in generated files; only the 4.02% car-count change and the -1.07/-0.20 local elasticities are reproduced
- Sec6.1 de Jong (2009) elasticities -0.16, -0.2, -0.4 default; LTM VoT slope 0.37: external literature/LTM values
- Sec6.1 'earlier form implied local cost elasticity of -2.0 in lowest quintile': needs beta calibrated to 0.46 and the earlier ownership shares; not reproduced
- Sec6.1 'aggregate elasticity does not depend on the reference cost K because gamma recalibrated': follows by definition of the calibration (gamma K enters as a product); reasoning
- Sec7 Discussion statements (Relation to standard models, Positive own elasticities, Income, Limitations): interpretation and reasoning
- Appendix sheet descriptions: descriptive

## Caveat

Results are conditional on the LaTeX-to-SymPy translation shown in the 'What was checked' column. Table values were read from `doc\generated\*.tex` as of this run; the cost-share load factors (L_H, L_C) come from the earlier run because LTM Table 5.8 is not in the document. Numeric tolerances reflect rounding of the printed inputs.
