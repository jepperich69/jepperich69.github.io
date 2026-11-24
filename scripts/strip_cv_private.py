"""Make a web copy of the CV without private details: private phone, birth date, family."""
import sys
from pathlib import Path

p = Path(sys.argv[1])
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
out = []
for line in lines:
    s = line.strip()
    if "Phone (private):" in s or s.startswith(r"\textbf{Family:}"):
        continue
    if r"\textbf{Nationality:}" in s:
        line = "\\noindent\\textbf{Nationality:} Danish.\n"
    out.append(line)
p.write_text("".join(out), encoding="utf-8")
print(f"{len(lines) - len(out)} lines removed from {p}")
