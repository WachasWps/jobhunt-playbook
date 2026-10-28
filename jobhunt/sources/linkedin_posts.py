#!/usr/bin/env python3
"""LinkedIn hiring-post harvester via the Apify API. No LinkedIn account, no browser.

Uses the Apify actor `harvestapi/linkedin-post-search` (cookieless keyword post search,
about $1.50 per 1000 posts, so a typical 8-query run costs around $0.05).

    export APIFY_TOKEN=<your-apify-token>     # or put it in jobhunt/.apify_token (gitignored)
    python3 jobhunt/sources/linkedin_posts.py --dry-run   # show queries, spend nothing
    python3 jobhunt/sources/linkedin_posts.py             # harvest

Builds queries from config, runs the actor, maps results into the shared pipeline
(posts_common.process) and appends net-new leads to data/posts_raw.json.
Reading public posts is all this does. You send every message yourself from your own account.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from posts_common import CFG, build_queries, process  # noqa: E402
from settings import JOBHUNT  # noqa: E402

PH = CFG["post_harvest"]
AP = PH["apify"]

_DATE_MAP = {"past-24h": "24h", "past-week": "week", "past-month": "month",
             "24h": "24h", "week": "week", "month": "month"}


def _token() -> str:
    t = os.environ.get(AP.get("token_env", "APIFY_TOKEN"))
    if t:
        return t.strip()
    tf = JOBHUNT / AP.get("token_file", ".apify_token")
    if tf.exists():
        return tf.read_text().strip()
    sys.exit("ERROR: no Apify token. Set APIFY_TOKEN or create jobhunt/.apify_token "
             "(apify.com > Settings > API & Integrations). Never commit that file.")


def _run_actor(queries: list[str]) -> list[dict]:
    actor = AP["actor"].replace("/", "~")
    timeout = AP.get("run_timeout_s", 240)
    url = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items?timeout={timeout}"
    payload = {
        "searchQueries": queries,
        "maxPosts": PH["max_posts_per_query"],
        "postedLimit": _DATE_MAP.get(PH.get("date_window", "week"), "week"),
        "sortBy": AP.get("sort_by", "date"),
        "scrapePages": AP.get("scrape_pages", 1),
        "scrapeComments": AP.get("scrape_comments", False),
        "maxComments": AP.get("max_comments", 10),
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {_token()}",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout + 30) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        if e.code in (402, 403):
            sys.exit(f"ERROR {e.code}: Apify credit or monthly limit exhausted. The free plan "
                     "is about $5/month. Wait for the reset or add credit, then re-run.")
        sys.exit(f"ERROR {e.code} from Apify: {detail}")
    except Exception as e:
        sys.exit(f"ERROR calling Apify: {type(e).__name__}: {e}")


def _map_item(it: dict) -> dict:
    """Map a harvestapi post item. Schema: content=text, author.{name,linkedinUrl},
    postedAt.{...}, and for job-share posts a job.{title,location,subtitle,linkedinUrl}."""
    author = it.get("author") or {}
    if isinstance(author, dict):
        author_name = author.get("name") or author.get("fullName") or ""
        author_url = (author.get("linkedinUrl") or author.get("url") or "").split("?")[0]
    else:
        author_name, author_url = str(author), ""
    text = it.get("content") or it.get("text") or it.get("commentary") or ""
    post_url = (it.get("linkedinUrl") or it.get("url") or "").split("?")[0]
    posted = it.get("postedAt") or it.get("createdAt") or ""
    if isinstance(posted, dict):
        posted = posted.get("date") or posted.get("timestamp") or posted.get("postedAgoShort") or ""
    job = it.get("job") or {}
    sub = job.get("subtitle") or ""
    job_company = sub[7:].strip() if sub.lower().startswith("job by ") else ""
    return {
        "author": author_name, "author_url": author_url,
        "text": text, "post_url": post_url, "age": str(posted),
        "job_title": job.get("title") or "",
        "job_location": job.get("location") or "",
        "job_url": (job.get("linkedinUrl") or "").split("?")[0],
        "job_company": job_company,
    }


def harvest() -> list[dict]:
    queries = build_queries()[:PH["max_queries_per_run"]]
    print(f"Running {AP['actor']} on {len(queries)} queries "
          f"(<= {PH['max_posts_per_query']} posts each)...")
    items = _run_actor(queries)
    posts = [i for i in items if i.get("type", "post") == "post"]
    comments = [i for i in items if i.get("type") == "comment"]
    print(f"  actor returned {len(items)} items ({len(posts)} posts, {len(comments)} comments)")
    comments_map: dict = {}
    for cm in comments:
        parent = ((cm.get("query") or {}).get("post") or "").split("?")[0]
        txt = cm.get("commentary") or ""
        if parent and txt:
            comments_map.setdefault(parent, []).append(txt)
    fresh = process([_map_item(it) for it in posts], source="linkedin-post", comments_map=comments_map)
    print(f"LinkedIn harvest done. {len(fresh)} net-new leads.")
    return fresh


if __name__ == "__main__":
    if "--dry-run" in sys.argv:
        print("Queries that would be sent to the actor:")
        for i, q in enumerate(build_queries()[:PH["max_queries_per_run"]], 1):
            print(f"  {i}. {q}")
        print(f"\nActor: {AP['actor']} | postedLimit="
              f"{_DATE_MAP.get(PH.get('date_window', 'week'), 'week')} | "
              f"maxPosts/query={PH['max_posts_per_query']}")
    else:
        harvest()
