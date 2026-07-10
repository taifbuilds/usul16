# -*- coding: utf-8 -*-
"""Book-wide scan for page-boundary truncation in Al-Kafi.

For each consecutive page pair (N, N+1) in the same volume, if page N+1
starts with body text before the first numbered-hadith marker, some hadith
must own that head text. If no hadith's full_text contains it, the last
hadith ending on page N is a truncation candidate.
"""
import sqlite3, re, unicodedata, json, sys

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
print("pages:", len(pages))

hs = cur.execute(
    "SELECT id, public_id, volume_start, volume_end, page_start, page_end, sequence_in_book, full_text_raw "
    "FROM hadiths WHERE book_id=? ORDER BY sequence_in_book",
    (BID,),
).fetchall()
h_norm = {h["public_id"]: norm(h["full_text_raw"]) for h in hs}

# index hadiths by (vol, page_end) and page ranges
from collections import defaultdict
by_end = defaultdict(list)
spanning = defaultdict(list)  # (vol, page) -> hadiths covering that page
for h in hs:
    by_end[(h["volume_start"], h["page_end"])].append(h)
    for pg in range(h["page_start"], h["page_end"] + 1):
        spanning[(h["volume_start"], pg)].append(h)

ARABIC_DIGITS = "٠-٩۰-۹"
num_marker_start = re.compile(r"^\s*(?:\d{1,4}|[" + ARABIC_DIGITS + r"]{1,4})\s*[-–]")
bab_start = re.compile(r"^\s*\(?\s*(?:باب|كتاب)\b")
first_marker = re.compile(r"(?:^|[.\]\s])(\d{1,4}|[" + ARABIC_DIGITS + r"]{1,4})\s*[-–]\s")

candidates = []
for (vol, pno), p in sorted(pmap.items()):
    nxt = pmap.get((vol, pno + 1))
    if not nxt or not nxt["text_raw"]:
        continue
    ntxt = norm(nxt["text_raw"])
    if not ntxt:
        continue
    if num_marker_start.match(ntxt):
        continue
    if bab_start.match(ntxt):
        continue
    cutm = first_marker.search(ntxt)
    head = ntxt[: cutm.start()].strip() if cutm else ntxt[:400].strip()
    if len(head) < 15:
        continue
    # pure chapter-heading head
    if re.match(r"^\(?\s*(باب|كتاب)", head) and len(head) < 120:
        continue
    probe = head[:60]
    owners = spanning.get((vol, pno), []) + spanning.get((vol, pno + 1), [])
    owned = any(probe in h_norm[h["public_id"]] for h in owners)
    if owned:
        continue
    # fall back: search all hadiths in the volume (maybe page ranges are off)
    owned_any = any(
        probe in h_norm[h["public_id"]]
        for h in hs
        if h["volume_start"] == vol and abs(h["page_start"] - pno) < 6
    )
    last = None
    for h in by_end.get((vol, pno), []):
        if last is None or h["sequence_in_book"] > last["sequence_in_book"]:
            last = h
    candidates.append(
        {
            "vol": vol,
            "page": pno,
            "next_page": pno + 1,
            "last_hadith": last["public_id"] if last else None,
            "owned_nearby": owned_any,
            "head": head[:200],
        }
    )

print("candidates:", len(candidates))
with open("scratch_audit/truncation_candidates.json", "w", encoding="utf-8") as f:
    json.dump(candidates, f, ensure_ascii=False, indent=1)
for c in candidates:
    print(c["vol"], c["page"], c["last_hadith"], "own_nearby=", c["owned_nearby"], "|", c["head"][:80])
