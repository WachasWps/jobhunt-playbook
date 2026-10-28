#!/usr/bin/env python3
"""Threads hiring-post harvester, driven by an agent through a browser MCP. Optional.

Threads search may need a one-time login in the browser profile the agent uses.
This is NOT a standalone script. Ask your agent: "run the Threads post harvest". It will:
  1. open threads.net/search for each configured query in its browser
  2. scroll a few times, then run EXTRACTOR_JS on the page
  3. pass the extracted list to posts_common.process(raw, source="threads")

harvest() takes the browser tool calls as callables so the same flow works with any
browser MCP (Playwright MCP, Chrome DevTools MCP, browser-mcp). Keep pacing human-like.
Running this file directly only prints the search URLs.
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from posts_common import CFG, build_queries, process  # noqa: E402

PH = CFG["post_harvest"]

# Threads renders posts as articles. Class names change often; innerText is reliable.
EXTRACTOR_JS = r"""
() => {
  const out = [];
  const cards = document.querySelectorAll(
    'div[data-pressable-container] article, div[role="article"]'
  );
  cards.forEach(card => {
    try {
      let text = '';
      card.querySelectorAll('span[dir="auto"]').forEach(p => {
        if (p.innerText.length > text.length) text = p.innerText;
      });
      if (!text || text.length < 20) return;
      const linkEl = card.querySelector('a[href^="/@"], a[href*="threads.net/@"]');
      const authorUrl = linkEl ? linkEl.href.split('?')[0] : '';
      const m = authorUrl.match(/@([^/]+)/);
      const timeLink = card.querySelector('a[href*="/post/"]');
      const timeEl = card.querySelector('time');
      out.push({
        author: m ? m[1] : '',
        authorUrl,
        text: text.trim(),
        postUrl: timeLink ? timeLink.href.split('?')[0] : '',
        age: timeEl ? (timeEl.getAttribute('datetime') || timeEl.innerText) : ''
      });
    } catch (e) {}
  });
  return out;
}
"""

SCROLL_JS = "window.scrollBy(0, document.body.scrollHeight * 0.5);"


def build_search_url(query: str) -> str:
    return "https://www.threads.net/search?q=" + urllib.parse.quote(query) + "&serp_type=default"


def harvest(navigate, evaluate) -> list[dict]:
    """navigate(url) and evaluate(js) are the agent's browser tool calls."""
    queries = build_queries()[:PH["max_queries_per_run"]]
    all_raw, seen = [], set()
    for i, query in enumerate(queries):
        print(f"[Threads {i + 1}/{len(queries)}] {query}")
        navigate(build_search_url(query))
        time.sleep(random.uniform(2, 3.5))
        for _ in range(PH.get("max_scroll_rounds", 3)):
            evaluate(SCROLL_JS)
            time.sleep(random.uniform(1.5, 2.5))
        try:
            posts = evaluate(EXTRACTOR_JS)
            if isinstance(posts, str):
                posts = json.loads(posts)
        except Exception as e:
            print(f"  extractor error: {e}")
            posts = []
        for p in (posts or [])[:PH["max_posts_per_query"]]:
            key = p.get("postUrl") or p.get("text", "")[:80]
            if key and key not in seen:
                seen.add(key)
                all_raw.append({"author": p.get("author"), "author_url": p.get("authorUrl"),
                                "text": p.get("text"), "post_url": p.get("postUrl"),
                                "age": p.get("age")})
        if i < len(queries) - 1:
            time.sleep(random.uniform(PH.get("pacing_seconds_min", 4), PH.get("pacing_seconds_max", 12)))
    fresh = process(all_raw, source="threads")
    print(f"Threads harvest done. {len(fresh)} net-new leads.")
    return fresh


if __name__ == "__main__":
    for i, q in enumerate(build_queries()[:PH["max_queries_per_run"]], 1):
        print(f"  {i}. {q}\n     {build_search_url(q)}")
    print("\nTo harvest, ask your agent: 'run the Threads post harvest'")
