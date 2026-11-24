"""
paper_status.py -- manage paper status for the website from papers/papers.yml.

The registry papers/papers.yml is the single source of truth. Every command that
changes it also rebuilds the generated snippets, so a status change shows up
everywhere (papers page, home page featured cards, paper subpage badge/subtitle).

Usage (python = C:\\Users\\rich\\AppData\\Local\\miniconda3\\python.exe):
  paper_status.py list
  paper_status.py set   <id> <status> [--substatus S] [--venue V] [--year Y] [--date D] [--no-event]
  paper_status.py event <id> "Presented at hEART 2026, Lisbon" [--date 2026-09]
  paper_status.py add   <id> --status wip --summary "One sentence."
  paper_status.py check         # validate only (exit 1 on errors)
  paper_status.py build         # validate + regenerate snippets

<id> is the project folder name (e.g. Pub_PopInt_PartB); a unique prefix or the
label also works. status: accepted | in-review | wip | working-paper.

Generated files (never edit by hand; Quarto ignores files starting with "_"):
  papers/_gen/{accepted,in-review,wip,working-paper}.md   included by papers/index.qmd
  papers/_gen/featured.md                                 included by index.qmd
  papers/<slug>/_status.md                                included by each paper subpage
  plus the `subtitle:` line in papers/<slug>/index.qmd front matter.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
import urllib.parse
from datetime import date
from pathlib import Path

import yaml

SITE = Path(__file__).resolve().parent.parent
REGISTRY = SITE / "papers" / "papers.yml"
GEN = SITE / "papers" / "_gen"
PUBS = SITE.parent / "Publikationer"
EMAIL = "rich@dtu.dk"

STATUSES = {
    "accepted": ("Accepted", "badge-st-accepted"),
    "in-review": ("In review", "badge-st-review"),
    "wip": ("Work in progress", "badge-st-wip"),
    "working-paper": ("Working paper", "badge-st-wp"),
}
ALIASES = {
    "in review": "in-review", "review": "in-review", "inreview": "in-review",
    "submitted": "in-review", "work-in-progress": "wip", "work in progress": "wip",
    "working paper": "working-paper", "wp": "working-paper", "published": "accepted",
}
WIP_FORBIDDEN = ("title", "abstract", "slug", "links", "authors", "venue", "doi")
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
HEADER = REGISTRY.read_text(encoding="utf-8").split("papers:", 1)[0] if REGISTRY.exists() else ""


# ---------------------------------------------------------------- registry I/O
def load() -> list[dict]:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    papers = data.get("papers") or []
    for p in papers:
        p.setdefault("events", [])
        for e in p["events"]:
            e["date"] = str(e.get("date", ""))
    return papers


def save(papers: list[dict]) -> None:
    body = yaml.safe_dump({"papers": papers}, sort_keys=False, allow_unicode=True, width=100)
    REGISTRY.write_text(HEADER + body, encoding="utf-8")


def norm_status(s: str) -> str:
    s = s.strip().lower()
    s = ALIASES.get(s, s)
    if s not in STATUSES:
        sys.exit(f"ERR | unknown status '{s}'. Use one of: {', '.join(STATUSES)}")
    return s


def find(papers: list[dict], key: str) -> dict:
    k = key.lower()
    exact = [p for p in papers if p["id"].lower() == k or str(p.get("label", "")).lower() == k]
    if exact:
        return exact[0]
    hits = [p for p in papers if p["id"].lower().startswith(k) or k in p["id"].lower()]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        sys.exit(f"ERR | no paper matches '{key}'. Use `add` for a new one.")
    sys.exit(f"ERR | '{key}' is ambiguous: {', '.join(p['id'] for p in hits)}")


# ---------------------------------------------------------------- validation
def validate(papers: list[dict]) -> tuple[list[str], list[str]]:
    errors, warns = [], []
    seen = set()
    slugs = {}
    for p in papers:
        pid = p.get("id")
        if not pid:
            errors.append("entry without id")
            continue
        if pid in seen:
            errors.append(f"{pid}: duplicate id")
        seen.add(pid)
        st = p.get("status")
        if st not in STATUSES:
            errors.append(f"{pid}: bad status '{st}'")
            continue
        if pid.startswith(("Pub_", "Pro_", "PhD_")) and not (PUBS / pid).is_dir():
            warns.append(f"{pid}: no project folder Publikationer\\{pid}")
        if not p.get("summary") and (st != "accepted" or p.get("featured")):
            errors.append(f"{pid}: missing summary (optional only for non-featured accepted papers)")
        if st == "wip":
            bad = [f for f in WIP_FORBIDDEN if p.get(f)]
            if bad:
                errors.append(f"{pid}: wip entries may not publish {', '.join(bad)}")
            if len(re.findall(r"[.!?](\s|$)", (p.get("summary") or "").strip())) > 1:
                errors.append(f"{pid}: wip summary must be one sentence")
        if st in ("accepted", "in-review"):
            for f in ("title", "authors"):
                if not p.get(f):
                    errors.append(f"{pid}: missing {f}")
            if not p.get("venue"):
                warns.append(f"{pid}: no venue recorded")
        if p.get("slug"):
            slugs[p["slug"]] = p
            if not (SITE / "papers" / p["slug"] / "index.qmd").exists():
                errors.append(f"{pid}: papers/{p['slug']}/index.qmd does not exist")
    # orphan subpages: a page exists but no public entry owns it (e.g. paper moved back to wip)
    for d in (SITE / "papers").iterdir():
        if d.is_dir() and not d.name.startswith("_") and (d / "index.qmd").exists():
            if d.name not in slugs:
                errors.append(f"papers/{d.name}/ has no registry entry with that slug "
                              f"(delete the page or add slug to the entry)")
    # accepted papers should also be in the hand-kept archive
    idx = (SITE / "papers" / "index.qmd").read_text(encoding="utf-8")
    archive = idx.split("Complete Archive", 1)[-1].lower()
    for p in papers:
        if p.get("status") == "accepted" and p.get("title"):
            head = re.sub(r"\s+", " ", p["title"]).lower()[:40]
            if head not in re.sub(r"\s+", " ", archive):
                warns.append(f"{p['id']}: accepted but not in the archive list in papers/index.qmd")
    return errors, warns


# ---------------------------------------------------------------- rendering
def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def fmt_date(d: str) -> str:
    m = re.match(r"(\d{4})(?:-(\d{1,2}))?", d or "")
    if not m:
        return d or ""
    return f"{MONTHS[int(m.group(2)) - 1]} {m.group(1)}" if m.group(2) else m.group(1)


def events_sorted(p: dict) -> list[dict]:
    return sorted(p.get("events", []), key=lambda e: e.get("date", ""), reverse=True)


def venue_line(p: dict) -> str:
    bits = [p.get("venue") or ""]
    if p.get("year"):
        bits[0] += f" ({p['year']})"
    if p.get("volume"):
        bits.append(p["volume"])
    return " · ".join(b for b in bits if b)


def status_badge(p: dict) -> str:
    label, cls = STATUSES[p["status"]]
    sub = p.get("substatus")
    if sub and sub.lower() != label.lower():
        label = f"{label} · {sub}"
    return f'<span class="jr-badge {cls}">{esc(label)}</span>'


def link_badges(p: dict, prefix: str) -> list[str]:
    out = []
    for l in p.get("links", []):
        url = l["url"]
        if not re.match(r"^(https?:|mailto:|/)", url):
            url = prefix + url
        cls = {"public": "badge-public", "private": "badge-private"}.get(l.get("kind"), "badge-pdf")
        tgt = ' target="_blank"' if url.startswith("http") else ""
        out.append(f'<a href="{esc(url)}" class="jr-badge {cls}"{tgt}>{esc(l["label"])}</a>')
    if p["status"] in ("accepted", "in-review") and p.get("preprint_request", True):
        subj = urllib.parse.quote(f"Preprint request: {p['title']}")
        out.append(f'<a href="mailto:{EMAIL}?subject={subj}" class="jr-badge badge-request">Request Preprint</a>')
    return out


def authors_html(authors: str) -> str:
    """Author list with the site owner in bold (matches 'Jeppe Rich' and 'Rich J.')."""
    return re.sub(r"(Jeppe Rich|Rich J\.(?:H\.)?)", r"<strong>\1</strong>", esc(authors))


def card(p: dict, root: str) -> str:
    """root: path from the including page to papers/ ('' or 'papers/')."""
    page = f"{root}{p['slug']}/index.qmd" if p.get("slug") else ""
    title = f'<a href="{page}">{esc(p["title"])}</a>' if page else esc(p["title"])
    meta = status_badge(p) + (f" · {esc(venue_line(p))}" if venue_line(p) else "")
    ev = events_sorted(p)
    latest = (f'<div class="jr-card-event">Latest: {esc(ev[0]["text"])}'
              f' ({fmt_date(ev[0]["date"])})</div>') if ev else ""
    badges = ([f'<a href="{page}" class="jr-badge badge-pdf">Paper Page</a>'] if page else [])
    badges += link_badges(p, f"{root}{p['slug']}/" if p.get("slug") else root)
    return (
        '  <div class="jr-card">\n    <div>\n'
        f'      <div class="jr-card-meta">{meta}</div>\n'
        f'      <h3>{title}</h3>\n'
        f'      <p>{authors_html(p["authors"])}'
        + (f' · {esc(p["summary"])}' if p.get("summary") else "") + '</p>\n'
        f'      {latest}\n    </div>\n'
        f'    <div class="badge-row">{" ".join(badges)}</div>\n  </div>\n'
    )


def grid(cards: list[str]) -> str:
    if not cards:
        return "*None at the moment.*\n"
    return "```{=html}\n<div class=\"card-grid\">\n" + "\n".join(cards) + "</div>\n```\n"


def table(rows: list[dict], first_col: str) -> str:
    if not rows:
        return "*None at the moment.*\n"
    out = [f"| {first_col} | Status | Topic | Latest |", "|---|---|---|---|"]
    for p in rows:
        ev = events_sorted(p)
        latest = f"{ev[0]['text']} ({fmt_date(ev[0]['date'])})" if ev else ""
        label = p.get("label") or p["id"]
        out.append(f"| **`{label}`** | {status_badge(p)} | {p['summary']} | {latest.replace('|', '/')} |")
    return "\n".join(out) + "\n"


def subpage_block(p: dict) -> str:
    badges = [status_badge(p)] + link_badges(p, "")
    s = ("```{=html}\n<div class=\"badge-row\" style=\"margin-bottom: 1.5rem;\">\n  "
         + "\n  ".join(badges) + "\n</div>\n```\n")
    ev = events_sorted(p)
    if ev:
        s += "\n::: {.paper-history}\n**History:** " + " · ".join(
            f"{e['text']} ({fmt_date(e['date'])})" for e in ev) + "\n:::\n"
    return s


def subtitle(p: dict) -> str:
    label = STATUSES[p["status"]][0]
    if p["status"] == "accepted":
        return venue_line(p) or label
    return " · ".join(x for x in (f"Status: {label}", p.get("venue")) if x)


def build(papers: list[dict]) -> None:
    GEN.mkdir(exist_ok=True)
    by = {s: [p for p in papers if p["status"] == s] for s in STATUSES}
    by["accepted"].sort(key=lambda p: -int(p.get("year") or 9999))  # newest first, stable
    stamp = "<!-- generated by scripts/paper_status.py from papers/papers.yml -- do not edit -->\n"
    (GEN / "accepted.md").write_text(stamp + grid([card(p, "") for p in by["accepted"]]), encoding="utf-8")
    (GEN / "in-review.md").write_text(stamp + grid([card(p, "") for p in by["in-review"]]), encoding="utf-8")
    (GEN / "wip.md").write_text(stamp + table(by["wip"], "Project Code"), encoding="utf-8")
    # Section 4 and its line in the category list appear only when at least one working paper exists.
    wp = by["working-paper"]
    wp_section = ("## 4. Unpublished working papers\n\n"
                  "Standalone working papers and archived technical reports not currently under journal review:\n\n"
                  + table(wp, "Identifier") + "\n---\n") if wp else ""
    wp_intro = ("4. **Unpublished working papers:** Standalone working papers and technical notes "
                "not currently under journal review.\n") if wp else ""
    (GEN / "working-paper.md").write_text(stamp + wp_section, encoding="utf-8")
    (GEN / "working-paper-intro.md").write_text(stamp + wp_intro, encoding="utf-8")
    feat = [p for p in papers if p.get("featured") and p["status"] in ("accepted", "in-review")]
    (GEN / "featured.md").write_text(stamp + grid([card(p, "papers/") for p in feat]), encoding="utf-8")
    for p in papers:
        if not p.get("slug"):
            continue
        d = SITE / "papers" / p["slug"]
        (d / "_status.md").write_text(stamp + subpage_block(p), encoding="utf-8")
        qmd = d / "index.qmd"
        txt = qmd.read_text(encoding="utf-8")
        new_sub = 'subtitle: "' + subtitle(p).replace('"', "'") + '"'
        if re.search(r"(?m)^subtitle:.*$", txt):
            txt2 = re.sub(r"(?m)^subtitle:.*$", lambda _: new_sub, txt, count=1)
        else:
            txt2 = re.sub(r"(?m)^(title:.*)$", lambda m: m.group(1) + "\n" + new_sub, txt, count=1)
        if "{{< include _status.md >}}" not in txt2:
            print(f"WARN | papers/{p['slug']}/index.qmd lacks '{{{{< include _status.md >}}}}'")
        if txt2 != txt:
            qmd.write_text(txt2, encoding="utf-8")


def check_and_build(papers, do_build=True) -> int:
    errors, warns = validate(papers)
    for w in warns:
        print(f"WARN | {w}")
    for e in errors:
        print(f"ERR  | {e}")
    if errors:
        print("Not built: fix the errors above.")
        return 1
    if do_build:
        build(papers)
        print(f"OK   | built snippets for {len(papers)} papers")
    else:
        print(f"OK   | {len(papers)} papers valid")
    return 0


# ---------------------------------------------------------------- commands
def auto_event(p: dict, new: str) -> str | None:
    v = p.get("venue")
    if new == "accepted":
        return f"Accepted in {v}" if v else "Accepted"
    if new == "in-review":
        return f"Submitted to {v}" if v else "Submitted"
    return None  # moving to wip / working paper is not announced


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("check")
    sub.add_parser("build")
    s = sub.add_parser("set")
    s.add_argument("id"); s.add_argument("status")
    s.add_argument("--substatus"); s.add_argument("--venue"); s.add_argument("--year", type=int)
    s.add_argument("--date", default=date.today().isoformat()); s.add_argument("--no-event", action="store_true")
    e = sub.add_parser("event")
    e.add_argument("id"); e.add_argument("text"); e.add_argument("--date", default=date.today().isoformat())
    a = sub.add_parser("add")
    a.add_argument("id"); a.add_argument("--status", default="wip"); a.add_argument("--summary", required=True)
    a.add_argument("--label")
    args = ap.parse_args(argv)

    papers = load()
    if args.cmd == "list":
        for st, (label, _) in STATUSES.items():
            print(f"\n{label}:")
            for p in (p for p in papers if p["status"] == st):
                ev = events_sorted(p)
                tail = f"  [latest: {ev[0]['text']}, {ev[0]['date']}]" if ev else ""
                sub_ = f" ({p['substatus']})" if p.get("substatus") else ""
                print(f"  {p['id']:<32}{sub_} {p.get('venue') or ''}{tail}")
        return 0
    if args.cmd == "check":
        return check_and_build(papers, do_build=False)
    if args.cmd == "build":
        return check_and_build(papers)

    if args.cmd == "set":
        p = find(papers, args.id)
        new = norm_status(args.status)
        old = p["status"]
        if args.venue:
            p["venue"] = args.venue
        if args.year:
            p["year"] = args.year
        if args.substatus is not None:
            p["substatus"] = args.substatus
        elif new != old:
            p.pop("substatus", None)
        p["status"] = new
        if new != old and not args.no_event:
            txt = auto_event(p, new)
            if txt:
                p["events"].append({"date": args.date, "text": txt})
        print(f"{p['id']}: {old} -> {new}" + (f" ({p.get('substatus')})" if p.get("substatus") else ""))
        if new != "wip" and old == "wip":
            print("NOTE | leaving wip: add title, authors, venue (and slug + papers/<slug>/index.qmd "
                  "with '{{< include _status.md >}}') before it will build.")
        if new == "wip" and old != "wip":
            print("NOTE | moving to wip: remove title/abstract/links/slug from the entry and delete "
                  "papers/<slug>/ before it will build.")
    elif args.cmd == "event":
        p = find(papers, args.id)
        p["events"].append({"date": args.date, "text": args.text})
        print(f"{p['id']}: event added ({args.date}) {args.text}")
    elif args.cmd == "add":
        if any(p["id"] == args.id for p in papers):
            sys.exit(f"ERR | {args.id} already exists; use `set`.")
        p = {"id": args.id, "status": norm_status(args.status), "summary": args.summary, "events": []}
        if args.label:
            p["label"] = args.label
        papers.append(p)
        print(f"{args.id}: added as {p['status']}")

    save(papers)
    return check_and_build(papers)


if __name__ == "__main__":
    sys.exit(main())
