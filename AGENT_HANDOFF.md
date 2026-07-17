# Agent Handoff

Shared working note for Codex and Claude. Read this before making project changes, then update it when you change the plan, database, scripts, or UI behavior.

## Update Protocol

- Keep this file concise. Add only durable status, decisions, and next steps.
- Before DB edits, record the intended scope and backup filename.
- After DB edits, record what changed, counts if available, and any caveats.
- Do not mark a corpus/book "clean" unless suspicious cases were audited and chain indexes were rebuilt afterward.
- If you discover a bad assumption, update this file so the other agent does not repeat it.

## Current Strategy

Primary focus is now Al-Kafi only.

Goal: make Al-Kafi a gold-standard pilot before expanding to the rest of the Four Books and Bihar.

Core product model:

- Raw Page View: exact printed page structure, page navigation, source verification, footnotes as printed.
- Hadith View: kitab -> bab -> complete hadith cards, one stable hadith ID per real hadith, full text across page breaks, clean isnad/matn split.
- Page numbers are provenance, not the main reading unit.

Narrator-clicking depends on this order:

1. Clean Al-Kafi hadith boundaries.
2. Clean Al-Kafi isnad_raw and matn_raw.
3. Rebuild Al-Kafi chains/chain_nodes.
4. Rerun narrator resolver for Al-Kafi.
5. Build clickable isnads and narrator profile UI.

## Main Database

Main DB:

`C:\Users\taifh\Downloads\Shia Hadith Project\eshia-research\eshia_research.db`

Useful source_book_id values:

- Al-Kafi: `11005`
- Tahdhib al-Ahkam: `10083`
- Al-Istibsar: `11002`
- Man La Yahduruhu al-Faqih: `11021`
- Bihar al-Anwar: `71860`
- Mujam Rijal al-Hadith: `14036`

## Current Al-Kafi State

Last checked by Codex on 2026-07-07:

- Al-Kafi rows: 15,355
- Non-rejected rows shown in Hadith View: 15,332
- Rejected non-hadith/commentary fragments hidden from Hadith View: 23
- Split reviews: 1,179 reviewed; 1,156 approved; 0 needs_review; 23 rejected
- Web-facing suspicious unreviewed rows: 0
- Remaining `missing_isnad`: 2 approved source-less liturgical rows (`alkafi-8098`, `alkafi-8124`), not parser failures
- Chain index rebuilt after approved-review sync:
  - 15,330 isnads tokenized
  - 17,184 chains
  - 87,747 chain nodes
  - 1,070 chains need tokenizer review; 93.8% clean

Important: many of the 14k unreviewed rows are likely fine. Do not assume unreviewed means bad. The next step is targeted spot-checking plus rerunning narrator resolution on the rebuilt Al-Kafi chains, not another broad split pass.

Recent Al-Kafi split work:

- Page-boundary continuation fixes: 273 real fixes, 6 false positives inspected
- Very-short matn audit: completed
- Missing-isnad high-confidence pass: 222 rows fixed
- Remaining 38 missing-isnad rows manually handled:
  - 18 real abbreviated/source-marker splits
  - 2 approved as source-less liturgical rows
  - 10 pure commentary/gloss fragments rejected
  - 9 continuation rows merged into previous real hadiths
  - `alkafi-15262`/`alkafi-15263` chopped-chain pair repaired
- Approved split reviews synced back into `hadiths` before rebuilding chains: 335 older rows updated

Codex update on 2026-07-07:

- Added shared split audit module: `eshia-research/src/eshia_research/hadith_split_audit.py`
- Added CLI command: `audit-hadith-splits`
- Updated split-review API to use active approved splits when computing suspicion flags.
- Approved split saves now copy approved `isnad_raw`/`matn_raw` back into `hadiths` so future chain rebuilds can use them.
- Reader routes now hide `rejected_non_hadith_fragment` rows from normal hadith/page/chapter views.
- Chain index rebuild now skips `rejected_non_hadith_fragment` rows.
- Manual remaining-row repair script for audit trail: `eshia-research/scratch_audit/apply_alkafi_remaining38_manual.py`
- Tightened `short_isnad_then_chainy_matn`; it no longer flags ordinary matn phrases like "سألته عن..." or embedded quoted reports. It now targets matn that actually starts like a leaked chain.
- Full tests passed after current changes: `175 passed`.

Latest audit commands/results:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m eshia_research.cli audit-hadith-splits --source-book-id 11005 --no-chain-index
```

Result:

- flagged_hadiths: 110
- suspicious_unreviewed: 0
- no unreviewed suspicious buckets remain

With chain-index checks:

```powershell
.\.venv\Scripts\python.exe -m eshia_research.cli audit-hadith-splits --source-book-id 11005 --include-chain-index
```

Result:

- flagged_hadiths: 110
- suspicious_unreviewed: 0
- `missing_isnad`: 2 approved source-less rows
- all remaining split flags are approved/rejected only

Planned DB edit recorded by Codex on 2026-07-07 before applying:

- Scope: Al-Kafi `missing_isnad` high-confidence repairs only.
- Command: `repair-missing-isnad-splits --source-book-id 11005 --apply`
- Dry-run result: 260 rows seen, 222 proposed, 38 skipped.
- Backup target before apply: `eshia-research/eshia_research.before-missing-isnad-highconf.20260707.db`

Planned DB edit recorded by Codex on 2026-07-07 before applying:

- Scope: Al-Kafi remaining 38 `missing_isnad` rows plus directly adjacent chopped fragments that are visibly part of those same page-break/commentary errors.
- Intended actions: approve genuine explicit/source-less rows, split abbreviated report openings, merge chopped continuation text into the previous real hadith where the previous row is incomplete, and reject pure commentary/gloss fragments from Hadith View.
- Backup target before apply: `eshia-research/eshia_research.before-alkafi-remaining38-manual.20260707-190545.db`

Planned DB edit recorded by Codex on 2026-07-07 before applying:

- Scope: sync approved Al-Kafi split reviews back into `hadiths.isnad_raw` / `hadiths.matn_raw` before the final chain rebuild.
- Reason: chain-aware audit still showed `chain_raw_mismatch` for older approved rows because those reviews predated the API change that copies approved splits into `hadiths`.
- Backup target before apply: `eshia-research/eshia_research.before-approved-split-sync.20260707-191133.db`

Applied by Codex on 2026-07-07:

- Manual remaining-row script applied successfully.
- Approved-review sync applied successfully: 335 `hadiths` rows updated from approved reviews.
- Al-Kafi chain index rebuilt after sync.
- Chain-aware split audit now has `suspicious_unreviewed=0`.

Planned DB edit recorded by Codex on 2026-07-07 before applying:

- Scope: rerun Al-Kafi narrator resolver against the rebuilt Al-Kafi chain nodes.
- Intended action: refresh derived `chain_node_candidates` and `chain_nodes` resolution fields only; no source hadith text edits.
- Backup target before apply: `eshia-research/eshia_research.before-alkafi-resolver-refresh.20260707-191658.db`

Applied by Codex on 2026-07-07:

- Al-Kafi narrator resolver rerun successfully after the chain rebuild.
- Named nodes: 39,874/68,745 resolved (58.0%); 22,846 ambiguous; 6,025 unresolved.
- Candidate rows stored: 150,838 for 62,720 nodes.
- Pronoun/relation nodes: 4,781/6,149 resolved; 375 ambiguous; 993 unresolved.
- Current Al-Kafi chain-node statuses after resolver: 44,655 resolved; 23,221 ambiguous; 7,018 unresolved across 87,747 nodes.

Planned DB edit recorded by Codex on 2026-07-07 before applying:

- Scope: final spot-check one-row correction for `alkafi-7954`.
- Reason: final `very_short_matn` review found the matn phrase `أن من المذخور الإتمام` incorrectly stored at the end of `isnad_raw`, leaving only `في الحرمين` as matn.
- Backup target before apply: `eshia-research/eshia_research.before-alkafi-final-spotcheck-7954.20260707-192805.db`

Applied by Codex on 2026-07-07:

- Final spot-check covered the remaining approved warning buckets:
  - `very_short_matn`
  - `terminal_speech_inside_matn`
  - `matn_starts_like_chain`
  - `short_isnad_then_chainy_matn`
  - approved `missing_isnad`
  - rejected continuation/commentary fragments
- Found and fixed one real issue: `alkafi-7954`.
  - Correct isnad now ends at `يونس عن معاوية بن عمار عن أبي عبد الله ع`.
  - Correct matn now starts `أن من المذخور الإتمام في الحرمين`.
- Verified rejected continuation rows preserve their hadith text in target rows before being hidden.
- Rebuilt Al-Kafi chain index and reran Al-Kafi narrator resolver after the fix.
- Final chain-aware split audit:
  - `flagged_hadiths=109`
  - `suspicious_unreviewed=0`
  - `very_short_matn=41`, all approved
  - `missing_isnad=2`, both approved source-less liturgical rows

Codex final UI/API spot-check on 2026-07-07:

- Frontend UTF-8/mojibake scan: clean across `web/src`.
- `npm run lint`: passed.
- `npm run build`: passed.
- The backend API process on port 8000 was stale and briefly reported the old noisy `short_isnad_then_chainy_matn=2512` backlog. Restarted Uvicorn from `eshia-research/.venv` with current code; live audit now matches CLI:
  - `total_hadiths=15355`
  - `reviewed=1179`
  - `approved=1156`
  - `rejected=23`
  - `suspicious_unreviewed=0`
  - `flagged_hadiths=109`
- Route checks passed with no mojibake:
  - `http://127.0.0.1:3000/read/1178/1/10`
  - `http://127.0.0.1:3000/read/1178/bab/1`
  - `http://127.0.0.1:3000/hadith/alkafi-1`
  - `http://127.0.0.1:3000/review/splits?source_book_id=11005&limit=30`
- First Al-Kafi hadith is correct in the live API: `alkafi-1` isnad ends at the Imam/report boundary, and matn starts `لَمَّا خَلَقَ اللَّهُ الْعَقْلَ`.
- Page-spanning behavior checked: `alkafi-2` appears on both printed pages 10 and 11 but keeps one stable hadith ID.
- Known rejected fragments tested as hidden from public hadith routes: `alkafi-8190`, `alkafi-14844`, `alkafi-15187` return 404.
- DB invariants checked:
  - Visible Al-Kafi hadith cards: 15,332
  - Rejected hidden fragments: 23
  - Visible rows missing matn: 0
  - Visible rows with isnad but no chain index row: 0
  - Visible missing isnad: 2 approved source-less ziyara/dua rows
  - Visible page-spanning hadiths: 2,487

Known rejected fragments:

- `alkafi-8190`
- `alkafi-14844`
- `alkafi-15187`

## Current Rijal State

Mujam crawl/parser/resolver work exists and is populated.

Last checked by Codex on 2026-07-07:

- Mujam pages: 11,095 across 24 vols
- Rijal entries: 15,593
- Narrators: 15,593
- Narrator aliases: 588
- Rijal statements: 12,012
- Rijal occurrences: 53,745
- Chains indexed across major books: 88,291
- Chain nodes: 401,951
- Chain node candidates: 449,228
- Resolver version: `resolver_v1`

Al-Kafi chains and narrator-resolution rows were refreshed after the latest split repairs on 2026-07-07. The resolver is current for Al-Kafi, but ambiguity remains expected and should be shown in the UI rather than hidden.

Relevant files:

- `eshia-research/src/eshia_research/isnad/tokenizer.py`
- `eshia-research/src/eshia_research/isnad/indexer.py`
- `eshia-research/src/eshia_research/rijal/mujam_parser.py`
- `eshia-research/src/eshia_research/rijal/indexer.py`
- `eshia-research/src/eshia_research/rijal/resolver.py`

## Tamyiz Engine (Person-Identity Resolution) — Approved Design

Approved by the user on 2026-07-08. Full design in Claude plan file
`C:\Users\taifh\.claude\plans\tkae-a-look-at-mutable-metcalfe.md`. Summary for all agents:

Problem this fixes (verified 2026-07-08): current `resolved` status means "token matched a
Mu'jam ENTRY", not "we know the PERSON". Concrete failures:

- Bare «أحمد بن محمد» (3,568 Al-Kafi nodes) resolves to al-Khoei's bare-form entry (narrator 780),
  silently merging Ibn Isa and al-Barqi; the full form «أحمد بن محمد بن عيسى» (903 nodes) resolves
  to a different narrator ID. Same man, split identities; different men, merged identity.
- «ابن محبوب» (1,118 nodes) and «الحسن بن محبوب» are two narrator profiles for one person.
- «عدة من أصحابنا منهم محمد بن يحيى العطار» is one opaque collective node; the named member
  gets no identity (11 such nodes; 3,738 plain عدة nodes have documented rosters, unused).
- «عن أبيه» resolution exists only as 2 hardcoded overrides in `rijal/resolver.py` (RELATION_OVERRIDES).

Core model: three distinct objects — chain-node MENTION, Mu'jam ENTRY (evidence document),
PERSON (new first-class historical individual). `chain_nodes.canonical_narrator_id` keeps meaning
"entry citation"; person identity is a separate new claim with its own evidence.

Layers / phases (each independently shippable; rebuild chains + audit + update this file after each):

- Phase A (Layers 0-1) — person ontology + name grammar. New tables: `persons`,
  `person_entry_links` (typed: is_subject / bare_form_evidence / tamyiz_discussion),
  `person_surface_forms` (generated nasab truncations, kunya, ibn-form, nisba-form, each with
  derivation + shared-count so bare forms are ambiguous BY CONSTRUCTION), `person_relations`
  (father/brother/etc from parsed nasab + Mu'jam), `collective_rosters`, `mention_resolutions`.
  Parse al-Khoei's own cross-references in entry text («هو فلان», «متحد مع», «مشترك بين») as
  identity evidence. 14 Ma'sumin get fixed person records (kunya forms; أبو جعفر ع is Baqir OR
  Jawad — ambiguity kept until tabaqa layer). New module `rijal/name_grammar.py`.
- Phase B (Layer 2) — reference calculus: generalized أبيه/جده/أخيه (the nasab of the previous
  mention names the father: for فلان بن X the father IS X; only WHICH X needs lookup; mint
  latent persons when rijal books lack him), عنه anaphora formalized, بهذا الإسناد copy,
  Kafi ta'liq splice detection (flagged, never silent), 'iddah roster expansion keyed by next
  resolved person (Najashi rosters; via_collective attribution, distinct from direct transmission).
- Phase C (Layer 3) — tabaqat lattice: generation intervals per person via constraint propagation
  over confident edges; anchors = Imams' dates + death notes + the 4,117 existing
  `rijal_statements` rows with statement_type='tabaqah_membership' (currently unused).
  Tabaqa becomes a hard candidate filter and disambiguates أبو جعفر ع.
- Phase D (Layer 4) — global collective resolution: bootstrap edge statistics from unique
  full-nasab resolutions, iterate (hard EM) so ambiguous mentions are resolved against
  neighbors, ALWAYS emitting a structured dalil (evidence dossier: Mu'jam citations, rosters,
  tabaqa arithmetic, co-occurrence counts) stored in evidence_json and rendered in the UI.
  Low-margin mentions STAY ambiguous with ranked candidates — never force winners.
- Phase E (Layer 5) — criticism layer: tashif detection (rasm-skeleton near-twins like
  الحسن/الحسين on chronologically implausible singleton edges) and saqt/dropped-link detection.
  Annotations only, never text edits. Review queue reusing the split-review pattern.

Acceptance test: `alkafi-1` — 'iddah shows Najashi roster with محمد بن يحيى العطار linked;
أحمد بن محمد resolves to Ibn Isa WITH rendered dalil; أبو جعفر ع resolves to al-Baqir via
tabaqa; محمد بن مسلم stays ranked-ambiguous unless context justifies.

Gold-standard eval: al-Khoei's explicit tamyiz rulings (parsed in Phase A) + Boroujerdi's
Tartib Asanid al-Kafi; resolver must agree with the masters where they ruled.

Planned DB edit recorded by Claude on 2026-07-08 before applying:

- Scope: Tamyiz Engine Phase A bootstrap — create and populate NEW tables only
  (`persons`, `person_entry_links`, `person_surface_forms`, `person_relations`,
  `collective_rosters`, `mention_resolutions` schema-only). No existing table is modified.
- Command: `build-person-layer` (new CLI command).
- Code added: `rijal/name_grammar.py`, `rijal/person_builder.py`, models, CLI, 18 new tests
  (`test_name_grammar.py`, `test_person_builder.py`); full suite 198 passed.
- Backup target before apply: `eshia-research/eshia_research.before-person-layer-phaseA.20260708.db`

Applied by Claude on 2026-07-08 (Phase A complete):

- `build-person-layer` run against the main DB. Final counts:
  - persons: 15,607 (15,593 from Mu'jam entries 1:1 + 14 Ma'sumin)
  - bare_form_proxy persons: 1,247 (e.g. «أحمد بن محمد» = person 779, claimed by 141
    fuller-named persons; «ابن محبوب» also a proxy)
  - surface forms: 60,439 with corpus-wide shared_count
    (spot checks: «احمد بن محمد» shared by 186, «ابن محبوب» by 13, «ابو بصیر» by 6,
    «محمد بن مسلم» by 14 — ambiguity now explicit by construction)
  - entry links: 25,823 (15,593 is_subject + 1,418 tamyiz_discussion cross-references
    parsed from al-Khoei's own «متحد مع/اتحاده مع/مشترک بین/تقدم بعنوان/یاتی بعنوان»
    + 8,812 bare_form_evidence)
  - father relations: 11,621 asserted by nasab; 1,696 uniquely matched to a person row
  - collective rosters: 13 'iddah member rows, 7 matched to persons
- Matching contract: two tiers (unique exact canonical title, then unique full-form
  claim incl. kunya/nisba-tailed entries). Non-unique -> related_person_id stays NULL
  with the name kept. This is intentional: e.g. «ابراهیم بن هاشم» is honestly ambiguous
  between أبو إسحاق القمي and العباسي at this layer; Phase B/D context resolves it.
- Bare entries with >40 extenders get kind+count only, no evidence links (hyper-generic names).
- Unmatched roster members (الکمیذانی spelling variants, «محمد بن الحسن» etc.) kept
  name-only; the 'iddah rosters for Barqi/Sahl are seeded at confidence 75 and should be
  verified against the crawled Mu'jam muqaddima text (task for Phase B session).
- Tests: 198 passed (18 new in `test_name_grammar.py` / `test_person_builder.py`).
- No existing tables touched; chain index/resolver output unaffected; API/frontend
  unchanged (person data gets API+UI exposure in Phase D). No server restart needed.

Planned + applied DB edit recorded by Claude on 2026-07-08 (Phase B complete):

- Scope: Tamyiz Engine Phase B — the reference calculus. Populates NEW table
  `mention_resolutions` (person-level identity claims, resolver_version='tamyiz_b1')
  and appends `kind='latent'` person rows for nasab-named fathers with no Mu'jam entry.
  No existing table modified; `chain_nodes.canonical_narrator_id` untouched.
