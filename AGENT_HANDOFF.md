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

## Near-Term Plan

1. Execute Tamyiz Engine phases A-E (above). Phase A DONE (person layer), Phase B DONE
   (reference calculus), Phase C DONE (tabaqat lattice + generation disambiguation).
   Phase D Al-Kafi compiler prior + global context/EM convergence DONE.
   Same-person identity links from al-Khoei tamyiz DONE. Machine-admin review
   decisions + external-review packet export DONE. Next is applying verified
   outside-review responses back into machine decision records, then cautious
   override/amend logic for only high-confidence externally verified cases.
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

## Open Cautions

- Do not use page breaks as hadith boundaries in Hadith View.
- Do not treat every `قال`, `في`, or `أن` boundary as safe.
- Do not resolve ambiguous narrator names by string match alone.
- Do not hide uncertainty in narrator resolution; store ranked candidates.
- Do not let rejected footnote/commentary fragments appear as normal hadith cards.
- After any split repair, derived chains and resolver output may be stale until rebuilt.
- Do not use broad "matn contains عن/قال" logic as a split error by itself; many valid matns contain inner dialogue or quoted reports.
