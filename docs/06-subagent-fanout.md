# 06. Subagent fan-out

Most of the work per application is reading and writing: research the JD, check fit, tailor, draft answers, find and verify an email, draft the note. That work is independent per role, so it runs in parallel subagents. Only the main agent touches the browser.

## Roles

| Agent | Browser | Does | Prompt |
|---|---|---|---|
| **Main agent** | yes, the user's Chrome | talks to the user, assigns work, reviews subagent output, runs `preflight.sh`, fills forms, logs | `AGENTS.md` |
| **Research and tailor** (one per role) | no | fetch the JD via the public ATS API, fit check, better-role suggestion, tailored resume, `answers.txt`, run fact-check | `prompts/research-and-tailor.md` |
| **Sourcer** | no | pull fresh roles from APIs and public pages, filter by title, geography, freshness, de-duplicate against the tracker | `prompts/sourcer.md` |
| **Cold-outreach drafter** | no | find and verify the right person's email, draft the email, DM and follow-up | `prompts/cold-outreach-drafter.md` |
| **Repo-idea reviewer** (occasional) | no | read another open-source job-hunt repo, extract ideas worth borrowing, check its license | `prompts/repo-idea-reviewer.md` |

Why subagents get no browser: one browser, one driver. Two agents in the same Chrome steal focus from each other, navigate each other's tabs, and Chrome only delivers real clicks to the visible tab. Subagents use public JSON APIs, `curl`, `dig` and web search instead.

## The pipeline

```
 main agent                         subagents (parallel, no browser)
 ----------                         --------------------------------
 shortlist roles (W1)  --------->   research+tailor x N  (one per role)
                                    cold-outreach drafter x M
 review each folder    <---------   tailored/<role>/ resume.md, jd.txt, answers.txt
 run preflight.sh
 prefill tabs 1..5 in Chrome
 hand batch to the user  ------->   (meanwhile: next batch being tailored)
 user solves captchas, submits
 log rows, close tabs
 present email drafts  ------->     user sends
```

While the user is busy with captchas and Submit on one batch, the next batch is being prepared. That is where the speed comes from.

## How to brief a subagent

A subagent knows only what you put in its prompt. Every brief includes:
1. The goal in one sentence and the exact output paths it may write.
2. The paths to read: `profile/factsheet.md`, `profile/profile.json`, `profile/answers-bank.md`, the relevant doc.
3. The hard rules, pasted, not referenced: no fabrication, run fact-check, no banned characters, no browser, no sending, no secrets, honest knockouts.
4. The inputs: role URL, company, ATS, or the list of sources.
5. The return format: a short summary (what was done, decisions, anything the human must answer). Not the file contents.

Fill the templates in `prompts/` and paste them as the subagent prompt.

## Rules for the fan-out

- **3 to 5 subagents at a time.** More than that trips usage limits and makes review the bottleneck. Six parallel scouts once exhausted the session limit.
- **One role per tailoring subagent.** Easier to review, and a failure does not take down the batch.
- **Subagents never write to `tracker/`.** The main agent logs after the human submits.
- **The main agent reviews everything.** Read each resume like a recruiter, check the fit decision, and run `preflight.sh` yourself. A subagent's "fact-check passed" is not enough.
- **Disagreements go to the human.** If a subagent says skip and you think apply, show the user both reasons.
- **Cap research.** About 5 searches per JD. If the role is still unclear after that, mark it for the human.

## Fit-check rules for subagents

- Skip a hard years minimum above the user's real count ("3+ years required" with 1.5 real years). "Preferred" or a range that includes the user's count is fine.
- Skip senior, staff, lead, principal and manager titles unless the user says otherwise.
- Skip location, on-site and visa rules the user cannot meet honestly.
- Skip when the core stack is something the factsheet never mentions.
- When skipping, check the same company's other open roles (same ATS endpoint) and suggest the best match, for example an SDE-1 next to an SDE-2, or a backend role next to a frontend one.
- Record the decision and the one-line reason at the top of `answers.txt`.
