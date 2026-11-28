"""Is there a newer month in the panels than in the published forecast? (stdlib only, for CI)

Usage: python src/check_new.py PATH/TO/forecast.json
Prints new=true|false and last=<YYYY-MM>; appends both to $GITHUB_OUTPUT when set.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    a = argv if argv is not None else sys.argv[1:]
    fc = Path(a[0])
    rows = csv.DictReader((ROOT / "Data" / "panels" / "fuel4_monthly.csv").open(encoding="utf-8"))
    last = max(r["month"] for r in rows)
    pub = json.loads(fc.read_text("utf-8"))["vintage"] if fc.exists() else ""
    new = last > pub
    out = f"new={'true' if new else 'false'}\nlast={last}\n"
    print(out.strip(), f"(published {pub or 'none'})")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
