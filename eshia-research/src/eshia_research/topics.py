"""Source-derived topic taxonomy for the core hadith collections."""

from __future__ import annotations

import re
import unicodedata
from bisect import bisect_left
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from eshia_research.models import (
    Book,
    Hadith,
    HadithTopicAssignment,
    HadithTranslation,
    ThaqalaynStructureMap,
    Topic,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.translation.publication import (
    PUBLIC_TRANSLATION_VERSIONS,
    is_public_english_translation,
    public_english_translation_candidate_filters,
)


AL_KAFI_SOURCE_BOOK_ID = "11005"
FAQIH_SOURCE_BOOK_ID = "11021"
TAXONOMY_SOURCE = "thaqalayn-structure"
SEMANTIC_TAXONOMY_SOURCE = "alkafi-semantic"
TAXONOMY_VERSION = "alkafi-topics-v2"
_LEADING_LABEL_RE = re.compile(
    r"^(?:the\s+)?(?:book|chapter)\s+(?:(?:about|concerning|of|on|regarding)\s+)?",
    re.IGNORECASE,
)
_NON_SLUG_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class TopicBuildStats:
    hadiths: int
    topics: int
    kitab_topics: int
    chapter_topics: int
    semantic_topics: int
    assignments: int
    semantic_assignments: int
    directly_placed: int
    inherited_placed: int
    method_counts: dict[str, int]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SemanticTopicRule:
    key: str
    name: str
    kind: str
    aliases: tuple[str, ...]
    english_terms: tuple[str, ...]
    arabic_terms: tuple[str, ...] = ()


def _semantic(
    key: str,
    name: str,
    kind: str,
    aliases: str,
    english_terms: str,
    arabic_terms: str = "",
) -> SemanticTopicRule:
    return SemanticTopicRule(
        key=key,
        name=name,
        kind=kind,
        aliases=tuple(part.strip() for part in aliases.split("|") if part.strip()),
        english_terms=tuple(
            part.strip() for part in english_terms.split("|") if part.strip()
        ),
        arabic_terms=tuple(
            normalise_arabic_persian(part.strip())
            for part in arabic_terms.split("|")
            if part.strip()
        ),
    )


SEMANTIC_TOPIC_RULES = (
    # Moods and inner states
    _semantic("hope", "Hope", "mood", "hopeful|optimism|despair|hopeless|looking for hope", "hope|hopes|despair|despaired|despondent", "رجاء|الرجاء|يأس|اليأس"),
    _semantic("grief", "Grief & Sadness", "mood", "grief|sad|sadness|sorrow|bereavement|heartbroken|loss", "grief|sadness|sorrow|mourn|mourning|wept|weep|tears", "حزن|الحزن|حزينا|بكاء|البكاء"),
    _semantic("anxiety", "Anxiety & Worry", "mood", "anxiety|anxious|worry|worried|stress|stressed|overwhelmed|uneasy|mental health", "anxiety|anxious|worry|worried|distress|anguish|uneasy", "الهم|غم|الغم|كرب|الكرب"),
    _semantic("fear", "Fear", "mood", "fear|afraid|scared|frightened|dread|feeling unsafe", "fear|afraid|frightened|terror|dread", "خوف|الخوف|خاف|يخاف"),
    _semantic("anger", "Anger", "mood", "anger|angry|rage|furious|temper|resentment", "anger|angry|rage|wrath|temper|furious", "غضب|الغضب|غضبان"),
    _semantic("love", "Love & Affection", "mood", "love|affection|loving|attachment|care for someone", "love|loves|loving|affection|beloved", "حب|الحب|محبة|المحبة"),
    _semantic("joy", "Joy & Happiness", "mood", "joy|happy|happiness|delight|glad|celebration", "joy|happy|happiness|delight|glad|rejoice", "فرح|الفرح|سرور|السرور"),
    _semantic("loneliness", "Loneliness", "mood", "lonely|loneliness|alone|isolated|without friends", "lonely|loneliness|isolation|isolated", "وحيدا"),
    _semantic("envy", "Envy & Jealousy", "mood", "envy|jealous|jealousy|resenting others", "envy|envious|jealous|jealousy", "حسد|الحسد|حاسد"),
    _semantic("shame", "Shame & Regret", "mood", "shame|ashamed|regret|remorse|guilt|guilty", "shame|ashamed|regret|remorse|guilt|guilty", "ندم|الندم|حياء|الحياء"),

    # Life situations and relationships
    _semantic("marriage", "Marriage", "life", "marriage|married|husband|wife|spouse|wedding|choosing a spouse", "marriage|marry|married|husband|wife|spouse|wedding|dowry", "زواج|الزواج|تزوج|زوج|الزوج|زوجة|الزوجة|نكاح|النكاح"),
    _semantic("divorce", "Divorce & Separation", "life", "divorce|separation|separated couple|marital breakdown", "divorce|divorced|separation|repudiation", "طلاق|الطلاق|طلقها|المطلقة"),
    _semantic("parents", "Parents", "life", "parents|mother|father|mum|mom|dad|honouring parents", "parents|mother|father|maternal|paternal", "والدين|الوالدين|والد|الوالد|والدة|الوالدة"),
    _semantic("children", "Children & Parenting", "life", "children|child|kids|parenting|raising children|son|daughter|baby", "children|child|parenting|son|daughter|infant|newborn|offspring", "ولد|الولد|أولاد|الأولاد|طفل|الطفل|ابن|الابن|بنت|البنت"),
    _semantic("family", "Family & Kinship", "life", "family|relatives|kinship|siblings|brother|sister|family problems|relationship problems", "family|relative|relatives|kinship|brother|sister|kinsfolk", "الرحم|قرابة|القرابة|أخ|الأخ|أخت|الأخت"),
    _semantic("friendship", "Friendship & Companionship", "life", "friend|friends|friendship|companion|companionship|good company", "friend|friends|friendship|companion|companionship", "صديق|الصديق|صاحب|الصاحب|صحبة|الصحبة"),
    _semantic("neighbours", "Neighbours", "life", "neighbor|neighbour|neighbours|neighborhood|community relations", "neighbor|neighbors|neighbour|neighbours", "جار|الجار|جيران|الجيران"),
    _semantic("work", "Work & Livelihood", "life", "work|job|career|business|earning|income|livelihood|employment", "work|worker|trade|business|earning|income|livelihood|occupation|wages", "تجارة|التجارة|كسب|الكسب|رزق|الرزق"),
    _semantic("wealth", "Wealth & Money", "life", "money|wealth|rich|finances|property|possessions|financial advice", "wealth|money|rich|property|possessions|fortune", "مال|المال|أموال|الأموال|غنى|الغنى"),
    _semantic("poverty", "Poverty & Hardship", "life", "poverty|poor|financial hardship|debt|debts|struggling financially", "poverty|poor|needy|destitute|debt|debtor|hardship", "فقر|الفقر|فقير|الفقراء|مديون"),
    _semantic("illness", "Illness & Healing", "life", "illness|sick|health|healing|cure|pain|doctor|medicine", "illness|sick|sickness|disease|healing|cure|medicine|patient", "مرض|المرض|مريض|المريض|شفاء|الشفاء|دواء|الدواء"),
    _semantic("death", "Death & Bereavement", "life", "death|dying|died|funeral|grave|bereavement|losing someone", "death|dying|died|dead|funeral|burial|grave|deceased", "موت|الموت|ميت|الميت|قبر|القبر|جنازة|الجنازة"),
    _semantic("travel", "Travel", "life", "travel|travelling|journey|trip|traveler|away from home", "travel|travelling|journey|traveler|traveller|voyage", "سفر|السفر|مسافر|المسافر|رحلة"),
    _semantic("food", "Food & Eating", "life", "food|eating|drink|hunger|meal|diet|table manners", "food|eat|eating|meal|drink|drinking|hunger|hungry", "طعام|الطعام|أكل|الأكل|شراب|الشراب|جوع|الجوع"),
    _semantic("sleep", "Sleep & Dreams", "life", "sleep|sleeping|dream|dreams|nightmare|insomnia|waking up", "sleep|sleeping|dream|dreams|vision|nightmare|wake", "نوم|النوم|منام|المنام|رؤيا|الرؤيا"),
    _semantic("conflict", "Conflict & Reconciliation", "life", "argument|conflict|fighting|disagreement|reconcile|make peace", "conflict|quarrel|argument|fighting|reconcile|reconciliation|make peace", "خصومة|الخصومة|نزاع|النزاع|صلح|الصلح"),
    _semantic("leadership", "Leadership & Responsibility", "life", "leadership|leader|authority|responsibility|governance|ruler", "leadership|leader|authority|governor|ruler|governance|responsibility", "حاكم|الحاكم|سلطان|السلطان|والي|الوالي|رعية|الرعية"),

    # Worship and practices
    _semantic("prayer", "Prayer", "practice", "prayer|pray|salah|salat|daily prayers|how to pray", "prayer|pray|praying|salah|salat|rak'at|prostration", "صلاة|الصلاة|صلوات|يصلي|سجود|السجود"),
    _semantic("dua", "Supplication", "practice", "dua|du'a|supplication|asking Allah|personal prayer|invocation", "supplication|supplicate|invocation|dua|du'a|beseech", "دعاء|الدعاء|يدعو|ادعوا"),
    _semantic("dhikr", "Remembrance of Allah", "practice", "dhikr|zikr|remember Allah|remembrance|tasbih|glorification", "remembrance of allah|remember allah|dhikr|zikr|tasbih|glorify", "ذكر الله|الذكر|تسبيح|التسبيح"),
    _semantic("quran", "Quran", "practice", "quran|qur'an|koran|recitation|verses|reading quran", "quran|qur'an|recite|recitation|verse of allah|holy book", "قرآن|القرآن|تلاوة|التلاوة|آية|الآية"),
    _semantic("fasting", "Fasting", "practice", "fasting|fast|sawm|siyam|ramadan|breaking a fast", "fasting|fast|sawm|siyam|ramadan", "صوم|الصوم|صيام|الصيام|رمضان"),
    _semantic("charity", "Charity & Zakat", "practice", "charity|zakat|alms|donation|giving to the poor|sadaqah", "charity|zakat|alms|donation|sadaqah|poor-rate", "زكاة|الزكاة|صدقة|الصدقة|يتصدق"),
    _semantic("hajj", "Hajj & Pilgrimage", "practice", "hajj|pilgrimage|umrah|mecca|kaaba|ka'bah|pilgrim", "hajj|pilgrimage|pilgrim|umrah|mecca|makka|kaaba|ka'bah", "حج|الحج|عمرة|العمرة|مكة|الكعبة"),
    _semantic("purification", "Purification", "practice", "wudu|ablution|ghusl|purity|cleanliness|ritual bath|najasa", "wudu|ablution|ghusl|purification|ritual bath|impurity|unclean", "وضوء|الوضوء|غسل|الغسل|طهارة|الطهارة|نجاسة|النجاسة"),
    _semantic("repentance", "Repentance", "practice", "repentance|repent|tawbah|asking forgiveness|returning to Allah", "repentance|repent|tawbah|turn back to allah|seeking forgiveness", "توبة|التوبة|تاب|يتوب|استغفار"),
    _semantic("mosque", "Mosques & Congregation", "practice", "mosque|masjid|congregational prayer|jama'ah|place of worship", "mosque|masjid|congregation|congregational", "مسجد|المسجد|مساجد|المساجد|جماعة|الجماعة"),
    _semantic("knowledge", "Seeking Knowledge", "practice", "knowledge|learning|study|studying|education|teacher|student|scholarship", "knowledge|learn|learning|study|teacher|student|scholar|education|understanding", "علم|العلم|تعلم|يتعلم|عالم|العالم|فقه|الفقه"),
    _semantic("ziyarah", "Visitation & Ziyarat", "practice", "ziyarah|ziyarat|visitation|visiting shrines|pilgrimage to imams", "ziyarah|ziyarat|visitation|visit the grave|shrine", "زيارة|الزيارة|يزور|مشهد"),

    # Virtues and conduct
    _semantic("patience", "Patience", "virtue", "patience|patient|sabr|perseverance|endurance|hard times", "patience|patient|sabr|persevere|endurance|steadfast", "صبر|الصبر|صابر|الصابرين"),
    _semantic("gratitude", "Gratitude", "virtue", "gratitude|grateful|thankful|thanks|shukr|appreciation", "gratitude|grateful|thankful|give thanks|shukr", "شكر|الشكر|شاكر|الشاكرين"),
    _semantic("sincerity", "Sincerity & Intention", "virtue", "sincerity|sincere|intention|niyyah|motivation|showing off", "sincerity|sincere|intention|intentions|niyyah|showing off|ostentation", "إخلاص|الإخلاص|نية|النية|رياء|الرياء"),
    _semantic("humility", "Humility", "virtue", "humility|humble|modesty|arrogance|pride|ego", "humility|humble|arrogance|arrogant|pride|conceit", "تواضع|التواضع|كبر|الكبر|تكبر|عجب|العجب"),
    _semantic("generosity", "Generosity", "virtue", "generosity|generous|giving|hospitality|sharing|stinginess", "generosity|generous|hospitality|giving freely|stingy|miser", "جود|الجود|كرم|الكرم|بخل|البخل"),
    _semantic("forgiveness", "Forgiveness", "virtue", "forgiveness|forgive|pardoning|mercy after harm|letting go", "forgiveness|forgive|forgiven|pardon|pardoning", "عفو|العفو|يعفو|غفر|يغفر"),
    _semantic("trust", "Trust in Allah", "virtue", "trust Allah|tawakkul|reliance on Allah|depend on God|faith during uncertainty", "trust in allah|rely on allah|reliance on allah|tawakkul", "توكل|التوكل|يتوكل"),
    _semantic("truthfulness", "Truthfulness", "virtue", "truth|truthful|honesty|honest|lying|lie|deception", "truthful|truthfulness|honest|honesty|lying|liar|falsehood", "صدق|الصدق|صادق|كذب|الكذب|كاذب"),
    _semantic("kindness", "Kindness & Mercy", "virtue", "kindness|kind|mercy|merciful|compassion|gentleness|helping others", "kindness|kind|mercy|merciful|compassion|gentle|gentleness", "رحمة|الرحمة|رحيم|رفق|الرفق|لين"),
    _semantic("contentment", "Contentment", "virtue", "contentment|content|satisfied|qana'ah|being happy with less", "contentment|contented|satisfied with|qana'ah", "قناعة|القناعة|رضا|الرضا"),
    _semantic("chastity", "Modesty & Chastity", "virtue", "modesty|chastity|haya|sexual ethics|lowering the gaze|indecency", "chastity|chaste|modesty|indecency|fornication|adultery", "عفة|العفة|حياء|الحياء|زنا|الزنا"),
    _semantic("piety", "Piety & God-consciousness", "virtue", "piety|pious|taqwa|god consciousness|fear of Allah|righteousness", "piety|pious|taqwa|god-fearing|righteous", "تقوى|التقوى|متقين|المتقين|ورع|الورع"),
    _semantic("good-character", "Good Character", "virtue", "good character|manners|akhlaq|behaviour|conduct|etiquette", "good character|good manners|conduct|behavior|behaviour|etiquette|morals", "حسن الخلق|الأخلاق|خلق حسن|أدب|الأدب"),
    _semantic("justice", "Justice", "virtue", "justice|fairness|fair|oppression|injustice|rights", "justice|justly|fairness|oppression|oppressor|injustice|rights", "عدل|العدل|ظلم|الظلم|ظالم"),

    # Belief and sacred history
    _semantic("tawhid", "Oneness of Allah", "belief", "tawhid|oneness of Allah|God's unity|attributes of Allah|knowing Allah", "oneness of allah|one god|attributes of allah|knowledge of allah|tawhid", "توحيد|التوحيد|الله واحد|معرفة الله"),
    _semantic("prophethood", "Prophethood", "belief", "prophethood|prophets|nabi|messengers|revelation", "prophet|prophets|prophethood|messenger of allah|revelation", "نبي|النبي|أنبياء|الأنبياء|رسول|الرسول|رسل"),
    _semantic("imamate", "Imamate & Wilayah", "belief", "imamate|imam|wilayah|walayah|divine authority|guardianship|ahl al-bayt", "imamate|divine authority|wilayah|walayah|guardian appointed|imam of his time", "إمامة|الإمامة|إمام|الإمام|ولاية|الولاية|أهل البيت"),
    _semantic("mahdi", "Imam al-Mahdi", "person", "mahdi|imam mahdi|al-qa'im|qaim|awaited imam|occultation|reappearance", "mahdi|al-mahdi|al-qa'im|al qa'im|occultation|reappearance|awaited imam", "المهدي|القائم|صاحب الزمان|الغيبة|الظهور"),
    _semantic("imam-ali", "Imam Ali", "person", "imam ali|amir al-mu'minin|ameerul momineen|commander of the faithful", "imam ali|amir al-mu'minin|commander of the faithful|ali ibn abu talib|ali ibn abi talib", "أمير المؤمنين|علي بن أبي طالب"),
    _semantic("ahl-al-bayt", "Ahl al-Bayt", "person", "ahl al-bayt|family of the prophet|household of Muhammad|the imams", "ahl al-bayt|family of the prophet|household of the prophet|holy family", "أهل البيت|آل محمد|عترة"),
    _semantic("afterlife", "Afterlife & Resurrection", "belief", "afterlife|resurrection|judgment day|day of judgement|hereafter|akhirah", "afterlife|hereafter|resurrection|day of judgment|day of judgement|raised from the grave", "قيامة|القيامة|بعث|البعث|الآخرة|يوم الحساب"),
    _semantic("paradise", "Paradise", "belief", "paradise|heaven|jannah|reward in the afterlife", "paradise|heaven|jannah|gardens of bliss", "جنة|الجنة|جنات"),
    _semantic("hell", "Hell & Punishment", "belief", "hell|hellfire|jahannam|punishment|fire of the afterlife", "hell|hellfire|jahannam|fire of hell|divine punishment", "جهنم|النار|عذاب|العذاب"),
    _semantic("faith", "Faith & Belief", "belief", "faith|belief|iman|believer|strengthen faith|certainty", "faith|belief|believer|iman|certainty in allah", "إيمان|الإيمان|مؤمن|المؤمن|يقين|اليقين"),
    _semantic("sin", "Sin & Temptation", "belief", "sin|sins|temptation|disobedience|bad habits|avoiding sin", "sin|sins|sinful|temptation|disobedience|transgression", "ذنب|الذنب|ذنوب|معصية|المعصية|إثم|الإثم"),
    _semantic("divine-tests", "Trials & Divine Tests", "belief", "trials|test from Allah|calamity|affliction|hardship|why bad things happen", "trial|trials|test from allah|affliction|calamity|tribulation", "بلاء|البلاء|ابتلاء|مصيبة|المصيبة"),
    _semantic("intercession", "Intercession", "belief", "intercession|shafa'ah|shafaa|seeking intercession", "intercession|intercede|shafa'ah", "شفاعة|الشفاعة|يشفع"),
    _semantic("angels", "Angels", "belief", "angels|angel|jibril|gabriel|malaika", "angel|angels|gabriel|jibril", "ملك|الملك|ملائكة|الملائكة|جبرئيل"),
)


def _slug_text(value: str) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .casefold()
    )
    return _NON_SLUG_RE.sub("-", ascii_value).strip("-")


