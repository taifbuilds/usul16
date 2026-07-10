from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.name_grammar import parse_name, surface_forms


def norm(text: str) -> str:
    return normalise_arabic_persian(text)


def forms_of(raw: str) -> dict[str, str]:
    return {f.form_norm: f.derivation for f in surface_forms(parse_name(raw))}


def test_parse_full_nasab_with_nisba():
    parsed = parse_name("أحمد بن محمد بن عيسى الأشعري")
    assert parsed.units == (norm("احمد"), norm("محمد"), norm("عیسی"))
    assert parsed.nisba_parts == (norm("الاشعری"),)
    assert parsed.father_norm == norm("محمد بن عیسی")
    assert not parsed.residue


def test_parse_father_that_is_a_kunya():
    # محمد بن أبي عمير: the father unit is the kunya «أبي عمير».
    parsed = parse_name("محمد بن أبي عمير")
    assert parsed.units == (norm("محمد"), norm("ابی عمیر"))
    assert parsed.father_norm == norm("ابی عمیر")


def test_parse_theophoric_compound():
    parsed = parse_name("عبد الله بن سنان")
    assert parsed.units == (norm("عبد الله"), norm("سنان"))


def test_parse_ibn_form():
    parsed = parse_name("ابن محبوب")
    assert parsed.is_ibn_form
    assert parsed.units == (norm("محبوب"),)


def test_parse_kunya_first_name():
    parsed = parse_name("أبو إبراهيم الأزدي")
    assert parsed.kunya == norm("ابو ابراهیم")
    assert parsed.units == ()
    assert parsed.nisba_parts == (norm("الازدی"),)


def test_parse_kunya_before_nasab():
    # al-Kulayni's chain opening: kunya precedes the full nasab.
    parsed = parse_name("أبو جعفر محمد بن يعقوب")
    assert parsed.kunya == norm("ابو جعفر")
    assert parsed.units == (norm("محمد"), norm("یعقوب"))
    assert parsed.father_norm == norm("یعقوب")
    forms = {f.form_norm for f in surface_forms(parsed)}
    assert norm("محمد بن یعقوب") in forms


def test_surface_forms_truncations_and_ibn_form():
    forms = forms_of("أحمد بن محمد بن عيسى الأشعري")
    assert forms[norm("احمد بن محمد بن عیسی")] == "full"
    assert forms[norm("احمد بن محمد")] == "nasab_truncation"
    assert forms[norm("احمد")] == "first_name"
    assert forms[norm("ابن محمد")] == "ibn_form"
    assert forms[norm("ابن عیسی")] == "ibn_form"
    assert forms[norm("الاشعری")] == "nisba_form"


def test_surface_forms_hasan_ibn_mahbub_claims_ibn_mahbub():
    forms = forms_of("الحسن بن محبوب")
    assert forms[norm("ابن محبوب")] == "ibn_form"


def test_surface_forms_kunya_case_variants():
    # Chains use the genitive after عن: «عن ابی بصیر».
    forms = forms_of("أبو بصير")
    assert forms[norm("ابو بصیر")] == "kunya"
    assert forms[norm("ابی بصیر")] == "kunya"
    assert forms[norm("ابا بصیر")] == "kunya"


def test_ibn_form_name_generates_only_itself():
    forms = forms_of("ابن محبوب")
    assert forms == {norm("ابن محبوب"): "full"}
