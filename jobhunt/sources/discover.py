#!/usr/bin/env python3
"""Discover jobs from public, documented job APIs and public pages. Standard library only.

Sources (toggle in config.json > sources):
  greenhouse  https://boards-api.greenhouse.io/v1/boards/<slug>/jobs?content=true
  lever       https://api.lever.co/v0/postings/<slug>?mode=json
  ashby       https://api.ashbyhq.com/posting-api/job-board/<slug>
  remoteok    https://remoteok.com/api
  remotive    https://remotive.com/api/remote-jobs
  hn          latest "Ask HN: Who is hiring?" thread via the Algolia API
  yc_jobs     ycombinator.com/jobs pages (listings are embedded as JSON in data-page)

Output: data/jobs_raw.json (normalized schema, deduped)
Run:    python3 jobhunt/sources/discover.py

No login-walled sites, no scraping behind auth. LinkedIn, Naukri and Reddit are handled
by other paths (see docs/03-lead-sourcing.md).
"""
from __future__ import annotations

import html as _html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import data_dir, load_config  # noqa: E402

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124 Safari/537.36")


def fetch(url: str, timeout: int = 25, accept: str = "application/json") -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def fetch_json(url: str, timeout: int = 25):
    return json.loads(fetch(url, timeout))


def strip_html(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = _html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


class Collector:
    def __init__(self, limit: int):
        self.jobs: list[dict] = []
        self.limit = limit

    def add(self, source, company, title, location, url, posted, desc, remote=None, tags=None):
        if not title:
            return
        self.jobs.append({
            "source": source, "company": (company or "").strip(), "title": title.strip(),
            "location": (location or "").strip(), "url": url or "", "posted": posted or "",
            "remote": remote, "tags": tags or [], "description": strip_html(desc)[:1600],
        })


def greenhouse(c: Collector, slug: str) -> int:
    n = 0
    try:
        d = fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")
        for j in d.get("jobs", [])[:c.limit]:
            loc = (j.get("location") or {}).get("name", "")
            c.add("greenhouse", slug, j.get("title"), loc, j.get("absolute_url"),
                  j.get("updated_at", ""), j.get("content", ""))
            n += 1
    except Exception as e:
        print(f"  greenhouse/{slug}: {type(e).__name__}")
    return n


def lever(c: Collector, slug: str) -> int:
    n = 0
    try:
        d = fetch_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
        for j in d[:c.limit]:
            cat = j.get("categories", {}) or {}
            c.add("lever", slug, j.get("text"), cat.get("location", ""), j.get("hostedUrl"),
                  str(j.get("createdAt", "")), j.get("descriptionPlain") or j.get("description", ""))
            n += 1
    except Exception as e:
        print(f"  lever/{slug}: {type(e).__name__}")
    return n


def ashby(c: Collector, slug: str) -> int:
    n = 0
    try:
        d = fetch_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true")
        for j in d.get("jobs", [])[:c.limit]:
            c.add("ashby", slug, j.get("title"), j.get("location", ""),
                  j.get("jobUrl") or j.get("applyUrl"), j.get("publishedDate", ""),
                  j.get("descriptionPlain") or j.get("descriptionHtml", ""), remote=j.get("isRemote"))
            n += 1
    except Exception as e:
        print(f"  ashby/{slug}: {type(e).__name__}")
    return n


def remoteok(c: Collector) -> int:
    n = 0
    try:
        for j in fetch_json("https://remoteok.com/api")[:c.limit + 1]:
            if not isinstance(j, dict) or "position" not in j:
                continue
            c.add("remoteok", j.get("company"), j.get("position"), j.get("location") or "Remote",
                  j.get("url"), j.get("date", ""), j.get("description", ""),
                  remote=True, tags=j.get("tags", []))
            n += 1
    except Exception as e:
        print(f"  remoteok: {type(e).__name__}")
    return n


def remotive(c: Collector) -> int:
    n = 0
    try:
        d = fetch_json("https://remotive.com/api/remote-jobs?limit=400")
        for j in d.get("jobs", [])[:c.limit]:
            c.add("remotive", j.get("company_name"), j.get("title"),
                  j.get("candidate_required_location") or "Remote", j.get("url"),
                  j.get("publication_date", ""), j.get("description", ""),
                  remote=True, tags=j.get("tags", []))
            n += 1
    except Exception as e:
        print(f"  remotive: {type(e).__name__}")
    return n


def hn(c: Collector, max_comments: int) -> int:
    n = 0
    try:
        q = urllib.parse.quote('"Ask HN: Who is hiring?"')
        s = fetch_json(f"https://hn.algolia.com/api/v1/search_by_date?query={q}&tags=story&hitsPerPage=10")
        story = next((h for h in s.get("hits", [])
                      if h.get("author") == "whoishiring" and "hiring" in (h.get("title") or "").lower()), None)
        if not story:
            print("  hn: no whoishiring story found")
            return 0
        item = fetch_json(f"https://hn.algolia.com/api/v1/items/{story['objectID']}")
        for cm in (item.get("children") or [])[:max_comments]:
            txt = strip_html(cm.get("text", ""))
            if len(txt) < 40:
                continue
            first = txt.split("|")[0].split(".")[0][:120]
            m = re.search(r"(https?://[^\s)\]]+)", cm.get("text", "") or "")
            url = m.group(1) if m else f"https://news.ycombinator.com/item?id={cm.get('id')}"
            c.add("hn", first.split("(")[0][:60], first, "", url, str(cm.get("created_at_i", "")), txt)
            n += 1
    except Exception as e:
        print(f"  hn: {type(e).__name__}: {e}")
    return n


def _relative_to_iso(rel: str) -> str:
    """'6 days' / '3 hours' / 'about 1 month' -> ISO timestamp (approximate)."""
    m = re.search(r"(\d+)\s*(minute|hour|day|week|month|year)", rel or "")
    if not m:
        return ""
    n, unit = int(m.group(1)), m.group(2)
    days = {"minute": n / 1440, "hour": n / 24, "day": n, "week": 7 * n, "month": 30 * n, "year": 365 * n}[unit]
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def yc_jobs(c: Collector, paths: list[str]) -> int:
    """ycombinator.com/jobs pages are server-rendered with a data-page JSON attribute."""
    n = 0
    for path in paths:
        try:
            page = fetch("https://www.ycombinator.com" + path, accept="text/html")
            m = re.search(r'data-page="([^"]+)"', page)
            if not m:
                print(f"  yc{path}: no data-page attribute (layout changed?)")
                continue
            props = json.loads(_html.unescape(m.group(1))).get("props", {})
            for j in props.get("jobPostings", [])[:c.limit]:
                desc = " | ".join(x for x in [
                    j.get("companyOneLiner", ""), j.get("type", ""), j.get("roleSpecificType", ""),
                    f"min experience {j.get('minExperience')}" if j.get("minExperience") else "",
                    j.get("salaryRange", ""), f"visa: {j.get('visa')}" if j.get("visa") else "",
                    f"YC {j.get('companyBatchName')}" if j.get("companyBatchName") else "",
                ] if x)
                url = "https://www.ycombinator.com" + (j.get("url") or "")
                loc = j.get("location", "")
                c.add("yc", j.get("companyName"), j.get("title"), loc, url,
                      _relative_to_iso(j.get("createdAt", "")), desc,
                      remote="remote" in loc.lower())
                n += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"  yc{path}: {type(e).__name__}")
    return n


