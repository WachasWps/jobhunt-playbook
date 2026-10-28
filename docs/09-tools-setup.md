# 09. Tools setup

Everything the system uses, how to install it, and how to review a browser extension before you let an agent drive your real Chrome.

## Base tools

| Tool | Why | Install (macOS example) |
|---|---|---|
| Python 3.9+ | discovery, ranking, fact guard | preinstalled or `brew install python` |
| Node 18+ | Markdown to HTML renderer | `brew install node` |
| Google Chrome or Chromium | headless PDF rendering, real-browser applying | chrome.com |
| poppler (`pdfinfo`) | 1-page check | `brew install poppler` / `apt install poppler-utils` |
| `python-docx` (optional) | DOCX resumes | `pip install python-docx` |
| `telethon` (optional) | Telegram harvester | `pip install telethon` (use a venv if your Python is externally managed) |
| `dig` | MX checks for email verification | preinstalled on macOS and most Linux |
| `gh` (optional) | GitHub commit-email lookups | `brew install gh` |

Check:
```bash
python3 --version && node --version && pdfinfo -v && dig -v
bash resume/templates/render-pdf.sh examples/aarav-mehta/tailored/2026-10/acme-ai-engineer/Aarav_Mehta_Resume.md
```
If Chrome is not found, set `CHROME=/path/to/chrome`.

## Browser MCP for the user's real Chrome

The agent needs to drive the user's own signed-in Chrome (`docs/04` explains why). We used **Agent360 browser-mcp** (MIT, npm package `@agent360/browser-mcp`, source on GitHub at Agent360dk/browser-mcp). It has two halves: a Chrome extension and a local MCP server.

### Install, pinned to a version you reviewed

1. Pick a version and review it (checklist below). We ran `1.30.3`.
2. Install the Chrome extension from the Chrome Web Store listing linked in the project README. Consider a **dedicated Chrome profile** for job hunting, signed in only to what the hunt needs (Gmail, LinkedIn, ATS accounts). It limits what the extension can see.
3. Add the MCP server **with the exact version**, never `@latest`:
   ```bash
   # Claude Code
   claude mcp add --scope user browser-mcp -- npx -y @agent360/browser-mcp@1.30.3
   ```
   For Codex or another client, add the same command (`npx -y @agent360/browser-mcp@1.30.3`) to that client's MCP config.
4. Restart the agent. Ask it to open example.com and take a screenshot to confirm it works.
5. **Deny the tools this system must never use.** In Claude Code, add them to `permissions.deny` in `.claude/settings.json` (or pass `--disallowedTools`):
   ```json
   {
     "permissions": {
       "deny": [
         "mcp__browser-mcp__browser_solve_captcha",
         "mcp__browser-mcp__browser_get_cookies",
         "mcp__browser-mcp__browser_set_cookies",
         "mcp__browser-mcp__browser_extract_token",
         "mcp__browser-mcp__browser_get_local_storage",
         "mcp__browser-mcp__browser_set_local_storage"
       ]
     }
   }
   ```
   Tool names differ by server and version. List them first and adjust.
6. To upgrade: review the new version with the checklist, then change the pinned version. Do not let `npx` pull a new version silently.

Alternative: Chrome DevTools MCP (`npx chrome-devtools-mcp@<version> --autoConnect`) attaches to a running Chrome with remote debugging enabled. Same pinning and review rules apply.

Do not use a separate headless or Playwright browser for applications. Lever rejects them, and the user cannot reach them for captchas. A Playwright browser is fine for public read-only pages.

### Security review checklist (before install and before every upgrade)

An extension that drives your browser can see every site you are signed in to. Review it like you would review a dependency with root access.