- Command: `resolve-persons --source-book-id 11005` (new CLI command).
- Code added: `rijal/person_resolver.py`, CLI command, 8 new tests (`test_person_resolver.py`);
  also improved `rijal/name_grammar.py` (kunya-before-nasab like «أبو جعفر محمد بن يعقوب»;
  fixed ال-initial isms like «الحسن» no longer mistaken for a nisba). Full suite: 207 passed.
- Backup before apply: `eshia-research/eshia_research.before-person-resolve-phaseB.20260708.db`.
  NOTE: the grammar fix changed surface-form generation, so `build-person-layer` was
  re-run before `resolve-persons` (surface forms 60,739; father matches 1,665). Anyone
  re-running must run build-person-layer FIRST, then resolve-persons.

Applied results (Al-Kafi, 87,747 nodes):

- resolved 27,183 | ambiguous 48,899 (ranked candidates kept) | via_collective 13 |
  unresolved 11,660. 281,307 mention_resolution rows.
- Reference calculus: 111 father/grandfather resolved, 7 latent persons minted,
  25,837 father references shown as ranked-ambiguous real persons (NOT fake latents —
  this was a deliberate fix: minting a latent when real ambiguous persons exist is
  dishonest and forbidden by project principles).
- Resolution rules (all deterministic, every row carries a dalil in evidence_summary/json):
  - surface-form person lookup with a "decisive" rule: resolve only when the best
    derivation tier has ONE winner, or exactly one exact canonical-title match breaks
    the tie. Bare forms (all candidates same tier, no exact title) stay ambiguous.
  - bare_form_proxy persons are never offered as identities — a bare mention surfaces
    its real fuller-named claimants.
  - «عن أبيه»/«عن جده»: documented `person_relations` father edge first, else the
    nasab-asserted father name (unique→resolved, several→ambiguous, none→latent).
  - «عدة/جماعة ... منهم فلان»: members split on waw/comma, greedy longest-matched,
    attributed `via_collective`.
- alkafi-1 ACCEPTANCE (the case the user raised — «عدة من أصحابنا منهم محمد بن يحيى العطار»):
  العطار is now SEGMENTED OUT of the collective and resolved (via_collective); الحسن بن
  محبوب and العلاء بن رزين resolved; bare أحمد بن محمد + محمد بن مسلم stay ranked-ambiguous;
  أبي جعفر ع stays Baqir/Jawad ambiguous. All correct for this phase.

Known Phase-B limitations (all honest, for later phases — do NOT paper over):

