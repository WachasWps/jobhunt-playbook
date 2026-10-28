# 10. Ideas borrowed (approach only) from other open-source job-hunt repos

Two open-source projects shaped parts of this playbook. Credit to:

- **[career-ops](https://github.com/career-ops-hq/career-ops)** by career-ops-hq (MIT).
- **[dossier](https://github.com/AienTech/dossier)** by AienTech (AGPL). Ideas only. No code from dossier is copied here, and none should be: AGPL code would change this repo's license obligations.

Each entry below is the idea, then how to adapt it to this repo. Some are already partly in place, the rest are a roadmap. Every adaptation must still follow the hard rules in `AGENTS.md`.

## 1. Warm-intro join

**What:** before cold-emailing a company, check whether you already know someone there.

**How to adapt:** LinkedIn lets you export your connections (Settings, Data privacy, Get a copy of your data, Connections). Save `Connections.csv` locally (gitignore it, it holds other people's data). A small script joins its `Company` column against the companies in `jobhunt/data/tracker.csv` and your shortlist, with fuzzy matching on company names. For every match, the agent drafts a short referral ask for the user to send before any cold email to that company. A weak referral beats a strong cold email.

## 2. Full public-ATS sweep

**What:** instead of a hand-picked company list, walk a community-maintained list of Greenhouse, Lever and Ashby board slugs, and keep only roles that are title-matched, in an eligible location, and posted within the last 3 days. Applying early wins, so freshness is the main filter.

**How to adapt:** add an optional `slug_lists` input to `discover.py` (a text file of `ats,slug` lines). Fetch each board's public JSON, filter before saving (title match from `role_keywords`, geography from `geo_rules`, posted date 3 days or less), and write only survivors to `jobs_raw.json`. **Cap concurrency per host** (for example 4 parallel requests per ATS domain with a small delay) so you stay polite and do not get rate limited. Cache slugs that return 404 and skip them next run.

## 3. JD-first requirements list and keyword coverage

**What:** before tailoring, extract up to 12 requirements from the JD, each tagged `critical`, `high` or `preferred`, each with a verbatim quote from the JD, and map each one to a factsheet line (or "missing"). After tailoring, flag `critical` terms the resume does not mention.

**How to adapt:** add a `requirements` block to the top of `answers.txt` (or a `requirements.md` in the tailored folder) produced by the research-and-tailor subagent. Then a `coverage` check next to `fact-check.py`: for each critical requirement that maps to a factsheet line, confirm a matching term appears in the resume. **Fact-check stops lies. Coverage stops omissions.** Run both in `preflight.sh`.

## 4. Form discipline

**What:** three small habits that prevent most application mistakes.

**How to adapt:**
- **Scan for knockout questions before tailoring.** Open the form first and list every required question in `jd.txt`. If an honest answer knocks you out, stop before spending time on the resume. (Already in `AGENTS.md` W2.)
- **Re-read the form right before the human clicks Submit.** The agent reads back every required field and confirms it holds its value. React forms and autocompletes can silently drop values. (In `docs/04`.)
- **Save the verbatim JD with its posted date.** Postings disappear, and you will need the text when a recruiter calls. (`jd.txt`.)

## 5. Seeded follow-ups

**What:** every application and outreach row carries its next follow-up date from the moment it is logged, so follow-ups never depend on memory.

**How to adapt:** the tracker templates already have `next_followup`, `followups` and `outcome` columns. Seed the date when the row is written:
- **+7 days** after an application with no response (cold emails use +5 days, see `docs/05`).
- **+3 days** after a reply that went quiet.
- **+1 day** after an interview, for the thank-you note.

Each follow-up adds something new. Never "just checking in". After 2 follow-ups with no reply, set `outcome` to `cold` and stop. At session start the agent lists every row with `next_followup` on or before today.

## 6. Adversarial hiring-manager review for top roles

**What:** for the few roles that matter most, a separate reviewer agent plays the screener and judges the tailored resume before it is sent.

**How to adapt:** a subagent prompt that receives only `jd.txt`, the tailored resume and `profile/factsheet.md`, and must answer as the hiring manager: `advance` or `hold`, plus exactly 3 concrete fixes. It may only suggest facts that exist in the factsheet. The main agent applies fixes that pass `fact-check.py`. Use it for Tier 1 roles only, it costs a full extra pass.

## 7. STAR+R story bank

**What:** 6 to 8 stories in Situation, Task, Action, Result, Reflection form, each tagged with the questions it answers (hardest bug, conflict, ownership, failure, ambiguity, tight deadline).

**How to adapt:** the factsheet template already has a Story bank section. Fact-check the stories like any other answer. The answer bank and the tailoring subagent pull from them for "tell us about a time" fields, and the same stories drive interview prep.

## 8. Channel yield

**What:** measure which channels and which score bands actually produce replies, then spend time accordingly.

**How to adapt:** after about 20 logged outcomes, a small script reads `tracker/applications.csv` and `tracker/outreach-log.csv` and reports reply rate per channel (ATS form, cold email, LinkedIn DM, referral, post-lead) and per `rank.py` score band. **Show no percentage for any group with fewer than 5 outcomes**, print the raw counts instead. Small samples lie.

## Avoid

These came up in other projects or in our own experiments. Do not add them.

- **Auto-submit, captcha solving, and hiding automation signals.** The human submits and solves captchas. No stealth plugins, no spoofed fingerprints.
- **Scraping behind a login.** Use official exports (LinkedIn data export, ATS public APIs) and the user's own browser at human pace. No logged-in scraping of LinkedIn, Naukri or similar.
- **Mass-applying to many roles at one company.** It looks like spam to the recruiter, and Ashby enforces per-company limits. Pick the single best-matching role.
- **Open-ended research.** Cap research at about 5 searches per JD. If it is still unclear, ask the human.
