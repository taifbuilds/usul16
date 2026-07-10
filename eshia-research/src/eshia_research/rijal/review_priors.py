"""Conservative Al-Kafi priors learned from imported external review.

The rules in this module are deliberately exact and source-scoped. They were
selected only when a deterministic 80/20 split of the imported review batch
showed at least 95% agreement in both the training and holdout slices. The
validator is read-only and remains available so the evidence can be rerun.
"""

from __future__ import annotations

import dataclasses

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from eshia_research.corpus import AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID
from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    Hadith,
    MentionResolution,
    Person,
    PersonResolutionDecision,
    RijalEntry,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.effective_resolution import ADMIN_REVIEWER
from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION


def _n(text: str) -> str:
    return normalise_arabic_persian(text)


@dataclasses.dataclass(frozen=True)
class ReviewPriorSpec:
    key: str
    method: str
    tokens: tuple[str, ...]
    target_names: tuple[str, ...]
    target_entry_numbers: tuple[int, ...] | None = None
    previous_tokens: tuple[str, ...] | None = None
    next_tokens: tuple[str, ...] | None = None
    position: int | None = None
    minimum_position: int | None = None
    rationale: str = ""

    def matches(
        self,
        *,
        token: str,
        position: int,
        previous_token: str | None,
        next_token: str | None,
    ) -> bool:
        if token not in self.tokens:
            return False
        if self.position is not None and position != self.position:
            return False
        if self.minimum_position is not None and position < self.minimum_position:
            return False
        if self.previous_tokens is not None and previous_token not in self.previous_tokens:
            return False
        if self.next_tokens is not None and next_token not in self.next_tokens:
            return False
        return True


