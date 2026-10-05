# Mu'jam volume-boundary repair audit

Date: 2026-10-05

Source work: Mu'jam Rijal al-Hadith (`source_book_id=14036`)

Parser: `mujam_v2`

## Finding and repair rule

The final numbered biography in each of volumes 1–23 was bounded by the next
accepted numbered heading, which occurs in the following volume. This attached
the intervening `تفصيل طبقات الرواة` occurrence appendix to one narrator and
created 23 impossible ledgers of roughly 1,200–2,600 rows each.

The repaired parser looks for the appendix heading during a cross-volume
transition, preserves any genuine continuation pages after the biography's
opening page, removes only printed blank placeholders immediately before the
appendix, and ends the biography before the appendix. Every repaired entry is
marked `volume_appendix_boundary`.

## Repaired ledger register

The “old end” is the next volume's first numbered-entry page. The “new end” is
the last page retained as biography text. The final citation in each row is the
source page on which the appendix heading establishes the boundary.

| Entry | Narrator | Old end | New end | Source evidence |
|---:|---|---:|---:|---|
| 380 | أحكم «أحلم» بن بشار المروزي | v2 p9 | v1 p335 | [entry](https://lib.eshia.ir/14036/1/335) · [appendix v1 p337](https://lib.eshia.ir/14036/1/337) |
| 780 | أحمد بن محمد | v3 p9 | v2 p248 | [entry](https://lib.eshia.ir/14036/2/207) · [appendix v2 p255](https://lib.eshia.ir/14036/2/255) |
| 1264 | أسماء بن حارثة | v4 p9 | v3 p252 | [entry](https://lib.eshia.ir/14036/3/252) · [appendix v3 p259](https://lib.eshia.ir/14036/3/259) |
| 2107 | جعفة | v5 p9 | v4 p365 | [entry](https://lib.eshia.ir/14036/4/365) · [appendix v4 p373](https://lib.eshia.ir/14036/4/373) |
| 2930 | الحسن بن علوية | v6 p8 | v5 p376 | [entry](https://lib.eshia.ir/14036/5/376) · [appendix v5 p383](https://lib.eshia.ir/14036/5/383) |
| 3452 | الحسين بن ظريف | v7 p8 | v6 p299 | [entry](https://lib.eshia.ir/14036/6/299) · [appendix v6 p307](https://lib.eshia.ir/14036/6/307) |
| 4148 | حيدرة بن أسامة | v8 p9 | v7 p333 | [entry](https://lib.eshia.ir/14036/7/333) · [appendix v7 p341](https://lib.eshia.ir/14036/7/341) |
| 4924 | زين العابدين بن نور الدين | v9 p9 | v8 p395 | [entry](https://lib.eshia.ir/14036/8/394) · [appendix v8 p403](https://lib.eshia.ir/14036/8/403) |
| 5677 | سيف النبي | v10 p9 | v9 p390 | [entry](https://lib.eshia.ir/14036/9/390) · [appendix v9 p397](https://lib.eshia.ir/14036/9/397) |
| 6486 | عبد الرحمن الهاشمي | v11 p8 | v10 p387 | [entry](https://lib.eshia.ir/14036/10/387) · [appendix v10 p395](https://lib.eshia.ir/14036/10/395) |
| 7275 | عبد الله الهاشمي | v12 p8 | v11 p418 | [entry](https://lib.eshia.ir/14036/11/418) · [appendix v11 p425](https://lib.eshia.ir/14036/11/425) |
| 8115 | علي بن حنظلة | v13 p9 | v12 p431 | [entry](https://lib.eshia.ir/14036/12/429) · [appendix v12 p439](https://lib.eshia.ir/14036/12/439) |
| 8687 | عمارة بن مهاجر | v14 p9 | v13 p294 | [entry](https://lib.eshia.ir/14036/13/294) · [appendix v13 p301](https://lib.eshia.ir/14036/13/301) |
| 9487 | فيهس | v15 p9 | v14 p373 | [entry](https://lib.eshia.ir/14036/14/373) · [appendix v14 p381](https://lib.eshia.ir/14036/14/381) |
| 10133 | محمد بن أحمد بن الصلت القمي | v16 p8 | v15 p351 | [entry](https://lib.eshia.ir/14036/15/351) · [appendix v15 p359](https://lib.eshia.ir/14036/15/359) |
| 10581 | محمد بن الحسين بن أبي الخطاب | v17 p9 | v16 p317 | [entry](https://lib.eshia.ir/14036/16/308) · [appendix v16 p325](https://lib.eshia.ir/14036/16/325) |
| 11358 | محمد بن علي بن متيل | v18 p9 | v17 p364 | [entry](https://lib.eshia.ir/14036/17/364) · [appendix v17 p371](https://lib.eshia.ir/14036/17/371) |
| 12004 | محمد بن ياسين | v19 p8 | v18 p346 | [entry](https://lib.eshia.ir/14036/18/346) · [appendix v18 p353](https://lib.eshia.ir/14036/18/353) |
| 12718 | منصور الصيقل | v20 p8 | v19 p386 | [entry](https://lib.eshia.ir/14036/19/384) · [appendix v19 p393](https://lib.eshia.ir/14036/19/393) |
| 13437 | الهيثم النهدي | v21 p9 | v20 p359 | [entry](https://lib.eshia.ir/14036/20/358) · [appendix v20 p367](https://lib.eshia.ir/14036/20/367) |
| 13882 | يونس النسباني | v22 p8 | v21 p250 | [entry](https://lib.eshia.ir/14036/21/250) · [appendix v21 p259](https://lib.eshia.ir/14036/21/259) |
| 14684 | أبو عيينة الرومي | v23 p8 | v22 p293 | [entry](https://lib.eshia.ir/14036/22/293) · [appendix v22 p301](https://lib.eshia.ir/14036/22/301) |
| 15158 | ابن الغضائري | v24 p8 | v23 p213 | [entry](https://lib.eshia.ir/14036/23/213) · [appendix v23 p221](https://lib.eshia.ir/14036/23/221) |

## Rehearsal and applied rebuild

The full operation first ran on
`eshia_research.phase2-mujam-disposable.20261005.db`. The accepted sequence was
then repeated on the main local research database:

1. rebuild Mu'jam entries, aliases, statements, and occurrence notes;
2. rebuild the person layer and materialize same-person links;
3. resolve people;
4. rebuild and refine ṭabaqāt;
5. apply compiler and Imam priors;
6. run collective context for Tahdhīb (`10083`) and Istibṣār (`11002`);
7. immediately repeat step 6 as an idempotence check.

Both runs produced the same principal counts:

| Output | Result |
|---|---:|
| Mu'jam numbered entries | 15,593 |
| Mu'jam pages represented | 11,095 |
| aliases | 588 |
| source statements | 12,017 |
| occurrence notes, before | 53,745 |
| occurrence notes, after | 12,807 |
| repaired boundary flags | 23 |
| largest occurrence ledger after repair | 24 |
| occurrence ledgers over 200 after repair | 0 |
| persons | 16,976 |
| surface forms | 60,739 |
| entry links | 25,848 |
| mention-resolution rows | 622,037 |
| persons constrained by ṭabaqāt | 6,524 |

The context pass examined 44,252 ambiguous Tahdhīb/Istibṣār nodes and resolved
6,566: 4,128 by collective context, 2,205 by source-opening consensus, and 233
by the narrow al-Ṭūsī opening rule. It expanded 2 collective nodes into 7 roster
rows. The immediate rerun resolved 0 nodes and expanded 0 rows.

## Evaluation after repair

| Book | Nodes | Resolved | Ambiguous | Bare-form leaks | Reliable generation violations | Mu'jam corroboration floor |
|---|---:|---:|---:|---:|---:|---:|
| Al-Kāfī (`11005`) | 88,379 | 54,474 | 23,729 | 0 | 0 / 128 | 58.0% |
| Man lā yaḥḍuruhu al-Faqīh (`11021`) | 9,020 | 5,921 | 2,415 | 0 | 0 / 44 | 77.5% |
| Tahdhīb al-aḥkām (`10083`) | 74,644 | 35,483 | 26,555 | 0 | 0 / 103 | 79.9% |
| Al-Istibṣār (`11002`) | 30,847 | 15,265 | 11,131 | 0 | 0 / 33 | 77.2% |

Tahdhīb gained 35 resolved mentions and Istibṣār gained 16 against the previous
baseline. Their corroboration floors decreased from 83.0% and 80.5% because the
old figures admitted occurrence rows copied from volume appendices into the
wrong narrator. The repaired figures are the source-faithful baseline.

## Integrity, validation, and rollback

- SQLite `quick_check`: `ok`
- SQLite foreign-key check: 0 violations
- source `pages`: 119,133 before and after; 0 changed, added, or removed
- source-derived Mu'jam entry payloads changed: exactly 23
- 135 additional `rijal_entries.narrator_id` values were remapped by the
  downstream person-layer rebuild; these are derived links, not source payload
- dangling resolution nodes, resolution persons, entry links, and generation
  persons: 0
- backend: 578 tests passed, 10 known warnings
- frontend: Next.js 16.2.9 production build passed compilation, TypeScript, and
  static page generation

Rollback copy:
`eshia-research/eshia_research.before-mujam-boundary-repair.20261005.db`

- size: 6,671,761,408 bytes
- SHA-256: `072AC2E2B50550357EDB08E618626E43CB57E78D07333E763F17E797744168BD`

The repaired database and rollback copy are local ignored artifacts. This audit
does not deploy or replace the production database.
