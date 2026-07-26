# English Translation Style Guide

Version: `matn_en_v1`

Arabic is the authority. English is a reader aid with explicit provenance, source hashes, QA status, and review history.

## Register

- Use faithful scholarly English, not paraphrase.
- Preserve ambiguity when the Arabic is ambiguous.
- Do not add theological explanation inside the translation. Put explanations in notes later.
- Use bracketed words only when English grammar requires supplied material.
- Preserve Quran quotations as detected spans until an approved Quran translation policy is chosen.

## Names And Chains

- Render isnad transmission formulae deterministically where the chain topology is reviewed.
- Use curated English/transliterated names when available.
- When no curated rendering exists, preserve the exact Arabic name and flag it for glossary/transliteration review.
- Do not ask a model to reinterpret complex route topology. Complex chains stay marked as reviewed complex or review required.

## Terminology

- Store preferred terms in `translation_glossary`.
- Retrieve only terms that actually occur in the source segment.
- QA should flag missed glossary terms, but a reviewer can override when context requires.

## Publishing Gate

A translation may be published only when:

- Rendered Thaqalayn website English is preferred where a current,
  Arabic-verified one-to-one relation exists.
- API-derived English remains a fallback and provenance record; it must not
  outrank an eligible `thaqalayn_website_v1` row.
- the stored source hashes match the current Arabic row;
- all segments exist and are current;
- deterministic QA has no red flags;
- model/provider/prompt/glossary versions are stored;
- high-risk amber cases are reviewed or explicitly queued.
