# 04. Applying in the real browser

The agent fills application forms in the user's own Chrome. The user solves captchas, checks the form and clicks Submit.

## Why the real browser

- **Automated browsers get rejected.** Lever returned "There was an error verifying your application" for applications from headless and Playwright browsers. The same application from the user's own Chrome went through.
- **The user can reach it.** Captchas, OTPs and the final review need the human. A separate automation browser window is often somewhere they cannot easily interact with. Their own Chrome is right in front of them.
- **Logins are already there.** Workday accounts, Google sign-in, saved addresses.

Use a browser MCP that attaches to the user's real Chrome. We used Agent360 browser-mcp, pinned to a reviewed version (`docs/09` has the install and the security review checklist). Chrome DevTools MCP with `--autoConnect` is an alternative.

## Who does what

| Step | Agent | Human |
|---|---|---|
| Open the posting, read knockouts | yes | |
| Fill fields from `answers.txt` and `profile.json` | yes | |
| Upload the tailored PDF | yes | |
| Re-read the form and confirm every required field holds its value | yes | |
| Captcha, OTP, login, 2FA | never | yes |
| Final review | | yes |
| Click Submit | only if the human says so for that form | yes, by default |
| Confirm the success page, log it, close the tab | yes | |

Never solve or auto-click a captcha, even when the tool offers a captcha action. Disable those tools (`docs/09`). Never spoof a user agent or hide automation signals.

## Pipeline it

Do not fill one form, wait, fill the next. Instead:
1. Prefill 3 to 5 tabs, one tab per application. Navigating the same tab to the next job wipes the filled form.
2. Hand them over together: a short list of tab, company, role, "captcha: yes/no", and anything the user must decide.
3. While the user reviews and submits, subagents prepare the next batch (tailoring, answers). See `docs/06`.

## Per-ATS notes

| ATS / site | Notes |
|---|---|
| **Greenhouse** | Often an invisible reCAPTCHA. Comboboxes (react-select): type, wait for the option list, then pick. School or company not listed: choose "Other". Location fields are autocomplete. |
| **Lever** | hCaptcha checkbox the human must tick. Rejects automated browsers, so the real browser is required. There is a hidden duplicate of the consent checkbox: target the visible one and check that it is actually ticked. Do not use "Apply with LinkedIn", fill the form so you control every answer. |
| **Ashby** | Usually clean. Has per-company application limits (for example a few applications per 60 or 180 days). A limit error means you already applied there recently. Pick the single best role per company. |
| **Workable** | The address or location field is an autocomplete. Type, wait, choose a suggestion, or the value does not stick. |
| **Workday** | Account per company, multi-page. Ask the user to sign in. Upload the resume first and then fix the fields it mis-parses. |
| **Google Forms** | Script-generated clicks do not register on Google Forms controls. Use real clicks, keyboard input (Tab, Space, arrows), or hand the form to the user. |
| **binary.so** | Sends an email OTP to log in. Ask the user for the code. |
| **Zia (itszia.ai)** and other AI pre-screens | An AI screen scores your years of experience. If you are screened out on years but the role fits, email the founder or hiring manager directly with a short note (`docs/05`). |
| **LinkedIn Easy Apply, Naukri** | Not automated by this system. The user applies there by hand if at all. |

## Technical tips for form filling

- **React and other controlled inputs need real input events.** Setting `input.value = "..."` in a script often looks right and is silently discarded on submit. Use the MCP's type or fill tool (it sends key events), or set the value through the native setter and dispatch `input` and `change` events. Then read the value back.
- **Chrome only delivers real clicks to a visible tab.** Trusted (CDP) mouse clicks on a background tab may do nothing. Switch to the tab, or ask the user before bringing Chrome to the front.
- **Some forms render twice** (a mobile and a desktop copy in the same DOM). Selectors can hit the hidden copy. Target the element that is visible (non-zero bounding box, `offsetParent` not null).
- **File upload:** use the MCP's upload tool with the absolute path of the tailored PDF. Confirm the file name appears on the page.
- **Dropdowns and comboboxes:** type to filter, then press Enter or click the option. Verify the chosen value is displayed.
- **Dates:** check the expected format on the field (DD/MM/YYYY vs MM/DD/YYYY).
- **Long answers:** paste from `answers.txt`, then check the field did not truncate at a character limit.
- **After filling:** take a screenshot or read the form state back, field by field. Required fields with an asterisk must all hold values.

## Answering form questions

- Knockouts: exactly what the factsheet says. If the truth disqualifies, stop and tell the user.
- Comp fields: `docs/07`.
- "Why us": specific to the company, from the JD or their product, 2 to 4 sentences.
- Optional demographic fields: leave blank or "prefer not to say" unless the user says otherwise.
- "How did you hear about us": the true source (careers page, a named person's LinkedIn post, a referral).
- Consent to be considered for future roles: tick it unless the user objects.
- Judgment calls (for example "is your experience mostly frontend?" when it is mixed): ask the user.

## After submit

1. Confirm the success page or confirmation email.
2. Append the row to `tracker/applications.csv` with `next_followup` set.
3. Close the tab.
4. If there is a hiring manager or founder you can reach, queue a short note (`docs/05`). A tailored application plus a direct note beats either alone.