AL_KAFI_REVIEW_PRIORS: tuple[ReviewPriorSpec, ...] = (
    ReviewPriorSpec(
        key="opening_ali_ibrahim",
        method="kafi_opening_ali_ibrahim",
        tokens=(_n("علي بن إبراهيم"),),
        position=0,
        target_names=(_n("علي بن إبراهيم بن هاشم"),),
        rationale="The Al-Kafi chain-opening source is Ali b. Ibrahim b. Hashim.",
    ),
    ReviewPriorSpec(
        key="father_after_ali_ibrahim",
        method="kafi_review_father_after_ali_ibrahim",
        tokens=(_n("أبيه"),),
        previous_tokens=(_n("علي بن إبراهيم"),),
        target_names=(_n("إبراهيم بن هاشم أبو إسحاق القمي"),),
        rationale="Al-Kafi «علي بن إبراهيم، عن أبيه» identifies Ibrahim b. Hashim.",
    ),
    ReviewPriorSpec(
        key="ibn_abi_umayr",
        method="kafi_review_ibn_abi_umayr",
        tokens=(_n("ابن أبي عمير"),),
        target_names=(_n("محمد بن أبي عمير زياد"),),
        rationale="The Al-Kafi ibn-form consistently denotes Muhammad b. Abi Umayr.",
    ),
    ReviewPriorSpec(
        key="terminal_abu_abdullah",
        method="kafi_review_terminal_abu_abdullah",
        tokens=(_n("أبي عبد الله ع"), _n("عن أبي عبد الله ع")),
        next_tokens=(None,),
        target_names=(_n("جعفر بن محمد الصادق عليه السلام"),),
        rationale="Terminal Abu Abd Allah in the reviewed Al-Kafi chains is al-Sadiq.",
    ),
    ReviewPriorSpec(
        key="opening_ali_muhammad_before_sahl",
        method="kafi_review_opening_ali_muhammad_before_sahl",
        tokens=(_n("علي بن محمد"),),
        position=0,
        next_tokens=(_n("سهل بن زياد"),),
        target_names=(_n("علي بن محمد بن بندار"),),
        rationale="The Al-Kafi opening source before Sahl b. Ziyad is Ali b. Muhammad b. Bandar.",
    ),
    ReviewPriorSpec(
        key="father_after_ahmad_barqi",
        method="kafi_review_father_after_ahmad_barqi",
        tokens=(_n("أبيه"),),
        previous_tokens=(_n("أحمد بن محمد بن خالد"),),
        target_names=(_n("محمد بن خالد البرقي"),),
        rationale="The father of Ahmad b. Muhammad b. Khalid is Muhammad b. Khalid al-Barqi.",
    ),
    ReviewPriorSpec(
        key="abu_jamila",
        method="kafi_review_abu_jamila",
        tokens=(_n("أبي جميلة"),),
        target_names=(_n("المفضل بن صالح الأسدي النخاس"),),
        rationale="Reviewed Al-Kafi Abu Jamila mentions identify al-Mufaddal b. Salih.",
    ),
    ReviewPriorSpec(
        key="terminal_abu_al_hasan_al_rida",
        method="kafi_review_terminal_abu_al_hasan_al_rida",
        tokens=(_n("أبي الحسن الرضا ع"),),
        next_tokens=(None,),
        target_names=(_n("علي بن موسى الرضا عليه السلام"),),
        rationale="The explicit terminal title Abu al-Hasan al-Rida identifies Imam al-Rida.",
    ),
    ReviewPriorSpec(
        key="internal_sahl_ibn_ziyad",
        method="kafi_review_internal_sahl_ibn_ziyad",
        tokens=(_n("سهل بن زياد"),),
        minimum_position=1,
        target_names=(_n("سهل بن زياد"),),
        target_entry_numbers=(5639,),
        rationale="Reviewed internal Al-Kafi mentions consistently identify Sahl b. Ziyad.",
    ),
    ReviewPriorSpec(
        key="internal_zurara",
        method="kafi_review_internal_zurara",
        tokens=(_n("زرارة"),),
        minimum_position=1,
        target_names=(_n("زرارة بن أعين"),),
        rationale="Reviewed internal Zurara mentions consistently identify Zurara b. Ayan.",
    ),
    ReviewPriorSpec(
        key="opening_husayn_ibn_muhammad",
        method="kafi_review_opening_husayn_ibn_muhammad",
        tokens=(_n("الحسين بن محمد"),),
        position=0,
        target_names=(_n("الحسين بن محمد الأشعري"),),
        rationale="The reviewed Al-Kafi opening source is al-Husayn b. Muhammad al-Ashari.",
    ),
    ReviewPriorSpec(
        key="internal_abdullah_ibn_sinan",
        method="kafi_review_internal_abdullah_ibn_sinan",
        tokens=(_n("عبد الله بن سنان"),),
        minimum_position=1,
        target_names=(_n("عبد الله بن سنان"),),
        target_entry_numbers=(6916,),
        rationale="Reviewed internal mentions consistently identify Abd Allah b. Sinan.",
    ),
    ReviewPriorSpec(
        key="internal_husayn_ibn_said",
        method="kafi_review_internal_husayn_ibn_said",
        tokens=(_n("الحسين بن سعيد"),),
        minimum_position=1,
        target_names=(_n("الحسين بن سعيد الأهوازي"),),
        rationale="Reviewed internal mentions consistently identify al-Husayn b. Said al-Ahwazi.",
    ),
    ReviewPriorSpec(
        key="opening_abu_ali_al_ashari",
        method="kafi_review_opening_abu_ali_al_ashari",
        tokens=(_n("أبو علي الأشعري"),),
        position=0,
        target_names=(_n("أبو علي الأشعري"),),
        rationale="The reviewed Al-Kafi opening kunya consistently identifies Abu Ali al-Ashari.",
    ),
    ReviewPriorSpec(
        key="yunus_after_muhammad_ibn_isa",
        method="kafi_review_yunus_after_muhammad_ibn_isa",
        tokens=(_n("يونس"),),
        previous_tokens=(_n("محمد بن عيسى"),),
        target_names=(_n("يونس بن عبد الرحمن"),),
        rationale="Reviewed Muhammad b. Isa -> Yunus edges identify Yunus b. Abd al-Rahman.",
    ),
    ReviewPriorSpec(
        key="muhammad_ibn_muslim_after_al_ala",
        method="kafi_review_muhammad_ibn_muslim_after_al_ala",
        tokens=(_n("محمد بن مسلم"),),
        previous_tokens=(_n("العلاء بن رزين"),),
        target_names=(_n("محمد بن مسلم الثقفي"),),
        rationale="Reviewed al-Ala b. Razin -> Muhammad b. Muslim edges identify al-Thaqafi.",
    ),
    ReviewPriorSpec(
        key="ahmad_ibn_muhammad_between_yahya_and_known_teacher",
        method="kafi_review_ahmad_ibn_muhammad_between_yahya_and_known_teacher",
        tokens=(_n("أحمد بن محمد"),),
        previous_tokens=(_n("محمد بن يحيى"),),
        next_tokens=(_n("علي بن الحكم"), _n("محمد بن سنان")),
        target_names=(_n("أحمد بن محمد بن عيسى الأشعري القمي"),),
        rationale=(
            "Reviewed Muhammad b. Yahya -> Ahmad b. Muhammad chains before "
            "Ali b. al-Hakam or Muhammad b. Sinan identify Ibn Isa al-Ashari."
        ),
    ),
    ReviewPriorSpec(
        key="internal_hariz",
        method="kafi_review_internal_hariz",
        tokens=(_n("حريز"),),
        minimum_position=1,
        target_names=(_n("حريز بن عبد الله"),),
        rationale="Reviewed internal Hariz mentions consistently identify Hariz b. Abd Allah.",
    ),
)

