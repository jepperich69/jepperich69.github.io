"""Minimal client for the Statistics Denmark (DST) StatBank API, with a local cache.

Stdlib only, so the monthly GitHub Action needs no installs for the fetch step.

API docs: https://www.dst.dk/en/Statistik/brug-statistikken/muligheder-i-statistikbanken/api
No key is required. Data is requested with ``valuePresentation="Code"`` so parsing never
depends on label text, and labels are taken from ``tableinfo`` when needed.

Cache rule: a cached extract is reused while the table's ``updated`` timestamp in
``tableinfo`` is unchanged. One ``tableinfo`` call per table per run decides that.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.statbank.dk/v1"
USER_AGENT = "ev-fleet-forecast/0.1 (python-urllib)"


class DSTError(RuntimeError):
    """Raised when the API returns an error payload or keeps failing."""


def _request(url: str, body: dict | None = None, *, retries: int = 4, timeout: float = 60.0) -> bytes:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"User-Agent": USER_AGENT}
    if data is not None:
        headers["Content-Type"] = "application/json"
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:  # 4xx carries a JSON error; do not retry those
            payload = e.read().decode("utf-8", "replace")
            if 400 <= e.code < 500:
                raise DSTError(f"DST {e.code} for {url}: {payload}") from e
            last = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
        time.sleep(2 ** attempt)
    raise DSTError(f"DST request failed after {retries} attempts: {url}: {last}")


def tableinfo(table: str, lang: str = "en") -> dict:
    """Metadata for a table: variables with value codes/labels, ``updated`` timestamp."""
    raw = _request(f"{API}/tableinfo/{table}?lang={lang}&format=JSON")
    info = json.loads(raw)
    if "errorTypeCode" in info:
        raise DSTError(f"{table}: {info.get('message')}")
    return info


def tables(lang: str = "en") -> list[dict]:
    """All active StatBank tables: id, text, firstPeriod, latestPeriod, variables."""
    return json.loads(_request(f"{API}/tables?lang={lang}&format=JSON"))


def latest_table(pattern: str, lang: str = "en") -> str:
    """Id of the newest table whose id fully matches ``pattern``.

    For yearly re-issued tables such as the population projection (FRDK126 in 2026,
    FRDK127 in 2027): the highest matching id wins.
    """
    import re
    ids = [t["id"] for t in tables(lang) if re.fullmatch(pattern, t["id"])]
    if not ids:
        raise DSTError(f"no table matches {pattern!r}")
    return max(ids)


def _parse_value(s: str) -> int | float | None:
    s = s.strip()
    if s in ("", "..", "-", "."):  # DST missing / suppressed markers
        return None
    try:
        return int(s)
    except ValueError:
        return float(s.replace(",", "."))


def fetch(table: str, variables: dict[str, list[str]], lang: str = "en") -> list[dict]:
    """Fetch an extract. ``variables`` maps variable id -> list of value codes ("*" = all).

    Returns rows as dicts keyed by upper-case variable id plus ``INDHOLD`` (the value,
    int/float or None). All selector values are codes.
    """
    body = {
        "table": table,
        "format": "CSV",
        "lang": lang,
        "valuePresentation": "Code",
        "variables": [{"code": k, "values": v} for k, v in variables.items()],
    }
    raw = _request(f"{API}/data", body).decode("utf-8-sig")
    if raw.lstrip().startswith("{"):
        err = json.loads(raw)
        raise DSTError(f"{table}: {err.get('message', raw)}")
    rows = list(csv.DictReader(io.StringIO(raw), delimiter=";"))
    for r in rows:
        r["INDHOLD"] = _parse_value(r["INDHOLD"])
    return rows


class Cache:
    """File cache: ``<dir>/<table>_<hash>.csv`` plus a ``.meta.json`` sidecar."""

    def __init__(self, directory: str | Path):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self._updated: dict[str, str] = {}

    def table_updated(self, table: str) -> str:
        if table not in self._updated:
            self._updated[table] = tableinfo(table)["updated"]
        return self._updated[table]

    def _paths(self, table: str, variables: dict, lang: str) -> tuple[Path, Path]:
        key = json.dumps({"v": variables, "lang": lang}, sort_keys=True)
        h = hashlib.sha1(key.encode()).hexdigest()[:10]
        base = self.dir / f"{table}_{h}"
        return base.with_suffix(".csv"), base.with_suffix(".meta.json")

    def get(self, table: str, variables: dict[str, list[str]], lang: str = "en",
            *, offline: bool = False) -> tuple[list[dict], dict]:
        """Rows and metadata, from cache when the table has not been updated since.

        ``offline=True`` never touches the network (raises if nothing is cached).
        """
        csv_path, meta_path = self._paths(table, variables, lang)
        meta = json.loads(meta_path.read_text("utf-8")) if meta_path.exists() else None
        if offline:
            if meta is None:
                raise DSTError(f"offline and no cache for {table}")
            return self._read(csv_path), meta
        updated = self.table_updated(table)
        if meta is not None and meta.get("updated") == updated and csv_path.exists():
            return self._read(csv_path), meta | {"from_cache": True}
        rows = fetch(table, variables, lang)
        if not rows:
            raise DSTError(f"{table}: empty extract for {variables}")
        meta = {
            "table": table,
            "variables": variables,
            "lang": lang,
            "updated": updated,
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "n_rows": len(rows),
        }
        self._write(csv_path, rows)
        meta_path.write_text(json.dumps(meta, indent=2), "utf-8")
        return rows, meta | {"from_cache": False}

    @staticmethod
    def _write(path: Path, rows: list[dict]) -> None:
        tmp = path.with_suffix(".tmp")
        with tmp.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        tmp.replace(path)  # atomic: a crash never leaves a half-written cache file

    @staticmethod
    def _read(path: Path) -> list[dict]:
        with path.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        for r in rows:
            r["INDHOLD"] = _parse_value(r["INDHOLD"])
        return rows
