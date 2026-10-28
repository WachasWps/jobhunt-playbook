#!/usr/bin/env node
/* Convert the constrained resume Markdown -> self-contained, ATS-safe HTML.
   Usage: node md-to-html.js <input.md> <css-path> <output.html>

   Expected Markdown shape (see examples/aarav-mehta/tailored/2026-10/acme-ai-engineer/Aarav_Mehta_Resume.md):
     # Full Name
     **Headline title | focus areas**
     +91 90000 00000 | you@example.com | linkedin.com/in/you | github.com/you | City, Country
     ## Section
     ### Title | Company
     *Mon YYYY - Mon YYYY | Remote*
     - bullet */
const fs = require("fs");

const [, , inPath, cssPath, outPath] = process.argv;
let md = fs.readFileSync(inPath, "utf8");
const css = fs.readFileSync(cssPath, "utf8");

// strip accidental code fences / leading commentary before the name
md = md.replace(/```[a-z]*\n?/gi, "");
const firstH1 = md.indexOf("# ");
if (firstH1 > 0) md = md.slice(firstH1);

function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function inline(s) {
  s = esc(s);
  s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/(^|[^*])\*([^*]+?)\*(?!\*)/g, "$1<em>$2</em>");
  return s;
}
// Contact line is "|"-separated (a middle dot is also accepted). Tokenize and
// linkify each piece on its own so the regexes never overlap.
function linkToken(t) {
  t = t.trim();
  if (!t) return "";
  if (/@/.test(t)) return `<a href="mailto:${t}">${esc(t)}</a>`;
  if (/^(https?:\/\/)?[a-z0-9.-]+\.[a-z]{2,}(\/\S*)?$/i.test(t)) {
    const href = /^https?:\/\//i.test(t) ? t : "https://" + t;
    return `<a href="${href}">${esc(t)}</a>`;
  }
  return esc(t);
}
function linkifyContact(s) {
  return s.split(/[\u00b7|]/).map(linkToken).filter(Boolean).join(" | ");
}

const lines = md.split(/\r?\n/);
let out = [];
let i = 0;
let seenSection = false;
let listBuf = [];
let listClass = "";
let inJobBlock = false;
let curSection = "";

function flushList() {
  if (listBuf.length) {
    out.push(`<ul${listClass ? ` class="${listClass}"` : ""}>` + listBuf.join("") + "</ul>");
    listBuf = [];
  }
}
function closeJobBlock() {
  flushList();
  if (inJobBlock) { out.push("</div>"); inJobBlock = false; }
}

while (i < lines.length) {
  let line = lines[i].trim();
  if (line === "") { i++; continue; }

  // Name
  if (/^#\s+/.test(line) && !/^##/.test(line)) {
    flushList();
    out.push(`<h1>${inline(line.replace(/^#\s+/, ""))}</h1>`);
    i++;
    // optional bold role/subtitle line (e.g. "**AI Engineer**") before contact info
    while (i < lines.length && lines[i].trim() === "") i++;
    if (i < lines.length && /^\*\*.+\*\*$/.test(lines[i].trim())) {
      out.push(`<p class="role">${inline(lines[i].trim())}</p>`);
      i++;
      while (i < lines.length && lines[i].trim() === "") i++;
    }
    // contact = next non-empty line if it's not a heading and before any section
    if (i < lines.length && !/^#/.test(lines[i].trim())) {
      out.push(`<p class="contact">${linkifyContact(lines[i].trim())}</p>`);
      i++;
    }
    continue;
  }

  // Section heading
  if (/^##\s+/.test(line)) {
    closeJobBlock();
    seenSection = true;
    curSection = line.replace(/^##\s+/, "").trim();
    const low = curSection.toLowerCase();
    listClass = /skill|tool/.test(low) ? "skills" : (/project|achievement|selected work|award/.test(low) ? "compact" : "");
    out.push(`<h2>${inline(curSection)}</h2>`);
    i++;
    // Summary paragraph(s): if first content under "Summary" is a plain line, render as .summary
    continue;
  }

  // Job title (###), paired with the following *meta* line
  if (/^###\s+/.test(line)) {
    closeJobBlock();
    const title = line.replace(/^###\s+/, "").trim();
    let meta = "";
    let j = i + 1;
    while (j < lines.length && lines[j].trim() === "") j++;
    if (j < lines.length && /^\*.+\*$/.test(lines[j].trim())) {
      meta = lines[j].trim().replace(/^\*/, "").replace(/\*$/, "").trim();
      i = j + 1;
    } else {
      i = i + 1;
    }
    out.push(`<div class="job-block">`);
    inJobBlock = true;
    if (meta) {
      out.push(`<div class="job"><span class="title">${inline(title)}</span><span class="dates">${inline(meta)}</span></div>`);
    } else {
      out.push(`<div class="job"><span class="title">${inline(title)}</span></div>`);
    }
    continue;
  }

  // Bullet
  if (/^[-*]\s+/.test(line)) {
    listBuf.push(`<li>${inline(line.replace(/^[-*]\s+/, ""))}</li>`);
    i++;
    continue;
  }

  // Standalone italic meta (e.g., a subhead under a section)
  if (/^\*.+\*$/.test(line)) {
    flushList();
    out.push(`<p class="subhead">${inline(line.replace(/^\*/, "").replace(/\*$/, ""))}</p>`);
    i++;
    continue;
  }

  // Plain paragraph (e.g., Summary text)
  flushList();
  const cls = curSection.toLowerCase() === "summary" ? ' class="summary"' : "";
  out.push(`<p${cls}>${inline(line)}</p>`);
  i++;
}
closeJobBlock();

const nameMatch = md.match(/^#\s+(.+)$/m);
const docTitle = esc((nameMatch ? nameMatch[1].trim() + " " : "") + "Resume");

const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>${docTitle}</title>
<style>${css}</style>
</head><body>
${out.join("\n")}
</body></html>`;

fs.writeFileSync(outPath, html);
console.log("wrote " + outPath);
