#!/usr/bin/env python3
"""Telegram job-channel harvester. Optional.

Reads new posts from the channels in config.json > telegram > channels as YOU, through a
Telethon user session (a bot cannot read a channel it does not admin, and many job channels
have their public web preview turned off). You must be a member of each channel.

One-time setup, in your own terminal (the login is interactive, an agent cannot do it):
    pip install telethon
    export TELEGRAM_API_ID=...  TELEGRAM_API_HASH=...     # from https://my.telegram.org
    python3 jobhunt/sources/telegram_posts.py --login      # phone number + login code once

Then:
    python3 jobhunt/sources/telegram_posts.py --dry-run    # parse and print, write nothing
    python3 jobhunt/sources/telegram_posts.py              # harvest new messages

The session file and api_hash are secrets. Both are gitignored. Never commit or share them.
Telethon is imported lazily so the parsing helpers work without it.
"""
from __future__ import annotations

import json
import os
import re
import sys
from urllib.parse import urlsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from posts_common import CFG, DATA, process  # noqa: E402
from settings import JOBHUNT  # noqa: E402

TG = CFG["telegram"]
STATE_PATH = os.path.join(DATA, "telegram_state.json")

URL_RE = re.compile(r"https?://[^\s)\]<>\"']+")
_TME_HOSTS = ("t.me", "telegram.me", "telegram.dog")

FRESHER_TERMS = [s.lower() for s in TG.get("fresher_terms", [])]
KEEP_YEARS = [s.lower() for s in TG.get("keep_batch_years", [])]
SENIOR_TERMS = [s.lower() for s in TG.get("senior_exclude", [])]
IGNORE_URL_SUBS = [s.lower() for s in TG.get("ignore_apply_url_substrings", [])]

_ATS_PATH_HOSTS = ("greenhouse.io", "lever.co")
_STOP_LABELS = {"boards", "jobs", "job-boards", "apply", "careers", "www", "app", "hire", "grnh"}
_JUNK_COMPANY_HOSTS = ("linkedin.com", "docs.google.com", "forms.gle", "topmate.io",
                       "bit.ly", "lnkd.in", "tinyurl.com", "unstop.com", "t.me")

# Structured post fields: "Company - X", "1) Company - X", "Role : SDE"
_COMPANY_RE = re.compile(r"(?im)^\s*(?:\d+[\).]\s*)?compan(?:y|ies)\s*[-:]\s*(.+)$")
_ROLE_RE = re.compile(r"(?im)^\s*(?:\d+[\).]\s*)?(?:role|position|profile)\s*[-:]\s*(.+)$")
_APPLY_RE = re.compile(r"(?is)apply\s*(?:link|here|via|at|now)?\s*[-:]?\s*(https?://\S+)")


def eligible_fresher(text: str) -> bool:
    """Keep batch-year / fresher / intern posts, drop explicitly senior ones.
    Ambiguous posts are kept and left to ranking. Edit the term lists in config."""
    t = (text or "").lower()
    keep = any(y in t for y in KEEP_YEARS) or any(k in t for k in FRESHER_TERMS)
    senior = any(s in t for s in SENIOR_TERMS)
    return not (senior and not keep)


def _first_field(text: str, pattern) -> str:
    m = pattern.search(text or "")
    return m.group(1).strip() if m else ""


def is_job_post(text: str) -> bool:
    """A listing has a Company or Role field. Channel promos and notices have neither."""
    return bool(_COMPANY_RE.search(text or "") or _ROLE_RE.search(text or ""))


def _external(url: str) -> bool:
    host = urlsplit(url).netloc.lower()
    if not host or any(host == h or host.endswith("." + h) for h in _TME_HOSTS):
        return False
    return not any(sub in url.lower() for sub in IGNORE_URL_SUBS)


def extract_apply_url(text: str, entity_urls: list[str] | None = None) -> str:
    m = _APPLY_RE.search(text or "")
    if m:
        cand = m.group(1).rstrip(".,);]")
        if _external(cand):
            return cand
    for u in (entity_urls or []) + URL_RE.findall(text or ""):
        if _external(u):
            return u.rstrip(".,);]")
    return ""


