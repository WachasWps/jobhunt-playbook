#!/usr/bin/env bash
# Pre-send checklist for one tailored application folder, in one command:
#   1. fact-check the resume (and answers.txt if present) against the factsheet + jd.txt
#   2. scan for banned characters (em-dash, en-dash, middle dot)
#   3. render the PDF and confirm it is exactly 1 page
#
# Usage:
#   bash resume/templates/preflight.sh tailored/2026-10/acme-backend-engineer
#   FACTSHEET=examples/aarav-mehta/factsheet.md PROFILE=examples/aarav-mehta/profile.json \
#     bash resume/templates/preflight.sh examples/aarav-mehta/tailored/2026-10/acme-ai-engineer
#
# The folder must contain First_Last_Resume.md (or resume.md). jd.txt and answers.txt
# are used when present.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
DIR="${1:?usage: preflight.sh <tailored-folder>}"
FACTSHEET="${FACTSHEET:-$REPO/profile/factsheet.md}"
PROFILE="${PROFILE:-$REPO/profile/profile.json}"
fail=0

RESUME=""
for cand in "$DIR"/*_Resume.md "$DIR"/resume.md; do
  if [ -f "$cand" ]; then RESUME="$cand"; break; fi
done
[ -n "$RESUME" ] || { echo "ERROR: no *_Resume.md or resume.md in $DIR"; exit 2; }

JD_ARGS=()
[ -f "$DIR/jd.txt" ] && JD_ARGS=(--jd "$DIR/jd.txt")

echo "== 1. fact-check"
for f in "$RESUME" "$DIR/answers.txt"; do
  [ -f "$f" ] || continue
  python3 "$HERE/fact-check.py" "$f" --factsheet "$FACTSHEET" --profile "$PROFILE" ${JD_ARGS[@]+"${JD_ARGS[@]}"} || fail=1
done

echo "== 2. banned characters"
python3 - "$DIR" <<'EOF' || fail=1
import pathlib, re, sys
bad = re.compile("[\u2014\u2013\u00b7]")
hits = 0
for f in sorted(pathlib.Path(sys.argv[1]).glob("*")):
    if f.suffix in (".md", ".txt"):
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if bad.search(line):
                hits += 1
                print(f"{f.name}:{n}: {line.strip()[:100]}")
print("FAIL: replace these with commas, periods, hyphens or |" if hits else "OK: none found")
sys.exit(1 if hits else 0)
EOF

echo "== 3. render + page count"
out="$(bash "$HERE/render-pdf.sh" "$RESUME" 2>&1)"; echo "$out"
echo "$out" | grep -q "WARNING\|ERROR" && fail=1

if [ "$fail" -eq 0 ]; then
  echo "PREFLIGHT PASSED: $DIR"
else
  echo "PREFLIGHT FAILED: fix the items above before sending."
fi
exit "$fail"
