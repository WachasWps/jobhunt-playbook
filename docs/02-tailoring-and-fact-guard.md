# 02. Per-JD tailoring with a fact guard

One tailored 1-page resume per role, built only from verified facts. The fact guard makes it safe to let an agent do the tailoring.

## The single source of truth

`profile/factsheet.md` holds everything true about you: timeline, titles, dates, a bullet bank tagged by role family, defensible numbers with their source, projects, education, skills, a story bank, and open `[confirm]` items. Template: `profile/factsheet.template.md`. Filled example: `examples/aarav-mehta/factsheet.md`.

Rules for the factsheet:
- Only your own work. Teammate work is out.
- A number goes in only with its source (commit count from `git log`, a dashboard, a release note).
- Unsure items are `[confirm: ...]`. The fact guard ignores those lines as evidence.
- Skills you have NOT used go on a line containing "not used in production". The fact guard ignores that line too, so it cannot back a claim, but agents still know to answer honestly.
- Confidential details never go in (customers, partners, ticket IDs, revenue).

## The per-role folder

```
tailored/2026-10/acme-ai-engineer/
  First_Last_Resume.md     tailored resume source
  First_Last_Resume.pdf    rendered, 1 page
  jd.txt                   verbatim JD + URL + posted date + saved date + form questions
  answers.txt              fit decision, then every form question in order with its answer
```

Keep `jd.txt` and `answers.txt` next to the resume. Postings disappear, and when a recruiter calls three weeks later you need to know exactly what you applied to and what you said.

## Step by step

1. **Save the JD.** Copy the full text into `jd.txt` with the URL, posted date, today's date, and the list of form questions (especially knockouts). The public ATS APIs return the full description: `boards-api.greenhouse.io`, `api.lever.co/v0/postings`, `api.ashbyhq.com/posting-api`.
2. **Fit check.** Hard years minimum, seniority, location, visa, core stack. Skip if any knockout fails honestly. Check the company's other openings for a better match.
3. **Extract requirements.** List the JD's must-haves and nice-to-haves in its own words. For each, find the factsheet line that backs it, or mark it missing.
4. **Pick the base.** The closest variant in `resume/base/`.
5. **Rewrite, do not invent:**
   - Headline: the JD's title if it honestly describes you, plus 2 to 3 focus areas from the JD.
   - Summary: 2 to 3 sentences using the JD's words for things you have done.
   - Skills: reorder so the JD's must-haves come first, using the JD's spelling.
   - Bullets: pick and reorder from the bullet bank. Reword toward the JD. Never add a fact.
   - Drop anything irrelevant to make room. Stay at 1 page.
6. **Draft answers.** Every form question, in order, in `answers.txt`. Start from `profile/answers-bank.md` and tilt to the JD. For "describe a time" questions, use the story bank.
7. **Run preflight:**
   ```bash
   bash resume/templates/preflight.sh tailored/2026-10/acme-ai-engineer
   ```
8. **Fix and rerun** until it prints `PREFLIGHT PASSED`.
9. **Coverage check (manual for now).** Re-read the must-have list from step 3. Any must-have you have and the resume does not mention is an omission. Add it. The fact guard stops lies, this step stops omissions.

## What the fact guard does

`resume/templates/fact-check.py` reads the resume or answers file line by line and flags:
- `CHECK [number]`: a number that does not appear in your factsheet or profile. "40%" with no source, "1.4 years" when the factsheet says "1 year 4 months" (write the decimal in the factsheet once so every form uses the same one).
- `CHECK [term]`: a capitalized name or tech term that is not in your sources ("Kubernetes" when you never used it).
- `CHECK [banned-char]`: an em-dash, en-dash or middle dot.
- `JD-ONLY`: a term that appears only in the JD. Fine for the company name or a negation ("LangChain: not used in production"). A red flag if the line claims the skill. `--strict` makes these fail too.

Usage:
```bash
python3 resume/templates/fact-check.py FILE [--jd jd.txt] [--sources a.md,dir/] \
    [--factsheet profile/factsheet.md] [--profile profile/profile.json] [--strict]
```

A flag is not always a lie. It means "no source mentions this". If the fact is true, add it to the factsheet with its source, then rerun. If it is not, delete it.

Limits: the guard checks terms and numbers, not meaning. "Led a team of 5" passes if "5" and "team" appear anywhere in the factsheet. Read the result like a recruiter would.

## Render

```bash
bash resume/templates/render-pdf.sh tailored/2026-10/acme-ai-engineer/First_Last_Resume.md
python3 resume/templates/build-docx.py in.md out.docx      # if a portal wants Word (needs python-docx)
pdfinfo tailored/2026-10/acme-ai-engineer/First_Last_Resume.pdf | grep Pages
```

The Markdown shape the renderer expects (see the example resume):
```
# Full Name
**Headline Title | Focus, Focus, Focus**
+91 90000 00000 | you@example.com | linkedin.com/in/you | github.com/you | City, Country

## Summary
Two or three sentences.

## Skills
- **Group:** item, item, item

## Experience

### Title | Company
*Mon YYYY - Present | Mode, City*
- Bullet
```

If it spills to 2 pages: cut the oldest role to 1 bullet, shorten the summary, merge skill groups, drop a project. Do not shrink the font below the CSS defaults.

## Reuse

When two roles are in the same family (two backend roles, two AI roles), reuse the previous tailored resume as the starting point and only retune the headline, summary and skills order. Build a new tilt only when the role family changes.
