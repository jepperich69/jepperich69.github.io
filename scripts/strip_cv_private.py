"""Make a web copy of the CV without private details (private phone, birth date, family)
and without the unpublished papers the author keeps off the web (WEB_EXCLUDE).
master_cv.tex itself is never changed; this runs on a copy."""
import sys
from pathlib import Path

# Papers listed in master_cv.tex that must not appear in the public web CV
# (matched on a distinctive part of the title). Author decision 2026-11-24.
WEB_EXCLUDE = [
    "Bracketing the Optimum: A Boltzmann Complement to SAA",
]

p = Path(sys.argv[1])
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
out = []
for line in lines:
    s = line.strip()
    if "Phone (private):" in s or s.startswith(r"\textbf{Family:}"):
        continue
    if any(title in s for title in WEB_EXCLUDE):
        continue
    if r"\textbf{Nationality:}" in s:
        line = "\\noindent\\textbf{Nationality:} Danish.\n"
    out.append(line)
p.write_text("".join(out), encoding="utf-8")
print(f"{len(lines) - len(out)} lines removed from {p}")
