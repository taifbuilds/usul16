"""Tokenizer tests against real isnads from the Four Books (eShia text)."""

from eshia_research.isnad.tokenizer import (
    COLLECTIVE,
    IMAM,
    NAMED,
    PRONOUN,
    tokenize_isnad,
)
from eshia_research.normalise import normalise_arabic_persian


def types(chain):
    return [t.node_type for t in chain.tokens]


def test_simple_kafi_chain():
    raw = (
        "عَلِيُّ بْنُ مُحَمَّدٍ عَنْ سَهْلِ بْنِ زِيَادٍ عَنْ عَمْرِو بْنِ عُثْمَانَ "
        "عَنْ مُفَضَّلِ بْنِ صَالِحٍ عَنْ سَعْدِ بْنِ طَرِيفٍ‌[4] عَنِ الْأَصْبَغِ بْنِ "
        "نُبَاتَةَ عَنْ عَلِيٍّ ع قَالَ:"
    )
    chains = tokenize_isnad(raw)
    assert len(chains) == 1
    chain = chains[0]
    assert len(chain.tokens) == 7
    assert types(chain) == [NAMED] * 6 + [IMAM]
    assert not chain.needs_review
    # Footnote marker stripped from the token.
    assert "[" not in chain.tokens[4].norm


def test_idda_collective_kept_whole():
    raw = (
        "عِدَّةٌ مِنْ أَصْحَابِنَا عَنْ أَحْمَدَ بْنِ مُحَمَّدِ بْنِ خَالِدٍ عَنِ "
        "الْحَسَنِ بْنِ عَلِيِّ بْنِ يَقْطِينٍ عَنْ مُحَمَّدِ بْنِ سِنَانٍ عَنْ أَبِي "
        "الْجَارُودِ عَنْ أَبِي جَعْفَرٍ ع قَالَ:"
    )
    chains = tokenize_isnad(raw)
    assert len(chains) == 1
    chain = chains[0]
    assert chain.tokens[0].node_type == COLLECTIVE
    assert chain.tokens[-1].node_type == IMAM
    assert not chain.needs_review


def test_idda_with_minhum_member_list_stays_one_token():
    raw = (
        "أَخْبَرَنَا[1] أَبُو جَعْفَرٍ مُحَمَّدُ بْنُ يَعْقُوبَ قَالَ حَدَّثَنِي "
        "عِدَّةٌ مِنْ أَصْحَابِنَا مِنْهُمْ مُحَمَّدُ بْنُ يَحْيَى الْعَطَّارُ عَنْ "
        "أَحْمَدَ بْنِ مُحَمَّدٍ عَنِ الْحَسَنِ بْنِ مَحْبُوبٍ عَنِ الْعَلَاءِ بْنِ "
        "رَزِينٍ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ:"
    )
    chains = tokenize_isnad(raw)
    assert len(chains) == 1
    chain = chains[0]
    # Kulayni himself, then the collective (with منهم list inside), then chain.
    assert chain.tokens[0].node_type == NAMED
    assert "يعقوب" in chain.tokens[0].norm.replace("ی", "ي")
    assert chain.tokens[1].node_type == COLLECTIVE
    assert chain.tokens[-1].node_type == IMAM


def test_an_abihi_is_pronoun_relation_not_a_name():
    raw = (
        "عَلِيُّ بْنُ إِبْرَاهِيمَ عَنْ أَبِيهِ عَنِ النَّوْفَلِيِّ عَنِ "
        "السَّكُونِيِّ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ"
    )
    chains = tokenize_isnad(raw)
    chain = chains[0]
    assert types(chain) == [NAMED, PRONOUN, NAMED, NAMED, IMAM]
    assert chain.tokens[1].relation_kind == "father"


def test_anhu_anaphora_chain():
    raw = (
        "وَ عَنْهُ عَنْ أَحْمَدَ بْنِ مُحَمَّدٍ عَنِ ابْنِ فَضَّالٍ عَنِ "
        "الْحَسَنِ بْنِ الْجَهْمِ قَالَ:"
    )
    chains = tokenize_isnad(raw)
    chain = chains[0]
    assert chain.tokens[0].node_type == PRONOUN
    assert chain.tokens[0].relation_kind == "anaphora"
    assert "no_imam_terminal" in chain.flags
    assert not chain.needs_review  # legitimately ends at a narrator


