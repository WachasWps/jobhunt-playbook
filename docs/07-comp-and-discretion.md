# 07. Compensation answers and discretion while employed

Forms ask for current and expected compensation, and job hunting while employed needs care. These rules come from what background checks actually verify and what can get back to a current employer.

## Current CTC: always the truth

- **Report current CTC truthfully.** Background verification checks it against bank credits, Form 16 and the income tax return (ITR), and often your last payslips. An inflated number found at that stage can cost you the offer, sometimes after you have resigned.
- Use the exact figure a check would find. Put it in `profile/profile.json` > `compensation.current_ctc_numeric` and `current_ctc_text` once, so every form uses the same number.
- **Fixed vs variable:** if your CTC has a variable part, say "X fixed + Y variable" in text fields. In a single numeric field, use the figure your offer letter calls CTC.
- **USD contractor pay:** convert to annual INR at the current exchange rate for numeric INR fields, and state the basis in text fields, for example "about X lakhs per annum, paid in USD as $N per month". Recompute when the rate moves.
- **Do not volunteer current CTC** where the form does not ask. In email, focus on fit, not money.

## Expected CTC: a range, set by the role

- Give a **range**, not a single number: "A to B lakhs per annum, open to discuss".
- The bottom of the range is a number you would actually accept.
- **For roles with a clearly higher posted band, ask higher.** If the posting or the market says the band starts above your range, quote near that band. Your ask should be set by the role, not only by your current pay.
- Remote USD roles: "open to discuss, around $N per month" or the posted band.
- Keep `expected_ctc_range` and `expected_ctc_high_band` in `profile.json`. The agent picks one per role and notes which in `answers.txt`.

## Never claim what you cannot verify

- No statements about your current package that you cannot prove, for example "I have no ESOPs" when you are not sure what your grant says, or a bonus you have not been paid.
- No competing-offer claims that do not exist.
- No title inflation beyond what your offer letter or LinkedIn shows. Using a standard searched title in a resume headline is fine only when it honestly describes the work (`docs/01`), and forms asking for "official title" get the official one.

## Discretion while employed

1. **No public Open-to-Work banner on LinkedIn.** It is visible to your colleagues and your employer's investors. Recruiter-only visibility is a setting the user changes themselves, the agent does not.
2. **Block your current employer on job portals** that support it (most Indian portals have a "hide profile from" or "block companies" setting). The user sets this.
3. **Avoid outreach likely to loop back.** Skip people close to your current employer: its investors, advisors, accelerator batchmates, close partners and customers. Add them to `profile.json` > `targeting.avoid_companies`. Ask the user when unsure.
4. **"Why are you leaving" stays positive.** Talk about scope, growth and the kind of problems you want next. Never criticize the current employer.
5. **Never reveal internals.** No customer or partner names, no internal metrics, revenue or headcount, no unreleased features, no ticket IDs, no internal tool names. Describe the work generically: "built an audit trail for support-team edits", not who the customers are.
6. **Keep the current job on the resume.** Hiding it would be dishonest and fails background checks. Discretion comes from where and how you search, not from hiding the job.
7. **Use personal accounts only.** Personal email, personal laptop where possible, never the work Slack, work email or work GitHub account for job hunting. On a shared machine, check which GitHub account the CLI is logged in as before any `gh` command.
8. **Notice period:** state the real one. "Immediately available" when you have a 30-day notice is a lie that surfaces fast.
9. **No urgency framing** when employed. Not "I will take anything" or "leaving soon". You are choosing, not escaping.

## Answers the agent can reuse

- "Why are you looking?": "I want to spend more of my time on <the kind of work in this JD>. This role is built around that."
- "Current CTC?" (text field): `<current_ctc_text>`.
- "Expected CTC?": `<expected range for this role>`, open to discuss.
- "Notice period?": `<notice_period>`.
- "Can you share details of your current project?": a generic one-line description of the problem and your part in it. No names.

When a form asks something in this area that the answer bank does not cover, the agent stops and asks the user.
