import type { Locale } from "./config";

// English is the source of truth; the Arabic dictionary must match its shape.
// Only interface copy lives here — hadith text, narrator names and citations
// come from the API and are never machine-translated.

const en = {
  nav: {
    read: "Read",
    readDetail: "The library",
    find: "Find",
    findDetail: "Corpus search",
    investigate: "Investigate",
    investigateDetail: "Narrator network",
    about: "About",
    aboutProject: "About the project",
    searchCorpus: "Search corpus",
    brandSub: "Shia hadith research",
    skip: "Skip to content",
    toggleMenu: "Toggle navigation menu",
    primaryNav: "Primary navigation",
    mobileNav: "Mobile navigation",
  },
  search: {
    placeholder: "Search the Arabic and English…",
    submit: "Search",
  },
  hero: {
    eyebrow: "A growing Shia hadith library",
    title: "The major Shia hadith collections, in Arabic and English.",
    subtitle:
      "The Four Books and later collections: the original Arabic with its English translation, the narrators in each chain linked to their profiles, and every report tied to the page it was printed on.",
    hint1: "Arabic and English",
    hint2: "Free, no sign-up",
    hint3: "Linked to the printed page",
    openLibrary: "Open the library",
    narratorNetwork: "Narrator network",
    folioRecord: "Research record",
    folioChainLabel: "Transmission chain",
    folioSource: "Printed source",
    folioSourceValue: "Al-Kāfī · vol. 1 · p. 30",
    folioKitab: "كتاب فضل العلم",
    folioVerified: "Verified route",
  },
  stats: {
    intro: "Where the library stands today—still early, and growing.",
    readableBooks: "Readable books",
    digitisedPages: "Digitised pages",
    cataloguedWorks: "Catalogued works",
    indexedAuthors: "Indexed authors",
    coverageLabel: "Corpus coverage",
  },
  paths: {
    eyebrow: "Using the library",
    title: "Read, search, and trace narrators.",
    intro:
      "Read a collection in full, look up a specific narration, or follow a narrator across the tradition. Each report stays linked to its source.",
    readBody: "Read a collection in order, by chapter or by the pages of the printed edition.",
    readAction: "Open the library",
    findBody: "Search the Arabic and English together and open the matching report.",
    findAction: "Search the collections",
    investigateBody: "Open any narrator to see who they narrated from and who narrated from them.",
    investigateAction: "Browse the narrators",
  },
  collections: {
    eyebrow: "The collections",
    title: "The Four Books and later works.",
    viewAll: "View the full catalogue",
  },
  evidence: {
    arabic: "من النص إلى الدليل",
    title: "What each record contains.",
    intro:
      "Every hadith record brings together the Arabic text, its translation, the narrators in its chain, the wider transmission, and a citation back to the printed edition.",
    item1Title: "Arabic text",
    item1Body: "The narration as printed, with the chain, body, chapter headings, and footnotes kept distinct.",
    item2Title: "English translation",
    item2Body: "The English alongside the Arabic, with the translator and source named on each one.",
    item3Title: "Narrator profiles",
    item3Body: "Each name in the chain links to that narrator, with the evidence for the identification.",
    item4Title: "Transmission",
    item4Body: "How the narrators connect across the collections, linked back to the reports that establish each link.",
    item5Title: "Citation",
    item5Body: "A stable reference, checkable against the volume, page, and original scan.",
  },
  cta: {
    title: "Open access.",
    body: "No account required. The full library is free to read, search, and cite.",
    about: "About the project",
    start: "Start reading",
  },
  footer: {
    tagline:
      "Read the major Shia hadith collections in Arabic and English, look up every narrator, and trace each chain—all linked to the printed page.",
    arabicTagline: "أصول الحديث، موصولة بمصادرها",
    pathsHeading: "Research paths",
    readCollections: "Read the collections",
    searchCorpus: "Search the corpus",
    investigate: "Investigate transmissions",
    corpusStatus: "Corpus status and methodology",
    whatHeading: "What you're reading",
    whatBody:
      "The Arabic is the original; the English sits alongside it, credited to its translator. Every narration links back to its volume and page, so you can always check it yourself.",
    aboutLink: "About the project",
    bottomNote: "Free and open · An independent project · Live corpus status",
  },
  about: {
    metaTitle: "About",
    eyebrow: "About Usul16",
    title: "A source-linked library of Shia hadith.",
    lead: "One place to read the Shia hadith collections, look up the narrators, and follow the chains—without ever losing sight of the printed source.",
    currentCorpus: "Current corpus",
    digitisedPages: "Digitised pages",
    readableBooks: "Readable books",
    indexedAuthors: "Indexed authors",
    whatHeading: "What it is",
    whatBody1:
      "The Shia hadith tradition runs to tens of thousands of narrations—the Four Books (Al-Kāfī, Man Lā Yaḥḍuruhu al-Faqīh, Tahdhīb al-Aḥkām, and al-Istibṣār) and centuries of collections after them. Most of it lives in dense scans, ageing websites, and scattered translations, where it's hard to tell how anything on screen relates to the book it came from.",
    whatBody2:
      "Usul16 brings it together and keeps it connected: the Arabic beside its English, each report beside its chain, every narrator's name beside who they actually were, and all of it beside the volume and page it was printed on.",
    readingHeading: "How to read what you find",
    readingBody1:
      "The Arabic and the printed edition are the original. The English sits alongside to help you read it, named to its translator. Where we've identified a narrator or mapped a chain, the evidence is shown so you can weigh it yourself.",
    readingBody2:
      "Nothing here asks you to take its word for it. Whatever you're looking at, the source is one click away.",
    goingHeading: "Where it's going",
    goingBody:
      "This is a small project, still early, and built with care rather than haste. The Four Books come first, done properly—clean text, real translations, and narrator profiles you can trust—with Al-Kāfī furthest along. From there, God willing, the same care extends through Biḥār al-Anwār and the wider tradition, one collection at a time. The hope is simply that it keeps growing, and keeps serving.",
    openLibrary: "Open the library",
    inspectNetwork: "Inspect the network",
    reviewStatus: "Review corpus status",
  },
  methodology: {
    metaTitle: "Corpus status and methodology",
    eyebrow: "Research transparency",
    title: "What is ready, what is provisional, and how to verify it.",
    lead: "Different collections are at different stages of editing. Every number on this page is read live from the database, so you can see exactly where each one stands.",
    corpusHeading: "Where each collection stands",
    corpusSub: "A book you can read isn't always one we've checked line by line yet—this table shows the difference.",
    liveCounts: "Live database counts",
    colCollection: "Collection and state",
    colPages: "Pages",
    colHadiths: "Hadiths",
    colChains: "Parsed chains",
    colFlagged: "Chains flagged",
    colEnglish: "Public English",
    countingHeading: "Counting Al-Kafi",
    countingBody:
      "Usul16 currently exposes 15,335 Al-Kafi records from the represented edition. The often-cited total of 16,199 follows a different counting tradition. Differences can arise from edition boundaries, reports combined or separated, headings, repetitions, and rejected parser artefacts; the totals must not be treated as interchangeable.",
    editorialHeading: "Editorial model",
    editorialBody:
      "Source Arabic and printed pagination remain authoritative. Hadith boundaries, chain tokenisation, narrator resolution and translations are layered research data. Automated results retain review states and supporting evidence so they can be challenged and revised.",
    citeHeading: "How to cite responsibly",
    citeBody:
      "Cite the printed work, volume and page first, then include the stable Usul16 identifier and permanent URL. Translation and narrator conclusions should be described as research aids unless their review state says otherwise.",
  },
  books: {
    eyebrow: "The reading library",
    title: "Choose a collection.",
    lead: "Open any work like a book and read it by chapter, or follow the printed edition page by page. Whatever you're reading, its source page is always a click away.",
    arabicTitle: "المكتبة",
    availableToRead: "Available to read",
    completeCatalogue: "Complete catalogue",
    worksShown: "works shown on this page",
    stagesNote: "Collections are published at different stages of editorial review.",
    seeStatus: "See live corpus status",
    catalogueView: "Catalogue view",
  },
};