def test_father_and_grandfather_sequence():
    raw = (
        "عنه عن محمد بن الحسين عن محمد بن عبد الله بن زرارة عن عيسى بن عبد الله "
        "عن أبيه عن جده عن علي عليه‌السلام قال"
    )
    chains = tokenize_isnad(raw)
    chain = chains[0]
    kinds = [t.relation_kind for t in chain.tokens if t.node_type == PRONOUN]
    assert kinds == ["anaphora", "father", "grandfather"]
    assert chain.tokens[-1].node_type == IMAM


def test_tahdhib_shaykh_opening_and_matn_spill_imam_recovery():
    raw = (
        "ما أخبرني به الشيخ أيده الله تعالى عن أحمد بن محمد عن أبيه عن الحسين "
        "بن الحسن بن أبان عن الحسين بن سعيد عن عثمان بن عيسى عن سماعة قال "
        "سئلت أبا عبد الله عليه‌السلام : عن الرجل ينام وهو ساجد قال :"
    )
    chains = tokenize_isnad(raw)
    chain = chains[0]
    # «به الشيخ أيده الله تعالى» -> just «الشيخ».
    assert chain.tokens[0].norm == "الشیخ"
    assert chain.tokens[0].node_type == NAMED
    # Chain recovered the Imam from «قال سئلت أبا عبد الله عليه السلام».
    assert chain.tokens[-1].node_type == IMAM
    # The question topic («عن الرجل ينام...») must NOT be a node.
    assert all("ینام" not in t.norm for t in chain.tokens)


def test_bihadha_alisnad_is_same_isnad_relation():
    raw = (
        "وبهذا الاسناد عن الحسين بن سعيد عن ابن أبي عمير عن ابن أذينة "
        "عن ابن بكير قال"
    )
    chains = tokenize_isnad(raw)
    chain = chains[0]
    assert chain.tokens[0].node_type == PRONOUN
    assert chain.tokens[0].relation_kind == "same_isnad"


def test_co_narrators_attached_waw_expand_to_two_chains():
    raw = (
        "وبهذا الاسناد عن الحسين بن سعيد عن حماد عن عمر بن أذينة وحريز عن "
        "زرارة عن أحدهما عليهما‌السلام قال :"
    )
    chains = tokenize_isnad(raw)
    assert len(chains) == 2
    variants = {chain.tokens[3].norm for chain in chains}
    assert any("اذینة" in v or "أذينة" in v for v in variants)
    assert any("حریز" in v for v in variants)
    for chain in chains:
        assert chain.tokens[-1].node_type == IMAM
        assert chain.tokens[-1].relation_kind == "ambiguous"  # أحدهما
        assert "co_narrator_expanded" in chain.flags


def test_jamian_convergence_is_flagged_not_guessed():
    raw = (
        "وأخبرني الشيخ رحمه‌الله عن أبي القسم جعفر بن محمد بن قولويه عن محمد "
        "بن يعقوب عن محمد بن إسماعيل عن الفضل بن شاذان عن صفوان وعلي بن "
        "إبراهيم عن أبيه عن حماد بن عيسى جميعا عن معاوية بن عمار قال :"
    )
    chains = tokenize_isnad(raw)
    assert len(chains) == 1
    chain = chains[0]
    assert "multi_route" in chain.flags
    assert chain.needs_review


def test_quranic_period_is_not_a_parallel_route():
    raw = (
        "\u0639\u064e\u0644\u0650\u064a\u0651\u064c \u0639\u064e\u0646\u0652 \u0623\u064e\u0628\u0650\u064a\u0647\u0650 \u0639\u064e\u0646\u0652 \u0623\u064e\u0628\u0650\u064a \u0639\u064e\u0628\u0652\u062f\u0650 \u0627\u0644\u0644\u0651\u064e\u0647\u0650 \u0639 "
        "\u0641\u0650\u064a \u0642\u064e\u0648\u0652\u0644\u0650\u0647\u0650 \u062a\u064e\u0639\u064e\u0627\u0644\u064e\u0649 \u0648\u064e\u0627\u0644\u0650\u062f\u064d \u0648\u064e \u0645\u064e\u0627 \u0648\u064e\u0644\u064e\u062f\u064e. \u0644\u0650\u0644\u0652\u0643\u064e\u0627\u0641\u0650\u0631\u0650\u064a\u0646\u064e \u0644\u064e\u064a\u0652\u0633\u064e \u0644\u064e\u0647\u064f \u062f\u064e\u0627\u0641\u0650\u0639\u064c."
    )

    chain = tokenize_isnad(raw)[0]

    assert "multi_route" not in chain.flags


