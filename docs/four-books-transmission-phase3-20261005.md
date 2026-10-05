# Phase 3 — Four Books transmission completion

Date: 2026-10-05

## Outcome

Tahdhīb al-aḥkām (`10083`) and al-Istibṣār (`11002`) now have the same
source-preserving transmission workflow as al-Kāfī and al-Faqīh. Their literal
chains remain authoritative, their shared al-Ṭūsī Mashyakha is stored as a
separate witness, unsafe chains remain review-only, and both collections pass
the independent graph publication gates.

## Shared al-Ṭūsī Mashyakha

Al-Ṭūsī explains that the abbreviated reports begin with the owner of the book
or original and that his routes to those works are supplied after the book
([al-Istibṣār 4:305](https://lib.eshia.ir/11002/4/305)). The preserved appendix
runs through [4:343](https://lib.eshia.ir/11002/4/343) and applies to both
Tahdhīb and Istibṣār.

The importer found 46 source entries and 37 distinct target forms. Each path
stores its exact source segment, URL, SHA-256, parsed target forms, parser
version, and review status. Parsed path components are transcription aids only:
they are never inserted into `chain_nodes` and never become graph edges.

### Tahdhīb proposal coverage

| Measure | Count |
|---|---:|
| literal chains examined | 15,159 |
| openings with any Mashyakha witness | 8,961 |
| exact matches | 5,292 |
| canonical orthographic matches | 15 |
| unique name extensions | 3,086 |
| ism/nisba elisions | 43 |
| partial-name cases | 525 |
| openings without a source witness | 6,198 |
| proposal rows | 20,522 |
| single-witness proposals | 5,337 |
| ranked review candidates | 15,185 |

### Istibṣār proposal coverage

| Measure | Count |
|---|---:|
| literal chains examined | 6,196 |
| openings with any Mashyakha witness | 4,255 |
| exact matches | 2,738 |
| canonical orthographic matches | 7 |
| unique name extensions | 1,322 |
| ism/nisba elisions | 18 |
| partial-name cases | 170 |
| openings without a source witness | 1,941 |
| proposal rows | 9,537 |
| single-witness proposals | 2,510 |
| ranked review candidates | 7,027 |

A strong name-match tier is not automatically a proposal when the appendix
contains more than one route for that target. Those alternatives remain ranked
review candidates rather than being collapsed to a winner. Immediate import and
materialization reruns created and removed zero rows.

## Retained-chain review

The [readable review](tusi-chain-review-20261005.md) covers all 56 chains carrying
`suspicious_token`; the adjacent
[JSON ledger](tusi-chain-review-20261005.json) records the complete literal isnad,
source URL, token list, flags, classification, disposition, and rationale for
every suspicious or multi-route chain.

- suspicious chains: 46 Tahdhīb and 10 Istibṣār;
- 52 contain parser-boundary spill and remain review-only;
- 4 contain preserved page/editorial contamination and remain review-only;
- multi-route chains classified: 275 Tahdhīb and 106 Istibṣār;
- no multi-route text was flattened into a fabricated linear chain.

## Rebuild and collection gates

The person, same-person, resolution, ṭabaqāt, compiler-prior, Imam-prior and
al-Ṭūsī context layers were rebuilt in dependency order. The scoped context pass
resolved 6,566 cases and expanded 7 collective-roster rows; its immediate rerun
resolved and expanded zero.

| Book | Nodes | Resolved | Ambiguous | Bare-form leaks | Reliable generation violations | Mu'jam corroboration floor |
|---|---:|---:|---:|---:|---:|---:|
| Al-Kāfī (`11005`) | 88,379 | 54,474 | 23,729 | 0 | 0 / 128 | 58.0% |
| Al-Faqīh (`11021`) | 9,020 | 5,921 | 2,415 | 0 | 0 / 44 | 77.5% |
| Tahdhīb (`10083`) | 74,644 | 35,483 | 26,555 | 0 | 0 / 103 | 79.9% |
| Al-Istibṣār (`11002`) | 30,847 | 15,265 | 11,131 | 0 | 0 / 33 | 77.2% |

Tahdhīb and Istibṣār are now included independently in
`POLISHED_TRANSMISSION_BOOK_IDS`. The graph UI exposes both collections as
separate filters and its collection-maturity copy states their remaining reader
coverage limitations.

## Integrity and validation

- SQLite `quick_check`: `ok`
- foreign-key violations: 0
- source pages changed, added, or removed: 0
- literal chains changed, added, or removed: 0
- dangling Mashyakha paths or chain proposals: 0
- dangling resolution nodes or persons: 0
- backend: 585 tests passed, 10 known warnings
- frontend: Next.js 16.2.9 production build passed compilation, TypeScript, and
  static page generation

Rollback copy:
`eshia-research/eshia_research.before-phase3-transmission.20261005.db`

- size: 6,671,761,408 bytes
- SHA-256: `BF11C0CC9C0BD41EFCAD490E09DD726460843821D22F8CCC26995F5D733ACF72`

The rebuilt database and rollback copy are ignored local artifacts. Database
publication remains a separate operation from merging the code.
