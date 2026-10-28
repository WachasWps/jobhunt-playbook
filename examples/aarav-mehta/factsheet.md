# MASTER FACTSHEET: Aarav Mehta

> FICTIONAL EXAMPLE. Aarav Mehta, his employers, his school and every number below are invented to show how a filled factsheet looks. Do not reuse any of it.

## Honesty rules
1. Only Aarav's own work counts. Teammate work is excluded.
2. No invented metrics. Every number below lists where it came from.
3. `[confirm: ...]` items are not used until Aarav resolves them.
4. Tidewater customers, carrier partners and ticket IDs never appear anywhere.

---

## CONTACT BLOCK
- **Name:** Aarav Mehta
- **Phone:** +91 90000 00000
- **Email:** aarav@example.com
- **LinkedIn:** linkedin.com/in/aarav-mehta-example
- **GitHub:** github.com/aarav-mehta-example
- **Location:** Bengaluru, India
- **Portfolio:** none

---

## VERIFIED TIMELINE (newest first)
| Role (official title) | Company as shown on resume | Legal entity (for forms) | Dates | Mode | Proof |
|---|---|---|---|---|---|
| Software Engineer | Tidewater Systems | Tidewater Systems Pvt Ltd | Jul 2025 - Present | Hybrid, Bengaluru | offer letter, payslips, 410 commits |
| Data Engineering Intern | Kestrel Analytics | Kestrel Analytics LLP | Jan 2025 - Jun 2025 | Remote | internship certificate |

**Naming rules:** company names as above on the resume. Legal entity only on forms that ask for "employer legal name".

**Title rule:** official title is "Software Engineer". "AI Engineer" may be used as a headline because about half of his current work is the RAG assistant below.

**Defensible numbers:**
- 410 commits to the Tidewater main repo (`git log --author`, Oct 2026)
- 1,200 help-center articles indexed by the support assistant
- 80-question eval set for the assistant
- 2 cron jobs moved to AWS Lambda
- 6 carrier integrations on the webhook service
- 3 Airflow pipelines at Kestrel
- CGPA 8.4/10

---

## EXPERIENCE: bullet bank

### 1. Software Engineer | Tidewater Systems | Jul 2025 - Present | Hybrid, Bengaluru
*Shipment-tracking SaaS for mid-size logistics companies (from the public website).*
*Confidentiality: never name Tidewater customers or carrier partners. Say "carrier integrations".*

- `[BE]` Built a webhook ingestion service in Python (FastAPI) for 6 carrier integrations: idempotency keys in PostgreSQL to drop duplicate events, and retries with exponential backoff for failed deliveries.
- `[AI][BE]` Shipped an internal support assistant that answers agent questions with RAG over 1,200 help-center articles, using OpenAI embeddings and pgvector in PostgreSQL.
- `[AI]` Wrote an 80-question eval set with expected answers for the assistant and reran it on every prompt or model change before release.
- `[INFRA]` Moved 2 cron jobs to AWS Lambda with EventBridge schedules, added structured JSON logs and CloudWatch alarms.
- `[FE][FS]` Built React and TypeScript admin screens for the operations team to replay failed webhook events.
- `[ALL]` Wrote the runbook for the webhook service and handled its on-call rotation for one quarter.
- **Stack:** Python, FastAPI, PostgreSQL, pgvector, OpenAI API, AWS (Lambda, EventBridge, CloudWatch, S3), Docker, React, TypeScript, GitHub Actions.

### 2. Data Engineering Intern | Kestrel Analytics | Jan 2025 - Jun 2025 | Remote
- `[DATA]` Built 3 Airflow pipelines that load marketing data from REST APIs into BigQuery, with schema checks before each load.
- `[DATA]` Wrote SQL models and a Looker Studio dashboard used in the weekly client report.
- **Stack:** Python, Airflow, BigQuery, SQL, Looker Studio.

---

## PROJECTS
- **DocSift (open source):** PDF question answering with RAG. Python, FastAPI, Chroma, OpenAI API. github.com/aarav-mehta-example/docsift
- **TrailMap (2nd place, Example State Hackathon 2024):** route planner for delivery riders with a React front end and a Python routing service.

## EDUCATION
- **B.Tech, Computer Science and Engineering**, Example Institute of Technology, Bengaluru | Aug 2021 - May 2025 | CGPA 8.4/10

## ACHIEVEMENTS
- 2nd place, Example State Hackathon 2024 (TrailMap)

---

## SKILLS INVENTORY
- **Languages:** Python, TypeScript, JavaScript, SQL
- **Backend:** FastAPI, REST APIs, webhooks, PostgreSQL, idempotency, retries with backoff
- **AI / ML:** LLM applications, RAG, embeddings, pgvector, Chroma, OpenAI API, LLM evaluation with eval sets
- **Frontend:** React, TypeScript
- **Data:** Airflow, BigQuery, Looker Studio
- **Cloud / Infra:** AWS (Lambda, EventBridge, CloudWatch, S3), Docker, GitHub Actions
- **Not used in production (say so if asked):** LangChain, Kubernetes

---

## STORY BANK

### Duplicate carrier events
- **Answers:** hardest bug | ownership
- **Situation:** carriers resent the same status event, so shipments showed "delivered" twice and alerts fired twice.
- **Task:** stop duplicates without losing real events.
- **Action:** added an idempotency key per event in PostgreSQL and a unique constraint, and moved retries to exponential backoff.
- **Result:** duplicate alerts stopped. Failed deliveries are retried instead of dropped.
- **Reflection:** should have added the constraint on day one instead of deduping in code.

### Eval set before launch
- **Answers:** quality | judgment
- **Situation:** the support assistant gave confident wrong answers on refund questions in testing.
- **Task:** know if a prompt change made it better or worse.
- **Action:** wrote 80 questions with expected answers from the help center and reran them on every change.
- **Result:** the team only shipped prompt changes that passed the set.
- **Reflection:** would add retrieval checks next, not just final-answer checks.

---

## STANDARD FACTS FOR FORMS
- **Years of experience:** 1 year 4 months full-time since Jul 2025, plus a 6-month internship
- **Years of experience (decimal, for numeric fields):** 1.4
- **Notice period:** 30 days
- **Work authorization:** Indian citizen, no sponsorship needed in India

---

## OPEN ITEMS
1. `[confirm: assistant usage numbers Aarav is allowed to share]`