def test_large_co_narrator_list_expands_without_cap():
    raw = (
        "\u062d\u064e\u0645\u0651\u064e\u0627\u062f\u064c \u0639\u064e\u0646\u0652 \u062d\u064e\u0631\u0650\u064a\u0632\u064d \u0639\u064e\u0646\u0652 \u0632\u064f\u0631\u064e\u0627\u0631\u064e\u0629\u064e \u0648\u064e \u0645\u064f\u062d\u064e\u0645\u0651\u064e\u062f\u0650 \u0628\u0652\u0646\u0650 \u0645\u064f\u0633\u0652\u0644\u0650\u0645\u064d "
        "\u0648\u064e \u0623\u064e\u0628\u0650\u064a \u0628\u064e\u0635\u0650\u064a\u0631\u064d \u0648\u064e \u0641\u064f\u0636\u064e\u064a\u0652\u0644\u064d \u0648\u064e \u0628\u064f\u0643\u064e\u064a\u0652\u0631\u064d \u0639\u064e\u0646\u0652 \u0623\u064e\u0628\u0650\u064a \u062c\u064e\u0639\u0652\u0641\u064e\u0631\u064d \u0648\u064e \u0623\u064e\u0628\u0650\u064a \u0639\u064e\u0628\u0652\u062f\u0650 \u0627\u0644\u0644\u0651\u064e\u0647\u0650 \u0639"
    )

    chains = tokenize_isnad(raw)

    assert len(chains) == 10
    assert all("co_narrator_cap" not in chain.flags for chain in chains)


def test_faqih_direct_qala_alsadiq_is_single_imam_node():
    raw = (
        "وَ قَالَ الصَّادِقُ ع‌ فِي الْمَاءِ الَّذِي تَبُولُ فِيهِ الدَّوَابُّ "
        "وَ تَلَغُ فِيهِ الْكِلَابُ إِنَّهُ إِذَا كَانَ قَدْرَ كُرٍّ لَمْ "
        "يُنَجِّسْهُ شَيْ‌ءٌ[6]. [5]. في الكافي ج 3 ص 14 بإسناده عن بكر بن "
        "حبيب عن أبي جعفر عليه السلام قال:"
    )
    chains = tokenize_isnad(raw)
    assert len(chains) == 1
    chain = chains[0]
    assert types(chain) == [IMAM]
    # The leaked footnote citation must not appear as chain nodes.
    assert all("بکر" not in t.norm for t in chain.tokens)


def test_faqih_saala_form_questioner_plus_imam():
    raw = (
        "وَ سَأَلَ هِشَامُ بْنُ سَالِمٍ أَبَا عَبْدِ اللَّهِ ع- عَنِ السَّطْحِ "
        "يُبَالُ عَلَيْهِ فَتُصِيبُهُ السَّمَاءُ [1]. في بعض النسخ بصيغة "
        "الغياب في الثلاثة. و في الكافي ج 3 ص 15 بإسناده عن السكونى عن "
        "الصادق( ع) قال:"
    )
    chains = tokenize_isnad(raw)
    chain = chains[0]
    assert types(chain) == [NAMED, IMAM]
    assert "هشام" in chain.tokens[0].norm
    # The topic of the question is not part of the chain.
    assert all("السطح" not in t.norm for t in chain.tokens)


def test_faqih_saala_form_accepts_colon_after_honorific():
    raw = (
        "وَ سَأَلَ هِشَامُ بْنُ سَالِمٍ أَبَا عَبْدِ اللَّهِ عَلَيْهِ السَّلَامُ: "
        "عَنِ السَّطْحِ يُبَالُ عَلَيْهِ فَقَالَ"
    )

    chain = tokenize_isnad(raw)[0]

    assert types(chain) == [NAMED, IMAM]
    assert "هشام بن سالم" in chain.tokens[0].norm
    assert "السطح" not in chain.tokens[1].norm


def test_faqih_saala_brother_form_splits_questioner_and_imam():
    raw = (
        "وَ سَأَلَ عَلِيُّ بْنُ جَعْفَرٍ أَخَاهُ مُوسَى بْنَ جَعْفَرٍ "
        "عَلَيْهِ السَّلَامُ: عَنِ الْبَيْتِ فَقَالَ"
    )

    chain = tokenize_isnad(raw)[0]

    assert types(chain) == [NAMED, IMAM]
    assert normalise_arabic_persian("علي بن جعفر") in chain.tokens[0].norm
    assert normalise_arabic_persian("موسى بن جعفر") in chain.tokens[1].norm