def topic_hashtag(name: str) -> str:
    concise = _LEADING_LABEL_RE.sub("", " ".join(name.split())).strip(" .:;,-")
    slug = _slug_text(concise or name)
    if len(slug) > 48:
        slug = slug[:48].rsplit("-", 1)[0]
    slug = slug.strip("-") or "topic"
    return f"#{slug}"


def _topic_search_text(name: str, hashtag: str) -> str:
    clean = hashtag.removeprefix("#").replace("-", " ")
    return " ".join(dict.fromkeys((name.casefold(), clean, hashtag.casefold())))


def _semantic_search_text(rule: SemanticTopicRule, hashtag: str) -> str:
    values = [
        rule.name.casefold(),
        hashtag.casefold(),
        hashtag.removeprefix("#").replace("-", " "),
        *rule.aliases,
    ]
    return " ".join(dict.fromkeys(_normalise_english(value) for value in values))


def _normalise_english(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    return _slug_text(value).replace("-", " ")


def _english_matches(text: str, terms: tuple[str, ...]) -> list[str]:
    padded = f" {text} "
    matches = []
    for term in terms:
        normalized = _normalise_english(term)
        if normalized and f" {normalized} " in padded:
            matches.append(term)
    return matches


def _arabic_matches(text: str, terms: tuple[str, ...]) -> list[str]:
    padded = f" {text} "
    return [term for term in terms if term and f" {term} " in padded]


def _preferred_translations(
    db: Session, hadiths: list[Hadith]
) -> dict[int, HadithTranslation]:
    hadith_by_id = {hadith.id: hadith for hadith in hadiths}
    candidates = list(
        db.execute(
            select(HadithTranslation).where(
                HadithTranslation.hadith_id.in_(hadith_by_id),
                *public_english_translation_candidate_filters(),
            )
        ).scalars()
    )
    version_rank = {
        version: index for index, version in enumerate(PUBLIC_TRANSLATION_VERSIONS)
    }
    chosen: dict[int, HadithTranslation] = {}
    for translation in sorted(
        candidates,
        key=lambda row: version_rank.get(row.translation_version, len(version_rank)),
    ):
        hadith = hadith_by_id[translation.hadith_id]
        if (
            translation.hadith_id not in chosen
            and is_public_english_translation(translation, hadith)
        ):
            chosen[translation.hadith_id] = translation
    return chosen


def _structure_key(mapping: ThaqalaynStructureMap) -> tuple[int, str, int]:
    return mapping.volume, mapping.kitab_id, mapping.chapter_id


def _choose_nearest_structure(
    hadith: Hadith,
    anchors: list[tuple[int, ThaqalaynStructureMap]],
) -> tuple[ThaqalaynStructureMap, str, float, dict]:
    sequences = [sequence for sequence, _ in anchors]
    position = bisect_left(sequences, hadith.sequence_in_book)
    previous = anchors[position - 1] if position else None
    following = anchors[position] if position < len(anchors) else None
    if previous and following:
        previous_distance = hadith.sequence_in_book - previous[0]
        following_distance = following[0] - hadith.sequence_in_book
        previous_map, following_map = previous[1], following[1]
        if _structure_key(previous_map) == _structure_key(following_map):
            chosen = previous_map
            method = "bounded_same_chapter"
            confidence = 0.84
        elif (previous_map.volume, previous_map.kitab_id) == (
            following_map.volume,
            following_map.kitab_id,
        ):
            chosen = previous_map if previous_distance <= following_distance else following_map
            method = "nearest_within_kitab"
            confidence = 0.68
        else:
            chosen = previous_map if previous_distance <= following_distance else following_map
            method = "nearest_structure"
            confidence = 0.52
        evidence = {
            "previous_hadith_id": previous_map.hadith_id,
            "previous_distance": previous_distance,
            "following_hadith_id": following_map.hadith_id,
            "following_distance": following_distance,
        }
    else:
        sequence, chosen = previous or following  # type: ignore[misc]
        method = "single_sided_structure"
        confidence = 0.5
        evidence = {
            "anchor_hadith_id": chosen.hadith_id,
            "distance": abs(hadith.sequence_in_book - sequence),
        }
    return chosen, method, confidence, evidence


def rebuild_book_topics(
    db: Session,
    *,
    source_book_id: str,
) -> TopicBuildStats:
    """Replace one book's generated taxonomy and assignments atomically."""

    book_config = {
        AL_KAFI_SOURCE_BOOK_ID: {
            "slug": "al-kafi",
            "structure_source": TAXONOMY_SOURCE,
            "taxonomy_version": TAXONOMY_VERSION,
        },
        FAQIH_SOURCE_BOOK_ID: {
            "slug": "faqih",
            "structure_source": "thaqalayn-structure-faqih",
            "taxonomy_version": "faqih-topics-v1",
        },
    }.get(source_book_id)
    if book_config is None:
        raise ValueError(f"No topic corpus configuration for {source_book_id}")
    slug_prefix = book_config["slug"]
    structure_source = book_config["structure_source"]
    taxonomy_version = book_config["taxonomy_version"]

    book = db.execute(
        select(Book).where(Book.source_book_id == source_book_id)
    ).scalar_one()
    all_hadith_ids = list(
        db.execute(select(Hadith.id).where(Hadith.book_id == book.id)).scalars()
    )
    hadiths = list(
        db.execute(
            select(Hadith)
            .where(
                Hadith.book_id == book.id,
                Hadith.review_status != "rejected_non_hadith_fragment",
            )
            .order_by(Hadith.sequence_in_book)
        ).scalars()
    )
    hadith_ids = [hadith.id for hadith in hadiths]
    structure_topic_ids = list(
        db.execute(
            select(Topic.id).where(
                Topic.source == structure_source
            )
        ).scalars()
    )
    semantic_topic_ids = list(
        db.execute(
            select(Topic.id).where(Topic.source == SEMANTIC_TAXONOMY_SOURCE)
        ).scalars()
    )
    # This builder owns every assignment for its configured book. Delete by
    # book membership rather than current topic IDs so assignments whose topic
    # was removed by an interrupted/older rebuild cannot survive as orphans.
    if all_hadith_ids:
        db.query(HadithTopicAssignment).filter(
            HadithTopicAssignment.hadith_id.in_(all_hadith_ids)
        ).delete(synchronize_session=False)
    if structure_topic_ids:
        db.query(Topic).filter(Topic.id.in_(structure_topic_ids)).delete(
            synchronize_session=False
        )
        db.flush()

    mappings = list(
        db.execute(
            select(ThaqalaynStructureMap)
            .join(Hadith, Hadith.id == ThaqalaynStructureMap.hadith_id)
            .where(
                Hadith.book_id == book.id,
                ThaqalaynStructureMap.source.in_(
                    ("thaqalayn-website", "thaqalayn-api")
                ),
            )
        ).scalars()
    )
    mapping_by_hadith = {mapping.hadith_id: mapping for mapping in mappings}
    translations_by_hadith = _preferred_translations(db, hadiths)
    anchors_by_volume: dict[int, list[tuple[int, ThaqalaynStructureMap]]] = defaultdict(list)
    sequence_by_id = {hadith.id: hadith.sequence_in_book for hadith in hadiths}
    for mapping in mappings:
        sequence = sequence_by_id.get(mapping.hadith_id)
        if sequence is not None:
            anchors_by_volume[mapping.volume].append((sequence, mapping))
    for anchors in anchors_by_volume.values():
        anchors.sort(key=lambda item: item[0])

    topics_by_key: dict[str, Topic] = {}
    semantic_topics_by_key: dict[str, Topic] = {}
    for topic in db.execute(
        select(Topic).where(Topic.source == SEMANTIC_TAXONOMY_SOURCE)
    ).scalars():
        semantic_topics_by_key[topic.source_key.rsplit(":", 1)[-1]] = topic
    assignments: list[HadithTopicAssignment] = []
    method_counts: Counter[str] = Counter()
    directly_placed = 0
    semantic_assignments = 0

    def get_topics(mapping: ThaqalaynStructureMap) -> tuple[Topic, Topic]:
        kitab_key = f"v:{mapping.volume}:k:{mapping.kitab_id}"
        raw_kitab_slug = _slug_text(mapping.kitab_id)
        kitab_slug = (
            raw_kitab_slug
            if raw_kitab_slug.startswith(f"v{mapping.volume}-k")
            else f"v{mapping.volume}-k{raw_kitab_slug}"
        )
        kitab = topics_by_key.get(kitab_key)
        if kitab is None:
            hashtag = topic_hashtag(mapping.kitab_name_en)
            kitab = Topic(
                slug=f"{slug_prefix}-{kitab_slug}",
                hashtag=hashtag,
                name_en=mapping.kitab_name_en,
                name_ar=None,
                kind="kitab",
                source=structure_source,
                source_key=f"{slug_prefix}:{kitab_key}",
                search_text=_topic_search_text(mapping.kitab_name_en, hashtag),
                aliases_json=[hashtag.removeprefix("#").replace("-", " ")],
            )
            db.add(kitab)
            db.flush()
            topics_by_key[kitab_key] = kitab
        chapter_key = f"{kitab_key}:c:{mapping.chapter_id}"
        chapter = topics_by_key.get(chapter_key)
        if chapter is None:
            hashtag = topic_hashtag(mapping.chapter_name_en)
            chapter = Topic(
                slug=(
                    f"{slug_prefix}-{kitab_slug}-c{mapping.chapter_id}"
                ),
                hashtag=hashtag,
                name_en=mapping.chapter_name_en,
                name_ar=None,
                kind="chapter",
                parent_id=kitab.id,
                source=structure_source,
                source_key=f"{slug_prefix}:{chapter_key}",
                search_text=_topic_search_text(mapping.chapter_name_en, hashtag),
                aliases_json=[hashtag.removeprefix("#").replace("-", " ")],
            )
            db.add(chapter)
            db.flush()
            topics_by_key[chapter_key] = chapter
        return kitab, chapter

    def get_semantic_topic(rule: SemanticTopicRule) -> Topic:
        topic = semantic_topics_by_key.get(rule.key)
        if topic is not None:
            return topic
        hashtag = f"#{rule.key}"
        topic = Topic(
            slug=f"al-kafi-{rule.kind}-{rule.key}",
            hashtag=hashtag,
            name_en=rule.name,
            name_ar=None,
            kind=rule.kind,
            source=SEMANTIC_TAXONOMY_SOURCE,
            source_key=f"semantic:{rule.kind}:{rule.key}",
            search_text=_semantic_search_text(rule, hashtag),
            aliases_json=list(rule.aliases),
        )
        db.add(topic)
        db.flush()
        semantic_topics_by_key[rule.key] = topic
        return topic

    for hadith in hadiths:
        mapping = mapping_by_hadith.get(hadith.id)
        if mapping is not None:
            directly_placed += 1
            method = (
                "structure_matched"
                if mapping.mapping_status == "matched"
                else "structure_interpolated"
            )
            confidence = (
                float(mapping.match_score)
                if mapping.match_score is not None
                else (0.95 if mapping.mapping_status == "matched" else 0.75)
            )
            evidence = {
                "structure_map_id": mapping.id,
                "mapping_status": mapping.mapping_status,
                "match_method": mapping.match_method,
            }
        else:
            anchors = anchors_by_volume.get(int(hadith.volume_start or 0), [])
            if not anchors:
                raise RuntimeError(
                    f"No structure anchor available for {hadith.public_id}"
                )
            mapping, method, confidence, evidence = _choose_nearest_structure(
                hadith, anchors
            )
        method_counts[method] += 1
        kitab, chapter = get_topics(mapping)
        provenance = {
            "taxonomy_version": taxonomy_version,
            "source": structure_source,
            "volume": mapping.volume,
            "kitab_id": mapping.kitab_id,
            "chapter_id": mapping.chapter_id,
            **evidence,
        }
        assignments.extend(
            [
                HadithTopicAssignment(
                    hadith_id=hadith.id,
                    topic_id=kitab.id,
                    relevance=100,
                    confidence=confidence,
                    assignment_method=method,
                    provenance_json=provenance,
                ),
                HadithTopicAssignment(
                    hadith_id=hadith.id,
                    topic_id=chapter.id,
                    relevance=90,
                    confidence=confidence,
                    assignment_method=method,
                    provenance_json=provenance,
                ),
            ]
        )

        structure_text = _normalise_english(
            f"{mapping.kitab_name_en} {mapping.chapter_name_en}"
        )
        translation = translations_by_hadith.get(hadith.id)
        translation_text = _normalise_english(
            translation.matn_translation if translation else ""
        )
        arabic_text = normalise_arabic_persian(hadith.matn_raw)
        semantic_candidates: list[
            tuple[int, float, SemanticTopicRule, str, dict]
        ] = []
        for rule in SEMANTIC_TOPIC_RULES:
            structure_matches = _english_matches(structure_text, rule.english_terms)
            translation_matches = _english_matches(
                translation_text, rule.english_terms
            )
            arabic_matches = _arabic_matches(arabic_text, rule.arabic_terms)
            evidence_count = sum(
                bool(matches)
                for matches in (
                    structure_matches,
                    translation_matches,
                    arabic_matches,
                )
            )
            if not evidence_count:
                continue
            if evidence_count >= 2:
                semantic_method = "semantic_multi_source"
                relevance = 92
                semantic_confidence = 0.95
            elif structure_matches:
                semantic_method = "semantic_structure"
                relevance = 88
                semantic_confidence = 0.92
            elif arabic_matches:
                semantic_method = "semantic_arabic"
                relevance = 82
                semantic_confidence = 0.86
            else:
                semantic_method = "semantic_translation"
                relevance = 74
                semantic_confidence = 0.8
            semantic_candidates.append(
                (
                    relevance,
                    semantic_confidence,
                    rule,
                    semantic_method,
                    {
                        "structure_terms": structure_matches,
                        "translation_terms": translation_matches,
                        "arabic_terms": arabic_matches,
                    },
                )
            )

        semantic_candidates.sort(key=lambda row: (-row[0], -row[1], row[2].key))
        for relevance, semantic_confidence, rule, semantic_method, matches in (
            semantic_candidates[:12]
        ):
            semantic_topic = get_semantic_topic(rule)
            assignments.append(
                HadithTopicAssignment(
                    hadith_id=hadith.id,
                    topic_id=semantic_topic.id,
                    relevance=relevance,
                    confidence=semantic_confidence,
                    assignment_method=semantic_method,
                    provenance_json={
                        "taxonomy_version": taxonomy_version,
                        "source": SEMANTIC_TAXONOMY_SOURCE,
                        "rule_key": rule.key,
                        "translation_version": (
                            translation.translation_version if translation else None
                        ),
                        **matches,
                    },
                )
            )
            semantic_assignments += 1
            method_counts[semantic_method] += 1
    db.add_all(assignments)
    db.flush()

    all_topics = [*topics_by_key.values(), *semantic_topics_by_key.values()]
    kind_counts = Counter(topic.kind for topic in all_topics)
    return TopicBuildStats(
        hadiths=len(hadiths),
        topics=len(all_topics),
        kitab_topics=kind_counts["kitab"],
        chapter_topics=kind_counts["chapter"],
        semantic_topics=len(semantic_topics_by_key),
        assignments=len(assignments),
        semantic_assignments=semantic_assignments,
        directly_placed=directly_placed,
        inherited_placed=len(hadiths) - directly_placed,
        method_counts=dict(sorted(method_counts.items())),
    )


def rebuild_alkafi_topics(db: Session) -> TopicBuildStats:
    return rebuild_book_topics(db, source_book_id=AL_KAFI_SOURCE_BOOK_ID)


def rebuild_faqih_topics(db: Session) -> TopicBuildStats:
    return rebuild_book_topics(db, source_book_id=FAQIH_SOURCE_BOOK_ID)
