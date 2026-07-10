# Al-Kafi External-Review Prior Validation

Date: 2026-07-10

Method: deterministic 80/20 split by `chain_node_id % 5`, evaluated against
the 10,031 imported admin-review decisions. A checked-in prior must have at
least 8 training cases, 3 holdout cases, and 95% agreement in both slices.
All selected rules passed at 100% in both slices.

| Rule | Train | Holdout | Corpus matches | Rank-1 changes |
|---|---:|---:|---:|---:|
| opening Ali b. Ibrahim -> Ali b. Ibrahim b. Hashim | 67/67 | 20/20 | 4,516 | 578 |
| `abihi` after Ali b. Ibrahim -> Ibrahim b. Hashim | 436/436 | 131/131 | 3,680 | 3,680 |
| Ibn Abi Umayr -> Muhammad b. Abi Umayr | 324/324 | 67/67 | 2,535 | 2,535 |
| terminal Abu Abd Allah -> Imam al-Sadiq | 256/256 | 58/58 | 5,666 | 1,809 |
| opening Ali b. Muhammad before Sahl -> Ibn Bandar | 61/61 | 17/17 | 159 | 159 |
| `abihi` after Ahmad al-Barqi -> Muhammad b. Khalid | 39/39 | 7/7 | 104 | 104 |
| Abu Jamila -> al-Mufaddal b. Salih | 27/27 | 4/4 | 133 | 133 |
| terminal Abu al-Hasan al-Rida -> Imam al-Rida | 18/18 | 5/5 | 106 | 106 |

Read-only command:

```powershell
$env:PYTHONPATH='src'
python -m eshia_research.cli validate-review-priors --source-book-id 11005
```

Resolver dry run:

```text
examined 25,182 target nodes
resolved 9,108
  9,104 validated review-prior corrections
  4 opening-anaphora refreshes
```

No source hadith text, chain token, person ontology, or admin-review evidence is
edited by this pass. Existing ranked candidates are retained as alternatives.