def company_from_url(url: str) -> str:
    if not url:
        return ""
    p = urlsplit(url)
    host = p.netloc.lower().replace("www.", "")
    if any(host == h or host.endswith("." + h) for h in _JUNK_COMPANY_HOSTS):
        return ""
    parts = [s for s in p.path.strip("/").split("/") if s]
    if any(host.endswith(h) for h in _ATS_PATH_HOSTS):
        return parts[0].title() if parts else ""
    if host.endswith("ashbyhq.com"):
        sub = host.split(".")[0]
        if sub not in _STOP_LABELS:
            return sub.title()
        return parts[0].title() if parts else ""
    for lab in host.split("."):
        if lab and lab not in _STOP_LABELS and lab not in ("com", "in", "io", "co", "org", "net", "ai"):
            return lab.title()
    return ""


def map_message(msg_id: int, text: str, date_iso: str, entity_urls: list[str], channel: str) -> dict:
    apply_url = extract_apply_url(text, entity_urls)
    return {
        "author": channel,
        "author_url": "",
        "text": text or "",
        "post_url": f"https://t.me/{channel}/{msg_id}",
        "age": date_iso or "",
        "job_url": apply_url,
        "job_company": _first_field(text, _COMPANY_RE) or company_from_url(apply_url),
        "job_title": _first_field(text, _ROLE_RE),
    }


def load_state() -> dict:
    if not os.path.exists(STATE_PATH):
        return {}
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state: dict) -> None:
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1)


def _client():
    try:
        from telethon.sync import TelegramClient
    except ImportError:
        sys.exit("ERROR: telethon not installed. Run: pip install telethon")
    api_id = os.environ.get(TG["api_id_env"])
    api_hash = os.environ.get(TG["api_hash_env"])
    if not api_id or not api_hash:
        sys.exit(f"ERROR: set {TG['api_id_env']} and {TG['api_hash_env']} (from https://my.telegram.org).")
    return TelegramClient(str(JOBHUNT / TG["session_file"]), int(api_id), api_hash)


def login() -> None:
    client = _client()
    client.start()  # prompts for phone number and the login code
    me = client.get_me()
    print(f"Logged in as {getattr(me, 'username', None) or getattr(me, 'first_name', '?')}.")
    client.disconnect()


def _entity_urls(msg) -> list[str]:
    urls = []
    try:
        from telethon.tl.types import MessageEntityTextUrl
        for ent in (msg.entities or []):
            if isinstance(ent, MessageEntityTextUrl) and ent.url:
                urls.append(ent.url)
    except Exception:
        pass
    return urls


def harvest(dry_run: bool = False) -> list[dict]:
    state = load_state()
    client = _client()
    client.connect()
    if not client.is_user_authorized():
        client.disconnect()
        sys.exit("ERROR: not authorized. Run `python3 jobhunt/sources/telegram_posts.py --login` "
                 "once in your own terminal first.")
    all_fresh: list[dict] = []
    limit = TG.get("max_messages_per_run", 200)
    for channel in TG["channels"]:
        min_id = int(state.get(channel, 0))
        raw, max_seen = [], min_id
        for msg in client.iter_messages(channel, min_id=min_id, limit=limit):
            text = msg.message or ""
            max_seen = max(max_seen, msg.id)
            if not text.strip() or not is_job_post(text) or not eligible_fresher(text):
                continue
            raw.append(map_message(msg.id, text, msg.date.isoformat() if msg.date else "",
                                   _entity_urls(msg), channel))
        print(f"[telegram:{channel}] since id {min_id}: {len(raw)} eligible new messages")
        if dry_run:
            for r in raw[:20]:
                print(f"   - {r['post_url']} co={r['job_company'] or '?'} apply={r['job_url'] or '(none)'}")
            continue
        all_fresh += process(raw, source="telegram", require_hiring_verb=False)
        if max_seen > min_id:
            state[channel] = max_seen
    client.disconnect()
    if not dry_run:
        save_state(state)
        print(f"Telegram harvest done. {len(all_fresh)} net-new leads.")
    else:
        print("(dry run: nothing written)")
    return all_fresh


if __name__ == "__main__":
    if "--login" in sys.argv:
        login()
    else:
        harvest(dry_run="--dry-run" in sys.argv)