def test_faqih_saalahu_form_keeps_questioner_and_cross_hadith_reference():
    raw = (
        "وَ سَأَلَهُ سَمَاعَةُ بْنُ مِهْرَانَ عَنِ الرَّجُلِ يَخْفِقُ رَأْسَهُ "
        "وَ هُوَ فِي الصَّلَاةِ قَالَ"
    )

    chain = tokenize_isnad(raw)[0]

    assert types(chain) == [NAMED, PRONOUN]
    assert chain.tokens[0].norm == normalise_arabic_persian("سماعة بن مهران")
    assert chain.tokens[1].relation_kind == "previous_hadith_imam"
    assert all("الرجل" not in token.norm for token in chain.tokens)


def test_faqih_ruwiya_mursal_opening():
    raw = "وَ رُوِيَ عَنْ أَبِي بَصِيرٍ[1] أَنَّهُ قَالَ:"
    chains = tokenize_isnad(raw)
    chain = chains[0]
    assert "mursal_opening" in chain.flags
    assert len(chain.tokens) == 1
    assert chain.tokens[0].node_type == NAMED
    assert "بصیر" in chain.tokens[0].norm


def test_rafahu_flagged_as_raf():
    raw = (
        "أَحْمَدُ بْنُ إِدْرِيسَ عَنْ مُحَمَّدِ بْنِ عَبْدِ الْجَبَّارِ عَنْ "
        "بَعْضِ أَصْحَابِنَا رَفَعَهُ إِلَى أَبِي عَبْدِ اللَّهِ ع قَالَ:"
    )
    chains = tokenize_isnad(raw)
    chain = chains[0]
    assert "raf" in chain.flags
    assert chain.tokens[-1].node_type == IMAM
    assert chain.tokens[2].node_type == COLLECTIVE  # بعض أصحابنا


def test_name_ending_in_ain_letter_is_not_imam():
    raw = "مُحَمَّدُ بْنُ يَحْيَى عَنْ أَحْمَدَ بْنِ مُحَمَّدٍ عَنِ الرَّبِيعِ قَالَ"
    chains = tokenize_isnad(raw)
    chain = chains[0]
    # «الربيع» ends with the letter ع but is NOT an Imam honorific.
    assert chain.tokens[-1].node_type == NAMED


def test_istibsar_ibn_dawud_style_ends_with_suila():
    raw = (
        "أخبرني الحسين بن عبيد الله [١] عن أحمد بن محمد بن يحيى عن أبيه عن "
        "محمد بن أحمد بن يحيى عن أيوب بن نوح عن صفوان عن إسماعيل بن جابر قال"
    )
    chains = tokenize_isnad(raw)
    chain = chains[0]
    assert chain.tokens[0].node_type == NAMED
    assert "عبید" in chain.tokens[0].norm
    assert chain.tokens[2].relation_kind == "father"
    assert "no_imam_terminal" in chain.flags


def test_attached_waw_anhu_is_anaphora_not_a_name():
    # «وعنه عن...» with the waw attached — 1,899 occurrences in the real
    # corpus were misclassified as a narrator named «وعنه» before this fix.
    raw = "وعنه عن السندي بن محمد عن يونس بن يعقوب قال"
    chains = tokenize_isnad(raw)
    chain = chains[0]
    assert chain.tokens[0].node_type == PRONOUN
    assert chain.tokens[0].relation_kind == "anaphora"


def test_fa_amma_ma_rawahu_opener_leaves_no_junk_token():
    # Tahdhib/Istibsar discussion opener «فأما ما رواه...» — the «فأما ما»
    # prefix must not become a narrator token.
    raw = (
        "فاما ما رواه الحسين بن سعيد عن محمد بن إسماعيل بن بزيع قال"
    )
    chains = tokenize_isnad(raw)
    chain = chains[0]
    assert chain.tokens[0].node_type == NAMED
    assert "الحسین بن سعید" == chain.tokens[0].norm
    assert all("اما" != t.norm and "فاما ما" != t.norm for t in chain.tokens)


def test_sami_a_recovery():
    raw = (
        "وبهذا الاسناد عن سعد بن عبد الله عن أحمد بن محمد بن عيسى عن العباس بن "
        "معروف عن حماد بن عيسى عن إبراهيم بن عمرو اليماني عن أبي خالد القماط "
        "أنه سمع أبا عبد الله عليه‌السلام يقول في الماء يمر به الرجل وهو نقيع "
        "فيه الميتة والجيفة فقال"
    )
    chains = tokenize_isnad(raw)
    chain = chains[0]
    assert chain.tokens[-1].node_type == IMAM
    # Matn («في الماء يمر به الرجل...») is not part of the chain.
    assert all("المیتة" not in t.norm for t in chain.tokens)
