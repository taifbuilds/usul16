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
    title: "The Shia hadith library.",
    subtitle:
      "The Four Books and later collections. Every report linked to the page it was printed on.",
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
    title: "Read, search, and trace narrators.",
    readBody: "In order, by chapter or by printed page.",
    readAction: "Open the library",
    findBody: "Arabic and English together, in one query.",
    findAction: "Search the collections",
    investigateBody: "Who a narrator heard from, and who heard from them.",
    investigateAction: "Browse the narrators",
  },
  collections: {
    title: "The Four Books and later works.",
    viewAll: "View the full catalogue",
  },
  evidence: {
    arabic: "من النص إلى الدليل",
    title: "What each record contains.",
    item1Title: "Arabic text",
    item1Body: "As printed — chain, body and footnotes kept distinct.",
    item2Title: "English translation",
    item2Body: "Alongside the Arabic, with its translator named.",
    item3Title: "Narrator profiles",
    item3Body: "Every name links to its narrator, with the evidence for the identification.",
    item4Title: "Transmission",
    item4Body: "How narrators connect, back to the reports that establish each link.",
    item5Title: "Citation",
    item5Body: "A stable reference to the volume, page and original scan.",
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
    eyebrow: "مكتبة للحديث الشيعي",
    title: "مكتبة الحديث الشيعي",
    subtitle:
      "الكتب الأربعة والمصنَّفات اللاحقة. ترتبط كل رواية بالصفحة المطبوعة التي وردت فيها.",
    hint1: "العربية والإنجليزية",
    hint2: "مجّانًا، بلا تسجيل",
    hint3: "مرتبط بالصفحة المطبوعة",
    openLibrary: "افتح المكتبة",
    narratorNetwork: "شبكة الرواة",
    folioRecord: "سجل بحثي",
    folioChainLabel: "الإسناد",
    folioSource: "المصدر المطبوع",
    folioSourceValue: "الكافي · ج ١ · ص ٣٠",
    folioKitab: "كتاب فضل العلم",
    folioVerified: "بيانات الإسناد",
  },
  stats: {
    intro: "الحالة الحالية للمكتبة.",
    readableBooks: "كتب متاحة للقراءة",
    digitisedPages: "صفحات مرقمنة",
    cataloguedWorks: "مصنَّفات مفهرسة",
    indexedAuthors: "مؤلِّفون مفهرسون",
    coverageLabel: "نطاق المصنَّفات",
  },
  paths: {
    title: "اقرأ، وابحث، وتتبَّع الرواة.",
    readBody: "على الترتيب، بابًا بابًا أو بحسب الصفحة المطبوعة.",
    readAction: "افتح المكتبة",
    findBody: "العربية والإنجليزية معًا، ببحثٍ واحد.",
    findAction: "ابحث في المصنَّفات",
    investigateBody: "عمّن روى الراوي، ومن روى عنه.",
    investigateAction: "تصفَّح الرواة",
  },
  collections: {
    title: "الكتب الأربعة وما تلاها من الأعمال.",
    viewAll: "اعرض الفهرس كاملًا",
  },
  evidence: {
    arabic: "من النص إلى الدليل",
    title: "محتويات كل سجل.",
    item1Title: "النصّ العربي",
    item1Body: "كما طُبع — مع تمييز السند والمتن والحواشي.",
    item2Title: "الترجمة الإنجليزية",
    item2Body: "إلى جانب العربية، مع ذكر المترجِم.",
    item3Title: "ملفات الرواة",
    item3Body: "يرتبط كل اسم بملف الراوي وبالأدلة المتاحة لتعيينه.",
    item4Title: "انتقال الرواية",
    item4Body: "صلة الرواة بعضهم ببعض، مع الرجوع إلى الروايات التي تدعم كل صلة.",
    item5Title: "الإحالة المرجعية",
    item5Body: "مرجعٌ ثابت إلى الجزء والصفحة والصورة الأصلية.",
  },
  cta: {
    title: "إتاحة مفتوحة.",
    body: "لا يتطلب حسابًا. المكتبة متاحة مجانًا للقراءة والبحث والاقتباس.",
    about: "عن المشروع",
    start: "ابدأ القراءة",
  },
  footer: {
    tagline:
      "اقرأ مصنَّفات الحديث الشيعي بالعربية والإنجليزية، وابحث في الرواة، وتتبع الأسانيد، مع إحالات إلى الصفحات المطبوعة.",
    arabicTagline: "الحديث الشيعي ومصادره",
    pathsHeading: "مسارات البحث",
    readCollections: "اقرأ المصنَّفات",
    searchCorpus: "ابحث في المصنَّفات",
    investigate: "تحقَّق في الأسانيد",
    corpusStatus: "حالة المصنَّفات والمنهجية",
    whatHeading: "محتوى السجل",
    whatBody:
      "العربية هي النص الأصل، وتُعرض الإنجليزية إلى جانبها مع نسبة الترجمة إلى صاحبها. تتضمن كل رواية إحالة إلى الجزء والصفحة المطبوعة.",
    aboutLink: "عن المشروع",
    bottomNote: "مفتوح ومجاني · مشروع مستقل · حالة المصنَّفات محدّثة",
  },
  about: {
    metaTitle: "عن المشروع",
    eyebrow: "عن أصول ١٦",
    title: "مكتبة للحديث الشيعي مرتبطة بمصادرها",
    lead: "مساحة لقراءة مصنَّفات الحديث الشيعي، والبحث في الرواة، وتتبع الأسانيد، مع إحالات إلى المصدر المطبوع.",
    currentCorpus: "المصنَّفات المتاحة حاليًا",
    digitisedPages: "صفحات مرقمنة",
    readableBooks: "كتب متاحة للقراءة",
    indexedAuthors: "مؤلِّفون مفهرسون",
    whatHeading: "ما هو المشروع؟",
    whatBody1:
      "يشمل تراث الحديث الشيعي عشرات الآلاف من الروايات: الكتب الأربعة (الكافي، ومن لا يحضره الفقيه، وتهذيب الأحكام، والاستبصار) ومصنَّفات تمتد عبر قرون. ويتوفر كثير منها في نسخ مصوَّرة، ومواقع قديمة، وترجمات متفرقة، مما يصعّب ربط النص المعروض بمصدره المطبوع.",
    whatBody2:
      "يجمع «أصول ١٦» هذه المواد ويربطها: النص العربي إلى جانب الترجمة الإنجليزية، والرواية إلى جانب سندها، واسم الراوي إلى جانب بيانات التعريف والأدلة المتاحة، مع الجزء والصفحة في الطبعة المطبوعة.",
    readingHeading: "كيفية قراءة المحتوى",
    readingBody1:
      "النص العربي والطبعة المطبوعة هما الأصل. وتُعرض الإنجليزية إلى جانبه مع نسبة الترجمة إلى صاحبها. وعند عرض تعيين راوٍ أو تحليل سند، تظهر الأدلة المتاحة معه.",
    readingBody2:
      "تُعرض بيانات المصدر والأدلة المتاحة مع نتائج البحث، ويمكن الرجوع إلى المصدر المطبوع من كل سجل.",
    goingHeading: "نطاق المشروع",
    goingBody:
      "المشروع في مرحلة تطوير. تبدأ أعمال المراجعة بالكتب الأربعة، ويظهر تقدم كل مصنَّف في صفحة حالة المصنَّفات والمنهجية. ويُضاف المحتوى بعد مراجعة مناسبة للمصدر والبيانات المرتبطة به.",
    openLibrary: "افتح المكتبة",
    inspectNetwork: "تفحَّص الشبكة",
    reviewStatus: "راجع حالة المصنَّفات",
  },
  methodology: {
    metaTitle: "حالة المصنَّفات والمنهجية",
    eyebrow: "المنهج البحثي",
    title: "المتاح، والأولي، وكيفية التحقق منه.",
    lead: "المصنَّفات في مراحل تحرير متفاوتة. وتُقرأ الأرقام في هذه الصفحة مباشرة من قاعدة البيانات لعرض حالة كل مصنَّف.",
    corpusHeading: "حالة كل مصنَّف",
    corpusSub: "ليس كل كتاب متاح للقراءة قد خضع بعد لمراجعة سطرية. يبيّن هذا الجدول الفرق.",
    liveCounts: "أعداد مباشرة من قاعدة البيانات",
    colCollection: "المصنَّف وحاله",
    colPages: "الصفحات",
    colHadiths: "الأحاديث",
    colChains: "أسانيد محلَّلة",
    colFlagged: "أسانيد معلَّمة للمراجعة",
    colEnglish: "إنجليزي منشور",
    countingHeading: "عدُّ الكافي",
    countingBody:
      "يعرض «أصول ١٦» حاليًّا ١٥٬٣٣٥ سجلًّا من الكافي بحسب الطبعة الممثَّلة. أمّا العدد الشائع ١٦٬١٩٩ فيتبع تقليدًا مختلفًا في العدّ. وقد تنشأ الفروق من حدود الطبعات، ومن روايات جُمعت أو فُصلت، والعناوين، والتكرار، وما رُفض من مخرجات التحليل؛ لذلك لا ينبغي اعتبار العددين متكافئين.",
    editorialHeading: "المنهج التحريري",
    editorialBody:
      "يبقى النص العربي وترقيم الطبعة المطبوعة مرجعين أساسيين. أمّا حدود الأحاديث، وتقطيع الأسانيد، وتعيين الرواة، والترجمات، فبيانات بحثية مضافة. وتحتفظ النتائج الآلية بحالات المراجعة والأدلة الداعمة لها.",
    citeHeading: "كيفية الإحالة العلمية",
    citeBody:
      "أحِل إلى العمل المطبوع وجزئه وصفحته أوّلًا، ثمّ أضف معرِّف «أصول ١٦» الثابت والرابط الدائم. وينبغي وصف نتائج الترجمة وتعيين الرواة بأنّها معيناتٌ بحثية ما لم تُصرِّح حالة مراجعتها بغير ذلك.",
  },
  books: {
    eyebrow: "مكتبة القراءة",
    title: "اختر مصنَّفًا",
    lead: "افتح أي مصنَّف واقرأه بحسب الأبواب، أو وفق صفحات الطبعة المطبوعة. وتتوافر إحالة إلى صفحة المصدر لكل نص.",
    arabicTitle: "المكتبة",
    availableToRead: "متاح للقراءة",
    completeCatalogue: "الفهرس الكامل",
    worksShown: "عملًا معروضًا في هذه الصفحة",
    stagesNote: "تُتاح المصنَّفات بمستويات مختلفة من المراجعة التحريرية.",
    seeStatus: "اطّلع على حالة المصنَّفات",
    catalogueView: "عرض الفهرس",
  },
};

const DICTIONARIES: Record<Locale, Dictionary> = { en, ar };

export function getDictionary(locale: Locale): Dictionary {
  return DICTIONARIES[locale] ?? en;
}
