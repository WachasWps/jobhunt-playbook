# MASTER FACTSHEET: <Your Name>

> Copy this file to `profile/factsheet.md` (gitignored) and fill it in. It is the single source of truth for every resume, form answer, cold email and interview story. `resume/templates/fact-check.py` flags any number or named term in a resume or answer that does not appear here, in `profile/profile.json`, or in the job description.
>
> A filled example for a fictional person lives in `examples/aarav-mehta/factsheet.md`.

## Honesty rules (keep these at the top)
1. Only your own work counts. If a teammate built it, leave it out or say "worked with".
2. No invented metrics. A number goes in only if you can show where it came from (commit count, dashboard, a release note, your own logs).
3. Mark anything you are unsure of as `[confirm: ...]`. Agents must not use a `[confirm]` item until you resolve it.
4. Confidential details stay out: customer names, partner names, internal ticket IDs, unreleased features, revenue. Describe the work generically.
5. Every fact here should survive an interviewer asking "tell me more about that".

---

## CONTACT BLOCK
- **Name:** <Full name as on your ID and degree>
- **Phone:** <+CC number>
- **Email:** <personal email, never your work email>
- **LinkedIn:** <linkedin.com/in/handle>
- **GitHub:** <github.com/handle>
- **Location:** <City, Country>
- **Portfolio:** <url or leave empty>

---

## VERIFIED TIMELINE (newest first)
| Role (official title) | Company as shown on resume | Legal entity (for forms) | Dates | Mode | Proof |
|---|---|---|---|---|---|
| <Software Engineer> | <Company> | <Company Pvt Ltd> | <Mon YYYY - Present> | <Remote/Hybrid/On-site> | <offer letter, payslips, commits> |
| <Intern> | <Company> | <...> | <Mon YYYY - Mon YYYY> | <...> | <...> |

**Naming rules:** <e.g. "Show the product name on the resume, use the legal entity on forms that ask for employer name, since background checks verify against it.">

**Title rule:** your official title and dates are what background checks verify. You may use a standard searched title as a headline (for example "Backend Engineer") only if it honestly describes the work.

**Defensible numbers (the only numbers agents may use):**
- <e.g. 340 commits to the main repo, from git log --author>
- <e.g. p95 latency from 900 ms to 300 ms, from the dashboard screenshot dated Mon YYYY>
- <e.g. 3 services migrated>

---

## EXPERIENCE: bullet bank
Tag each bullet so agents can pick by role family. Suggested tags: `[AI]` AI/ML, `[BE]` backend, `[FE]` frontend, `[FS]` full-stack, `[DATA]` data, `[INFRA]` cloud/devops, `[ALL]` fits anything. Write more bullets than any one resume needs. Agents select and reword, they never add.

### 1. <Title> | <Company> | <Mon YYYY - Present> | <Mode>
*<One line on what the company or product does, from a public source.>*
*Confidentiality: <what must never appear, e.g. customer names, partner names, ticket IDs>.*

- `[BE]` <What you built, the technical choice, and the result. Concrete nouns, real tech names.>
- `[AI][BE]` <...>
- `[FS]` <...>
- **Stack:** <languages, frameworks, cloud services you actually used here>

### 2. <Title> | <Company> | <Mon YYYY - Mon YYYY> | <Mode>
- `[..]` <...>

---

## PROJECTS
- **<Project name> (<award or context, if any>):** <what it does, the tech, a link if public>.

## EDUCATION
- **<Degree, Major>**, <Institute>, <City> | <Mon YYYY - Mon YYYY> | <grade, if you want it shown>

## ACHIEVEMENTS
- <Hackathon wins, ranks, scholarships, publications. Name and year.>

---

## SKILLS INVENTORY (master list, reorder and trim per role)
- **Languages:** <...>
- **Backend:** <...>
- **Frontend:** <...>
- **AI / ML:** <...>
- **Data:** <...>
- **Cloud / Infra:** <...>
- **Tools / practices:** <...>

Only list a skill if you could answer two follow-up questions about it in an interview.

---

## STORY BANK (STAR + Result, for "tell us about a time" fields and interviews)
Write 6 to 8. Each one tagged with the questions it answers. Facts must match the bullets above.

### <Story title>
- **Answers:** <hardest bug | conflict | ownership | failure | tight deadline | ambiguity>
- **Situation:** <...>
- **Task:** <...>
- **Action:** <...>
- **Result:** <...>
- **Reflection:** <what you would do differently>

---

## STANDARD FACTS FOR FORMS
- **Years of experience (honest count):** <e.g. 1 year 4 months of full-time work since Mon YYYY, plus a 6-month internship>
- **Years of experience (decimal, for numeric fields):** <e.g. 1.4>. Write the exact number here once so every form uses the same one.
- **Notice period:** <...>
- **Work authorization:** <...>
- Compensation facts live in `profile/profile.json` > `compensation` and follow `docs/07-comp-and-discretion.md`.

---

## OPEN ITEMS (`[confirm]`)
1. <A number or fact only you can supply. Agents ask you, they do not guess.>
