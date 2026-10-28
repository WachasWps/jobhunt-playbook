# 05. Cold outreach and email verification

Short, specific emails to real people at companies where you fit, sent to verified addresses, paired with a LinkedIn DM, followed up once or twice. The agent drafts and verifies. The human sends.

## Who to write to

In order of reply rate:
1. The person who posted the role (a LinkedIn post, a Reddit thread comment, an HN comment).
2. The hiring manager or the engineer who leads the team.
3. A founder or CTO at an early-stage company (under about 50 people).
4. A recruiter named on the posting.

Avoid generic inboxes (`careers@`, `hello@`) unless the post asks for them. They bounce or go unread more often.

Check `tracker/outreach-log.csv` first. Never pitch the same person twice, and do not pitch a second person at the same company within a few weeks unless it is for a different, specific role.

## The email formula

- **Subject:** 5 to 9 words, lowercase-leaning, specific. It should read like a human typed it: `first backend engineer, webhooks and rag in prod`, `sde role at <company>, can join in 30 days`.
- **Body:** 60 to 90 words.
  - **Line 1, the hook, about THEM:** their post, their product, a launch, a specific problem in their space. Not about you.
  - **1 to 2 lines of proof:** the one or two things you built that match what they need, with real tech names and real numbers from the factsheet.
  - **One binary CTA:** a yes or no question. "Worth a quick 15 min chat?" works. Never three options.
- **Signature:** name, then `github.com/you | linkedin.com/in/you`. No phone unless they asked. No quotes or logos.
- **P.S.:** one human line tied to something real. You used their product, you live in their city, you read their engineering post. Never a made-up anecdote.
- **Attachment:** the tailored resume PDF, named `First_Last_Resume.pdf`.

Full example: `examples/aarav-mehta/cold-email.md`. Drafting prompt: `prompts/cold-outreach-drafter.md`.

Things that kill replies: a long intro about yourself, "I hope this email finds you well", buzzwords, em-dashes, three CTAs, a pasted resume summary, a wall of text.

## Email verification (never blind-guess)

Blind `firstname@domain` guesses bounced about 30% of the time in our runs, and bounces hurt your sender reputation more than silence does. Verify every address, in this order:

1. **Published by them.** In the hiring post itself, or on the company site: `/contact`, `/about`, `/team`, `/careers`, `/privacy`, `/security`, the footer. A post that says "send your CV to x@company.com" is the best signal there is.
2. **GitHub commit emails.** For technical founders, the author email on their own commits is ground truth. Look at the company's or the founder's public repos, open a commit and append `.patch` to the commit URL, or use `gh api repos/<owner>/<repo>/commits` and read `commit.author.email`. Ignore `@users.noreply.github.com`.
3. **A proven pattern.** If you have one real address at the same domain (from 1 or 2), derive the format (`first@`, `first.last@`) for another person there. Mark it as pattern-derived, lower confidence.
4. **SMTP verifier.** Optional. Apify actors exist for this (search the Apify store for an email verifier). Beware catch-all domains: they accept every address, so "valid" proves nothing there.
5. **Check MX on the exact domain:**
   ```bash
   dig MX company.com +short
   ```
   No MX records means mail to that domain will not deliver.

**Watch for the wrong domain.** A real case: the product domain had no MX at all, and the founder's working address was on a different domain (the parent company's), listed on the product's contact page. Other traps: a parked or expired domain, a rebrand (old domain dead, new one live), a different company with the same name, and a person who has left. Check the domain is the company you mean and that it has MX.

If nothing verifies, use a LinkedIn DM instead of guessing.

Record how you verified in `tracker/outreach-log.csv` (`email_source`: post, site, github, pattern, verifier, and `mx_checked`: yes or no).

## Pair every email with a LinkedIn DM

Send a connection request with a note (LinkedIn caps notes at 300 characters) the same day:

> Hi <first name>, saw your post about <role>. I build <one matching thing> at <company>. Just emailed you my resume. Happy to chat if it fits.

The DM is the human channel: zero bounce, and founders read their LinkedIn. Send it from the user's own account, by hand. Never automate LinkedIn.

## Volume and pacing

- At most **15 to 20 cold emails a day**, spread through the day. A burst of 35 emails in 2 minutes once hurt deliverability.
- Quality first: 10 sharp emails to people who posted a role beat 40 to generic inboxes.
- New Gmail account or new domain: start at 5 a day and ramp.

## Follow-ups

- **Day 5, no reply:** one follow-up **in the same thread** (reply to your own sent email so it stacks under the original). 2 to 4 lines, add something new: a relevant link, a one-line result, an offer to do a short take-home. Never "just checking in" or "any update?".
- **Forgot the attachment:** follow up in the same thread right away with the file and one short line.
- **Second follow-up:** about a week later, if at all. After 2 follow-ups with no reply, mark the contact `cold` and stop.
- **Bounce:** mark it, find the right address or switch to a LinkedIn DM.

## Replies

- **Match their tone and length.** Two casual lines in means two casual lines out. A long, polished reply to a short message reads as AI-written and cools a warm lead.
- Contractions are fine. Drop the heavy signature in replies.
- Scheduling: offer two concrete slots or ask for their link. If they go quiet after "let's chat", nudge after 3 days with slots, not "any update?".
- Before a call: research the company and the person (their posts, talks, repos), map what you built to their problem, and prepare 2 or 3 questions.

## Tools

- **Gmail MCP** (`docs/09`): create drafts, including in-thread replies. Most connectors cannot attach files, so the user drags the PDF into the draft before sending. Prefer a connector without a send tool, or deny the send tool in your agent's permissions.
- **No Gmail MCP:** the agent writes drafts to `outreach/YYYY-MM-DD-cold.md` with To, Subject, Body, the resume path and the verification note. The user copies them into Gmail.

## Checklist per email

- [ ] Address verified, source recorded, MX checked
- [ ] Not already contacted (outreach log)
- [ ] Subject 5 to 9 words, specific
- [ ] Body 60 to 90 words, hook about them, proof from the factsheet, one yes or no CTA
- [ ] True P.S.
- [ ] No em-dashes, en-dashes or middle dots (`fact-check.py` on the draft catches them)
- [ ] Tailored resume attached
- [ ] LinkedIn note drafted
- [ ] Logged with `next_followup` at +5 days