REVIEW_PRIOR_METHODS = frozenset(spec.method for spec in AL_KAFI_REVIEW_PRIORS)


@dataclasses.dataclass(frozen=True)
class ReviewPriorValidation:
    key: str
    method: str
    target_person_id: int | None
    target_name: str | None
    corpus_matches: int
    current_changes: int
    train_correct: int
    train_total: int
    holdout_correct: int
    holdout_total: int
    passed: bool

    @property
    def train_accuracy(self) -> float:
        return self.train_correct / self.train_total if self.train_total else 0.0

    @property
    def holdout_accuracy(self) -> float:
        return self.holdout_correct / self.holdout_total if self.holdout_total else 0.0


def target_person_for_spec(db: Session, spec: ReviewPriorSpec) -> Person | None:
    people = db.execute(
        select(Person).where(Person.canonical_name_norm.in_(spec.target_names))
    ).scalars().all()
    if len(people) > 1 and spec.target_entry_numbers:
        people = db.execute(
            select(Person)
            .join(RijalEntry, RijalEntry.id == Person.primary_entry_id)
            .where(
                Person.canonical_name_norm.in_(spec.target_names),
                RijalEntry.entry_number.in_(spec.target_entry_numbers),
            )
        ).scalars().all()
    if len(people) != 1:
        return None
    return people[0]


