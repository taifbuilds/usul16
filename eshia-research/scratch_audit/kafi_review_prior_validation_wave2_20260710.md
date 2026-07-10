# Al-Kafi Review-Prior Validation — Wave 2

Date: 2026-07-10

The second wave uses the same deterministic 80/20 holdout contract as wave 1:
`chain_node_id % 5`, at least 8 training cases, at least 3 holdout cases, and
at least 95% agreement in both. Every selected rule achieved 100% agreement.

| Rule | Reviewed agreement | Corpus matches | Current external-review queue |
|---|---:|---:|---:|
| internal Sahl b. Ziyad | 239/239 | 1,375 | 1,366 |
| internal Zurara | 95/95 | 714 | 714 |
| opening al-Husayn b. Muhammad | 246/246 | 656 | 656 |
| internal Abd Allah b. Sinan | 95/95 | 467 | 467 |
| internal al-Husayn b. Said | 63/63 | 604 | 374 |
| opening Abu Ali al-Ashari | 33/33 | 657 | 171 |
| Yunus after Muhammad b. Isa | 97/97 | 284 | 283 |
| Muhammad b. Muslim after al-Ala | 15/15 | 163 | 163 |
| Ahmad b. Muhammad between Muhammad b. Yahya and a bounded teacher set | 60/60 | 405 | 405 |
| internal Hariz | 13/13 | 378 | 158 |

Rules use exact normalized surfaces plus position/neighbor constraints where
the surface alone is not sufficiently specific. Duplicate exact Mu'jam titles
for Sahl b. Ziyad and Abd Allah b. Sinan are pinned by stable Mu'jam entry
numbers 5639 and 6916, respectively.

Generation calibration correction: `person_generations.method='conflict'`
means the generation inference itself is unresolved. These rows are no longer
used as hard chronological evidence in machine review, the eval harness, or the
graph quality overlay. Reliable anchored/propagated generations still produce
hard flags. This corrects an audit-classification bug; it does not edit any
generation row.

Transactional combined simulation:

```text
rank-1 rows resolved or evidence-upgraded: 9,579
resolved coverage: 57,298 -> 60,185 (65.3% -> 68.6%)
machine approve_current: 44,431 -> 54,092
machine needs_external_review: 37,215 -> 32,663
machine flag_contradiction: 6,101 -> 992
reliable generation violations: 496 / 4,245 checkable edges
bare-form leaks: 0
```

The exact-match Mu'jam floor becomes 11,222 corroborated / 7,022 contradicted
because newly confident identities make 2,170 additional edges judgeable. The
external-review agreement is unanimous; this floor remains a triage signal,
not a veto, especially for well-known but incompletely extracted occurrence
lists such as Sahl b. Ziyad.
