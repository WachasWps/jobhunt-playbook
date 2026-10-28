#!/usr/bin/env python3
"""Fact guard: flag numbers, names and tech terms in a resume or form answer that no
verified source backs up, plus any banned characters (em-dash, en-dash, middle dot).

Usage
  python3 resume/templates/fact-check.py <file.md|answers.txt> [options]

Options
  --jd FILE           the job description. Terms found ONLY in the JD (not in your facts)
                      are printed as JD-ONLY notes: fine for the company name or a negation
                      ("not used in production"), a red flag if the line claims the skill.
  --strict            make JD-ONLY notes fail too
  --sources A,B,...   extra source files or directories (*.md, *.txt, *.json inside)
  --factsheet FILE    default: profile/factsheet.md
  --profile FILE      default: profile/profile.json

Exit code 0 = clean, 1 = something to check. A CHECK flag is not always a lie: it means
"no source mentions this". Either add the fact to the factsheet (if true) or remove it.

Lines in your sources that contain "[confirm" or "not used in production" do NOT count
as evidence, so unresolved items and skills you lack can never back a claim.

The idea of a "fact guard" comes from the open-source AienTech/dossier project.
This is an independent implementation, no code was copied.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

BANNED = re.compile("[\u2014\u2013\u00b7]")  # em-dash, en-dash, middle dot

IGNORE = {
    "summary", "skills", "experience", "projects", "education", "achievements", "technical",
    "present", "remote", "hybrid", "on-site", "onsite", "built", "shipped", "designed",
    "integrated", "led", "cut", "added", "ship", "now", "currently", "also", "the", "and", "with",
    "for", "freelance", "part-time", "full-time", "intern", "internship", "i", "i'm", "i've",
    "i'd", "my", "we", "our", "yes", "no", "nothing", "before", "after", "at", "a", "an",
    "ok", "na", "n/a", "etc", "e.g", "i.e", "vs", "p.s",
}
MONTHS = {m.lower() for m in (
    "Jan Feb Mar Apr May Jun Jul Aug Sep Sept Oct Nov Dec January February March April June "
    "July August September October November December").split()}
NUMBER = re.compile(r"(?<![\w.])(\d+(?:[.,]\d+)?)\s*(k|m|\+|%)?(?![\w])", re.I)
TERM = re.compile(r"\b(?:[A-Z][\w.+#/-]*[A-Za-z0-9+#]|[a-z]+\.[a-z]{2,}|\w*\d\w*)\b")


def norm_num(digits: str, suffix: str | None) -> float:
    v = float(digits.replace(",", ""))
    return v * {"k": 1e3, "m": 1e6}.get((suffix or "").lower(), 1)


NOT_EVIDENCE = ("[confirm", "not used in production")


def _read_sources(paths: list[Path], drop_unverified: bool = True) -> str:
    parts = []
    for p in paths:
        files = sorted(f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in (".md", ".txt", ".json")) \
            if p.is_dir() else ([p] if p.is_file() else [])
        if not files:
            print(f"warning: source not found: {p}", file=sys.stderr)
        for f in files:
            for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
                if drop_unverified and any(t in line.lower() for t in NOT_EVIDENCE):
                    continue
                parts.append(line)
    return "\n".join(parts)


def _nums(text: str) -> set:
    return {norm_num(m.group(1), m.group(2)) for m in NUMBER.finditer(text)}


def build_sources(factsheet: Path, profile: Path, extra: list[Path], jd: Path | None):
    if not factsheet.exists():
        sys.exit(f"ERROR: factsheet not found at {factsheet}. Copy profile/factsheet.template.md "
                 "to profile/factsheet.md and fill it in, or pass --factsheet.")
    facts = _read_sources([factsheet, profile] + extra)
    jd_text = _read_sources([jd], drop_unverified=False) if jd else ""
    return facts.lower(), _nums(facts), jd_text.lower(), _nums(jd_text)


def check(path: Path, src: str, nums: set, jd: str = "", jd_nums: set | None = None, strict: bool = False) -> int:
    jd_nums = jd_nums or set()
    flagged = []
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if BANNED.search(raw):
            flagged.append((n, "banned-char", BANNED.search(raw).group(0), raw.strip()))
        stripped = raw.lstrip()
        # contact lines and form-question lines are not claims
        if stripped.startswith("+") or "@" in raw:
            continue
        if stripped.startswith(("Link:", "Resume:", "Apply:", "URL:", "Source:")):
            continue
        if raw.rstrip().endswith(("?", "?**")):  # a form question, not a claim
            continue
        line = re.sub(r"https?://\S+|`[^`]*`", " ", raw)
        for m in NUMBER.finditer(line):
            v = norm_num(m.group(1), m.group(2))
            if v not in nums:
                kind = "jd-only" if v in jd_nums else "number"
                flagged.append((n, kind, m.group(0).strip(), raw.strip()))
        for m in TERM.finditer(line):
            t = m.group(0).strip(".")
            before = line[: m.start()].rstrip(" *")
            sentence_start = not before or before.endswith((".", ":", "-", "?", "!", "|", "(")) or before.endswith("**")
            if sentence_start and t.isalpha() and t[1:].islower():
                continue
            pieces = [p for p in re.split(r"[-/]", t)
                      if p and (any(c.isupper() for c in p[1:]) or any(c.isdigit() for c in p) or p[0].isupper())]
            for p in pieces or [t]:
                pl = p.lower()
                if pl in IGNORE or pl in MONTHS or len(p) < 2 or pl.isdigit() or pl in src:
                    continue
                flagged.append((n, "jd-only" if pl in jd else "term", p, raw.strip()))
    seen, failing = set(), 0
    for n, kind, claim, line in flagged:
        key = (kind, claim.lower()) if kind != "banned-char" else (kind, n)
        if key in seen:
            continue
        seen.add(key)
        label = "JD-ONLY" if kind == "jd-only" else "CHECK"
        if kind != "jd-only" or strict:
            failing += 1
        print(f"{label} line {n} [{kind}] {claim!r}: {line[:110]}")
    if not failing:
        notes = len(seen)
        tail = f" ({notes} JD-ONLY note(s): confirm each is not a claim)" if notes else ""
        print(f"OK: {path.name}: every number and named term is backed by your facts, no banned characters{tail}.")
    return 1 if failing else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    ap.add_argument("--jd", type=Path)
    ap.add_argument("--sources", default="", help="comma-separated extra files or directories")
    ap.add_argument("--factsheet", type=Path, default=REPO / "profile" / "factsheet.md")
    ap.add_argument("--profile", type=Path, default=REPO / "profile" / "profile.json")
    ap.add_argument("--strict", action="store_true", help="fail on JD-ONLY terms too")
    a = ap.parse_args()
    extra = [Path(x.strip()) for x in a.sources.split(",") if x.strip()]
    src, nums, jd, jd_nums = build_sources(a.factsheet, a.profile, extra, a.jd)
    sys.exit(check(a.file, src, nums, jd, jd_nums, a.strict))


if __name__ == "__main__":
    main()
