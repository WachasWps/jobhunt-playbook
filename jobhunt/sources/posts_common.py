#!/usr/bin/env python3
"""Shared pipeline for the hiring-post harvesters (LinkedIn, Threads, Telegram).

  raw post dicts (from linkedin_posts.py / threads_posts.py / telegram_posts.py)
    -> relevant()   must contain a hiring verb + a role keyword + pass the geo gate
    -> normalize()  emit a post-lead record (superset of the discover.py job schema)
    -> _is_noise()  drop aggregator bots, influencer listicles, skip-listed accounts
    -> dedupe()     drop if already seen (posts_seen.json) or company already contacted
    -> appended to data/posts_raw.json

Post-lead record:
  source, company, title, location, url, posted, remote, description, tags,
  author, author_url, contact_email, contact_channel, apply_url, post_excerpt, _geo_bucket
"""
from __future__ import annotations

import csv
import glob as _glob
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import OUTREACH, TRACKER_DIR, data_dir, load_config  # noqa: E402

CFG = load_config()
PH = CFG["post_harvest"]
GEO = CFG["geo_rules"]
DATA = str(data_dir())

SEEN_PATH = os.path.join(DATA, os.path.basename(PH.get("seen_store", "posts_seen.json")))
RAW_PATH = os.path.join(DATA, os.path.basename(PH.get("raw_output", "posts_raw.json")))
SKIPLIST_PATH = os.path.join(DATA, "posts_skiplist.json")

HIRING_VERBS = [v.lower() for v in PH["hiring_verbs"]]
ROLE_KWS = [k.lower() for k in CFG["role_keywords"]]
EXCL_KWS = [k.lower() for k in CFG["hard_exclude_keywords"]]
GULF_KWS = GEO["gulf_terms"]
HOME_KWS = GEO["india_terms"]
REMOTE_KWS = GEO["remote_terms"]
GULF_OK = bool(GEO.get("gulf_eligible", False))

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def build_queries() -> list[str]:
    return list(PH["query_templates"])


def relevant(text: str, require_hiring_verb: bool = True) -> bool:
    """True if the post is a real hiring signal for the roles in config.
    require_hiring_verb=False for sources that only carry job posts (Telegram job channels)."""
    t = (text or "").lower()
    if require_hiring_verb and not any(v in t for v in HIRING_VERBS):
        return False
    if not any(k in t for k in ROLE_KWS):
        return False
    if any(k in t for k in EXCL_KWS):
        return False
    if not GULF_OK and any(k in t for k in GULF_KWS) and not any(k in t for k in HOME_KWS + REMOTE_KWS):
        return False
    return True


def extract_contacts(text: str, comments: list[str] | None = None) -> tuple[str, str]:
    """Return (email_or_empty, channel). Scans the post first, then comments
    (recruiters often drop the email in a comment)."""
    for blob in [text] + (comments or []):
        for m in EMAIL_RE.finditer(blob or ""):
            email = m.group(0).lower()
            if "example.com" in email or "sentry" in email or email.endswith((".png", ".jpg")):
                continue
            return email, "email"
    return "", "linkedin-dm"


def _geo_from_text(text: str) -> tuple[str, str]:
    t = (text or "").lower()
    if any(k in t for k in HOME_KWS):
        if any(k in t for k in REMOTE_KWS):
            return "india-remote", "Home country / Remote"
        return "india", "Home country"
    if any(k in t for k in REMOTE_KWS):
        return "global-remote", "Remote"
    if any(k in t for k in GULF_KWS):
        return "gulf", "Gulf"
    return "unknown", ""


FREE_MAIL = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "proton.me",
             "protonmail.com", "icloud.com", "rediffmail.com", "aol.com", "live.com",
             "ymail.com", "googlemail.com"}

