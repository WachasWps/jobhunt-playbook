#!/usr/bin/env python3
"""Rank and filter discovered jobs and post-leads against your profile.

Reads   data/jobs_raw.json (board jobs from sources/discover.py)
        data/posts_raw.json (post-leads from the post harvesters)
Writes  data/jobs_ranked.csv, data/posts_ranked.csv,
        data/tracker.csv (merge-aware: keeps statuses you set by hand),
        data/dashboard.html

Run:    python3 jobhunt/rank.py

Importing this module has no side effects. Only running it as a script writes files,
so tests and agents can import score() and friends safely.
"""
from __future__ import annotations

import csv
import hashlib
import html as _html
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from settings import data_dir, load_config, load_profile  # noqa: E402

CFG = load_config()
PROF = load_profile()
NOW = datetime.now(timezone.utc)

GEO = CFG["geo_rules"]
SC = CFG.get("scoring", {})
DOWN = [k.lower() for k in CFG["downrank_keywords"]]
EXCL = [k.lower() for k in CFG["hard_exclude_keywords"]]
ROLE = [k.lower() for k in CFG["role_keywords"]]
HOME_CITY = (PROF.get("identity", {}).get("location_city") or "").strip().lower()
if HOME_CITY.startswith("<"):
    HOME_CITY = ""

AI = ["ai", "ml", "machine learning", "machine-learning", "llm", "genai", "generative",
      "deep learning", "nlp", "rag", "agent", "applied scientist", "data scien"]
FS = ["full stack", "fullstack", "full-stack", "frontend", "front-end", "front end",
      "react", "next.js", "node"]
BACK = ["backend", "back-end", "back end", "api", "platform engineer", "distributed"]
FOUND = ["founding engineer", "founding member", "first engineer"]
FRESH = ["new grad", "new-grad", "graduate", "junior", "entry level", "entry-level",
         "0-2 year", "early career", "university grad"]

# Titles that contain "engineer" or "developer" but are not software roles.
TITLE_EXCLUDE = ["support engineer", "sales engineer", "solutions engineer", "customer engineer",
    "field engineer", "value engineer", "business engineer", "technical trainer", "trainer",
    "implementation engineer", "escalation", "claims", "supply chain", "analyst", "specialist",
    "coordinator", "investment", "accountant", "recruit", "designer", "marketing", "strategist",
    "rfp", "bid manager", "video editor", "editor", "go-to-market", "martech", "demo engineer",
    "content", "copywriter", "administrator", "creative producer", "producer"]

TITLE_ENG = AI + FS + BACK + FOUND + ["software eng", "software dev", "developer", "sde",
    "programmer", "technical staff", "applied scientist", "research engineer",
    "forward deployed", "data scientist", "ml engineer", "data engineer"]

POST_SOURCES = ("linkedin-post", "threads", "telegram")


def hasw(text: str, kws) -> bool:
    """Word or phrase boundary match, so 'ai' does not match 'claims' and 'ml' not 'html'."""
    t = (text or "").lower()
    for k in (x.lower().strip() for x in kws):
        if not k:
            continue
        if " " in k or "." in k or "+" in k:
            if k in t:
                return True
        elif re.search(r"\b" + re.escape(k) + r"\b", t):
            return True
    return False


def days_old(posted):
    if not posted:
        return None
    try:
        if re.fullmatch(r"\d{9,13}", str(posted)):
            ts = int(posted)
            ts = ts / 1000 if ts > 1e11 else ts
            d = datetime.fromtimestamp(ts, timezone.utc)
        else:
            d = datetime.fromisoformat(str(posted).replace("Z", "+00:00"))
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
        return (NOW - d).days
    except Exception:
        return None