export type Dictionary = typeof en;

const ar: Dictionary = {
  nav: {
    read: "اقرأ",
    readDetail: "المكتبة",
    find: "ابحث",
    findDetail: "بحث في المصنَّفات",
    investigate: "تحقَّق",
    investigateDetail: "شبكة الرواة",
    about: "عن المشروع",
    aboutProject: "عن المشروع",
    searchCorpus: "ابحث في المصنَّفات",
    brandSub: "بحوث الحديث الشيعي",
    skip: "تخطَّ إلى المحتوى",
    toggleMenu: "إظهار قائمة التنقُّل",
    primaryNav: "التنقُّل الرئيسي",
    mobileNav: "تنقُّل الجوّال",
  },
  search: {
    placeholder: "ابحث في النص العربي والإنجليزي…",
    submit: "بحث",
  },
  hero: {
    eyebrow: "مكتبةٌ للحديث الشيعي في نموّ",
    title: "أمّهات مصنَّفات الحديث الشيعي، بالعربية والإنجليزية.",
    subtitle:
      "الكتب الأربعة وما تلاها من المصنَّفات: النصّ العربي الأصلي مع ترجمته الإنجليزية، ورواة كلّ سند موصولون بتراجمهم، وكلّ رواية مرتبطة بصفحتها المطبوعة.",
    hint1: "عربي وإنجليزي",
    hint2: "مجّاني، دون تسجيل",
    hint3: "موصول بالصفحة المطبوعة",
    openLibrary: "افتح المكتبة",
    narratorNetwork: "شبكة الرواة",
    folioRecord: "بطاقة بحثية",
    folioChainLabel: "سلسلة السند",
    folioSource: "المصدر المطبوع",
    folioSourceValue: "الكافي · ج ١ · ص ٣٠",
    folioKitab: "كتاب فضل العلم",
    folioVerified: "مسار موثَّق",
  },
  stats: {
    intro: "حال المكتبة اليوم — في بداياتها، وفي نموّ مستمرّ.",
    readableBooks: "كتب متاحة للقراءة",
    digitisedPages: "صفحات مرقمنة",
    cataloguedWorks: "مصنَّفات مفهرسة",
    indexedAuthors: "مؤلِّفون مفهرسون",
    coverageLabel: "نطاق المصنَّفات",
  },
  paths: {
    eyebrow: "استعمال المكتبة",
    title: "اقرأ، وابحث، وتتبَّع الرواة.",
    intro:
      "اقرأ مصنَّفًا كاملًا، أو ابحث عن روايةٍ بعينها، أو تتبَّع راويًا عبر التراث. تبقى كلّ رواية موصولةً بمصدرها.",
    readBody: "اقرأ المصنَّف على ترتيبه، بابًا بابًا أو بحسب صفحات الطبعة المطبوعة.",
    readAction: "افتح المكتبة",
    findBody: "ابحث في النصّ العربي والإنجليزي معًا وافتح الرواية المطابِقة.",
    findAction: "ابحث في المصنَّفات",
    investigateBody: "افتح أيّ راوٍ لترى عمّن روى ومن روى عنه.",
    investigateAction: "تصفَّح الرواة",
  },
  collections: {
    eyebrow: "المصنَّفات",
    title: "الكتب الأربعة وما تلاها من الأعمال.",
    viewAll: "اعرض الفهرس كاملًا",
  },
  evidence: {
    arabic: "من النص إلى الدليل",
    title: "ما تحتويه كلّ بطاقة.",
    intro:
      "تجمع كلّ بطاقة حديثٍ بين النصّ العربي وترجمته ورواة سنده والتحمُّل الأوسع، مع إحالةٍ إلى الطبعة المطبوعة.",
    item1Title: "النصّ العربي",
    item1Body: "الرواية كما طُبعت، مع تمييز السند والمتن وعناوين الأبواب والحواشي.",
    item2Title: "الترجمة الإنجليزية",
    item2Body: "الإنجليزية إلى جانب العربية، مع ذكر المترجِم والمصدر في كلّ واحدة.",
    item3Title: "تراجم الرواة",
    item3Body: "كلّ اسمٍ في السند موصولٌ بترجمة راويه، مع دليل التعيين.",
    item4Title: "التحمُّل والرواية",
    item4Body: "كيف يترابط الرواة عبر المصنَّفات، موصولًا بالروايات التي تُثبت كلّ صلة.",
    item5Title: "الإحالة",
    item5Body: "مرجعٌ ثابت، يمكن التحقُّق منه بالجزء والصفحة والصورة الأصلية.",
  },
  cta: {
    title: "وصولٌ مفتوح.",
    body: "دون حاجةٍ إلى حساب. المكتبة كاملةً متاحةٌ مجّانًا للقراءة والبحث والاقتباس.",
    about: "عن المشروع",
    start: "ابدأ القراءة",
  },
  footer: {
    tagline:
      "اقرأ أمّهات مصنَّفات الحديث الشيعي بالعربية والإنجليزية، وابحث في تراجم الرواة، وتتبَّع كلّ سند — والكلّ موصولٌ بالصفحة المطبوعة.",
    arabicTagline: "أصول الحديث، موصولة بمصادرها",
    pathsHeading: "مسارات البحث",
    readCollections: "اقرأ المصنَّفات",
    searchCorpus: "ابحث في المصنَّفات",
    investigate: "تحقَّق في الأسانيد",
    corpusStatus: "حال المصنَّفات والمنهج",
    whatHeading: "ما الذي تقرؤه",
    whatBody:
      "العربية هي الأصل؛ والإنجليزية تسير إلى جانبها منسوبةً إلى مترجِمها. كلّ روايةٍ موصولةٌ بجزئها وصفحتها، فلك أن تتحقَّق منها بنفسك دائمًا.",
    aboutLink: "عن المشروع",
    bottomNote: "مجّاني ومفتوح · مشروع مستقلّ · حال المصنَّفات مباشر",
  },
  about: {
    metaTitle: "عن المشروع",
    eyebrow: "عن أصول ١٦",
    title: "مكتبةٌ للحديث الشيعي موصولةٌ بمصادرها.",
    lead: "مكانٌ واحدٌ لقراءة مصنَّفات الحديث الشيعي، والبحث في تراجم الرواة، وتتبُّع الأسانيد — دون أن يغيب عنك المصدر المطبوع.",
    currentCorpus: "المصنَّفات الحالية",
    digitisedPages: "صفحات مرقمنة",
    readableBooks: "كتب متاحة للقراءة",
    indexedAuthors: "مؤلِّفون مفهرسون",
    whatHeading: "ما هو",
    whatBody1:
      "يمتدّ تراث الحديث الشيعي إلى عشرات الآلاف من الروايات — الكتب الأربعة (الكافي، ومن لا يحضره الفقيه، وتهذيب الأحكام، والاستبصار) وقرونٌ من المصنَّفات بعدها. وأكثره متناثرٌ في صورٍ مزدحمة، ومواقع قديمة، وترجماتٍ متفرِّقة، يصعب معها أن تعرف علاقة ما تراه بالكتاب الذي جاء منه.",
    whatBody2:
      "يجمع «أصول ١٦» ذلك ويُبقيه موصولًا: العربية إلى جانب إنجليزيتها، وكلّ رواية إلى جانب سندها، واسم كلّ راوٍ إلى جانب من كان في الحقيقة، وذلك كلّه إلى جانب الجزء والصفحة اللذين طُبع فيهما.",
    readingHeading: "كيف تقرأ ما تجده",
    readingBody1:
      "العربية والطبعة المطبوعة هما الأصل. والإنجليزية تسير إلى جانبها لتُعينك على قراءتها، منسوبةً إلى مترجِمها. وحيث عيَّنّا راويًا أو رسمنا سندًا، عُرض الدليل لتزنه بنفسك.",
    readingBody2:
      "لا شيء هنا يطلب منك أن تأخذ بقوله تسليمًا. فمهما نظرت إليه، فالمصدر على بُعد نقرةٍ واحدة.",
    goingHeading: "إلى أين يمضي",
    goingBody:
      "هذا مشروعٌ صغير، لا يزال في بداياته، بُني بعنايةٍ لا بعجلة. تأتي الكتب الأربعة أوّلًا، على وجهها الصحيح — نصٌّ نظيف، وترجماتٌ حقيقية، وتراجم رواةٍ يُوثَق بها — والكافي أبعدها شوطًا. ومن هناك، إن شاء الله، تمتدّ العناية نفسها إلى بحار الأنوار وسائر التراث، مصنَّفًا بعد مصنَّف. والأملُ ببساطةٍ أن يظلّ في نموّ، وأن يظلّ نافعًا.",
    openLibrary: "افتح المكتبة",
    inspectNetwork: "تفحَّص الشبكة",
    reviewStatus: "راجِع حال المصنَّفات",
  },
  methodology: {
    metaTitle: "حال المصنَّفات والمنهج",
    eyebrow: "شفافية بحثية",
    title: "ما الجاهز، وما المؤقَّت، وكيف تتحقَّق منه.",
    lead: "المصنَّفات في مراحل تحريرٍ متفاوتة. وكلّ رقمٍ في هذه الصفحة مقروءٌ مباشرةً من قاعدة البيانات، لترى بالضبط أين يقف كلّ واحد.",
    corpusHeading: "أين يقف كلّ مصنَّف",
    corpusSub: "الكتاب المتاح للقراءة ليس دائمًا كتابًا دقَّقناه سطرًا سطرًا بعد — وهذا الجدول يُبيِّن الفرق.",
    liveCounts: "أعداد مباشرة من قاعدة البيانات",
    colCollection: "المصنَّف وحاله",
    colPages: "الصفحات",
    colHadiths: "الأحاديث",
    colChains: "أسانيد محلَّلة",
    colFlagged: "أسانيد موسومة",
    colEnglish: "إنجليزي منشور",
    countingHeading: "عدُّ الكافي",
    countingBody:
      "يعرض «أصول ١٦» حاليًّا ١٥٬٣٣٥ سجلًّا من الكافي بحسب الطبعة الممثَّلة. أمّا العدد الشائع ١٦٬١٩٩ فيتبع تقليدًا مختلفًا في العدّ. وقد تنشأ الفروق من حدود الطبعات، ومن روايات جُمعت أو فُصلت، والعناوين، والتكرار، وما رُفض من مخرجات التحليل؛ ولا يجوز التعامل مع العددين على أنّهما متكافئان.",
    editorialHeading: "النموذج التحريري",
    editorialBody:
      "يبقى النصّ العربي والترقيم المطبوع هما الحجّة. أمّا حدود الأحاديث، وتقطيع الأسانيد، وتعيين الرواة، والترجمات، فبياناتٌ بحثيةٌ مضافة. وتحتفظ النتائج الآلية بحالات المراجعة وأدلّتها لتُناقَش وتُنقَّح.",
    citeHeading: "كيف تُحيل بأمانة",
    citeBody:
      "أحِل إلى العمل المطبوع وجزئه وصفحته أوّلًا، ثمّ أضف معرِّف «أصول ١٦» الثابت والرابط الدائم. وينبغي وصف نتائج الترجمة وتعيين الرواة بأنّها معيناتٌ بحثية ما لم تُصرِّح حالة مراجعتها بغير ذلك.",
  },
  books: {
    eyebrow: "مكتبة القراءة",
    title: "اختر مصنَّفًا.",
    lead: "افتح أيّ عملٍ كالكتاب واقرأه بابًا بابًا، أو اتبع الطبعة المطبوعة صفحةً صفحة. ومهما قرأت، فصفحة مصدره على بُعد نقرةٍ دائمًا.",
    arabicTitle: "المكتبة",
    availableToRead: "متاح للقراءة",
    completeCatalogue: "الفهرس الكامل",
    worksShown: "عملًا معروضًا في هذه الصفحة",
    stagesNote: "تُنشَر المصنَّفات في مراحل مراجعةٍ تحريريةٍ متفاوتة.",
    seeStatus: "اطَّلِع على حال المصنَّفات مباشرةً",
    catalogueView: "عرض الفهرس",
  },
};

const DICTIONARIES: Record<Locale, Dictionary> = { en, ar };

export function getDictionary(locale: Locale): Dictionary {
  return DICTIONARIES[locale] ?? en;
}
