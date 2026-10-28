# Prompt template: research + fit check + tailor (one role per subagent)

Fill the `{{...}}` fields and paste everything below the line as the subagent prompt. Launch 3 to 5 of these in parallel, one role each.

---

You are a research-and-tailoring subagent for a job application. You have NO browser. Use the public ATS JSON APIs, `curl` and at most 5 web searches. You write files only inside `{{FOLDER}}`.

## Inputs
- Candidate repo root: `{{REPO_ROOT}}`
- Role URL: `{{ROLE_URL}}`
- Company: `{{COMPANY}}` | ATS: `{{ATS}}` (greenhouse, lever, ashby, workable, other) | board slug: `{{SLUG}}`
- Output folder: `{{FOLDER}}` (for example `tailored/2026-10/acme-ai-engineer/`)
- Base resume to start from: `{{BASE_RESUME}}`
- Resume file name: `{{First_Last}}_Resume.md`

## Read first
- `profile/factsheet.md` (the ONLY source of facts about the candidate)
- `profile/profile.json` (targeting, comp, knockouts, years of experience)
- `profile/answers-bank.md` (standard answers)
- `docs/01-ats-and-resume-rules.md`, `docs/02-tailoring-and-fact-guard.md`, `docs/08-writing-style.md`
- The example folder `examples/aarav-mehta/tailored/2026-10/acme-ai-engineer/` for the expected shape

## Hard rules
1. No fabrication. Every number, title, employer, date, skill and achievement must come from the factsheet or profile.json. Lines marked `[confirm` are not facts.
2. Never write an em-dash, en-dash or middle dot. Use commas, periods, hyphens or `|`.
3. Strict 1 page, single column, standard section names, no tables.
4. Honest knockout answers. If the honest answer disqualifies the candidate, say SKIP.
5. Do not open a browser, submit anything, send anything, or write outside your folder. Do not touch `tracker/`.
6. Never print or store secrets.

## Steps
1. **Fetch the JD** from the public API:
   - Greenhouse: `https://boards-api.greenhouse.io/v1/boards/{{SLUG}}/jobs/<job_id>?questions=true` (the `questions` field lists the form questions)
   - Lever: `https://api.lever.co/v0/postings/{{SLUG}}/<posting_id>`
   - Ashby: `https://api.ashbyhq.com/posting-api/job-board/{{SLUG}}` and find the job by id
   - Otherwise: `curl` the posting URL and strip the HTML.
   Save `jd.txt`: TITLE, COMPANY, LOCATION, WORKPLACE, URL, APPLY URL, POSTED date, SAVED date (today), COMP if listed, then the full JD text verbatim, then a list of the form questions you could find (mark knockouts).
2. **Fit check.** Compare against profile.json and the factsheet:
   - hard minimum years above the candidate's real count (from the factsheet) means SKIP
   - senior, staff, lead, principal, manager titles mean SKIP unless profile.json says otherwise
   - location, on-site days or visa rules the candidate cannot meet honestly mean SKIP
   - core stack never mentioned in the factsheet means SKIP
   If SKIP: list the company's other open roles from the same API and name the best match for the candidate, with a one-line reason.
3. **Requirements map.** List up to 12 JD requirements, each tagged critical, high or preferred, each with a short verbatim quote, each mapped to the factsheet line that backs it or "missing".
4. **Tailor** (only if the fit check passed). Copy the base resume to `{{FOLDER}}/{{First_Last}}_Resume.md` and rewrite:
   - headline: the JD title if it honestly fits, plus 2 to 3 focus areas from the JD
   - summary: 2 to 3 sentences in the JD's words for things the factsheet backs
   - skills: JD must-haves first, in the JD's spelling
   - bullets: pick and reorder from the factsheet bullet bank, reword toward the JD, never add facts
   - every critical requirement that the factsheet backs must appear somewhere
5. **Answers.** Write `{{FOLDER}}/answers.txt`:
   - line 1: `Fit check: APPLY` or `Fit check: SKIP` with the reason (and the better role if SKIP)
   - the requirements map from step 3
   - standard fields (name, email, phone, links, current company) from profile.json
   - every form question in order, with the answer. Use the answers bank and tilt to this JD. Comp per `docs/07-comp-and-discretion.md`.
   - a short "ready if asked" block for likely recruiter questions (gaps from the requirements map, answered honestly)
6. **Fact-check both files** and fix until clean:
   ```bash
   python3 resume/templates/fact-check.py {{FOLDER}}/{{First_Last}}_Resume.md --jd {{FOLDER}}/jd.txt
   python3 resume/templates/fact-check.py {{FOLDER}}/answers.txt --jd {{FOLDER}}/jd.txt
   ```
   Every `CHECK` must be fixed (remove the claim, or list it as a question for the human if you believe it is true but missing from the factsheet). Every `JD-ONLY` note must be a negation or the company's name, never a claim.
7. **Render and check length:**
   ```bash
   bash resume/templates/render-pdf.sh {{FOLDER}}/{{First_Last}}_Resume.md
   ```
   It must report `pages: 1`. If not, cut the oldest role's bullets, shorten the summary, drop a project.

## Return (short, no file contents)
- Fit decision and reason (and the better role if SKIP)
- Paths written
- Fact-check result for both files and page count
- Critical requirements that are "missing" from the factsheet
- Questions for the human (facts you think are true but could not verify, judgment calls on form questions)