def role_bucket(title: str, desc: str) -> str:
    """The TITLE must signal a software/ML role, else 'other' (dropped).
    The description only disambiguates among real engineering titles."""
    tl, dl = (title or "").lower(), (desc or "").lower()
    if any(x in tl for x in TITLE_EXCLUDE):
        return "other"
    is_eng = hasw(tl, TITLE_ENG) or re.search(r"\bengineer(ing)?\b", tl) or re.search(r"\bdeveloper\b", tl)
    if not is_eng:
        return "other"
    if hasw(tl, FOUND):
        return "founding"
    if hasw(tl, AI) or "applied scientist" in tl or "research engineer" in tl:
        return "ai"
    if hasw(tl, FS):
        return "fullstack"
    if hasw(tl, BACK):
        return "backend"
    if hasw(dl, AI) and not hasw(dl, FS):
        return "ai"
    return "swe"


def geo_classify(job: dict):
    """Return (geo_bucket, eligible, label). Tuned for an India-based candidate by default;
    edit geo_rules in config.json for another country."""
    loc = (job.get("location") or "").lower()
    desc = (job.get("description") or "").lower()
    blob = loc + " | " + desc
    remote_flag = job.get("remote") is True or any(k in loc for k in GEO["remote_terms"])
    is_home = any(k in blob for k in GEO["india_terms"]) or bool(re.search(r"(^|[/(,|])\s*in\s*([/),|]|$)", loc))  # "IN" as a country code in a list
    is_gulf = any(k in blob for k in GEO["gulf_terms"])
    has_sponsor = any(k in desc for k in GEO["sponsor_terms"])
    restricted = bool(re.search(
        r"(us|u\.s\.|usa|united states|emea|europe|uk|canada|latam|americas)[ -]?(only|based|resident|time ?zone)",
        blob)) or "must be located in" in blob or "must reside in" in blob \
        or bool(re.search(r"\b(us|usa|united states|uk|canada|eu|europe|emea|americas|latam)\b", loc))
    if is_home:
        return "india", True, "Home country"
    if remote_flag:
        if "india" in blob or "worldwide" in blob or "anywhere" in blob or "global" in blob:
            return "global-remote", True, "Remote (open to your country)"
        if restricted:
            return "remote-restricted", False, "Remote but region-locked"
        return "global-remote", True, "Remote (eligibility unclear, verify on the live posting)"
    if is_gulf:
        ok = bool(GEO.get("gulf_eligible", False))
        return "gulf", ok, "Gulf on-site" + ("" if ok else " (excluded in config)")
    if has_sponsor:
        return "foreign-sponsor", True, "Foreign on-site with a sponsorship signal"
    if loc.strip():
        return "foreign-onsite", False, "Foreign on-site, no sponsorship signal"
    return "unknown", True, "Location unclear"


def score(job: dict):
    """Return a score dict, or None if the job is not a relevant role."""
    title = job.get("title") or ""
    desc = job.get("description") or ""
    tl = title.lower()
    if any(k in tl for k in EXCL):
        return None
    bucket = role_bucket(title, desc)
    if bucket == "other":
        return None
    geo, eligible, geo_label = geo_classify(job)
    s = 40
    weights = SC.get("role_weights", {"founding": 28, "ai": 28, "fullstack": 24, "backend": 22, "swe": 18})
    s += weights.get(bucket, 0)
    if hasw(tl, ROLE):
        s += 6
    s += {"india": 16, "global-remote": 16, "gulf": 9, "foreign-sponsor": 8,
          "unknown": 4, "remote-restricted": -30, "foreign-onsite": -30}.get(geo, 0)
    if not eligible:
        s -= 40
    senior = hasw(tl, DOWN)
    if senior:
        s -= 26
    elif hasw(desc, DOWN):
        s -= 6
    if hasw(tl, FRESH) or hasw(desc, FRESH):
        s += 9
    if HOME_CITY and HOME_CITY in ((job.get("location") or "") + " " + desc).lower():
        s += SC.get("home_city_boost", 10)
    d = days_old(job.get("posted"))
    if d is not None:
        if d <= 2:
            s += 10
        elif d <= 7:
            s += 5
        elif d > 60:
            s -= 6
    s = max(0, min(100, s))
    return {"score": s, "tier": "skip", "role": bucket, "geo": geo, "geo_label": geo_label,
            "eligible": eligible, "senior": senior, "days_old": d if d is not None else ""}