- [ ] **Source and license:** public repository, a license you accept (MIT here), a real maintainer, recent activity. The npm package links to that repository.
- [ ] **Pinned version:** you know exactly which version runs (`@x.y.z`, not `@latest`, no `^` ranges).
- [ ] **Diff on upgrade:** `npm diff --diff=@agent360/browser-mcp@<old> --diff=@agent360/browser-mcp@<new>` and read what changed, especially network code.
- [ ] **Extension permissions:** read `manifest.json`. Expect `tabs`, `scripting`, `debugger` and broad host access for a tool like this. Know that `cookies` and `<all_urls>` mean it can read session cookies on every site. That is why the cookie and token tools are denied above.
- [ ] **Network:** the local server should bind to `127.0.0.1` only. Search the code for outbound `fetch`, `XMLHttpRequest`, `WebSocket` and analytics or telemetry endpoints. "No telemetry" should be checkable in code, not just claimed.
- [ ] **Install scripts:** check `package.json` for `preinstall` or `postinstall` scripts and read them.
- [ ] **Tool list:** list the MCP tools. Deny anything you do not need (cookies, tokens, local storage, captcha solving).
- [ ] **Human prompts:** the agent must ask you for passwords, OTPs and captchas. Nothing sensitive should be typed by the agent from memory.
- [ ] **Scope:** prefer a dedicated Chrome profile. Close tabs for banking or anything unrelated while the agent works.

## Apify (LinkedIn hiring posts)

1. Create a free account at apify.com. The free plan includes about $5 a month of credit.
2. Copy the API token (Settings, API & Integrations).
3. Save it where only you can read it, never in git:
   ```bash
   echo "<token>" > jobhunt/.apify_token && chmod 600 jobhunt/.apify_token
   # or: export APIFY_TOKEN=<token> in your shell profile or .env
   ```
4. `python3 jobhunt/sources/linkedin_posts.py --dry-run`, then a real run. The script sends the token in an Authorization header, never in the URL.
5. Credit gone (402 or 403): wait for the monthly reset or add credit.

Optional Apify actors for email work (`docs/05`): an SMTP email verifier and a website email scraper. Search the Apify store, check pricing per result, and remember catch-all domains.

## Exa web search (via mcporter, or as an MCP)

Exa gives clean web search and page fetch for company and founder research.

**Option A, mcporter (a CLI that calls MCP servers):**
```bash
npm install -g mcporter
mkdir -p config && cp config/mcporter.example.json config/mcporter.json
mcporter list exa --config config/mcporter.json          # shows tools and arguments
mcporter call exa.web_search_exa query="seed-stage clinic scheduling startups in Bengaluru hiring backend engineers" \
  numResults=5 objective="company pages and recent hiring posts, skip job aggregators" --config config/mcporter.json
mcporter call exa.web_fetch_exa urls='["https://example.com/careers"]' --config config/mcporter.json
```
`config/mcporter.json` is gitignored in case you add an API key to it.

**Option B, add it to your agent directly:**
```bash
claude mcp add --transport http exa https://mcp.exa.ai/mcp
```

Cap research at about 5 searches per JD.

## Gmail MCP (optional)

Lets the agent create drafts (including in-thread replies) and search sent mail for follow-ups.

- Prefer a connector that **cannot send** (for example the Claude Gmail connector exposes draft creation and search, not send). If yours has a send tool, deny it in permissions.
- Most connectors cannot attach files. The user drags the PDF into the draft and clicks Send.
- Useful queries: sent mail with your GitHub link in the last 30 days, to find silent threads; `from:mailer-daemon` for bounces.
- Without a Gmail MCP, the agent writes drafts to `outreach/` and the user pastes them.

## Telegram (optional)

See the header of `jobhunt/sources/telegram_posts.py`. You create an app at my.telegram.org, export `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`, and log in once in your own terminal. The session file is a login credential: it is gitignored, never share it.

## Secrets summary

| Secret | Where | Never |
|---|---|---|
| Apify token | `jobhunt/.apify_token` or `APIFY_TOKEN` | in git, in a URL, in chat |
| Telegram api_hash, session | env vars, `jobhunt/.telegram.session` | in git, shared |
| Exa key (if any) | `config/mcporter.json` or env | in git |
| Passwords, OTPs | typed by the user | stored anywhere |
