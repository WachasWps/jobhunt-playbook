#!/usr/bin/env python3
"""Turn ranked post-leads into FIRST-DRAFT cold emails, DM notes and an apply shortlist.

Reads   jobhunt/data/posts_ranked.csv (from rank.py) and profile.json > outreach
Writes  outreach/posts-batch{N}-email.json     email drafts (to, subject, body, resume)
        outreach/posts-batch{N}-linkedin.md    DM notes for leads with no email
        outreach/posts-batch{N}-tracker.csv    send tracker (read by tomorrow's dedupe)
        outreach/telegram-apply-batch{N}.md    apply-link shortlist from job channels

Run:    python3 jobhunt/draft_posts.py

These are skeletons. The agent rewrites every draft per prompts/cold-outreach-drafter.md
(hook about THEM, proof from the factsheet, one binary CTA, a true P.S.) and verifies each
address per docs/05. Nothing here sends anything.
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from settings import OUTREACH, data_dir, load_config, load_profile  # noqa: E402

CFG = load_config()
PROF = load_profile()
PH = CFG["post_harvest"]
DAILY_CAP = PH.get("daily_draft_cap", 15)
OUT = str(OUTREACH)

BANNED_RE = re.compile("[\u2014\u2013\u00b7]")   # em-dash, en-dash, middle dot
OUTREACH_CFG = PROF.get("outreach", {})
SIG_LINES = [s for s in OUTREACH_CFG.get("signature_lines", []) if not s.startswith("<")] or \
    [PROF.get("identity", {}).get("full_name", "")]
ANGLES = [a for a in OUTREACH_CFG.get("pitch_angles", []) if not str(a.get("key", "")).startswith("<")]
DEFAULT_ANGLE = OUTREACH_CFG.get("default_angle", "")
PS_LINES = [s for s in OUTREACH_CFG.get("ps_lines", []) if not s.startswith("<")]


def _kw(text: str, kws) -> bool:
    """Word-boundary match so 'voice' does not match 'invoice'."""
    t = (text or "").lower()
    for k in (x.lower() for x in kws):
        if " " in k:
            if k in t:
                return True
        elif re.search(r"\b" + re.escape(k) + r"\b", t):
            return True
    return False


def _pick_angle(post_text: str) -> dict:
    for a in ANGLES:
        if _kw(post_text, a.get("keywords", [])):
            return a
    for a in ANGLES:
        if a.get("key") == DEFAULT_ANGLE:
            return a
    return ANGLES[0] if ANGLES else {"key": "none", "proof": "[ADD PROOF FROM factsheet.md]"}


def _greeting(author: str, company: str) -> str:
    first = author.split()[0] if author else ""
    comp = (company or "").lower()
    if first and first.lower() not in comp and comp not in first.lower():
        return f"Hi {first},"
    return "Hi there,"


def _subject(title: str, company: str) -> str:
    t = (title or "").strip()
    if t and t != "Engineer (see post)":
        return f"your {t.lower()} post"
    if company and "." not in company:
        return f"your {company} hiring post"
    return "your hiring post"


def _body(lead: dict, angle: dict) -> str:
    title = lead.get("title") or "engineering"
    company = lead.get("company") or ""
    at = f" at {company}" if company and company.lower() not in title.lower() else ""
    lines = [
        _greeting(lead.get("author", ""), company),
        "",
        f"Saw your post about the {title} role{at}. [HOOK: one specific line about THEM or the post]",
        "",
        angle.get("proof", ""),
        "",
        "Worth a quick 15 min chat?",
        "",
        *SIG_LINES,
    ]
    if PS_LINES:
        lines += ["", "P.S. " + PS_LINES[0]]
    return BANNED_RE.sub(",", "\n".join(lines))


def _words(text: str) -> int:
    return len(re.sub(r"\[[^\]]*\]", " ", text).split())


def _next_n(prefix: str, suffix: str) -> int:
    nums = [int(m.group(1)) for f in glob.glob(os.path.join(OUT, f"{prefix}*{suffix}"))
            for m in [re.search(re.escape(prefix) + r"(\d+)", os.path.basename(f))] if m]
    return max(nums) + 1 if nums else 1


def _prior(pattern: str, col: str) -> set:
    vals = set()
    for tf in glob.glob(os.path.join(OUT, pattern)):
        with open(tf, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get(col):
                    vals.add(row[col].lower() if col == "email" else row[col])
    return vals


def _score(r) -> int:
    try:
        return int(r.get("score", 0))
    except (TypeError, ValueError):
        return 0


def write_apply_shortlist(rows: list) -> None:
    prior = _prior("telegram-apply-batch*-tracker.csv", "post_url")
    cap = CFG.get("telegram", {}).get("daily_shortlist_cap", 25)
    leads = sorted([r for r in rows if r.get("source") == "telegram" and not r.get("contact_email")
                    and r.get("url", "") not in prior], key=_score, reverse=True)[:cap]
    if not leads:
        return
    n = _next_n("telegram-apply-batch", "-tracker.csv")
    md = os.path.join(OUT, f"telegram-apply-batch{n}.md")
    tr = os.path.join(OUT, f"telegram-apply-batch{n}-tracker.csv")
    with open(md, "w", encoding="utf-8") as f:
        f.write(f"# Apply shortlist {n} ({date.today()})\n\nCheck fit, then apply yourself. Nothing is auto-applied.\n\n")
        f.write("| # | Score | Role | Company | Resume | Apply | Post |\n|---|---|---|---|---|---|---|\n")
        for i, r in enumerate(leads, 1):
            f.write(f"| {i} | {r.get('score', '')} | {r.get('role', '')} | {(r.get('company') or '?')[:28]} | "
                    f"`{r.get('resume_variant', '')}` | {r.get('apply_url') or '(see post)'} | {r.get('url', '')} |\n")
    with open(tr, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["company", "role", "apply_url", "resume_variant", "post_url", "score", "applied"],
                           extrasaction="ignore")
        w.writeheader()
        for r in leads:
            w.writerow({**r, "post_url": r.get("url", ""), "applied": ""})
    print(f"Apply shortlist: {len(leads)} roles -> {md}")


def run() -> None:
    ranked = os.path.join(str(data_dir()), "posts_ranked.csv")
    if not os.path.exists(ranked):
        print(f"No {ranked}. Run a harvester and rank.py first.")
        return
    os.makedirs(OUT, exist_ok=True)
    with open(ranked, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    write_apply_shortlist(rows)

    done_emails = _prior("posts-batch*-tracker.csv", "email")
    done_urls = _prior("posts-batch*-tracker.csv", "post_url")
    cands = [r for r in rows if not (r.get("source") == "telegram" and not r.get("contact_email"))]
    leads = sorted([r for r in cands if (r.get("contact_email") or _score(r) >= 70)
                    and r.get("contact_email", "").lower() not in done_emails
                    and r.get("url", "") not in done_urls], key=_score, reverse=True)
    seen, deduped = set(), []
    for r in leads:
        e = r.get("contact_email", "").lower()
        if e and e in seen:
            continue
        seen.add(e) if e else None
        deduped.append(r)
    email_leads = [r for r in deduped if r.get("contact_email")][:DAILY_CAP]
    dm_leads = [r for r in deduped if not r.get("contact_email")][:max(0, DAILY_CAP - len(email_leads))]
    if not email_leads and not dm_leads:
        print("No actionable post-leads. Nothing to draft.")
        return

    n = _next_n("posts-batch", "-email.json")
    drafts, dms, track = [], [], []
    for lead in email_leads + dm_leads:
        text = lead.get("post_excerpt", "") + " " + lead.get("title", "")
        angle = _pick_angle(text)
        email = lead.get("contact_email", "")
        if email:
            body = _body(lead, angle)
            drafts.append({"company": lead.get("company", ""), "to": email,
                           "email_verified": False, "subject": _subject(lead.get("title", ""), lead.get("company", "")),
                           "body": body, "_word_count": _words(body), "_angle": angle.get("key"),
                           "_post_url": lead.get("url", ""), "_author": lead.get("author", ""),
                           "_author_url": lead.get("author_url", ""), "_resume": lead.get("resume_variant", "")})
        else:
            first = (lead.get("author") or "").split(" ")[0] or "there"
            proof = (angle.get("proof", "").split(". ")[0]).rstrip(".") + "."
            note = BANNED_RE.sub(",", f"Hi {first}, saw your post about the {lead.get('title', 'role')} role. "
                                      f"{proof} Open to a quick chat?")
            dms.append({"company": lead.get("company", ""), "profile": lead.get("author_url", ""),
                        "post": lead.get("url", ""), "note": note[:300], "resume": lead.get("resume_variant", "")})
        track.append({"company": lead.get("company", ""), "email": email,
                      "channel": "email" if email else lead.get("contact_channel", "linkedin-dm"),
                      "linkedin": lead.get("author_url", ""), "post_url": lead.get("url", ""),
                      "tier": lead.get("tier", ""), "email_sent": "", "li_sent": "", "reply": ""})

    ej = os.path.join(OUT, f"posts-batch{n}-email.json")
    with open(ej, "w", encoding="utf-8") as f:
        json.dump(drafts, f, indent=1, ensure_ascii=False)
    dm = os.path.join(OUT, f"posts-batch{n}-linkedin.md")
    with open(dm, "w", encoding="utf-8") as f:
        f.write(f"# DM notes, batch {n} ({date.today()})\n\nSend from your own account. Max 300 characters per connection note.\n\n")
        for d in dms:
            f.write(f"## {d['company']}\n- Profile: {d['profile']}\n- Post: {d['post']}\n- Resume: {d['resume']}\n\n```\n{d['note']}\n```\n\n")
    tr = os.path.join(OUT, f"posts-batch{n}-tracker.csv")
    with open(tr, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["company", "email", "channel", "linkedin", "post_url", "tier",
                                          "email_sent", "li_sent", "reply"])
        w.writeheader()
        w.writerows(track)
    print(f"Batch {n}: {len(drafts)} email drafts -> {ej}\n         {len(dms)} DM notes -> {dm}\n         tracker -> {tr}")
    print("Next: the agent rewrites each draft (prompts/cold-outreach-drafter.md) and verifies every address.")


if __name__ == "__main__":
    run()
