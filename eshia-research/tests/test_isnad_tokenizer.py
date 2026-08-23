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


# --- matn is not chain: the 2026-08-16 Faqih review ---------------------------
# Faqih's isnad_raw regularly carries the first words of the matn, because
# al-Saduq's abbreviated openings run into the report with nothing but a
# speech verb between. Reading that tail as chain produced 798 chains marked
# for review, nearly all of them correct parses, plus narrator tokens that
# were sentences. These pin each defect that review found.


def test_preposition_after_a_mursal_phrase_is_not_part_of_the_name():
    # «روي عن فلان» puts two transmission phrases back to back; «عن» used to
    # stay inside the token, and 424 Faqih nodes were named «عن فلان».
    raw = "وَ رُوِيَ عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ قَالَ‌ سَأَلْتُ"
    chain = tokenize_isnad(raw)[0]
    assert chain.tokens[0].node_type == NAMED
    assert chain.tokens[0].norm == normalise_arabic_persian("عبد الرحمن بن الحجاج")


def test_qad_is_not_a_narrator():
    raw = "وَ قَدْ رَوَى زُرَارَةُ عَنْ أَبِي جَعْفَرٍ ع قَالَ- قُلْتُ"
    chain = tokenize_isnad(raw)[0]
    assert types(chain) == [NAMED, IMAM]
    assert chain.tokens[0].norm == normalise_arabic_persian("زرارة")


def test_printed_report_number_is_not_citation_noise():
    raw = "2553- وَ رَوَى الْحَلَبِيُّ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ"
    chain = tokenize_isnad(raw)[0]
    assert types(chain) == [NAMED, IMAM]
    assert "citation_noise" not in chain.flags
    assert not chain.needs_review


def test_matn_after_the_imam_is_not_a_review_flag():
    # The chain reached the Ma'sum; everything after is matn by design, so
    # there is nothing for a human to adjudicate.
    raw = (
        "وَ رَوَى عَبْدُ الرَّحِيمِ الْقَصِيرُ عَنْ أَبِي جَعْفَرٍ ع أَنَّهُ قَالَ- "
        "مَنْ أَخَذَ مِنْ أَظْفَارِهِ وَ شَارِبِهِ كُلَّ جُمُعَةٍ وَ قَالَ"
    )
    chain = tokenize_isnad(raw)[0]
    assert types(chain) == [NAMED, IMAM]
    assert "matn_spill" not in chain.flags
    assert not chain.needs_review


def test_first_person_question_is_matn_not_a_dropped_narrator():
    raw = "رَوَى صَفْوَانُ بْنُ يَحْيَى عَنِ الْعِيصِ بْنِ الْقَاسِمِ قَالَ‌ سَأَلْتُ"
    chain = tokenize_isnad(raw)[0]
    assert types(chain) == [NAMED, NAMED]
    assert "matn_spill" not in chain.flags
    assert "no_imam_terminal" in chain.flags  # informational, not review
    assert not chain.needs_review


def test_a_narrator_after_a_speech_verb_is_kept_not_discarded():
    # What narrowing matn_spill rests on: a transmission phrase always opens
    # a segment, so a narrator introduced after «قال» is tokenized rather
    # than swallowed by the discarded tail. matn_spill survives only as the
    # backstop for a spill that still carries transmission structure.
    raw = "رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ قَالَ حَدَّثَنِي عَلِيُّ بْنُ رِئَابٍ"
    chain = tokenize_isnad(raw)[0]
    assert types(chain) == [NAMED, NAMED]
    assert chain.tokens[-1].norm == normalise_arabic_persian("علي بن رئاب")
    assert "matn_spill" not in chain.flags


def test_imam_name_is_cut_from_the_matn_that_follows_it():
    # al-Saduq runs from the Ma'sum straight into the report with no speech
    # verb; the whole thing used to be one named_narrator token.
    raw = (
        "وَ رَوَى عَبْدُ الرَّحْمَنِ بْنِ الْحَجَّاجِ عَنْ أَبِي الْحَسَنِ ع‌ "
        "فِي رَجُلٍ صَلَّى فِي جَمَاعَةٍ يَوْمَ الْجُمُعَةِ فَلَمَّا رَكَعَ الْإِمَامُ"
    )
    chain = tokenize_isnad(raw)[0]
    assert types(chain) == [NAMED, IMAM]
    assert chain.tokens[-1].norm == normalise_arabic_persian("أبي الحسن ع")


