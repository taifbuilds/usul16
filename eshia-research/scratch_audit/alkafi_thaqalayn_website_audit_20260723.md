# Al-Kafi website completeness audit

Audited: `2026-07-23T12:13:10.266886+00:00`
Website witness: `https://thaqalayn.net`
Inventory SHA-256: `7f33cfd47db26b7f26fbb07d162bc1655268b509da39efe3ebff5a19ffb75aee`

## Result

- Local visible report units: **15,336**
- Thaqalayn website reports: **14,249**
- Local reports confirmed against website Arabic: **13,568**
- Website reports confirmed against local Arabic: **13,564**
- Unaccounted local reports: **1,768**
- Unaccounted website reports: **685**
- Candidate split/merge review blocks: **504**
- Completeness claim ready: **NO**

The two editions do not need equal row counts. The claim gate is zero
unaccounted reports in both directions after split/merge review.

## Website inventory

- Chapter pages: **2,722**
- Hadith sitemap routes: **14,250**
- Rendered reports: **14,249**
- Non-report placeholders: **1**
- Website display anomalies: **4**

Every Al-Kafi route in the website sitemap was found in the rendered
chapter inventory. Placeholder and anomaly details are retained in JSON.

## Review queue

- Bounded candidate blocks: **504**
- Candidate local units: **595**
- Candidate website reports: **598**
- Local units outside candidates: **1,173**
- Website reports outside candidates: **87**

## Method

Rendered Thaqalayn chapter pages are the source witness. Existing API-derived
structure mappings and translation URLs are treated only as candidate links;
each accepted relation is reverified against Arabic rendered on the website.
No database row is changed by this audit.
