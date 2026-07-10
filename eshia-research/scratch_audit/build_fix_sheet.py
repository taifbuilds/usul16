# -*- coding: utf-8 -*-
"""Build the page-boundary fix sheet: for every confirmed truncated hadith,
extract the raw continuation text from the following page(s) and emit a
verification sheet (tail + continuation) plus a machine-readable fix plan.
Nothing is written to the DB here."""
import sqlite3, re, unicodedata, json
from collections import defaultdict

DB = "eshia_research.db"
BID = 1178

def strip_d(s):
    s = unicodedata.normalize("NFC", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.replace("‌", " ").replace("‏", "").replace("﻿", "")

def norm(s):
    return re.sub(r"\s+", " ", strip_d(s)).strip()

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

with open("scratch_audit/truncation_classified.json", encoding="utf-8") as f:
    classified = json.load(f)
cands = classified["truncated_last"]
print("candidates:", len(cands))

pages = cur.execute(
    "SELECT id, volume_number, page_number, text_raw FROM pages WHERE book_id=? ORDER BY volume_number, page_number",
    (BID,),
).fetchall()
pmap = {(p["volume_number"], p["page_number"]): p for p in pages}

AR = "٠-٩۰-۹"
num_line = re.compile(r"^\s*(?:\d{1,4}|[" + AR + r"]{1,4})\s*[-–]")
foot_line = re.compile(r"^\s*\[\s*\d+\s*\]")

def is_heading(line):
    bare = norm(line)
    return bool(re.match(r"^\(?\s*(?:باب|كتاب|بسم الله)\b", bare))

def extract_continuation(vol, start_page):
    """Return (raw_continuation, end_page, end_page_id, stopped_reason)."""
    parts = []
    pno = start_page
    for _ in range(4):  # at most 4 extra pages
        p = pmap.get((vol, pno))
        if p is None or not p["text_raw"]:
            return None, None, None, f"page {pno} missing"
        lines = p["text_raw"].splitlines()
        stop = None
        reason = None
        for i, l in enumerate(lines):
            if num_line.match(l):
                stop, reason = i, "num"
                break
            if is_heading(l):
                stop, reason = i, "heading"
                break
            if foot_line.match(l):
                # footnote block start: everything from here down must be footnotes
                stop, reason = i, "footnotes"
                break
        if stop is not None:
            parts.append("\n".join(lines[:stop]))
            return "\n".join(parts).strip(), pno, p["id"], reason
        parts.append(p["text_raw"])
        pno += 1
    return None, None, None, "ran past 4 pages"

hmap = {}
plan = []
sheet = []
for c in cands:
    h = cur.execute(
        "SELECT h.id, h.public_id, h.volume_start, h.page_start, h.page_end, h.full_text_raw, h.isnad_raw, h.matn_raw, "
        "r.review_status, r.reviewer FROM hadiths h LEFT JOIN hadith_split_reviews r ON r.hadith_id=h.id WHERE h.public_id=?",
        (c["hadith"],),
    ).fetchone()
    cont, endp, endpid, reason = extract_continuation(c["vol"], c["page"] + 1)
    entry = {
        "public_id": c["hadith"],
        "vol": c["vol"],
        "page": c["page"],
        "existing_review": h["review_status"],
        "reviewer": h["reviewer"],
        "stop_reason": reason,
        "cont_end_page": endp,
        "cont_end_page_id": endpid,
        "continuation_raw": cont,
    }
    ok = cont is not None
    if ok:
        # cross-check: classifier head should be prefix of normalized continuation
        nc = norm(cont)
        if not nc.startswith(norm(c["head"])[:40]):
            entry["mismatch"] = True
            ok = False
        terminal = nc.endswith(".") or nc.endswith("»") or re.search(r"\[\s*\d+\s*\]\.?$", nc)
        entry["terminal_ok"] = bool(terminal)
    entry["extract_ok"] = ok
    plan.append(entry)
    tail = norm(h["full_text_raw"])[-110:]
    headn = norm(cont)[:110] if cont else "(EXTRACT FAILED: %s)" % reason
    tailc = norm(cont)[-60:] if cont else ""
    sheet.append(
        f"### {c['hadith']} v{c['vol']} p{c['page']}->{endp} rev={h['review_status']} stop={reason} term={entry.get('terminal_ok')}\n"
        f"TAIL : …{tail}\n"
        f"CONT : {headn}…\n"
        f"CEND : …{tailc}\n"
    )

with open("scratch_audit/fix_plan.json", "w", encoding="utf-8") as f:
    json.dump(plan, f, ensure_ascii=False, indent=1)
with open("scratch_audit/verify_sheet.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(sheet))

n_ok = sum(1 for e in plan if e["extract_ok"])
n_rev = sum(1 for e in plan if e["existing_review"])
n_noterm = sum(1 for e in plan if e["extract_ok"] and not e.get("terminal_ok"))
print("extract ok:", n_ok, "| with existing review:", n_rev, "| non-terminal ending:", n_noterm)
for e in plan:
    if not e["extract_ok"] or e["existing_review"]:
        print("ATTN:", e["public_id"], "review=", e["existing_review"], "reason=", e["stop_reason"], "mismatch=", e.get("mismatch"))
