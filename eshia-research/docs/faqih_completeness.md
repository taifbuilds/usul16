# Man La Yahduruhu al-Faqih website reconciliation

Last boundary reconciliation: 2026-07-24

## Current decision

The Arabic report corpus is **ready for continued rijal work**, but the public
English release is **not yet production-ready**. Report identities, Arabic
boundaries, local-only records, website continuations, duplicate occurrences,
and active isnad preservation now pass the fail-closed boundary gate. Twenty-one
records still lack a complete publishable website translation.

This distinction is deliberate: translation gaps do not prevent chain
tokenization and narrator research, but they continue to block a public-release
claim. The remaining rijal queue includes 798 chain-tokenizer results marked
for review; it is not another hadith-count reconciliation.

## Mashyakha source and proposal layer (2026-08-10, matcher `v2`)

Faqih's abbreviated openings can only be expanded against a separately
preserved Mashyakha witness. The local database stores that witness
independently of the report chain, and proposes — never applies — a virtual
preface for each abbreviated opening it can account for.

**Source side.** 387 entries crawled; **378 parsed**, 5 keyed on a subject
rather than a narrator (`topic_entry`), 4 held for review. 383 distinct target
forms.

**Report side.** 2,907 chains flagged `mursal_opening`:

| | chains | |
|---|---|---|
| exactly one source witness → `proposed` | **1,931** | 66.4% |
| ranked candidates → `needs_review` | 567 | 19.5% |
| no Mashyakha entry exists for the narrator | 409 | 14.1% |

3,564 proposal rows: 1,931 `proposed`, 1,633 `needs_review`.

### Evidence tiers

`match_method` records *why* each proposal exists. Only a tier that leaves
exactly one witness standing is proposed; the rest are ranked candidates.

| tier | openings | what it asserts |
|---|---|---|
| `exact_first_narrator` | 1,248 | the normalised opening equals a target form |
| `canonical_first_narrator` | 354 | equal after removing orthography, not identity |
| `unique_name_extension` | 308 | the opening is the *opening* of exactly one target |
| `ism_nisba_elision` | 27 | ism and nisba both agree; only the patronymic is elided |
| `partial_name_candidate` | 561 | a partial name with more than one reading |

Tiers sum to 2,498 openings with a witness; 1,931 of them are `proposed`. The
gap is 6 openings whose tier is single-candidate but whose narrator has **two**
Mashyakha entries, so they too are `needs_review` — 567 chains in total.

`canonical_first_narrator` removes only what a chain opening carries and a
Mashyakha target never does: a preposition the tokenizer kept (`عن معاوية بن
عمار`), a trailing `بإسناده` or honorific, the bracketed dua the edition prints
after a name (`الكليني- رحمة الله عليه-`), and the kunya's grammatical case —
the Mashyakha always names its target in the genitive after `عن` (`أبي بصير`),
while the report prints whatever case its own sentence needs (`أبو بصير`).
None of that is identity, so stripping it is not a relaxed threshold. It is
applied to **both sides**.

**Three rules deliberately refuse an available answer:**

1. **`ابن X` never auto-resolves.** The form declares that the ism is elided,
   so a target merely *ending* in `بن X` is not evidence it is this Ibn X.
   `ابن محبوب` (62 chains) has exactly one such target — `محمد بن علي بن
   محبوب` — and that is the wrong man; the Ibn Mahbub of the isnads is
   al-Hasan b. Mahbub, who has no entry. Uniqueness inside a 383-form roster
   is not uniqueness in the tradition.
2. **A subject-scoped target is never the sole candidate.** `شعيب بن واقد في
   المناهي` and `الفضل بن شاذان من العلل التي ذكرها` vouch for one subject,
   not for everything the man narrated.
3. **Two witnesses for one narrator stay two.** `كليب الأسدي` (ch117, ch292)
   and `محمد بن حمران` (ch31, ch231) keep both paths visible.

### What is actually left

**567 chains with ranked candidates**, concentrated in 55 partial-name forms
plus 3 two-witness narrators (`كليب الأسدي`, `محمد بن حمران`, `إدريس بن زيد`).
The largest
are genuinely ambiguous single names — `حماد` (68 chains, 6 candidates),
`العلاء` (67, 5), `أبان` (48, 2), `الحلبي` (37, 3) — and patronymic
abbreviations that rule 1 holds back: `ابن أبي عمير` (56), `ابن مسكان` (38),
`ابن فضال` (12). Several of the latter have a single candidate and are decided
by one editorial judgement each.

**409 chains have no Mashyakha entry at all** and never will. Al-Saduq wrote no
entry for `محمد بن الفضيل` (29), `موسى بن بكر` (18), `يونس بن عبد الرحمن` (13),
`القاسم بن محمد الجوهري` (11) or `عثمان بن عيسى` (7); each appears in the
Mashyakha only *inside* someone else's path. This is the honest floor for this
source, not a matcher deficit.

