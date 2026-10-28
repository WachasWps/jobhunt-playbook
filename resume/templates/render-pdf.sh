#!/usr/bin/env bash
# Render resume Markdown -> HTML -> PDF with headless Chrome, then report the page count.
# Usage:
#   bash resume/templates/render-pdf.sh path/to/First_Last_Resume.md [more.md ...]
#   bash resume/templates/render-pdf.sh            # no args = every .md under resume/base/
# Env:
#   CHROME=/path/to/chrome   override browser detection
# Output: .html and .pdf with the same name, next to each .md file.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
CSS="$HERE/resume.css"

find_chrome() {
  if [ -n "${CHROME:-}" ]; then echo "$CHROME"; return; fi
  for c in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "$(command -v google-chrome 2>/dev/null || true)" \
    "$(command -v google-chrome-stable 2>/dev/null || true)" \
    "$(command -v chromium 2>/dev/null || true)" \
    "$(command -v chromium-browser 2>/dev/null || true)"; do
    if [ -n "$c" ] && [ -x "$c" ]; then echo "$c"; return; fi
  done
  echo "ERROR: Chrome or Chromium not found. Set CHROME=/path/to/chrome" >&2
  exit 1
}
CHROME_BIN="$(find_chrome)"

FILES=()
if [ "$#" -gt 0 ]; then
  FILES=("$@")
else
  while IFS= read -r f; do FILES+=("$f"); done < <(find "$REPO/resume/base" -name '*.md' ! -name 'README.md' 2>/dev/null)
fi
if [ "${#FILES[@]}" -eq 0 ]; then
  echo "No Markdown files to render." >&2
  exit 1
fi

for md in "${FILES[@]}"; do
  dir="$(cd "$(dirname "$md")" && pwd)"
  name="$(basename "$md")"; name="${name%.md}"
  html="$dir/$name.html"
  pdf="$dir/$name.pdf"
  node "$HERE/md-to-html.js" "$md" "$CSS" "$html" >/dev/null
  "$CHROME_BIN" --headless=new --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$pdf" "file://$html" >/dev/null 2>&1
  pages=""
  if command -v pdfinfo >/dev/null 2>&1; then
    pages="$(pdfinfo "$pdf" 2>/dev/null | awk '/^Pages:/ {print $2}')"
  fi
  echo "PDF: ${pdf#"$REPO"/}${pages:+  (pages: $pages)}"
  if [ -n "$pages" ] && [ "$pages" != "1" ]; then
    echo "WARNING: $name.pdf is $pages pages. Trim it to 1 page (see docs/01-ats-and-resume-rules.md)." >&2
  fi
done