# Job-board, staffing and repost-bot accounts (matched in author or company).
AGGREGATOR_TOKENS = ["remote job", "remotejob", "rubyonremote", "remoteyeah", "remoteok",
                     "big remote", "vacancies", "job alert", "hiring alert", "job portal",
                     "jobs board", "jobboard", "naukri", "indeed", "weworkremotely", "himalayas",
                     "remotive", "jobspresso", "workana", "freshersworld", "hirist", "instahyre",
                     "staffing", "consultancy", "recruitment services", "search solutions",
                     "talent solutions", "c2c / w2", "c2c/w2"]

# Influencer "listicle" tells (engagement-bait reposts of other companies' openings).
# Only applied to posts with no email or a free-mail address, so real hiring managers
# with a corporate email are never dropped.
LISTICLE_TOKENS = ["verified opening", "mass hiring", "openings across", "companies hiring",
                   "highest-paying", "highest paying", "freshers", "off campus", "off-campus",
                   "register by", "hiring right now", "batch 2024", "batch 2025", "batch 2026",
                   "\U0001F6A8", "1\ufe0f\u20e3", "2\ufe0f\u20e3", "3\ufe0f\u20e3",
                   "multiple it job", "multiple remote", "multiple roles", "multiple openings",
                   "hiring globally", "opportunities worldwide", "hiring worldwide",
                   "mailing list", "jobs like below", "500+ jobs", "daily job"]


def _company_from_email(email: str) -> str:
    if not email or "@" not in email:
        return ""
    dom = email.split("@")[1].lower().strip()
    if dom in FREE_MAIL:
        return ""
    label = dom.split(".")[0]
    return label[:1].upper() + label[1:] if label else ""


def _infer_company(author: str, text: str) -> str:
    m = re.search(r"(?<!\w)@([A-Za-z0-9_\-]{2,40})", text or "")
    if m:
        return m.group(1)
    m = re.search(r"\bat\s+([A-Z][A-Za-z0-9\s&\.]{1,40}?)(?:\s*[,!.\n]|$)", text or "")
    if m:
        return m.group(1).strip()
    return author


def _load_skiplist() -> list[str]:
    """Your own list of recurring-noise accounts (staffing firms, weekly reposters).
    data/posts_skiplist.json is a JSON list of lowercase substrings."""
    try:
        with open(SKIPLIST_PATH, encoding="utf-8") as f:
            return [s.lower() for s in json.load(f)]
    except Exception:
        return []


SKIPLIST = _load_skiplist()


def _is_noise(rec: dict) -> bool:
    blob = (rec.get("author", "") + " " + rec.get("company", "")).lower()
    if any(tok in blob for tok in AGGREGATOR_TOKENS):
        return True
    idblob = blob + " " + rec.get("contact_email", "").lower()
    if any(s in idblob for s in SKIPLIST):
        return True
    if rec.get("source") == "telegram":
        return False  # job channel: "batch 2026" and "freshers" are wanted signals there
    email = rec.get("contact_email", "")
    dom = email.split("@")[1].lower() if "@" in email else ""
    if (not email) or (dom in FREE_MAIL):
        t = rec.get("description", "").lower()
        if t.count("lnkd.in/") >= 2:
            return True
        if any(tok in t for tok in LISTICLE_TOKENS):
            return True
    return False


def _infer_title(text: str) -> str:
    t = (text or "").lower()
    for kw in ["founding engineer", "ai engineer", "ml engineer", "backend engineer",
               "full stack engineer", "fullstack engineer", "frontend engineer", "data engineer",
               "software engineer", "forward deployed engineer", "platform engineer"]:
        if kw in t:
            return kw.title()
    return "Engineer (see post)"


