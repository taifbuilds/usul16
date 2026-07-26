# Al-Kafi topic taxonomy

Last rebuilt: 2026-07-23

## Coverage

Every visible Al-Kafi hadith has two structural topic assignments:

1. its broad kitab subject, and
2. its precise chapter subject.

A controlled semantic layer adds searchable moods, life situations,
practices, virtues, beliefs, and people where the source evidence supports
them. Current totals:

- 15,336 categorized hadith IDs
- 34 kitab topics
- 2,620 chapter topics
- 67 semantic topics
- 75,425 total hadith-topic assignments
- 44,753 semantic assignments
- 2 to 14 assignments per hadith (4.92 average)
- 1,209 hadiths retain only their two structural topics

The semantic layer is deliberately conservative. A hadith without a reliable
semantic trigger is not assigned a guessed label.

## Semantic evidence

Semantic assignments are generated from three reviewable sources:

- the existing Al-Kafi kitab and chapter titles,
- the preferred public English translation, with website-first versions
  taking priority, and
- normalized Arabic matn terms matched as whole words or phrases.

Each assignment records its method, confidence, taxonomy version, matched
terms, and translation version where applicable. The generated methods are
`semantic_structure`, `semantic_translation`, `semantic_arabic`, and
`semantic_multi_source`.

Labels indicate that a narration discusses or mentions a subject. They do
not state a legal ruling, authenticity judgment, or exclusive interpretation.
Ambiguous short Arabic terms are excluded when they cannot identify a topic
reliably on their own.

## Structural evidence

- 13,122 records use Arabic-verified structure matches.
- 519 records use existing interpolated structure placements.
- 1,695 edition-gap records inherit the nearest same-volume structure anchor.

Inherited placements remain distinguishable and replaceable as edition
boundary work improves.

## Product behavior

- Everyday searches such as `I feel anxious`, `hadiths about marriage`, and
  `seeking knowledge` match controlled aliases and return relevant hadiths.
- Hashtag searches such as `#prayer` use the same search box.
- Every hadith response includes its ordered topic assignments.
- `/topics` groups semantic topics by mood, life, practice, virtue, belief,
  and person, followed by the Al-Kafi kitab structure.
- `/topics/{slug}` lists co-occurring topics and paginated narrations.
- Topic chips on hadith records link back to those result pages.

## Rebuild

Apply migrations, then rebuild from `eshia-research`:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m eshia_research.cli rebuild-alkafi-topics
```

Use `--dry-run` to execute the complete rebuild and roll it back. The command
replaces generated topics from `thaqalayn-structure` and `alkafi-semantic`;
manually curated topic sources are left untouched.
