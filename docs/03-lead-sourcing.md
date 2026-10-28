# 03. Lead sourcing

Where fresh, real roles come from, ranked by what actually produced applications and replies. The rule behind all of it: **fresh and specific beats big and stale**. Lists sort by date, so a role posted 2 days ago is worth ten posted 3 weeks ago.

## Sources at a glance

| Source | How | Cost | Signal | Notes |
|---|---|---|---|---|
| Greenhouse, Lever, Ashby boards | `discover.py` (public JSON APIs) | free | high | full JD text, posted date, direct apply link |
| LinkedIn hiring posts | `linkedin_posts.py` (Apify actor) | about $0.05 a run | high when the post has a corporate email | no LinkedIn login, no ban risk |
| Reddit r/developersIndia "Who's hiring" monthly thread | real browser, read only | free | high | founders post directly, often with an email |
| YC jobs | `discover.py` (`yc_jobs`) | free | high | startup quality, apply on workatastartup.com |
| HN "Who is hiring" | `discover.py` (`hn_whoishiring`) | free | medium | mostly US, filter hard for your geography |
| RemoteOK, Remotive | `discover.py` | free | low to medium | many region-locked "remote" roles |
| Telegram job channels | `telegram_posts.py` (your own Telethon session) | free | medium | fresher roles, many Google Form links |
| Company careers pages | browser or the ATS API behind them | free | high | the page usually embeds a Greenhouse, Lever or Ashby board |
| X / Twitter search | skip | | low | mostly aggregator noise. The CLI tools we tried were broken. |
| Threads | `threads_posts.py` (optional, browser) | free | low | login-walled, little volume |

## 1. Public ATS JSON APIs (the backbone)

These are documented, public, no auth:

```
Greenhouse  https://boards-api.greenhouse.io/v1/boards/<slug>/jobs?content=true
Lever       https://api.lever.co/v0/postings/<slug>?mode=json
Ashby       https://api.ashbyhq.com/posting-api/job-board/<slug>?includeCompensation=true
```

Find a company's slug from its careers link: `boards.greenhouse.io/<slug>`, `jobs.lever.co/<slug>`, `jobs.ashbyhq.com/<slug>`. Add slugs to `jobhunt/config.json` > `companies`. A wrong slug returns 0 jobs, nothing breaks.

Run:
```bash
python3 jobhunt/sources/discover.py      # writes jobhunt/data/jobs_raw.json
python3 jobhunt/rank.py                  # writes ranked CSVs, tracker.csv, dashboard.html
open jobhunt/data/dashboard.html
```

The same APIs give you the full JD text for `jd.txt`, so the agent never has to scrape the page.

## 2. How ranking works (`rank.py`)

- **Title gate.** Only real software/ML titles pass. Word-boundary matching, so "claims" does not count as "ai" and "html" does not count as "ml". Non-dev "engineer" titles (sales engineer, support engineer) are dropped.
- **Role bucket.** founding, ai, fullstack, backend or swe, weighted by `config.scoring.role_weights`.
- **Geography.** Home country, India-friendly remote, foreign on-site only with a sponsorship signal. Region-locked remote ("US only") and unsponsored foreign on-site are marked ineligible. Edit `geo_rules` for your country.
- **Seniority.** senior, staff, lead, "5+ years" in the title push a role down. A "3+ years" in the description is a smaller penalty, but treat it as a likely knockout during fit check.
- **Freshness.** Posted in the last 2 days gets a boost, older than 60 days a penalty.
- **Home city.** Roles in `profile.identity.location_city` get a boost.
- **Tiers.** T1 (top, capped, at most 3 per company) gets full tailoring plus outreach. T2 is a faster pass. The rest is skipped.
- **Resume pick.** From `profile.resume_variant_map` by role and geography.
- `data/tracker.csv` is merge-aware: rerunning keeps any status or notes you set by hand.

`rank.py` only writes files when run as a script. Importing it (tests, agents) is safe.

## 3. LinkedIn hiring posts via Apify

Hiring posts carry intent and a human contact. Many say "send your CV to name@company.com".