def test_no_second_imam_is_invented_from_the_story():
    # «كان لرجل على عهد علي ع جاريتان» names Ali inside the matn; the chain
    # already ended at al-Baqir and must not gain a second Imam node.
    raw = (
        "رَوَى عَاصِمُ بْنُ حُمَيْدٍ عَنْ مُحَمَّدِ بْنِ قَيْسٍ عَنْ أَبِي جَعْفَرٍ ع "
        "قَالَ‌ كَانَ لِرَجُلٍ عَلَى عَهْدِ عَلِيٍّ ع جَارِيَتَانِ فَوَلَدَتَا"
    )
    chain = tokenize_isnad(raw)[0]
    assert types(chain) == [NAMED, NAMED, IMAM]
    assert chain.tokens[-1].norm == normalise_arabic_persian("أبي جعفر ع")


def test_jamian_in_the_matn_is_not_a_convergence():
    raw = (
        "وَ رَوَى عَلِيُّ بْنُ رِئَابٍ عَنْ أَبَانِ بْنِ تَغْلِبَ عَنْ أَبِي عَبْدِ "
        "اللَّهِ ع‌ فِي قَوْمٍ حُجَّاجٍ مُحْرِمِينَ أَصَابُوا أَفْرَاخَ نَعَامٍ "
        "فَأَكَلُوا جَمِيعاً قَالَ"
    )
    chain = tokenize_isnad(raw)[0]
    assert "multi_route" not in chain.flags
    assert types(chain) == [NAMED, NAMED, IMAM]


def test_simple_opening_jamian_expands_unambiguous_co_narrators():
    raw = (
        "رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ وَ اَلْحَلَبِيُّ جَمِيعاً عَنْ أَبِي عَبْدِ "
        "اَللَّهِ عَلَيْهِ اَلسَّلاَمُ :"
    )
    chains = tokenize_isnad(raw)
    assert len(chains) == 2
    assert {chain.tokens[0].norm for chain in chains} == {
        normalise_arabic_persian("محمد بن مسلم"),
        normalise_arabic_persian("الحلبي"),
    }
    assert all(types(chain) == [NAMED, IMAM] for chain in chains)
    assert all("multi_route" not in chain.flags for chain in chains)


def test_matn_clauses_do_not_expand_into_parallel_chains():
    # «مات و أوصى إلى رجل و له ابن صغير» is one report, not four routes.
    raw = (
        "رَوَى مُحَمَّدُ بْنُ يَعْقُوبَ الْكُلَيْنِيُّ عَنْ مُحَمَّدِ بْنِ يَحْيَى "
        "عَنْ مُحَمَّدِ بْنِ قَيْسٍ عَمَّنْ رَوَاهُ عَنْ أَبِي عَبْدِ اللَّهِ ع "
        "قَالَ‌ فِي رَجُلٍ مَاتَ وَ أَوْصَى إِلَى رَجُلٍ وَ لَهُ ابْنٌ صَغِيرٌ "
        "فَأَدْرَكَ الْغُلَامُ وَ ذَهَبَ إِلَى الْوَصِيِّ فَقَالَ"
    )
    chains = tokenize_isnad(raw)
    assert len(chains) == 1
    assert chains[0].tokens[-1].node_type == IMAM


def test_quranic_citation_does_not_expand_into_parallel_chains():
    raw = (
        "عِدَّةٌ مِنْ أَصْحَابِنَا عَنْ سَهْلِ بْنِ زِيَادٍ رَفَعَهُ عَنْ أَبِي "
        "عَبْدِ اللَّهِ ع‌ فِي قَوْلِ اللَّهِ عَزَّ وَ جَلَّ- وَ لا تَرْكَنُوا "
        "إِلَى الَّذِينَ ظَلَمُوا فَتَمَسَّكُمُ النَّارُ"
    )
    chains = tokenize_isnad(raw)
    assert len(chains) == 1
    assert chains[0].tokens[-1].node_type == IMAM
    assert "raf" in chains[0].flags  # «رفعه عن» — back-to-back phrases


def test_walad_is_not_an_attached_conjunction():
    raw = (
        "عَلِيُّ بْنُ مُحَمَّدٍ عَنْ سَهْلِ بْنِ زِيَادٍ عَنْ عَلِيِّ بْنِ شَجَرَةَ "
        "عَنْ بَعْضِ وُلْدِ مِيثَمٍ قَالَ:"
    )
    chains = tokenize_isnad(raw)
    assert len(chains) == 1
    assert chains[0].tokens[-1].norm == normalise_arabic_persian("بعض ولد ميثم")


