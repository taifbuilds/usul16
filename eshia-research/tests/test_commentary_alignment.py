"""Chapter-sequence alignment: the layer that reaches unquoted commentary."""

from eshia_research.commentary.alignment import (
    ChapterRun,
    align_chapters,
    propose_by_ordinal,
    title_similarity,
    _weighted_monotonic_subset,
)


def _runs(spec: list[tuple[str, list[int]]]) -> list[ChapterRun]:
    """Build runs from (title, ordinals); each unit is the string "i:ordinal"."""
    built = []
    for index, (title, ordinals) in enumerate(spec):
        built.append(
            ChapterRun(
                index=index,
                title=title,
                units_by_ordinal={o: f"{index}:{o}" for o in ordinals},
            )
        )
    return built


def _titles(spec: list[tuple[str, list[int]]]) -> list[list[str]]:
    return [title.split() for title, _ in spec]


def test_monotonic_subset_drops_backwards_anchors():
    # (source, target, weight) — the middle pair would run the alignment
    # backwards, which chapter order forbids.
    pairs = [(0, 0, 3), (1, 9, 1), (2, 1, 4), (3, 2, 2)]

    kept = _weighted_monotonic_subset(pairs)

    assert [(s, t) for s, t, _w in kept] == [(0, 0), (2, 1), (3, 2)]


def test_monotonic_subset_prefers_total_support_over_length():
    pairs = [(0, 5, 20), (1, 1, 1), (2, 2, 1)]

    kept = _weighted_monotonic_subset(pairs)

    assert [(s, t) for s, t, _w in kept] == [(0, 5)]


def test_equal_gap_between_anchors_is_carried_through_in_order():
    """The common case: both works simply continue through the same chapters."""
    source_spec = [("باب الاول", [1]), ("باب الثاني", [1, 2]), ("باب الثالث", [1])]
    target_spec = [("باب الاول", [1]), ("باب الثاني", [1, 2]), ("باب الثالث", [1])]
    source_runs, target_runs = _runs(source_spec), _runs(target_spec)

    # Only the first and last chapters are text-verified; the middle is unquoted.
    confirmed = {"0:1": (0, 1), "2:1": (2, 1)}

    links = align_chapters(
        source_runs, target_runs, confirmed, lambda unit: unit,
        source_titles=_titles(source_spec), target_titles=_titles(target_spec),
    )
    by_source = {link.source_index: link for link in links}

    assert by_source[1].target_index == 1
    assert by_source[1].method == "interpolated"
    assert by_source[0].method == "anchored"


def test_ordinal_proposals_only_where_both_sides_carry_the_number():
    """A commentary that skips a report must not shift every later report."""
    source_spec = [("باب الصدق", [1, 2, 5])]
    target_spec = [("باب الصدق", [1, 2, 3])]
    source_runs, target_runs = _runs(source_spec), _runs(target_spec)

    links = align_chapters(
        source_runs, target_runs, {"0:1": (0, 1)}, lambda unit: unit,
        source_titles=_titles(source_spec), target_titles=_titles(target_spec),
    )
    proposals = propose_by_ordinal(source_runs, target_runs, links)

    assert sorted(p.ordinal for p in proposals) == [1, 2]
    assert all(p.source_unit.split(":")[1] == p.target_unit.split(":")[1] for p in proposals)


def test_chapter_numbering_offset_is_learned_from_its_own_anchors():
    """Real case: al-Kafi's «باب البداء» runs one behind the sharh throughout.

    Assuming a zero offset would land every positional placement on the
    neighbouring report.
    """
    source_spec = [("باب البداء", [3, 4, 5, 6])]
    target_spec = [("باب البداء", [2, 3, 4, 5])]
    source_runs, target_runs = _runs(source_spec), _runs(target_spec)
    # Passages 3 and 4 were text-verified onto hadiths 2 and 3: offset -1.
    confirmed = {"0:3": (0, 2), "0:4": (0, 3)}

    links = align_chapters(
        source_runs, target_runs, confirmed, lambda unit: unit,
        source_titles=_titles(source_spec), target_titles=_titles(target_spec),
    )
    assert links[0].ordinal_delta == -1
    assert links[0].ordinal_delta_confidence == 1.0

    proposals = propose_by_ordinal(source_runs, target_runs, links)
    mapping = {p.source_unit: p.target_unit for p in proposals}

    assert mapping["0:5"] == "0:4"
    assert mapping["0:6"] == "0:5"


def test_disagreeing_anchors_lower_the_offset_confidence():
    """Anchors that contradict each other must not be averaged into a guess."""
    source_spec = [("باب مختلط", [1, 2])]
    target_spec = [("باب مختلط", [1, 2, 3])]
    source_runs, target_runs = _runs(source_spec), _runs(target_spec)
    confirmed = {"0:1": (0, 1), "0:2": (0, 3)}  # deltas 0 and +1

    links = align_chapters(
        source_runs, target_runs, confirmed, lambda unit: unit,
        source_titles=_titles(source_spec), target_titles=_titles(target_spec),
    )

    assert links[0].ordinal_delta_confidence == 0.5


def test_unequal_gap_requires_title_agreement():
    """When one side has a chapter the other lacks, position alone is not enough."""
    source_spec = [
        ("باب الاول", [1]),
        ("باب الصدق والامانة", [1]),
        ("باب الاخير", [1]),
    ]
    target_spec = [
        ("باب الاول", [1]),
        ("باب شيء اخر تماما", [1]),
        ("باب الصدق والامانة", [1]),
        ("باب الاخير", [1]),
    ]
    source_runs, target_runs = _runs(source_spec), _runs(target_spec)
    confirmed = {"0:1": (0, 1), "2:1": (3, 1)}

    links = align_chapters(
        source_runs, target_runs, confirmed, lambda unit: unit,
        source_titles=_titles(source_spec), target_titles=_titles(target_spec),
    )
    by_source = {link.source_index: link for link in links}

    # The middle source chapter matches target 2 by title, not target 1.
    assert by_source[1].target_index == 2
    assert by_source[1].title_similarity == 1.0


def test_unrelated_titles_in_an_unequal_gap_are_left_unaligned():
    source_spec = [("باب الاول", [1]), ("باب لا مثيل له هنا", [1]), ("باب الاخير", [1])]
    target_spec = [
        ("باب الاول", [1]),
        ("شيء", [1]),
        ("اخر", [1]),
        ("باب الاخير", [1]),
    ]
    source_runs, target_runs = _runs(source_spec), _runs(target_spec)
    confirmed = {"0:1": (0, 1), "2:1": (3, 1)}

    links = align_chapters(
        source_runs, target_runs, confirmed, lambda unit: unit,
        source_titles=_titles(source_spec), target_titles=_titles(target_spec),
    )

    assert 1 not in {link.source_index for link in links}


def test_title_similarity_is_symmetric_and_bounded():
    assert title_similarity(["باب", "الصدق"], ["باب", "الصدق"]) == 1.0
    assert title_similarity(["باب"], ["فصل"]) == 0.0
    assert title_similarity([], ["باب"]) == 0.0