def validate_review_priors(
    db: Session,
    *,
    source_book_id: str = AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
    holdout_modulo: int = 5,
    minimum_train: int = 8,
    minimum_holdout: int = 3,
    minimum_accuracy: float = 0.95,
) -> list[ReviewPriorValidation]:
    """Validate the checked-in priors against imported admin-review decisions."""
    previous = aliased(ChainNode)
    following = aliased(ChainNode)
    top = aliased(MentionResolution)
    rows = db.execute(
        select(
            ChainNode.id.label("node_id"),
            ChainNode.token_normalised.label("token"),
            ChainNode.position.label("position"),
            previous.token_normalised.label("previous_token"),
            following.token_normalised.label("next_token"),
            PersonResolutionDecision.decision_type.label("decision_type"),
            PersonResolutionDecision.selected_person_id.label("selected_person_id"),
            top.person_id.label("current_person_id"),
        )
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .join(Book, Book.id == Hadith.book_id)
        .outerjoin(
            previous,
            (previous.chain_id == ChainNode.chain_id)
            & (previous.position == ChainNode.position - 1),
        )
        .outerjoin(
            following,
            (following.chain_id == ChainNode.chain_id)
            & (following.position == ChainNode.position + 1),
        )
        .join(
            PersonResolutionDecision,
            (PersonResolutionDecision.chain_node_id == ChainNode.id)
            & (PersonResolutionDecision.reviewer == ADMIN_REVIEWER)
            & (PersonResolutionDecision.resolver_version == PERSON_RESOLVER_VERSION),
        )
        .outerjoin(
            top,
            (top.chain_node_id == ChainNode.id)
            & (top.resolver_version == PERSON_RESOLVER_VERSION)
            & (top.rank == 1),
        )
        .where(Book.source_book_id == source_book_id)
    ).all()

    corpus_rows = db.execute(
        select(
            ChainNode.id.label("node_id"),
            ChainNode.token_normalised.label("token"),
            ChainNode.position.label("position"),
            previous.token_normalised.label("previous_token"),
            following.token_normalised.label("next_token"),
            top.person_id.label("current_person_id"),
        )
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .join(Book, Book.id == Hadith.book_id)
        .outerjoin(
            previous,
            (previous.chain_id == ChainNode.chain_id)
            & (previous.position == ChainNode.position - 1),
        )
        .outerjoin(
            following,
            (following.chain_id == ChainNode.chain_id)
            & (following.position == ChainNode.position + 1),
        )
        .outerjoin(
            top,
            (top.chain_node_id == ChainNode.id)
            & (top.resolver_version == PERSON_RESOLVER_VERSION)
            & (top.rank == 1),
        )
        .where(Book.source_book_id == source_book_id)
    ).all()

    results: list[ReviewPriorValidation] = []
    for spec in AL_KAFI_REVIEW_PRIORS:
        target = target_person_for_spec(db, spec)
        reviewed = [
            row
            for row in rows
            if spec.matches(
                token=row.token,
                position=row.position,
                previous_token=row.previous_token,
                next_token=row.next_token,
            )
        ]
        corpus = [
            row
            for row in corpus_rows
            if spec.matches(
                token=row.token,
                position=row.position,
                previous_token=row.previous_token,
                next_token=row.next_token,
            )
        ]
        train = [row for row in reviewed if row.node_id % holdout_modulo != 0]
        holdout = [row for row in reviewed if row.node_id % holdout_modulo == 0]

        def correct(row) -> bool:
            return bool(
                target is not None
                and row.decision_type in {"approve_external_override", "approve_current"}
                and row.selected_person_id == target.id
            )

        train_correct = sum(correct(row) for row in train)
        holdout_correct = sum(correct(row) for row in holdout)
        train_accuracy = train_correct / len(train) if train else 0.0
        holdout_accuracy = holdout_correct / len(holdout) if holdout else 0.0
        passed = bool(
            target is not None
            and len(train) >= minimum_train
            and len(holdout) >= minimum_holdout
            and train_accuracy >= minimum_accuracy
            and holdout_accuracy >= minimum_accuracy
        )
        results.append(
            ReviewPriorValidation(
                key=spec.key,
                method=spec.method,
                target_person_id=target.id if target else None,
                target_name=target.canonical_name_ar if target else None,
                corpus_matches=len(corpus),
                current_changes=sum(
                    target is not None and row.current_person_id != target.id for row in corpus
                ),
                train_correct=train_correct,
                train_total=len(train),
                holdout_correct=holdout_correct,
                holdout_total=len(holdout),
                passed=passed,
            )
        )
    return results


def format_review_prior_validation(results: list[ReviewPriorValidation]) -> str:
    lines = ["Al-Kafi external-review prior validation", ""]
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        lines.extend(
            [
                f"[{status}] {result.key} -> {result.target_name or 'missing target'}",
                (
                    f"  train {result.train_correct}/{result.train_total} "
                    f"({result.train_accuracy:.1%}); holdout "
                    f"{result.holdout_correct}/{result.holdout_total} "
                    f"({result.holdout_accuracy:.1%})"
                ),
                (
                    f"  corpus matches {result.corpus_matches}; "
                    f"current rank-1 changes {result.current_changes}"
                ),
            ]
        )
    return "\n".join(lines)