def main() -> None:
    cfg = load_config()
    src = cfg["sources"]
    companies = cfg.get("companies", {})
    c = Collector(cfg.get("limits", {}).get("max_jobs_per_source", 400))
    counts = {}
    print("Discovering...")
    if src.get("greenhouse"):
        counts["greenhouse"] = sum(greenhouse(c, t) for t in companies.get("greenhouse", []))
    if src.get("lever"):
        counts["lever"] = sum(lever(c, t) for t in companies.get("lever", []))
    if src.get("ashby"):
        counts["ashby"] = sum(ashby(c, t) for t in companies.get("ashby", []))
    if src.get("remoteok"):
        counts["remoteok"] = remoteok(c)
    if src.get("remotive"):
        counts["remotive"] = remotive(c)
    if src.get("hn_whoishiring"):
        counts["hn"] = hn(c, cfg.get("hn_whoishiring", {}).get("max_comments", 600))
    if src.get("yc_jobs"):
        counts["yc"] = yc_jobs(c, cfg.get("yc_jobs", {}).get("paths", []))

    seen, out = set(), []
    for j in c.jobs:
        k = (j["company"].lower(), j["title"].lower())
        ku = j["url"].split("?")[0]
        if k in seen or (ku and ku in seen):
            continue
        seen.add(k)
        if ku:
            seen.add(ku)
        out.append(j)

    path = data_dir() / "jobs_raw.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print("\nper-source counts:", counts)
    print(f"total raw: {len(c.jobs)} | after dedupe: {len(out)} -> {path}")


if __name__ == "__main__":
    main()
