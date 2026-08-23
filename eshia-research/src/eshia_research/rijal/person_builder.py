"""Phase A of the Tamyiz Engine: bootstrap the person layer.

Builds `persons`, `person_entry_links`, `person_surface_forms`,
`person_relations` and `collective_rosters` from the already-crawled Mu'jam
entries. Deterministic — no probabilistic inference here; that arrives in
later phases. Rebuild-style: wipes and repopulates the person tables (chain
tables and rijal source tables are never touched).

Steps:

1. one person per Mu'jam entry (1:1 today; merges come later as
   `same_person_as` relations, never destructive row deletion);
2. surface-form generation via the name grammar, with corpus-wide
   shared_count so bare forms are explicitly ambiguous;
3. bare-form detection: an entry whose name is a truncation/kunya/ibn-form
   claimed by >= 2 fuller-named persons becomes kind='bare_form_proxy', and
   each fuller person gets a bare_form_evidence link to that entry;
4. father relations mined from the nasab itself (فلان بن X asserts the
   father is named X), matched to a person row only when the match is unique;
5. al-Khoei's own cross-reference rulings («متحد مع», «مشترک بین»,
   «تقدم بعنوان»...) captured as tamyiz_discussion links with quotes;
6. the 14 Ma'sumin as fixed persons with kunya/laqab surface forms
   (deliberately shared forms like «ابو جعفر» stay ambiguous until the
   tabaqat layer);
7. Kulayni's documented «عدة من أصحابنا» rosters keyed by the next narrator.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Callable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from eshia_research.models import (
    Book,
    CollectiveRoster,
    MentionResolution,
    Person,
    PersonEntryLink,
    PersonRelation,
    PersonSurfaceForm,
    RijalEntry,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.name_grammar import parse_name, surface_forms
from eshia_research.rijal.mujam_parser import MUJAM_ENTRY_KIND, MUJAM_SOURCE_BOOK_ID

PERSON_BUILDER_VERSION = "tamyiz_a1"

ProgressCallback = Callable[[str, int, int], None]


def _n(text: str) -> str:
    return normalise_arabic_persian(text)


# Derivations that make a shorter name an honest claim of a fuller name.
_BARE_CLAIM_DERIVATIONS = {"nasab_truncation", "first_name", "kunya", "ibn_form"}
# Linking every bare entry to every extender is honest but useless for
# hyper-generic names («محمد» has thousands); above this we mark the entry
# bare and record the count without materialising links.
_MAX_BARE_LINKS = 40

# Honorific suffixes as they appear (normalised) after Ma'sumin names/kunyas
# in chain tokens: «ابی عبد الله ع», «ابی عبد الله علیه السلام».
_MASUM_SUFFIXES = ("", " ع", " علیه السلام")

# (canonical Arabic name, [surface form bases]). Forms get case variants for
# kunyas (ابو/ابی/ابا) and the honorific suffixes above. Shared bases like
# «ابو جعفر» (al-Baqir AND al-Jawad) and «ابو الحسن» (al-Kazim, al-Rida,
# al-Hadi) are intentionally listed for each claimant: shared_count carries
# the ambiguity until the tabaqat layer can split them.
MASUMIN: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("النبي محمد صلى الله عليه وآله", ("النبی", "رسول الله", "النبی صلی الله علیه")),
    ("فاطمة الزهراء عليها السلام", ("فاطمة", "الزهراء")),
    ("علي بن أبي طالب أمير المؤمنين عليه السلام", ("علی", "امیر المؤمنین", "ابو الحسن")),
    ("الحسن بن علي المجتبى عليه السلام", ("الحسن", "ابو محمد")),
    ("الحسين بن علي سيد الشهداء عليه السلام", ("الحسین", "ابو عبد الله")),
    ("علي بن الحسين زين العابدين عليه السلام", ("علی بن الحسین", "زین العابدین", "السجاد")),
    ("محمد بن علي الباقر عليه السلام", ("الباقر", "ابو جعفر")),
    ("جعفر بن محمد الصادق عليه السلام", ("الصادق", "ابو عبد الله", "جعفر بن محمد")),
    ("موسى بن جعفر الكاظم عليه السلام", ("الکاظم", "ابو الحسن", "ابو ابراهیم", "العبد الصالح")),
    ("علي بن موسى الرضا عليه السلام", ("الرضا", "ابو الحسن")),
    ("محمد بن علي الجواد عليه السلام", ("الجواد", "ابو جعفر")),
    ("علي بن محمد الهادي عليه السلام", ("الهادی", "ابو الحسن")),
    ("الحسن بن علي العسكري عليه السلام", ("العسکری", "ابو محمد")),
    ("الحجة المهدي عجل الله فرجه", ("القائم", "صاحب الزمان", "الحجة")),
)

# Kulayni's documented «عدة من أصحابنا» rosters, keyed by the narrator the
# collective transmits from. Source: Allama al-Hilli, Khulasat al-Aqwal,
# reporting Kulayni's own statement; discussed in the muqaddima of Mu'jam
# Rijal al-Hadith. The Ibn Isa roster is the best attested; the other two are
# recorded at lower confidence pending verification against the crawled
# Mu'jam muqaddima text.
IDDA_COLLECTIVE = "عدة من أصحابنا"
IDDA_ROSTERS: tuple[tuple[str, int, tuple[str, ...]], ...] = (
    (
        "أحمد بن محمد بن عيسى",
        90,
        (
            "محمد بن يحيى العطار",
            "علي بن موسى بن جعفر الكميذاني",
            "داود بن كورة",
            "أحمد بن إدريس",
            "علي بن إبراهيم بن هاشم",
        ),
    ),
    (
        "أحمد بن محمد بن خالد البرقي",
        75,
        (
            "علي بن إبراهيم بن هاشم",
            "محمد بن عبد الله بن أذينة",
            "أحمد بن عبد الله بن أمية",
            "علي بن الحسين السعدآبادي",
        ),
    ),
    (
        "سهل بن زياد",
        75,
        (
            "علي بن محمد بن علان",
            "محمد بن أبي عبد الله",
            "محمد بن الحسن",
            "محمد بن عقيل الكليني",
        ),
    ),
)
IDDA_SOURCE_CITATION = (
    "Khulasat al-Aqwal (Allama al-Hilli) reporting Kulayni; "
    "Mu'jam Rijal al-Hadith muqaddima"
)

# Al-Khoei's cross-reference language inside entry text. Each match becomes a
# tamyiz_discussion link carrying the quote — machine-readable identity
# rulings from the highest authority in the corpus.
_TAMYIZ_PHRASES = tuple(
    _n(p) for p in ("متحد مع", "اتحاده مع", "مشترک بین", "تقدم بعنوان", "یاتی بعنوان")
)
_TAMYIZ_RE = re.compile("|".join(re.escape(p) for p in _TAMYIZ_PHRASES))
_TAMYIZ_QUOTE_WINDOW = 160


def _tamyiz_quotes(text_norm: str) -> list[str]:
    quotes = []
    for match in _TAMYIZ_RE.finditer(text_norm):
        window = text_norm[match.start() : match.start() + _TAMYIZ_QUOTE_WINDOW]
        quotes.append(window.strip())
    return quotes


def build_person_layer(
    db: Session, on_progress: ProgressCallback | None = None
) -> dict[str, int]:
    def progress(phase: str, done: int, total: int) -> None:
        if on_progress is not None:
            on_progress(phase, done, total)

    # Full rebuild of derived person tables only.
    for model in (
        MentionResolution,
        CollectiveRoster,
        PersonRelation,
        PersonSurfaceForm,
        PersonEntryLink,
        Person,
    ):
        db.execute(delete(model))
    db.flush()

    entries = db.execute(
        select(
            RijalEntry.id,
            RijalEntry.canonical_name_raw,
            RijalEntry.canonical_name_normalised,
            RijalEntry.text_normalised,
        )
        .join(Book, Book.id == RijalEntry.book_id)
        .where(
            Book.source_book_id == MUJAM_SOURCE_BOOK_ID,
            RijalEntry.entry_kind == MUJAM_ENTRY_KIND,
        )
    ).all()

    persons: list[dict] = []
    entry_links: list[dict] = []
    form_rows: list[dict] = []
    relations: list[dict] = []
    # form_norm -> list[(person_id, derivation)]
    form_index: defaultdict[str, list[tuple[int, str]]] = defaultdict(list)
    parsed_by_pid: dict[int, object] = {}
    entry_id_by_pid: dict[int, int] = {}

    next_pid = 1
    total = len(entries)
    for done, (entry_id, name_raw, name_norm, text_norm) in enumerate(entries, start=1):
        parsed = parse_name(name_raw)
        pid = next_pid
        next_pid += 1
        persons.append(
            {
                "id": pid,
                "canonical_name_ar": name_raw,
                "canonical_name_norm": name_norm,
                "kunya": parsed.kunya,
                "nisba": " ".join(parsed.nisba_parts) or None,
                "father_name_norm": parsed.father_norm,
                "kind": "individual",
                "origin": "mujam_entry",
                "primary_entry_id": entry_id,
            }
        )
        parsed_by_pid[pid] = parsed
        entry_id_by_pid[pid] = entry_id
        entry_links.append(
            {
                "person_id": pid,
                "entry_id": entry_id,
                "link_type": "is_subject",
                "confidence": 95,
            }
        )
        for form in surface_forms(parsed):
            form_rows.append(
                {
                    "person_id": pid,
                    "form_raw": form.form_norm,
                    "form_norm": form.form_norm,
                    "derivation": form.derivation,
                }
            )
            form_index[form.form_norm].append((pid, form.derivation))
        for quote in _tamyiz_quotes(text_norm or ""):
            entry_links.append(
                {
                    "person_id": pid,
                    "entry_id": entry_id,
                    "link_type": "tamyiz_discussion",
                    "evidence_quote": quote,
                    "confidence": 85,
                }
            )
        if done % 2000 == 0 or done == total:
            progress("parse entries", done, total)

    # Deduplicate tamyiz links (several phrases can hit one entry) while
    # keeping the first quote.
    seen_links: set[tuple[int, int, str]] = set()
    deduped_links: list[dict] = []
    for link in entry_links:
        key = (link["person_id"], link["entry_id"], link["link_type"])
        if key in seen_links:
            continue
        seen_links.add(key)
        deduped_links.append(link)
    entry_links = deduped_links

    # Ma'sumin: fixed persons with title/kunya forms + honorific suffixes.
    masum_count = 0
    for name_ar, bases in MASUMIN:
        pid = next_pid
        next_pid += 1
        masum_count += 1
        persons.append(
            {
                "id": pid,
                "canonical_name_ar": name_ar,
                "canonical_name_norm": _n(name_ar),
                "kind": "masum",
                "origin": "fixed_masum",
            }
        )
        seen_forms: set[str] = set()
        for base in bases:
            base_norm = _n(base)
            case_variants = [base_norm]
            head, _, rest = base_norm.partition(" ")
            if head == _n("ابو") and rest:
                case_variants = [f"{v} {rest}" for v in (_n("ابو"), _n("ابی"), _n("ابا"))]
            for variant in case_variants:
                for suffix in _MASUM_SUFFIXES:
                    form = f"{variant}{suffix}"
                    if form in seen_forms:
                        continue
                    seen_forms.add(form)
                    form_rows.append(
                        {
                            "person_id": pid,
                            "form_raw": form,
                            "form_norm": form,
                            "derivation": "masum_title",
                        }
                    )
                    form_index[form].append((pid, "masum_title"))

    # Corpus-wide shared_count per normalised form.
    shared_totals = {form: len({pid for pid, _ in claims}) for form, claims in form_index.items()}
    for row in form_rows:
        row["shared_count"] = shared_totals[row["form_norm"]]

    # Bare-form detection: entry name claimed as a shorter form of fuller
    # persons. The bare person keeps existing (al-Khoei made the entry) but
    # is marked a proxy, and extenders get evidence links to it.
    bare_count = 0
    bare_links = 0
    person_by_id = {p["id"]: p for p in persons}
    progress_total = len(persons)
    for done, person in enumerate(persons, start=1):
        if person.get("origin") != "mujam_entry":
            continue
        name_norm = person["canonical_name_norm"]
        extenders = [
            (pid, derivation)
            for pid, derivation in form_index.get(name_norm, [])
            if pid != person["id"]
            and derivation in _BARE_CLAIM_DERIVATIONS
            and person_by_id[pid].get("origin") == "mujam_entry"
        ]
        extender_ids = sorted({pid for pid, _ in extenders})
        if len(extender_ids) < 2:
            continue
        bare_count += 1
        person["kind"] = "bare_form_proxy"
        person["notes"] = f"bare form claimed by {len(extender_ids)} fuller-named persons"
        if len(extender_ids) <= _MAX_BARE_LINKS:
            for pid in extender_ids:
                entry_links.append(
                    {
                        "person_id": pid,
                        "entry_id": entry_id_by_pid[person["id"]],
                        "link_type": "bare_form_evidence",
                        "confidence": 60,
                    }
                )
                bare_links += 1
        if done % 4000 == 0 or done == progress_total:
            progress("bare-form detection", done, progress_total)

    # Unique-match helper, two tiers of claim strength:
    # 1. exactly one entry has this as its canonical title;
    # 2. exactly one person claims it as a *full* form (whole nasab, with or
    #    without kunya/nisba tail — «إبراهيم بن هاشم» matches the entry
    #    «إبراهيم بن هاشم أبو إسحاق القمي»).
    # Truncation claims are deliberately excluded: they are the ambiguity.
    # Non-unique at both tiers -> None; refusing to guess is the contract.
    canonical_pids: defaultdict[str, set[int]] = defaultdict(set)
    for person in persons:
        if person.get("origin") == "mujam_entry" and person["kind"] != "bare_form_proxy":
            canonical_pids[person["canonical_name_norm"]].add(person["id"])

    def unique_full_match(name_norm: str) -> int | None:
        exact = canonical_pids.get(name_norm, set())
        if len(exact) == 1:
            return next(iter(exact))
        matches = {
            pid
            for pid, derivation in form_index.get(name_norm, [])
            if derivation == "full"
            and person_by_id[pid].get("origin") == "mujam_entry"
            and person_by_id[pid]["kind"] != "bare_form_proxy"
        }
        return next(iter(matches)) if len(matches) == 1 else None

    # Father relations from the nasab. The asserted name is always kept;
    # a person row is linked only when the match is unique.
    father_links = 0
    for person in persons:
        parsed = parsed_by_pid.get(person["id"])
        if parsed is None or parsed.is_ibn_form:
            continue
        father_norm = parsed.father_norm
        if not father_norm:
            continue
        related_pid = unique_full_match(father_norm)
        if related_pid == person["id"]:
            related_pid = None
        if related_pid is not None:
            father_links += 1
        relations.append(
            {
                "person_id": person["id"],
                "related_person_id": related_pid,
                "relation_kind": "father",
                "related_name_norm": father_norm,
                "source_note": "asserted by nasab (فلان بن X)",
                "confidence": 95 if related_pid else 70,
            }
        )

    # Collective rosters, members matched to persons when unique.
    roster_rows: list[dict] = []
    for keyed_by_ar, confidence, members in IDDA_ROSTERS:
        keyed_norm = _n(keyed_by_ar)
        for member_ar in members:
            member_norm = _n(member_ar)
            roster_rows.append(
                {
                    "collective_norm": _n(IDDA_COLLECTIVE),
                    "keyed_by_norm": keyed_norm,
                    "member_person_id": unique_full_match(member_norm),
                    "member_name_ar": member_ar,
                    "member_name_norm": member_norm,
                    "source_citation": IDDA_SOURCE_CITATION,
                    "confidence": confidence,
                }
            )

    db.bulk_insert_mappings(Person, persons)
    db.bulk_insert_mappings(PersonEntryLink, entry_links)
    db.bulk_insert_mappings(PersonSurfaceForm, form_rows)
    db.bulk_insert_mappings(PersonRelation, relations)
    db.bulk_insert_mappings(CollectiveRoster, roster_rows)
    db.flush()

    # Rebuild-style person generation deletes all derived entry links. Restore
    # conservative links from locally imported source witnesses after the
    # Mu'jam identity backbone and its surface-form index exist again.
    from eshia_research.rijal.shiaresearch import link_external_rijal_entries

    external_links = link_external_rijal_entries(db)

    tamyiz_links = sum(1 for link in entry_links if link["link_type"] == "tamyiz_discussion")
    return {
        "persons": len(persons) + external_links.created,
        "masum_persons": masum_count,
        "bare_form_persons": bare_count,
        "surface_forms": len(form_rows),
        "entry_links": len(entry_links),
        "tamyiz_links": tamyiz_links,
        "bare_form_links": bare_links,
        "father_relations": len(relations),
        "father_relations_matched": father_links,
        "roster_members": len(roster_rows),
        "external_exact_links": external_links.exact,
        "external_full_form_links": external_links.full_form,
        "external_ambiguous_entries": external_links.ambiguous,
        "external_unmatched_entries": external_links.unmatched,
    }
