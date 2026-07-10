from eshia_research.normalise import normalise_arabic_persian as norm
from eshia_research.rijal.review_priors import AL_KAFI_REVIEW_PRIORS, REVIEW_PRIOR_METHODS


def test_review_prior_methods_are_unique():
    assert len(REVIEW_PRIOR_METHODS) == len(AL_KAFI_REVIEW_PRIORS)


def test_contextual_review_prior_does_not_match_without_required_neighbor():
    spec = next(rule for rule in AL_KAFI_REVIEW_PRIORS if rule.key == "father_after_ali_ibrahim")

    assert spec.matches(
        token=norm("أبيه"),
        position=1,
        previous_token=norm("علي بن إبراهيم"),
        next_token=None,
    )
    assert not spec.matches(
        token=norm("أبيه"),
        position=1,
        previous_token=norm("أحمد بن محمد"),
        next_token=None,
    )


def test_terminal_imam_prior_does_not_match_mid_chain():
    spec = next(rule for rule in AL_KAFI_REVIEW_PRIORS if rule.key == "terminal_abu_abdullah")

    assert spec.matches(
        token=norm("أبي عبد الله ع"),
        position=4,
        previous_token=norm("زرارة"),
        next_token=None,
    )
    assert not spec.matches(
        token=norm("أبي عبد الله ع"),
        position=4,
        previous_token=norm("زرارة"),
        next_token=norm("رجل"),
    )