def test_bare_speech_verb_never_becomes_a_narrator():
    raw = (
        "عَلِيُّ بْنُ إِبْرَاهِيمَ عَنْ عَمْرِو بْنِ عُثْمَانَ عَنْ عَلِيِّ بْنِ "
        "عِيسَى رَفَعَهُ قَالَ‌: إِنَّ مُوسَى ع نَاجَاهُ اللَّهُ"
    )
    chain = tokenize_isnad(raw)[0]
    assert all(t.norm != normalise_arabic_persian("قال") for t in chain.tokens)


def test_anna_opens_the_report_like_qala_does():
    raw = (
        "وَ رَوَى سَهْلُ بْنُ زِيَادٍ عَنْ يُونُسَ بْنِ يَعْقُوبَ‌ أَنَّ رَجُلًا "
        "كَانَ بِهَمَذَانَ ذَكَرَ أَنَّ أَبَاهُ مَاتَ"
    )
    chain = tokenize_isnad(raw)[0]
    assert types(chain) == [NAMED, NAMED]
    assert chain.tokens[-1].norm == normalise_arabic_persian("يونس بن يعقوب")


def test_narrative_with_no_chain_stays_flagged():
    # isnad_raw here is pure matn. A four-word Imam node would look tidy and
    # be wrong; the honest answer is to keep it in front of a human.
    raw = (
        "وَ كُنَّ نِسَاءُ النَّبِيِ‌[2] ص إِذَا كَانَ عَلَيْهِنَّ صِيَامٌ أَخَّرْنَ "
        "ذَلِكَ إِلَى شَعْبَانَ كَرَاهِيَةَ أَنْ يَمْنَعْنَ رَسُولَ اللَّهِ ص حَاجَتَهُ"
    )
    chain = tokenize_isnad(raw)[0]
    assert "suspicious_token" in chain.flags
    assert chain.needs_review


def test_faqih_direct_imam_narrative_is_one_attribution_node():
    raw = "وَ كَانَ عَلِيُّ بْنُ الْحُسَيْنِ عَلَيْهِمَا السَّلَامُ يَقُولُ"
    chain = tokenize_isnad(raw)[0]
    assert types(chain) == [IMAM]
    assert chain.tokens[0].norm == normalise_arabic_persian(
        "علي بن الحسين عليهما السلام"
    )
    assert "direct_attribution" in chain.flags
    assert not chain.needs_review


def test_faqih_anonymous_followup_question_uses_previous_imam():
    raw = "وَ سُئِلَ عَنِ الرَّجُلِ يَنَامُ ثُمَّ يَسْتَيْقِظُ فَقَالَ"
    chain = tokenize_isnad(raw)[0]
    assert types(chain) == [PRONOUN]
    assert chain.tokens[0].relation_kind == "previous_hadith_imam"
    assert not chain.needs_review


def test_faqih_named_followup_question_keeps_asker_and_previous_imam():
    raw = "وَ سَأَلَ مُعَاوِيَةُ بْنُ عَمَّارٍ عَنِ الرَّجُلِ يَطَّلِي قَالَ"
    chain = tokenize_isnad(raw)[0]
    assert types(chain) == [NAMED, PRONOUN]
    assert chain.tokens[0].norm == normalise_arabic_persian("معاوية بن عمار")
    assert chain.tokens[1].relation_kind == "previous_hadith_imam"
    assert not chain.needs_review


def test_faqih_correspondence_keeps_writer_and_explicit_imam():
    raw = (
        "وَ كَتَبَ صَفْوَانُ بْنُ يَحْيَى إِلَى أَبِي الْحَسَنِ عَلَيْهِ السَّلَامُ "
        "يَسْأَلُهُ عَنِ الرَّجُلِ فَقَالَ"
    )
    chain = tokenize_isnad(raw)[0]
    assert types(chain) == [NAMED, IMAM]
    assert chain.tokens[0].norm == normalise_arabic_persian("صفوان بن يحيى")
    assert chain.tokens[1].norm == normalise_arabic_persian(
        "أبي الحسن عليه السلام"
    )
    assert "direct_correspondence" in chain.flags
    assert not chain.needs_review


def test_faqih_attached_waw_anonymous_question_uses_previous_imam():
    chain = tokenize_isnad(
        "وَسُئِلَ عَلَيْهِ السَّلَامُ عَنِ الصَّائِمِ الْمُتَطَوِّعِ فَقَالَ"
    )[0]
    assert types(chain) == [PRONOUN]
    assert chain.tokens[0].relation_kind == "previous_hadith_imam"
    assert not chain.needs_review