- **Actor:** `harvestapi/linkedin-post-search`. Cookieless keyword post search: no LinkedIn account, nothing touches your profile, zero ban risk. About $1.50 per 1000 posts, so a typical 8-query run is about $0.05.
- **Free plan:** about $5 a month of credit. One full run a week is comfortable. If you see a 402 or 403, the monthly credit is gone.
- **Do not** automate your own LinkedIn account and do not create a burner. New accounts now demand selfie or ID verification, and automation gets accounts restricted.
- **Queries** live in `config.json` > `post_harvest.query_templates`. Write them like the LinkedIn search bar: role + location + seniority + "hiring". Fewer, sharper queries beat many vague ones.

```bash
export APIFY_TOKEN=<your token>          # or save it in jobhunt/.apify_token (gitignored)
python3 jobhunt/sources/linkedin_posts.py --dry-run
python3 jobhunt/sources/linkedin_posts.py
python3 jobhunt/rank.py
python3 jobhunt/draft_posts.py           # first-draft emails and DM notes in outreach/
```

**Noise filters** (`posts_common.py`), hard won, keep them:
- A **corporate email in the post** is the strongest real-lead signal.
- Aggregator and staffing accounts are dropped by name.
- Posts with no email or a free-mail address face a listicle filter ("mass hiring", "500+ jobs", multiple `lnkd.in` links, emoji numbering). These are influencers reposting other companies' openings.
- Add recurring noise accounts to `jobhunt/data/posts_skiplist.json` (a JSON list of lowercase substrings).
- Dedupe: by post URL and content hash, and against every company already in your trackers.

Curate by hand after the script: skip staffing firms that slipped through, senior-only roles, and anything outside your geography.

## 4. Reddit r/developersIndia "Who's hiring" megathread

A monthly pinned thread where founders and hiring managers post roles directly, often with an email or a form. High signal, low competition.

- **Read it in the real browser** (the user's Chrome via the browser MCP). Reddit blocks `curl` and the `.json` endpoints for scripts.
- Sort comments by new. Pull company, role, location, years, contact and link into a list.
- Read only. Never post or DM from automation.

Other subreddits and monthly threads work the same way. Check the rules of each.

## 5. YC jobs

`ycombinator.com/jobs/role/<role>[/<location>]` pages are server-rendered. The listings are embedded as JSON in a `data-page` attribute, so `discover.py` reads them without a browser. Fields include company, batch, title, location, salary range, minimum experience and visa policy.

- Apply links go through a login on workatastartup.com. The user applies there.
- Listings have no email. For outreach, find the founder's verified email separately (`docs/05`).

Edit `config.json` > `yc_jobs.paths` for the roles and locations you want.

## 6. Hacker News "Who is hiring"

The monthly thread by `whoishiring`, via the Algolia API. `discover.py` pulls top-level comments. Mostly US roles: rely on the geo filter, and check "REMOTE (worldwide)" claims on the live posting.

## 7. Telegram job channels (optional)

Some channels post structured fresher and SDE roles (`Company - X`, `Role - Y`, `Apply Link: ...`). `telegram_posts.py` reads them through your own Telethon session, because a bot cannot read a channel it does not admin. One-time interactive login in your own terminal. See the file header. Apply-link posts become a shortlist in `outreach/`. Many links are Google Forms (see `docs/04` for the click caveat). Ignore paid-referral and self-promo links (`ignore_apply_url_substrings`).

## 8. Company careers pages and GCCs

For a target company, open its careers page and find the ATS behind it. Add the slug to `config.json` so `discover.py` checks it every run. In India, Global Capability Centres (engineering centres of global companies) are a growing channel: many have Greenhouse or Workday boards.

## 9. Research with Exa

For company research, founder background and "is this company real", use Exa web search (`docs/09`). Cap research at about 5 searches per JD so it never turns into open-ended browsing.

## Daily sourcing loop

1. `discover.py` then `rank.py` (daily or every 2 to 3 days).
2. LinkedIn post harvest (weekly, or when credit allows).
3. Reddit monthly thread (when a new one is up, then every few days for new comments).
4. Filter: posted in the last 3 days, title match, eligible geography, not already in `tracker/applications.csv`.
5. Hand the shortlist to fit check (`AGENTS.md` W2). A subagent with `prompts/sourcer.md` can do steps 3 and 4 in parallel.