- 'iddah ROSTER expansion (keyed by next narrator) fired only 13x because the classic
  next narrator is the BARE «أحمد بن محمد» which is ambiguous, so the roster key doesn't
  uniquely resolve. Deliberately not guessing which 'iddah (Ibn Isa vs Barqi vs Sahl) —
  that is Phase C/D work (tabaqa + context pick the 'iddah, then roster expands).
- anaphora «عنه» resolved 0x: the previous chain's opening is usually itself ambiguous,
  so there's no unique anchor yet. Phase D (ranked-candidate propagation) will handle it.
- Compiler «أبو جعفر محمد بن يعقوب» (al-Kulayni, chain pos 0) stays ambiguous among
  «محمد بن يعقوب بن ...» — needs a compiler-convention prior (Phase D).
- IDDA_ROSTERS for Barqi/Sahl still seeded at confidence 75; verify against the crawled
  Mu'jam muqaddima text.

Planned + applied DB edit recorded by Claude on 2026-07-08 (Phase C complete):

- Scope: Tamyiz Engine Phase C — the tabaqat (generation) lattice. NEW table
  `person_generations`; refinement UPDATES `mention_resolutions` rows (ambiguous->resolved
  for generation-decisive mentions). No source/identity table modified.
- Commands: `build-tabaqat --source-book-id 11005` then `refine-tabaqat --source-book-id 11005`.
- Code added: `rijal/tabaqat.py`, `PersonGeneration` model, 2 CLI commands, 5 new tests
  (`test_tabaqat.py`). Full suite: 212 passed.
- Backup before apply: `eshia-research/eshia_research.before-tabaqat-phaseC.20260708.db`.

How it works (Boroujerdi's method, automated):

- Generation = layer from the Prophet (0). Fixed Imam layers: Prophet 0, Ali 1, Hasan/Husayn 2,
  Sajjad 3, Baqir 4, Sadiq 5, Kazim 6, Rida 7, Jawad 8, Hadi 9, Askari 10, Mahdi 11
  (`MASUM_GENERATIONS` in tabaqat.py).
- Anchors: the 4,117 `tabaqah_membership` statements — a companion of an Imam at layer G is
  placed at layer G+1 (soft +/-1). `imam_generation_from_raw` maps imam_raw keywords in
  specificity order (al-Askari before bare al-Hasan).
- Propagation: confident edges = adjacent RESOLVED person mentions in a chain
  (gen student = gen teacher + 1); intervals relaxed to a fixpoint. Contradictions only
  flag a `conflict` when the edge is corroborated (>=2 chains) — a lone bad edge doesn't
  poison both persons.

Applied results (Al-Kafi):

- person_generations: 5,747 persons constrained (8 fixed-Imam rows shown [others became
  anchor_and_propagated], 4,100 companionship anchors, 1,339 propagated-only); 1,565 pinned
  to a single layer; 328 conflicts flagged (down from 621 before the >=2-support fix).
- `refine-tabaqat`: examined 38,926 ambiguous nodes; DISAMBIGUATED 5,372 imam mentions and
  35 narrators by generation, each rewritten to a single resolved row method=
  'tabaqat_disambiguated' with a dalil.
- Al-Kafi resolved distinct nodes: 27,183 -> 32,582. Imam nodes now 5,591 resolved,
  1,874 still ambiguous, 1,003 unresolved.
- alkafi-1 ACCEPTANCE: pos-6 «أبي جعفر ع» now resolves to AL-BAQIR (layer 4) with dalil
  "Generation 4 fits the chain: expected ~4 from العلاء بن رزين (gen 6, 2 steps away);
  chosen al-Baqir over 1 generation-incompatible candidate [al-Jawad, layer 8]." This is
  exactly the tabaqa reasoning the plan targeted.

Phase C notes / limitations:

- Refinement only fires when ALL candidates of an ambiguous node have a known generation
  (so imams, which are all fixed, benefit most; narrators only when every candidate is
  gen-known). Conservative by design — unknown-generation candidates are never pruned.
- 328 conflict persons have contradictory generation evidence (often a misresolved edge or
  a late-narrating companion). They keep a widened interval; surface them in a review UI later.
- FULL RE-RUN ORDER (grammar/person-layer changes invalidate downstream):
  build-person-layer -> resolve-persons -> build-tabaqat -> refine-tabaqat.

Next session: Phase D (global collective resolver / dalil) — bootstrap edge statistics from
the now-larger resolved set, iterate (hard EM) so ambiguous narrator mentions resolve against
resolved neighbors + Mu'jam mashyakha (`rijal_occurrences`), fold in compiler-convention priors
(pins al-Kulayni at chain pos 0) and 'iddah-roster keying once the next narrator resolves.
Then the UI/API work to surface person-level resolutions + dalils (plan Layer 4, and the
narrator->person page upgrade). See plan file
`C:\Users\taifh\.claude\plans\tkae-a-look-at-mutable-metcalfe.md`.

Codex update on 2026-07-08, Tamyiz API/UI visibility slice:

- Local dev app restarted for live inspection:
  - Frontend: `http://127.0.0.1:3000`
  - Backend: `http://127.0.0.1:8000`
- Extended existing `GET /hadiths/{public_id}/chains` response with per-node
  `person_resolution` from `mention_resolutions` + `persons` + `person_generations`.
  - Old entry-level fields (`narrator`, `candidates`, `canonical_narrator_id`) remain
    unchanged as fallback and citation context.
  - `via_collective` rows now expose the segmented person as `resolved_person`.
- Updated frontend API types and `web/src/components/reader/HadithBody.tsx`:
  - Chain chips prefer Tamyiz person-level status when available.
  - Popovers show resolved person / ranked person candidates / generation tag / dalil.
  - Inline clickable isnad overlay links resolved persons through the existing narrator page
    when the person has a Mu'jam-backed `narrator_id`.
- Live API smoke for `alkafi-1`:
  - `عدة من أصحابنا منهم محمد بن يحيى العطار` surfaces `محمد بن يحيى العطار` as
    `via_collective`, generation 11.
  - `الحسن بن محبوب` and `العلاء بن رزين` are person-resolved.
  - bare `أحمد بن محمد` and `محمد بن مسلم` remain ranked person-ambiguous.
  - `أبي جعفر ع` resolves to al-Baqir, generation 4.
- Verification:
  - Backend tests: `212 passed`
  - Frontend lint: passed
  - Frontend build: passed
- Not done yet:
  - No person-detail page yet; links still reuse narrator pages where possible.
  - Phase D global EM resolver / full 'iddah roster keying still needs optimization
    and application; the narrow compiler-prior slice below is now applied.

Planned DB edit recorded by Codex on 2026-07-08 before applying:

- Scope: Tamyiz Engine Phase D first slice for Al-Kafi only. Resolve chain-opening
  compiler-convention mentions matching `Abu Ja'far Muhammad b. Ya'qub` to the
  existing al-Kulayni person row in `mention_resolutions`; keep existing ranked
  alternatives. No source hadith text, chain nodes, or person ontology rows are edited.
- Command: `refine-compiler-priors --source-book-id 11005`.
- Dry-run result: 5 target nodes, all expected compiler openings:
  `alkafi-1`, `alkafi-212`, `alkafi-427`, `alkafi-3795`, `alkafi-11097`.
- Backup target before apply:
  `eshia-research/eshia_research.before-phaseD-compiler-prior.20260708-155029.db`

Applied by Codex on 2026-07-08:

- Added fast Phase D compiler-prior code:
  - `rijal/collective_resolver.py`: `refine_compiler_priors`, plus idempotent
    al-Kafi compiler-prior replacement that retains ranked alternatives.
  - `cli.py`: `refine-compiler-priors` with `--dry-run`.
  - `tests/test_collective_resolver.py`: direct coverage for the fast slice.
- Applied `refine-compiler-priors --source-book-id 11005` after creating the
  backup above.
- Result: 5 Al-Kafi chain-opening nodes resolved to existing person `15376`
  (`al-Kulayni`) with method `compiler_prior_kulayni` and a rendered dalil:
  `alkafi-1`, `alkafi-212`, `alkafi-427`, `alkafi-3795`, `alkafi-11097`.
  Existing Muhammad b. Ya'qub alternatives are retained as ranked ambiguous
  alternatives where they existed.
- Idempotency check after apply:
  `refine-compiler-priors --source-book-id 11005 --dry-run` examines the same
  5 targets and resolves 0 new rows.
- Live API check: all five target hadiths return `person_resolution.status=resolved`,
  `resolved_person.id=15376`, first candidate method `compiler_prior_kulayni`,
  and `primary_dalil` present.
- Verification: full backend suite passed, `216 passed, 1 warning`.
- Caveat: the broad `refine-collective-context` global/context loop exists but
  is not yet optimized enough for full Al-Kafi application; keep using the fast
  compiler-prior command for this specific Phase D slice.

Planned DB edit recorded by Codex on 2026-07-08 before applying:

- Scope: Tamyiz Engine Phase D broad Al-Kafi context pass. Refine only
  `mention_resolutions` for Al-Kafi chain nodes using already-resolved adjacent
  person edges, Mu'jam occurrence support, generation compatibility, and
  documented 'iddah roster keys. No source hadith text, chain nodes, or person
  ontology rows are edited.
- Code safety fix before apply: `collective_resolver.py` disables SQLAlchemy
  session synchronization for per-node bulk deletes in this Phase D pass; the
  previous broad pass timed out on scratch because the ORM tried to synchronize
  each delete against the large loaded resolution identity map.
- Additional conservative guard: `first_name`/`kunya` context winners require
  edge support >=2 or Mu'jam support; two low-evidence scratch winners now stay
  ambiguous.
- Scratch dry-run result on a copied DB:
  - examined 43,490 ambiguous nodes
  - resolved 3,214 by `collective_context`
  - expanded 48 collective nodes with 168 `collective_roster_after_context` rows
  - skipped 40,276 weak cases
  - runtime roughly 16-19 seconds after the performance fix
- Acceptance spot-check on scratch: `alkafi-1` now has al-Kulayni at position 0,
  expanded 'iddah roster members keyed by Ahmad b. Muhammad b. Isa, bare
  `Ahmad b. Muhammad` resolved to Ahmad b. Muhammad b. Isa with score/margin
  in evidence JSON, and `Muhammad b. Muslim` remains ranked ambiguous.
- Backup target before apply:
  `eshia-research/eshia_research.before-phaseD-context.20260708-171558.db`

Applied by Codex on 2026-07-08:

- Applied `refine-collective-context --source-book-id 11005` to the main DB.
- Result:
  - examined 43,490 ambiguous nodes
  - resolved 3,214 by `collective_context`
  - added 1,364 retained `collective_context_alternative` rows
  - expanded 48 collective nodes with 168 `collective_roster_after_context`
    rows
  - skipped 40,276 weak cases
- Live `alkafi-1` API check after restart:
  - position 0 remains al-Kulayni via `compiler_prior_kulayni`
  - position 1 has the named member plus Phase D 'iddah roster rows
  - bare `Ahmad b. Muhammad` resolves to Ahmad b. Muhammad b. Isa
    (`person_id=901`) with score/margin evidence JSON
  - `Muhammad b. Muslim` remains ambiguous
  - `Abu Ja'far` remains al-Baqir via tabaqat
- Verification after code changes: full backend suite passed, `216 passed, 1 warning`.
- New CLI support: `refine-collective-context --dry-run`.

Planned DB edit recorded by Codex on 2026-07-08 before applying:

- Scope: Tamyiz Engine Phase D second hard-EM/context iteration for Al-Kafi.
  Uses the newly resolved first-pass neighbors and roster rows as additional
  context. Still only edits `mention_resolutions`.
- Dry-run result on main after the first pass:
  - examined 40,276 ambiguous nodes
  - would resolve 982 by `collective_context`
  - would expand 78 collective nodes with 312 roster rows
- Scratch inspection of the second-wave-only nodes:
  - 982 new context nodes
  - derivations: 284 nasab_truncation, 269 first_name, 250 full,
    161 ibn_form, 13 masum_title, 5 kunya
  - top new tokens include `Zurarah`, `Ahmad b. Muhammad b. Isa`,
    `Ahmad b. Muhammad`, `Ibn Muskan`, `Yunus`, `Muhammad b. al-Husayn`,
    and `Muhammad b. Isma'il`; evidence is mostly repeated edges with
    generation/Mu'jam support.
- Backup target before apply:
  `eshia-research/eshia_research.before-phaseD-context-round2.20260708-171947.db`

Applied by Codex on 2026-07-08:

- Applied Phase D context round 2 to the main DB.
- Result:
  - examined 40,276 ambiguous nodes
  - resolved 982 by `collective_context`
  - expanded 78 collective nodes with 312 `collective_roster_after_context`
    rows
  - skipped 39,294 weak cases
- Post-round-2 dry-run showed a smaller third wave:
  - 218 context resolutions
  - 11 collective nodes / 44 roster rows

Planned DB edit recorded by Codex on 2026-07-08 before applying:

- Scope: Tamyiz Engine Phase D third context iteration for Al-Kafi. Still only
  edits `mention_resolutions`.
- Scratch inspection of third-wave-only nodes:
  - 218 new context nodes
  - derivations: 130 full, 64 nasab_truncation, 16 first_name, 8 ibn_form
  - top new tokens: `Muhammad b. Yahya`, `Ahmad b. Muhammad`,
    `Ibn Muskan`, `Muhammad b. al-Husayn`, `Sama'ah`, `Zurarah`
  - strongest repeated pattern: `Muhammad b. Yahya` -> al-Attar from a
    repeated edge to the next narrator (often x106) plus generation fit.
- Backup target before apply:
  `eshia-research/eshia_research.before-phaseD-context-round3.20260708-172201.db`

Applied by Codex on 2026-07-08:

- Applied Phase D context round 3 to the main DB.
- Result:
  - examined 39,294 ambiguous nodes
  - resolved 218 by `collective_context`
  - expanded 11 collective nodes with 44 `collective_roster_after_context`
    rows
  - skipped 39,076 weak cases
- Post-round-3 dry-run showed a very small fourth wave:
  - 47 context resolutions
  - 1 collective node / 4 roster rows

Planned DB edit recorded by Codex on 2026-07-08 before applying:

- Scope: Tamyiz Engine Phase D fourth/convergence context iteration for
  Al-Kafi. Still only edits `mention_resolutions`.
- Scratch inspection of fourth-wave-only nodes:
  - 47 new context nodes
  - 40 full-form, 7 first-name
  - 39 are `Muhammad b. Yahya` -> al-Attar with repeated edge support x224
    plus generation fit
  - 7 are `Yunus` -> Yunus b. Abd al-Rahman with edge x9 plus generation fit
  - 1 is `Ahmad b. Muhammad b. Isa` -> Ahmad b. Muhammad b. Isa al-Ash'ari
- Backup target before apply:
  `eshia-research/eshia_research.before-phaseD-context-round4.20260708-173535.db`

Applied by Codex on 2026-07-08:

- Applied Phase D context round 4 to the main DB.
- Result:
  - examined 39,076 ambiguous nodes
  - resolved 47 by `collective_context`
  - expanded 1 collective node with 4 `collective_roster_after_context` rows
  - skipped 39,029 weak cases
- Post-round-4 dry-run showed only 6 remaining context resolutions and no
  roster rows.

Planned DB edit recorded by Codex on 2026-07-08 before applying:

- Scope: final Phase D context convergence pass for Al-Kafi. Still only edits
  `mention_resolutions`.
- Scratch inspection of final 6 nodes:
  - all are `Muhammad b. 'Isa` -> Muhammad b. 'Isa b. Ubayd
  - evidence: edge support x85 plus generation fit
- Backup target before apply:
  `eshia-research/eshia_research.before-phaseD-context-final.20260708-173751.db`

Applied by Codex on 2026-07-08:

- Applied the final Phase D context convergence pass to the main DB.
- Result:
  - examined 39,029 ambiguous nodes
  - resolved 6 by `collective_context`
  - added no roster rows
  - skipped 39,023 weak cases
- Convergence check:
  `refine-collective-context --source-book-id 11005 --dry-run` now resolves
  0 context nodes and adds 0 roster rows.
- Final Phase D applied totals now present in `mention_resolutions`:
  - `compiler_prior_kulayni`: 5 resolved
  - `compiler_prior_alternative`: 6 ambiguous alternatives
  - `collective_context`: 4,467 resolved
  - `collective_context_alternative`: 1,996 ambiguous alternatives
  - `collective_roster_after_context`: 528 via-collective rows
- Live `alkafi-1` API check:
  - pos 0 `compiler_prior_kulayni` -> person 15376 (al-Kulayni)
  - pos 1 collective has 4 visible person candidates/roster members in the API payload
  - pos 2 `Ahmad b. Muhammad` -> person 901 via `collective_context`
  - pos 5 `Muhammad b. Muslim` still ambiguous with 6 candidates
  - pos 6 remains al-Baqir via `tabaqat_disambiguated`
- Verification:
  - `http://127.0.0.1:3000/hadith/alkafi-1` returns 200
  - `http://127.0.0.1:8000/hadiths/alkafi-1/chains` returns 200
  - full backend suite passed, `216 passed, 1 warning`
- Local backend restarted on `127.0.0.1:8000`.

Codex update on 2026-07-09, person-resolution audit admin view:

- Answer to "is Al-Kafi fully resolved?": no. As of this check, Al-Kafi has
  87,747 visible chain nodes. Rank-1/top person-resolution status:
  - resolved: 37,054
  - via_collective: 5
  - ambiguous: 39,023
  - unresolved: 11,520
  - latent: 8
  - missing rank-1 person-resolution row: 137
  - open nodes total (ambiguous + unresolved + latent + missing rank-1): 50,688
- Added read-only backend audit endpoints:
  - `GET /person-resolution-audit/summary`
  - `GET /person-resolution-audit/queue`
  - Default `source_book_id=11005`; queue supports `status`, `node_type`, `q`,
    `skip`, and `limit`.
  - Status filters: `open`, `ambiguous`, `unresolved`, `latent`,
    `missing_rank1`, `resolved`, `via_collective`, `all`.
  - Queue items include hadith location, chain/node position, token, status,
    method, resolved person when present, candidates, dalil, risk flags,
    isnad excerpt, and matn excerpt.
- Added frontend admin page:
  - `http://127.0.0.1:3000/review/person-resolutions`
  - Shows totals, status links, node-type/method breakdowns, filters, paged
    queue, candidate lists, dalil snippets, and links to hadith/reader/narrator
    pages.
- Files changed:
  - `eshia-research/src/eshia_research/schemas.py`
  - `eshia-research/src/eshia_research/api/routes_books.py`
  - `web/src/lib/api/types.ts`
  - `web/src/lib/api/books.ts`
  - `web/src/app/review/person-resolutions/page.tsx`
- Verification:
  - `GET /person-resolution-audit/summary?source_book_id=11005` returns
    `total_nodes=87747`, `open_nodes=50688`.
  - `GET /person-resolution-audit/queue?source_book_id=11005&status=open&limit=2`
    returns 2 items from a total 50,688.
  - Live page `/review/person-resolutions?source_book_id=11005&status=open&limit=5`
    returns 200 and shows the open count.
  - Frontend lint passed.
  - Frontend build passed.
  - Backend full test suite passed, `216 passed, 1 warning`.
- Local dev servers restarted:
  - Frontend: `127.0.0.1:3000`
  - Backend: `127.0.0.1:8000`

Codex update on 2026-07-09, risky-resolved audit mode:

- Extended `GET /person-resolution-audit/queue` with a `risk` filter for
  inspecting resolved-but-worth-auditing person decisions.
- Supported risk filters:
  - `any`
  - `phase_d_context`
  - `weak_surface`
  - `shared_surface`
  - `low_margin`
  - `many_candidates`
- The backend now adds `phase_d_context` to `risk_flags` for rows whose top
  method is `collective_context`, `compiler_prior_kulayni`, or
  `collective_roster_after_context`.
- Frontend `/review/person-resolutions` now has:
  - a Risk dropdown
  - a one-click `risky resolved` chip
  - chips for each risk class
  - pagination/link preservation of the selected risk filter
- Current live risky-resolved counts:
  - `status=resolved&risk=any`: 4,472 nodes
  - `phase_d_context`: 4,472
  - `weak_surface`: 1,176
  - `shared_surface`: 1,510
  - `low_margin`: 186
  - `many_candidates`: 137
- Live route:
  `http://127.0.0.1:3000/review/person-resolutions?source_book_id=11005&status=resolved&risk=any&limit=5`
  returns 200 and shows `4,472`.
- Verification:
  - Backend full test suite passed, `216 passed, 1 warning`.
  - Frontend lint passed.
  - Frontend build passed.

## Resolution Eval Harness (Baseline) — Claude 2026-07-09

First *measurement* of person-resolution quality (previously every phase closed
with an `alkafi-1` anecdote + green tests, never a score). New read-only module
`eshia-research/src/eshia_research/rijal/eval_resolution.py`; CLI
`eval-resolution --source-book-id 11005` (add `--json` for the full report). 6
new tests in `tests/test_eval_resolution.py`; full suite `222 passed`. No DB
writes — safe to re-run anytime.

It scores four things against independent gold signals:

1. **Coverage** — 87,747 Al-Kafi nodes: resolved 42.2%, ambiguous 44.5%,
   unresolved 13.1%. named_narrator is the weak spot (31,309/68,744 resolved).
2. **Bare-form leak invariant (HARD): 0 leaks — PASS.** No rank-1 `resolved`
   row points at a `bare_form_proxy` person. Good.
3. **Generation monotonicity: 2,051 violations / 18,516 gen-checkable edges
   (~11%)** — edges where the resolver put the teacher in a strictly *later*
   tabaqa than the student (impossible). Gap sizes are mixed (1 layer = soft
   boundary noise; 4-5 layers like حماد بن عيسى gen2 <- ربعي gen7 = a real
   mis-resolution somewhere). Actionable review queue.
4. **Mu'jam edge corroboration (floor): 88.3%** — of confident adjacent person
   edges where al-Khoei's `rijal_occurrences` attest the endpoint well enough to
   judge (5,421 edges), 88.3% are corroborated by his own narrated_by/narrates_from
   lists. This is a FLOOR (exact-normalised-string match, so it under-counts).

**Two concrete findings the eval surfaced (both real, both for a follow-up session):**

- **Split-identity confound in the 636 "contradicted" edges.** Spot-checked the
  famous `محمد بن يحيى العطار -> أحمد بن محمد بن عيسى`: it was flagged
  contradicted only because the resolver picked person **902** (`al-Ash'ari
  al-Qumi`) while al-Khoei's matching gold edge sits on person **901**
  (`al-Ash'ari`, no qumi). Same man, two person rows — the exact "same man, split
  identities" failure the Tamyiz plan named. So some contradictions are
  split-identity artifacts, not resolver errors; the metric is honest about this
  (it doesn't paper over it) but the 636 needs triage before acting.
- **al-Khoei's own identity rulings are captured but never applied.** Phase A
  parsed 1,418 «متحد مع/مشترک بین» cross-references into
  `person_entry_links.tamyiz_discussion`, but `person_relations` contains ONLY
  `father` edges — **zero `same_person_as` rows** (the plan lists that
  relation_kind). So persons like 901/902 are never merged. Materializing
  `same_person_as` from the tamyiz_discussion links (and using it to cluster
  persons + de-confound the eval) is the natural next task this eval justifies.

Codex update on 2026-07-09, same-person identity links from al-Khoei tamyiz:

- Added `eshia-research/src/eshia_research/rijal/identity_links.py`.
  - New CLI: `materialize-same-person-links [--dry-run]`.
  - Reads existing `person_entry_links.tamyiz_discussion` evidence and writes
    non-destructive, auditable `person_relations.same_person_as` rows.
  - Conservative target rules only:
    - skip `mushtarak/shared-between-several` discussions;
    - `ma ba'dahu / man ba'dahu` -> next Mu'jam numbered entry;
    - `ma qablahu / sabiqahu` -> previous Mu'jam numbered entry;
    - exact-name target only inside the immediate identity-target segment, not
      later route/source-note prose.
  - Important: first dry-run/apply exposed an over-broad exact-name matcher
    that could grab names later in `tariq al-shaykh...` prose. Those generated
    rows were deleted, the parser was tightened, and regression coverage was
    added before rebuilding.
- Applied to main DB after backup:
  - Backup: `eshia-research/eshia_research.before-same-person-links.20260709-133858.db`
  - Final applied rows: 1,858 `same_person_as` rows across 932 pairs.
  - Current clusters: 780 total; mostly pairs/triples; largest clusters are
    size 8 and 7; no runaway giant component.
- Eval harness now treats same-person clusters as equivalent for:
  - Mu'jam edge corroboration surface forms / narrator occurrence evidence;
  - generation monotonicity generation intervals.
- Final post-cluster `eval-resolution --source-book-id 11005`:
  - coverage unchanged: 87,747 nodes; resolved 37,054; ambiguous 39,023;
    unresolved 11,520; missing 137; latent 8; via_collective 5.
  - bare-form leaks: 0 PASS.
  - generation monotonicity improved: 1,943 violations / 18,569 gen-checkable
    edges (was 2,051 / 18,516).
  - Mu'jam corroborated edges improved: 5,959 corroborated (was 4,785).
  - Contradicted/judgeable queue changed: 1,360 contradicted, 7,705
    under-documented. This is not a simple regression: clustering made more
    endpoints well-attested and therefore testable instead of set aside. Treat
    the 1,360 as a sharper audit queue, not an accuracy percentage by itself.
- Files changed:
  - `eshia-research/src/eshia_research/rijal/identity_links.py`
  - `eshia-research/src/eshia_research/rijal/eval_resolution.py`
  - `eshia-research/src/eshia_research/cli.py`
  - `eshia-research/tests/test_person_builder.py`
  - `eshia-research/tests/test_eval_resolution.py`
- Verification:
  - Focused tests: `19 passed`.
  - Full backend suite: `226 passed, 1 warning`.
  - Admin audit API still returns `total_nodes=87747`, `open_nodes=50688`.
  - Frontend admin route still returns 200:
    `http://127.0.0.1:3000/review/person-resolutions?source_book_id=11005&status=open&limit=5`

Codex update on 2026-07-09, machine-admin review + external packets:

- User clarified there is no human review team right now. Decision: add a
  conservative machine-admin layer, not fake human approval.
- Added new table/model:
  - `person_resolution_decisions`
  - one decision per `(chain_node_id, reviewer, resolver_version)`
  - separate from `mention_resolutions`; resolver claims remain intact.
  - decision types currently:
    - `approve_current`
    - `needs_external_review`
    - `flag_contradiction`
    - `keep_ambiguous` reserved for later
- Added module:
  - `eshia-research/src/eshia_research/rijal/machine_review.py`
- Added CLI:
  - `machine-review-person-resolutions --source-book-id 11005 [--dry-run]`
  - `export-person-review-packet --source-book-id 11005 --limit 25`
- Machine-review behavior:
  - Approves only low-risk current winners, e.g. strong full-surface/tabaqat/
    father/roster evidence without hard flags.
  - Sends ambiguous, unresolved, low-margin, many-candidate, weak/shared
    surface, and risky Phase-D context cases to external review.
  - Flags hard contradictions such as generation-monotonicity violations and
    bare-form-proxy leaks.
  - Uses cluster-aware generation and Mu'jam occurrence corroboration where
    available, but does not override `mention_resolutions` yet.
- Applied to main DB after backup:
  - Backup: `eshia-research/eshia_research.before-machine-review.20260709-142125.db`
  - Decisions written: 87,747
  - `approve_current`: 28,959
  - `needs_external_review`: 54,910
  - `flag_contradiction`: 3,878
  - Confidence tiers:
    - high: 27,311
    - medium: 6,007
    - low: 50,551
    - blocked: 3,878
- Added backend summary endpoint:
  - `GET /person-resolution-decisions/summary?source_book_id=11005`
  - Live check returns `total_decisions=87747`.
- Frontend `/review/person-resolutions` now shows machine-admin totals:
  - machine decisions
  - machine approved
  - external review
  - contradiction flags
- External-review packet format:
  - Markdown + JSONL, UTF-8, not PDF for now.
  - Reason: predictable, pasteable into another LLM, searchable, and still
    convertible to PDF later.
  - Every case includes:
    - fixed case id
    - review question
    - machine suspicion/current decision
    - full Arabic hadith
    - Arabic isnad
    - target mention and parsed chain table
    - ranked candidate persons with dalil
    - strict response template for outside verifier
- Generated packets:
  - General external-review sample:
    - `eshia-research/scratch_audit/person_review_packet_11005_20260709-142932.md`
    - `eshia-research/scratch_audit/person_review_packet_11005_20260709-142932.jsonl`
  - Contradiction-only sample:
    - `eshia-research/scratch_audit/person_review_packet_11005_20260709-143241.md`
    - `eshia-research/scratch_audit/person_review_packet_11005_20260709-143241.jsonl`
- Operational note:
  - SQLite locked while stale dry-run Python workers were still alive.
  - Stopped stale workers, then applied successfully.
  - Backend restarted on `127.0.0.1:8000`; frontend still on `127.0.0.1:3000`.
- Verification:
  - Full backend suite: `228 passed, 1 warning`.
  - Frontend lint: passed.
  - Frontend build: passed after the UI changes.
  - Live admin page returns 200:
    `http://127.0.0.1:3000/review/person-resolutions?source_book_id=11005&status=open&limit=5`

## Transmission Network Graph ("The Network") — Claude 2026-07-10

Obsidian-style interactive map of the Al-Kafi narrator network, live at
`http://127.0.0.1:3000/graph` (nav: "The Network"). Read-only feature; no DB changes.

Backend:

- `GET /transmission-graph?source_book_id=11005&min_count=3&max_nodes=400`
  (routes_books.py). Aggregates confident (resolved/via_collective, rank-1,
  PERSON_RESOLVER_VERSION) adjacent person edges; weights are DISTINCT-hadith
  counts (same semantics as /narrators/{id}/transmission-edges); rejected
  fragments excluded. **same_person_as clusters are collapsed** via
  `identity_links.same_person_clusters` — the al-Ash'ari 901/902 split renders
  as one node (verified: top edge al-Attar -> Ibn Isa x1918, merged=2).
  ~1.2s on the real DB. Schemas: `TransmissionGraph*` in schemas.py.
- Tests: `tests/test_api_transmission_graph.py` (merge, min_count pruning,
  imam kind + narrator link). Full suite passed when added (242 at the time).

Frontend (`web/src/app/graph/page.tsx` + `web/src/components/graph/TransmissionGraphClient.tsx`):

- Canvas force-directed graph, no new deps; custom physics with velocity
  clamping + non-finite guards (unclamped springs can overflow positions to
  NaN, which used to throw in createRadialGradient and silently kill the rAF
  loop — don't remove those guards).
- Layout is **pre-settled synchronously** (warmupSim) then **fit-to-view**
  (fitCamera) — first paint is a formed, framed constellation. Reset view
  re-fits. Layout toggle re-fits after the morph settles (refitPending).
- Two modes: **Constellation** (free force) and **Ṭabaqāt** (?layout=tabaqat;
  y-banded by generation with hairline rules + "ṭabaqa N" labels; time flows
  down from the Imams to the compilers). Mode read via useSearchParams
  (NOT window.location — that caused a hydration mismatch; page wraps the
  client component in <Suspense>).
- Design (dataviz-skill validated against plate #121c17): Imams gold #c98500
  with glow; narrators on the 5-step blue ordinal ramp by ṭabaqa bucket
  (#cde2fb -> #256abf); undated gray-green #6f7d72. Node size = distinct
  hadiths, edge width/alpha = log(shared hadiths). Ordinal ramp + gold pass
  the palette validator (CVD ΔE 54.3, contrast >= 3:1).
- Interactions: pan/zoom/drag, hover ego-highlight + tooltip, click ->
  detail panel (ṭabaqa, counts, top teachers/students, link to
  /narrators/{id}), search with normalized Arabic matching + fly-to,
  min-shared-hadiths slider (client-side, fetched at min_count=2/500 nodes),
  gold direction chevrons student->teacher on focused edges, table view
  (<details>) as the non-visual path, prefers-reduced-motion settles
  instantly.
- Physics constants note: repulsion/rest tuning changes the equilibrium size;
  fitCamera makes the framing robust to that, so tune freely.
- React lint note: sim mutation lives in module-level functions (tickSim,
  applyWeightFilter, etc.) — `react-hooks/immutability` forbids mutating
  ref-reachable state inside hooks; keep new mutations out there.
- Verification: backend suite green; frontend lint + build green; both modes
  screenshot-verified via headless Edge (headless throttles rAF — that's why
  warmup/fit matter); live API + page return 200. Hover/drag not exercised
  headless — spot-check by hand.

## Transmission Graph v2 — decision-aware + evidence + quality — Claude 2026-07-10

The graph now reflects the review/accuracy layer, not just raw resolver output,
and gained two analysis affordances. Backend suite `270 passed`; frontend lint +
build green.

Answer to "do accuracy updates elsewhere reflect on the graph?" — NOW YES for all
three paths:

- **Resolver re-runs** (resolve-persons -> build-tabaqat -> refine-* ) already flowed
  through (graph reads `mention_resolutions` live).
- **same_person_as merges** already flowed through (cluster collapse per request).
- **Human/admin review decisions** (PersonResolutionDecision, reviewer
  `codex-admin-external-v1`) did NOT — now they do. On the live DB this promoted/
  demoted **3,963** confident nodes on first run (visible in the UI stats line as
  "N review corrections applied").

Keystone: new `eshia-research/src/eshia_research/rijal/effective_resolution.py` — the
single source of truth for a node's *effective* person (rank-1 overlaid with the admin
decision). `apply_admin_decision` semantics: approve_external_override replaces the
person (can PROMOTE an ambiguous node), keep_ambiguous / flag_text_or_chain_issue
DEMOTE, approve_current keeps, unknown types pass through to machine. Used by:
`get_transmission_graph`, `_person_resolution_map` (hadith chain popovers now show
corrections; `NodePersonResolution.effective`), and `_effective_resolution_read`
(audit queue) — so all three read surfaces agree. `routes_books._ADMIN_PERSON_REVIEWER`
now imports `ADMIN_REVIEWER` from the core module.

New/changed endpoints:

- `GET /transmission-graph` — rewired onto `load_confident_nodes` + `adjacent_pairs`;
  new response fields `decisions_applied`, `computed_at`, `quality`; edges gained
  optional `quality` + `gen_violation`. TTL-cached (300s) at the pair-aggregation
  stage keyed by `(book, version, admin-decisions-fingerprint)` so a review
  promotion invalidates immediately. `clear_transmission_graph_cache()` exported —
  **tests MUST call it (autouse fixture)** or the module-level cache leaks a prior
  test's DB across the shared TestClient process.
- `GET /transmission-graph?quality=1` — annotates each surviving edge with the eval
  harness's Mu'jam verdict (corroborated | contradicted | under_documented | no_mujam)
  + `gen_violation`, via new reusable `eval_resolution.score_person_edges` (shares
  `_classify_corroboration` with `evaluate_resolution`; test_eval_resolution unchanged).
- `GET /transmission-graph/edge-evidence?source_person_id=&target_person_id=` — the
  actual shared hadiths behind one edge (distinct-hadith set from the SAME cached
  bundle, so it matches the drawn edge exactly). Node ids are cluster ROOTS; a
  member id returns nothing. Live: al-Attar(11938)->Ibn-Isa(901) = 1,985 hadiths.

Frontend (`web/src/components/graph/TransmissionGraphClient.tsx`,
`web/src/lib/api/{books,types}.ts`, narrator page):

- getTransmissionGraph now `cache:"no-store"` (backend TTL absorbs the cost) so
  corrections/re-runs show immediately; stats line shows "N review corrections
  applied · as of <time>".
- "Evidence quality" toggle (also `?quality=1`): edges tint green=corroborated,
  red(#d03b3b)=contradicted or gen-violation, dashed+dim=under/no-mujam; focus
  highlight always wins; legend rows appear only when on. Merged into live edges via
  module-level `applyEdgeQuality`/`clearEdgeQuality` (NOT a sim rebuild — preserves
  layout; the react-hooks/immutability rule still applies, keep sim mutation
  module-level). `qualityOnRef` feeds the draw loop; **`ctx.setLineDash([])` reset
  after every stroke** or the ṭabaqa rules go dashed.
- Detail-panel teacher/student rows: the count is now an evidence button ->
  `/transmission-graph/edge-evidence` -> a bottom-right list of hadiths linking to
  `/hadith/{public_id}`.
- Deep links `?focus=<personId>` / `?narrator=<narratorId>` fly to + select a node
  once on load (matched against merged_person_ids / narrator_id); narrator profile
  pages now have a "View in the network →" link. `useSearchParams` + `<Suspense>`
  already wired (don't read window.location — hydration).
- Verification: `270 passed` backend; lint+build green; deep-link + detail panel +
  evidence-count buttons + corrections/timestamp screenshot-verified on
  `/graph?narrator=901`. Quality edge-COLORING and the open evidence panel need a
  click / un-throttled rAF — verified by API + 8 new tests, not by headless
  screenshot; spot-check by hand.

New tests: `test_effective_resolution.py` (12), `test_api_edge_evidence.py` (4),
+ decision/quality cases in `test_api_transmission_graph.py`, + override-through-chains
in `test_api_books.py`.

## External-Review-to-Rule Accuracy Sprint — Codex 2026-07-10

Safety baseline completed before resolver work:

- Initialized a local Git repository at the workspace root and committed the
  code-only baseline as `a7386b6`.
- Databases, snapshots, environments, dependencies, logs, and generated review
  packets are excluded from Git.
- Added `scripts/database-backup-retention.ps1`; it is dry-run by default,
  protects the seven newest snapshots, requires a 14-day minimum age, and never
  considers the live database. Initial dry run removed nothing.
- Aligned `pyproject.toml` with the tested/runtime floor of Python 3.11 and
  refreshed stale README/architecture documentation.

Read-only review mining implemented in
`src/eshia_research/rijal/review_priors.py` with CLI command
`validate-review-priors`. Selection contract: deterministic 80/20 split by
`chain_node_id % 5`, minimum 8 training and 3 holdout examples, and >=95%
agreement in both. Eight narrow Al-Kafi rules passed at 100% on both slices.
Full report: `scratch_audit/kafi_review_prior_validation_20260710.md`.

Dry-run result for `refine-compiler-priors --source-book-id 11005 --dry-run`:

- target nodes examined: 25,182
- proposed rank-1 updates: 9,108
- validated review-prior updates: 9,104
- opening-anaphora refreshes: 4
- ranked alternatives retained; no source text or chain-token edits
- backend verification before apply: 281 passed, 1 warning

Planned DB edit recorded by Codex on 2026-07-10 before applying:

- Scope: Al-Kafi derived person-resolution rows only. Apply the eight checked-in
  review priors, rerun Phase-D collective context from the corrected seeds, and
  refresh `codex-machine-v1` decisions. Existing external/admin decisions remain
  separate and are not overwritten. No hadith text, split, chain token, Mu'jam
  entry, person, or same-person relation is edited.
- Commands:
  - `refine-compiler-priors --source-book-id 11005`
  - `refine-collective-context --source-book-id 11005`
  - `machine-review-person-resolutions --source-book-id 11005`
- Backup target before apply:
  `eshia-research/eshia_research.before-review-priors.20260710-231620.db`

Applied by Codex on 2026-07-10:

- Stopped the API writer, copied the 2.032 GiB main database to the recorded
  backup, verified equal length, and ran `PRAGMA quick_check` on the snapshot:
  `ok`.
- Applied the validated prior pass exactly as dry-run predicted:
  - total derived rank-1 updates: 9,108
  - review-prior updates: 9,104
  - opening-anaphora refreshes: 4
  - `abihi` after Ali b. Ibrahim -> Ibrahim b. Hashim: 3,680
  - Ibn Abi Umayr -> Muhammad b. Abi Umayr: 2,535
  - terminal Abu Abd Allah -> Imam al-Sadiq: 1,809
  - parallel-chain opening Ali b. Ibrahim: 578
  - opening Ali b. Muhammad before Sahl: 159
  - Abu Jamila: 133; explicit al-Rida title: 106; Ahmad al-Barqi's father: 104
- Raw confident coverage improved:
  - resolved: 48,552/87,747 (55.3%) -> 57,298/87,747 (65.3%)
  - ambiguous: 27,973 -> 19,495
  - unresolved: 11,072 -> 10,804
  - bare-form leaks remain 0 (PASS)
- A transactional Phase-D collective-context simulation proposed another 2,328
  context resolutions, but worsened the independent contradiction rates. It was
  rolled back and was NOT applied. Do not propagate context again until the
  generation/eval conflicts below are understood.
- Refreshed only `codex-machine-v1` decisions after the validated priors:
  - `approve_current`: 37,844 -> 44,431
  - `needs_external_review`: 45,991 -> 37,215
  - `flag_contradiction`: 3,912 -> 6,101
  - the 10,031 `codex-admin-external-v1` decisions were preserved unchanged
- Important quality caution: broader confident coverage exposes more edges to
  the independent checks. Generation violations are now 3,066/23,501 and the
  exact-match Mu'jam corroboration floor is 64.2% (10,366 corroborated, 5,771
  contradicted). Some flags are known evaluation/tabaqa defects — e.g. the
  historically valid Ibn Abi Umayr -> Jamil b. Darraj edge is flagged because
  their stored generation numbers are inverted. The next accuracy task is to
  repair/validate generation assignments and decompose these flags, not to
  roll back the externally unanimous identity rules.
- Verification after apply:
  - main DB `PRAGMA quick_check`: `ok`
  - backend: 281 passed, 1 warning
  - frontend lint and production build: passed
  - split audit remains 109 reviewed flags / 0 suspicious unreviewed
  - live API, `alkafi-1`, admin review, and quality graph routes return 200
  - backend PID 9080; frontend PID 17316

## Review-Prior Accuracy Sprint Wave 2 — Codex 2026-07-10

User requested a further reduction in the remaining review count. Read-only
queue profiling found repeated exact/contextual cases still marked weak even
where imported review was unanimous. Added ten more Al-Kafi-only priors using
the same deterministic holdout contract; all passed at 100%. Report:
`scratch_audit/kafi_review_prior_validation_wave2_20260710.md`.

Also fixed a machine-review/eval calibration bug: generation rows whose own
method is `conflict` were being used as hard chronology evidence. They are now
excluded from hard generation checks in machine review, eval, and graph quality.
Reliable generation rows are unchanged and still checked. Added regression
coverage across all three read paths.

Pre-apply verification:

- focused tests: 55 passed before full suite expansion
- full backend: 294 passed, 1 warning
- frontend lint and production build: passed
- second-wave prior dry run: 9,579 rank-1/evidence updates
- transactional combined simulation:
  - resolved coverage: 57,298 -> 60,185 (65.3% -> 68.6%)
  - `approve_current`: 44,431 -> 54,090
  - `needs_external_review`: 37,215 -> 32,665
  - `flag_contradiction`: 6,101 -> 992
  - reliable chronology violations: 496/4,244
  - bare-form leaks: 0

Planned DB edit recorded by Codex on 2026-07-10 before applying:

- Scope: Al-Kafi `mention_resolutions` matching the ten checked-in wave-2
  priors or already-validated wave-1 rows whose evidence method needs upgrading,
  followed by a refresh of `codex-machine-v1` decisions under the corrected
  generation calibration. Do not rerun global context. Preserve all 10,031
  external/admin decisions. No source text, split, chain token, person,
  generation, Mu'jam, or same-person row is edited.
- Commands:
  - `refine-compiler-priors --source-book-id 11005`
  - `machine-review-person-resolutions --source-book-id 11005`
- Backup target before apply:
  `eshia-research/eshia_research.before-review-priors-wave2.20260710-235837.db`

Applied by Codex on 2026-07-10:

- Stopped backend PID 9080 and created the recorded 2.032 GiB backup; backup
  `PRAGMA quick_check`: `ok`.
- Applied exactly 9,579 derived updates/revalidations:
  - 9,577 review-prior rows
  - 2 opening-anaphora refreshes
  - highest-volume wave-2 methods: Sahl b. Ziyad 1,375; Zurara 714; Abu Ali
    al-Ashari 657; al-Husayn b. Muhammad 656; al-Husayn b. Said 604;
    Abd Allah b. Sinan 467; bounded Ahmad b. Muhammad context 405; Hariz 378;
    Yunus 284; Muhammad b. Muslim 163
- Refreshed `codex-machine-v1` under the corrected generation calibration:
  - `approve_current`: 44,431 -> 54,092 (+9,661)
  - `needs_external_review`: 37,215 -> 32,663 (-4,552)
  - `flag_contradiction`: 6,101 -> 992 (-5,109)
  - all 10,031 external/admin decisions preserved unchanged
- Final raw resolution state:
  - resolved 60,187/87,747 (68.6%)
  - ambiguous 16,608 (18.9%)
  - unresolved 10,802 (12.3%)
  - bare-form leaks 0
  - reliable generation violations 496/4,245
- Mu'jam exact-match floor after broader coverage: 11,222 corroborated, 7,022
  contradicted, 13,806 under-documented. Treat the contradicted queue as the
  next evidence audit, not as proof that unanimous exact/context priors are bad.
- Final verification:
  - main DB `PRAGMA quick_check`: `ok`
  - backend 294 passed, 1 warning
  - frontend lint/build passed
  - split audit still has 0 suspicious unreviewed
  - API, quality graph, `alkafi-1`, and review UI return 200
  - backend PID 19392; frontend PID 17316

## Generation-Lattice Audit + Reliability Gate + Gated Context Round — Claude 2026-07-11

This sprint executed the "audit the generation lattice" gate the Near-Term Plan
named, then unlocked one accuracy-positive context round behind it. Headline
outcome for Al-Kafi: **resolved 60,187 -> 63,280 (68.6% -> 72.1%)** while the
independent **Mu'jam corroboration rate went UP 61.51% -> 61.73%** and **reliable
generation violations went 496(effective) -> 0**. bare-form leaks stayed 0.
Admin decisions (10,031 `codex-admin-external-v1`) untouched throughout.

### The key finding (why almost nothing needed "fixing")

A new read-only audit (`audit-generations`) classified all 496 chronology
violations: **493 were `suspect_generation`, 0 `suspect_identity`, 3
unclassified.** Only **3** violations sat between two anchor-derived generations,
and all 3 are gap-1 companion-of-two-Imams noise. The other ~493 are PROPAGATION
noise on unanchored hub narrators — above all محمد بن أبي عمير (361 violations)
and معاوية بن عمار (232), who have NO companionship anchor and whose generations
were pinned (and inverted) by pure propagation through same-person cluster
siblings. **The identities were correct; the generation lattice over-trusted
propagation.** So the repair is semantic, not a data purge — no identity was
demoted (0 admin disagreements, and demotion machinery was deliberately not
built because it would act on nothing).

### Code changes (all shipped, full suite 309 passed)

Phase 0/1 — conflict-method generation rows no longer used as hard evidence in
the three paths that still consumed them:
- `rijal/tabaqat.py` `refine_with_tabaqat`: gen_point load excludes `method='conflict'`.
- `rijal/collective_resolver.py` context lookup: same exclusion.
- `api/routes_books.py` graph node-generation read (line ~2103): excludes conflict
  so a self-contradictory person renders UNDATED in the ṭabaqāt layout instead of
  banded at a bogus layer (now matches the quality overlay).

Phase 2 — `rijal/generation_audit.py` (NEW, read-only) + CLI `audit-generations`
(`--output-dir`, `--json`, `--no-write`). Full uncapped export (md + JSONL) of
every violation / conflict-person / Mu'jam-contradicted edge with stable ids
(node_id, person_id, hadith public_id, chain position), each violation
auto-bucketed `suspect_generation | suspect_identity | suspect_text |
unclassified`. Cross-checks: reproduces eval's exact 496/4245. Tests
`tests/test_generation_audit.py` (5).

Phase 3 — the reliability gate (the substantive accuracy fix). New shared
constants in `rijal/eval_resolution.py`: `RELIABLE_GEN_METHODS =
{imam_fixed, ashab_anchor, anchor_and_propagated}` and `GEN_VIOLATION_TOLERANCE
= 1`, plus helper `gen_violation(sg, tg)`. A HARD chronology claim now requires
BOTH endpoints anchor-derived, past a 1-layer soft tolerance. Applied in:
- `eval_resolution`: `_load_generations(reliable_only=...)`; report gained
  `reliable_gen_violations` / `reliable_gen_edges_checked` (the raw
  `gen_violations` is kept for transparency). `score_person_edges` (graph
  quality) now uses reliable-only + tolerance.
- `machine_review._generation_violation`: reliable-only + tolerance.
- `tabaqat.imam_generation_from_raw`: guard so bare «أبي الحسن» (Kazim/Rida/Hadi
  kunya) returns None instead of falling through to «الحسن» -> layer 2 (0 rows
  today; defensive).

Phase 4 — `rijal/collective_resolver.py` hard generation VETO: a candidate whose
anchor-derived interval is >= `GENERATION_VETO_GAP` (3) layers from an
anchor-derived neighbour's expectation is dropped in `_choose_winner`
(`evidence_json["generation_vetoed"]`). Anchor-vs-anchor only, so it never fires
on the unreliable propagated hubs. `ContextLookup.reliable_generation` added.

Phase 5 — review UI can browse by machine decision:
- `GET /person-resolution-audit/queue` gained `machine_decision`
  (`approve_current|needs_external_review|flag_contradiction`), a SQL EXISTS join
  on `codex-machine-v1` decisions. `web/.../review/person-resolutions/page.tsx`
  got a "Machine decision" select (sticky across pagination) + `books.ts`
  `machineDecision` param. Tests: `test_api_books.py` machine_decision filter.

New/changed tests across `test_tabaqat`, `test_eval_resolution`,
`test_api_transmission_graph`, `test_machine_review`, `test_collective_resolver`,
`test_generation_audit`, `test_api_books`. Frontend lint + build green.

### DB writes (each backed up, quick_check ok, admin rows preserved)

1. `machine-review-person-resolutions --source-book-id 11005` under the new
   reliable gate. Backup `eshia_research.before-generation-reliability.20260711-112159.db`.
   `flag_contradiction` 992 -> **0** (all were propagation-noise false flags);
   approve_current 54,092 -> 55,053; needs_external_review -> 32,694. No
   mention_resolutions or person_generations touched, so resolved/corroboration
   identical at this step.
2. `refine-collective-context --source-book-id 11005` ONE round (with the veto).
   Backup `eshia_research.before-phaseD-context-veto.20260711-113145.db`.
   Resolved +3,093 -> 63,280; roster expansion +1,064 rows. Then
   machine-review refreshed: approve_current 55,925 / needs_external_review 31,822.
   IMPORTANT — convergence was tested and REJECTED: rounds 2-3 (+898) had 52%
   marginal corroboration (below corpus) and dropped the rate to 61.39%, so the
   backup was restored and only round 1 (marginal 63.2%, rate 61.73%) was kept.
   **Lesson: convergence is not the objective; stop when marginal corroboration
   falls below the corpus rate. Do NOT re-run context to convergence.**

### Final measured state (Al-Kafi, `eval-resolution`, snapshot in scratch_audit)

- resolved 63,280 / 87,747 (72.1%); ambiguous 13,515; unresolved 10,536;
  via_collective 5; missing 403; latent 8.
- bare-form leaks: 0 (PASS). raw gen_violations 552; **reliable_gen_violations 0**.
- Mu'jam: corroborated 12,975 / contradicted 8,044 / under-documented 15,282;
  **corroboration_rate 61.73%** (up from 61.51%). The 8,044 contradicted is a
  SHARPER AUDIT QUEUE (more edges became testable), not an accuracy drop — the
  rate rose. `machine_decision=flag_contradiction` is empty; browse the
  contradicted queue via the audit JSONL / `needs_external_review` (31,822).
- Graph verified live: quality overlay `gen_violation` edges = 0 (no more
  propagation-noise reds), node generations exclude conflict, admin corrections
  (3,963) still flow through, `alkafi-1` chains 200.
- Snapshots: `scratch_audit/generation_audit_11005_20260711-114424.{md,jsonl}`,
  `scratch_audit/eval_final_generation_sprint_20260711.json`.

### DONE definition for Al-Kafi person resolution (standing)

Every chain node is one of: (a) resolved with a rendered dalil + machine
approve_current or admin approval; (b) ranked-ambiguous with candidates shown;
(c) flagged (machine needs_external_review / admin flag / audit `suspect_text`).
Plateau ~72% resolved is expected — the residual ambiguity (bare «محمد بن مسلم»
etc.) is the honest answer, not backlog. **Do not chase 100%.**

### Residual / next (for a later session, all non-blocking)

- The 3 `suspect_text` violations (ميسر بياع الزطي -> al-Jawad, gap 2) and the
  8,044 Mu'jam-contradicted edges are the Phase E (tashif/saqt) input — annotate
  only, never silent text edits.
- 328 conflict-method persons + the unanchored famous hubs (Ibn Abi Umayr,
  Mu'awiya b. Ammar, Hisham b. al-Hakam) would benefit from real companionship
  anchors sourced from the Mu'jam — NOT hand-fabricated. Their generations stay
  advisory until then. INVESTIGATED 2026-07-11 and deliberately deferred (it is a
  real multi-session research task, not a safe quick win): (a) `rijal_occurrences`
  is too noisy to anchor on — Ibn Abi Umayr has 1 clean «أبي الحسن موسى»
  narrates_from, but Mu'awiya has 0 parsed and Hisham's "occurrences" are whole
  isnad+matn snippets, not names. (b) The clean source is the ENTRY PROSE: the
  text literally states «لقي أبا الحسن موسى ... روى عن الرضا» (Ibn Abi Umayr) and
  «روى عن أبي جعفر و أبي عبد الله و العبد الصالح» (Mu'awiya) — narrates-from an
  Imam at layer G ⇒ person at G+1, the same rule as companionship. But a prose
  extractor needs care: normalization maps «روى»→«روی» (Farsi yeh), the Imam
  honorifics sit in comma-separated teacher LISTS after «روی عن», bare «أبي جعفر»/
  «أبي الحسن»/«أبي محمد» are ambiguous and must be skipped, and precision is hard
  to validate because prose-narration entries barely overlap the ~4,100 Tusi-
  anchored ground-truth set. A WRONG hard anchor on a famous narrator regresses
  accuracy (it can wrongly veto/disambiguate), so this needs its own holdout
  validation contract (cross-check derived layers vs Tusi anchors AND against
  death-date arithmetic) before any apply. Do it as a dedicated session.
- Barqi/Sahl 'iddah roster seeds still at confidence 75 (verify vs muqaddima).
- Boroujerdi Tartib Asanid al-Kafi gold-eval still unbuilt.

## Near-Term Plan

1. Execute Tamyiz Engine phases A-E (above). Phases A-D, same-person links,
   external-review import, decision overlays, the first holdout-validated
   review-to-rule pass, and the generation-lattice audit + reliability gate +
   one gated context round are DONE. The chronology-flag gate is RESOLVED: the
   flags were propagation noise on unanchored hubs, not bad identities; reliable
   violations are now 0. Next unlock is Phase E (tashif/saqt annotation) over the
   `suspect_text` + Mu'jam-contradicted queues, and sourcing real anchors for the
   famous unanchored hub narrators. Do NOT re-run context to convergence.
2. Expand clickable narrator UI from opt-in graph panel into direct isnad-token linking once token-to-text alignment is mature.
3. Improve narrator pages with better grouping of Mu'jam occurrences and links back to hadith appearances.
4. Add targeted Al-Kafi spot-check dashboards for approved warning buckets (`very_short_matn`, `terminal_speech_inside_matn`, etc.).
5. Only after Al-Kafi is solid, apply the learned pipeline to Tahdhib, Istibsar, and Faqih.
6. Treat Bihar as a later source-matching project anchored against the cleaned Four Books.

## Current Clickable Isnad State

Codex update on 2026-07-07:

- Added read-only backend graph endpoint: `GET /hadiths/{public_id}/chains`
  - Returns chains, chain nodes, resolved narrator summary, confidence, resolution method/reason, and top 5 ranked candidates.
  - Rejected non-hadith fragments return 404.
- Added read-only backend narrator endpoint: `GET /narrators/{narrator_id}`
  - Returns narrator identity, aliases, Mu'jam entries, extracted rijal statements, and a capped occurrence-note list with `occurrences_total`.
- Added frontend lazy graph panel inside indexed hadith cards:
  - Original isnad text remains unchanged.
  - `Show narrator chain` loads the graph on demand.
  - Resolved nodes link to `/narrators/{id}`.
  - Ambiguous nodes show ranked possible identities instead of forcing one.
  - Collective/unresolved/relation nodes remain visible but not falsely linked.
- Added narrator profile page: `/narrators/[narratorId]`.
- Real-data smoke test:
  - `GET /hadiths/alkafi-1/chains` returns 1 chain / 7 nodes.
  - `أحمد بن محمد`, `الحسن بن محبوب`, and `العلاء بن رزين` resolve.
  - `محمد بن مسلم` remains ambiguous with two candidates.
  - `أبو جعفر محمد بن يعقوب` remains unresolved and `عدة من أصحابنا` remains collective, as expected.
  - `/narrators/780` serves the Mu'jam profile for `أحمد بن محمد`.
- Verification:
  - Backend tests: `178 passed`
  - Frontend lint: passed
  - Frontend build: passed

Codex update on 2026-07-07, narrator appearances:

- Added resolved-hadith appearance data to narrator profiles.
  - Counts are by distinct hadith, not raw chain-node count.
  - Ambiguous candidate-only matches are not counted as confirmed appearances.
  - Rejected non-hadith fragments are excluded.
- Added paged backend endpoint:
  - `GET /narrators/{narrator_id}/hadith-appearances`
  - Params: `source_book_id`, `skip`, `limit` (max 500).
- `GET /narrators/{narrator_id}` now includes:
  - `appearance_counts`
  - `appearances`
  - `appearances_total`
- Updated `/narrators/[narratorId]` UI:
  - Stats at top.
  - Hadith appearances near the top with links to permalink and reader page.
  - Counts grouped by book.
  - Mu'jam entry collapsed and preview-truncated in UI to avoid giant pages.
  - Transmission notes collapsed.
- Real-data smoke test for `/narrators/780` (`أحمد بن محمد`):
  - Total resolved distinct hadiths: 6,994.
  - Al-Kafi resolved distinct hadiths: 3,299.
  - First Al-Kafi appearances: `alkafi-1`, `alkafi-5`, `alkafi-10`.
  - Live page `http://127.0.0.1:3000/narrators/780` returns 200 and shows hadith appearances.
- Verification after this update:
  - Backend tests: `179 passed`
  - Frontend lint: passed
  - Frontend build: passed

Codex update on 2026-07-07, inline clickable isnad:

- Updated `web/src/components/reader/HadithBody.tsx`.
- The original isnad text still renders immediately as plain Arabic.
- Opening `Show clickable narrator chain` lazy-loads `GET /hadiths/{public_id}/chains`.
- Once chain data is loaded, the visible isnad line upgrades into inline clickable spans where chain-node text alignment succeeds.
  - Resolved nodes link to `/narrators/{id}`.
  - Ambiguous nodes open an inline candidate list.
  - Collective/unresolved nodes are marked but not falsely linked.
- The graph/chip panel remains underneath as a transparent fallback/debug view.
- Current inline alignment is conservative:
  - It uses the first parsed chain as the inline overlay.
  - Multi-route or hard-to-align cases still rely on the graph panel.
  - Footnote markers in the upgraded isnad are preserved visually, while the normal footnote list remains below.
- Live smoke:
  - `http://127.0.0.1:3000/read/1178/1/10` returns 200 and contains `Show clickable narrator chain`.
  - `http://127.0.0.1:3000/hadith/alkafi-1` returns 200 and contains `Show clickable narrator chain`.
- Verification:
  - Backend tests: `179 passed`
  - Frontend lint: passed
  - Frontend build: passed

Codex update on 2026-07-07, narrator appearance browser:

- Added `web/src/components/narrator/NarratorAppearancesClient.tsx`.
- Narrator pages now render the hadith appearance list as an interactive browser:
  - filter by book/source using the grouped counts
  - `Load more` pages through `/narrators/{id}/hadith-appearances`
  - appearance cards still link to both hadith permalink and reader page
- `/narrators/780` live smoke:
  - page returns 200
  - page contains `Hadith appearances`, `Load more`, counts, and `alkafi-1`
  - no mojibake detected
  - API paging check: `/narrators/780/hadith-appearances?source_book_id=11005&skip=120&limit=3` returns total `3299` and next items `alkafi-691`, `alkafi-694`, `alkafi-701`.
- Verification:
  - Frontend lint: passed
  - Frontend build: passed

Codex update on 2026-07-07, narrator transmission graph:

- Added computed adjacent-transmission graph API:
  - `GET /narrators/{narrator_id}/transmission-edges`
  - Params: `source_book_id`, `limit` (max 100), `sample_limit` (max 10).
  - Response has `teachers` and `students`.
  - Counts are distinct hadiths, not raw chain-node rows.
  - Rejected non-hadith fragments are excluded.
- Direction semantics:
  - Chain position `0` is closest to the compiler.
  - `teachers` / "Narrates from" = adjacent resolved node at `position + 1`.
  - `students` / "Narrated by" = adjacent resolved node at `position - 1`.
- Added frontend transmission browser:
  - `web/src/components/narrator/NarratorTransmissionEdgesClient.tsx`
  - `/narrators/[narratorId]` now preloads Al-Kafi scope when present, then allows switching scopes.
  - Relationship cards link to related narrator pages and sample hadiths.
- Real-data smoke test:
  - `GET /narrators/780/transmission-edges?source_book_id=11005&limit=5&sample_limit=3`
  - Returned 5 teacher edges and 5 student edges.
  - Live page `http://127.0.0.1:3000/narrators/780` contains `Transmission graph`, `Narrates from`, and `Narrated by`.
- Verification:
  - Backend tests: `180 passed`
  - Frontend lint: passed
  - Frontend build: passed
- Live backend restarted on `127.0.0.1:8000`, PID `9568`.

## Useful Commands

Codex update on 2026-07-09, external person-review import/admin promotion:

- Local site is running:
  - Frontend: `http://127.0.0.1:3000`, PID `10364`
  - Backend: `http://127.0.0.1:8000`, PID `14404`
- External review result files imported:
  - `C:\Users\taifh\.codex\attachments\b3a8c2dc-1275-4185-af0d-b19449ba64e8\pasted-text.txt`
  - `C:\Users\taifh\.codex\attachments\fbefd25f-b399-466b-a1e3-a44e1892f51b\pasted-text.txt`
- DB backup before import:
  - `eshia-research\eshia_research.before-external-review-import.20260709-174616.db`
- Added durable external-review table/model:
  - `person_resolution_external_reviews`
  - Stores parsed reviewer verdict, confidence, reasoning, source reference, raw case text, matched local person ID, and source label.
- Added importer/promoter:
  - `eshia-research\src\eshia_research\rijal\external_review.py`
  - CLI: `python -m eshia_research.cli import-person-review-results <files...>`
  - CLI: `python -m eshia_research.cli promote-person-review-results --source-book-id 11005`
- Imported external-review result totals:
  - 50 parsed/stored review rows
  - 47 actionable rows matched to local `persons.id`
  - 0 unmatched actionable rows
  - 0 missing chain nodes
  - verdicts: `approve_current=33`, `override_person=14`, `keep_ambiguous=2`, `flag_text_or_chain_issue=1`
  - confidence: `high=48`, `medium=2`
- Promoted those imported rows to separate admin decisions under reviewer `codex-admin-external-v1`.
  - Admin decisions: `approve_current=33`, `approve_external_override=14`, `keep_ambiguous=2`, `flag_text_or_chain_issue=1`
  - Machine decisions under `codex-machine-v1` were not overwritten.
- Important matcher correction:
  - The first import pass briefly matched one `علي بن محمد بن بندار` review to a shorter embedded `محمد بن أبي القاسم عبد الله` person row.
  - The importer was tightened to prefer source-reference Arabic names and unique exact/prefix matches, then re-imported.
  - Current override mapping is now `node605173 => person 8362 علي بن محمد بن بندار`.
- Admin UI update:
  - `/review/person-resolutions` now shows a separate `External admin` summary band.
  - Live smoke: page returned 200 and contains `External admin` and `Approved override`.
- Verification:
  - Backend full suite: `232 passed, 1 warning`
  - Frontend lint: passed
  - Frontend build: passed

Codex update on 2026-07-09, effective-resolution admin view:

- Added effective-resolution fields to the person-resolution audit queue API:
  - `admin_decision`
  - `effective_resolution`
- Added `admin_reviewed=true` filter to:
  - `GET /person-resolution-audit/queue`
  - Example: `http://127.0.0.1:8000/person-resolution-audit/queue?source_book_id=11005&status=all&admin_reviewed=true&limit=3`
- Effective-resolution precedence currently shown in API/UI:
  - admin `approve_current` -> effective `admin approved current`
  - admin `approve_external_override` -> effective `admin override`
  - admin `keep_ambiguous` -> effective `admin kept ambiguous`
  - admin `flag_text_or_chain_issue` -> effective `admin flagged text/chain`
  - otherwise falls back to machine rank-1 result.
- Updated `/review/person-resolutions`:
  - Added `Admin reviewed` checkbox.
  - Added `reviewed nodes 50` quick link.
  - Each returned card now shows an `Effective result` strip with final source/status/person and imported external case/source reference when present.
- Live smoke:
  - `http://127.0.0.1:3000/review/person-resolutions?source_book_id=11005&status=all&admin_reviewed=true&limit=10` returned 200.
  - Page contains `Effective result`, `reviewed nodes`, and `admin override`.
- Backend restarted after code changes:
  - Backend: `127.0.0.1:8000`, PID `30672`
  - Frontend remained live: `127.0.0.1:3000`, PID `10364`
- Verification:
  - Backend full suite: `232 passed, 1 warning`
  - Frontend lint: passed
  - Frontend build: passed

Codex update on 2026-07-09, Al-Kafi source-prior rule pass:

- Goal of this pass:
  - Stop circling around review mechanics and turn the first 50 external reviews into measurable resolver improvement.
- Added narrow Phase D source-opening priors in `eshia-research\src\eshia_research\rijal\collective_resolver.py`:
  - `محمد بن يحيى` at Al-Kafi chain opening -> `محمد بن يحيى أبو جعفر العطار`
  - `علي بن إبراهيم` at Al-Kafi chain opening -> `علي بن إبراهيم بن هاشم`
  - opening `عنه` -> same opening source as previous hadith
  - These priors retain previous ranked candidates as audit alternatives.
- Updated machine reviewer in `eshia-research\src\eshia_research\rijal\machine_review.py`:
  - Treats the new source-prior methods as strong methods.
  - Does not penalize their retained audit alternatives as ordinary `many_candidates`.
- Tests added:
  - `tests\test_collective_resolver.py` covers the three source priors.
  - `tests\test_machine_review.py` covers source-prior approval with retained alternatives.
- Backup before applying:
  - `eshia-research\eshia_research.before-kafi-source-priors.20260709-183514.db`
- Applied commands:
  - `python -m eshia_research.cli refine-compiler-priors --source-book-id 11005`
  - `python -m eshia_research.cli refine-collective-context --source-book-id 11005`
  - `python -m eshia_research.cli machine-review-person-resolutions --source-book-id 11005`
  - Re-imported/promoted the two external review files afterward to relink current machine decisions.
- Resolver impact:
  - Source-prior pass resolved `7,858` Al-Kafi opening nodes:
    - `kafi_opening_ali_ibrahim`: `3,921`
    - `kafi_opening_muhammad_yahya`: `3,489`
    - `kafi_opening_anaphora_previous_hadith`: `448`
  - Context rerun resolved another `3,800` ambiguous nodes.
- Machine-review before -> after:
  - `approve_current`: `28,959` -> `37,844` (`+8,885`)
  - `needs_external_review`: `54,910` -> `45,991` (`-8,919`)
  - `flag_contradiction`: `3,878` -> `3,912` (`+34`)
- Source-prior machine decisions:
  - `kafi_opening_ali_ibrahim`: `3,921 approve_current`
  - `kafi_opening_muhammad_yahya`: `3,489 approve_current`
  - `kafi_opening_anaphora_previous_hadith`: `440 approve_current`, `8 flag_contradiction`
- Impact report:
  - `eshia-research\scratch_audit\kafi_source_prior_impact_20260709.md`
- Verification:
  - Backend full suite: `236 passed, 1 warning`
  - Frontend lint: passed
  - Frontend build: passed
  - Live admin page smoke: passed
- Local servers still running:
  - Frontend: `127.0.0.1:3000`, PID `10364`
  - Backend: `127.0.0.1:8000`, PID `30672`

Codex update on 2026-07-09, 10k corrected external assessment import:

- User supplied corrected result file:
  - `eshia-research\scratch_audit\external_assessment_alkafi_10000_review_results_REDO_v2_ambiguity_corrected.md`
- Backup before applying:
  - `eshia-research\eshia_research.before-10k-external-import.20260709-225954.db`
- Tightened external-review parsing/matching in `eshia-research\src\eshia_research\rijal\external_review.py`:
  - case headings no longer leak into `source_reference` or `raw_case_text`
  - slash variants such as `al-Sarrad / al-Zarrad`, `al-Yaqtini` vs `b. Yaqtin`, and `mawla Al Yaqtin` notes now match local person rows conservatively
  - broad trailing-nisba fallback is not used too early against existing resolver candidates
  - promotion deduplicates multiple reviews for the same node by keeping the latest imported row
  - `approve_current` rows that supply a matched person where the machine had no/different selected person are promoted as admin overrides, not false machine approvals
- Re-imported:
  - the corrected 10k result file
  - the earlier two `pasted-text.txt` external review files, to clean stored evidence text with the fixed parser
- External review storage after cleanup:
  - total rows: `10,050`
  - corrected 10k source label rows: `10,000`
  - earlier `pasted-text` rows: `50`
  - source references with leaked case headings: `0`
  - raw case texts with leaked case headings: `0`
- Corrected 10k import stats:
  - parsed cases: `10,000`
  - matched actionable persons: `3,933`
  - unmatched actionable persons: `0`
  - missing nodes: `0`
  - verdicts: `keep_ambiguous=5,792`, `approve_current=2,056`, `override_person=1,877`, `flag_text_or_chain_issue=275`
- Promoted Al-Kafi external reviews under reviewer `codex-admin-external-v1`:
  - review rows considered: `10,050`
  - unique admin decisions written: `10,031`
  - duplicate-reviewed nodes collapsed: `19`
  - skipped unmatched actionable: `0`
  - admin decisions: `keep_ambiguous=5,792`, `approve_external_override=3,961`, `flag_text_or_chain_issue=276`, `approve_current=2`
- Report:
  - `eshia-research\scratch_audit\external_assessment_10k_import_20260709.md`
- Verification:
  - focused external-review tests: `7 passed`
  - backend full suite: `239 passed, 1 warning`
  - API summary confirmed `total_decisions=10031`
  - frontend admin page smoke returned `200`
- Next recommended phase:
  - mine repeated high-confidence admin overrides into narrow resolver/source-prior rules, rerun Al-Kafi machine review, and measure reduction in `needs_external_review`; do not generate another broad 10k packet until that signal is used.

Useful review commands:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONIOENCODING='utf-8'

python -m eshia_research.cli import-person-review-results --dry-run `
  "C:\Users\taifh\.codex\attachments\b3a8c2dc-1275-4185-af0d-b19449ba64e8\pasted-text.txt" `
  "C:\Users\taifh\.codex\attachments\fbefd25f-b399-466b-a1e3-a44e1892f51b\pasted-text.txt"

python -m eshia_research.cli promote-person-review-results --dry-run --source-book-id 11005
```

PowerShell from `eshia-research`:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONIOENCODING='utf-8'
```

Check split review stats if backend is running:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/hadith-split-reviews/stats?source_book_id=11005' | ConvertTo-Json -Depth 5
```

Check split audit if backend is running:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/hadith-split-reviews/audit?source_book_id=11005' | ConvertTo-Json -Depth 5
```

Planned DB edit recorded by Codex on 2026-07-11 before applying:

- Scope: reconcile the Al-Kafi hadith index with a complete corrected-parser scan of all eight volumes.
- Intended source-row changes: recover 6 swallowed numbered reports, reject 3 additional editorial/commentary false rows, refresh the 6 anchor rows and 3 cross-page continuation targets, and correct 6 rows whose printed number/isnad retained an outer page or verse number.
- ID policy: preserve every existing `hadiths.id` and `public_id`; recovered reports use deterministic suffixed public IDs and are inserted into a contiguous internal `sequence_in_book` ordering.
- Derived-data policy: delete chains/resolution evidence belonging only to the 3 newly rejected false rows; synchronize genuine existing chain/node rows in place so their node IDs and valid external/admin decisions remain linked; add chains for the 6 recovered reports; then refresh resolver-derived data.
- Validated dry run: parser draft `15,335`; current visible `15,332`; exactly 9 page mismatches explained by 6 missing reports and 3 false visible rows. Parser volume counts: `1,442 / 2,344 / 2,182 / 2,192 / 2,201 / 2,666 / 1,711 / 597`.
- Backup target before apply: `eshia-research/eshia_research.before-alkafi-count-reconciliation.20260711-175031.db`

Corrective derived-data plan recorded by Codex on 2026-07-12 before applying:

- The full post-repair person-resolver rebuild passed invariants but regressed the independent Mu'jam corroboration floor from the validated backup's `61.7%` (`63,280/87,747` resolved) to `58.8%` (`58,319/87,752` resolved). Do not retain that regression.
- Scope: restore the validated backup's `mention_resolutions` for chain-node IDs that still exist, retain fresh rows for the 22 genuinely new node IDs, exclude the 17 removed false/surplus node IDs, and restore the validated `person_generations`; then rerun machine review and evaluation.
- This does not restore or overwrite source hadiths, corrected chain text, chain-node structure, external reviews, or admin decisions. It uses the same already verified pre-edit backup: `eshia-research/eshia_research.before-alkafi-count-reconciliation.20260711-175031.db`.

Applied by Codex on 2026-07-12:

- Corrected parser scan and main-DB reconciliation completed.
- Final Al-Kafi counts: `15,361` stored, `26` rejected audit rows, `15,335` visible genuine printed units; corrected-parser draft also `15,335`, with zero page mismatches.
- Visible volume counts: `1,442 / 2,344 / 2,182 / 2,192 / 2,201 / 2,666 / 1,711 / 597`.
- Recovered 6 swallowed reports with stable suffixed IDs; rejected 3 newly proven editorial rows; refreshed 15 genuine rows; internal sequence is unique/contiguous while all existing public IDs remain stable.
- Al-Kafi derived state: `17,184` chains, `87,752` nodes, `1,174` approved splits, `26` rejected splits, `0` needs-review, `suspicious_unreviewed=0`.
- Invalid evidence removed with the false rows: 10 external reviews and 23 decisions. Remaining external rows: `10,040`; admin decisions: `10,021` (`3,961` overrides, `5,782` keep-ambiguous, `276` text/chain flags, `2` approve-current).
- The full resolver rerun's corroboration regression (`58.8%`) was rejected. Validated resolutions were restored for unchanged node IDs and fresh rows retained for 22 new IDs. Final eval: `63,292/87,752` resolved (72.1%), Mu'jam corroboration `61.7%`, reliable generation violations `0/185`, bare-form leaks `0`.
- Final `PRAGMA quick_check`: `ok`; all derived orphan checks: `0`; backend suite: `320 passed, 1 warning`.
- Full report: `eshia-research/scratch_audit/alkafi_count_reconciliation_20260712.md`.
- Live smoke after restart: backend health `ok` on `127.0.0.1:8000` (PID `9260`), frontend HTTP `200` on `127.0.0.1:3000` (listener PID `24276`); split-stats API returned `15,361 / 1,174 / 26 / 0` total/approved/rejected/needs-review.

Planned DB edit recorded by Codex on 2026-07-12 before applying:

- Scope: complete adjudication of all `1,060` Al-Kafi chains previously marked `needs_review`.
- Repairs: 106 source-verified isnad/matn boundary corrections; restore the flattened printed number/body and manually reconstruct both routes for `alkafi-4680`; expand every unambiguous co-narrator combination up to the observed Al-Kafi maximum (24); preserve already-reviewed abbreviated/complex exceptions; mark `جميعاً` convergence chains as `reviewed_complex` while retaining their raw isnad and `multi_route` flag rather than guessing topology.
- ID/evidence policy: preserve existing chain/node IDs whenever tokens are unchanged; retain all external/admin evidence; refuse any destructive remap that touches such evidence; add new IDs only for newly materialized routes.
- Validated dry run: 106 split repairs, 2 explicit complex approvals, 1 source/two-route repair; no remaining non-structural flag in the repair set. Focused tests: `53 passed`.
- Backup target before apply: `eshia-research/eshia_research.before-alkafi-flagged-chain-repair.20260712-004051.db`.

Applied by Codex on 2026-07-12:

- Completed all `1,060` previously flagged chains across `1,030` Al-Kafi hadiths.
- Applied 106 source-verified split repairs, restored the two independent routes
  of `alkafi-4680`, and retokenized every affected hadith with the corrected
  period/parallel-route detector and co-narrator expansion ceiling.
- Final Al-Kafi state: `15,361` stored / `26` rejected / `15,335` visible,
  parser draft `15,335`, page mismatches `0`; `17,299` chains and `88,380`
  nodes; chain statuses `16,122` pending-clean, `248` approved, `892`
  reviewed-complex, `37` reviewed-exception, and **`0` needs-review**.
- Evidence-safe reconciliation preserved stable node IDs, migrated 9 external
  reviews and 1 admin decision, collapsed 8 duplicate admin decisions, and
  retired 46 external + 46 admin parser-artifact reviews whose old node text
  was proven not to be isnad. Every retired case ID is retained in the hadith's
  split-review audit note. Remaining external/admin rows: `9,994 / 9,967`.
- Repaired all inherited external-review `decision_id` audit pointers. Final
  foreign-key check, node-count check, duplicate checks, and all derived orphan
  checks are `0`; `PRAGMA quick_check` is `ok`.
- Full derived rebuild and token-safe restoration completed. Final evaluation:
  `63,847/88,380` resolved (`72.2%`), Mu'jam corroboration floor `61.9%`,
  reliable generation violations `0/185`, bare-form leaks `0`.
- Machine review: `56,441` approve-current and `31,939` external-review cases.
- Full backend suite: `322 passed, 1 warning`.
- Live smoke: backend health `ok`, frontend HTTP `200`, live split stats
  `15,361 / 1,284 / 26 / 0` total/approved/rejected/needs-review;
  `alkafi-4680` exposes 2 chains / 10 nodes.
- Full report:
  `eshia-research/scratch_audit/alkafi_flagged_chain_repair_20260712.md`.

Planned DB edit recorded by Codex on 2026-07-12 before continuing translation setup:

- Scope: translation foundation only. Align the new empty translation schema with Alembic and persist one planned, stratified 300-hadith Al-Kafi English pilot job.
- Important correction: an earlier CLI dry-run invoked the repo's existing `_init_db()` helper and created the empty translation tables before Alembic was stamped. Verified all new translation tables existed with `0` rows and no corpus/translation/job rows written.
- Intended actions now: back up the DB, stamp/align Alembic to translation revision `e8f2c5d9a341`, then run `plan-translation-jobs --source-book-id 11005 --pilot-size 300 --apply --job-key alkafi-en-pilot-300-v1`.
- Non-scope: no model/API calls, no generated English translations, no Arabic hadith/isnad/matn edits, no chain or rijal rebuilds.
- Backup target before continuing: `eshia-research/eshia_research.before-translation-foundation.20260712-130405.db`.

Applied by Codex on 2026-07-12:

- Added first-class translation foundation:
  - SQLAlchemy models and Alembic revision `e8f2c5d9a341_add_translation_tables.py`
  - package `eshia_research.translation` with source hashing, segmentation, deterministic QA, English-formula isnad rendering, and token/cost job planning
  - style guide: `eshia-research/docs/translation_style_guide.md`
  - CLI commands: `plan-translation-jobs`, `render-english-isnad`, `qa-translations`
- DB backup before final alignment/pilot write:
  - `eshia-research/eshia_research.before-translation-foundation.20260712-130405.db`
  - SHA256: `97F4B5DA7A419F44ABCE4451765615D78888753CBF132CC95B2750BDCC7DEDFB`
- Alembic stamped/aligned to `e8f2c5d9a341`. The new translation tables had already been created empty by the earlier dry-run via `_init_db()`; they were verified at `0` rows before pilot write.
- Persisted one representative Al-Kafi English pilot planning job only:
  - job key: `alkafi-en-pilot-300-v1`
  - `300` planned hadiths / `303` matn segments / `303` planned job items
  - length mix: `150` short, `90` medium, `24` long, `16` very-long, `20` oversize
  - volume spread: `39 / 39 / 38 / 38 / 37 / 37 / 36 / 36` hadiths across volumes 1-8
  - source chars `119,915`; estimated input/output tokens `59,570 / 39,096`
  - provider/model recorded as `pending`; no model/API calls made and no English translations generated
- Post-apply DB verification:
  - `PRAGMA quick_check`: `ok`
  - `PRAGMA foreign_key_check`: `0`
  - translation table counts: `hadith_translations=300`, `translation_segments=303`, `translation_jobs=1`, `translation_job_items=303`, attempts/reviews/glossary/memory all `0`
  - `qa-translations` checked `0` rows because no draft translation text exists yet
- Verification: backend suite `330 passed, 1 warning`.

Planned DB edit recorded by Codex on 2026-07-12 before applying direct translations:

- Scope: directly translate the first proof batch from `alkafi-en-pilot-300-v1`: pilot job items `1-12` / translation segments `1-12`.
- Method: Codex direct translation in-session, not an external model/provider API. Store provenance as `provider='codex-direct'`, keep source hashes, run deterministic QA, and update only translation tables/job item status.
- Non-scope: no Arabic hadith/isnad/matn edits, no chain or rijal rebuilds, no bulk pilot completion claim.
- Backup target before apply: `eshia-research/eshia_research.before-direct-translation-batch1.20260712-131534.db`.
- Backup SHA256: `0B7FA39A1B1E25460DBB4A8E491B9EB7585A9C8032140717B10322A9CE9F7ED7`.

Applied by Codex on 2026-07-12:

- User clarified they wanted Codex to translate directly in-session, not call an external provider/model API.
- Direct translation batches written under `provider='codex-direct'`, `model='gpt-5-codex-direct'`, cost `0.0`, with one `translation_attempts` row per translated segment.
- Completed direct English translations for `46` full hadiths in the Al-Kafi pilot job:
  - `alkafi-1` through `alkafi-11`
  - `alkafi-13`
  - `alkafi-15` through `alkafi-22`
  - `alkafi-24`, `alkafi-25`, `alkafi-26`, `alkafi-28`, `alkafi-31`
  - `alkafi-33`, `alkafi-36`, `alkafi-37`, `alkafi-38`, `alkafi-39`, `alkafi-41`, `alkafi-42`, `alkafi-43`, `alkafi-44`, `alkafi-45`, `alkafi-48`, `alkafi-49`
  - `alkafi-1444` through `alkafi-1449`
  - `alkafi-1459`, `alkafi-1460`, `alkafi-1461`
- Also translated segment `0` of long `alkafi-12`, but deliberately kept the hadith-level translation row `planned/unscored` with `matn_translation=NULL` so partial text is not mistaken for a complete hadith translation.
- Current translation DB counts:
  - `translation_segments`: `47` machine_verified/green, `256` planned/unscored
  - `translation_job_items`: `47` verified/green, `256` planned/unscored
  - `hadith_translations`: `46` machine_verified/green/codex-direct, `253` planned/unscored/no provider, `1` planned/unscored/codex-direct partial (`alkafi-12`)
  - `translation_attempts`: `47` completed codex-direct
- QA/integrity:
  - `qa-translations --source-book-id 11005 --language en --limit 80`: checked `46`, all `green`
  - `PRAGMA quick_check`: `ok`
  - `PRAGMA foreign_key_check`: `0`
  - focused translation tests: `8 passed`
- Next direct translation recommendation: continue with complete one-segment reports first, and reserve very long reports (`alkafi-12`, `alkafi-14`, etc.) for dedicated long-form passes so partials never publish as complete.
- Cross-check packet exported for ChatGPT review:
  - `eshia-research/scratch_audit/alkafi_direct_translation_crosscheck_46_of_1000_20260712.txt`
  - Contains Arabic isnad, Arabic matn, English isnad context, English matn translation, source location, source matn SHA256, and reviewer instructions.
  - Honest scope: `46` complete green translations out of the requested `1,000`; no placeholder/fake translations included.

CLI commands visible in `eshia-research/src/eshia_research/cli.py`:

- `rebuild-chain-index`
- `rebuild-mujam-index`
- `resolve-chain-narrators`
- `audit-hadith-splits`
- `build-person-layer`
- `resolve-persons`
- `build-tabaqat`
- `refine-tabaqat`
- `refine-compiler-priors`
- `refine-collective-context`
- `plan-translation-jobs`
- `render-english-isnad`
- `qa-translations`

## Translation reader UI (Codex, 2026-07-12)

- Added the public translation slice to the existing hadith API responses used by printed-page, chapter, and permalink readers.
- Publication gate is enforced server-side: only English `matn_en_v1` rows with a non-empty matn, `green` risk, status `machine_verified`, `human_reviewed`, or `published`, and matching full/isnad/matn source hashes are returned. Planned, partial, red/amber, rejected, and source-stale translations return as `translation: null`.
- Added an unobtrusive native disclosure below the Arabic matn: `Read English translation` / `Hide English translation`. Arabic remains visible and authoritative; the English panel is LTR, shows the deterministic English isnad when available, and clearly labels machine-verified drafts versus human-reviewed/published text.
- No disabled or unavailable translation control is rendered on untranslated hadiths. Future complete green batches appear automatically without further frontend changes.
- Verification:
  - focused backend API tests: `30 passed, 1 warning`
  - full backend suite: `331 passed, 1 warning`
  - frontend lint: passed
  - frontend production build: passed on Next.js `16.2.9`
  - real DB smoke: `alkafi-1` exposed a green `machine_verified` translation; partial `alkafi-12` correctly exposed none

Live start follow-up by Codex on 2026-07-12:

- While starting the local app, the live API initially hid `alkafi-1`'s verified translation because the publication gate required `source_isnad_sha256` to be truthy before comparing it. Fixed the gate to compare against the expected hash directly, allowing `None == None` for matn-only/no-separate-isnad rows while preserving full/isnad/matn stale-source protection.
- Added regression coverage for the no-isnad publishable case in `tests/test_api_books.py`.
- Verification:
  - focused backend API tests: `30 passed, 1 warning`
  - `git diff --check`: no whitespace errors, CRLF warnings only
  - live smoke: backend `http://127.0.0.1:8000/hadiths/alkafi-1` returns the `machine_verified` translation, and frontend `http://127.0.0.1:3000/hadith/alkafi-1` contains `Read English translation`.

## Thaqalayn Al-Kafi Translation Import (Codex, 2026-07-12)

- Added `eshia_research.translation.thaqalayn_importer` and CLI command `import-thaqalayn-alkafi`.
- Source: public Thaqalayn API v2 Al-Kafi volume endpoints (`Al-Kafi-Volume-1-Kulayni` through `Al-Kafi-Volume-8-Kulayni`), translator recorded as Muhammad Sarwar, provider `thaqalayn-api`, model `muhammad-sarwar`.
- Matching method: forward-only per-volume Arabic word coverage plus exact normalized substring checks, minimum score `0.88`, matcher version `thaqalayn_match_v1`.
- Import policy:
  - does not overwrite existing green current translations unless `--overwrite-current` is explicitly supplied
  - stores source hashes against the local Arabic hadith so public API stale-source protection still applies
  - treats edition footnote/number mismatches as provenance QA flags, not fatal blockers
  - blocks empty output, provider-refusal text, untranslated Arabic blocks, and suspicious length collapse/expansion
- Backup before write:
  - `eshia-research/eshia_research.before-thaqalayn-import.20260712-144548.db`
  - SHA256 `6D2A046B245A6C04FDB928AD316E09263E08EDB70621791F406FA7159850C5A6`
- Applied import result:
  - fetched Thaqalayn rows: `14,245`
  - local visible Al-Kafi reports considered: `15,335`
  - confident Arabic matches: `13,292`
  - imported new green rows: `13,209`
  - skipped existing green Codex-direct rows: `46`
  - blocked by import QA: `37`
  - unmatched local reports: `2,043`
  - unmatched Thaqalayn rows: `953`
  - errors: `0`
- Current green English translation counts after import:
  - total: `13,255`
  - Thaqalayn/Sarwar: `13,209`
  - Codex-direct: `46`
- Public API now includes translation `provider`, `model`, and `provenance_json`; reader UI shows source attribution, e.g. `Muhammad Sarwar, via Thaqalayn`, linked to the Thaqalayn source URL.
- Verification:
  - focused importer/pipeline/API tests: `40 passed, 1 warning`
  - full backend suite: `333 passed, 1 warning`
  - DB `PRAGMA quick_check`: `ok`
  - DB `PRAGMA foreign_key_check`: `0`
  - frontend production build: passed on Next.js `16.2.9`
  - frontend lint: blocked by pre-existing unrelated React lint findings in `SiteHeader.tsx` and `ThemeToggle.tsx`, plus an unused `Rise` import in `app/page.tsx`
  - live smoke: backend `http://127.0.0.1:8000/hadiths/alkafi-47` returns Thaqalayn provenance; frontend `http://127.0.0.1:3000/hadith/alkafi-47?fresh=1` contains `Muhammad Sarwar, via Thaqalayn`

## Thaqalayn Al-Kafi Translation Rematch (Codex, 2026-07-13)

- Fixed the reader label so public users see translation source attribution instead of the internal `Machine-verified draft` status.
- Corrected Thaqalayn provenance semantics: Muhammad Sarwar / Thaqalayn imports are now stored as `published`, not machine-generated drafts.
- Upgraded the Arabic matcher to `thaqalayn_match_v2`:
  - evaluates the strongest candidate in the bounded sequence window instead of accepting the first adequate candidate
  - permits a 64-row look-back for small cross-edition reorderings
  - retains sequence-proximity tie-breaking and the existing `0.88` threshold / QA gates
- Added regression tests for best-candidate selection, cross-edition reordering, and published status.
- Backup before the live rematch:
  - `eshia-research/eshia_research.before-thaqalayn-rematch.20260713-143318.db`
  - SHA256 `5849E4FE4F282E7831AF6DE8071E47A549B8C36D3CAE1F02983998EC114FB912`
- Applied result:
  - fetched Thaqalayn rows: `14,245`
  - local visible Al-Kafi reports: `15,335`
  - confident matches: `13,398`
  - newly imported publishable rows: `104`
  - existing Thaqalayn rows relabelled as published: `13,209`
  - current public translations: `13,359` (`87.11%`)
  - missing translations: `1,976` (`1,937` unmatched plus `39` blocked by QA)
  - all `13,359` public rows match the current full/isnad/matn source hashes
- The remaining gap cannot be filled honestly from this Thaqalayn/Sarwar source alone: the API supplies `1,090` fewer rows than the verified local edition, with the largest structural gap in volume 7 (`1,711` local vs `891` remote). Do not attach translations to uncertain reports merely to claim complete coverage.
- Integrity/live checks:
  - SQLite `quick_check`: `ok`
  - foreign-key violations: `0`
  - `alkafi-1152` API: `provider=thaqalayn-api`, `status=published`, live Thaqalayn source URL
  - reader: English toggle and `Muhammad Sarwar, via Thaqalayn` present; `Machine-verified draft` absent

## ThaqalaynData Al-Kafi Translation Completion Pass (Codex, 2026-07-14)

Planned DB edit recorded by Codex on 2026-07-14 before applying:

- Scope: import additional Al-Kafi English translations from the CC0 ThaqalaynData static dataset, using Sarwar first and HubeAli only where Sarwar is absent; replace existing public `codex-direct` pilot translations when a publishable ThaqalaynData human translation is available; preserve existing current Thaqalayn/Sarwar rows.
- Source cache: `C:\Users\taifh\AppData\Local\Temp\thaqalayn-al-kafi-static-full-fromzip.json`, generated from the `narmafraz/ThaqalaynData` GitHub archive and the complete Al-Kafi manifest (`15,385` refs; `15,381` usable human translation rows).
- Dry-run result: `15,381` remote rows; `15,335` visible local Al-Kafi reports; `15,062` confident Arabic matches; `273` unmatched local reports; `139` QA-blocked matched rows.
- Expected public gain from current DB state: `1,777` new translations plus replacement of all `46` public `codex-direct` rows, leaving about `199` visible Al-Kafi reports still untranslated/blocked.
- Command: `import-thaqalayn-alkafi --source static --static-cache-path %TEMP%\thaqalayn-al-kafi-static-full-fromzip.json --replace-provider codex-direct --apply`.
- Backup target before apply: `eshia-research/eshia_research.before-thaqalayndata-completion.20260714-143000.db`.
- Backup SHA256: `6746DC7839168AD41CD0A21F8A4689CB53523AC98EB0FA4ACCA06F52E082DA87`.

Applied by Codex on 2026-07-14:

- Applied ThaqalaynData static import with `--replace-provider codex-direct`.
- Apply result: `15,381` fetched usable remote rows, `15,335` visible local Al-Kafi reports, `15,062` confident matches, `1,823` imported/updated rows, `13,203` existing Thaqalayn rows preserved, `36` new matched rows blocked by import QA, `273` unmatched local reports, `0` errors.
- Public current Al-Kafi English coverage after import:
  - `15,136 / 15,335` visible reports translated (`98.70%`)
  - `199` visible reports still untranslated/blocked
  - provider counts: `13,313` `thaqalayn-api`, `1,823` `thaqalayn-data`
  - model/translator counts: `14,090` Muhammad Sarwar, `1,046` HubeAli
  - all public rows are `published`; public `codex-direct` rows: `0`
  - all public rows match current local source hashes; stale public rows: `0`
- Remaining missing by volume: v1 `16`, v2 `6`, v3 `12`, v4 `7`, v5 `28`, v6 `87`, v7 `25`, v8 `18`.
- Integrity/verification:
  - `PRAGMA quick_check`: `ok`
  - `PRAGMA foreign_key_check`: `0`
  - focused backend tests: `48 passed, 1 warning`
  - live API smoke: `alkafi-12` exposes `provider=thaqalayn-data`, `model=hubeali`, `status=published`, translator `HubeAli`
  - backend and frontend restarted; backend health `ok`, frontend `http://127.0.0.1:3000/hadith/alkafi-12?fresh=1` HTTP `200`

## Sarwar-only verified rematch (Codex, 2026-07-15)

User direction: do not add further HubeAli translations; use Muhammad Sarwar as the primary English translation.

Planned DB edit recorded before applying:

- Scope: replace only current HubeAli fallbacks with a unique, unowned Muhammad Sarwar record from the official Thaqalayn API, and fill only currently unpublished rows meeting the same checks.
- Required checks: Arabic score at least `0.88`, runner-up margin at least `0.03`, no remote-record ownership collision, no blocking translation-QA flag, and a verified live canonical Thaqalayn source page.
- Dry-run result: `32` changes (`30` HubeAli-to-Sarwar replacements and `2` new Sarwar translations).
- Rejected from this pass: low-confidence/ambiguous candidates, `14` missing-row candidates with blocking QA, and `3` strong candidates whose remote Sarwar record was already owned by a different local report.
- Apply script: `eshia-research/scratch_audit/apply_verified_sarwar_api_rematch.py`.
- Reviewed manifest: `eshia-research/scratch_audit/alkafi_sarwar_api_verified_manifest_20260715.json`.
- Backup target before apply: `eshia-research/eshia_research.before-sarwar-verified-rematch.20260715-170238.db`.

Applied and verified by Codex on 2026-07-15:

- Backup created successfully; SHA256 `EAB10E3EF644AB0D9EAEE0992B6C3560444A3FCCB672AED9C7033D1A586DBEF9`.
- Applied `32` records: `30` HubeAli fallbacks replaced by Muhammad Sarwar and `2` previously missing reports supplied with Muhammad Sarwar.
- Current public coverage: `15,138 / 15,335` (`98.72%`); missing `197`.
- Current public translator counts: Muhammad Sarwar `14,122`; HubeAli `1,016`.
- No new HubeAli rows were added. Existing HubeAli rows remain only where this pass did not establish a collision-free, QA-safe Sarwar replacement.
- Corrected legacy Thaqalayn API URLs so imported volumes 2-8 point to their actual live volume route instead of the upstream `/hadith/1/...` error.
- Verification: SQLite `quick_check=ok`; foreign-key violations `0`; stale public source hashes `0`; rematch rerun selected `0` (idempotent); focused tests `50 passed, 1 warning`; live API source/model/status checks passed for `alkafi-1`, `alkafi-10316`, `alkafi-14141`, and `alkafi-14453`.

## Launch hardening (Codex, 2026-07-13)

- Public editorial writes now fail closed. `PUT /hadith-split-reviews/{public_id}` requires `X-Admin-Token`; an empty `API_ADMIN_TOKEN` disables writes with HTTP 503. API docs are disabled by default, CORS origins are environment-configured, and public review pages return 404 unless `ENABLE_REVIEW_UI=true`.
- Added an administrator-token field to the private split-review client without persisting the secret in browser storage.
- Search now queries public green/published English translations and links those hits to stable hadith records. Latin queries bypass the Arabic page scan and known collection names are searchable. Real DB `prayer` search improved from about `19.3s` to `0.15s`.
- Added `/corpus-status` and the public `/methodology` page with live per-collection page, visible-hadith, chain-review, English-coverage, and approved-split counts. Book surfaces now identify Al-Kafi as the research beta and distinguish under-review, preview, page-text, and rijal-reference collections.
- Replaced the unsupported global completeness claim with collection-specific maturity language and documented the 15,335 versus commonly cited 16,199 Al-Kafi counting issue.
- Expanded copied citations with volume/page range, printed number, public ID, canonical URL, source URL, and access date.
- Added global error recovery, a useful 404, page metadata/canonicals, robots/sitemap, security headers, request timeouts, and production environment/deployment gates.
- Reduced narrator initial payloads (15 initial appearances, 25 initial transmission edges, source-linked 6,000-character rijal previews). Representative production narrator HTML dropped from about `530KB` before hardening to `247KB` before the final 15/25 reduction.
- Increased graph aggregation cache TTL to one hour and documented prewarming plus edge/proxy rate limiting.
- Fixed nested main landmarks, missing reader/hadith headings, reduced-motion gaps, animated layout padding, and undersized primary reader/search/graph/citation controls and footnote markers.
- Added `docs/content-rights-register.md`. Arabic source, translation, and cover reuse permission remains an external public-launch gate until evidence is recorded.
- Verification:
  - full backend suite: `337 passed, 1 warning`
  - frontend lint: passed
  - frontend production build: passed on Next.js `16.2.9`
  - production smoke: homepage, methodology, English search, stable hadith permalink all HTTP 200; `/review/splits` HTTP 404
  - live write probe without admin configuration: HTTP 503, no mutation
  - local servers restarted at `http://127.0.0.1:3000` and `http://127.0.0.1:8000`

## Al-Kafi 179-report Sarwar recovery, phases 1-3 (Codex, 2026-07-16)

- Scope approved for database write: import exactly the `109` clean `ready_sarwar` records in `eshia-research/scratch_audit/alkafi_sarwar_179_dossier_20260715.json`; do not modify the other `70` target reports or the separately deferred `18` reports.
- Source mix: `62` records recovered from checksum-pinned published Muhammad Sarwar scans and `47` from ThaqalaynData rows explicitly attributed to Muhammad Sarwar. Volume mix: v1 `5`, v2 `2`, v3 `8`, v4 `4`, v5 `8`, v6 `75`, v7 `7`, v8 `0`.
- Identity evidence is restricted to direct Arabic matches or one-to-one gaps bounded by direct Arabic anchors. The older API-URL/static-path planner was found invalid and is not used for any import decision.
- Source-purity safeguard excludes `hubeali.com` and HubeAli-style `(azwj)`, `(saww)`, and `(asws)` markers. Twelve mislabeled volume-8 candidates were removed before the manifest was locked.
- Reviewed dossier SHA-256: `6f656feb9334767668729dd5444472d10c997bf3327031927c6e4cbfac4e9b77`.
- Backup target before apply: `eshia-research/eshia_research.before-sarwar-179-phases1-3.20260716-005431.db`.
- Backup completed at `2,250,383,360` bytes with SHA-256 `4D14D27DC6CDC76ECEC86D0D2B29C68F5BF20CC8F1F2B8E97C93431056B791D9`.
- Import completed atomically: `109` published/green translations, `109` published/green linked segments, `109` verified job items, and `109` completed zero-cost source-import attempts. Idempotent rerun reports `selected=0`.
- Resulting Al-Kafi public English coverage: `15,247 / 15,335` (`99.4261%`), leaving `88`; translator counts are Muhammad Sarwar `14,231` and pre-existing HubeAli `1,016`.
- Verification: no forbidden source markers in the new rows; stale public source hashes `0`; SQLite `quick_check=ok`; foreign-key violations `0`; focused translation/import/API tests `50 passed, 1 warning`; API spot checks passed for static-source `alkafi-211` and scan-recovery `alkafi-11141`.

## Al-Kafi strict human-source translation enforcement (planned, 2026-07-16)

- User explicitly prohibited all Codex-generated English and reported suspicious wording in the opening reports.
- Deep audit found zero current/public Codex-marked hadith-level rows, but one surviving green Codex partial segment (`alkafi-12`, segment `12`), 47 Codex attempt payloads containing English, and the obsolete 303-item Codex pilot job still marked `running`.
- Eight public rows contain project-authored English rather than a verbatim/bounded external excerpt and will be rejected/red with their English cleared: `alkafi-10724`, `alkafi-11166`, `alkafi-11167`, `alkafi-11168`, `alkafi-11169`, `alkafi-11277`, `alkafi-11999`, `alkafi-12739`.
- `alkafi-1160` is retained because its public wording is an exact bounded excerpt of the external Sarwar field. `alkafi-1282` and `alkafi-1292` are retained as explicitly labelled numeric corrections, not newly translated prose.
- Pinned-source dry run verified `13,363` Thaqalayn API rows and `1,840` ThaqalaynData rows against source snapshots, including harmless HTML-to-plain-text normalization; it found `12,041` legacy API citation URLs requiring volume repair and `15,203` current whole-matn segment metadata rows to pin with English/source hashes.
- Cleanup script: `eshia-research/scratch_audit/retire_alkafi_codex_and_repair_provenance.py`; dry-run completed successfully. It redacts generated text from all 47 Codex attempt payloads, clears/rejects segment 12, cancels the pilot job, quarantines the eight authored rows, and pins/repairs external provenance.
- Backend public policy is now centralized across reader, English search, and corpus metrics: only `human_reviewed`/`published`, green, nonempty, source-current, non-AI rows can publish. Frontend source labels now expose translator attribution honestly and translation-bearing fetches bypass stale caching.
- Backup target before apply: `eshia-research/eshia_research.before-human-source-enforcement.20260716-123401.db`.
- Backup completed at `2,251,923,456` bytes with SHA-256 `B087571137BB5F43EF9FD3AEF7B8D3D0B1959F4236D22F92BE6426341E9FC06A`.
- Cleanup applied atomically: `47` generated attempt payloads redacted, the surviving Codex partial segment cleared/rejected, obsolete `303`-item pilot cancelled/retired, and all `8` project-authored public English rows cleared/rejected. The `15,203` remaining external rows now have pinned source-English hashes/metadata, and `12,041` legacy API citation URLs were repaired.
- Planned follow-up DB edit: replace opening reports `alkafi-1` through `alkafi-34` with exact, bounded Muhammad Sarwar matn excerpts from the checksum-pinned published Volume 1 PDF; this is source transcription/alignment only, with no project-generated translation or paraphrase. Reviewed manifest: `eshia-research/scratch_audit/alkafi_opening_sarwar_pdf_manifest_20260716.json`, SHA-256 `e014622db49797548dd6d2ba620e84d873c9298cc57f1ea1490d8b9053d2248c`.
- Opening-import source PDF SHA-256: `969ff47af5fe9d0bf6ca542aa11f2d27130437b156448ee9cb4b141ba2f1d41a`; identity is direct/anchored, with explicit manual evidence for reports 14 and 23. Dry run selected exactly `34`, with `0` blocking QA findings and `0` generated-English markers.
- Backup target before opening import: `eshia-research/eshia_research.before-opening-sarwar-import.20260716-124003.db`.
- Opening-import backup completed at `2,279,903,232` bytes with SHA-256 `3596F0BDD2A8EEF17CE3EC3EB7E3BC91EE32BE1CB9306FAD3F5ED10D62473747`.
- Opening import applied atomically to `alkafi-1` through `alkafi-34`; all `34` rows/segments exactly match the pinned manifest and published Sarwar PDF excerpts. Immediate idempotency rerun selected `0`; import job `7` completed with `34` verified items/attempts and zero tokens/cost.
- Follow-up publication hardening requires positive human-source metadata (named translator plus approved external-source classification), rejects any green row retaining a critical flag, and repeats that guard in the active frontend reader/search paths. Search responses now carry the minimal source evidence needed for the client-side gate.
- Planned DB edit: normalize legacy draft-oriented QA false positives on exactly `7,176` checksum-verified external source rows (`7,123` number differences, `6,093` local footnote-marker differences, `3` literal narrative phrases). This changes only flags/provenance, preserves the original diagnostics in import attempts, and changes zero Arabic/English characters. Dry run leaves `0` green/public rows with critical flags.
- Planned DB edit: quarantine `alkafi-1282` and `alkafi-1292`. Their English numbers were project corrections of the published Sarwar wording rather than verbatim external-source text; clear/reject them until a citable human-published correction is found. The bounded external excerpt `alkafi-1160` remains because every displayed word is an exact contiguous Sarwar source excerpt.
- Backup target before QA normalization and the final two-row quarantine: `eshia-research/eshia_research.before-external-source-finalization.20260716-130630.db`.
- Backup completed at `2,280,108,032` bytes with SHA-256 `3BCC9392240271EA3DB5B6FAF4E467DB14933A42E0454DED3242FDB3AF950925`.
- QA-normalization caution: an initial broad normalization of all `7,176` rows was immediately reversed after the deeper Arabic-extent audit found that the legacy numeric bucket mixes apparatus differences with genuine overmerges/wrong alignments. `rollback_alkafi_external_source_qa_normalization.py --apply` restored exactly the pre-normalization `risk_flags`, provenance/metadata, QA versions, and timestamps from the recorded backup; post-rollback logical diffs versus the backup are `0` for translations and segments, and no text column was touched. Selective alignment-aware normalization replaces the broad plan.

## Non-canonical translation source-hash repair (Claude, 2026-07-17)

Undocumented prior work found first. The 2026-07-16 afternoon session left seven
backups (`before-75-source-alignment-quarantine` 141231, `before-deep-human-source-repair`
134621, `before-structural-source-repair` 145546, `before-final-human-source-republication`
150546, `before-final-boundary-repair-wave` 155500, `before-extent33-source-repair`
155900/160300, `before-extent33-sarwar-republication` 161000) that NO section of this file
records. That breaches the Update Protocol above. Two measured consequences:

- Visible Al-Kafi rows moved `15,335` -> `15,336` and rejected `26` -> `25` during
  `structural-source-repair` (between 145546 and 155500): one previously rejected
  fragment was restored to visible. This may well be correct, but it is unaudited and
  every count in this file above still says `15,335`.
- The published coverage figure recorded on 2026-07-16 (`15,211 / 15,335`, missing `124`)
  is stale. Measured through the real gate on 2026-07-17: `15,180 / 15,336` public,
  missing `156`.

### The bug

`eshia_research.translation.text.sha256_text` hashes WHITESPACE-COLLAPSED text
(`clean_ws`). Three scratch scripts define a LOCAL `sha256_text` that shadows it and
hashes the raw string instead:

- `apply_alkafi_extent33_sarwar_republication.py` (writes source hashes)
- `apply_alkafi_editorial_contamination_quarantine.py` (writes source hashes)
- `apply_alkafi_structural_extent_repairs.py` (verify-only, does not write)

`apply_alkafi_extent33_sarwar_republication.py` republished 30 rows on 2026-07-16 using
its raw hasher. The 20 whose Arabic was already whitespace-clean were unaffected (both
conventions agree there). The 10 carrying a stray double space or newline got a hash the
public gate can never reproduce, so `source_hashes_are_current` failed and they stayed
invisible. That pass believed it recovered 30 reports; it actually recovered 20.

These 10 are published, green, correctly attributed Muhammad Sarwar translations. Their
Arabic never changed: the stored hash equals the RAW hash of the CURRENT text, which is
proof of no drift. This was never Arabic drift, contrary to the first reading.

### Planned DB edit recorded before applying

- Scope: re-pin `source_full_sha256` / `source_isnad_sha256` / `source_matn_sha256` with
  the canonical `sha256_text` for exactly the 10 Al-Kafi rows whose stored hash matches
  the raw convention. Writes only those three columns plus a
  `source_hash_convention_repair` provenance note. Changes ZERO Arabic and ZERO English
  characters.
- Fail-closed rule: a row is touched ONLY when its stored hash equals the raw hash of the
  current text (proving the text is unchanged). Any row matching neither convention is
  genuine drift and is reported, never rewritten.
- Targets: `alkafi-934`, `alkafi-1073`, `alkafi-4295`, `alkafi-5698`, `alkafi-5743`,
  `alkafi-6681`, `alkafi-9383`, `alkafi-11329`, `alkafi-12933`, `alkafi-14751`.
- Deliberately NOT touched: `alkafi-11096`, `alkafi-11210`, `alkafi-14040`, `alkafi-15260`
  match neither convention (genuine drift) and are rejected/red on other grounds anyway.
- Script: `eshia-research/scratch_audit/repair_noncanonical_translation_source_hashes.py`
  (dry-run by default, `--apply` to write).
- Dry run: examined 15,274 rows, selected exactly 10, all 10 currently hidden from readers.
- Backup target before apply:
  `eshia-research/eshia_research.before-noncanonical-hash-repair.20260717-094508.db`
- Backup completed at `2,311,577,600` bytes with SHA-256
  `FF605EEE2CCE43EA442F1A9D4D924CDE3D857CE2BC55DCE4A010DDC60ECD2412`.

### Applied by Claude on 2026-07-17

- Re-pinned exactly the 10 rows. Public Al-Kafi English coverage
  `15,180 / 15,336` -> `15,190 / 15,336` (`99.0480%`); missing `156` -> `146`.
- Proved a no-op on content by diffing every row against the backup:
  `matn_raw`, `isnad_raw`, `full_text_raw`, `review_status`, `matn_translation`,
  `full_translation`, `status`, `risk_level`, and `risk_flags` all changed on `0` rows.
  Only `source_*_sha256` changed, on exactly the 10 expected `public_id`s.
- Idempotent: rerunning the dry run now selects `0` non-canonical rows and still
  reports the same `4` genuinely drifted rows, untouched.
- Integrity: `PRAGMA quick_check` = `ok`; `PRAGMA foreign_key_check` = `0` violations.
- Live API confirms `alkafi-934`, `alkafi-1073`, `alkafi-4295`, and `alkafi-14751` now
  serve `status=published`, `provider=thaqalayn-api`, translator `Muhammad Sarwar`.
  `alkafi-11096` (genuine drift) correctly still returns `translation: null` — the gate
  still fails closed.
- Regression test added:
  `test_source_hashes_are_current_requires_the_canonical_hasher` in
  `tests/test_translation_pipeline.py`. It pins the same hadith with both hashers and
  asserts the raw one fails the gate. Full backend suite: `351 passed, 1 warning`.

### Standing caution

Any code writing `source_*_sha256` MUST use `eshia_research.translation.text.sha256_text`.
Never re-implement it: a local raw `hashlib.sha256` silently agrees on whitespace-clean
text and diverges only on the minority of rows with irregular whitespace, so the damage
is invisible in testing and shows up as translations that vanish from the reader. The two
writer scripts named above still contain the shadowing definition and are left as applied
audit artifacts — do NOT re-run them without switching them to the canonical hasher.

### Still open from the 2026-07-16 undocumented work

- The `15,335` -> `15,336` visible-count change (one fragment un-rejected during
  `structural-source-repair`) is still unaudited. Every count in the sections above
  predates it. Someone should confirm that row is a genuine printed report.
- `alkafi-11096`, `alkafi-11210`, `alkafi-14040`, `alkafi-15260` carry real source drift
  (stored hash matches neither convention). They are rejected/red on other grounds, so
  they are not public, but the drift itself is unexplained.

## Global-match translation recovery (Claude, 2026-07-17)

User direction: match thaqalayn.net, which shows an English translation for every report.

### The windowed matcher was hiding real matches

`_match_volume` scans only a bounded window (`WINDOW_BACK`/`WINDOW_FORWARD`) around a
running cursor. Where the editions diverge enough that a report's counterpart sits far
outside that window, it is never scored. The `no_reliable_alignment: 62` verdict in
`alkafi_post_deep_scan_queue_20260716.json` was therefore substantially an artefact of
HOW WE SEARCHED, not evidence the translation was absent.

An unbounded search of all 15,385 ThaqalaynData rows against the 146 untranslated reports
found 70 with a >=0.88 match, 44 of them >=0.95. Do not trust the old "no reliable
alignment" label without re-running an unbounded search.

### What thaqalayn.net actually has (measured, not assumed)

- 15,385 rows, `0` with no English at all. Their 100% is real.
- Muhammad Sarwar covers only `14,175 / 15,385` (`92.14%`). They reach 100% via HubeAli.
- Volume 7 Sarwar is `890 / 1,734` (`51.33%`) -- the real Sarwar gap.
- **Volume 8 `en_sarwar` is contaminated**: `457 / 597` (`76.55%`) of its "Sarwar" rows
  carry HubeAli-style `(azwj)/(saww)/(asws)` markers, against `0.00%` in volumes 1-7.
  That field is not Sarwar. This confirms the earlier "no verified Sarwar volume 8"
  finding — do not import volume-8 `en_sarwar` as Sarwar.

### Identity contract (guards against the containment trap)

Word coverage is asymmetric: a long remote report that merely CONTAINS a short local matn
scores 1.0 forward while being a different report. Required, all four:

- forward coverage >= 0.88, reverse coverage >= 0.50, length ratio in [0.30, 1.30]
- same volume, no remote row used twice, no remote row owned by another local report

This rejected 10 of the 70, including `alkafi-14752` (600 local words vs 4,026 remote,
fwd 0.97 / rev 0.15) and `alkafi-14755` (549 vs 3,348). Publishing those would have
attached a multi-thousand-word translation to a much smaller report.

### Planned DB edit recorded before applying

- Scope: import English for 60 verified Al-Kafi reports via
  `import_thaqalayn_al_kafi(matches=...)`, a new seam that accepts externally established
  pairings and still applies every existing QA, publishability, hashing and provenance
  rule. Hashes go through the canonical `sha256_text`.
- Translator mix: Muhammad Sarwar `9`, HubeAli `51`. This knowingly relaxes the
  2026-07-15 Sarwar-only instruction, on explicit user direction to match thaqalayn.net,
  which itself serves HubeAli for these reports. Attribution stays per-row and visible.
- Of the 60, QA passes `35` and blocks `25` (`number_mismatch`, `missing_placeholder`,
  `translation_too_long/short`). The 25 are NOT overridden: that is the same flag bucket
  the 2026-07-16 broad normalization tried to clear and then rolled back after finding it
  mixes apparatus differences with genuine overmerges. Only the 35 publish.
- Scripts: `scratch_audit/import_globally_matched_thaqalayn_rows.py` (identity contract +
  import), dry-run by default.
- Backup target before apply:
  `eshia-research/eshia_research.before-global-match-import.20260717-100233.db`
- Backup completed at `2,311,577,600` bytes with SHA-256
  `31969A0A7BE5E24D1BE22C6F068B12BAB2B0AB438482E70FFB3695C9AE0B5B2B`.

### Applied by Claude on 2026-07-17

- Imported `35`; QA skipped `25`; `0` errors; `0` skipped as low-confidence or existing.
- Public Al-Kafi English coverage `15,190 / 15,336` -> `15,225 / 15,336` (`99.2762%`).
  Untranslated `146` -> `111`.
- Integrity: `PRAGMA quick_check` = `ok`; `PRAGMA foreign_key_check` = `0`.
- Backend suite `351 passed, 1 warning`. Live API + reader verified for `alkafi-11096`,
  `alkafi-11141`, `alkafi-11142`: `published`, `provider=thaqalayn-data`, translator
  `HubeAli` rendered on the page, no mojibake.
- The 10 rows in the earlier `STALE SOURCE HASH` class are gone; that bucket is now empty.

### The remaining 111, and why 15,336 is not reachable from this source

- `61` have no translation row at all -- their best global candidate scores below the
  identity contract, mostly `<0.60`. There is no Thaqalayn entry that IS these reports.
- `28` rejected misnumbered Sarwar scans, `9` AI-marker quarantined, `8` project-authored
  and cleared, `3` stale+rejected, `2` planned/unscored.
- The blocker is edition divergence, not translator availability and not effort. The local
  eShia edition and Thaqalayn's edition split reports differently; this is the same
  15,335-vs-16,199 counting divergence the methodology page documents. Closing the last
  111 by attaching each report's nearest candidate would publish translations of text that
  is not the report displayed, which the product's source-verifiability forbids. If the
  gap must close, it needs a human adjudicating each report against the print editions --
  a research task, not a matching threshold.
- Re-running an unbounded search will NOT find more: it has already been run against all
  15,385 rows. The next honest gain is hand-review of the `25` QA-blocked rows above
  (mostly `number_mismatch`/`missing_placeholder`, which may be apparatus differences
  rather than misalignments) and the 17 scoring 0.80-0.88.

## HubeAli-preference pass + a QA blind spot (Claude, 2026-07-17)

User direction: use HubeAli for the missing reports. Measured headroom first: HubeAli was
ALREADY the automatic fallback (`_choose_static_translation` takes Sarwar, else HubeAli;
51 of the 60 rows in the global-match pass were HubeAli). Preferring it harder unlocks
almost nothing, because translator choice is not the blocker. Of the 111 then untranslated:

- `39` identity failed, best global candidate `<0.60`
- `37` identity failed, best candidate `0.60-0.88`
- `16` QA-blocked while ALREADY using HubeAli, no alternative translator exists
- `10` identity failed, `>=0.88` but rejected by the symmetry/containment guard
- `6` QA-blocked on Sarwar, HubeAli fails too
- `3` QA-blocked on Sarwar where HubeAli would pass

### QA blind spot found (important, affects the whole number_mismatch bucket)

`number_tokens` in `translation/text.py` matches `[0-9٠-٩۰-۹]+` — DIGITS ONLY. Al-Kafi's
Arabic spells numerals as words (`خَمْسٍ وَ سِتِّينَ`), so the Arabic side contributes ZERO
number tokens and `number_mismatch` cannot compare the actual quantities. The flag fires
only on digits appearing in the English (list prefixes, dates). Consequences:

- The `7,123` "number differences" the 2026-07-16 pass tried to normalize are largely this
  artefact — which is consistent with that pass being rolled back.
- A `number_mismatch` PASS is not evidence the numbers agree. It was about to publish
  `alkafi-1282` whose HubeAli English says "fifty-six" against Arabic reading
  `خَمْسٍ وَ سِتِّينَ` (sixty-five). Al-Sadiq died in 148 AH aged 65; the Arabic is right and
  HubeAli is wrong. Any future numeric QA for this corpus must parse spelled-out Arabic
  numerals, not digits.

### Applied by Claude on 2026-07-17

- Backup: `eshia-research/eshia_research.before-hubeali-forced-2rows.20260717-110253.db`
  (`2,311,577,600` bytes).
- Hand-verified all 3 candidates against the Arabic numeral-by-numeral, then imported 2:
  - `alkafi-1292`: Arabic 54 / year 183 / 35 years — HubeAli "fifty-four" / "one hundred
    and eighty three" / "thirty five". All agree. IMPORTED.
  - `alkafi-2782`: Arabic 70,000 walls / 1,000 years — HubeAli "seventy thousand barriers"
    / "a thousand years". Agrees. IMPORTED.
  - `alkafi-1282`: HubeAli age contradicts the Arabic. NOT IMPORTED; stays withheld.
- For these rows Thaqalayn's own `en_sarwar` field carries a DIFFERENT report than its
  Arabic (1282/1292 show an unrelated "why we became Shi'a" report; 2782 shows a Rida
  report). Their Sarwar alignment is wrong for these rows, so HubeAli is the correct
  English. `--force_translator` in the manifest hides `en_sarwar` so the normal chooser
  picks HubeAli; all QA/publishability rules still apply.
- Coverage `15,225 / 15,336` -> `15,227 / 15,336` (`99.2893%`). Untranslated `111` -> `109`.
- `quick_check` ok, `0` fk violations, suite `351 passed`. Live: 1292 and 2782 publish as
  HubeAli; 1282 correctly returns `translation: null`.

### Bottom line on reaching 15,336

Not reachable from Thaqalayn. `86` of the remaining `109` have no verified counterpart in
their edition at any threshold, and that is edition divergence, not translator choice or
effort. The remaining honest work is human adjudication per report against the print
editions, plus review of the `25` QA-blocked rows — noting the number-check blind spot
above means those flags must be re-judged by eye, not cleared in bulk.

## Anchor-bijection recovery (Claude, 2026-07-17)

User idea, and it was the right one: stop matching each report as an isolated string and
use POSITION the way a reader would. If a report sits between two reports whose Thaqalayn
counterparts are verified, its counterpart must lie between those two — and if exactly one
unclaimed remote row sits in that span, identity follows by ELIMINATION. This is the
"one-to-one gaps bounded by direct Arabic anchors" method the 2026-07-16 session already
permitted. It is NOT number-joining: anchors are verified Arabic matches and only a strict
1:1 gap counts.

Result: `16` bijections out of the 109 then-missing; `10` passed text corroboration;
`6` correctly rejected as edition split/merge; `5` published after QA.

### Why the similarity scores were misleading

Eyeballing the candidates showed our Arabic and Thaqalayn's are often IDENTICAL apart from
a trailing space or honorific formatting (`ع` vs `( عليه السلام )`). Word-level coverage
counts those as whole tokens, which crushes the score on 4-6 word reports — `alkafi-11160`
scored 0.80 on two strings that differ only by a trailing period. Low similarity on SHORT
reports is a tokenizer artefact, not disagreement. The anchor-bijection contract therefore
lowers the textual bar (fwd/rev >= 0.60) while KEEPING the extent bar tight (ratio
0.70-1.40), because a ratio far from 1 is the real signal that the editions split the
report differently.

Data issue found, not a translation gap: `alkafi-14406`'s matn has the printed colophon
(`هَذَا آخِرُ كِتَابِ الدِّيَاتِ ...`) glued onto the hadith text. That is editorial apparatus
and should not be in `matn_raw`. Worth a targeted look for other end-of-kitab rows.

### Applied by Claude on 2026-07-17

- Backup: `eshia-research/eshia_research.before-anchor-bijection.20260717-111805.db`
  (`2,311,577,600` bytes).
- Imported `5` (all HubeAli); `2` QA-blocked; `3` below the importer's confidence floor.
- Coverage `15,227 / 15,336` -> `15,232 / 15,336` (`99.3219%`). Untranslated `109` -> `104`.
- `quick_check` ok, `0` fk violations, suite `351 passed`, live reader verified.
- Manifest: `scratch_audit/alkafi_anchor_bijection_manifest_20260717.json`.

### Where the remaining 104 stand

`80` sit in gaps that are NOT 1:1 (several local reports against several remote rows), and
`13` have no bounding anchors. Both are consequences of only `1,774` reports being
anchorable: only `thaqalayn-data` rows carry a `/books/al-kafi:` provenance path, and the
~13k `thaqalayn-api` rows do not. Recovering their remote row by exact normalised Arabic
added just `1` anchor, because the two editions' Arabic is not byte-identical.

**The highest-value next step** is fuzzy-anchoring those ~13k API rows to their static
counterparts. Every extra anchor narrows the surrounding gaps, and many of the 80 would
collapse into 1:1 bijections. That is the honest route to most of the remaining 104 —
better than loosening any threshold.

## Open Cautions

### Remaining-88 deep scan correction (Codex, 2026-07-16)

- The deeper source audit discovered that the published Muhammad Sarwar scans and the ThaqalaynData/static edition use incompatible global `H`-number sequences in affected ranges. The prior 62 `sarwar-published-scan` rows joined genuine Sarwar text to the wrong local reports by number alone.
- Corrective write scope: preserve the 62 translation/segment/job/attempt audit records but change the translations to `rejected/red`, segments and job items to `qa_failed/red`, and annotate provenance with `incompatible_edition_h_number`. The 47 static-source imports from the same batch remain untouched.
- Dry run invariant: exactly 62 translations, 62 segments, 62 job items, and 62 attempts, spanning `alkafi-11141` through `alkafi-14406` by sorted public ID.
- Backup target before correction: `eshia-research/eshia_research.before-reject-misnumbered-sarwar-scans.20260716-103847.db`.
- After correction, the honest public coverage baseline will be `15,185 / 15,335`, leaving `150`; the deep scan must rebuild the recovery set against Arabic/content crosswalks and must never join these editions by global H-number alone.
- Correction backup completed at `2,251,522,048` bytes with SHA-256 `7B695A892DEBB7379EE881D85C8B739C9BFB52F16248A7F56B39D555212C9BEE`; all 62 affected translations were marked `rejected/red` with preserved audit history.
- Reviewed recovery scope after the full 150-row scan: import exactly 26 records from `eshia-research/scratch_audit/alkafi_deep_scan_recovery_manifest_20260716.json` (manifest SHA-256 `21998b7028a02a2e67640eec3a646011db106b761f951ead0e99587d3befbcf6`). This comprises 15 unchanged/HTML-cleaned Sarwar texts, 3 transparently corrected Sarwar texts, and 8 bounded/source-aligned editorial texts; volume 8 contributes zero.
- Backup target before the 26-row recovery apply: `eshia-research/eshia_research.before-alkafi-deep-scan-recovery.20260716-104814.db`.
- Recovery backup completed at `2,251,624,448` bytes with SHA-256 `013A2039E4F500F996B63CB999057A99B680D9AC7510DF77BB0A48A62E88A84B`.
- The 26-row recovery committed atomically and reruns with `selected=0`. Two previously rejected scan-number rows (`alkafi-11167` and `alkafi-11168`) were independently recovered through the correct Arabic/content crosswalk, leaving 60 of the 62 misnumbered imports rejected.
- Final verified public coverage after correction and recovery: `15,211 / 15,335` (`99.1914%`), leaving `124`. Public source/model breakdown includes `14,184` unchanged Muhammad Sarwar rows, `3` transparently corrected Sarwar rows, `8` Sarwar-scoped/source-aligned editorial rows, and `1,016` pre-existing HubeAli rows.
- Remaining queue: `eshia-research/scratch_audit/alkafi_post_deep_scan_queue_20260716.json`; reasons are no reliable alignment `62`, ambiguous alignment `32`, no verified Sarwar volume 8 `18`, explicit source non-translation `6`, edition split/merge `5`, and English/Arabic content mismatch `1`.
- Verification: stale public source hashes `0`; forbidden markers in the 26 new rows `0`; SQLite `quick_check=ok`; foreign-key violations `0`; focused tests `50 passed, 1 warning`; API checks passed for unchanged Sarwar `alkafi-1241`, scoped editorial `alkafi-11167`, and rejected/non-public `alkafi-11141`.

- Do not use page breaks as hadith boundaries in Hadith View.
- Do not treat every `قال`, `في`, or `أن` boundary as safe.
- Do not resolve ambiguous narrator names by string match alone.
- Do not hide uncertainty in narrator resolution; store ranked candidates.
- Do not let rejected footnote/commentary fragments appear as normal hadith cards.
- After any split repair, derived chains and resolver output may be stale until rebuilt.
- Do not use broad "matn contains عن/قال" logic as a split error by itself; many valid matns contain inner dialogue or quoted reports.