def resume_variant(job: dict, role: str, geo: str) -> str:
    """Pick a resume from profile.resume_variant_map: <role>_<geo>, then <role>, then default.
    Fresher-framed posts (new grad, intern, batch year) use the 'fresher' entry if present."""
    m = {k: v for k, v in PROF.get("resume_variant_map", {}).items() if not k.startswith("_")}
    blob = ((job.get("title") or "") + " " + (job.get("description") or "")).lower()
    if "fresher" in m and (hasw(blob, FRESH) or "fresher" in blob or "intern" in blob):
        return m["fresher"]
    g = "india" if geo == "india" else "global"
    return m.get(f"{role}_{g}") or m.get(role) or m.get("default", "")


def jid(job: dict) -> str:
    key = (job.get("company", "") + "|" + job.get("title", "") + "|" + job.get("url", ""))
    return hashlib.md5(key.encode()).hexdigest()[:10]


def assign_tiers(ranked: list) -> None:
    """T1 = deep tailoring + outreach, T2 = quick apply. Caps keep T1 human-sized."""
    t1_cap = SC.get("tier1_cap", 40)
    t2_cap = SC.get("tier2_cap", 300)
    per_co = SC.get("per_company_tier1_cap", 3)
    t1_min = SC.get("tier1_min_score", 66)
    t_min = SC.get("tier_min_score", 50)
    t1n = t2n = 0
    co_t1 = defaultdict(int)
    for r in ranked:
        if not r["eligible"] or r["score"] < t_min:
            r["tier"] = "skip"
            continue
        co = (r.get("company") or "").lower()
        if t1n < t1_cap and r["score"] >= t1_min and not r["senior"] and co_t1[co] < per_co:
            r["tier"] = "T1"
            t1n += 1
            co_t1[co] += 1
        elif t2n < t2_cap:
            r["tier"] = "T2"
            t2n += 1
        else:
            r["tier"] = "skip"


def rank_all(jobs: list) -> list:
    ranked = []
    for j in jobs:
        sc = score(j)
        if not sc:
            continue
        ranked.append({**j, **sc, "id": jid(j), "resume_variant": resume_variant(j, sc["role"], sc["geo"])})
    ranked.sort(key=lambda r: r["score"], reverse=True)
    assign_tiers(ranked)
    return ranked


