"""
update_metrics.py
-----------------
Fetches live citation metrics (H-index, i10-index, total citations) for Jeppe Rich
from Google Scholar (user=dLP3kAMAAAAJ) with OpenAlex / Semantic Scholar metadata,
writes Website_JeppeRich/assets/metrics.json (and docs/assets/metrics.json), and
updates the default fallback numbers in index.qmd and group-cv/index.qmd.
"""
import json
import os
import re
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
import urllib.request

SCHOLAR_USER = "dLP3kAMAAAAJ"
ORCID_ID = "0000-0001-5706-3836"

SITE_ROOT = Path(__file__).resolve().parent.parent
ASSETS_JSON = SITE_ROOT / "assets" / "metrics.json"
DOCS_ASSETS_JSON = SITE_ROOT / "docs" / "assets" / "metrics.json"


def fetch_google_scholar(user_id: str) -> dict | None:
    url = f"https://scholar.google.com/citations?user={user_id}&hl=en"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    cells = re.findall(r'class="gsc_rsb_std">(\d+)<', html)
    if len(cells) >= 6:
        return {
            "source": "Google Scholar",
            "citations_all": int(cells[0]),
            "citations_5y": int(cells[1]),
            "h_index": int(cells[2]),
            "h_index_5y": int(cells[3]),
            "i10_index": int(cells[4]),
            "i10_index_5y": int(cells[5]),
        }
    return None


def fetch_openalex(orcid: str) -> dict | None:
    url = f"https://api.openalex.org/authors/https://orcid.org/{orcid}"
    req = urllib.request.Request(url, headers={"User-Agent": "mailto:rich@dtu.dk"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    stats = data.get("summary_stats", {})
    return {
        "openalex_works": data.get("works_count"),
        "openalex_citations": data.get("cited_by_count"),
        "openalex_h_index": stats.get("h_index"),
        "openalex_i10_index": stats.get("i10_index"),
    }


# Scopus has split the author record in two (both IDs listed on the ORCID record); the metrics
# below are computed over the union of documents, so they equal those of a merged profile.
SCOPUS_AUTHOR_IDS = os.environ.get("SCOPUS_AUTHOR_IDS", "7202729520,57210454726")


def h_index(cites: list[int]) -> int:
    """Largest h such that h documents have at least h citations each."""
    s = sorted(cites, reverse=True)
    return sum(1 for i, c in enumerate(s, start=1) if c >= i)


def fetch_scopus(author_ids: str) -> dict | None:
    """Scopus Search API over all documents of the given author IDs.
    Needs env SCOPUS_API_KEY (dev.elsevier.com); off the DTU network also SCOPUS_INSTTOKEN.
    Returns None (and keeps the previous values) when no key is set."""
    key = os.environ.get("SCOPUS_API_KEY")
    if not key:
        print("SKIP | Scopus: SCOPUS_API_KEY not set")
        return None
    headers = {"X-ELS-APIKey": key, "Accept": "application/json"}
    if os.environ.get("SCOPUS_INSTTOKEN"):
        headers["X-ELS-Insttoken"] = os.environ["SCOPUS_INSTTOKEN"]
    ids = [a.strip() for a in author_ids.split(",") if a.strip()]
    query = urllib.parse.quote(" OR ".join(f"AU-ID({a})" for a in ids))
    cites, eids, start = [], set(), 0
    while True:
        url = (f"https://api.elsevier.com/content/search/scopus?query={query}"
               f"&field=eid,citedby-count&count=25&start={start}")
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as resp:
            res = json.loads(resp.read().decode("utf-8"))["search-results"]
        entries = [e for e in res.get("entry", []) if "error" not in e]
        for e in entries:
            if e.get("eid") not in eids:  # a document on both profiles counts once
                eids.add(e.get("eid"))
                cites.append(int(e.get("citedby-count") or 0))
        start += len(entries)
        if not entries or start >= int(res.get("opensearch:totalResults", 0)):
            break
    if not cites:
        return None
    return {
        "scopus_documents": len(cites),
        "scopus_citations": sum(cites),
        "scopus_h_index": h_index(cites),
        "scopus_updated_date": datetime.now().strftime("%Y-%m-%d"),
    }


def main():
    existing = {}
    if ASSETS_JSON.exists():
        try:
            existing = json.loads(ASSETS_JSON.read_text(encoding="utf-8"))
        except Exception:
            existing = {}

    result = dict(existing)
    result["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result["updated_date"] = datetime.now().strftime("%Y-%m-%d")

    try:
        gs = fetch_google_scholar(SCHOLAR_USER)
        if gs:
            result.update(gs)
            print(f"OK | Google Scholar: H={gs['h_index']}, i10={gs['i10_index']}, citations={gs['citations_all']}")
        else:
            print("WARN | Google Scholar table cells not found in response")
    except Exception as e:
        print(f"WARN | Google Scholar fetch failed: {e}")

    try:
        oa = fetch_openalex(ORCID_ID)
        if oa:
            result.update(oa)
            print(f"OK | OpenAlex: H={oa['openalex_h_index']}, i10={oa['openalex_i10_index']}, citations={oa['openalex_citations']}")
    except Exception as e:
        print(f"WARN | OpenAlex fetch failed: {e}")

    try:
        sc = fetch_scopus(SCOPUS_AUTHOR_IDS)
        if sc:
            result.update(sc)
            print(f"OK | Scopus: H={sc['scopus_h_index']}, citations={sc['scopus_citations']}, documents={sc['scopus_documents']}")
    except Exception as e:
        print(f"WARN | Scopus fetch failed (previous values kept): {e}")

    ASSETS_JSON.parent.mkdir(parents=True, exist_ok=True)
    ASSETS_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if DOCS_ASSETS_JSON.parent.exists():
        DOCS_ASSETS_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
