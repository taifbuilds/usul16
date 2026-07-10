# -*- coding: utf-8 -*-
"""Refined page-boundary truncation classifier.

For each candidate boundary (page N -> N+1):
  - body(N) = page text before trailing footnote block
  - if the last hadith ending on N runs to the very end of body(N)
    and the head of N+1 is not owned by any hadith -> confirmed truncation
  - if no hadith ends on N but one spans the boundary without owning the
    head -> mid-hadith gap (separate class)
  - else -> prose/TOC/front-matter (ignore)
"""
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

pages = cur.execute(
    "SELECT id, volume_number, page_number, text_raw FROM pages WHERE book_id=? ORDER BY volume_number, page_number",
    (BID,),
).fetchall()
pmap = {(p["volume_number"], p["page_number"]): p for p in pages}

hs = cur.execute(
    "SELECT id, public_id, volume_start, page_start, page_end, sequence_in_book, full_text_raw "
    "FROM hadiths WHERE book_id=? ORDER BY sequence_in_book",
    (BID,),
).fetchall()
h_norm = {h["public_id"]: norm(h["full_text_raw"]) for h in hs}
by_end = defaultdict(list)
spanning = defaultdict(list)
for h in hs:
    by_end[(h["volume_start"], h["page_end"])].append(h)
    for pg in range(h["page_start"], h["page_end"] + 1):
        spanning[(h["volume_start"], pg)].append(h)

AR = "٠-٩۰-۹"
num_marker_start = re.compile(r"^\s*(?:\d{1,4}|[" + AR + r"]{1,4})\s*[-–]")
bab_start = re.compile(r"^\s*\(?\s*(?:باب|كتاب)\b")
first_marker = re.compile(r"(?:^|[.\]\s])(\d{1,4}|[" + AR + r"]{1,4})\s*[-–]\s")
# footnote block line: starts with [n]
footline = re.compile(r"^\s*\[\s*\d+\s*\]")

def body_of(raw):
    """Strip the trailing footnote block: from the first line that starts
    with [n] and after which no non-footnote-ish content resumes."""
    lines = (raw or "").splitlines()
    # walk from the end: find the earliest line index i such that lines[i]
    # starts a footnote and all "starter" lines after it are footnotes too
    idx = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        if footline.match(lines[i] or ""):
            idx = i
        elif (lines[i] or "").strip() and idx == i + 1:
            # non-footnote line directly above a footnote start: stop only
            # if it looks like body (footnote text wraps without markers)
            continue
    # simpler heuristic: first footnote-start line after which no numbered-
    # hadith marker appears
    starts = [i for i, l in enumerate(lines) if footline.match(l or "")]
    for i in starts:
        rest = "\n".join(lines[i:])
        if not first_marker.search(norm(rest)):
            return "\n".join(lines[:i])
    return raw or ""

results = {"truncated_last": [], "midgap": [], "ignored": []}
for (vol, pno), p in sorted(pmap.items()):
    nxt = pmap.get((vol, pno + 1))
    if not nxt or not nxt["text_raw"]:
        continue
    ntxt = norm(nxt["text_raw"])
    if not ntxt or num_marker_start.match(ntxt) or bab_start.match(ntxt):
        continue
    cutm = first_marker.search(ntxt)
    head = ntxt[: cutm.start()].strip() if cutm else ntxt.strip()
    if len(head) < 15:
        continue
    if re.match(r"^\(?\s*(باب|كتاب)", head) and len(head) < 120:
        continue
    probe = head[:60]
    owners = spanning.get((vol, pno), []) + spanning.get((vol, pno + 1), [])
    if any(probe in h_norm[h["public_id"]] for h in owners):
        continue
    # TOC / front-matter / basmala-transition
    if "فهرست" in head[:60] or "رقم الصفحة" in head[:60]:
        results["ignored"].append({"vol": vol, "page": pno, "why": "toc", "head": head[:80]})
        continue
    if head.startswith("بسم الله"):
        results["ignored"].append({"vol": vol, "page": pno, "why": "basmala", "head": head[:80]})
        continue
    last = None
    for h in by_end.get((vol, pno), []):
        if last is None or h["sequence_in_book"] > last["sequence_in_book"]:
            last = h
    body = norm(body_of(p["text_raw"]))
    if last is not None:
        tail = h_norm[last["public_id"]][-50:]
        tpos = body.rfind(tail)
        dist_to_end = len(body) - (tpos + len(tail)) if tpos >= 0 else -1
        if tpos >= 0 and dist_to_end <= 5:
            results["truncated_last"].append({
                "vol": vol, "page": pno, "hadith": last["public_id"],
                "head": head[:200], "head_len": len(head),
            })
            continue
        results["ignored"].append({
            "vol": vol, "page": pno, "why": f"last hadith ends {dist_to_end} chars before body end",
            "hadith": last["public_id"], "head": head[:80],
        })
    else:
        spans = [h for h in spanning.get((vol, pno), []) if h["page_end"] > pno]
        if spans:
            results["midgap"].append({
                "vol": vol, "page": pno,
                "hadith": spans[0]["public_id"], "head": head[:150],
            })
        else:
            results["ignored"].append({"vol": vol, "page": pno, "why": "no hadith on page", "head": head[:80]})

print("confirmed truncated_last:", len(results["truncated_last"]))
print("midgap:", len(results["midgap"]))
print("ignored:", len(results["ignored"]))
with open("scratch_audit/truncation_classified.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
for r in results["truncated_last"]:
    print("TRUNC", r["vol"], r["page"], r["hadith"], "|", r["head"][:70])
print("---- midgap ----")
for r in results["midgap"]:
    print("MID", r["vol"], r["page"], r["hadith"], "|", r["head"][:70])