def normalize(raw: dict, source: str, comments: list[str] | None = None) -> dict:
    text = (raw.get("text") or "").strip()
    author = (raw.get("author") or "").strip()
    author_url = (raw.get("author_url") or raw.get("authorUrl") or "").strip()
    post_url = (raw.get("post_url") or raw.get("postUrl") or "").strip()
    age = (raw.get("age") or "").strip()

    email, channel = extract_contacts(text, comments)
    if source == "threads" and not email:
        channel = "threads-dm"
    if source == "telegram" and not email:
        channel = "apply-link"

    job_title = (raw.get("job_title") or "").strip()
    job_location = (raw.get("job_location") or "").strip()
    job_company = (raw.get("job_company") or "").strip()
    job_url = (raw.get("job_url") or "").strip()
    geo, loc_label = _geo_from_text(text + " " + job_location)

    return {
        "source": source,
        "company": job_company or _company_from_email(email) or _infer_company(author, text),
        "title": job_title or _infer_title(text),
        "location": job_location or loc_label,
        "url": post_url,
        "posted": age,
        "remote": geo in ("global-remote", "india-remote"),
        "tags": [],
        "description": text,
        "author": author,
        "author_url": author_url,
        "contact_email": email,
        "contact_channel": channel,
        "apply_url": job_url,
        "post_excerpt": text[:200].replace("\n", " "),
        "_geo_bucket": geo,
    }


def _load_seen() -> set:
    if not os.path.exists(SEEN_PATH):
        return set()
    try:
        with open(SEEN_PATH, encoding="utf-8") as f:
            return set(json.load(f).get("keys", []))
    except Exception:
        return set()


def _save_seen(keys: set) -> None:
    allk = sorted(_load_seen() | keys)
    with open(SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump({"keys": allk}, f, indent=1)


def _content_hash(text: str) -> str:
    return hashlib.md5((text or "")[:500].encode()).hexdigest()[:12]


def _already_contacted_companies() -> set:
    """Lowercased company names from every tracker CSV (tracker/*.csv and outreach/*tracker*.csv)
    and any outreach batch JSON list, so you never pitch the same company twice by accident."""
    companies = set()
    csvs = _glob.glob(str(TRACKER_DIR / "*.csv")) + _glob.glob(str(OUTREACH / "*tracker*.csv"))
    for fpath in csvs:
        try:
            with open(fpath, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    co = (row.get("company") or "").strip().lower()
                    if co:
                        companies.add(co)
        except Exception:
            pass
    for fpath in _glob.glob(str(OUTREACH / "*.json")):
        try:
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    co = (item.get("company") or "").strip().lower() if isinstance(item, dict) else ""
                    if co:
                        companies.add(co)
        except Exception:
            pass
    return companies


def dedupe(records: list[dict]) -> list[dict]:
    seen = _load_seen()
    contacted = _already_contacted_companies()
    new_keys, out = set(), []
    for r in records:
        url = r.get("url", "")
        chash = _content_hash(r.get("description", ""))
        co = r.get("company", "").lower()
        if (url and url in seen) or chash in seen:
            continue
        if co and co in contacted:
            continue
        out.append(r)
        if url:
            new_keys.add(url)
        new_keys.add(chash)
    _save_seen(new_keys)
    return out


def append_raw(records: list[dict]) -> int:
    existing = []
    if os.path.exists(RAW_PATH):
        try:
            with open(RAW_PATH, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass
    with open(RAW_PATH, "w", encoding="utf-8") as f:
        json.dump(existing + records, f, indent=1, ensure_ascii=False)
    return len(records)


def process(raw_posts: list[dict], source: str,
            comments_map: dict[str, list[str]] | None = None,
            require_hiring_verb: bool = True) -> list[dict]:
    """Filter, normalize, de-noise and dedupe a batch. Returns net-new records
    (already appended to posts_raw.json)."""
    comments_map = comments_map or {}
    filtered = [r for r in raw_posts if relevant(r.get("text", ""), require_hiring_verb)]
    normed = [normalize(r, source, comments_map.get(r.get("post_url", ""), [])) for r in filtered]
    clean = [r for r in normed if not _is_noise(r)]
    fresh = dedupe(clean)
    if fresh:
        append_raw(fresh)
    print(f"  [{source}] raw={len(raw_posts)} relevant={len(filtered)} "
          f"non-noise={len(clean)} net-new={len(fresh)} -> {RAW_PATH}")
    return fresh
