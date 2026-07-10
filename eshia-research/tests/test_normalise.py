from eshia_research.normalise import (
    normalise_alif,
    normalise_arabic_persian,
    normalise_kaf,
    normalise_whitespace,
    normalise_yeh,
    strip_diacritics,
)


def test_strip_diacritics_removes_tashkil():
    assert strip_diacritics("الْحَمْدُ لِلَّهِ") == "الحمد لله"


def test_normalise_yeh_unifies_arabic_and_persian_yeh():
    assert normalise_yeh("علي") == "علی"
    assert normalise_yeh("علی") == "علی"


def test_normalise_kaf_unifies_arabic_and_persian_kaf():
    assert normalise_kaf("كتاب") == "کتاب"
    assert normalise_kaf("کتاب") == "کتاب"


def test_normalise_alif_collapses_hamza_and_madda_variants():
    assert normalise_alif("أحمد") == "احمد"
    assert normalise_alif("إحسان") == "احسان"
    assert normalise_alif("آمين") == "امين"


def test_normalise_whitespace_collapses_runs_and_strips():
    assert normalise_whitespace("  a   b\n\tc  ") == "a b c"


def test_normalise_arabic_persian_full_pipeline():
    raw = "  الْكَافِي ، يَا أَخِي  "
    result = normalise_arabic_persian(raw)
    assert result == "الکافی ، یا اخی"


def test_normalise_arabic_persian_preserves_non_arabic_text():
    assert normalise_arabic_persian("Hello world") == "Hello world"


def test_normalise_is_idempotent():
    raw = "الكافي"
    once = normalise_arabic_persian(raw)
    twice = normalise_arabic_persian(once)
    assert once == twice