def test_faqih_raised_narrative_keeps_narrator_and_explicit_imam():
    raw = (
        "رُوِيَ عَنْ صَبَّاحٍ الْمُزَنِيِّ رَفَعَهُ قَالَ جَاءَ رَجُلَانِ "
        "إِلَى أَمِيرِ الْمُؤْمِنِينَ ع فَقَالَ"
    )
    chain = tokenize_isnad(raw)[0]
    assert types(chain) == [NAMED, IMAM]
    assert chain.tokens[0].norm == normalise_arabic_persian("صباح المزني")
    assert chain.tokens[1].norm == normalise_arabic_persian("أمير المؤمنين ع")
    assert "raf" in chain.flags
    assert not chain.needs_review


def test_shared_honorific_applies_to_both_imams():
    raw = (
        "رَوَى جَمِيلٌ عَنْ زُرَارَةَ عَنْ أَبِي جَعْفَرٍ وَ أَبِي عَبْدِ اللَّهِ ع "
        "فِي رَجُلٍ أَعْتَقَ عَبْداً"
    )
    chains = tokenize_isnad(raw)
    assert len(chains) == 2
    assert all(types(chain) == [NAMED, NAMED, IMAM] for chain in chains)
    assert {chain.tokens[-1].norm for chain in chains} == {
        normalise_arabic_persian("أبي جعفر ع"),
        normalise_arabic_persian("أبي عبد الله ع"),
    }
    assert all(not chain.needs_review for chain in chains)


def test_plural_raised_co_narrators_expand_to_same_imam():
    raw = (
        "وَ فِي رِوَايَةِ عَبْدِ اللَّهِ بْنِ الْمُغِيرَةِ وَ صَفْوَانَ وَ غَيْرِ "
        "وَاحِدٍ رَفَعُوهُ إِلَى أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ"
    )
    chains = tokenize_isnad(raw)
    assert len(chains) == 3
    assert all(types(chain)[-1] == IMAM for chain in chains)
    assert {chain.tokens[0].node_type for chain in chains} == {NAMED, COLLECTIVE}
    assert all("raf" in chain.flags for chain in chains)
    assert all(not chain.needs_review for chain in chains)


def test_faqih_compiler_byline_is_not_mistaken_for_the_chain():
    raw = (
        "قَالَ أَبُو جَعْفَرٍ مُحَمَّدُ بْنُ الْحُسَيْنِ بْنِ مُوسَى بْنِ "
        "بَابَوَيْهِ الْقُمِّيُّ مُصَنِّفُ هَذَا الْكِتَابِ رَضِيَ اللَّهُ عَنْهُ "
        "رُوِيَ عَنْ شُعَيْبِ بْنِ وَاقِدٍ عَنِ الْحُسَيْنِ بْنِ زَيْدٍ "
        "عَنِ الصَّادِقِ جَعْفَرِ بْنِ مُحَمَّدٍ عَنْ أَبِيهِ عَنْ آبَائِهِ "
        "عَنْ أَمِيرِ الْمُؤْمِنِينَ ع قَالَ"
    )
    chain = tokenize_isnad(raw)[0]
    assert [token.norm for token in chain.tokens[:2]] == [
        normalise_arabic_persian("شعيب بن واقد"),
        normalise_arabic_persian("الحسين بن زيد"),
    ]
    assert chain.tokens[-1].norm == normalise_arabic_persian("الصادق جعفر بن محمد")
    assert not chain.needs_review


def test_faqih_moses_narrative_ignores_editorial_bracket():
    raw = (
        "وَ لَمَّا نَاجَى اللَّهُ مُوسَى بْنَ عِمْرَانَ [عَلَى نَبِيِّنَا وَ] "
        "عَلَيْهِ السَّلَامُ قَالَ"
    )
    chain = tokenize_isnad(raw)[0]
    assert types(chain) == [IMAM]
    assert chain.tokens[0].norm == normalise_arabic_persian(
        "موسى بن عمران عليه السلام"
    )
    assert not chain.needs_review


def test_faqih_direct_prophet_narrative_accepts_spaced_honorific_waw():
    raw = (
        "وَ عَقَّ أَبُو طَالِبٍ رَحِمَهُ اللَّهُ عَنْ رَسُولِ اللَّهِ "
        "صَلَّى اللَّهُ عَلَيْهِ وَ آلِهِ يَوْمَ السَّابِعِ فَقَالَ"
    )
    chain = tokenize_isnad(raw)[0]
    assert types(chain) == [IMAM]
    assert chain.tokens[0].norm == normalise_arabic_persian(
        "رسول الله صلى الله عليه و آله"
    )
    assert not chain.needs_review