def _load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_outputs(ranked: list, data: str) -> None:
    cols_posts = ["score", "tier", "role", "geo", "geo_label", "eligible", "days_old", "company", "title",
                  "location", "source", "resume_variant", "url", "apply_url", "contact_email",
                  "contact_channel", "author", "author_url", "post_excerpt"]
    with open(os.path.join(data, "posts_ranked.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols_posts, extrasaction="ignore")
        w.writeheader()
        for r in ranked:
            if r.get("source", "") in POST_SOURCES:
                w.writerow(r)

    cols_jobs = ["score", "tier", "role", "geo", "geo_label", "eligible", "days_old", "company",
                 "title", "location", "source", "resume_variant", "url"]
    with open(os.path.join(data, "jobs_ranked.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols_jobs, extrasaction="ignore")
        w.writeheader()
        for r in ranked:
            if r.get("source", "") not in POST_SOURCES:
                w.writerow(r)

    # tracker.csv is merge-aware: hand-set fields survive a re-rank
    tpath = os.path.join(data, "tracker.csv")
    prev = {}
    if os.path.exists(tpath):
        with open(tpath, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                prev[row["id"]] = row
    tcols = ["id", "tier", "score", "role", "geo", "company", "title", "location", "source",
             "resume_variant", "status", "applied_on", "outreach_status", "followup_on", "url",
             "notes", "contact_email", "contact_channel", "author", "author_url", "post_excerpt"]
    queue = [r for r in ranked if r["tier"] in ("T1", "T2")]
    queue_ids = {r["id"] for r in queue}
    with open(tpath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=tcols, extrasaction="ignore")
        w.writeheader()
        for r in queue:
            p = prev.get(r["id"], {})
            w.writerow({**r,
                        "status": p.get("status") or "queued",
                        "applied_on": p.get("applied_on", ""),
                        "outreach_status": p.get("outreach_status", ""),
                        "followup_on": p.get("followup_on", ""),
                        "notes": p.get("notes", "")})
        # keep rows you touched by hand even if they fell out of the queue
        for pid, p in prev.items():
            if pid not in queue_ids and (p.get("status", "queued") != "queued" or p.get("notes")):
                w.writerow(p)

    t1 = [r for r in queue if r["tier"] == "T1"]
    t2 = [r for r in queue if r["tier"] == "T2"]
    name = PROF.get("identity", {}).get("full_name", "") or "Job"
    if name.startswith("<"):
        name = "Job"
    esc = _html.escape

    def rows(rs):
        out = []
        for r in rs:
            out.append(
                f"<tr><td>{r['score']}</td><td>{r['tier']}</td><td>{r['role']}</td><td>{r['geo']}</td>"
                f"<td>{esc((r.get('company') or '?')[:28])}</td><td>{esc((r.get('title') or '')[:60])}</td>"
                f"<td>{esc((r.get('location') or '')[:24])}</td><td>{esc(r.get('source', ''))}</td>"
                f"<td><code>{esc(r.get('resume_variant', ''))}</code></td>"
                f"<td><a href='{esc(r.get('url', ''))}' target='_blank'>open</a></td></tr>")
        return "\n".join(out)

    head = ("<tr><th>score</th><th>tier</th><th>role</th><th>geo</th><th>company</th><th>title</th>"
            "<th>location</th><th>src</th><th>resume</th><th>link</th></tr>")
    gc = Counter(r["geo"] for r in queue)
    rc = Counter(r["role"] for r in queue)
    page = f"""<!doctype html><meta charset=utf-8><title>{esc(name)} pipeline</title>
<style>body{{font:13px/1.4 -apple-system,Segoe UI,Arial;margin:24px;color:#1a1a1a}}
table{{border-collapse:collapse;width:100%;margin:8px 0 28px}}
th,td{{border:1px solid #ddd;padding:4px 7px;text-align:left;vertical-align:top}}
th{{background:#1f3a5f;color:#fff;position:sticky;top:0}}code{{font-size:11px;color:#444}}
.sum{{background:#f3f6fb;padding:12px 16px;border-radius:8px;margin-bottom:18px}}</style>
<h1>{esc(name)} pipeline</h1>
<div class=sum><b>Scored:</b> {len(ranked)} | <b>Tier 1:</b> {len(t1)} | <b>Tier 2:</b> {len(t2)}<br>
<b>Queue by geo:</b> {esc(str(dict(gc)))} | <b>by role:</b> {esc(str(dict(rc)))}<br>
<small>Generated {NOW.strftime('%Y-%m-%d %H:%M UTC')}. Source of truth: data/tracker.csv. You review and submit everything.</small></div>
<h2>Tier 1: {len(t1)} (tailor + outreach)</h2><table>{head}
{rows(t1)}</table>
<h2>Tier 2: {len(t2)} (quick apply)</h2><table>{head}
{rows(t2[:300])}</table>"""
    with open(os.path.join(data, "dashboard.html"), "w", encoding="utf-8") as f:
        f.write(page)

    tc = Counter(r["tier"] for r in ranked)
    print(f"scored relevant: {len(ranked)} | T1={len(t1)} T2={len(t2)} skip={tc['skip']}")
    print(f"queue by geo: {dict(gc)}")
    print(f"queue by role: {dict(rc)}")
    print(f"-> {data}/jobs_ranked.csv, posts_ranked.csv, tracker.csv, dashboard.html")


def main() -> None:
    data = str(data_dir())
    jobs = _load_json(os.path.join(data, "jobs_raw.json")) + _load_json(os.path.join(data, "posts_raw.json"))
    if not jobs:
        print(f"No jobs found in {data}. Run sources/discover.py (or a post harvester) first.")
        return
    write_outputs(rank_all(jobs), data)


if __name__ == "__main__":
    main()
