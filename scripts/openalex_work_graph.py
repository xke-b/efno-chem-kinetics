#!/usr/bin/env python3
"""Fetch a small OpenAlex citation graph for a work DOI or OpenAlex id.

Examples
--------
python scripts/openalex_work_graph.py \
  --work https://doi.org/10.1016/j.combustflame.2024.113847 \
  --out artifacts/papers/efno_weng_2025/openalex_graph.json
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from typing import Any

BASE = "https://api.openalex.org"
MAILTO = "research@example.com"


def get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def openalex_work_url(work: str) -> str:
    if work.startswith("http://") or work.startswith("https://"):
        encoded = urllib.parse.quote(work, safe="")
        return f"{BASE}/works/{encoded}?mailto={MAILTO}"
    if work.startswith("W"):
        return f"{BASE}/works/{work}?mailto={MAILTO}"
    raise ValueError(f"Unsupported work identifier: {work}")


def compact_work(work: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": work.get("id"),
        "title": work.get("display_name"),
        "year": work.get("publication_year"),
        "doi": work.get("doi"),
        "type": work.get("type"),
        "cited_by_count": work.get("cited_by_count"),
        "topics": [t.get("display_name") for t in work.get("topics", [])[:5]],
        "primary_location": (work.get("primary_location") or {}).get("source", {}).get("display_name"),
    }


def fetch_related_works(ids: list[str], limit: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for wid in ids[:limit]:
        short_id = wid.rsplit("/", 1)[-1]
        url = f"{BASE}/works/{short_id}?mailto={MAILTO}"
        try:
            items.append(compact_work(get_json(url)))
            time.sleep(0.1)
        except Exception as exc:  # pragma: no cover - network failure path
            items.append({"id": wid, "error": str(exc)})
    return items


def fetch_citing_works(openalex_id: str, limit: int) -> list[dict[str, Any]]:
    short_id = openalex_id.rsplit("/", 1)[-1]
    url = (
        f"{BASE}/works?filter=cites:{urllib.parse.quote(short_id)}"
        f"&per-page={limit}&sort=publication_date:desc&mailto={MAILTO}"
    )
    data = get_json(url)
    return [compact_work(w) for w in data.get("results", [])]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", required=True, help="DOI URL or OpenAlex work id (e.g. W4404610207)")
    parser.add_argument("--reference-limit", type=int, default=15)
    parser.add_argument("--citing-limit", type=int, default=15)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    root = get_json(openalex_work_url(args.work))
    payload = {
        "root": compact_work(root),
        "reference_count": len(root.get("referenced_works", [])),
        "references": fetch_related_works(root.get("referenced_works", []), args.reference_limit),
        "citations": fetch_citing_works(root["id"], args.citing_limit),
    }

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
