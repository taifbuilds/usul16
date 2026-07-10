from eshia_research.hadith_split_repair import propose_missing_isnad_split


def test_missing_isnad_repair_splits_fi_hadith_topic():
    proposal, reason = propose_missing_isnad_split(
        "علي بن إبراهيم عن أبيه عن عباس بن عمرو عن هشام بن الحكم "
        "في حديث الزنديق الذي أتى أبا عبد الله ع لا يخلو قولك."
    )

    assert proposal is not None
    assert reason == "fi_topic"
    assert proposal.isnad_raw == "علي بن إبراهيم عن أبيه عن عباس بن عمرو عن هشام بن الحكم"
    assert proposal.matn_raw.startswith("في حديث الزنديق")


def test_missing_isnad_repair_consumes_terminal_yaqul():
    proposal, reason = propose_missing_isnad_split(
        "علي بن محمد عن سهل بن زياد عن هشام بن سالم قالوا سمعنا أبا عبد الله ع يقول "
        "حديثي حديث أبي."
    )

    assert proposal is not None
    assert reason == "terminal_marker"
    assert proposal.isnad_raw.endswith("أبا عبد الله ع يقول")
    assert proposal.matn_raw == "حديثي حديث أبي."


def test_missing_isnad_repair_splits_pre_terminal_an_report():
    proposal, reason = propose_missing_isnad_split(
        "محمد بن يحيى عن سعد بن عبد الله عن محمد بن عيسى عن أيوب بن نوح "
        "أنه كتب إلى أبي الحسن ع يسأله عن الله."
    )

    assert proposal is not None
    assert reason == "an_report"
    assert proposal.isnad_raw.endswith("أيوب بن نوح")
    assert proposal.matn_raw.startswith("أنه كتب")


def test_missing_isnad_repair_skips_commentary_fragment():
    proposal, reason = propose_missing_isnad_split(
        "قوله: في هذا الموضع شرح من المحقق ثم تكملة مقطوعة."
    )

    assert proposal is None
    assert reason == "skip_commentary"


def test_missing_isnad_repair_skips_continuation_fragment():
    proposal, reason = propose_missing_isnad_split(
        "قال: و قال رجل لأبي جعفر ع يا ابن رسول الله لا تغضب علي."
    )

    assert proposal is None
    assert reason == "skip_continuation"
