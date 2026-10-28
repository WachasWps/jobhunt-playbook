# 01. ATS reality and resume rules

How applications actually get filtered, and the resume format that survives it. Research and practice from 2026 job hunting, mostly in India and global-remote software roles.

## How shortlisting really works

1. **Knockout questions are the main automatic cut.** Forms ask about work authorization, sponsorship, minimum years, location, on-site days, notice period. A "no" on a must-have, or a number below the minimum, is often an automatic reject. Read every one and answer it truthfully. If the truth disqualifies you, skip the role and spend the time elsewhere.
2. **The "75% of resumes are auto-rejected by ATS" figure is a myth.** Most ATS do not score and silently bin resumes. A human (recruiter or hiring manager) looks at the pool, filtered by knockouts and searches.
3. **Recruiters keyword-search the pool.** Mostly on job titles first, then must-have skills. A resume whose headline and most recent title match the searched title gets found far more often (one large study of 2.5M applications put title match at about 10x the interview rate). Use the standard title that honestly describes your work ("Backend Engineer", "AI Engineer", "Software Engineer"), not an unusual one.
4. **Candidate lists sort by application date.** The newest applicants are on top. Apply in the first days of a posting. A great application on day 20 may never be opened.
5. **AI match tiers.** Greenhouse, Lever and Workday now show recruiters an AI "match" rating against the JD. Tilting the resume to the JD's own words (where true) moves you up that list.
6. **Mass-applying does not work.** Recruiters see AI-spammed applications and filter against them. A tailored application on the company's own careers page, plus a short note to the hiring manager, beats 50 Easy Apply clicks.

## What this means in practice

- Apply early: prioritize roles posted in the last 3 days.
- Answer knockouts first: scan the form before you tailor anything.
- Mirror the JD title in the resume headline, if it honestly fits.
- Mirror the JD's must-have skills in the summary and skills section, in the JD's spelling ("PostgreSQL" vs "Postgres"), only if the factsheet backs them.
- Prefer roles whose years range includes your real number. If a JD says "3+ years required" and you have 1.5, skip it, unless a human referral is involved.

## Resume format rules

- **Strict 1 page** for anyone under about 8 years of experience. Indian and global recruiters both expect it. The first scan is about 7 seconds, mostly on titles, companies and dates.
- **Single column.** No tables, no text boxes, no columns, no icons, no photos, no skill bars. Contact info in the body, not a document header.
- **Standard section names:** Summary, Skills, Experience, Projects, Education (and Achievements if you have them). Parsers and recruiters look for these words.
- **Dates as `Mon YYYY - Mon YYYY`.** Roles strictly newest first.
- **No em-dashes, en-dashes or middle dots.** Use `|`, commas or hyphens. They read as AI-written, and some parsers mangle them.
- **A one-line headline under your name** with the target title and 2 to 3 focus areas, for example `Backend Engineer | Python, PostgreSQL, Event-Driven Systems`.
- **Bullets per role (early career):** current role 3 to 4, previous role 3, older roles 2, oldest 1. Each bullet 1 to 2 lines (about 20 to 30 words): what you built, how, and the result.
- **Skills live in the Skills section and inside bullets.** No "Stack:" line under every role.
- **Real numbers only.** A number goes in only if the factsheet says where it came from.
- **File format:** PDF with selectable text for email and most portals. DOCX when a portal says it parses Word better (`python3 resume/templates/build-docx.py in.md out.docx`).
- **File name:** `First_Last_Resume.pdf`. Never `resume_final_v3.pdf`.
- **Personal data:** name, phone, email, LinkedIn, GitHub, city. No date of birth, photo, marital status or full address.

## Variants

Keep a few base variants in `resume/base/` (for example backend, AI, full-stack, new-grad) and tailor a copy per application (`docs/02`). Base variants should already pass `fact-check.py`.

Use the honest standard title for board and ATS applications. Keep unusual titles like "Founding Engineer" for warm founder conversations where they help.

## New grads and early career

If you graduated recently but have real production work, frame yourself as "a recent grad who has already shipped" with the concrete thing you shipped. Calling yourself "1.5 years experienced" can put you in a pool against people with 3 to 5 years, while pure fresher framing undersells you. Apply to new-grad, SDE-1, 0 to 2 year and early-stage roles, and lead with the shipped work.

## Market notes (India, 2026)

- Office mandates are back: most active India roles are on-site or hybrid, fully remote roles fell sharply. Do not filter to remote-only. Include on-site roles in your city and the main hubs.
- Global Capability Centres (India engineering centres of global companies) are hiring while IT services shrink, and most of their new roles want AI or data skills.
- "AI engineer who calls an LLM API" is crowded. The premium is on production reliability: evaluation, guardrails, tool-call validation, observability, cost and latency work. Lead with that if you have it.

## Checklist before any resume leaves your machine

- [ ] 1 page (`pdfinfo file.pdf | grep Pages` says 1)
- [ ] `fact-check.py` passes
- [ ] No banned characters
- [ ] Headline matches the JD title (honestly)
- [ ] Top 3 must-have skills from the JD appear, if true
- [ ] File named `First_Last_Resume.pdf`

`bash resume/templates/preflight.sh <folder>` does the first three in one command.
