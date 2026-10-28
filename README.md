# jobhunt-playbook

A job-hunt system you run with a coding agent (Claude Code or Codex). The agent finds fresh roles, checks fit, tailors a 1-page resume per job with a fact guard, drafts form answers, fills applications in your real browser, and drafts verified cold emails. You review everything, solve captchas, and click Submit and Send.

Built by Wachas Pati ([github.com/WachasWps](https://github.com/WachasWps)) during his own 2026 job hunt, then cleaned up so a friend's agent could run it for the friend's profile. Every method here was used on real applications. Nothing in this repo belongs to a real candidate: the example person, Aarav Mehta, is fictional.

## What is inside

| Path | What it is |
|---|---|
| `AGENTS.md` | Operating manual for the coding agent. Start here if you are the agent. |
| `CLAUDE.md` | Points Claude Code at `AGENTS.md`, plus the key rules. |
| `docs/` | One file per method (ATS rules, tailoring, sourcing, browser applying, cold outreach, subagents, comp, writing, tools, roadmap). |
| `profile/` | Templates for your factsheet, profile.json and answers bank. Your filled copies are gitignored. |
| `examples/aarav-mehta/` | A fully filled fictional example: factsheet, profile, one tailored application folder, one cold email. |
| `resume/templates/` | Markdown to HTML to PDF/DOCX renderer, CSS, `fact-check.py`, `preflight.sh`. |
| `jobhunt/` | Lead discovery (public ATS APIs, HN, YC, LinkedIn posts via Apify, Telegram), ranking, first-draft outreach. |
| `prompts/` | Subagent prompt templates: research and tailor, sourcer, cold-outreach drafter, repo-idea reviewer. |
| `tracker/` | CSV headers for the applications log and outreach log. Copy them to `applications.csv` and `outreach-log.csv` (gitignored). |
| `config/` | `mcporter.example.json` for Exa web search through mcporter. |

## Quickstart (about 30 minutes, once)

1. **Make your copy private.** Use this repo as a template and set your copy to private. Personal files are gitignored as a second guard.
2. **Fill your facts.**
   ```bash
   cp profile/factsheet.template.md profile/factsheet.md
   cp profile/profile.template.json profile/profile.json
   cp profile/answers-bank.template.md profile/answers-bank.md
   cp jobhunt/config.example.json jobhunt/config.json
   cp tracker/applications.template.csv tracker/applications.csv
   cp tracker/outreach-log.template.csv tracker/outreach-log.csv
   ```
   Fill `factsheet.md` first. It is the single source of truth: every resume line and form answer must trace back to it. Your agent can interview you to fill it, then you correct it. See `examples/aarav-mehta/factsheet.md`.
3. **Write one base resume** in `resume/base/` (copy the shape of `examples/aarav-mehta/tailored/2026-10/acme-ai-engineer/Aarav_Mehta_Resume.md`) and render it:
   ```bash
   bash resume/templates/render-pdf.sh resume/base/First_Last_Resume.md
   ```
4. **Check the tools** in `docs/09-tools-setup.md`: Python 3.9+, Node 18+, Chrome, `pdfinfo` (poppler), optionally `python-docx`, a browser MCP for your real Chrome, an Apify token, Exa search.
5. **Test the fact guard** on the example:
   ```bash
   FACTSHEET=examples/aarav-mehta/factsheet.md PROFILE=examples/aarav-mehta/profile.json \
     bash resume/templates/preflight.sh examples/aarav-mehta/tailored/2026-10/acme-ai-engineer
   ```
6. **Edit `jobhunt/config.json`**: your target companies' ATS slugs, role keywords, geography, LinkedIn search queries.
7. Open the repo in Claude Code or Codex and say: **"Read AGENTS.md, then run today's job-hunt loop."**

## The daily loop

1. **Follow-ups and replies first.** Anything due today in `tracker/` gets a short in-thread follow-up. Replies get a tone-matched answer.
2. **Fresh leads.** `python3 jobhunt/sources/discover.py && python3 jobhunt/rank.py`, plus the LinkedIn post harvest and any manual sources (Reddit hiring threads, YC, HN). Prefer roles posted in the last few days.
3. **Fit check.** Subagents read each JD and drop roles with a hard years minimum you do not meet, senior titles, or location and visa knockouts. They suggest a better-matching role at the same company when there is one.
4. **Tailor.** One folder per role: tailored 1-page resume, `jd.txt`, `answers.txt`. Run `preflight.sh` on every folder.
5. **Apply in your real browser.** The agent prefills several tabs. You solve captchas, check each form, and click Submit.
6. **Cold outreach.** 15 to 20 verified emails a day at most, each paired with a LinkedIn DM. You click Send.
7. **Log everything** in `tracker/applications.csv` and `tracker/outreach-log.csv` with the next follow-up date.

## Principles

- **No fabrication.** The fact guard flags any number or term your factsheet does not back.
- **The human submits.** The agent never auto-submits an application, never sends an email, never solves a captcha.
- **Quality over spray.** Apply early to roles that fit. Tailor each one. Verify each email.
- **Discretion if employed.** No public Open-to-Work banner, no internals of your current employer, block your employer on job portals.
- **Human writing.** No em-dashes, en-dashes or middle dots. Short and specific.

## Docs

1. [ATS and resume rules](docs/01-ats-and-resume-rules.md)
2. [Tailoring and the fact guard](docs/02-tailoring-and-fact-guard.md)
3. [Lead sourcing](docs/03-lead-sourcing.md)
4. [Applying in your real browser](docs/04-applying-in-real-browser.md)
5. [Cold outreach and email verification](docs/05-cold-outreach-and-email-verification.md)
6. [Subagent fan-out](docs/06-subagent-fanout.md)
7. [Compensation and discretion](docs/07-comp-and-discretion.md)
8. [Writing style](docs/08-writing-style.md)
9. [Tools setup](docs/09-tools-setup.md)
10. [Ideas borrowed from other open-source job-hunt repos](docs/10-roadmap-ideas.md)

## Credits

Some ideas are adapted (approach only, no code copied) from [career-ops](https://github.com/career-ops-hq/career-ops) by career-ops-hq (MIT) and [dossier](https://github.com/AienTech/dossier) by AienTech (AGPL). See `docs/10-roadmap-ideas.md`.

## License

MIT. Copyright (c) 2026 Wachas Pati.