A proposal records the opening form, the target form it matched, the tier, the
candidate rank and count, and the witness's chapter and SHA-256. It does
**not** alter `chains`, insert `chain_nodes`, resolve narrator identities, add
a graph edge, or clear the chain's existing review status. Verified after the
run: Faqih still has 9,586 chain nodes and 798 `needs_review` chains, unchanged.

Rebuild this local evidence layer with:

```powershell
.\.venv\Scripts\python.exe -m eshia_research.cli crawl-faqih-mashyakha `
  --output-path scratch_audit\faqih_mashyakha.json
.\.venv\Scripts\python.exe -m eshia_research.cli import-faqih-mashyakha `
  --snapshot-path scratch_audit\faqih_mashyakha.json --apply
.\.venv\Scripts\python.exe -m eshia_research.cli materialize-faqih-mashyakha-expansions --apply
.\.venv\Scripts\python.exe -m eshia_research.cli audit-faqih-mashyakha
```

Take a SQLite backup before either `--apply` command. Both are idempotent and
default to dry-run; the materializer also **deletes** proposals its current
rules no longer make, so a rule change cannot leave orphaned evidence behind.
Rows a human has already ruled `approved` or `rejected` are decisions, not
output, and are never deleted.

## Website inventory

- Thaqalayn website books: `34`, `35`, `36`, and `37`
- Rendered chapter pages: 659
- Rendered content routes: 5,927
- Website rows with no English: 23, including three field-placement anomalies
- Website display anomalies retained in the inventory: 87

The website includes compiler rulings, chapter introductions, supplications,
and guide subdivisions as hadith routes. Ninety-five such routes were reviewed
as non-independent units; they are evidence, not extra narrations.

## Final reconciliation

- Local visible reports: 5,924
- Unique visible public IDs: 5,924
- Arabic-confirmed local reports: 5,829
- Arabic-confirmed website routes: 5,832
- Confirmed relation edges: 5,832
- Reviewed local-edition reports without standalone website routes: 95
- Reviewed website non-independent units: 95
- Missing numbered website reports: 0
- Unclassified local units: 0
- Unclassified website units: 0
- Inventory reconciliation ready: yes
- Arabic boundaries ready for rijal: yes
- Production release ready: no

The opening failures are repaired: reports 9 and 10 are separate records,
compiler material no longer leaks into the displayed Arabic, and incomplete
local boundaries use the rendered website report. The source extraction is
retained in `full_text_raw` as provenance.

The combined source row at report 2119 was split into its numbered report and
its second unnumbered transmitted report, which now has stable ID
`faqih-web-35-3-1-12`. Repeated wording at reports 2296, 2189, 2153, 3402,
and 5765 remains separate because each occurrence has its own source location.
Manual relations and exclusions are bound to local and website Arabic hashes;
the local-only set is additionally locked to its Arabic content evidence.

## Publication gate

- Boundary-blocking records: 0
- Mapped records below 90% website-Arabic coverage: 0
- Non-one-to-one record boundaries: 0
- Unreviewed local-only records: 0
- Approved splits with a detectable source isnad omitted: 0
- Website reports without usable English: 20
- Records without a publishable website translation: 21

The review restored 293 deterministic active isnads that an earlier website
repair had placed inside the matn, manually corrected eleven compiler/heading
overruns, and rebuilt the Faqih chain index. The resulting 3,277 isnad-bearing
rows produce 3,809 chain routes and 8,560 narrator nodes; 804 chains are marked
for parser review and uncertainty handling during rijal work.

## Publication state

- Stored published rendered-website English rows: 5,808
- Website structure rows: 5,904
- Topic assignments: 28,622 across all 5,924 visible reports
- Generated topics: 711, including 67 semantic search topics

English is published only where the website supplies English and the report
relation is safe for publication. Missing website English, partial
continuations, and combined-edition boundaries remain visibly untranslated;
the importer does not invent or misattach text to make the percentage larger.

## Excluded apparatus

Sixteen source rows remain preserved but hidden as proven non-hadith
apparatus: `faqih-1574` and `faqih-5909` through `faqih-5923`. Their status is
`rejected_non_hadith_fragment`; source Arabic and provenance were not deleted.

## Rerun

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m eshia_research.cli audit-thaqalayn-website `
  --corpus faqih `
  --inventory-path scratch_audit\faqih_thaqalayn_website_inventory_20260723.json `
  --audit-path scratch_audit\faqih_thaqalayn_website_audit_20260723.json `
  --markdown-path scratch_audit\faqih_thaqalayn_website_audit_20260723.md `
  --cache-dir scratch_audit\faqih_cache `
  --review-manifest-path data\reconciliation\faqih_thaqalayn_website_20260723.json `
  --reuse-inventory
```

The numbered-gap, structure, English, and topic imports remain separate and
dry-run capable. Take a full database backup before applying any future
reconciliation change.