def test_faqih_mursal_honorific_pronoun_uses_previous_imam():
    chain = tokenize_isnad(
        "وَ رُوِيَ : أَنَّهُ عَلَيْهِ السَّلَامُ حَجَّ عِشْرِينَ حَجَّةً"
    )[0]
    assert types(chain) == [PRONOUN]
    assert chain.tokens[0].relation_kind == "previous_hadith_imam"
    assert "mursal_opening" in chain.flags
    assert not chain.needs_review


def test_question_inside_matn_does_not_swallow_an_existing_chain():
    raw = (
        "رَوَى السَّكُونِيُّ عَنْ جَعْفَرِ بْنِ مُحَمَّدٍ عَنْ أَبِيهِ ع "
        "أَنَّ عَلِيَّ بْنَ أَبِي طَالِبٍ ع سُئِلَ عَنْ رَجُلٍ"
    )
    chain = tokenize_isnad(raw)[0]
    assert [token.norm for token in chain.tokens[:2]] == [
        normalise_arabic_persian("السكوني"),
        normalise_arabic_persian("جعفر بن محمد"),
    ]
    assert chain.tokens[-1].node_type == IMAM
    assert not chain.needs_review


def test_tahdhib_argument_prefix_is_not_a_narrator():
    raw = (
        "فَالَّذِي يَدُلُّ عَلَى ذَلِكَ مَا أَخْبَرَنِي بِهِ الشَّيْخُ أَيَّدَهُ اللَّهُ "
        "عَنْ أَحْمَدَ بْنِ مُحَمَّدٍ عَنْ أَبِيهِ عَنْ زُرَارَةَ قَالَ"
    )
    chain = tokenize_isnad(raw)[0]
    assert chain.tokens[0].norm == normalise_arabic_persian("الشيخ")
    assert all("يدل" not in token.norm for token in chain.tokens)
    assert not chain.needs_review


def test_inline_book_citation_repairs_split_narrator_name():
    raw = (
        "يَدُلُّ عَلَيْهِ مَا أَخْبَرَنِي بِهِ الشَّيْخُ عَنْ أَحْمَدَ "
        "(٢٧ التَّهْذِيب ج ١) ابْنِ مُحَمَّدٍ عَنْ أَبِيهِ عَنْ زُرَارَةَ قَالَ"
    )
    chain = tokenize_isnad(raw)[0]
    assert [token.norm for token in chain.tokens[:2]] == [
        normalise_arabic_persian("الشيخ"),
        normalise_arabic_persian("أحمد ابن محمد"),
    ]
    assert "citation_noise" not in chain.flags
    assert not chain.needs_review


def test_quran_cross_reference_inside_chain_is_removed():
    raw = (
        "مُحَمَّدُ بْنُ أَحْمَدَ عَنْ يَعْقُوبَ بْنِ يَزِيدَ عَنْ يَحْيَى بْنِ "
        "الْمُبَارَكِ سُورَةُ الْبَقَرَةِ الْآيَةُ: ١٨١ عَنْ عَبْدِ اللَّهِ بْنِ "
        "جَبَلَةَ عَنْ سَمَاعَةَ قَالَ"
    )
    chain = tokenize_isnad(raw)[0]
    assert [token.norm for token in chain.tokens[-2:]] == [
        normalise_arabic_persian("عبد الله بن جبلة"),
        normalise_arabic_persian("سماعة"),
    ]
    assert "citation_noise" not in chain.flags
    assert not chain.needs_review


def test_tusi_discussion_wrapper_is_not_a_narrator():
    raw = (
        "وَ لَا يُنَافِي ذَلِكَ مَا رَوَاهُ مُحَمَّدُ بْنُ أَحْمَدَ عَنْ "
        "إِبْرَاهِيمَ بْنِ هَاشِمٍ عَنِ السَّكُونِيِّ عَنْ جَعْفَرٍ عَنْ أَبِيهِ"
    )
    chain = tokenize_isnad(raw)[0]
    assert chain.tokens[0].norm == normalise_arabic_persian("محمد بن أحمد")
    assert all("ينافي" not in token.norm for token in chain.tokens)
    assert not chain.needs_review


def test_attached_waw_written_question_keeps_writer_and_imam():
    raw = (
        "وَكَتَبَ مُحَمَّدُ بْنُ الْحَسَنِ الصَّفَّارُ إِلَى أَبِي مُحَمَّدٍ "
        "الْحَسَنِ بْنِ عَلِيٍّ عَلَيْهِمَا السَّلَامُ رَجُلٌ مَاتَ وَتَرَكَ بِنْتَهُ"
    )
    chain = tokenize_isnad(raw)[0]
    assert types(chain) == [NAMED, IMAM]
    assert chain.tokens[0].norm == normalise_arabic_persian(
        "محمد بن الحسن الصفار"
    )
    assert not chain.needs_review
