# Cold email example (FICTIONAL)

Everyone and every company here is invented. Northwind Labs and Riya Kapoor do not exist. `.example` domains are reserved and never deliver.

## Lead record
- **Company:** Northwind Labs (seed-stage, builds an AI assistant for clinic front desks)
- **Person:** Riya Kapoor, co-founder and CTO
- **Source:** her LinkedIn post on Oct 26: "hiring our first backend engineer, 0-2 years, Bengaluru, Python"
- **Email:** riya@northwind.example
- **Verification:** the address is written in her post ("send your resume to riya@...") and the domain has MX records (`dig MX northwind.example +short` returned Google Workspace hosts). Product site is northwind-app.example, which has NO MX, so mail must go to the northwind.example domain.
- **Resume:** `tailored/2026-10/northwind-backend-engineer/Aarav_Mehta_Resume.pdf` (tailored, preflight passed)
- **Paired DM:** LinkedIn connection note to Riya, sent the same day (below)

## Email

**Subject:** first backend engineer, webhooks and rag in prod

Hi Riya,

Saw your post about hiring the first backend engineer at Northwind. Clinic front desks live on missed calls and double bookings, so I can see why reliable integrations matter here.

At Tidewater Systems I built a FastAPI webhook service for 6 carrier integrations, with idempotency keys in PostgreSQL and retries with backoff. I also shipped a RAG support assistant with an eval set that gates every prompt change.

Worth a quick 15 min chat this week?

Aarav Mehta
github.com/aarav-mehta-example | linkedin.com/in/aarav-mehta-example

P.S. I tried the demo on northwind-app.example. Rescheduling took two taps, which is rare.

*(Body is about 80 words. Hook is about them. Two lines of proof from the factsheet. One yes or no question. The P.S. is true and specific.)*

## Paired LinkedIn connection note (under 300 characters)

Hi Riya, saw your post about Northwind's first backend hire. I build FastAPI webhook services and a RAG assistant in production at Tidewater Systems. Just emailed you my resume. Happy to chat if it fits.

## Follow-up (day 5, in the same thread, only if no reply)

Hi Riya, bumping this in case it got buried. Happy to do a short take-home on one of your integrations if that is easier than a call.

Aarav

## If she replies "sure, send times" (match her length)

Great, Thu 4pm or Fri 11am work for me. Or send a link and I will pick a slot.

Aarav
