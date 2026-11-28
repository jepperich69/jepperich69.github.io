Elbil-taelleren, monthly pipeline (production copy of the EVadaptation model code).

Run from this folder:
  python src/fetch.py                       # Statistics Denmark -> Data/panels (stdlib only)
  python src/check_new.py ../app/data/forecast.json
  python src/total.py && python src/shares.py   # Bayesian fits; non-zero exit = convergence gate failed
  python src/export.py --app-data ../app/data   # forecast.json + vintages/<YYYY-MM>.json
The GitHub Action .github/workflows/ev_fleet_monthly.yml runs these steps daily and only
refits when Statistics Denmark has published a new month. If any step fails, nothing is
committed and the previous forecast stays online.
Methods: ../app/methods.pdf
