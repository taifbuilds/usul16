# Faqih `needs_review` chains — Part 1 of 2

Chains **1–399** of **798** flagged `needs_review` by the isnad tokenizer in *Man lā yaḥḍuruhu al-Faqīh* (`source_book_id=11021`). These are almost all al-Ṣadūq's abbreviated «رَوَى فلان عن…» reports whose isnad boundary and/or opening path the tokenizer could not settle automatically.


## Second-pass resolution status

A second source-comparison pass was completed for every block previously labelled `ambiguous`. No generic `ambiguous` verdict remains. “Resolved” here means that the transmission structure is represented without guessing: explicit parallel sources are used where they identify an Imam; genuine *muḍmar* reports retain an unnamed Imam; genuinely unnamed intermediaries remain labelled as such; documentary transmissions and duplicate tokenizer records are distinguished from ordinary oral isnāds.

Second-pass outcomes among the former 26 entries:

- 17 entries were resolved by clear grammar, local continuation, or an explicit parallel source.
- 4 entries are explicitly classified as *muḍmar* rather than being assigned an unsupported Imam name: Chains 104, 121, 233, and 313.
- Chain 197 contains a genuinely unnamed intermediary stated by the source as «رَجُلًا».
- Chains 61/62 and 318/319 are two duplicated tokenizer pairs, not four independent reports.
- Chains 10 and 17 are documentary/epistolary transmissions and are represented accordingly.

## What a reviewer should produce

For **each** chain below, append a `CLARIFIED` block in this exact format so the output stays consistent:

```
### Chain {N} · `{public_id}` — CLARIFIED
- Transmitters (student → teacher): X → Y → … → [Imam, if named]
- Corrected isnad (Arabic): «…»
- Isnad ends / matn begins at: "first words of the true matn"
- Mursal opening: al-Ṣadūq → [first named narrator]; full path via Mashyakha = {known: … | omitted}
- Verdict: clean | needs_mashyakha_expansion | ambiguous
- Notes: …
```

Rules: do not invent narrators; if al-Ṣadūq's path to the first narrator is not in the text, mark it `omitted` (Mashyakha work). Keep the Arabic verbatim from the source. Uncertainty is stated, never guessed.

## Flag legend

- `matn_spill` — the isnad/matn boundary is uncertain — the extractor may have carried matn text into the chain (or cut it early). Decide where the isnad ends.
- `mursal_opening` — the report opens with al-Ṣadūq's abbreviated attribution («رَوَى فلان…» / «قال فلان…»). Al-Ṣadūq's own path TO the first named narrator is omitted; it lives in his Mashyakha. Flag it — never invent it.
- `no_imam_terminal` — the chain does not end at a recognised Imam token. Often fine (the report may not name an Imam, or the honorific wasn't matched).
- `co_narrator_expanded` — co-narrators («فلان و فلان جميعاً عن…») were split into parallel routes.
- `expanded` — the chain was expanded from co-narrators / conjunctions.
- `suspicious_token` — a token that does not look like a clean narrator name was detected.
- `multi_route` — a fork («وعن…») — more than one attachment point; the join is ambiguous.
- `citation_noise` — non-isnad citation/book text was detected inside the chain.

---

### Chain 1 · `faqih-302`
- **Location:** vol. 1, p. 126 · seq 303 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى عَبْدُ الرَّحِيمِ الْقَصِيرُ عَنْ أَبِي جَعْفَرٍ ع أَنَّهُ قَالَ- مَنْ أَخَذَ مِنْ أَظْفَارِهِ وَ شَارِبِهِ كُلَّ جُمُعَةٍ وَ قَالَ حِينَ يَأْخُذُهُ- بِسْمِ اللَّهِ وَ بِاللَّهِ وَ عَلَى سُنَّةِ مُحَمَّدٍ وَ آلِ مُحَمَّدٍ صَلَوَاتُ اللَّهِ عَلَيْهِمْ لَمْ تَسْقُطْ مِنْهُ قُلَامَةٌ وَ لَا جُزَازَةٌ[5] إِلَّا كَتَبَ اللَّهُ عَزَّ وَ جَلَّ لَهُ بِهَا عِتْقَ نَسَمَةٍ[6] وَ لَمْ يَمْرَضْ إِلَّا مَرَضَهُ الَّذِي يَمُوتُ فِيهِ.
- **Isnad as currently extracted:**
  > وَ رَوَى عَبْدُ الرَّحِيمِ الْقَصِيرُ عَنْ أَبِي جَعْفَرٍ ع أَنَّهُ قَالَ- مَنْ أَخَذَ مِنْ أَظْفَارِهِ وَ شَارِبِهِ كُلَّ جُمُعَةٍ وَ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عبد الرحیم القصیر | روی |  |
  | 1 | imam | ابی جعفر ع | عن |  |

### Chain 1 · `faqih-302` — CLARIFIED
- Transmitters (student → teacher): عبد الرحيم القصير → ابي جعفر ع
- Corrected isnad (Arabic): «وَ رَوَى عَبْدُ الرَّحِيمِ الْقَصِيرُ عَنْ أَبِي جَعْفَرٍ ع أَنَّهُ قَالَ»
- Isnad ends / matn begins at: "مَنْ أَخَذَ مِنْ أَظْفَارِهِ وَ شَارِبِهِ كُلَّ جُمُعَةٍ وَ"
- Mursal opening: al-Ṣadūq → عبد الرحيم القصير; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 2 · `faqih-463`
- **Location:** vol. 1, p. 163 · seq 464 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ- سَأَلْتُهُ عَنِ الْمَشْيِ مَعَ الْجَنَازَةِ فَقَالَ بَيْنَ يَدَيْهَا وَ عَنْ يَمِينِهَا وَ عَنْ شِمَالِهَا وَ خَلْفِهَا.
- **Isnad as currently extracted:**
  > وَ رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ- سَأَلْتُهُ عَنِ الْمَشْيِ مَعَ الْجَنَازَةِ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن مسلم | روی |  |
  | 1 | imam | احدهما ع | عن | ambiguous |

### Chain 2 · `faqih-463` — CLARIFIED
- Transmitters (student → teacher): محمد بن مسلم → احدهما ع
- Corrected isnad (Arabic): «وَ رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْمَشْيِ مَعَ الْجَنَازَةِ فَقَالَ بَيْنَ يَدَيْهَا وَ"
- Mursal opening: al-Ṣadūq → محمد بن مسلم; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 3 · `faqih-642`
- **Location:** vol. 1, p. 211 · seq 643 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رُوِيَ عَنِ الْحَسَنِ بْنِ عَلِيِّ بْنِ أَبِي طَالِبٍ ع أَنَّهُ قَالَ- جَاءَ نَفَرٌ مِنَ الْيَهُودِ إِلَى النَّبِيِّ ص فَسَأَلَهُ أَعْلَمُهُمْ عَنْ مَسَائِلَ فَكَانَ مِمَّا سَأَلَهُ أَنَّهُ قَالَ أَخْبِرْنِي‌
عَنِ اللَّهِ عَزَّ وَ جَلَّ لِأَيِّ شَيْ‌ءٍ فَرَضَ اللَّهُ عَزَّ وَ جَلَّ هَذِهِ الْخَمْسَ الصَّلَوَاتِ فِي خَمْسِ مَوَاقِيتَ عَلَى أُمَّتِكَ فِي سَاعَاتِ اللَّيْلِ وَ النَّهَارِ فَقَالَ النَّبِيُّ ص إِنَّ الشَّمْسَ عِنْدَ الزَّوَالِ لَهَا حَلْقَةٌ تَدْخُلُ فِيهَا[1] فَإِذَا دَخَلَتْ فِيهَا زَالَتِ الشَّمْسُ فَيُسَبِّحُ كُلُّ شَيْ‌ءٍ دُونَ الْعَرْشِ بِحَمْدِ رَبِّي جَلَّ جَلَالُهُ وَ هِيَ السَّاعَةُ[2] الَّتِي يُصَلِّي عَلَيَّ فِيهَا رَبِّي جَلَّ جَلَالُهُ فَفَرَضَ اللَّهُ عَلَيَّ وَ عَلَى أُمَّتِي فِيهَا الصَّلَاةَ وَ قَالَ‌ أَقِمِ الصَّلاةَ لِدُلُوكِ الشَّمْسِ إِلى‌ غَسَقِ اللَّيْلِ‌[3] وَ هِيَ السَّاعَةُ الَّتِي يُؤْتَى فِيهَا- بِجَهَنَّمَ يَوْمَ الْقِيَامَةِ فَمَا مِنْ مُؤْمِنٍ يُوَافِقُ تِلْكَ السَّاعَةَ أَنْ يَكُونَ سَاجِداً أَوْ رَاكِعاً أَوْ قَائِماً إِلَّا حَرَّمَ اللَّهُ جَسَدَهُ عَلَى النَّارِ وَ أَمَّا صَلَاةُ الْعَصْرِ فَهِيَ السَّاعَةُ الَّتِي أَكَلَ آدَمُ ع فِيهَا مِنَ الشَّجَرَةِ فَأَخْرَجَهُ اللَّهُ عَزَّ وَ جَلَّ مِنَ الْجَنَّةِ فَأَمَرَ اللَّهُ عَزَّ وَ جَلَّ ذُرِّيَّتَهُ بِهَذِهِ الصَّلَاةِ إِلَى يَوْمِ الْقِيَامَةِ وَ اخْتَارَهَا لِأُمَّتِي فَهِيَ مِنْ أَحَبِّ الصَّلَوَاتِ‌
و قال الفاضل التفرشى: فان قلت: السؤال ليس مختصا بالنبى صلّى اللّه عليه و آله و لا باهل الحرمين بل عام بالنسبة الى جميع الأمة و ظاهر أن الزوال مختلف بالنسبة الى البقاع التي تختلف طولها فلا يختص الزوال بوقت معين كما يستفاد من ظاهر العبارة. قلنا: يمكن الحمل على أنّها تدخل في الحلقة في نصف النهار من أول المعمورة و تخرج عنها في آخرها فكل جزء من ذلك الوقت زوال بالنسبة الى أهل بقعة تصل الشمس الى نصف نهارها، فاهل كل بقعة كانوا في ساعتهم راكعين و ساجدين حرم اللّه عزّ و جلّ جسدهم على النار، و لا يبعد أن يراد بالحلقة مجرى الشمس في الفلك كمجرى الحوت في الماء- ا ه. و لفظ« دون» فى قوله صلّى اللّه عليه و آله« دون العرش» بمعنى تحت.
إِلَى اللَّهِ عَزَّ وَ جَلَّ وَ أَوْصَانِي أَنْ أَحْفَظ …[truncated]
- **Isnad as currently extracted:**
  > رُوِيَ عَنِ اَلْحَسَنِ بْنِ عَلِيِّ بْنِ أَبِي طَالِبٍ عَلَيْهِ اَلسَّلاَمُ أَنَّهُ قَالَ - جَاءَ نَفَرٌ مِنَ اَلْيَهُودِ إِلَى اَلنَّبِيِّ صَلَّى اَللَّهُ عَلَيْهِ وَ آلِهِ فَسَأَلَهُ أَعْلَمُهُمْ عَنْ مَسَائِلَ فَكَانَ مِمَّا سَأَلَهُ أَنَّهُ قَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | imam | عن الحسن بن علی بن ابی طالب علیه السلام | روی |  |

### Chain 3 · `faqih-642` — CLARIFIED
- Transmitters (student → teacher): الحسن بن علي بن ابي طالب عليه السلام
- Corrected isnad (Arabic): «رُوِيَ عَنِ الْحَسَنِ بْنِ عَلِيِّ بْنِ أَبِي طَالِبٍ ع أَنَّهُ قَالَ»
- Isnad ends / matn begins at: "جَاءَ نَفَرٌ مِنَ الْيَهُودِ إِلَى النَّبِيِّ ص فَسَأَلَهُ أَعْلَمُهُمْ"
- Mursal opening: al-Ṣadūq → الحسن بن علي بن ابي طالب عليه السلام; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 4 · `faqih-643`
- **Location:** vol. 1, p. 214 · seq 644 · chain 1
- **Flags:** `matn_spill`
- **Full report (Arabic):**
  > مَا رَوَاهُ الْحُسَيْنُ بْنُ أَبِي الْعَلَاءِ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ- لَمَّا أُهْبِطَ آدَمُ مِنَ الْجَنَّةِ- ظَهَرَتْ بِهِ شَامَةٌ سَوْدَاءُ فِي وَجْهِهِ مِنْ قَرْنِهِ إِلَى قَدَمِهِ‌[1] فَطَالَ حُزْنُهُ وَ بُكَاؤُهُ عَلَى مَا ظَهَرَ بِهِ فَأَتَاهُ جَبْرَئِيلُ ع فَقَالَ لَهُ مَا يُبْكِيكَ يَا آدَمُ فَقَالَ مِنْ هَذِهِ الشَّامَةِ الَّتِي ظَهَرَتِ بِي قَالَ قُمْ يَا آدَمُ فَصَلِّ فَهَذَا وَقْتُ الصَّلَاةِ الْأُولَى‌[2] فَقَامَ فَصَلَّى فَانْحَطَّتِ الشَّامَةُ إِلَى عُنُقِهِ‌[3] فَجَاءَهُ فِي الصَّلَاةِ الثَّانِيَةِ فَقَالَ قُمْ فَصَلِّ يَا آدَمُ- فَهَذَا وَقْتُ الصَّلَاةِ الثَّانِيَةِ فَقَامَ فَصَلَّى فَانْحَطَّتِ الشَّامَةُ إِلَى سُرَّتِهِ فَجَاءَهُ فِي الصَّلَاةِ الثَّالِثَةِ فَقَالَ يَا آدَمُ قُمْ فَصَلِّ فَهَذَا وَقْتُ الصَّلَاةِ الثَّالِثَةِ فَقَامَ فَصَلَّى فَانْحَطَّتِ الشَّامَةُ إِلَى رُكْبَتَيْهِ فَجَاءَهُ فِي الصَّلَاةِ الرَّابِعَةِ فَقَالَ يَا آدَمُ قُمْ فَصَلِّ فَهَذَا وَقْتُ الصَّلَاةِ الرَّابِعَةِ فَقَامَ فَصَلَّى فَانْحَطَّتِ الشَّامَةُ إِلَى قَدَمَيْهِ فَجَاءَهُ فِي الصَّلَاةِ الْخَامِسَةِ فَقَالَ يَا آدَمُ قُمْ فَصَلِّ فَهَذَا وَقْتُ الصَّلَاةِ الْخَامِسَةِ فَقَامَ فَصَلَّى فَخَرَجَ مِنْهَا فَحَمِدَ اللَّهَ وَ أَثْنَى عَلَيْهِ فَقَالَ جَبْرَئِيلُ ع يَا آدَمُ- مَثَلُ وُلْدِكَ فِي هَذِهِ الصَّلَوَاتِ كَمَثَلِكَ فِي هَذِهِ الشَّامَةِ مَنْ صَلَّى مِنْ وُلْدِكَ فِي كُلِّ يَوْمٍ وَ لَيْلَةٍ خَمْسَ صَلَوَاتٍ خَرَجَ مِنْ ذُنُوبِهِ كَمَا خَرَجْتَ مِنْ هَذِهِ الشَّامَةِ.
عِلَّةٌ أُخْرَى لِوُجُوبِ الصَّلَاةِ.
- **Isnad as currently extracted:**
  > مَا رَوَاهُ الْحُسَيْنُ بْنُ أَبِي الْعَلَاءِ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ- لَمَّا أُهْبِطَ آدَمُ مِنَ الْجَنَّةِ- ظَهَرَتْ بِهِ شَامَةٌ سَوْدَاءُ فِي وَجْهِهِ مِنْ قَرْنِهِ إِلَى قَدَمِهِ‌[1] فَطَالَ حُزْنُهُ وَ بُكَاؤُهُ عَلَى مَا ظَهَرَ بِهِ فَأَتَاهُ جَبْرَئِيلُ ع فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسین بن ابی العلاء | رواه |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 4 · `faqih-643` — CLARIFIED
- Transmitters (student → teacher): الحسين بن ابي العلاء → ابي عبد الله ع
- Corrected isnad (Arabic): «مَا رَوَاهُ الْحُسَيْنُ بْنُ أَبِي الْعَلَاءِ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ»
- Isnad ends / matn begins at: "لَمَّا أُهْبِطَ آدَمُ مِنَ الْجَنَّةِ- ظَهَرَتْ بِهِ شَامَةٌ سَوْدَاءُ"
- Mursal opening: al-Ṣadūq → الحسين بن ابي العلاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 5 · `faqih-890`
- **Location:** vol. 1, p. 288 · seq 891 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى حَارِثُ بْنُ الْمُغِيرَةِ النَّضْرِيُ‌[1] عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ- مَنْ سَمِعَ الْمُؤَذِّنَ يَقُولُ- أَشْهَدُ أَنْ لَا إِلَهَ إِلَّا اللَّهُ وَ أَشْهَدُ أَنَّ مُحَمَّداً رَسُولُ اللَّهِ فَقَالَ مُصَدِّقاً مُحْتَسِباً وَ أَنَا أَشْهَدُ أَنْ لَا إِلَهَ إِلَّا اللَّهُ وَ أَشْهَدُ أَنَّ مُحَمَّداً رَسُولُ اللَّهِ أَكْتَفِي بِهِمَا[2] عَنْ كُلِّ مَنْ أَبَى وَ جَحَدَ وَ أُعِينُ بِهِمَا مَنْ أَقَرَّ وَ شَهِدَ كَانَ لَهُ مِنَ الْأَجْرِ عَدَدُ مَنْ أَنْكَرَ وَ جَحَدَ وَ عَدَدُ مَنْ أَقَرَّ وَ شَهِدَ.
- **Isnad as currently extracted:**
  > وَ رَوَى حَارِثُ بْنُ الْمُغِيرَةِ النَّضْرِيُ‌[1] عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ- مَنْ سَمِعَ الْمُؤَذِّنَ يَقُولُ- أَشْهَدُ أَنْ لَا إِلَهَ إِلَّا اللَّهُ وَ أَشْهَدُ أَنَّ مُحَمَّداً رَسُولُ اللَّهِ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حارث بن المغیرة النضری | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 5 · `faqih-890` — CLARIFIED
- Transmitters (student → teacher): حارث بن المغيرة النضري → ابي عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى حَارِثُ بْنُ الْمُغِيرَةِ النَّضْرِيُ‌[1] عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ»
- Isnad ends / matn begins at: "مَنْ سَمِعَ الْمُؤَذِّنَ يَقُولُ- أَشْهَدُ أَنْ لَا إِلَهَ إِلَّا"
- Mursal opening: al-Ṣadūq → حارث بن المغيرة النضري; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 6 · `faqih-978`
- **Location:** vol. 1, p. 333 · seq 979 · chain 1
- **Flags:** `mursal_opening`, `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > وَ رَوَى أَحْمَدُ بْنُ أَبِي عَبْدِ اللَّهِ عَنْ أَبِيهِ عَنْ مُحَمَّدِ بْنِ أَبِي عُمَيْرٍ عَنْ حَرِيزٍ عَنْ مُرَازِمٍ عَنْ أَبِي عَبْدِ اللَّهِ ع‌ سَجْدَةُ الشُّكْرِ وَاجِبَةٌ عَلَى كُلِّ مُسْلِمٍ‌[6] تُتِمُّ بِهَا صَلَاتَكَ وَ تُرْضِي بِهَا رَبَّكَ وَ تَعْجَبُ الْمَلَائِكَةُ مِنْكَ وَ إِنَّ الْعَبْدَ إِذَا صَلَّى ثُمَّ سَجَدَ سَجْدَةَ
الشُّكْرِ فَتَحَ الرَّبُّ تَبَارَكَ وَ تَعَالَى الْحِجَابَ بَيْنَ الْعَبْدِ وَ بَيْنَ الْمَلَائِكَةِ فَيَقُولُ يَا مَلَائِكَتِي انْظُرُوا إِلَى عَبْدِي أَدَّى فَرْضِي وَ أَتَمَّ عَهْدِي ثُمَّ سَجَدَ لِي شُكْراً عَلَى مَا أَنْعَمْتُ بِهِ عَلَيْهِ مَلَائِكَتِي مَا ذَا لَهُ عِنْدِي قَالَ فَتَقُولُ الْمَلَائِكَةُ يَا رَبَّنَا رَحْمَتُكَ ثُمَّ يَقُولُ الرَّبُّ تَبَارَكَ وَ تَعَالَى ثُمَّ مَا ذَا لَهُ فَتَقُولُ الْمَلَائِكَةُ يَا رَبَّنَا جَنَّتُكَ ثُمَّ يَقُولُ الرَّبُّ تَبَارَكَ وَ تَعَالَى ثُمَّ مَا ذَا فَتَقُولُ الْمَلَائِكَةُ يَا رَبَّنَا كِفَايَةُ مُهِمِّهِ فَيَقُولُ الرَّبُّ تَبَارَكَ وَ تَعَالَى ثُمَّ مَا ذَا قَالَ وَ لَا يَبْقَى شَيْ‌ءٌ مِنَ الْخَيْرِ إِلَّا قَالَتْهُ الْمَلَائِكَةُ فَيَقُولُ اللَّهُ تَبَارَكَ وَ تَعَالَى يَا مَلَائِكَتِي ثُمَّ مَا ذَا فَتَقُولُ الْمَلَائِكَةُ رَبَّنَا لَا عِلْمَ لَنَا قَالَ فَيَقُولُ اللَّهُ تَبَارَكَ وَ تَعَالَى أَشْكُرُ لَهُ كَمَا شَكَرَ لِي وَ أُقْبِلُ إِلَيْهِ بِفَضْلِي وَ أُرِيهِ وَجْهِي.
- **Isnad as currently extracted:**
  > وَ رَوَى أَحْمَدُ بْنُ أَبِي عَبْدِ اللَّهِ عَنْ أَبِيهِ عَنْ مُحَمَّدِ بْنِ أَبِي عُمَيْرٍ عَنْ حَرِيزٍ عَنْ مُرَازِمٍ عَنْ أَبِي عَبْدِ اللَّهِ ع‌ سَجْدَةُ الشُّكْرِ وَاجِبَةٌ عَلَى كُلِّ مُسْلِمٍ‌[6] تُتِمُّ بِهَا صَلَاتَكَ وَ تُرْضِي بِهَا رَبَّكَ وَ تَعْجَبُ الْمَلَائِكَةُ مِنْكَ وَ إِنَّ الْعَبْدَ إِذَا صَلَّى ثُمَّ سَجَدَ سَجْدَةَ الشُّكْرِ فَتَحَ الرَّبُّ تَبَارَكَ وَ تَعَالَى الْحِجَابَ بَيْنَ الْعَبْدِ وَ بَيْنَ الْمَلَائِكَةِ فَيَقُولُ
- **Current node split (6 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | احمد بن ابی عبد الله | روی |  |
  | 1 | pronoun_relation | ابیه | عن | father |
  | 2 | named_narrator | محمد بن ابی عمیر | عن |  |
  | 3 | named_narrator | حریز | عن |  |
  | 4 | named_narrator | مرازم | عن |  |
  | 5 | named_narrator | ابی عبد الله ع سجدة الشکر واجبة علی کل مسلم تتم بها صلاتک و ترضی بها ربک و تعجب الملائکة منک و ان العبد اذا صلی ثم سجد سجدة الشکر فتح الرب تبارک و تعالی الحجاب بین العبد و بین الملائکة فیقول | عن |  |

### Chain 6 · `faqih-978` — CLARIFIED
- Transmitters (student → teacher): أحمد بن أبي عبد الله → أبيه (غير مسمّى في النص) → محمد بن أبي عمير → حريز → مرازم → أبو عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى أَحْمَدُ بْنُ أَبِي عَبْدِ اللَّهِ عَنْ أَبِيهِ عَنْ مُحَمَّدِ بْنِ أَبِي عُمَيْرٍ عَنْ حَرِيزٍ عَنْ مُرَازِمٍ عَنْ أَبِي عَبْدِ اللَّهِ ع‌»
- Isnad ends / matn begins at: "سَجْدَةُ الشُّكْرِ وَاجِبَةٌ عَلَى كُلِّ مُسْلِمٍ‌[6] تُتِمُّ بِهَا صَلَاتَكَ"
- Mursal opening: al-Ṣadūq → أحمد بن أبي عبد الله; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name.

---

### Chain 7 · `faqih-991`
- **Location:** vol. 1, p. 339 · seq 992 · chain 1
- **Flags:** `citation_noise`
- **Full report (Arabic):**
  > وَ رَوَى زُرَارَةُ عَنْ أَبِي جَعْفَرٍ ع أَنَّهُ قَالَ: لَا تُعَادُ الصَّلَاةُ إِلَّا مِنْ خَمْسَةٍ[3] الطَّهُورِ وَ الْوَقْتِ وَ الْقِبْلَةِ وَ الرُّكُوعِ وَ السُّجُودِ ثُمَّ قَالَ الْقِرَاءَةُ سُنَّةٌ وَ التَّشَهُّدُ
سُنَّةٌ وَ لَا تَنْقُضُ السُّنَّةُ الْفَرِيضَةَ[1].
وَ الْأَصْلُ فِي السَّهْوِ أَنَّ مَنْ سَهَا فِي الرَّكْعَتَيْنِ الْأَوَّلَتَيْنِ‌[2] مِنْ كُلِّ صَلَاةٍ فَعَلَيْهِ الْإِعَادَةُ وَ مَنْ شَكَّ فِي الْمَغْرِبِ فَعَلَيْهِ الْإِعَادَةُ وَ مَنْ شَكَّ فِي الْغَدَاةِ فَعَلَيْهِ الْإِعَادَةُ وَ مَنْ شَكَّ فِي الْجُمُعَةِ فَعَلَيْهِ الْإِعَادَةُ وَ مَنْ شَكَّ فِي الثَّانِيَةِ وَ الثَّالِثَةِ أَوْ فِي الثَّالِثَةِ وَ الرَّابِعَةِ أَخَذَ بِالْأَكْثَرِ فَإِذَا سَلَّمَ أَتَمَّ مَا ظَنَّ أَنَّهُ قَدْ نَقَصَ.
- **Isnad as currently extracted:**
  > 991 وَ رَوَى زُرَارَةُ عَنْ أَبِي جَعْفَرٍ عَلَيْهِ اَلسَّلاَمُ أَنَّهُ قَالَ:
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | زرارة | روی |  |
  | 1 | imam | ابی جعفر علیه السلام | عن |  |

### Chain 7 · `faqih-991` — CLARIFIED
- Transmitters (student → teacher): زرارة → ابي جعفر عليه السلام
- Corrected isnad (Arabic): «وَ رَوَى زُرَارَةُ عَنْ أَبِي جَعْفَرٍ ع أَنَّهُ قَالَ»
- Isnad ends / matn begins at: "لَا تُعَادُ الصَّلَاةُ إِلَّا مِنْ خَمْسَةٍ[3] الطَّهُورِ وَ الْوَقْتِ"
- Mursal opening: al-Ṣadūq → زرارة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. Numeric/citation material is not part of the isnād.

---

### Chain 8 · `faqih-1001`
- **Location:** vol. 1, p. 343 · seq 1002 · chain 1
- **Flags:** `matn_spill`
- **Full report (Arabic):**
  > وَ قَدْ رَوَى زُرَارَةُ[3] عَنْ أَبِي جَعْفَرٍ ع قَالَ- قُلْتُ لَهُ رَجُلٌ نَسِيَ أَوَّلَ تَكْبِيرَةِ الِافْتِتَاحِ فَقَالَ إِنْ ذَكَرَهَا قَبْلَ الرُّكُوعِ كَبَّرَ ثُمَّ قَرَأَ ثُمَّ رَكَعَ وَ إِنْ ذَكَرَهَا فِي الصَّلَاةِ كَبَّرَهَا فِي مَقَامِهِ فِي مَوْضِعِ التَّكْبِيرِ قَبْلَ الْقِرَاءَةِ أَوْ بَعْدَ الْقِرَاءَةِ قُلْتُ فَإِنْ ذَكَرَهَا بَعْدَ الصَّلَاةِ قَالَ فَلْيَقْضِهَا[4] وَ لَا شَيْ‌ءَ عَلَيْهِ.
- **Isnad as currently extracted:**
  > وَ قَدْ رَوَى زُرَارَةُ[3] عَنْ أَبِي جَعْفَرٍ ع قَالَ- قُلْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | قد |  |  |
  | 1 | named_narrator | زرارة | روی |  |
  | 2 | imam | ابی جعفر ع | عن |  |

### Chain 8 · `faqih-1001` — CLARIFIED
- Transmitters (student → teacher): زرارة → ابي جعفر ع
- Corrected isnad (Arabic): «وَ قَدْ رَوَى زُرَارَةُ[3] عَنْ أَبِي جَعْفَرٍ ع قَالَ»
- Isnad ends / matn begins at: "قُلْتُ لَهُ رَجُلٌ نَسِيَ أَوَّلَ تَكْبِيرَةِ الِافْتِتَاحِ فَقَالَ إِنْ"
- Mursal opening: al-Ṣadūq → زرارة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 9 · `faqih-1236`
- **Location:** vol. 1, p. 419 · seq 1237 · chain 1
- **Flags:** `mursal_opening`, `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > وَ رَوَى عَبْدُ الرَّحْمَنِ بْنُ الْحَجَّاجِ‌[2] عَنْ أَبِي الْحَسَنِ ع‌ فِي رَجُلٍ صَلَّى فِي جَمَاعَةٍ يَوْمَ الْجُمُعَةِ فَلَمَّا رَكَعَ الْإِمَامُ الْجَأَهُ النَّاسُ إِلَى جِدَارٍ أَوْ أُسْطُوَانَةٍ فَلَمْ يَقْدِرْ عَلَى أَنْ يَرْكَعَ وَ لَا أَنْ يَسْجُدَ حَتَّى يَرْفَعَ الْقَوْمُ رُءُوسَهُمْ أَ يَرْكَعُ ثُمَّ يَسْجُدُ وَ يَلْحَقُ بِالصَّفِّ وَ قَدْ قَامَ الْقَوْمُ أَمْ كَيْفَ يَصْنَعُ فَقَالَ يَرْكَعُ وَ يَسْجُدُ ثُمَّ يَقُومُ فِي الصَّفِّ وَ لَا بَأْسَ بِذَلِكَ.
- **Isnad as currently extracted:**
  > وَ رَوَى عَبْدُ الرَّحْمَنِ بْنُ الْحَجَّاجِ‌[2] عَنْ أَبِي الْحَسَنِ ع‌ فِي رَجُلٍ صَلَّى فِي جَمَاعَةٍ يَوْمَ الْجُمُعَةِ فَلَمَّا رَكَعَ الْإِمَامُ الْجَأَهُ النَّاسُ إِلَى جِدَارٍ أَوْ أُسْطُوَانَةٍ فَلَمْ يَقْدِرْ عَلَى أَنْ يَرْكَعَ وَ لَا أَنْ يَسْجُدَ حَتَّى يَرْفَعَ الْقَوْمُ رُءُوسَهُمْ أَ يَرْكَعُ ثُمَّ يَسْجُدُ وَ يَلْحَقُ بِالصَّفِّ وَ قَدْ قَامَ الْقَوْمُ أَمْ كَيْفَ يَصْنَعُ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عبد الرحمن بن الحجاج | روی |  |
  | 1 | named_narrator | ابی الحسن ع فی رجل صلی فی جماعة یوم الجمعة فلما رکع الامام الجاه الناس الی جدار او اسطوانة فلم یقدر علی ان یرکع و لا ان یسجد حتی یرفع القوم رءوسهم ا یرکع ثم یسجد و یلحق بالصف و قد قام القوم ام کیف یصنع فقال | عن |  |

### Chain 9 · `faqih-1236` — CLARIFIED
- Transmitters (student → teacher): عبد الرحمن بن الحجاج → أبو الحسن ع
- Corrected isnad (Arabic): «وَ رَوَى عَبْدُ الرَّحْمَنِ بْنُ الْحَجَّاجِ‌[2] عَنْ أَبِي الْحَسَنِ ع‌»
- Isnad ends / matn begins at: "فِي رَجُلٍ صَلَّى فِي جَمَاعَةٍ يَوْمَ الْجُمُعَةِ فَلَمَّا رَكَعَ"
- Mursal opening: al-Ṣadūq → عبد الرحمن بن الحجاج; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name.

---

### Chain 10 · `faqih-1427`
- **Location:** vol. 1, p. 498 · seq 1429 · chain 1
- **Flags:** `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > عَنْ أَبِي الْحُسَيْنِ مُحَمَّدِ بْنِ جَعْفَرٍ الْأَسَدِيِّ رَضِيَ اللَّهُ عَنْهُ أَنَّهُ وَرَدَ عَلَيْهِ فِيمَا وَرَدَ مِنْ جَوَابِ مَسَائِلِهِ مِنْ مُحَمَّدِ بْنِ عُثْمَانَ الْعَمْرِيِّ قَدَّسَ اللَّهُ رُوحَهُ‌ وَ أَمَّا مَا سَأَلْتَ عَنْهُ مِنَ الصَّلَاةِ عِنْدَ طُلُوعِ الشَّمْسِ وَ عِنْدَ غُرُوبِهَا فَلَئِنْ كَانَ كَمَا يَقُولُ النَّاسُ إِنَّ الشَّمْسَ تَطْلُعُ بَيْنَ قَرْنَيْ شَيْطَانٍ وَ تَغْرُبُ بَيْنَ قَرْنَيْ شَيْطَانٍ فَمَا أُرْغِمَ أَنْفُ الشَّيْطَانِ بِشَيْ‌ءٍ أَفْضَلَ مِنَ الصَّلَاةِ فَصَلِّهَا وَ أَرْغِمْ أَنْفَ الشَّيْطَانِ‌[1].
- **Isnad as currently extracted:**
  > عَنْ أَبِي الْحُسَيْنِ مُحَمَّدِ بْنِ جَعْفَرٍ الْأَسَدِيِّ رَضِيَ اللَّهُ عَنْهُ أَنَّهُ وَرَدَ عَلَيْهِ فِيمَا وَرَدَ مِنْ جَوَابِ مَسَائِلِهِ مِنْ مُحَمَّدِ بْنِ عُثْمَانَ الْعَمْرِيِّ قَدَّسَ اللَّهُ رُوحَهُ‌ وَ أَمَّا مَا سَأَلْتَ عَنْهُ مِنَ الصَّلَاةِ عِنْدَ طُلُوعِ الشَّمْسِ وَ عِنْدَ غُرُوبِهَا فَلَئِنْ كَانَ كَمَا يَقُولُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابی الحسین محمد بن جعفر الاسدی انه ورد علیه فیما ورد من جواب مسائله من محمد بن عثمان العمری قدس الله روحه و اما ما سالت عنه من الصلاة عند طلوع الشمس و عند غروبها فلئن کان کما | عن |  |

### Chain 10 · `faqih-1427` — CLARIFIED
- Transmitters (student → teacher): أبو الحسين محمد بن جعفر الأسدي → محمد بن عثمان العمري → الإمام المهدي صاحب الزمان ع (توقيعٌ خرج في جواب المسائل)
- Corrected isnad (Arabic): «عَنْ أَبِي الْحُسَيْنِ مُحَمَّدِ بْنِ جَعْفَرٍ الْأَسَدِيِّ رَضِيَ اللَّهُ عَنْهُ أَنَّهُ وَرَدَ عَلَيْهِ فِيمَا وَرَدَ مِنْ جَوَابِ مَسَائِلِهِ مِنْ مُحَمَّدِ بْنِ عُثْمَانَ الْعَمْرِيِّ قَدَّسَ اللَّهُ رُوحَهُ‌»
- Isnad ends / matn begins at: "وَ أَمَّا مَا سَأَلْتَ عَنْهُ مِنَ الصَّلَاةِ عِنْدَ طُلُوعِ"
- Mursal opening: al-Ṣadūq → أبو الحسين محمد بن جعفر الأسدي; full path via Mashyakha = omitted in this excerpt; the parallel in *Kamāl al-Dīn* names محمد بن أحمد الشيباني + علي بن أحمد الدقاق + الحسين بن إبراهيم المؤدب + علي بن عبد الله الوراق → محمد بن جعفر الأسدي
- Verdict: needs_mashyakha_expansion
- Notes: This is a documentary tawqīʿ, not a bare report from Muḥammad b. ʿUthmān on his own authority. The parallel explicitly says that al-Asadī’s questions were addressed «إِلَى صَاحِبِ الزَّمَانِ» and that the response came through the second deputy. Sources: [Jāmiʿ Aḥādīth al-Shīʿa, vol. 4, p. 259](https://lib.eshia.ir/10565/4/259); [Biḥār al-Anwār, vol. 83, p. 146](https://lib.eshia.ir/11008/83/146).
---

### Chain 11 · `faqih-1486`
- **Location:** vol. 1, p. 522 · seq 1488 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى الْحَلَبِيُّ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ- فِي صَلَاةِ الْعِيدَيْنِ إِذَا كَانَ الْقَوْمُ خَمْسَةً أَوْ سَبْعَةً فَإِنَّهُمْ يُجَمِّعُونَ الصَّلَاةَ[4] كَمَا يَصْنَعُونَ يَوْمَ الْجُمُعَةِ
وَ قَالَ يَقْنُتُ فِي الرَّكْعَةِ الثَّانِيَةِ قَالَ قُلْتُ يَجُوزُ بِغَيْرِ عِمَامَةٍ قَالَ نَعَمْ وَ الْعِمَامَةُ أَحَبُّ إِلَيَّ.
- **Isnad as currently extracted:**
  > وَ رَوَى الْحَلَبِيُّ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ- فِي صَلَاةِ الْعِيدَيْنِ إِذَا كَانَ الْقَوْمُ خَمْسَةً أَوْ سَبْعَةً فَإِنَّهُمْ يُجَمِّعُونَ الصَّلَاةَ[4] كَمَا يَصْنَعُونَ يَوْمَ الْجُمُعَةِ وَ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحلبی | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 11 · `faqih-1486` — CLARIFIED
- Transmitters (student → teacher): الحلبي → ابي عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى الْحَلَبِيُّ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ»
- Isnad ends / matn begins at: "فِي صَلَاةِ الْعِيدَيْنِ إِذَا كَانَ الْقَوْمُ خَمْسَةً أَوْ سَبْعَةً"
- Mursal opening: al-Ṣadūq → الحلبي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 12 · `faqih-1487`
- **Location:** vol. 1, p. 523 · seq 1489 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى أَبُو الصَّبَّاحِ الْكِنَانِيُ‌[1] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ- سَأَلْتُهُ عَنِ التَّكْبِيرِ فِي الْعِيدَيْنِ فَقَالَ اثْنَتَا عَشْرَةَ سَبْعٌ فِي الْأُولَى وَ خَمْسٌ فِي الْأُخْرَى فَإِذَا قُمْتَ إِلَى الصَّلَاةِ فَكَبِّرْ وَاحِدَةً ثُمَّ تَقُولُ أَشْهَدُ أَنْ لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ وَ أَشْهَدُ أَنَّ مُحَمَّداً عَبْدُهُ وَ رَسُولُهُ اللَّهُمَّ أَنْتَ أَهْلُ الْكِبْرِيَاءِ وَ الْعَظَمَةِ وَ أَهْلُ الْجُودِ وَ الْجَبَرُوتِ وَ الْقُدْرَةِ وَ السُّلْطَانِ وَ الْعِزَّةِ أَسْأَلُكَ فِي هَذَا الْيَوْمِ الَّذِي جَعَلْتَهُ لِلْمُسْلِمِينَ عِيداً وَ لِمُحَمَّدٍ صَلَوَاتُكَ عَلَيْهِ وَ آلِهِ ذُخْراً وَ مَزِيداً أَنْ تُصَلِّيَ عَلَى مُحَمَّدٍ وَ آلِ مُحَمَّدٍ وَ أَنْ تُصَلِّيَ عَلَى مَلَائِكَتِكَ الْمُقَرَّبِينَ وَ أَنْبِيَائِكَ الْمُرْسَلِينَ وَ أَنْ تَغْفِرَ لَنَا وَ لِجَمِيعِ الْمُؤْمِنِينَ وَ الْمُؤْمِنَاتِ وَ الْمُسْلِمِينَ وَ الْمُسْلِمَاتِ الْأَحْيَاءِ مِنْهُمْ وَ الْأَمْوَاتِ اللَّهُمَّ إِنِّي أَسْأَلُكَ مِنْ خَيْرِ مَا سَأَلَكَ بِهِ عِبَادُكَ الْمُرْسَلُونَ وَ أَعُوذُ بِكَ مِنْ شَرِّ مَا عَاذَ مِنْهُ عِبَادُكَ الْمُخْلَصُونَ اللَّهُ أَكْبَرُ أَوَّلُ كُلِّ شَيْ‌ءٍ وَ آخِرُهُ وَ بَدِيعُ كُلِّ شَيْ‌ءٍ وَ مُنْتَهَاهُ وَ عَالِمٌ بِكُلِّ شَيْ‌ءٍ وَ مَعَادُهُ وَ مَصِيرُ كُلِّ شَيْ‌ءٍ إِلَيْهِ وَ مَرَدُّهُ وَ مُدَبِّرُ الْأُمُورِ وَ بَاعِثُ‌ مَنْ فِي الْقُبُورِ قَابِلُ الْأَعْمَالِ مُبْدِئُ الْخَفِيَّاتِ مُعْلِنُ السَّرَائِرِ اللَّهُ أَكْبَرُ عَظِيمُ الْمَلَكُوتِ شَدِيدُ الْجَبَرُوتِ حَيٌّ لَا يَمُوتُ دَائِمٌ لَا يَزُولُ‌ إِذا قَضى‌ أَمْراً فَإِنَّما يَقُولُ لَهُ كُنْ فَيَكُونُ* اللَّهُ أَكْبَرُ خَشَعَتْ لَكَ الْأَصْوَاتُ وَ عَنَتْ لَكَ الْوُجُوهُ وَ حَارَتْ دُونَكَ الْأَبْصَارُ وَ كَلَّتِ الْأَلْسُنُ عَنْ عَظَمَتِكَ وَ النَّوَاصِي كُلُّهَا بِيَدِكَ وَ مَقَادِيرُ الْأُمُورِ كُلِّهَا إِلَيْكَ لَا يَقْضِي فِيهَا غَيْرُكَ وَ لَا يَتِمُّ مِنْهَا شَيْ‌ءٌ دُونَكَ اللَّهُ أَكْبَرُ أَحَاطَ بِكُلِّ شَيْ‌ءٍ حِفْظُكَ وَ قَهَرَ كُلَّ شَيْ‌ءٍ عِزُّكَ وَ نَفَذَ كُلَّ شَيْ‌ءٍ أَمْرُكَ وَ قَامَ كُلُّ شَيْ‌ءٍ بِكَ وَ تَوَاضَعَ كُلُّ شَيْ‌ءٍ لِعَظَمَ …[truncated]
- **Isnad as currently extracted:**
  > وَ رَوَى أَبُو الصَّبَّاحِ الْكِنَانِيُ‌[1] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ- سَأَلْتُهُ عَنِ التَّكْبِيرِ فِي الْعِيدَيْنِ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابو الصباح الکنانی | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 12 · `faqih-1487` — CLARIFIED
- Transmitters (student → teacher): ابو الصباح الكناني → ابي عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى أَبُو الصَّبَّاحِ الْكِنَانِيُ‌[1] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ التَّكْبِيرِ فِي الْعِيدَيْنِ فَقَالَ اثْنَتَا عَشْرَةَ سَبْعٌ"
- Mursal opening: al-Ṣadūq → ابو الصباح الكناني; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 13 · `faqih-1526`
- **Location:** vol. 1, p. 548 · seq 1528 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى زُرَارَةُ وَ مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالا قُلْنَا لَهُ أَ رَأَيْتَ هَذِهِ الرِّيَاحَ وَ الظُّلَمَ الَّتِي تَكُونُ هَلْ يُصَلَّى بِهَا قَالَ كُلُّ أَخَاوِيفِ السَّمَاءِ مِنْ ظُلْمَةٍ أَوْ رِيحٍ أَوْ فَزَعٍ فَصَلِّ لَهَا صَلَاةَ الْكُسُوفِ حَتَّى تَسْكُنَ‌[2].
- **Isnad as currently extracted:**
  > وَ رَوَى زُرَارَةُ وَ مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالا قُلْنَا لَهُ أَ رَأَيْتَ هَذِهِ الرِّيَاحَ وَ الظُّلَمَ الَّتِي تَكُونُ هَلْ يُصَلَّى بِهَا قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | زرارة | روی |  |
  | 1 | imam | ابی جعفر ع | عن |  |

### Chain 13 · `faqih-1526` — CLARIFIED
- Transmitters (student → teacher): زرارة → ابي جعفر ع
- Corrected isnad (Arabic): «وَ رَوَى زُرَارَةُ وَ مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالا»
- Isnad ends / matn begins at: "قُلْنَا لَهُ أَ رَأَيْتَ هَذِهِ الرِّيَاحَ وَ الظُّلَمَ الَّتِي"
- Mursal opening: al-Ṣadūq → زرارة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim.

---

### Chain 14 · `faqih-1526`
- **Location:** vol. 1, p. 548 · seq 1528 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى زُرَارَةُ وَ مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالا قُلْنَا لَهُ أَ رَأَيْتَ هَذِهِ الرِّيَاحَ وَ الظُّلَمَ الَّتِي تَكُونُ هَلْ يُصَلَّى بِهَا قَالَ كُلُّ أَخَاوِيفِ السَّمَاءِ مِنْ ظُلْمَةٍ أَوْ رِيحٍ أَوْ فَزَعٍ فَصَلِّ لَهَا صَلَاةَ الْكُسُوفِ حَتَّى تَسْكُنَ‌[2].
- **Isnad as currently extracted:**
  > وَ رَوَى زُرَارَةُ وَ مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالا قُلْنَا لَهُ أَ رَأَيْتَ هَذِهِ الرِّيَاحَ وَ الظُّلَمَ الَّتِي تَكُونُ هَلْ يُصَلَّى بِهَا قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن مسلم | روی |  |
  | 1 | imam | ابی جعفر ع | عن |  |

### Chain 14 · `faqih-1526` — CLARIFIED
- Transmitters (student → teacher): محمد بن مسلم → ابي جعفر ع
- Corrected isnad (Arabic): «وَ رَوَى زُرَارَةُ وَ مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالا»
- Isnad ends / matn begins at: "قُلْنَا لَهُ أَ رَأَيْتَ هَذِهِ الرِّيَاحَ وَ الظُّلَمَ الَّتِي"
- Mursal opening: al-Ṣadūq → محمد بن مسلم; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim.

---

### Chain 15 · `faqih-1539`
- **Location:** vol. 1, p. 554 · seq 1541 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > و روى أبو بصير عن أبي عبد الله ع قال‌ صل صلاة جعفر في أي وقت شئت من ليل أو نهار و إن شئت حسبتها من نوافل الليل و إن شئت حسبتها من نوافل النهار تحسبُ لَكَ مِنْ نَوَافِلِكَ وَ تُحْسَبُ لَكَ مِنْ صَلَاةِ جَعْفَرٍ ع.
- **Isnad as currently extracted:**
  > و روى أبو بصير عن أبي عبد الله ع قال‌ صل صلاة جعفر في أي وقت شئت من ليل أو نهار و
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابو بصیر | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 15 · `faqih-1539` — CLARIFIED
- Transmitters (student → teacher): ابو بصير → ابي عبد الله ع
- Corrected isnad (Arabic): «و روى أبو بصير عن أبي عبد الله ع قال‌»
- Isnad ends / matn begins at: "صل صلاة جعفر في أي وقت شئت من ليل"
- Mursal opening: al-Ṣadūq → ابو بصير; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 16 · `faqih-1548`
- **Location:** vol. 1, p. 559 · seq 1550 · chain 1
- **Flags:** `mursal_opening`, `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > رَوَى زِيَادٌ الْقَنْدِيُّ عَنْ عَبْدِ الرَّحِيمِ الْقَصِيرِ قَالَ: دَخَلْتُ عَلَى أَبِي‌
عَبْدِ اللَّهِ ع فَقُلْتُ جُعِلْتُ فِدَاكَ إِنِّي اخْتَرَعْتُ دُعَاءً فَقَالَ دَعْنِي مِنِ اخْتِرَاعِكَ‌[1] إِذَا نَزَلَ بِكَ أَمْرٌ فَافْزَعْ إِلَى رَسُولِ اللَّهِ ص فَصَلِّ رَكْعَتَيْنِ تُهْدِيهِمَا إِلَى رَسُولِ اللَّهِ ص قُلْتُ كَيْفَ أَصْنَعُ قَالَ تَغْتَسِلُ وَ تُصَلِّي رَكْعَتَيْنِ تَسْتَفْتِحُ بِهِمَا افْتِتَاحَ الْفَرِيضَةِ وَ تَتَشَهَّدُ تَشَهُّدَ الْفَرِيضَةِ[2] فَإِذَا فَرَغْتَ مِنَ التَّشَهُّدِ وَ سَلَّمْتَ قُلْتَ اللَّهُمَّ أَنْتَ السَّلَامُ‌[3] وَ مِنْكَ السَّلَامُ وَ إِلَيْكَ يَرْجِعُ السَّلَامُ اللَّهُمَّ صَلِّ عَلَى مُحَمَّدٍ وَ آلِ مُحَمَّدٍ- وَ بَلِّغْ رُوحَ مُحَمَّدٍ وَ آلِ مُحَمَّدٍ عَنِّي السَّلَامَ وَ السَّلَامُ عَلَيْهِمْ وَ رَحْمَةُ اللَّهِ وَ بَرَكَاتُهُ اللَّهُمَّ إِنَّ هَاتَيْنِ الرَّكْعَتَيْنِ هَدِيَّةٌ مِنِّي إِلَى رَسُولِكَ ص فَأَثِبْنِي عَلَيْهِمَا[4] مَا أَمَّلْتُ وَ رَجَوْتُ مِنْكَ وَ فِي رَسُولِكَ‌[5] يَا وَلِيَّ الْمُؤْمِنِينَ- ثُمَّ تَخِرُّ سَاجِداً وَ تَقُولُ- يَا حَيُّ يَا قَيُّومُ يَا حَيّاً لَا يَمُوتُ يَا حَيُّ لَا إِلَهَ إِلَّا أَنْتَ يَا ذَا الْجَلَالِ وَ الْإِكْرَامِ يَا أَرْحَمَ الرَّاحِمِينَ أَرْبَعِينَ مَرَّةً ثُمَّ تَضَعُ خَدَّكَ الْأَيْمَنَ عَلَى الْأَرْضِ فَتَقُولُهَا أَرْبَعِينَ مَرَّةً ثُمَّ تَضَعُ خَدَّكَ الْأَيْسَرَ فَتَقُولُ ذَلِكَ أَرْبَعِينَ مَرَّةً ثُمَّ تَرْفَعُ رَأْسَكَ وَ تَمُدُّ يَدَيْكَ وَ تَقُولُ ذَلِكَ أَرْبَعِينَ مَرَّةً ثُمَّ تَرُدُّ يَدَكَ إِلَى رَقَبَتِكَ وَ تَلُوذُ
بِسَبَّابَتِكَ‌[1] أَرْبَعِينَ مَرَّةً ثُمَّ خُذْ لِحْيَتَكَ بِيَدِكَ الْيُسْرَى فَابْكِ أَوْ تَبَاكَ وَ قُلْ يَا مُحَمَّدُ يَا رَسُولَ اللَّهِ أَشْكُو إِلَى اللَّهِ وَ إِلَيْكَ حَاجَتِي وَ أَشْكُو إِلَى أَهْلِ بَيْتِكَ الرَّاشِدِينَ حَاجَتِي وَ بِكُمْ أَتَوَجَّهُ إِلَى اللَّهِ فِي حَاجَتِي ثُمَّ تَسْجُدُ وَ تَقُولُ يَا اللَّهُ يَا اللَّهُ حَتَّى يَنْقَطِعَ نَفَسُكَ صَلِّ عَلَى مُحَمَّدٍ وَ آلِ مُحَمَّدٍ وَ افْعَلْ بِي كَذَا وَ كَذَا قَالَ أَبُو عَبْدِ اللَّهِ ع أَنَا الضَّامِنُ عَلَى اللَّهِ عَزَّ وَ جَلَّ أَنْ لَا يَبْرَحَ حَتَّى تُقْضَى حَاجَت …[truncated]
- **Isnad as currently extracted:**
  > رَوَى زِيَادٌ اَلْقَنْدِيُّ عَنْ عَبْدِ اَلرَّحِيمِ اَلْقَصِيرِ قَالَ: دَخَلْتُ عَلَى أَبِي عَبْدِ اَللَّهِ عَلَيْهِ اَلسَّلاَمُ فَقُلْتُ جُعِلْتُ فِدَاكَ إِنِّي اِخْتَرَعْتُ دُعَاءً فَقَالَ «دَعْنِي مِنِ اِخْتِرَاعِكَ إِذَا نَزَلَ بِكَ أَمْرٌ فَافْزَعْ إِلَى رَسُولِ اَللَّهِ صَلَّى اَللَّهُ عَلَيْهِ وَ آلِهِ فَصَلِّ رَكْعَتَيْنِ تُهْدِيهِمَا إِلَى رَسُولِ اَللَّهِ صَلَّى اَللَّهُ عَلَيْهِ وَ آلِهِ » قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | زیاد القندی | روی |  |
  | 1 | named_narrator | عبد الرحیم القصیر قال: دخلت علی ابی عبد الله علیه السلام فقلت جعلت فداک انی اخترعت دعاء فقال دعنی من اختراعک اذا نزل بک امر فافزع الی رسول الله صلی الله علیه و اله فصل رکعتین تهدیهما الی رسول الله صلی الله علیه و اله قلت | عن |  |

### Chain 16 · `faqih-1548` — CLARIFIED
- Transmitters (student → teacher): زياد القندي → عبد الرحيم القصير → أبو عبد الله ع (مذكور في صدر المتن بصيغة «دخلت على»)
- Corrected isnad (Arabic): «رَوَى زِيَادٌ الْقَنْدِيُّ عَنْ عَبْدِ الرَّحِيمِ الْقَصِيرِ قَالَ»
- Isnad ends / matn begins at: "دَخَلْتُ عَلَى أَبِي‌ عَبْدِ اللَّهِ ع فَقُلْتُ جُعِلْتُ فِدَاكَ"
- Mursal opening: al-Ṣadūq → زياد القندي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name.

---

### Chain 17 · `faqih-1581`
- **Location:** vol. 2, p. 8 · seq 1583 · chain 1
- **Flags:** `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > وَ كَتَبَ الرِّضَا عَلِيُّ بْنُ مُوسَى ع إِلَى مُحَمَّدِ بْنِ سِنَانٍ فِيمَا كَتَبَ إِلَيْهِ مِنْ جَوَابِ مَسَائِلِهِ‌ أَنَّ عِلَّةَ الزَّكَاةِ مِنْ أَجْلِ قُوتِ الْفُقَرَاءِ وَ تَحْصِينِ أَمْوَالِ الْأَغْنِيَاءِ لِأَنَّ اللَّهَ عَزَّ وَ جَلَّ كَلَّفَ أَهْلَ الصِّحَّةِ الْقِيَامَ بِشَأْنِ أَهْلِ الزَّمَانَةِ وَ الْبَلْوَى‌[2] كَمَا قَالَ اللَّهُ تَبَارَكَ وَ تَعَالَى- لَتُبْلَوُنَ‌ فِي أَمْوالِكُمْ‌ وَ أَنْفُسِكُمْ‌ فِي أَمْوَالِكُمْ إِخْرَاجُ الزَّكَاةِ وَ فِي أَنْفُسِكُمْ تَوْطِينُ الْأَنْفُسِ عَلَى الصَّبْرِ مَعَ مَا فِي ذَلِكَ مِنْ أَدَاءِ شُكْرِ نِعَمِ اللَّهِ عَزَّ وَ جَلَّ وَ الطَّمَعِ فِي الزِّيَادَةِ مَعَ مَا فِيهِ مِنَ الزِّيَادَةِ وَ الرَّأْفَةِ وَ الرَّحْمَةِ لِأَهْلِ الضَّعْفِ‌[3] وَ الْعَطْفِ عَلَى أَهْلِ الْمَسْكَنَةِ وَ الْحَثِّ لَهُمْ عَلَى الْمُوَاسَاةِ وَ تَقْوِيَةِ الْفُقَرَاءِ وَ الْمَعُونَةِ لَهُمْ عَلَى أَمْرِ الدِّينِ وَ هُوَ عِظَةٌ لِأَهْلِ الْغِنَى وَ عِبْرَةٌ لَهُمْ لِيَسْتَدِلُّوا عَلَى فُقَرَاءِ الْآخِرَةِ بِهِمْ‌[4] وَ مَا لَهُمْ مِنَ الْحَثِّ فِي ذَلِكَ عَلَى الشُّكْرِ لِلَّهِ تَبَارَكَ وَ تَعَالَى لِمَا خَوَّلَهُمْ‌[5] وَ أَعْطَاهُمْ وَ الدُّعَاءِ وَ التَّضَرُّعِ وَ الْخَوْفِ مِنْ أَنْ يَصِيرُوا مِثْلَهُمْ فِي أُمُورٍ كَثِيرَةٍ[6] فِي أَدَاءِ الزَّكَاةِ
- **Isnad as currently extracted:**
  > وَ كَتَبَ الرِّضَا عَلِيُّ بْنُ مُوسَى ع إِلَى مُحَمَّدِ بْنِ سِنَانٍ فِيمَا كَتَبَ إِلَيْهِ مِنْ جَوَابِ مَسَائِلِهِ‌ أَنَّ عِلَّةَ الزَّكَاةِ مِنْ أَجْلِ قُوتِ الْفُقَرَاءِ وَ تَحْصِينِ أَمْوَالِ الْأَغْنِيَاءِ لِأَنَّ اللَّهَ عَزَّ وَ جَلَّ كَلَّفَ أَهْلَ الصِّحَّةِ الْقِيَامَ بِشَأْنِ أَهْلِ الزَّمَانَةِ وَ الْبَلْوَى‌[2] كَمَا قَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | کتب الرضا علی بن موسی ع الی محمد بن سنان فیما کتب الیه من جواب مسائله ان علة الزکاة من اجل قوت الفقراء و تحصین اموال الاغنیاء لان الله عز و جل کلف اهل الصحة القیام بشان اهل الزمانة و البلوی کما |  |  |

### Chain 17 · `faqih-1581` — CLARIFIED
- Transmitters (student → teacher): محمد بن سنان → الإمام الرضا علي بن موسى ع (مكاتبة واردة من الإمام)
- Corrected isnad (Arabic): «وَ كَتَبَ الرِّضَا عَلِيُّ بْنُ مُوسَى ع إِلَى مُحَمَّدِ بْنِ سِنَانٍ فِيمَا كَتَبَ إِلَيْهِ مِنْ جَوَابِ مَسَائِلِهِ‌»
- Isnad ends / matn begins at: "أَنَّ عِلَّةَ الزَّكَاةِ مِنْ أَجْلِ قُوتِ الْفُقَرَاءِ وَ تَحْصِينِ"
- Mursal opening: al-Ṣadūq → محمد بن سنان; full path via Mashyakha = known in two routes: (1) محمد بن علي ماجيلويه → محمد بن أبي القاسم → محمد بن علي الكوفي → محمد بن سنان; (2) والد الصدوق → علي بن إبراهيم → إبراهيم بن هاشم → محمد بن سنان
- Verdict: needs_mashyakha_expansion
- Notes: The transmission is an epistolary answer from Imam al-Riḍā to Muḥammad b. Sinān. It is not ambiguous merely because its grammar runs from the author of the letter to its recipient rather than through repeated «عن». Mashyakha source: [Man lā yaḥḍuruhu al-Faqīh, vol. 4, p. 523](https://lib.eshia.ir/11021/4/523).
---

### Chain 18 · `faqih-1827`
- **Location:** vol. 2, p. 94 · seq 1831 · chain 1
- **Flags:** `suspicious_token`
- **Full report (Arabic):**
  > وَ كُنَّ نِسَاءُ النَّبِيِ‌[2] ص إِذَا كَانَ عَلَيْهِنَّ صِيَامٌ أَخَّرْنَ ذَلِكَ إِلَى شَعْبَانَ كَرَاهِيَةَ أَنْ يَمْنَعْنَ رَسُولَ اللَّهِ ص حَاجَتَهُ وَ إِذَا كَانَ شَعْبَانُ صُمْنَ وَ صَامَ مَعَهُنَّ وَ كَانَ ع يَقُولُ شَعْبَانُ شَهْرِي.
- **Isnad as currently extracted:**
  > وَ كُنَّ نِسَاءُ النَّبِيِ‌[2] ص إِذَا كَانَ عَلَيْهِنَّ صِيَامٌ أَخَّرْنَ ذَلِكَ إِلَى شَعْبَانَ كَرَاهِيَةَ أَنْ يَمْنَعْنَ رَسُولَ اللَّهِ ص حَاجَتَهُ وَ إِذَا كَانَ شَعْبَانُ صُمْنَ وَ صَامَ مَعَهُنَّ وَ كَانَ ع يَقُولُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | imam | کن نساء النبی ص اذا کان علیهن صیام اخرن ذلک الی شعبان کراهیة ان یمنعن رسول الله ص حاجته و اذا کان شعبان صمن و صام معهن و کان ع |  |  |

### Chain 18 · `faqih-1827` — CLARIFIED
- Transmitters (student → teacher): لا توجد سلسلة رواة مذكورة؛ النص تقرير مباشر عن نساء النبي ص
- Corrected isnad (Arabic): «—»
- Isnad ends / matn begins at: "وَ كُنَّ نِسَاءُ النَّبِيِ‌[2] ص إِذَا كَانَ عَلَيْهِنَّ صِيَامٌ"
- Mursal opening: not applicable; no opening isnād is stated in the report
- Verdict: clean
- Notes: This item is not an isnād-bearing report in the supplied text; the tokenizer should treat the whole sentence as matn. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name.

---

### Chain 19 · `faqih-1954`
- **Location:** vol. 2, p. 134 · seq 1958 · chain 1
- **Flags:** `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > وَ كَانَ عَلِيُّ بْنُ الْحُسَيْنِ ع‌ إِذَا كَانَ الْيَوْمُ الَّذِي يَصُومُ فِيهِ أَمَرَ بِشَاةٍ
فَتُذْبَحُ وَ تُقْطَعُ أَعْضَاؤُهُ وَ تُطْبَخُ فَإِذَا كَانَ عِنْدَ الْمَسَاءِ أَكَبَّ عَلَى الْقُدُورِ حَتَّى يَجِدَ رِيحَ الْمَرَقِ وَ هُوَ صَائِمٌ ثُمَّ يَقُولُ هَاتُوا الْقِصَاعَ‌[1] اغْرِفُوا لآِلِ فُلَانٍ اغْرِفُوا لآِلِ فُلَانٍ ثُمَّ يُؤْتَى بِخُبْزٍ وَ تَمْرٍ فَيَكُونُ ذَلِكَ عَشَاءَهُ‌[2].
- **Isnad as currently extracted:**
  > وَ كَانَ عَلِيُّ بْنُ الْحُسَيْنِ ع‌ إِذَا كَانَ الْيَوْمُ الَّذِي يَصُومُ فِيهِ أَمَرَ بِشَاةٍ فَتُذْبَحُ وَ تُقْطَعُ أَعْضَاؤُهُ وَ تُطْبَخُ فَإِذَا كَانَ عِنْدَ الْمَسَاءِ أَكَبَّ عَلَى الْقُدُورِ حَتَّى يَجِدَ رِيحَ الْمَرَقِ وَ هُوَ صَائِمٌ ثُمَّ يَقُولُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | کان علی بن الحسین ع اذا کان الیوم الذی یصوم فیه امر بشاة فتذبح و تقطع اعضاؤه و تطبخ فاذا کان عند المساء اکب علی القدور حتی یجد ریح المرق و هو صائم |  |  |

### Chain 19 · `faqih-1954` — CLARIFIED
- Transmitters (student → teacher): لا توجد سلسلة رواة مذكورة؛ النص حكاية مباشرة عن علي بن الحسين ع
- Corrected isnad (Arabic): «—»
- Isnad ends / matn begins at: "وَ كَانَ عَلِيُّ بْنُ الْحُسَيْنِ ع‌ إِذَا كَانَ الْيَوْمُ"
- Mursal opening: not applicable; no opening isnād is stated in the report
- Verdict: clean
- Notes: This item is not an isnād-bearing report in the supplied text; the tokenizer should treat the whole sentence as matn. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name.

---

### Chain 20 · `faqih-1963`
- **Location:** vol. 2, p. 137 · seq 1967 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > سَأَلَ زُرَارَةُ وَ مُحَمَّدُ بْنُ مُسْلِمٍ وَ الْفُضَيْلُ أَبَا جَعْفَرٍ الْبَاقِرَ وَ أَبَا عَبْدِ اللَّهِ الصَّادِقَ ع‌ عَنِ الصَّلَاةِ فِي شَهْرِ رَمَضَانَ نَافِلَةً بِاللَّيْلِ جَمَاعَةً فَقَالا[1] إِنَّ النَّبِيَّ ص كَانَ إِذَا صَلَّى الْعِشَاءَ الْآخِرَةَ انْصَرَفَ إِلَى مَنْزِلِهِ ثُمَّ يَخْرُجُ مِنْ آخِرِ اللَّيْلِ إِلَى الْمَسْجِدِ فَيَقُومُ فَيُصَلِّي فَخَرَجَ فِي أَوَّلِ لَيْلَةٍ مِنْ شَهْرِ رَمَضَانَ لِيُصَلِّيَ كَمَا كَانَ يُصَلِّي فَاصْطَفَّ النَّاسُ خَلْفَهُ فَهَرَبَ مِنْهُمْ إِلَى بَيْتِهِ وَ تَرَكَهُمْ فَفَعَلُوا ذَلِكَ ثَلَاثَ لَيَالٍ فَقَامَ ص فِي الْيَوْمِ الثَّالِثِ‌[2] عَلَى مِنْبَرِهِ فَحَمِدَ اللَّهَ وَ أَثْنَى عَلَيْهِ ثُمَّ قَالَ أَيُّهَا النَّاسُ إِنَّ الصَّلَاةَ بِاللَّيْلِ فِي شَهْرِ رَمَضَانَ مِنَ النَّافِلَةِ فِي جَمَاعَةٍ بِدْعَةٌ وَ صَلَاةَ الضُّحَى بِدْعَةٌ أَلَا فَلَا تَجْتَمِعُوا لَيْلًا فِي شَهْرِ رَمَضَانَ لِصَلَاةِ اللَّيْلِ وَ لَا تُصَلُّوا صَلَاةَ الضُّحَى فَإِنَّ تِلْكَ مَعْصِيَةٌ أَلَا فَإِنَّ كُلَّ بِدْعَةٍ ضَلَالَةٌ وَ كُلَّ ضَلَالَةٍ سَبِيلُهَا إِلَى النَّارِ ثُمَّ نَزَلَ ص وَ هُوَ يَقُولُ قَلِيلٌ فِي سُنَّةٍ خَيْرٌ مِنْ كَثِيرٍ فِي بِدْعَةٍ.
- **Isnad as currently extracted:**
  > سَأَلَ زُرَارَةُ وَ مُحَمَّدُ بْنُ مُسْلِمٍ وَ الْفُضَيْلُ أَبَا جَعْفَرٍ الْبَاقِرَ وَ أَبَا عَبْدِ اللَّهِ الصَّادِقَ ع‌ عَنِ الصَّلَاةِ فِي شَهْرِ رَمَضَانَ نَافِلَةً بِاللَّيْلِ جَمَاعَةً فَقَالا[1] إِنَّ النَّبِيَّ ص كَانَ إِذَا صَلَّى الْعِشَاءَ الْآخِرَةَ انْصَرَفَ إِلَى مَنْزِلِهِ ثُمَّ يَخْرُجُ مِنْ آخِرِ اللَّيْلِ إِلَى الْمَسْجِدِ فَيَقُومُ فَيُصَلِّي فَخَرَجَ فِي أَوَّلِ لَيْلَةٍ مِنْ شَهْرِ رَمَضَانَ لِيُصَلِّيَ كَمَا كَانَ يُصَلِّي فَاصْطَفَّ النَّاسُ خَلْفَهُ فَهَرَبَ مِنْهُمْ إِلَى بَيْتِهِ وَ تَرَكَهُمْ فَفَعَلُوا ذَلِكَ ثَلَاثَ لَيَالٍ فَقَامَ ص فِي الْيَوْمِ الثَّالِثِ‌[2] عَلَى مِنْبَرِهِ فَحَمِدَ اللَّهَ وَ أَثْنَى عَلَيْهِ ثُمَّ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | سال زرارة |  |  |
  | 1 | named_narrator | الصلاة فی شهر رمضان نافلة باللیل جماعة فقالا ان النبی ص کان اذا صلی العشاء الاخرة انصرف الی منزله ثم یخرج من اخر اللیل الی المسجد فیقوم فیصلی فخرج فی اول لیلة من شهر رمضان لیصلی کما کان یصلی فاصطف الناس خلفه فهرب منهم الی بیته و ترکهم ففعلوا ذلک ثلاث لیال فقام ص فی الیوم الثالث علی منبره فحمد الله و اثنی علیه | عن |  |

### Chain 20 · `faqih-1963` — CLARIFIED
- Transmitters (student → teacher): زرارة → أبو جعفر الباقر ع وأبو عبد الله الصادق ع (جواب مشترك)
- Corrected isnad (Arabic): «سَأَلَ زُرَارَةُ وَ مُحَمَّدُ بْنُ مُسْلِمٍ وَ الْفُضَيْلُ أَبَا جَعْفَرٍ الْبَاقِرَ وَ أَبَا عَبْدِ اللَّهِ الصَّادِقَ ع‌»
- Isnad ends / matn begins at: "عَنِ الصَّلَاةِ فِي شَهْرِ رَمَضَانَ نَافِلَةً بِاللَّيْلِ جَمَاعَةً فَقَالا[1]"
- Mursal opening: al-Ṣadūq → زرارة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim. The source attributes the joint answer to both Imams; each generated chain corresponds to one of the three questioners.

---

### Chain 21 · `faqih-1963`
- **Location:** vol. 2, p. 137 · seq 1967 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > سَأَلَ زُرَارَةُ وَ مُحَمَّدُ بْنُ مُسْلِمٍ وَ الْفُضَيْلُ أَبَا جَعْفَرٍ الْبَاقِرَ وَ أَبَا عَبْدِ اللَّهِ الصَّادِقَ ع‌ عَنِ الصَّلَاةِ فِي شَهْرِ رَمَضَانَ نَافِلَةً بِاللَّيْلِ جَمَاعَةً فَقَالا[1] إِنَّ النَّبِيَّ ص كَانَ إِذَا صَلَّى الْعِشَاءَ الْآخِرَةَ انْصَرَفَ إِلَى مَنْزِلِهِ ثُمَّ يَخْرُجُ مِنْ آخِرِ اللَّيْلِ إِلَى الْمَسْجِدِ فَيَقُومُ فَيُصَلِّي فَخَرَجَ فِي أَوَّلِ لَيْلَةٍ مِنْ شَهْرِ رَمَضَانَ لِيُصَلِّيَ كَمَا كَانَ يُصَلِّي فَاصْطَفَّ النَّاسُ خَلْفَهُ فَهَرَبَ مِنْهُمْ إِلَى بَيْتِهِ وَ تَرَكَهُمْ فَفَعَلُوا ذَلِكَ ثَلَاثَ لَيَالٍ فَقَامَ ص فِي الْيَوْمِ الثَّالِثِ‌[2] عَلَى مِنْبَرِهِ فَحَمِدَ اللَّهَ وَ أَثْنَى عَلَيْهِ ثُمَّ قَالَ أَيُّهَا النَّاسُ إِنَّ الصَّلَاةَ بِاللَّيْلِ فِي شَهْرِ رَمَضَانَ مِنَ النَّافِلَةِ فِي جَمَاعَةٍ بِدْعَةٌ وَ صَلَاةَ الضُّحَى بِدْعَةٌ أَلَا فَلَا تَجْتَمِعُوا لَيْلًا فِي شَهْرِ رَمَضَانَ لِصَلَاةِ اللَّيْلِ وَ لَا تُصَلُّوا صَلَاةَ الضُّحَى فَإِنَّ تِلْكَ مَعْصِيَةٌ أَلَا فَإِنَّ كُلَّ بِدْعَةٍ ضَلَالَةٌ وَ كُلَّ ضَلَالَةٍ سَبِيلُهَا إِلَى النَّارِ ثُمَّ نَزَلَ ص وَ هُوَ يَقُولُ قَلِيلٌ فِي سُنَّةٍ خَيْرٌ مِنْ كَثِيرٍ فِي بِدْعَةٍ.
- **Isnad as currently extracted:**
  > سَأَلَ زُرَارَةُ وَ مُحَمَّدُ بْنُ مُسْلِمٍ وَ الْفُضَيْلُ أَبَا جَعْفَرٍ الْبَاقِرَ وَ أَبَا عَبْدِ اللَّهِ الصَّادِقَ ع‌ عَنِ الصَّلَاةِ فِي شَهْرِ رَمَضَانَ نَافِلَةً بِاللَّيْلِ جَمَاعَةً فَقَالا[1] إِنَّ النَّبِيَّ ص كَانَ إِذَا صَلَّى الْعِشَاءَ الْآخِرَةَ انْصَرَفَ إِلَى مَنْزِلِهِ ثُمَّ يَخْرُجُ مِنْ آخِرِ اللَّيْلِ إِلَى الْمَسْجِدِ فَيَقُومُ فَيُصَلِّي فَخَرَجَ فِي أَوَّلِ لَيْلَةٍ مِنْ شَهْرِ رَمَضَانَ لِيُصَلِّيَ كَمَا كَانَ يُصَلِّي فَاصْطَفَّ النَّاسُ خَلْفَهُ فَهَرَبَ مِنْهُمْ إِلَى بَيْتِهِ وَ تَرَكَهُمْ فَفَعَلُوا ذَلِكَ ثَلَاثَ لَيَالٍ فَقَامَ ص فِي الْيَوْمِ الثَّالِثِ‌[2] عَلَى مِنْبَرِهِ فَحَمِدَ اللَّهَ وَ أَثْنَى عَلَيْهِ ثُمَّ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن مسلم |  |  |
  | 1 | named_narrator | الصلاة فی شهر رمضان نافلة باللیل جماعة فقالا ان النبی ص کان اذا صلی العشاء الاخرة انصرف الی منزله ثم یخرج من اخر اللیل الی المسجد فیقوم فیصلی فخرج فی اول لیلة من شهر رمضان لیصلی کما کان یصلی فاصطف الناس خلفه فهرب منهم الی بیته و ترکهم ففعلوا ذلک ثلاث لیال فقام ص فی الیوم الثالث علی منبره فحمد الله و اثنی علیه | عن |  |

### Chain 21 · `faqih-1963` — CLARIFIED
- Transmitters (student → teacher): محمد بن مسلم → أبو جعفر الباقر ع وأبو عبد الله الصادق ع (جواب مشترك)
- Corrected isnad (Arabic): «سَأَلَ زُرَارَةُ وَ مُحَمَّدُ بْنُ مُسْلِمٍ وَ الْفُضَيْلُ أَبَا جَعْفَرٍ الْبَاقِرَ وَ أَبَا عَبْدِ اللَّهِ الصَّادِقَ ع‌»
- Isnad ends / matn begins at: "عَنِ الصَّلَاةِ فِي شَهْرِ رَمَضَانَ نَافِلَةً بِاللَّيْلِ جَمَاعَةً فَقَالا[1]"
- Mursal opening: al-Ṣadūq → محمد بن مسلم; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim. The source attributes the joint answer to both Imams; each generated chain corresponds to one of the three questioners.

---

### Chain 22 · `faqih-1963`
- **Location:** vol. 2, p. 137 · seq 1967 · chain 3
- **Flags:** `co_narrator_expanded`, `expanded`, `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > سَأَلَ زُرَارَةُ وَ مُحَمَّدُ بْنُ مُسْلِمٍ وَ الْفُضَيْلُ أَبَا جَعْفَرٍ الْبَاقِرَ وَ أَبَا عَبْدِ اللَّهِ الصَّادِقَ ع‌ عَنِ الصَّلَاةِ فِي شَهْرِ رَمَضَانَ نَافِلَةً بِاللَّيْلِ جَمَاعَةً فَقَالا[1] إِنَّ النَّبِيَّ ص كَانَ إِذَا صَلَّى الْعِشَاءَ الْآخِرَةَ انْصَرَفَ إِلَى مَنْزِلِهِ ثُمَّ يَخْرُجُ مِنْ آخِرِ اللَّيْلِ إِلَى الْمَسْجِدِ فَيَقُومُ فَيُصَلِّي فَخَرَجَ فِي أَوَّلِ لَيْلَةٍ مِنْ شَهْرِ رَمَضَانَ لِيُصَلِّيَ كَمَا كَانَ يُصَلِّي فَاصْطَفَّ النَّاسُ خَلْفَهُ فَهَرَبَ مِنْهُمْ إِلَى بَيْتِهِ وَ تَرَكَهُمْ فَفَعَلُوا ذَلِكَ ثَلَاثَ لَيَالٍ فَقَامَ ص فِي الْيَوْمِ الثَّالِثِ‌[2] عَلَى مِنْبَرِهِ فَحَمِدَ اللَّهَ وَ أَثْنَى عَلَيْهِ ثُمَّ قَالَ أَيُّهَا النَّاسُ إِنَّ الصَّلَاةَ بِاللَّيْلِ فِي شَهْرِ رَمَضَانَ مِنَ النَّافِلَةِ فِي جَمَاعَةٍ بِدْعَةٌ وَ صَلَاةَ الضُّحَى بِدْعَةٌ أَلَا فَلَا تَجْتَمِعُوا لَيْلًا فِي شَهْرِ رَمَضَانَ لِصَلَاةِ اللَّيْلِ وَ لَا تُصَلُّوا صَلَاةَ الضُّحَى فَإِنَّ تِلْكَ مَعْصِيَةٌ أَلَا فَإِنَّ كُلَّ بِدْعَةٍ ضَلَالَةٌ وَ كُلَّ ضَلَالَةٍ سَبِيلُهَا إِلَى النَّارِ ثُمَّ نَزَلَ ص وَ هُوَ يَقُولُ قَلِيلٌ فِي سُنَّةٍ خَيْرٌ مِنْ كَثِيرٍ فِي بِدْعَةٍ.
- **Isnad as currently extracted:**
  > سَأَلَ زُرَارَةُ وَ مُحَمَّدُ بْنُ مُسْلِمٍ وَ الْفُضَيْلُ أَبَا جَعْفَرٍ الْبَاقِرَ وَ أَبَا عَبْدِ اللَّهِ الصَّادِقَ ع‌ عَنِ الصَّلَاةِ فِي شَهْرِ رَمَضَانَ نَافِلَةً بِاللَّيْلِ جَمَاعَةً فَقَالا[1] إِنَّ النَّبِيَّ ص كَانَ إِذَا صَلَّى الْعِشَاءَ الْآخِرَةَ انْصَرَفَ إِلَى مَنْزِلِهِ ثُمَّ يَخْرُجُ مِنْ آخِرِ اللَّيْلِ إِلَى الْمَسْجِدِ فَيَقُومُ فَيُصَلِّي فَخَرَجَ فِي أَوَّلِ لَيْلَةٍ مِنْ شَهْرِ رَمَضَانَ لِيُصَلِّيَ كَمَا كَانَ يُصَلِّي فَاصْطَفَّ النَّاسُ خَلْفَهُ فَهَرَبَ مِنْهُمْ إِلَى بَيْتِهِ وَ تَرَكَهُمْ فَفَعَلُوا ذَلِكَ ثَلَاثَ لَيَالٍ فَقَامَ ص فِي الْيَوْمِ الثَّالِثِ‌[2] عَلَى مِنْبَرِهِ فَحَمِدَ اللَّهَ وَ أَثْنَى عَلَيْهِ ثُمَّ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الفضیل ابا جعفر الباقر |  |  |
  | 1 | named_narrator | الصلاة فی شهر رمضان نافلة باللیل جماعة فقالا ان النبی ص کان اذا صلی العشاء الاخرة انصرف الی منزله ثم یخرج من اخر اللیل الی المسجد فیقوم فیصلی فخرج فی اول لیلة من شهر رمضان لیصلی کما کان یصلی فاصطف الناس خلفه فهرب منهم الی بیته و ترکهم ففعلوا ذلک ثلاث لیال فقام ص فی الیوم الثالث علی منبره فحمد الله و اثنی علیه | عن |  |

### Chain 22 · `faqih-1963` — CLARIFIED
- Transmitters (student → teacher): الفضيل → أبو جعفر الباقر ع وأبو عبد الله الصادق ع (جواب مشترك)
- Corrected isnad (Arabic): «سَأَلَ زُرَارَةُ وَ مُحَمَّدُ بْنُ مُسْلِمٍ وَ الْفُضَيْلُ أَبَا جَعْفَرٍ الْبَاقِرَ وَ أَبَا عَبْدِ اللَّهِ الصَّادِقَ ع‌»
- Isnad ends / matn begins at: "عَنِ الصَّلَاةِ فِي شَهْرِ رَمَضَانَ نَافِلَةً بِاللَّيْلِ جَمَاعَةً فَقَالا[1]"
- Mursal opening: al-Ṣadūq → الفضيل; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim. The source attributes the joint answer to both Imams; each generated chain corresponds to one of the three questioners.

---

### Chain 23 · `faqih-2010`
- **Location:** vol. 2, p. 154 · seq 2014 · chain 1
- **Flags:** `mursal_opening`, `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > رَوَى أَحْمَدُ بْنُ مُحَمَّدِ بْنِ أَبِي نَصْرٍ الْبَزَنْطِيُّ عَنْ أَبِي الْحَسَنِ الرِّضَا ع‌ فِي رَجُلٍ نَذَرَ عَلَى نَفْسِهِ إِنْ هُوَ سَلِمَ مِنْ مَرَضٍ أَوْ تَخَلَّصَ مِنْ حَبْسٍ أَنْ يَصُومَ كُلَّ يَوْمِ أَرْبِعَاءَ وَ هُوَ الْيَوْمُ الَّذِي تَخَلَّصَ فِيهِ فَعَجَزَ عَنْ ذَلِكَ لِعِلَّةٍ أَصَابَتْهُ أَوْ غَيْرِ ذَلِكَ فَمَدَّ اللَّهُ عَزَّ وَ جَلَّ لِلرَّجُلِ فِي عُمُرِهِ وَ اجْتَمَعَ عَلَيْهِ صَوْمٌ كَثِيرٌ مَا كَفَّارَةُ ذَلِكَ قَالَ تَصَدَّقَ لِكُلِّ يَوْمٍ مُدّاً مِنْ حِنْطَةٍ أَوْ بِمُدِّ تَمْرٍ[2].
- **Isnad as currently extracted:**
  > رَوَى أَحْمَدُ بْنُ مُحَمَّدِ بْنِ أَبِي نَصْرٍ الْبَزَنْطِيُّ عَنْ أَبِي الْحَسَنِ الرِّضَا ع‌ فِي رَجُلٍ نَذَرَ عَلَى نَفْسِهِ إِنْ هُوَ سَلِمَ مِنْ مَرَضٍ أَوْ تَخَلَّصَ مِنْ حَبْسٍ أَنْ يَصُومَ كُلَّ يَوْمِ أَرْبِعَاءَ وَ هُوَ الْيَوْمُ الَّذِي تَخَلَّصَ فِيهِ فَعَجَزَ عَنْ ذَلِكَ لِعِلَّةٍ أَصَابَتْهُ أَوْ غَيْرِ ذَلِكَ فَمَدَّ اللَّهُ عَزَّ وَ جَلَّ لِلرَّجُلِ فِي عُمُرِهِ وَ اجْتَمَعَ عَلَيْهِ صَوْمٌ كَثِيرٌ مَا كَفَّارَةُ ذَلِكَ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | احمد بن محمد بن ابی نصر البزنطی | روی |  |
  | 1 | named_narrator | ابی الحسن الرضا ع فی رجل نذر علی نفسه ان هو سلم من مرض او تخلص من حبس ان یصوم کل یوم اربعاء و هو الیوم الذی تخلص فیه فعجز | عن |  |
  | 2 | named_narrator | ذلک لعلة اصابته او غیر ذلک فمد الله عز و جل للرجل فی عمره و اجتمع علیه صوم کثیر ما کفارة ذلک | عن |  |

### Chain 23 · `faqih-2010` — CLARIFIED
- Transmitters (student → teacher): أحمد بن محمد بن أبي نصر البزنطي → أبو الحسن الرضا ع
- Corrected isnad (Arabic): «رَوَى أَحْمَدُ بْنُ مُحَمَّدِ بْنِ أَبِي نَصْرٍ الْبَزَنْطِيُّ عَنْ أَبِي الْحَسَنِ الرِّضَا ع‌»
- Isnad ends / matn begins at: "فِي رَجُلٍ نَذَرَ عَلَى نَفْسِهِ إِنْ هُوَ سَلِمَ مِنْ"
- Mursal opening: al-Ṣadūq → أحمد بن محمد بن أبي نصر البزنطي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name.

---

### Chain 24 · `faqih-2230`
- **Location:** vol. 2, p. 221 · seq 2237 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ رَجُلًا اسْتَشَارَنِي فِي الْحَجِّ وَ كَانَ ضَعِيفَ الْحَالِ فَأَشَرْتُ عَلَيْهِ أَنْ لَا يَحُجَّ فَقَالَ مَا أَخْلَقَكَ أَنْ تَمْرَضَ سَنَةً فَقَالَ فَمَرِضْتُ سَنَةً.
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن اسحاق بن عمار | روی |  |

### Chain 24 · `faqih-2230` — CLARIFIED
- Transmitters (student → teacher): اسحاق بن عمار
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ رَجُلًا اسْتَشَارَنِي فِي"
- Mursal opening: al-Ṣadūq → اسحاق بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 25 · `faqih-2299`
- **Location:** vol. 2, p. 242 · seq 2306 · chain 1
- **Flags:** `matn_spill`
- **Full report (Arabic):**
  > وَ فِي رِوَايَةِ عِيسَى بْنِ عَبْدِ اللَّهِ الْهَاشِمِيِّ عَنْ أَبِيهِ عَنْ أَبِي عَبْدِ اللَّهِ عَنْ أَبِيهِ ع قَالَ‌ كَانَ مَوْضِعُ الْكَعْبَةِ رَبْوَةً مِنَ الْأَرْضِ بَيْضَاءَ[3] تُضِي‌ءُ كَضَوْءِ الشَّمْسِ‌
وَ الْقَمَرِ حَتَّى قَتَلَ ابْنَا آدَمَ أَحَدُهُمَا صَاحِبَهُ فَاسْوَدَّتْ فَلَمَّا نَزَلَ آدَمُ ع رَفَعَ اللَّهُ عَزَّ وَ جَلَّ لَهُ الْأَرْضَ كُلَّهَا حَتَّى رَآهَا ثُمَّ قَالَ هَذِهِ لَكَ كُلُّهَا قَالَ يَا رَبِّ مَا هَذِهِ الْأَرْضُ الْبَيْضَاءُ الْمُنِيرَةُ قَالَ هِيَ حَرَمِي فِي أَرْضِي وَ قَدْ جَعَلْتُ عَلَيْكَ أَنْ تَطُوفَ بِهَا كُلَّ يَوْمٍ سَبْعَمِائَةِ طَوَافٍ.
- **Isnad as currently extracted:**
  > وَ فِي رِوَايَةِ عِيسَى بْنِ عَبْدِ اللَّهِ الْهَاشِمِيِّ عَنْ أَبِيهِ عَنْ أَبِي عَبْدِ اللَّهِ عَنْ أَبِيهِ ع قَالَ‌ كَانَ مَوْضِعُ الْكَعْبَةِ رَبْوَةً مِنَ الْأَرْضِ بَيْضَاءَ[3] تُضِي‌ءُ كَضَوْءِ الشَّمْسِ‌ وَ الْقَمَرِ حَتَّى قَتَلَ ابْنَا آدَمَ أَحَدُهُمَا صَاحِبَهُ فَاسْوَدَّتْ فَلَمَّا نَزَلَ آدَمُ ع رَفَعَ اللَّهُ عَزَّ وَ جَلَّ لَهُ الْأَرْضَ كُلَّهَا حَتَّى رَآهَا ثُمَّ قَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | فی روایة عیسی بن عبد الله الهاشمی |  |  |
  | 1 | pronoun_relation | ابیه | عن | father |
  | 2 | named_narrator | ابی عبد الله | عن |  |
  | 3 | imam | ابیه ع | عن |  |

### Chain 25 · `faqih-2299` — CLARIFIED
- Transmitters (student → teacher): عيسي بن عبد الله الهاشمي → أبيه (غير مسمّى في النص) → ابي عبد الله → ابيه ع
- Corrected isnad (Arabic): «وَ فِي رِوَايَةِ عِيسَى بْنِ عَبْدِ اللَّهِ الْهَاشِمِيِّ عَنْ أَبِيهِ عَنْ أَبِي عَبْدِ اللَّهِ عَنْ أَبِيهِ ع قَالَ‌»
- Isnad ends / matn begins at: "كَانَ مَوْضِعُ الْكَعْبَةِ رَبْوَةً مِنَ الْأَرْضِ بَيْضَاءَ[3] تُضِي‌ءُ كَضَوْءِ"
- Mursal opening: al-Ṣadūq → عيسي بن عبد الله الهاشمي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 26 · `faqih-2316`
- **Location:** vol. 2, p. 247 · seq 2323 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ سَعِيدِ بْنِ عَبْدِ اللَّهِ الْأَعْرَجِ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌ إِنَّ قُرَيْشاً فِي الْجَاهِلِيَّةِ هَدَمُوا الْبَيْتَ فَلَمَّا أَرَادُوا بِنَاءَهُ حِيلَ بَيْنَهُ وَ بَيْنَهُمْ وَ أُلْقِيَ فِي رُوعِهِمُ الرُّعْبُ‌[2] حَتَّى قَالَ قَائِلٌ مِنْهُمْ لِيَأْتِ كُلُّ رَجُلٍ مِنْكُمْ بِأَطْيَبِ مَالِهِ وَ لَا تَأْتُوا بِمَالٍ اكْتَسَبْتُمُوهُ مِنْ قَطِيعَةِ رَحِمٍ أَوْ حَرَامٍ فَفَعَلُوا فَخُلِّيَ بَيْنَهُمْ وَ بَيْنَ بُنْيَانِهِ فَبَنَوْهُ حَتَّى انْتَهَوْا إِلَى مَوْضِعِ الْحَجَرِ الْأَسْوَدِ فَتَشَاجَرُوا فِيهِ أَيُّهُمْ يَضَعُ الْحَجَرَ فِي مَوْضِعِهِ حَتَّى كَادَ أَنْ يَكُونَ بَيْنَهُمْ شَرٌّ فَحَكَّمُوا أَوَّلَ مَنْ يَدْخُلُ مِنْ بَابِ الْمَسْجِدِ فَدَخَلَ رَسُولُ اللَّهِ ص فَلَمَّا أَتَاهُمْ أَمَرَ بِثَوْبٍ فَبَسَطَ ثُمَّ وَضَعَ الْحَجَرَ فِي وَسَطِهِ ثُمَّ أَخَذَتِ الْقَبَائِلُ بِجَوَانِبِ الثَّوْبِ فَرَفَعُوهُ ثُمَّ تَنَاوَلَهُ عَلَيْهِ السَّلَامُ فَوَضَعَهُ فِي مَوْضِعِهِ فَخَصَّهُ اللَّهُ عَزَّ وَ جَلَّ بِهِ.
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ سَعِيدِ بْنِ عَبْدِ اللَّهِ الْأَعْرَجِ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌ إِنَّ قُرَيْشاً فِي الْجَاهِلِيَّةِ هَدَمُوا الْبَيْتَ فَلَمَّا أَرَادُوا بِنَاءَهُ حِيلَ بَيْنَهُ وَ بَيْنَهُمْ وَ أُلْقِيَ فِي رُوعِهِمُ الرُّعْبُ‌[2] حَتَّى قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن سعید بن عبد الله الاعرج | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 26 · `faqih-2316` — CLARIFIED
- Transmitters (student → teacher): سعيد بن عبد الله الاعرج → ابي عبد الله ع
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ سَعِيدِ بْنِ عَبْدِ اللَّهِ الْأَعْرَجِ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌»
- Isnad ends / matn begins at: "إِنَّ قُرَيْشاً فِي الْجَاهِلِيَّةِ هَدَمُوا الْبَيْتَ فَلَمَّا أَرَادُوا بِنَاءَهُ"
- Mursal opening: al-Ṣadūq → سعيد بن عبد الله الاعرج; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 27 · `faqih-2321`
- **Location:** vol. 2, p. 249 · seq 2328 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ عِيسَى بْنِ يُونُسَ قَالَ‌ كَانَ ابْنُ أَبِي الْعَوْجَاءِ مِنْ تَلَامِذَةِ الْحَسَنِ الْبَصْرِيِّ فَانْحَرَفَ عَنِ التَّوْحِيدِ فَقِيلَ لَهُ تَرَكْتَ مَذْهَبَ صَاحِبِكَ وَ دَخَلْتَ فِيمَا لَا أَصْلَ لَهُ وَ لَا حَقِيقَةَ فَقَالَ إِنَّ صَاحِبِي كَانَ مِخْلَطاً كَانَ يَقُولُ طَوْراً بِالْقَدَرِ وَ طَوْراً بِالْجَبْرِ وَ مَا أَعْلَمُهُ اعْتَقَدَ مَذْهَباً دَامَ عَلَيْهِ قَالَ وَ دَخَلَ مَكَّةَ تَمَرُّداً وَ إِنْكَاراً عَلَى مَنْ يَحُجُّ وَ كَانَ يَكْرَهُ الْعُلَمَاءُ مُسَاءَلَتَهُ إِيَّاهُمْ وَ مُجَالَسَتَهُ لَهُمْ لِخُبْثِ لِسَانِهِ وَ فَسَادِ ضَمِيرِهِ فَأَتَى جَعْفَرَ بْنَ مُحَمَّدٍ ع فَجَلَسَ إِلَيْهِ فِي جَمَاعَةٍ مِنْ نُظَرَائِهِ ثُمَّ قَالَ لَهُ إِنَّ الْمَجَالِسَ أَمَانَاتٌ وَ لَا بُدَّ لِكُلِّ مَنْ كَانَ بِهِ سُعَالٌ أَنْ يَسْعُلَ‌[3] أَ فَتَأْذَنُ لِي فِي الْكَلَامِ فَقَالَ تَكَلَّمْ فَقَالَ إِلَى كَمْ تَدُوسُونَ هَذَا الْبَيْدَرَ وَ تَلُوذُونَ بِهَذَا الْحَجَرِ وَ تَعْبُدُونَ هَذَا الْبَيْتَ الْمَرْفُوعَ‌
بِالطُّوبِ وَ الْمَدَرِ[1] وَ تُهَرْوِلُونَ حَوْلَهُ هَرْوَلَةَ الْبَعِيرِ إِذَا نَفَرَ مَنْ فَكَّرَ فِي هَذَا أَوْ قَدَّرَ عَلِمَ أَنَّ هَذَا فِعْلٌ أَسَّسَهُ غَيْرُ حَكِيمٍ وَ لَا ذِي نَظَرٍ فَقُلْ فَإِنَّكَ رَأْسُ هَذَا الْأَمْرِ وَ سَنَامُهُ وَ أَبُوكَ أُسُّهُ وَ نِظَامُهُ فَقَالَ أَبُو عَبْدِ اللَّهِ ع إِنَّ مَنْ أَضَلَّهُ اللَّهُ وَ أَعْمَى قَلْبَهُ اسْتَوْخَمَ الْحَقَ‌[2] فَلَمْ يَسْتَعْذِبْهُ وَ صَارَ الشَّيْطَانُ وَلِيَّهُ يُورِدُهُ مَنَاهِلَ الْهَلَكَةِ ثُمَّ لَا يُصْدِرُهُ وَ هَذَا بَيْتٌ اسْتَعْبَدَ اللَّهُ بِهِ خَلْقَهُ لِيَخْتَبِرَ طَاعَتَهُمْ فِي إِتْيَانِهِ فَحَثَّهُمْ عَلَى تَعْظِيمِهِ وَ زِيَارَتِهِ وَ جَعَلَهُ مَحَلَّ أَنْبِيَائِهِ وَ قِبْلَةً لِلْمُصَلِّينَ لَهُ فَهُوَ شُعْبَةٌ مِنْ رِضْوَانِهِ وَ طَرِيقٌ يُؤَدِّي إِلَى غُفْرَانِهِ مَنْصُوبٌ عَلَى اسْتِوَاءِ الْكَمَالِ وَ مُجْتَمَعِ الْعَظَمَةِ وَ الْجَلَالِ خَلَقَهُ اللَّهُ قَبْلَ دَحْوِ الْأَرْضِ بِأَلْفَيْ عَامٍ وَ أَحَقُّ مَنْ أُطِيعَ فِيمَا أَمَرَ وَ انْتُهِيَ عَمَّا نَهَى عَنْهُ وَ زَجَرَ اللَّهُ الْمُنْشِئُ لِلْأَرْوَاحِ بِالصُّوَرِ فَقَالَ ابْنُ أَبِي الْعَوْجَاءِ  …[truncated]
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ عِيسَى بْنِ يُونُسَ قَالَ‌ كَانَ ابْنُ أَبِي الْعَوْجَاءِ مِنْ تَلَامِذَةِ الْحَسَنِ الْبَصْرِيِّ فَانْحَرَفَ عَنِ التَّوْحِيدِ فَقِيلَ لَهُ تَرَكْتَ مَذْهَبَ صَاحِبِكَ وَ دَخَلْتَ فِيمَا لَا أَصْلَ لَهُ وَ لَا حَقِيقَةَ فَقَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن عیسی بن یونس | روی |  |

### Chain 27 · `faqih-2321` — CLARIFIED
- Transmitters (student → teacher): عيسي بن يونس
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ عِيسَى بْنِ يُونُسَ قَالَ‌»
- Isnad ends / matn begins at: "كَانَ ابْنُ أَبِي الْعَوْجَاءِ مِنْ تَلَامِذَةِ الْحَسَنِ الْبَصْرِيِّ فَانْحَرَفَ"
- Mursal opening: al-Ṣadūq → عيسي بن يونس; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 28 · `faqih-2321`
- **Location:** vol. 2, p. 249 · seq 2328 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ عِيسَى بْنِ يُونُسَ قَالَ‌ كَانَ ابْنُ أَبِي الْعَوْجَاءِ مِنْ تَلَامِذَةِ الْحَسَنِ الْبَصْرِيِّ فَانْحَرَفَ عَنِ التَّوْحِيدِ فَقِيلَ لَهُ تَرَكْتَ مَذْهَبَ صَاحِبِكَ وَ دَخَلْتَ فِيمَا لَا أَصْلَ لَهُ وَ لَا حَقِيقَةَ فَقَالَ إِنَّ صَاحِبِي كَانَ مِخْلَطاً كَانَ يَقُولُ طَوْراً بِالْقَدَرِ وَ طَوْراً بِالْجَبْرِ وَ مَا أَعْلَمُهُ اعْتَقَدَ مَذْهَباً دَامَ عَلَيْهِ قَالَ وَ دَخَلَ مَكَّةَ تَمَرُّداً وَ إِنْكَاراً عَلَى مَنْ يَحُجُّ وَ كَانَ يَكْرَهُ الْعُلَمَاءُ مُسَاءَلَتَهُ إِيَّاهُمْ وَ مُجَالَسَتَهُ لَهُمْ لِخُبْثِ لِسَانِهِ وَ فَسَادِ ضَمِيرِهِ فَأَتَى جَعْفَرَ بْنَ مُحَمَّدٍ ع فَجَلَسَ إِلَيْهِ فِي جَمَاعَةٍ مِنْ نُظَرَائِهِ ثُمَّ قَالَ لَهُ إِنَّ الْمَجَالِسَ أَمَانَاتٌ وَ لَا بُدَّ لِكُلِّ مَنْ كَانَ بِهِ سُعَالٌ أَنْ يَسْعُلَ‌[3] أَ فَتَأْذَنُ لِي فِي الْكَلَامِ فَقَالَ تَكَلَّمْ فَقَالَ إِلَى كَمْ تَدُوسُونَ هَذَا الْبَيْدَرَ وَ تَلُوذُونَ بِهَذَا الْحَجَرِ وَ تَعْبُدُونَ هَذَا الْبَيْتَ الْمَرْفُوعَ‌
بِالطُّوبِ وَ الْمَدَرِ[1] وَ تُهَرْوِلُونَ حَوْلَهُ هَرْوَلَةَ الْبَعِيرِ إِذَا نَفَرَ مَنْ فَكَّرَ فِي هَذَا أَوْ قَدَّرَ عَلِمَ أَنَّ هَذَا فِعْلٌ أَسَّسَهُ غَيْرُ حَكِيمٍ وَ لَا ذِي نَظَرٍ فَقُلْ فَإِنَّكَ رَأْسُ هَذَا الْأَمْرِ وَ سَنَامُهُ وَ أَبُوكَ أُسُّهُ وَ نِظَامُهُ فَقَالَ أَبُو عَبْدِ اللَّهِ ع إِنَّ مَنْ أَضَلَّهُ اللَّهُ وَ أَعْمَى قَلْبَهُ اسْتَوْخَمَ الْحَقَ‌[2] فَلَمْ يَسْتَعْذِبْهُ وَ صَارَ الشَّيْطَانُ وَلِيَّهُ يُورِدُهُ مَنَاهِلَ الْهَلَكَةِ ثُمَّ لَا يُصْدِرُهُ وَ هَذَا بَيْتٌ اسْتَعْبَدَ اللَّهُ بِهِ خَلْقَهُ لِيَخْتَبِرَ طَاعَتَهُمْ فِي إِتْيَانِهِ فَحَثَّهُمْ عَلَى تَعْظِيمِهِ وَ زِيَارَتِهِ وَ جَعَلَهُ مَحَلَّ أَنْبِيَائِهِ وَ قِبْلَةً لِلْمُصَلِّينَ لَهُ فَهُوَ شُعْبَةٌ مِنْ رِضْوَانِهِ وَ طَرِيقٌ يُؤَدِّي إِلَى غُفْرَانِهِ مَنْصُوبٌ عَلَى اسْتِوَاءِ الْكَمَالِ وَ مُجْتَمَعِ الْعَظَمَةِ وَ الْجَلَالِ خَلَقَهُ اللَّهُ قَبْلَ دَحْوِ الْأَرْضِ بِأَلْفَيْ عَامٍ وَ أَحَقُّ مَنْ أُطِيعَ فِيمَا أَمَرَ وَ انْتُهِيَ عَمَّا نَهَى عَنْهُ وَ زَجَرَ اللَّهُ الْمُنْشِئُ لِلْأَرْوَاحِ بِالصُّوَرِ فَقَالَ ابْنُ أَبِي الْعَوْجَاءِ  …[truncated]
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ عِيسَى بْنِ يُونُسَ قَالَ‌ كَانَ ابْنُ أَبِي الْعَوْجَاءِ مِنْ تَلَامِذَةِ الْحَسَنِ الْبَصْرِيِّ فَانْحَرَفَ عَنِ التَّوْحِيدِ فَقِيلَ لَهُ تَرَكْتَ مَذْهَبَ صَاحِبِكَ وَ دَخَلْتَ فِيمَا لَا أَصْلَ لَهُ وَ لَا حَقِيقَةَ فَقَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن عیسی بن یونس | روی |  |

### Chain 28 · `faqih-2321` — CLARIFIED
- Transmitters (student → teacher): عيسي بن يونس
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ عِيسَى بْنِ يُونُسَ قَالَ‌»
- Isnad ends / matn begins at: "كَانَ ابْنُ أَبِي الْعَوْجَاءِ مِنْ تَلَامِذَةِ الْحَسَنِ الْبَصْرِيِّ فَانْحَرَفَ"
- Mursal opening: al-Ṣadūq → عيسي بن يونس; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 29 · `faqih-2321`
- **Location:** vol. 2, p. 249 · seq 2328 · chain 3
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ عِيسَى بْنِ يُونُسَ قَالَ‌ كَانَ ابْنُ أَبِي الْعَوْجَاءِ مِنْ تَلَامِذَةِ الْحَسَنِ الْبَصْرِيِّ فَانْحَرَفَ عَنِ التَّوْحِيدِ فَقِيلَ لَهُ تَرَكْتَ مَذْهَبَ صَاحِبِكَ وَ دَخَلْتَ فِيمَا لَا أَصْلَ لَهُ وَ لَا حَقِيقَةَ فَقَالَ إِنَّ صَاحِبِي كَانَ مِخْلَطاً كَانَ يَقُولُ طَوْراً بِالْقَدَرِ وَ طَوْراً بِالْجَبْرِ وَ مَا أَعْلَمُهُ اعْتَقَدَ مَذْهَباً دَامَ عَلَيْهِ قَالَ وَ دَخَلَ مَكَّةَ تَمَرُّداً وَ إِنْكَاراً عَلَى مَنْ يَحُجُّ وَ كَانَ يَكْرَهُ الْعُلَمَاءُ مُسَاءَلَتَهُ إِيَّاهُمْ وَ مُجَالَسَتَهُ لَهُمْ لِخُبْثِ لِسَانِهِ وَ فَسَادِ ضَمِيرِهِ فَأَتَى جَعْفَرَ بْنَ مُحَمَّدٍ ع فَجَلَسَ إِلَيْهِ فِي جَمَاعَةٍ مِنْ نُظَرَائِهِ ثُمَّ قَالَ لَهُ إِنَّ الْمَجَالِسَ أَمَانَاتٌ وَ لَا بُدَّ لِكُلِّ مَنْ كَانَ بِهِ سُعَالٌ أَنْ يَسْعُلَ‌[3] أَ فَتَأْذَنُ لِي فِي الْكَلَامِ فَقَالَ تَكَلَّمْ فَقَالَ إِلَى كَمْ تَدُوسُونَ هَذَا الْبَيْدَرَ وَ تَلُوذُونَ بِهَذَا الْحَجَرِ وَ تَعْبُدُونَ هَذَا الْبَيْتَ الْمَرْفُوعَ‌
بِالطُّوبِ وَ الْمَدَرِ[1] وَ تُهَرْوِلُونَ حَوْلَهُ هَرْوَلَةَ الْبَعِيرِ إِذَا نَفَرَ مَنْ فَكَّرَ فِي هَذَا أَوْ قَدَّرَ عَلِمَ أَنَّ هَذَا فِعْلٌ أَسَّسَهُ غَيْرُ حَكِيمٍ وَ لَا ذِي نَظَرٍ فَقُلْ فَإِنَّكَ رَأْسُ هَذَا الْأَمْرِ وَ سَنَامُهُ وَ أَبُوكَ أُسُّهُ وَ نِظَامُهُ فَقَالَ أَبُو عَبْدِ اللَّهِ ع إِنَّ مَنْ أَضَلَّهُ اللَّهُ وَ أَعْمَى قَلْبَهُ اسْتَوْخَمَ الْحَقَ‌[2] فَلَمْ يَسْتَعْذِبْهُ وَ صَارَ الشَّيْطَانُ وَلِيَّهُ يُورِدُهُ مَنَاهِلَ الْهَلَكَةِ ثُمَّ لَا يُصْدِرُهُ وَ هَذَا بَيْتٌ اسْتَعْبَدَ اللَّهُ بِهِ خَلْقَهُ لِيَخْتَبِرَ طَاعَتَهُمْ فِي إِتْيَانِهِ فَحَثَّهُمْ عَلَى تَعْظِيمِهِ وَ زِيَارَتِهِ وَ جَعَلَهُ مَحَلَّ أَنْبِيَائِهِ وَ قِبْلَةً لِلْمُصَلِّينَ لَهُ فَهُوَ شُعْبَةٌ مِنْ رِضْوَانِهِ وَ طَرِيقٌ يُؤَدِّي إِلَى غُفْرَانِهِ مَنْصُوبٌ عَلَى اسْتِوَاءِ الْكَمَالِ وَ مُجْتَمَعِ الْعَظَمَةِ وَ الْجَلَالِ خَلَقَهُ اللَّهُ قَبْلَ دَحْوِ الْأَرْضِ بِأَلْفَيْ عَامٍ وَ أَحَقُّ مَنْ أُطِيعَ فِيمَا أَمَرَ وَ انْتُهِيَ عَمَّا نَهَى عَنْهُ وَ زَجَرَ اللَّهُ الْمُنْشِئُ لِلْأَرْوَاحِ بِالصُّوَرِ فَقَالَ ابْنُ أَبِي الْعَوْجَاءِ  …[truncated]
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ عِيسَى بْنِ يُونُسَ قَالَ‌ كَانَ ابْنُ أَبِي الْعَوْجَاءِ مِنْ تَلَامِذَةِ الْحَسَنِ الْبَصْرِيِّ فَانْحَرَفَ عَنِ التَّوْحِيدِ فَقِيلَ لَهُ تَرَكْتَ مَذْهَبَ صَاحِبِكَ وَ دَخَلْتَ فِيمَا لَا أَصْلَ لَهُ وَ لَا حَقِيقَةَ فَقَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن عیسی بن یونس | روی |  |

### Chain 29 · `faqih-2321` — CLARIFIED
- Transmitters (student → teacher): عيسي بن يونس
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ عِيسَى بْنِ يُونُسَ قَالَ‌»
- Isnad ends / matn begins at: "كَانَ ابْنُ أَبِي الْعَوْجَاءِ مِنْ تَلَامِذَةِ الْحَسَنِ الْبَصْرِيِّ فَانْحَرَفَ"
- Mursal opening: al-Ṣadūq → عيسي بن يونس; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 30 · `faqih-2324`
- **Location:** vol. 2, p. 251 · seq 2331 · chain 1
- **Flags:** `mursal_opening`, `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ أَنَّهُ أُتِيَ أَبُو عَبْدِ اللَّهِ ع فَقِيلَ لَهُ إِنَ‌
سَبُعاً مِنْ سِبَاعِ الطَّيْرِ عَلَى الْكَعْبَةِ لَيْسَ يَمُرُّ بِهِ شَيْ‌ءٌ مِنْ حَمَامِ الْحَرَمِ إِلَّا ضَرَبَهُ فَقَالَ انْصِبُوا لَهُ وَ اقْتُلُوهُ فَإِنَّهُ قَدْ أَلْحَدَ[1].
- **Isnad as currently extracted:**
  > وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ أَنَّهُ أُتِيَ أَبُو عَبْدِ اللَّهِ ع فَقِيلَ لَهُ إِنَ‌ سَبُعاً مِنْ سِبَاعِ الطَّيْرِ عَلَى الْكَعْبَةِ لَيْسَ يَمُرُّ بِهِ شَيْ‌ءٌ مِنْ حَمَامِ الْحَرَمِ إِلَّا ضَرَبَهُ فَقَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن عمار انه اتی ابو عبد الله ع فقیل له ان سبعا من سباع الطیر علی الکعبة لیس یمر به شی ء من حمام الحرم الا ضربه فقال | روی |  |

### Chain 30 · `faqih-2324` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار → أبو عبد الله ع (حكاية واقعة عند الإمام)
- Corrected isnad (Arabic): «وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ أَنَّهُ أُتِيَ أَبُو عَبْدِ اللَّهِ ع»
- Isnad ends / matn begins at: "فَقِيلَ لَهُ إِنَ‌ سَبُعاً مِنْ سِبَاعِ الطَّيْرِ عَلَى الْكَعْبَةِ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name.

---

### Chain 31 · `faqih-2330`
- **Location:** vol. 2, p. 253 · seq 2337 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع أَخَذْتُ سُكّاً[3] مِنْ سُكِّ الْمَقَامِ وَ تُرَاباً مِنْ تُرَابِ الْبَيْتِ وَ سَبْعَ حَصَيَاتٍ فَقَالَ بِئْسَ مَا صَنَعْتَ أَمَّا التُّرَابَ وَ الْحَصَى فَرُدَّهُ‌[4].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن معاویة بن عمار | روی |  |

### Chain 31 · `faqih-2330` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع أَخَذْتُ سُكّاً[3] مِنْ سُكِّ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 32 · `faqih-2334`
- **Location:** vol. 2, p. 254 · seq 2341 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ لَا يَنْبَغِي لِلرَّجُلِ أَنْ يُقِيمَ بِمَكَّةَ سَنَةً قُلْتُ كَيْفَ يَصْنَعُ قَالَ يَتَحَوَّلُ عَنْهَا وَ لَا يَنْبَغِي أَنْ يُرْفَعَ بِنَاءٌ فَوْقَ الْكَعْبَةِ[1].
- **Isnad as currently extracted:**
  > وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ لَا يَنْبَغِي لِلرَّجُلِ أَنْ يُقِيمَ بِمَكَّةَ سَنَةً قُلْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | العلاء | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |
  | 2 | imam | ابی جعفر ع | عن |  |

### Chain 32 · `faqih-2334` — CLARIFIED
- Transmitters (student → teacher): العلاء → محمد بن مسلم → ابي جعفر ع
- Corrected isnad (Arabic): «وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "لَا يَنْبَغِي لِلرَّجُلِ أَنْ يُقِيمَ بِمَكَّةَ سَنَةً قُلْتُ كَيْفَ"
- Mursal opening: al-Ṣadūq → العلاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 33 · `faqih-2337`
- **Location:** vol. 2, p. 254 · seq 2344 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع شَجَرَةٌ أَصْلُهَا فِي الْحِلِّ وَ فَرْعُهَا فِي الْحَرَمِ فَقَالَ حُرِّمَ أَصْلُهَا لِمَكَانِ فَرْعِهَا قُلْتُ فَإِنَّ أَصْلَهَا فِي الْحَرَمِ وَ فَرْعَهَا فِي الْحِلِّ قَالَ حُرِّمَ فَرْعُهَا لِمَكَانِ أَصْلِهَا.
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن معاویة بن عمار | روی |  |

### Chain 33 · `faqih-2337` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع شَجَرَةٌ أَصْلُهَا فِي الْحِلِّ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 34 · `faqih-2342`
- **Location:** vol. 2, p. 255 · seq 2349 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ قُلْتُ لَهُ الْمُحْرِمُ يَنْزِعُ الْحَشِيشَ مِنْ غَيْرِ الْحَرَمِ فَقَالَ نَعَمْ قُلْتُ فَمِنَ الْحَرَمِ قَالَ لَا[3].
- **Isnad as currently extracted:**
  > وَ رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن مسلم | روی |  |
  | 1 | imam | احدهما ع | عن | ambiguous |

### Chain 34 · `faqih-2342` — CLARIFIED
- Transmitters (student → teacher): محمد بن مسلم → احدهما ع
- Corrected isnad (Arabic): «وَ رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ الْمُحْرِمُ يَنْزِعُ الْحَشِيشَ مِنْ غَيْرِ الْحَرَمِ فَقَالَ"
- Mursal opening: al-Ṣadūq → محمد بن مسلم; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 35 · `faqih-2349`
- **Location:** vol. 2, p. 258 · seq 2356 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ قَتَلَ حَمَامَةً مِنْ حَمَامِ الْحَرَمِ وَ هُوَ فِي الْحَرَمِ غَيْرُ مُحْرِمٍ فَقَالَ عَلَيْهِ قِيمَتُهَا وَ هُوَ دِرْهَمٌ يَتَصَدَّقُ بِهِ أَوْ يَشْتَرِي بِهِ طَعَاماً لِحَمَامِ الْحَرَمِ فَإِنْ قَتَلَهَا وَ هُوَ مُحْرِمٌ فِي الْحَرَمِ فَعَلَيْهِ شَاةٌ وَ قِيمَةُ الْحَمَامَةِ[2].
- **Isnad as currently extracted:**
  > وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ قَتَلَ حَمَامَةً مِنْ حَمَامِ الْحَرَمِ وَ هُوَ فِي الْحَرَمِ غَيْرُ مُحْرِمٍ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن الفضیل | روی |  |
  | 1 | imam | ابی الحسن ع | عن |  |

### Chain 35 · `faqih-2349` — CLARIFIED
- Transmitters (student → teacher): محمد بن الفضيل → ابي الحسن ع
- Corrected isnad (Arabic): «وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الْحَسَنِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ قَتَلَ حَمَامَةً مِنْ حَمَامِ الْحَرَمِ وَ"
- Mursal opening: al-Ṣadūq → محمد بن الفضيل; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 36 · `faqih-2349`
- **Location:** vol. 2, p. 258 · seq 2356 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ قَتَلَ حَمَامَةً مِنْ حَمَامِ الْحَرَمِ وَ هُوَ فِي الْحَرَمِ غَيْرُ مُحْرِمٍ فَقَالَ عَلَيْهِ قِيمَتُهَا وَ هُوَ دِرْهَمٌ يَتَصَدَّقُ بِهِ أَوْ يَشْتَرِي بِهِ طَعَاماً لِحَمَامِ الْحَرَمِ فَإِنْ قَتَلَهَا وَ هُوَ مُحْرِمٌ فِي الْحَرَمِ فَعَلَيْهِ شَاةٌ وَ قِيمَةُ الْحَمَامَةِ[2].
- **Isnad as currently extracted:**
  > وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ قَتَلَ حَمَامَةً مِنْ حَمَامِ الْحَرَمِ وَ هُوَ فِي الْحَرَمِ غَيْرُ مُحْرِمٍ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن الفضیل | روی |  |
  | 1 | imam | ابی الحسن ع | عن |  |

### Chain 36 · `faqih-2349` — CLARIFIED
- Transmitters (student → teacher): محمد بن الفضيل → ابي الحسن ع
- Corrected isnad (Arabic): «وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الْحَسَنِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ قَتَلَ حَمَامَةً مِنْ حَمَامِ الْحَرَمِ وَ"
- Mursal opening: al-Ṣadūq → محمد بن الفضيل; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 37 · `faqih-2351`
- **Location:** vol. 2, p. 259 · seq 2358 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الرَّجُلِ يُحْرِمُ وَ عِنْدَهُ فِي أَهْلِهِ صَيْدٌ إِمَّا وَحْشٌ وَ إِمَّا طَيْرٌ قَالَ لَا بَأْسَ‌[1].
- **Isnad as currently extracted:**
  > وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | العلاء | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |

### Chain 37 · `faqih-2351` — CLARIFIED
- Transmitters (student → teacher): العلاء → محمد بن مسلم → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الرَّجُلِ يُحْرِمُ وَ"
- Mursal opening: al-Ṣadūq → العلاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 38 · `faqih-2354`
- **Location:** vol. 2, p. 259 · seq 2361 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى صَفْوَانُ عَنِ الْعِيصِ بْنِ الْقَاسِمِ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع‌
- **Isnad as currently extracted:**
  > وَ رَوَى صَفْوَانُ عَنِ الْعِيصِ بْنِ الْقَاسِمِ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان | روی |  |
  | 1 | named_narrator | العیص بن القاسم | عن |  |

### Chain 38 · `faqih-2354` — CLARIFIED
- Transmitters (student → teacher): صفوان → العيص بن القاسم → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى صَفْوَانُ عَنِ الْعِيصِ بْنِ الْقَاسِمِ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع‌"
- Mursal opening: al-Ṣadūq → صفوان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 39 · `faqih-2356`
- **Location:** vol. 2, p. 260 · seq 2363 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ أُهْدِيَ لَهُ حَمَامٌ أَهْلِيٌّ وَ جِي‌ءَ بِهِ وَ هُوَ فِي الْحَرَمِ مُحِلٌّ قَالَ إِنْ أَصَابَ مِنْهُ شَيْئاً فَلْيَتَصَدَّقْ مَكَانَهُ بِنَحْوٍ مِنْ ثَمَنِهِ‌[4].
- **Isnad as currently extracted:**
  > وَ رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حریز | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |

### Chain 39 · `faqih-2356` — CLARIFIED
- Transmitters (student → teacher): حريز → محمد بن مسلم → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ أُهْدِيَ لَهُ"
- Mursal opening: al-Ṣadūq → حريز; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 40 · `faqih-2357`
- **Location:** vol. 2, p. 260 · seq 2364 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى صَفْوَانُ بْنُ يَحْيَى عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع‌[5] عَنْ رَجُلٍ رَمَى صَيْداً فِي الْحِلِّ وَ هُوَ يَؤُمُّ الْحَرَمَ فِيمَا بَيْنَ الْبَرِيدِ وَ الْمَسْجِدِ فَأَصَابَهُ فِي الْحِلِّ فَمَضَى بِرَمْيَتِهِ حَتَّى دَخَلَ الْحَرَمَ فَمَاتَ مِنْ رَمْيَتِهِ هَلْ عَلَيْهِ جَزَاءٌ فَقَالَ لَيْسَ عَلَيْهِ جَزَاءٌ إِنَّمَا مَثَلُ ذَلِكَ مَثَلُ مَنْ نَصَبَ شَرَكاً فِي الْحِلِّ إِلَى جَانِبِ الْحَرَمِ فَوَقَعَ فِيهِ صَيْدٌ فَاضْطَرَبَ حَتَّى دَخَلَ الْحَرَمَ فَمَاتَ فَلَيْسَ عَلَيْهِ جَزَاؤُهُ لِأَنَّهُ نَصَبَ حَيْثُ نَصَبَ وَ هُوَ لَهُ حَلَالٌ وَ رَمَى حَيْثُ رَمَى وَ هُوَ لَهُ حَلَالٌ فَلَيْسَ عَلَيْهِ فِيمَا كَانَ بَعْدَ ذَلِكَ شَيْ‌ءٌ فَقُلْتُ هَذَا الْقِيَاسُ عِنْدَ النَّاسِ فَقَالَ إِنَّمَا شَبَّهْتُ لَكَ الشَّيْ‌ءَ بِالشَّيْ‌ءِ لِتَعْرِفَهُ.
- **Isnad as currently extracted:**
  > وَ رَوَى صَفْوَانُ بْنُ يَحْيَى عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان بن یحیی | روی |  |
  | 1 | named_narrator | عبد الرحمن بن الحجاج | عن |  |

### Chain 40 · `faqih-2357` — CLARIFIED
- Transmitters (student → teacher): صفوان بن يحيي → عبد الرحمن بن الحجاج → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى صَفْوَانُ بْنُ يَحْيَى عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع‌[5] عَنْ رَجُلٍ رَمَى صَيْداً"
- Mursal opening: al-Ṣadūq → صفوان بن يحيي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 41 · `faqih-2358`
- **Location:** vol. 2, p. 260 · seq 2365 · chain 1
- **Flags:** `matn_spill`, `multi_route`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى الْمُثَنَّى عَنْ كَرِبٍ الصَّيْرَفِيِّ قَالَ‌ كُنَّا جَمِيعاً فَاشْتَرَيْنَا طَيْراً فَقَصَصْنَاهُ فَدَخَلْنَا بِهِ مَكَّةَ فَعَابَ ذَلِكَ أَهْلُ مَكَّةَ فَأَرْسَلَ كَرِبٌ إِلَى أَبِي عَبْدِ اللَّهِ ع فَسَأَلَهُ فَقَالَ اسْتَوْدِعُوهُ رَجُلًا مِنْ أَهْلِ مَكَّةَ- مُسْلِماً أَوِ امْرَأَةً مُسْلِمَةً فَإِذَا اسْتَوَى‌
خَلَّوْا سَبِيلَهُ‌[1].
- **Isnad as currently extracted:**
  > وَ رَوَى الْمُثَنَّى عَنْ كَرِبٍ الصَّيْرَفِيِّ قَالَ‌ كُنَّا جَمِيعاً فَاشْتَرَيْنَا طَيْراً فَقَصَصْنَاهُ فَدَخَلْنَا بِهِ مَكَّةَ فَعَابَ ذَلِكَ أَهْلُ مَكَّةَ فَأَرْسَلَ كَرِبٌ إِلَى أَبِي عَبْدِ اللَّهِ ع فَسَأَلَهُ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | المثنی | روی |  |
  | 1 | named_narrator | کرب الصیرفی | عن |  |

### Chain 41 · `faqih-2358` — CLARIFIED
- Transmitters (student → teacher): المثنى → كرب الصيرفي → أبو عبد الله ع (السؤال والجواب بالمراسلة)
- Corrected isnad (Arabic): «وَ رَوَى الْمُثَنَّى عَنْ كَرِبٍ الصَّيْرَفِيِّ قَالَ‌»
- Isnad ends / matn begins at: "كُنَّا جَمِيعاً فَاشْتَرَيْنَا طَيْراً فَقَصَصْنَاهُ فَدَخَلْنَا بِهِ مَكَّةَ فَعَابَ"
- Mursal opening: al-Ṣadūq → المثنى; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The formal opening chain ends at Karb. Inside the narrative, Karb says that he sent the question to Abū ʿAbd Allāh and received the ruling. This is an indirect correspondence link, not an unresolved fork and not proof of face-to-face audition.
---

### Chain 42 · `faqih-2359`
- **Location:** vol. 2, p. 261 · seq 2366 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى ابْنُ مُسْكَانَ عَنْ إِبْرَاهِيمَ بْنِ مَيْمُونٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ نَتَفَ حَمَامَةً مِنْ حَمَامِ الْحَرَمِ‌[2] فَقَالَ يَتَصَدَّقُ بِصَدَقَةٍ عَلَى مِسْكِينٍ وَ يُعْطِي بِالْيَدِ الَّتِي نَتَفَ بِهَا فَإِنَّهُ قَدْ أَوْجَعَهُ.
- **Isnad as currently extracted:**
  > وَ رَوَى ابْنُ مُسْكَانَ عَنْ إِبْرَاهِيمَ بْنِ مَيْمُونٍ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن مسکان | روی |  |
  | 1 | named_narrator | ابراهیم بن میمون | عن |  |

### Chain 42 · `faqih-2359` — CLARIFIED
- Transmitters (student → teacher): ابن مسكان → ابراهيم بن ميمون → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى ابْنُ مُسْكَانَ عَنْ إِبْرَاهِيمَ بْنِ مَيْمُونٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ نَتَفَ حَمَامَةً مِنْ"
- Mursal opening: al-Ṣadūq → ابن مسكان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 43 · `faqih-2360`
- **Location:** vol. 2, p. 261 · seq 2367 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى صَفْوَانُ عَنْ مَنْصُورِ بْنِ حَازِمٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع أُهْدِيَ لَنَا طَيْرٌ مَذْبُوحٌ بِمَكَّةَ فَأَكَلَهُ أَهْلُنَا فَقَالَ لَا يَرَى بِهِ أَهْلُ مَكَّةَ بَأْساً قُلْتُ فَأَيَّ شَيْ‌ءٍ تَقُولُ أَنْتَ قَالَ عَلَيْهِمْ ثَمَنُهُ.
- **Isnad as currently extracted:**
  > وَ رَوَى صَفْوَانُ عَنْ مَنْصُورِ بْنِ حَازِمٍ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان | روی |  |
  | 1 | named_narrator | منصور بن حازم | عن |  |

### Chain 43 · `faqih-2360` — CLARIFIED
- Transmitters (student → teacher): صفوان → منصور بن حازم → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى صَفْوَانُ عَنْ مَنْصُورِ بْنِ حَازِمٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع أُهْدِيَ لَنَا طَيْرٌ مَذْبُوحٌ"
- Mursal opening: al-Ṣadūq → صفوان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 44 · `faqih-2365`
- **Location:** vol. 2, p. 262 · seq 2372 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى ابْنُ مُسْكَانَ عَنْ يَزِيدَ بْنِ خَلِيفَةَ قَالَ‌ كَانَ فِي جَانِبِ بَيْتِي مِكْتَلٌ‌[2] كَانَ فِيهِ بَيْضَتَانِ مِنْ حَمَامِ الْحَرَمِ فَذَهَبَ غُلَامِي فَكَبَّ الْمِكْتَلَ وَ هُوَ لَا يَعْلَمُ أَنَّ فِيهِ بَيْضَتَيْنِ فَكَسَرَهُمَا فَخَرَجْتُ فَلَقِيتُ عَبْدَ اللَّهِ بْنَ الْحَسَنِ فَذَكَرْتُ ذَلِكَ لَهُ فَقَالَ تَصَدَّقْ بِكَفَّيْنِ مِنْ دَقِيقٍ قَالَ فَلَقِيتُ أَبَا عَبْدِ اللَّهِ ع بَعْدُ فَأَخْبَرْتُهُ فَقَالَ لِي ع عَلَيْهِ ثَمَنُ طَيْرَيْنِ يُطْعِمُ بِهِ حَمَامَ الْحَرَمِ فَلَقِيتُ عَبْدَ اللَّهِ بْنَ الْحَسَنِ فَأَخْبَرْتُهُ فَقَالَ صَدَقَ خُذْ بِهِ فَإِنَّهُ أَخَذَ عَنْ آبَائِهِ ع.
- **Isnad as currently extracted:**
  > وَ رَوَى ابْنُ مُسْكَانَ عَنْ يَزِيدَ بْنِ خَلِيفَةَ قَالَ‌ كَانَ فِي جَانِبِ بَيْتِي مِكْتَلٌ‌[2] كَانَ فِيهِ بَيْضَتَانِ مِنْ حَمَامِ الْحَرَمِ فَذَهَبَ غُلَامِي فَكَبَّ الْمِكْتَلَ وَ هُوَ لَا يَعْلَمُ أَنَّ فِيهِ بَيْضَتَيْنِ فَكَسَرَهُمَا فَخَرَجْتُ فَلَقِيتُ عَبْدَ اللَّهِ بْنَ الْحَسَنِ فَذَكَرْتُ ذَلِكَ لَهُ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن مسکان | روی |  |
  | 1 | named_narrator | یزید بن خلیفة | عن |  |

### Chain 44 · `faqih-2365` — CLARIFIED
- Transmitters (student → teacher): ابن مسكان → يزيد بن خليفة
- Corrected isnad (Arabic): «وَ رَوَى ابْنُ مُسْكَانَ عَنْ يَزِيدَ بْنِ خَلِيفَةَ قَالَ‌»
- Isnad ends / matn begins at: "كَانَ فِي جَانِبِ بَيْتِي مِكْتَلٌ‌[2] كَانَ فِيهِ بَيْضَتَانِ مِنْ"
- Mursal opening: al-Ṣadūq → ابن مسكان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 45 · `faqih-2366`
- **Location:** vol. 2, p. 262 · seq 2373 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ شِهَابِ بْنِ عَبْدِ رَبِّهِ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنِّي أَتَسَحَّرُ بِفِرَاخٍ أُتِيَ بِهَا مِنْ غَيْرِ مَكَّةَ فَتُذْبَحُ فِي الْحَرَمِ فَأَتَسَحَّرُ بِهَا فَقَالَ بِئْسَ السَّحُورُ سَحُورُكَ أَ مَا عَلِمْتَ أَنَّ مَا أَدْخَلْتَ بِهِ الْحَرَمَ حَيّاً فَقَدْ حَرُمَ عَلَيْكَ ذَبْحُهُ وَ إِمْسَاكُهُ‌[3].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ شِهَابِ بْنِ عَبْدِ رَبِّهِ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن شهاب بن عبد ربه | روی |  |

### Chain 45 · `faqih-2366` — CLARIFIED
- Transmitters (student → teacher): شهاب بن عبد ربه
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ شِهَابِ بْنِ عَبْدِ رَبِّهِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنِّي أَتَسَحَّرُ بِفِرَاخٍ أُتِيَ"
- Mursal opening: al-Ṣadūq → شهاب بن عبد ربه; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 46 · `faqih-2368`
- **Location:** vol. 2, p. 263 · seq 2375 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ‌[1] قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ فَرْخَيْنِ مُسَرْوَلَيْنِ‌[2] ذَبَحْتُهُمَا وَ أَنَا بِمَكَّةَ فَقَالَ لِي لِمَ ذَبَحْتَهُمَا فَقُلْتُ جَاءَتْنِي بِهِمَا جَارِيَةٌ مِنْ أَهْلِ مَكَّةَ فَسَأَلَتْنِي أَنْ أَذْبَحَهُمَا فَظَنَنْتُ أَنِّي بِالْكُوفَةِ وَ لَمْ أَذْكُرِ الْحَرَمَ قَالَ تَصَدَّقْ بِقِيمَتِهِمَا قُلْتُ كَمْ قَالَ دِرْهَماً وَ هُوَ خَيْرٌ مِنْهُمَا.
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ‌[1] قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن عبد الرحمن بن الحجاج | روی |  |

### Chain 46 · `faqih-2368` — CLARIFIED
- Transmitters (student → teacher): عبد الرحمن بن الحجاج → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ‌[1] قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ فَرْخَيْنِ مُسَرْوَلَيْنِ‌[2] ذَبَحْتُهُمَا"
- Mursal opening: al-Ṣadūq → عبد الرحمن بن الحجاج; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 47 · `faqih-2370`
- **Location:** vol. 2, p. 263 · seq 2377 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى الْمُثَنَّى عَنْ مُحَمَّدِ بْنِ أَبِي الْحَكَمِ قَالَ‌ قُلْتُ لِغُلَامٍ لَنَا هَيِّئْ لَنَا غَدَاءَنَا فَأَخَذَ لَنَا مِنْ أَطْيَارِ مَكَّةَ فَذَبَحَهَا وَ طَبَخَهَا فَدَخَلْتُ عَلَى أَبِي عَبْدِ اللَّهِ ع فَقَالَ ادْفِنْهُنَّ وَ افْدِ عَنْ كُلِّ طَيْرٍ مِنْهُنَّ.
- **Isnad as currently extracted:**
  > وَ رَوَى الْمُثَنَّى عَنْ مُحَمَّدِ بْنِ أَبِي الْحَكَمِ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | المثنی | روی |  |
  | 1 | named_narrator | محمد بن ابی الحکم | عن |  |

### Chain 47 · `faqih-2370` — CLARIFIED
- Transmitters (student → teacher): المثني → محمد بن ابي الحكم → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى الْمُثَنَّى عَنْ مُحَمَّدِ بْنِ أَبِي الْحَكَمِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِغُلَامٍ لَنَا هَيِّئْ لَنَا غَدَاءَنَا فَأَخَذَ لَنَا مِنْ"
- Mursal opening: al-Ṣadūq → المثني; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 48 · `faqih-2380`
- **Location:** vol. 2, p. 265 · seq 2387 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى عَنْهُ ع مُعَاوِيَةُ بْنُ عَمَّارٍ أَنَّهُ قَالَ‌ لَا بَأْسَ بِقَتْلِ النَّمْلِ‌[1] وَ الْبَقِّ فِي الْحَرَمِ وَ قَالَ لَا بَأْسَ بِقَتْلِ الْقَمْلَةِ فِي الْحَرَمِ وَ غَيْرِهِ.
- **Isnad as currently extracted:**
  > وَ رَوَى عَنْهُ ع مُعَاوِيَةُ بْنُ عَمَّارٍ أَنَّهُ قَالَ‌ لَا بَأْسَ بِقَتْلِ النَّمْلِ‌[1] وَ الْبَقِّ فِي الْحَرَمِ وَ قَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عنه ع معاویة بن عمار | روی |  |

### Chain 48 · `faqih-2380` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار → أبو عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى عَنْهُ ع مُعَاوِيَةُ بْنُ عَمَّارٍ أَنَّهُ قَالَ‌»
- Isnad ends / matn begins at: "لَا بَأْسَ بِقَتْلِ النَّمْلِ‌[1] وَ الْبَقِّ فِي الْحَرَمِ وَ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The antecedent of «عنه ع» is Abū ʿAbd Allāh. The same report is catalogued under Muʿāwiya b. ʿAmmār’s narrations from Imam al-Ṣādiq, and its parallel routes pass through Muʿāwiya. Source: [Kitāb al-Ḥajj—Muʿāwiya b. ʿAmmār, p. 30](https://ablibrary.net/book_content/13399/30).
---

### Chain 49 · `faqih-2396`
- **Location:** vol. 2, p. 267 · seq 2403 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ أَبِي أَيُّوبَ الْخَزَّازِ أَنَّهُ قَالَ‌ أَرَدْنَا أَنْ نَخْرُجَ فَجِئْنَا نُسَلِّمُ عَلَى أَبِي عَبْدِ اللَّهِ ع فَقَالَ كَأَنَّكُمْ طَلَبْتُمْ بَرَكَةَ الْإِثْنَيْنِ قُلْنَا نَعَمْ قَالَ فَأَيُّ يَوْمٍ أَعْظَمُ شُؤْماً مِنْ يَوْمِ الْإِثْنَيْنِ فَقَدْنَا فِيهِ نَبِيَّنَا ص وَ ارْتَفَعَ الْوَحْيُ عَنَّا لَا تَخْرُجُوا يَوْمَ الْإِثْنَيْنِ وَ اخْرُجُوا يَوْمَ الثَّلَاثَاءِ.
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ أَبِي أَيُّوبَ الْخَزَّازِ أَنَّهُ قَالَ‌ أَرَدْنَا أَنْ نَخْرُجَ فَجِئْنَا نُسَلِّمُ عَلَى أَبِي عَبْدِ اللَّهِ ع فَقَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن ابی ایوب الخزاز | روی |  |

### Chain 49 · `faqih-2396` — CLARIFIED
- Transmitters (student → teacher): ابي ايوب الخزاز
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ أَبِي أَيُّوبَ الْخَزَّازِ أَنَّهُ قَالَ‌»
- Isnad ends / matn begins at: "أَرَدْنَا أَنْ نَخْرُجَ فَجِئْنَا نُسَلِّمُ عَلَى أَبِي عَبْدِ اللَّهِ"
- Mursal opening: al-Ṣadūq → ابي ايوب الخزاز; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 50 · `faqih-2398`
- **Location:** vol. 2, p. 267 · seq 2405 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ عَبْدِ الْمَلِكِ بْنِ أَعْيَنَ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنِّي قَدِ ابْتُلِيتُ بِهَذَا الْعِلْمِ فَأُرِيدُ الْحَاجَةَ فَإِذَا نَظَرْتُ إِلَى الطَّالِعِ وَ رَأَيْتُ الطَّالِعَ الشَّرَّ جَلَسْتُ وَ لَمْ أَذْهَبْ فِيهَا وَ إِذَا رَأَيْتُ الطَّالِعَ الْخَيْرَ ذَهَبْتُ فِي الْحَاجَةِ فَقَالَ لِي تَقْضِي‌[2] قُلْتُ نَعَمْ قَالَ أَحْرِقْ كُتُبَكَ‌[3].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ عَبْدِ الْمَلِكِ بْنِ أَعْيَنَ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن عبد الملک بن اعین | روی |  |

### Chain 50 · `faqih-2398` — CLARIFIED
- Transmitters (student → teacher): عبد الملك بن اعين → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ عَبْدِ الْمَلِكِ بْنِ أَعْيَنَ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنِّي قَدِ ابْتُلِيتُ بِهَذَا"
- Mursal opening: al-Ṣadūq → عبد الملك بن اعين; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 51 · `faqih-2401`
- **Location:** vol. 2, p. 269 · seq 2408 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ حَمَّادِ بْنِ عُثْمَانَ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع أَ يُكْرَهُ السَّفَرُ فِي شَيْ‌ءٍ مِنَ الْأَيَّامِ الْمَكْرُوهَةِ مِثْلِ الْأَرْبِعَاءِ وَ غَيْرِهِ فَقَالَ افْتَتِحْ سَفَرَكَ بِالصَّدَقَةِ وَ اخْرُجْ إِذَا بَدَا لَكَ وَ اقْرَأْ آيَةَ الْكُرْسِيِّ وَ احْتَجِمْ إِذَا بَدَا لَكَ‌[1].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ حَمَّادِ بْنِ عُثْمَانَ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن حماد بن عثمان | روی |  |

### Chain 51 · `faqih-2401` — CLARIFIED
- Transmitters (student → teacher): حماد بن عثمان
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ حَمَّادِ بْنِ عُثْمَانَ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع أَ يُكْرَهُ السَّفَرُ فِي"
- Mursal opening: al-Ṣadūq → حماد بن عثمان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 52 · `faqih-2402`
- **Location:** vol. 2, p. 269 · seq 2409 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ ابْنِ أَبِي عُمَيْرٍ أَنَّهُ‌[2] قَالَ‌ كُنْتُ أَنْظُرُ فِي النُّجُومِ وَ أَعْرِفُهَا[3] وَ أَعْرِفُ الطَّالِعَ فَيَدْخُلُنِي مِنْ ذَلِكَ شَيْ‌ءٌ فَشَكَوْتُ ذَلِكَ إِلَى أَبِي الْحَسَنِ مُوسَى بْنِ جَعْفَرٍ ع فَقَالَ إِذَا وَقَعَ فِي نَفْسِكَ شَيْ‌ءٌ فَتَصَدَّقْ عَلَى أَوَّلِ مِسْكِينٍ ثُمَّ امْضِ فَإِنَّ اللَّهَ عَزَّ وَ جَلَّ يَدْفَعُ عَنْكَ‌[4].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ ابْنِ أَبِي عُمَيْرٍ أَنَّهُ‌[2] قَالَ‌ كُنْتُ أَنْظُرُ فِي النُّجُومِ وَ أَعْرِفُهَا[3] وَ أَعْرِفُ الطَّالِعَ فَيَدْخُلُنِي مِنْ ذَلِكَ شَيْ‌ءٌ فَشَكَوْتُ ذَلِكَ إِلَى أَبِي الْحَسَنِ مُوسَى بْنِ جَعْفَرٍ ع فَقَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن ابن ابی عمیر | روی |  |

### Chain 52 · `faqih-2402` — CLARIFIED
- Transmitters (student → teacher): ابن ابي عمير
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ ابْنِ أَبِي عُمَيْرٍ أَنَّهُ‌[2] قَالَ‌»
- Isnad ends / matn begins at: "كُنْتُ أَنْظُرُ فِي النُّجُومِ وَ أَعْرِفُهَا[3] وَ أَعْرِفُ الطَّالِعَ"
- Mursal opening: al-Ṣadūq → ابن ابي عمير; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 53 · `faqih-2413`
- **Location:** vol. 2, p. 272 · seq 2420 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى أَبُو بَصِيرٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ مَنْ قَالَ حِينَ يَخْرُجُ مِنْ بَابِ دَارِهِ‌[4] أَعُوذُ بِاللَّهِ مِمَّا عَاذَتْ مِنْهُ مَلَائِكَةُ اللَّهِ مِنْ شَرِّ هَذَا الْيَوْمِ وَ مِنْ شَرِّ الشَّيَاطِينِ وَ مِنْ شَرِّ مَنْ نَصَبَ لِأَوْلِيَاءِ اللَّهِ عَزَّ وَ جَلَّ وَ مِنْ شَرِّ الْجِنِّ وَ الْإِنْسِ وَ مِنْ شَرِّ السِّبَاعِ وَ الْهَوَامِّ وَ مِنْ شَرِّ رُكُوبِ الْمَحَارِمِ كُلِّهَا أُجِيرُ نَفْسِي بِاللَّهِ مِنْ كُلِّ شَرٍّ غَفَرَ اللَّهُ لَهُ وَ تَابَ عَلَيْهِ‌[5] وَ كَفَاهُ الْمُهِمَّ وَ حَجَزَهُ عَنِ السُّوءِ وَ عَصَمَهُ مِنَ الشَّرِّ.
- **Isnad as currently extracted:**
  > وَ رَوَى أَبُو بَصِيرٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ مَنْ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابو بصیر | روی |  |
  | 1 | imam | ابی جعفر ع | عن |  |

### Chain 53 · `faqih-2413` — CLARIFIED
- Transmitters (student → teacher): ابو بصير → ابي جعفر ع
- Corrected isnad (Arabic): «وَ رَوَى أَبُو بَصِيرٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "مَنْ قَالَ حِينَ يَخْرُجُ مِنْ بَابِ دَارِهِ‌[4] أَعُوذُ بِاللَّهِ"
- Mursal opening: al-Ṣadūq → ابو بصير; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 54 · `faqih-2437`
- **Location:** vol. 2, p. 278 · seq 2444 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى شِهَابُ بْنُ عَبْدِ رَبِّهِ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع قَدْ عَرَفْتَ‌
حَالِي وَ سَعَةَ يَدِي وَ تَوْسِيعِي عَلَى إِخْوَانِي فَأَصْحَبُ النَّفَرَ مِنْهُمْ فِي طَرِيقِ مَكَّةَ فَأُوَسِّعُ عَلَيْهِمْ قَالَ لَا تَفْعَلْ يَا شِهَابُ فَإِنَّكَ إِنْ بَسَطْتَ وَ بَسَطُوا أَجْحَفْتَ بِهِمْ‌[1] وَ إِنْ هُمْ أَمْسَكُوا أَذْلَلْتَهُمْ فَاصْحَبْ نُظَرَاءَكَ اصْحَبْ نُظَرَاءَكَ‌[2].
- **Isnad as currently extracted:**
  > وَ رَوَى شِهَابُ بْنُ عَبْدِ رَبِّهِ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | شهاب بن عبد ربه | روی |  |

### Chain 54 · `faqih-2437` — CLARIFIED
- Transmitters (student → teacher): شهاب بن عبد ربه
- Corrected isnad (Arabic): «وَ رَوَى شِهَابُ بْنُ عَبْدِ رَبِّهِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع قَدْ عَرَفْتَ‌ حَالِي وَ"
- Mursal opening: al-Ṣadūq → شهاب بن عبد ربه; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 55 · `faqih-2444`
- **Location:** vol. 2, p. 280 · seq 2451 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ صَفْوَانَ الْجَمَّالِ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ مَعِي أَهْلِي وَ أَنَا أُرِيدُ الْحَجَّ فَأَشُدُّ نَفَقَتِي فِي حَقْوَيَّ قَالَ نَعَمْ فَإِنَّ أَبِي ع كَانَ يَقُولُ مِنْ قُوَّةِ الْمُسَافِرِ حِفْظُ نَفَقَتِهِ‌[2].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ صَفْوَانَ الْجَمَّالِ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن صفوان الجمال | روی |  |

### Chain 55 · `faqih-2444` — CLARIFIED
- Transmitters (student → teacher): صفوان الجمال → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنْ صَفْوَانَ الْجَمَّالِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ مَعِي أَهْلِي وَ"
- Mursal opening: al-Ṣadūq → صفوان الجمال; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 56 · `faqih-2445`
- **Location:** vol. 2, p. 280 · seq 2452 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى عَلِيُّ بْنُ أَسْبَاطٍ عَنْ عَمِّهِ يَعْقُوبَ بْنِ سَالِمٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع تَكُونُ مَعِيَ الدَّرَاهِمُ فِيهَا تَمَاثِيلُ وَ أَنَا مُحْرِمٌ فَأَجْعَلُهَا فِي هِمْيَانِي وَ أَشُدُّهُ فِي وَسَطِي قَالَ لَا بَأْسَ أَ وَ لَيْسَ هِيَ نَفَقَتَكَ وَ عَلَيْهَا اعْتِمَادُكَ بَعْدَ اللَّهِ عَزَّ وَ جَلَّ.
- **Isnad as currently extracted:**
  > وَ رَوَى عَلِيُّ بْنُ أَسْبَاطٍ عَنْ عَمِّهِ يَعْقُوبَ بْنِ سَالِمٍ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن اسباط | روی |  |
  | 1 | named_narrator | عمه یعقوب بن سالم | عن |  |

### Chain 56 · `faqih-2445` — CLARIFIED
- Transmitters (student → teacher): علي بن اسباط → عمه يعقوب بن سالم → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى عَلِيُّ بْنُ أَسْبَاطٍ عَنْ عَمِّهِ يَعْقُوبَ بْنِ سَالِمٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع تَكُونُ مَعِيَ الدَّرَاهِمُ فِيهَا"
- Mursal opening: al-Ṣadūq → علي بن اسباط; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 57 · `faqih-2447`
- **Location:** vol. 2, p. 281 · seq 2454 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ نَصْرٍ الْخَادِمِ قَالَ‌ نَظَرَ الْعَبْدُ الصَّالِحُ أَبُو الْحَسَنِ مُوسَى بْنُ جَعْفَرٍ ع إِلَى سُفْرَةٍ عَلَيْهَا حَلَقُ صُفْرٍ[1] فَقَالَ انْزِعُوا هَذِهِ وَ اجْعَلُوا مَكَانَهَا حَدِيداً فَإِنَّهُ لَا يَقْرَبُ شَيْئاً مِمَّا فِيهَا شَيْ‌ءٌ مِنَ الْهَوَامِّ.
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ نَصْرٍ الْخَادِمِ قَالَ‌ نَظَرَ الْعَبْدُ الصَّالِحُ أَبُو الْحَسَنِ مُوسَى بْنُ جَعْفَرٍ ع إِلَى سُفْرَةٍ عَلَيْهَا حَلَقُ صُفْرٍ[1] فَقَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن نصر الخادم | روی |  |

### Chain 57 · `faqih-2447` — CLARIFIED
- Transmitters (student → teacher): نصر الخادم
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ نَصْرٍ الْخَادِمِ قَالَ‌»
- Isnad ends / matn begins at: "نَظَرَ الْعَبْدُ الصَّالِحُ أَبُو الْحَسَنِ مُوسَى بْنُ جَعْفَرٍ ع"
- Mursal opening: al-Ṣadūq → نصر الخادم; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 58 · `faqih-2472`
- **Location:** vol. 2, p. 289 · seq 2479 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى حَمَّادُ بْنُ عُثْمَانَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ لَهُ جُعِلْتُ فِدَاكَ نَرَى الدَّوَابَّ فِي بُطُونِ أَيْدِيهَا مِثْلُ الرُّقْعَتَيْنِ‌[1] فِي بَاطِنِ يَدَيْهَا مِثْلُ الْكَيِ‌[2] فَأَيُّ شَيْ‌ءٍ هُوَ قَالَ ذَلِكَ مَوْضِعُ مَنْخِرَيْهِ فِي بَطْنِ أُمِّهِ.
- **Isnad as currently extracted:**
  > رَوَى حَمَّادُ بْنُ عُثْمَانَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حماد بن عثمان | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 58 · `faqih-2472` — CLARIFIED
- Transmitters (student → teacher): حماد بن عثمان → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى حَمَّادُ بْنُ عُثْمَانَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ جُعِلْتُ فِدَاكَ نَرَى الدَّوَابَّ فِي بُطُونِ أَيْدِيهَا"
- Mursal opening: al-Ṣadūq → حماد بن عثمان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 59 · `faqih-2489`
- **Location:** vol. 2, p. 292 · seq 2496 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ أَيُّوبُ بْنُ أَعْيَنَ قَالَ‌ سَمِعْتُ الْوَلِيدَ بْنَ صَبِيحٍ يَقُولُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ أَبَا حَنِيفَةَ[4] رَأَى هِلَالَ ذِي الْحِجَّةِ بِالْقَادِسِيَّةِ وَ شَهِدَ مَعَنَا عَرَفَةَ-
فَقَالَ مَا لِهَذَا صَلَاةٌ مَا لِهَذَا صَلَاةٌ[1].
- **Isnad as currently extracted:**
  > وَ رُوِيَ أَيُّوبُ بْنُ أَعْيَنَ قَالَ‌ سَمِعْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ایوب بن اعین | روی |  |

### Chain 59 · `faqih-2489` — CLARIFIED
- Transmitters (student → teacher): ايوب بن اعين → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ أَيُّوبُ بْنُ أَعْيَنَ قَالَ‌»
- Isnad ends / matn begins at: "سَمِعْتُ الْوَلِيدَ بْنَ صَبِيحٍ يَقُولُ لِأَبِي عَبْدِ اللَّهِ ع"
- Mursal opening: al-Ṣadūq → ايوب بن اعين; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 60 · `faqih-2500`
- **Location:** vol. 2, p. 295 · seq 2507 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى عَلِيُّ بْنُ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ لَهُ قَوْلُ اللَّهِ عَزَّ وَ جَلَّ- وَ لِلَّهِ عَلَى النَّاسِ حِجُّ الْبَيْتِ مَنِ اسْتَطاعَ إِلَيْهِ سَبِيلًا قَالَ يَخْرُجُ يَمْشِي إِنْ لَمْ يَكُنْ عِنْدَهُ شَيْ‌ءٌ قُلْتُ لَا يَقْدِرُ عَلَى الْمَشْيِ قَالَ يَمْشِي‌
وَ يَرْكَبُ قُلْتُ لَا يَقْدِرُ عَلَى ذَلِكَ قَالَ يَخْدُمُ الْقَوْمَ وَ يَخْرُجُ مَعَهُمْ‌[1].
- **Isnad as currently extracted:**
  > وَ رَوَى عَلِيُّ بْنُ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن ابی حمزة | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |
  | 2 | imam | ابی عبد الله ع | عن |  |

### Chain 60 · `faqih-2500` — CLARIFIED
- Transmitters (student → teacher): علي بن ابي حمزة → ابي بصير → ابي عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى عَلِيُّ بْنُ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ قَوْلُ اللَّهِ عَزَّ وَ جَلَّ- وَ لِلَّهِ"
- Mursal opening: al-Ṣadūq → علي بن ابي حمزة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 61 · `faqih-2517`
- **Location:** vol. 2, p. 302 · seq 2524 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ سَمَاعَةَ قَالَ‌ سَأَلْتُهُ عَنِ الْحِجَامَةِ وَ حَلْقِ الْقَفَا فِي أَشْهُرِ الْحَجِّ قَالَ لَا بَأْسَ وَ لَا بَأْسَ بِالنُّورَةِ وَ السِّوَاكِ‌[3].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ سَمَاعَةَ قَالَ‌ سَأَلْتُهُ عَنِ الْحِجَامَةِ وَ حَلْقِ الْقَفَا فِي أَشْهُرِ الْحَجِّ قَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن سماعة | روی |  |

### Chain 61 · `faqih-2517` — CLARIFIED
- Transmitters (student → teacher): سماعة → أبو عبد الله ع
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ سَمَاعَةَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْحِجَامَةِ وَ حَلْقِ الْقَفَا فِي أَشْهُرِ الْحَجِّ"
- Mursal opening: al-Ṣadūq → سماعة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: A full parallel explicitly reads «زُرْعَةَ عَنْ سَمَاعَةَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ: سَأَلْتُهُ...», resolving the pronoun to Imam al-Ṣādiq. Source: [al-Istibṣār, vol. 2, p. 160](https://ar.lib.eshia.ir/11002/2/160). This and Chain 62 are duplicate tokenizer records of one textual report.
---

### Chain 62 · `faqih-2517`
- **Location:** vol. 2, p. 302 · seq 2524 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ سَمَاعَةَ قَالَ‌ سَأَلْتُهُ عَنِ الْحِجَامَةِ وَ حَلْقِ الْقَفَا فِي أَشْهُرِ الْحَجِّ قَالَ لَا بَأْسَ وَ لَا بَأْسَ بِالنُّورَةِ وَ السِّوَاكِ‌[3].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ سَمَاعَةَ قَالَ‌ سَأَلْتُهُ عَنِ الْحِجَامَةِ وَ حَلْقِ الْقَفَا فِي أَشْهُرِ الْحَجِّ قَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن سماعة | روی |  |

### Chain 62 · `faqih-2517` — CLARIFIED
- Transmitters (student → teacher): سماعة → أبو عبد الله ع
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ سَمَاعَةَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْحِجَامَةِ وَ حَلْقِ الْقَفَا فِي أَشْهُرِ الْحَجِّ"
- Mursal opening: al-Ṣadūq → سماعة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: Duplicate tokenizer record of Chain 61, not a second independent route. The full parallel names Abū ʿAbd Allāh explicitly: [al-Istibṣār, vol. 2, p. 160](https://ar.lib.eshia.ir/11002/2/160).
---

### Chain 63 · `faqih-2524`
- **Location:** vol. 2, p. 306 · seq 2531 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ أَبِي بَصِيرٍ[2] قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّا نُرْوَى بِالْكُوفَةِ أَنَّ عَلِيّاً ع قَالَ إِنَّ مِنْ تَمَامِ حَجِّكَ إِحْرَامُكَ مِنْ دُوَيْرَةِ أَهْلِكَ فَقَالَ سُبْحَانَ اللَّهِ لَوْ كَانَ كَمَا يَقُولُونَ لَمَا تَمَتَّعَ‌[3] رَسُولُ اللَّهِ ص بِثِيَابِهِ إِلَى الشَّجَرَةِ[4].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ أَبِي بَصِيرٍ[2] قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن ابی بصیر | روی |  |

### Chain 63 · `faqih-2524` — CLARIFIED
- Transmitters (student → teacher): ابي بصير → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ أَبِي بَصِيرٍ[2] قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّا نُرْوَى بِالْكُوفَةِ أَنَّ"
- Mursal opening: al-Ṣadūq → ابي بصير; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 64 · `faqih-2530`
- **Location:** vol. 2, p. 308 · seq 2537 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى مُعَاوِيَةُ بْنُ وَهْبٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع وَ نَحْنُ بِالْمَدِينَةِ عَنِ التَّهَيُّؤِ لِلْإِحْرَامِ فَقَالَ اطَّلِ بِالْمَدِينَةِ وَ تَجَهَّزْ بِكُلِّ مَا تُرِيدُ وَ اغْتَسِلْ إِنْ شِئْتَ‌[2]- وَ إِنْ شِئْتَ اسْتَمْتَعْتَ بِقَمِيصِكَ حَتَّى تَأْتِيَ مَسْجِدَ الشَّجَرَةِ.
- **Isnad as currently extracted:**
  > وَ رَوَى مُعَاوِيَةُ بْنُ وَهْبٍ قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن وهب | روی |  |

### Chain 64 · `faqih-2530` — CLARIFIED
- Transmitters (student → teacher): معاوية بن وهب → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى مُعَاوِيَةُ بْنُ وَهْبٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع وَ نَحْنُ بِالْمَدِينَةِ عَنِ"
- Mursal opening: al-Ṣadūq → معاوية بن وهب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 65 · `faqih-2535`
- **Location:** vol. 2, p. 310 · seq 2542 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْهُ ع قَالَ‌ الرَّجُلُ يَدَّهِنُ بِأَيِّ دُهْنٍ شَاءَ إِذَا لَمْ يَكُنْ فِيهِ مِسْكٌ وَ لَا عَنْبَرٌ وَ لَا زَعْفَرَانٌ وَ لَا وَرْسٌ‌[2] قَبْلَ أَنْ يَغْتَسِلَ لِلْإِحْرَامِ قَالَ وَ لَا تُجَمِّرْ ثَوْباً لِإِحْرَامِكَ.
- **Isnad as currently extracted:**
  > وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْهُ ع قَالَ‌ الرَّجُلُ يَدَّهِنُ بِأَيِّ دُهْنٍ شَاءَ إِذَا لَمْ يَكُنْ فِيهِ مِسْكٌ وَ لَا عَنْبَرٌ وَ لَا زَعْفَرَانٌ وَ لَا وَرْسٌ‌[2] قَبْلَ أَنْ يَغْتَسِلَ لِلْإِحْرَامِ قَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | imam | معاویة بن عمار عنه ع | روی |  |

### Chain 65 · `faqih-2535` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار عنه ع
- Corrected isnad (Arabic): «وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْهُ ع قَالَ‌»
- Isnad ends / matn begins at: "الرَّجُلُ يَدَّهِنُ بِأَيِّ دُهْنٍ شَاءَ إِذَا لَمْ يَكُنْ فِيهِ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار عنه ع; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 66 · `faqih-2536`
- **Location:** vol. 2, p. 310 · seq 2543 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى الْقَاسِمُ بْنُ مُحَمَّدٍ الْجَوْهَرِيُّ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ قَالَ‌ سَأَلْتُهُ عَنِ الرَّجُلِ يَدَّهِنُ بِدُهْنٍ فِيهِ طِيبٌ وَ هُوَ يُرِيدُ أَنْ يُحْرِمَ فَقَالَ لَا تَدَّهِنْ حِينَ تُرِيدُ أَنْ تُحْرِمَ بِدُهْنٍ فِيهِ مِسْكٌ وَ لَا عَنْبَرٌ يَبْقَى رِيحُهُ فِي رَأْسِكَ بَعْدَ مَا تُحْرِمُ وَ ادَّهِنْ بِمَا شِئْتَ مِنَ الدُّهْنِ حِينَ تُرِيدُ أَنْ تُحْرِمَ قَبْلَ الْغُسْلِ وَ بَعْدَهُ فَإِذَا أَحْرَمْتَ فَقَدْ حَرُمَ عَلَيْكَ الدُّهْنُ حَتَّى تُحِلَّ.
- **Isnad as currently extracted:**
  > وَ رَوَى الْقَاسِمُ بْنُ مُحَمَّدٍ الْجَوْهَرِيُّ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ قَالَ‌ سَأَلْتُهُ عَنِ الرَّجُلِ يَدَّهِنُ بِدُهْنٍ فِيهِ طِيبٌ وَ هُوَ يُرِيدُ أَنْ يُحْرِمَ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | القاسم بن محمد الجوهری | روی |  |
  | 1 | named_narrator | علی بن ابی حمزة | عن |  |

### Chain 66 · `faqih-2536` — CLARIFIED
- Transmitters (student → teacher): القاسم بن محمد الجوهري → علي بن ابي حمزة
- Corrected isnad (Arabic): «وَ رَوَى الْقَاسِمُ بْنُ مُحَمَّدٍ الْجَوْهَرِيُّ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الرَّجُلِ يَدَّهِنُ بِدُهْنٍ فِيهِ طِيبٌ وَ هُوَ"
- Mursal opening: al-Ṣadūq → القاسم بن محمد الجوهري; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 67 · `faqih-2536`
- **Location:** vol. 2, p. 310 · seq 2543 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى الْقَاسِمُ بْنُ مُحَمَّدٍ الْجَوْهَرِيُّ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ قَالَ‌ سَأَلْتُهُ عَنِ الرَّجُلِ يَدَّهِنُ بِدُهْنٍ فِيهِ طِيبٌ وَ هُوَ يُرِيدُ أَنْ يُحْرِمَ فَقَالَ لَا تَدَّهِنْ حِينَ تُرِيدُ أَنْ تُحْرِمَ بِدُهْنٍ فِيهِ مِسْكٌ وَ لَا عَنْبَرٌ يَبْقَى رِيحُهُ فِي رَأْسِكَ بَعْدَ مَا تُحْرِمُ وَ ادَّهِنْ بِمَا شِئْتَ مِنَ الدُّهْنِ حِينَ تُرِيدُ أَنْ تُحْرِمَ قَبْلَ الْغُسْلِ وَ بَعْدَهُ فَإِذَا أَحْرَمْتَ فَقَدْ حَرُمَ عَلَيْكَ الدُّهْنُ حَتَّى تُحِلَّ.
- **Isnad as currently extracted:**
  > وَ رَوَى الْقَاسِمُ بْنُ مُحَمَّدٍ الْجَوْهَرِيُّ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ قَالَ‌ سَأَلْتُهُ عَنِ الرَّجُلِ يَدَّهِنُ بِدُهْنٍ فِيهِ طِيبٌ وَ هُوَ يُرِيدُ أَنْ يُحْرِمَ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | القاسم بن محمد الجوهری | روی |  |
  | 1 | named_narrator | علی بن ابی حمزة | عن |  |

### Chain 67 · `faqih-2536` — CLARIFIED
- Transmitters (student → teacher): القاسم بن محمد الجوهري → علي بن ابي حمزة
- Corrected isnad (Arabic): «وَ رَوَى الْقَاسِمُ بْنُ مُحَمَّدٍ الْجَوْهَرِيُّ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الرَّجُلِ يَدَّهِنُ بِدُهْنٍ فِيهِ طِيبٌ وَ هُوَ"
- Mursal opening: al-Ṣadūq → القاسم بن محمد الجوهري; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 68 · `faqih-2544`
- **Location:** vol. 2, p. 314 · seq 2552 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ يَعْقُوبَ بْنِ شُعَيْبٍ‌[3] قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الرَّجُلُ يُحْرِمُ بِحَجَّةٍ وَ عُمْرَةٍ وَ يُنْشِئُ الْعُمْرَةَ أَ يَتَمَتَّعُ‌[4] قَالَ نَعَمْ.
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ يَعْقُوبَ بْنِ شُعَيْبٍ‌[3] قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن یعقوب بن شعیب | روی |  |

### Chain 68 · `faqih-2544` — CLARIFIED
- Transmitters (student → teacher): يعقوب بن شعيب → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ يَعْقُوبَ بْنِ شُعَيْبٍ‌[3] قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الرَّجُلُ يُحْرِمُ بِحَجَّةٍ وَ"
- Mursal opening: al-Ṣadūq → يعقوب بن شعيب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 69 · `faqih-2545`
- **Location:** vol. 2, p. 314 · seq 2553 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ أَبِي بَصِيرٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ يُفْرِدُ الْحَجَّ فَيَطُوفُ بِالْبَيْتِ وَ يَسْعَى بَيْنَ الصَّفَا وَ الْمَرْوَةِ ثُمَّ يَبْدُو لَهُ أَنْ يَجْعَلَهَا عُمْرَةً فَقَالَ إِنْ كَانَ لَبَّى بَعْدَ مَا سَعَى قَبْلَ أَنْ يُقَصِّرَ فَلَا مُتْعَةَ لَهُ‌[5].
- **Isnad as currently extracted:**
  > وَ رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ أَبِي بَصِيرٍ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | اسحاق بن عمار | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |

### Chain 69 · `faqih-2545` — CLARIFIED
- Transmitters (student → teacher): اسحاق بن عمار → ابي بصير
- Corrected isnad (Arabic): «وَ رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ يُفْرِدُ الْحَجَّ فَيَطُوفُ"
- Mursal opening: al-Ṣadūq → اسحاق بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 70 · `faqih-2548`
- **Location:** vol. 2, p. 315 · seq 2556 · chain 1
- **Flags:** `citation_noise`
- **Full report (Arabic):**
  > 2553- وَ رَوَى الْحَلَبِيُّ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ قَالَ ابْنُ عَبَّاسٍ‌ دَخَلَتِ الْعُمْرَةُ فِي الْحَجِّ إِلَى يَوْمِ الْقِيَامَةِ.
- **Isnad as currently extracted:**
  > 2553- وَ رَوَى الْحَلَبِيُّ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحلبی | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 70 · `faqih-2548` — CLARIFIED
- Transmitters (student → teacher): الحلبي → أبو عبد الله ع
- Corrected isnad (Arabic): «2553- وَ رَوَى الْحَلَبِيُّ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ»
- Isnad ends / matn begins at: "قَالَ ابْنُ عَبَّاسٍ‌ دَخَلَتِ الْعُمْرَةُ فِي الْحَجِّ إِلَى يَوْمِ"
- Mursal opening: al-Ṣadūq → الحلبي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. Numeric/citation material is not part of the isnād.

---

### Chain 71 · `faqih-2550`
- **Location:** vol. 2, p. 317 · seq 2558 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى دُرُسْتُ‌[1] عَنْ مُحَمَّدِ بْنِ الْفَضْلِ الْهَاشِمِيِّ قَالَ‌ دَخَلْتُ مَعَ إِخْوَانِي عَلَى أَبِي عَبْدِ اللَّهِ ع فَقُلْنَا لَهُ إِنَّا نُرِيدُ الْحَجَّ وَ بَعْضُنَا صَرُورَةٌ فَقَالَ ع عَلَيْكُمْ بِالتَّمَتُّعِ فَإِنَّا لَا نَتَّقِي أَحَداً فِي التَّمَتُّعِ‌ بِالْعُمْرَةِ إِلَى الْحَجِ‌ وَ اجْتِنَابِ الْمُسْكِرِ وَ الْمَسْحِ عَلَى الْخُفَّيْنِ.
- **Isnad as currently extracted:**
  > وَ رَوَى دُرُسْتُ‌[1] عَنْ مُحَمَّدِ بْنِ الْفَضْلِ الْهَاشِمِيِّ قَالَ‌ دَخَلْتُ مَعَ إِخْوَانِي عَلَى أَبِي عَبْدِ اللَّهِ ع فَقُلْنَا لَهُ إِنَّا نُرِيدُ الْحَجَّ وَ بَعْضُنَا صَرُورَةٌ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | درست | روی |  |
  | 1 | named_narrator | محمد بن الفضل الهاشمی | عن |  |

### Chain 71 · `faqih-2550` — CLARIFIED
- Transmitters (student → teacher): درست → محمد بن الفضل الهاشمي → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى دُرُسْتُ‌[1] عَنْ مُحَمَّدِ بْنِ الْفَضْلِ الْهَاشِمِيِّ قَالَ‌»
- Isnad ends / matn begins at: "دَخَلْتُ مَعَ إِخْوَانِي عَلَى أَبِي عَبْدِ اللَّهِ ع فَقُلْنَا"
- Mursal opening: al-Ṣadūq → درست; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 72 · `faqih-2555`
- **Location:** vol. 2, p. 319 · seq 2563 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى ابْنُ أَبِي عُمَيْرٍ عَنْ حَمَّادِ بْنِ عُثْمَانَ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنِّي أُرِيدُ أَنْ أَتَمَتَّعَ‌ بِالْعُمْرَةِ إِلَى الْحَجِ‌ فَكَيْفَ أَقُولُ فَقَالَ تَقُولُ اللَّهُمَ‌
إِنِّي أُرِيدُ التَّمَتُّعَ‌ بِالْعُمْرَةِ إِلَى الْحَجِ‌ عَلَى كِتَابِكَ وَ سُنَّةِ نَبِيِّكَ وَ إِنْ شِئْتَ أَضْمَرْتَ الَّذِي تُرِيدُ.
- **Isnad as currently extracted:**
  > وَ رَوَى ابْنُ أَبِي عُمَيْرٍ عَنْ حَمَّادِ بْنِ عُثْمَانَ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن ابی عمیر | روی |  |
  | 1 | named_narrator | حماد بن عثمان | عن |  |

### Chain 72 · `faqih-2555` — CLARIFIED
- Transmitters (student → teacher): ابن ابي عمير → حماد بن عثمان
- Corrected isnad (Arabic): «وَ رَوَى ابْنُ أَبِي عُمَيْرٍ عَنْ حَمَّادِ بْنِ عُثْمَانَ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنِّي أُرِيدُ أَنْ أَتَمَتَّعَ‌"
- Mursal opening: al-Ṣadūq → ابن ابي عمير; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 73 · `faqih-2557`
- **Location:** vol. 2, p. 320 · seq 2565 · chain 1
- **Flags:** `multi_route`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى حَفْصُ بْنُ الْبَخْتَرِيِّ وَ مُعَاوِيَةُ بْنُ عَمَّارٍ وَ عَبْدُ الرَّحْمَنِ بْنُ الْحَجَّاجِ وَ الْحَلَبِيُّ جَمِيعاً عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ إِذَا صَلَّيْتَ فِي مَسْجِدِ الشَّجَرَةِ فَقُلْ وَ أَنْتَ قَاعِدٌ فِي دُبُرِ الصَّلَاةِ قَبْلَ أَنْ تَقُومَ مَا يَقُولُ الْمُحْرِمُ ثُمَّ قُمْ فَامْشِ حَتَّى تَبْلُغَ الْمِيلَ وَ تَسْتَوِيَ بِكَ الْبَيْدَاءُ فَإِذَا اسْتَوَتْ بِكَ الْبَيْدَاءُ فَلَبِ‌[2].
وَ إِنْ أَهْلَلْتَ‌[3] مِنَ الْمَسْجِدِ الْحَرَامِ لِلْحَجِّ فَإِنْ شِئْتَ لَبَّيْتَ خَلْفَ الْمَقَامِ وَ أَفْضَلُ ذَلِكَ أَنْ تَمْضِيَ حَتَّى تَأْتِيَ الرَّقْطَاءَ[4] وَ تُلَبِّيَ قَبْلَ أَنْ تَصِيرَ إِلَى الْأَبْطَحِ‌[5].
- **Isnad as currently extracted:**
  > وَ رَوَى حَفْصُ بْنُ اَلْبَخْتَرِيِّ وَ مُعَاوِيَةُ بْنُ عَمَّارٍ وَ عَبْدُ اَلرَّحْمَنِ بْنُ اَلْحَجَّاجِ وَ اَلْحَلَبِيُّ جَمِيعاً عَنْ أَبِي عَبْدِ اَللَّهِ عَلَيْهِ اَلسَّلاَمُ قَالَ :
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حفص بن البختری و معاویة بن عمار و عبد الرحمن بن الحجاج و الحلبی | روی |  |
  | 1 | imam | ابی عبد الله علیه السلام | عن |  |

### Chain 73 · `faqih-2557` — CLARIFIED
- Transmitters (student → teacher): حفص بن البختري + معاوية بن عمار + عبد الرحمن بن الحجاج + الحلبي → أبو عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى حَفْصُ بْنُ الْبَخْتَرِيِّ وَ مُعَاوِيَةُ بْنُ عَمَّارٍ وَ عَبْدُ الرَّحْمَنِ بْنُ الْحَجَّاجِ وَ الْحَلَبِيُّ جَمِيعاً عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "إِذَا صَلَّيْتَ فِي مَسْجِدِ الشَّجَرَةِ فَقُلْ وَ أَنْتَ قَاعِدٌ"
- Mursal opening: al-Ṣadūq → [حفص بن البختري + معاوية بن عمار + عبد الرحمن بن الحجاج + الحلبي]; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: This is one clear co-narrator bundle: all four narrators transmit jointly from Abū ʿAbd Allāh. The automatic `multi_route` concern was a false positive; there is no uncertain attachment point.
---

### Chain 74 · `faqih-2558`
- **Location:** vol. 2, p. 321 · seq 2566 · chain 1
- **Flags:** `matn_spill`
- **Full report (Arabic):**
  > وَ فِي رِوَايَةِ هِشَامِ بْنِ الْحَكَمِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ إِذَا أَحْرَمْتَ مِنْ غَمْرَةَ[1] أَوْ بَرِيدِ الْبَعْثِ صَلَّيْتَ وَ قُلْتَ مَا يَقُولُ الْمُحْرِمُ فِي دُبُرِ صَلَاتِكَ وَ إِنْ شِئْتَ لَبَّيْتَ مِنْ مَوْضِعِكَ وَ الْفَضْلُ أَنْ تَمْشِيَ قَلِيلًا ثُمَّ تُلَبِّيَ‌[2].
- **Isnad as currently extracted:**
  > وَ فِي رِوَايَةِ هِشَامِ بْنِ الْحَكَمِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ إِذَا أَحْرَمْتَ مِنْ غَمْرَةَ[1] أَوْ بَرِيدِ الْبَعْثِ صَلَّيْتَ وَ قُلْتَ مَا يَقُولُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | فی روایة هشام بن الحکم |  |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 74 · `faqih-2558` — CLARIFIED
- Transmitters (student → teacher): هشام بن الحكم → ابي عبد الله ع
- Corrected isnad (Arabic): «وَ فِي رِوَايَةِ هِشَامِ بْنِ الْحَكَمِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "إِذَا أَحْرَمْتَ مِنْ غَمْرَةَ[1] أَوْ بَرِيدِ الْبَعْثِ صَلَّيْتَ وَ"
- Mursal opening: al-Ṣadūq → هشام بن الحكم; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 75 · `faqih-2568`
- **Location:** vol. 2, p. 324 · seq 2576 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ جَمِيلِ بْنِ صَالِحٍ عَنِ الْفُضَيْلِ بْنِ يَسَارٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ أَحْرَمَ مِنَ الْوَقْتِ‌[2] وَ مَضَى ثُمَّ إِنَّهُ اشْتَرَى بَدَنَةً بَعْدَ ذَلِكَ بِيَوْمٍ أَوْ يَوْمَيْنِ فَأَشْعَرَهَا وَ قَلَّدَهَا وَ سَاقَهَا فَقَالَ إِنْ كَانَ ابْتَاعَهَا قَبْلَ أَنْ يَدْخُلَ الْحَرَمَ فَلَا بَأْسَ قُلْتُ فَإِنَّهُ اشْتَرَاهَا قَبْلَ أَنْ يَنْتَهِيَ إِلَى الْوَقْتِ الَّذِي يُحْرِمُ مِنْهُ فَأَشْعَرَهَا وَ قَلَّدَهَا أَ يَجِبُ عَلَيْهِ حِينَ فَعَلَ ذَلِكَ مَا يَجِبُ عَلَى الْمُحْرِمِ قَالَ لَا وَ لَكِنْ إِذَا انْتَهَى إِلَى الْوَقْتِ فَلْيُحْرِمْ ثُمَّ يُشْعِرُهَا وَ يُقَلِّدُهَا فَإِنَّ تَقْلِيدَهُ الْأَوَّلَ لَيْسَ بِشَيْ‌ءٍ[3].
- **Isnad as currently extracted:**
  > وَ رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ جَمِيلِ بْنِ صَالِحٍ عَنِ الْفُضَيْلِ بْنِ يَسَارٍ قَالَ‌ قُلْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | جمیل بن صالح | عن |  |
  | 2 | named_narrator | الفضیل بن یسار | عن |  |

### Chain 75 · `faqih-2568` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → جميل بن صالح → الفضيل بن يسار → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ جَمِيلِ بْنِ صَالِحٍ عَنِ الْفُضَيْلِ بْنِ يَسَارٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ أَحْرَمَ مِنَ الْوَقْتِ‌[2]"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 76 · `faqih-2569`
- **Location:** vol. 2, p. 324 · seq 2577 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الصَّبَّاحِ الْكِنَانِيِّ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الْبُدْنِ كَيْفَ تُشْعَرُ فَقَالَ تُشْعَرُ وَ هِيَ بَارِكَةٌ مِنْ شَقِّ سَنَامِهَا الْأَيْمَنِ وَ تُنْحَرُ وَ هِيَ قَائِمَةٌ مِنْ قِبَلِ الْأَيْمَنِ.
- **Isnad as currently extracted:**
  > وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الصَّبَّاحِ الْكِنَانِيِّ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن الفضیل | روی |  |
  | 1 | named_narrator | ابی الصباح الکنانی | عن |  |

### Chain 76 · `faqih-2569` — CLARIFIED
- Transmitters (student → teacher): محمد بن الفضيل → ابي الصباح الكناني → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الصَّبَّاحِ الْكِنَانِيِّ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الْبُدْنِ كَيْفَ تُشْعَرُ"
- Mursal opening: al-Ṣadūq → محمد بن الفضيل; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 77 · `faqih-2582`
- **Location:** vol. 2, p. 328 · seq 2590 · chain 1
- **Flags:** `multi_route`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ وَ الْحَلَبِيُّ جَمِيعاً عَنْ أَبِي عَبْدِ اللَّهِ ع‌ فِي قَوْلِ اللَّهِ عَزَّ وَ جَلَ‌ الْحَجُ‌ أَشْهُرٌ مَعْلُوماتٌ فَمَنْ فَرَضَ فِيهِنَّ الْحَجَّ فَلا رَفَثَ‌ وَ لا فُسُوقَ وَ لا جِدالَ فِي الْحَجِ‌[2] فَقَالَ إِنَّ اللَّهَ عَزَّ وَ جَلَّ اشْتَرَطَ عَلَى النَّاسِ شَرْطاً وَ شَرَطَ لَهُمْ شَرْطاً فَمَنْ وَفَى لَهُ وَفَى اللَّهُ لَهُ فَقَالا لَهُ فَمَا الَّذِي اشْتَرَطَ عَلَيْهِمْ وَ مَا الَّذِي شَرَطَ لَهُمْ فَقَالَ أَمَّا الَّذِي اشْتَرَطَ عَلَيْهِمْ فَإِنَّهُ قَالَ‌ الْحَجُّ أَشْهُرٌ مَعْلُوماتٌ فَمَنْ فَرَضَ فِيهِنَّ الْحَجَّ فَلا رَفَثَ وَ لا فُسُوقَ وَ لا جِدالَ فِي الْحَجِ‌ وَ أَمَّا مَا شَرَطَ لَهُمْ فَإِنَّهُ قَالَ- فَمَنْ تَعَجَّلَ فِي يَوْمَيْنِ‌ فَلا إِثْمَ عَلَيْهِ‌ وَ مَنْ تَأَخَّرَ فَلا إِثْمَ عَلَيْهِ لِمَنِ اتَّقى‌ قَالَ يَرْجِعُ وَ لَا ذَنْبَ لَهُ فَقَالا لَهُ أَ رَأَيْتَ مَنِ ابْتُلِيَ بِالْفُسُوقِ مَا عَلَيْهِ فَقَالَ لَمْ يَجْعَلِ اللَّهُ عَزَّ وَ جَلَّ لَهُ حَدّاً يَسْتَغْفِرُ اللَّهَ وَ يُلَبِّي فَقَالا لَهُ فَمَنِ ابْتُلِيَ بِالْجِدَالِ مَا عَلَيْهِ فَقَالَ إِذَا جَادَلَ فَوْقَ مَرَّتَيْنِ فَعَلَى الْمُصِيبِ دَمٌ يُهَرِيقُهُ شَاةٌ وَ عَلَى الْمُخْطِئِ بَقَرَةٌ[3].
وَ قَالَ أَبِي رَضِيَ اللَّهُ عَنْهُ فِي رِسَالَتِهِ إِلَيَ‌[4] اتَّقِ فِي إِحْرَامِكَ الْكَذِبَ‌
وَ الْيَمِينَ الْكَاذِبَةَ وَ الصَّادِقَةَ وَ هُوَ الْجِدَالُ وَ الْجِدَالُ قَوْلُ الرَّجُلِ لَا وَ اللَّهِ وَ بَلَى وَ اللَّهِ فَإِنْ جَادَلْتَ مَرَّةً أَوْ مَرَّتَيْنِ وَ أَنْتَ صَادِقٌ فَلَا شَيْ‌ءَ عَلَيْكَ فَإِنْ جَادَلْتَ ثَلَاثاً وَ أَنْتَ صَادِقٌ فَعَلَيْكَ دَمُ شَاةٍ فَإِنْ جَادَلْتَ مَرَّةً كَاذِباً فَعَلَيْكَ دَمُ شَاةٍ وَ إِنْ جَادَلْتَ مَرَّتَيْنِ كَاذِباً فَعَلَيْكَ دَمُ بَقَرَةٍ وَ إِنْ جَادَلْتَ كَاذِباً ثَلَاثاً فَعَلَيْكَ بَدَنَةٌ وَ الْفُسُوقُ الْكَذِبُ فَاسْتَغْفِرِ اللَّهَ مِنْهُ وَ الرَّفَثُ الْجِمَاعُ فَإِنْ جَامَعْتَ وَ أَنْتَ مُحْرِمٌ فِي الْفَرْجِ فَعَلَيْكَ بَدَنَةٌ[1] وَ الْحَجُّ مِنْ قَابِلٍ وَ يَجِبُ أَنْ يُفَرَّقَ بَيْنَكَ وَ بَيْنَ أَهْلِكَ حَتَّى تَقْضِيَا الْمَنَاسِكَ ثُمَّ تَجْتَمِعَانِ فَإِنْ أَخَذْتُمَا عَلَى طَرِيقٍ غ …[truncated]
- **Isnad as currently extracted:**
  > رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ وَ اَلْحَلَبِيُّ جَمِيعاً عَنْ أَبِي عَبْدِ اَللَّهِ عَلَيْهِ اَلسَّلاَمُ :
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن مسلم و الحلبی | روی |  |
  | 1 | imam | ابی عبد الله علیه السلام | عن |  |

### Chain 77 · `faqih-2582` — CLARIFIED
- Transmitters (student → teacher): محمد بن مسلم + الحلبي → أبو عبد الله ع
- Corrected isnad (Arabic): «رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ وَ الْحَلَبِيُّ جَمِيعاً عَنْ أَبِي عَبْدِ اللَّهِ ع‌»
- Isnad ends / matn begins at: "فِي قَوْلِ اللَّهِ عَزَّ وَ جَلَ‌ الْحَجُ‌ أَشْهُرٌ مَعْلُوماتٌ"
- Mursal opening: al-Ṣadūq → [محمد بن مسلم + الحلبي]; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The word «جميعاً» makes the structure explicit: Muḥammad b. Muslim and al-Ḥalabī are co-narrators from Abū ʿAbd Allāh. No unresolved fork remains.
---

### Chain 78 · `faqih-2587`
- **Location:** vol. 2, p. 333 · seq 2595 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى ابْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الْمُحْرِمِ يُرِيدُ أَنْ يَعْمَلَ الْعَمَلَ فَيَقُولُ لَهُ أَصْحَابُهُ وَ اللَّهِ لَا تَعْمَلْهُ‌[3] فَيَقُولُ وَ اللَّهِ لَأَعْمَلَنَّهُ فَيُحَالِفُهُ مِرَاراً فَيَلْزَمُهُ مَا يَلْزَمُ صَاحِبَ الْجِدَالِ فَقَالَ لَا إِنَّمَا أَرَادَ بِهَذَا إِكْرَامَ أَخِيهِ إِنَّمَا يَلْزَمُهُ مَا كَانَ لِلَّهِ عَزَّ وَ جَلَّ مَعْصِيَةً.
- **Isnad as currently extracted:**
  > وَ رَوَى ابْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن مسکان | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |

### Chain 78 · `faqih-2587` — CLARIFIED
- Transmitters (student → teacher): ابن مسكان → ابي بصير → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى ابْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الْمُحْرِمِ يُرِيدُ أَنْ"
- Mursal opening: al-Ṣadūq → ابن مسكان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 79 · `faqih-2597`
- **Location:** vol. 2, p. 336 · seq 2605 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنِ الْحُسَيْنِ بْنِ الْمُخْتَارِ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع أَ يُحْرِمُ الرَّجُلُ فِي الثَّوْبِ الْأَسْوَدِ قَالَ لَا يُحْرِمُ فِي الثَّوْبِ الْأَسْوَدِ وَ لَا يُكَفَّنُ فِيهِ الْمَيِّتُ‌[1].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنِ الْحُسَيْنِ بْنِ الْمُخْتَارِ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن الحسین بن المختار | روی |  |

### Chain 79 · `faqih-2597` — CLARIFIED
- Transmitters (student → teacher): الحسين بن المختار → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنِ الْحُسَيْنِ بْنِ الْمُخْتَارِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع أَ يُحْرِمُ الرَّجُلُ فِي"
- Mursal opening: al-Ṣadūq → الحسين بن المختار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 80 · `faqih-2599`
- **Location:** vol. 2, p. 336 · seq 2607 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنِ الْحَلَبِيِّ قَالَ‌ سَأَلْتُهُ عَنْ الرَّجُلِ يُحْرِمُ فِي ثَوْبٍ لَهُ عَلَمٌ فَقَالَ لَا بَأْسَ بِهِ‌[3].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنِ الْحَلَبِيِّ قَالَ‌ سَأَلْتُهُ عَنْ الرَّجُلِ يُحْرِمُ فِي ثَوْبٍ لَهُ عَلَمٌ فَقَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن الحلبی | روی |  |

### Chain 80 · `faqih-2599` — CLARIFIED
- Transmitters (student → teacher): الحلبي → أبو عبد الله ع
- Corrected isnad (Arabic): «وَ رُوِيَ عَنِ الْحَلَبِيِّ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ الرَّجُلِ يُحْرِمُ فِي ثَوْبٍ لَهُ عَلَمٌ فَقَالَ"
- Mursal opening: al-Ṣadūq → الحلبي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The parallel explicitly expands the pronoun as «سَأَلَ أَبَا عَبْدِ اللَّهِ عَنْ الرَّجُلِ يُحْرِمُ فِي ثَوْبٍ لَهُ عَلَمٌ». Source: [Wasāʾil al-Shīʿa, vol. 12](https://alkafeel.net/islamiclibrary/hadith/wasael-12/wasael-12/v19.html).
---

### Chain 81 · `faqih-2604`
- **Location:** vol. 2, p. 337 · seq 2612 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنِ الْكَاهِلِيِّ قَالَ‌ سَأَلَهُ رَجُلٌ وَ أَنَا حَاضِرٌ عَنِ الثَّوْبِ يَكُونُ مَصْبُوغاً بِالْعُصْفُرِ[3] ثُمَّ يُغْسَلُ أَلْبَسُهُ وَ أَنَا مُحْرِمٌ فَقَالَ نَعَمْ لَيْسَ الْعُصْفُرُ مِنَ الطِّيبِ وَ لَكِنِّي أَكْرَهُ أَنْ تَلْبَسَ مَا يَشْهَرُكَ بِهِ النَّاسُ.
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنِ الْكَاهِلِيِّ قَالَ‌ سَأَلَهُ رَجُلٌ وَ أَنَا حَاضِرٌ عَنِ الثَّوْبِ يَكُونُ مَصْبُوغاً بِالْعُصْفُرِ[3] ثُمَّ يُغْسَلُ أَلْبَسُهُ وَ أَنَا مُحْرِمٌ فَقَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن الکاهلی | روی |  |

### Chain 81 · `faqih-2604` — CLARIFIED
- Transmitters (student → teacher): الكاهلي
- Corrected isnad (Arabic): «وَ رُوِيَ عَنِ الْكَاهِلِيِّ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلَهُ رَجُلٌ وَ أَنَا حَاضِرٌ عَنِ الثَّوْبِ يَكُونُ مَصْبُوغاً"
- Mursal opening: al-Ṣadūq → الكاهلي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 82 · `faqih-2604`
- **Location:** vol. 2, p. 337 · seq 2612 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنِ الْكَاهِلِيِّ قَالَ‌ سَأَلَهُ رَجُلٌ وَ أَنَا حَاضِرٌ عَنِ الثَّوْبِ يَكُونُ مَصْبُوغاً بِالْعُصْفُرِ[3] ثُمَّ يُغْسَلُ أَلْبَسُهُ وَ أَنَا مُحْرِمٌ فَقَالَ نَعَمْ لَيْسَ الْعُصْفُرُ مِنَ الطِّيبِ وَ لَكِنِّي أَكْرَهُ أَنْ تَلْبَسَ مَا يَشْهَرُكَ بِهِ النَّاسُ.
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنِ الْكَاهِلِيِّ قَالَ‌ سَأَلَهُ رَجُلٌ وَ أَنَا حَاضِرٌ عَنِ الثَّوْبِ يَكُونُ مَصْبُوغاً بِالْعُصْفُرِ[3] ثُمَّ يُغْسَلُ أَلْبَسُهُ وَ أَنَا مُحْرِمٌ فَقَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن الکاهلی | روی |  |

### Chain 82 · `faqih-2604` — CLARIFIED
- Transmitters (student → teacher): الكاهلي
- Corrected isnad (Arabic): «وَ رُوِيَ عَنِ الْكَاهِلِيِّ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلَهُ رَجُلٌ وَ أَنَا حَاضِرٌ عَنِ الثَّوْبِ يَكُونُ مَصْبُوغاً"
- Mursal opening: al-Ṣadūq → الكاهلي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 83 · `faqih-2613`
- **Location:** vol. 2, p. 341 · seq 2621 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى زُرَارَةُ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَمَّا يُكْرَهُ لِلْمُحْرِمِ أَنْ يَلْبَسَهُ فَقَالَ يَلْبَسُ كُلَّ ثَوْبٍ إِلَّا ثَوْباً وَاحِداً يَتَدَرَّعُهُ.
- **Isnad as currently extracted:**
  > وَ رَوَى زُرَارَةُ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَمَّا يُكْرَهُ لِلْمُحْرِمِ أَنْ يَلْبَسَهُ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | زرارة | روی |  |
  | 1 | imam | احدهما ع | عن | ambiguous |

### Chain 83 · `faqih-2613` — CLARIFIED
- Transmitters (student → teacher): زرارة → احدهما ع
- Corrected isnad (Arabic): «وَ رَوَى زُرَارَةُ عَنْ أَحَدِهِمَا ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَمَّا يُكْرَهُ لِلْمُحْرِمِ أَنْ يَلْبَسَهُ فَقَالَ يَلْبَسُ كُلَّ"
- Mursal opening: al-Ṣadūq → زرارة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 84 · `faqih-2618`
- **Location:** vol. 2, p. 341 · seq 2626 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ‌[4] عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنِ الْمُحْرِمِ إِذَا احْتَاجَ إِلَى ضُرُوبٍ مِنَ الثِّيَابِ مُخْتَلِفَةٍ فَقَالَ ع عَلَيْهِ لِكُلِّ صِنْفٍ مِنْهَا فِدَاءٌ[5].
- **Isnad as currently extracted:**
  > وَ رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ‌[4] عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنِ الْمُحْرِمِ إِذَا احْتَاجَ إِلَى ضُرُوبٍ مِنَ الثِّيَابِ مُخْتَلِفَةٍ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن مسلم | روی |  |
  | 1 | imam | احدهما ع | عن | ambiguous |

### Chain 84 · `faqih-2618` — CLARIFIED
- Transmitters (student → teacher): محمد بن مسلم → احدهما ع
- Corrected isnad (Arabic): «وَ رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ‌[4] عَنْ أَحَدِهِمَا ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْمُحْرِمِ إِذَا احْتَاجَ إِلَى ضُرُوبٍ مِنَ الثِّيَابِ"
- Mursal opening: al-Ṣadūq → محمد بن مسلم; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 85 · `faqih-2619`
- **Location:** vol. 2, p. 341 · seq 2627 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنِ الْمُحْرِمِ تُصِيبُ ثَوْبَهُ الْجَنَابَةُ قَالَ لَا يَلْبَسْهُ حَتَّى يَغْسِلَهُ وَ إِحْرَامُهُ تَامٌ‌[6].
- **Isnad as currently extracted:**
  > وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنِ الْمُحْرِمِ تُصِيبُ ثَوْبَهُ الْجَنَابَةُ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن عمار | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 85 · `faqih-2619` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار → ابي عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْمُحْرِمِ تُصِيبُ ثَوْبَهُ الْجَنَابَةُ قَالَ لَا يَلْبَسْهُ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 86 · `faqih-2640`
- **Location:** vol. 2, p. 346 · seq 2648 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى ابْنُ فَضَّالٍ عَنْ يُونُسَ بْنِ يَعْقُوبَ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع عَنِ الرَّجُلِ الْمُحْرِمِ يَشُدُّ الْهِمْيَانَ فِي وَسَطِهِ‌[4] فَقَالَ نَعَمْ وَ مَا خَيْرُهُ بَعْدَ نَفَقَتِهِ‌[5].
- **Isnad as currently extracted:**
  > وَ رَوَى ابْنُ فَضَّالٍ عَنْ يُونُسَ بْنِ يَعْقُوبَ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن فضال | روی |  |
  | 1 | named_narrator | یونس بن یعقوب | عن |  |

### Chain 86 · `faqih-2640` — CLARIFIED
- Transmitters (student → teacher): ابن فضال → يونس بن يعقوب → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى ابْنُ فَضَّالٍ عَنْ يُونُسَ بْنِ يَعْقُوبَ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع عَنِ الرَّجُلِ الْمُحْرِمِ يَشُدُّ"
- Mursal opening: al-Ṣadūq → ابن فضال; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 87 · `faqih-2645`
- **Location:** vol. 2, p. 347 · seq 2653 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع فِي الْمُحْرِمِ يَسْتَاكُ قَالَ نَعَمْ قَالَ قُلْتُ فَإِنْ أَدْمَى يَسْتَاكُ‌[4] قَالَ نَعَمْ هُوَ مِنَ السُّنَّةِ.
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن معاویة بن عمار | روی |  |

### Chain 87 · `faqih-2645` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع فِي الْمُحْرِمِ يَسْتَاكُ قَالَ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 88 · `faqih-2654`
- **Location:** vol. 2, p. 349 · seq 2662 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الصَّبَّاحِ الْكِنَانِيِّ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ امْرَأَةٍ أَرَادَتْ أَنْ تُحْرِمَ فَتَخَوَّفَتِ الشُّقَاقَ‌[4] تَخْضِبُ بِالْحِنَّاءِ قَبْلَ ذَلِكَ‌
قَالَ مَا يُعْجِبُنِي أَنْ تَفْعَلَ‌[1].
الطِّيبُ لِلْمُحْرِمِ‌
- **Isnad as currently extracted:**
  > وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الصَّبَّاحِ الْكِنَانِيِّ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن الفضیل | روی |  |
  | 1 | named_narrator | ابی الصباح الکنانی | عن |  |

### Chain 88 · `faqih-2654` — CLARIFIED
- Transmitters (student → teacher): محمد بن الفضيل → ابي الصباح الكناني → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الصَّبَّاحِ الْكِنَانِيِّ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ امْرَأَةٍ أَرَادَتْ أَنْ"
- Mursal opening: al-Ṣadūq → محمد بن الفضيل; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 89 · `faqih-2657`
- **Location:** vol. 2, p. 350 · seq 2665 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنِ الْحَسَنِ بْنِ هَارُونَ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع أَكَلْتُ خَبِيصاً فِيهِ زَعْفَرَانٌ‌[6] حَتَّى شَبِعْتُ مِنْهُ وَ أَنَا مُحْرِمٌ فَقَالَ إِذَا فَرَغْتَ مِنْ مَنَاسِكِكَ وَ أَرَدْتَ الْخُرُوجَ مِنْ مَكَّةَ فَابْتَعْ بِدِرْهَمٍ تَمْراً وَ تَصَدَّقْ بِهِ‌[7] فَيَكُونَ كَفَّارَةً لِذَلِكَ وَ لِمَا دَخَلَ عَلَيْكَ فِي إِحْرَامِكَ مِمَّا لَا تَعْلَمُ.
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنِ الْحَسَنِ بْنِ هَارُونَ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن الحسن بن هارون | روی |  |

### Chain 89 · `faqih-2657` — CLARIFIED
- Transmitters (student → teacher): الحسن بن هارون → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنِ الْحَسَنِ بْنِ هَارُونَ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع أَكَلْتُ خَبِيصاً فِيهِ زَعْفَرَانٌ‌[6]"
- Mursal opening: al-Ṣadūq → الحسن بن هارون; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 90 · `faqih-2659`
- **Location:** vol. 2, p. 350 · seq 2667 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنِ الْحَسَنِ بْنِ زِيَادٍ[8] قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع وَضَّأَنِي‌
الْغُلَامُ وَ أَنَا لَا أَعْلَمُ بدستشان‌[1] فِيهِ طِيبٌ فَغَسَلْتُ يَدَيَّ وَ أَنَا مُحْرِمٌ فَقَالَ تَصَدَّقْ بِشَيْ‌ءٍ لِذَلِكَ‌[2].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنِ الْحَسَنِ بْنِ زِيَادٍ[8] قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن الحسن بن زیاد | روی |  |

### Chain 90 · `faqih-2659` — CLARIFIED
- Transmitters (student → teacher): الحسن بن زياد → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنِ الْحَسَنِ بْنِ زِيَادٍ[8] قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع وَضَّأَنِي‌ الْغُلَامُ وَ أَنَا"
- Mursal opening: al-Ṣadūq → الحسن بن زياد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 91 · `faqih-2661`
- **Location:** vol. 2, p. 351 · seq 2669 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ مَسَّ الطِّيبَ نَاسِياً وَ هُوَ مُحْرِمٌ قَالَ يَغْسِلُ يَدَيْهِ وَ يُلَبِّي وَ لَيْسَ عَلَيْهِ شَيْ‌ءٌ.
- وَ فِي خَبَرٍ آخَرَ وَ يَسْتَغْفِرُ رَبَّهُ‌[4].
- **Isnad as currently extracted:**
  > وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ مَسَّ الطِّيبَ نَاسِياً وَ هُوَ مُحْرِمٌ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن عمار | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 91 · `faqih-2661` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار → ابي عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ مَسَّ الطِّيبَ نَاسِياً وَ هُوَ مُحْرِمٌ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 92 · `faqih-2661`
- **Location:** vol. 2, p. 351 · seq 2669 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ مَسَّ الطِّيبَ نَاسِياً وَ هُوَ مُحْرِمٌ قَالَ يَغْسِلُ يَدَيْهِ وَ يُلَبِّي وَ لَيْسَ عَلَيْهِ شَيْ‌ءٌ.
- وَ فِي خَبَرٍ آخَرَ وَ يَسْتَغْفِرُ رَبَّهُ‌[4].
- **Isnad as currently extracted:**
  > وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ مَسَّ الطِّيبَ نَاسِياً وَ هُوَ مُحْرِمٌ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن عمار | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 92 · `faqih-2661` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار → ابي عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ مَسَّ الطِّيبَ نَاسِياً وَ هُوَ مُحْرِمٌ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 93 · `faqih-2667`
- **Location:** vol. 2, p. 352 · seq 2675 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌ لَا بَأْسَ أَنْ تَشَمَّ الْإِذْخِرَ وَ الْقَيْصُومَ وَ الْخُزَامَى وَ الشِّيحَ‌[2] وَ أَشْبَاهَهُ وَ أَنْتَ مُحْرِمٌ.
وَ رَوَى عَلِيُّ بْنُ مَهْزِيَارَ قَالَ: سَأَلْتُ ابْنَ أَبِي عُمَيْرٍ عَنِ التُّفَّاحِ وَ الْأُتْرُجِّ وَ النَّبِقِ وَ مَا طَابَ مِنْ رِيحِهِ فَقَالَ تُمْسِكُ عَنْ شَمِّهِ وَ أَكْلِهِ‌[3] وَ لَمْ يَرْوِ فِيهِ شَيْئاً.
الظِّلَالُ لِلْمُحْرِمِ‌
- **Isnad as currently extracted:**
  > وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌ لَا بَأْسَ أَنْ تَشَمَّ الْإِذْخِرَ وَ الْقَيْصُومَ وَ الْخُزَامَى وَ الشِّيحَ‌[2] وَ أَشْبَاهَهُ وَ أَنْتَ مُحْرِمٌ. وَ رَوَى عَلِيُّ بْنُ مَهْزِيَارَ قَالَ:
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن عمار | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 93 · `faqih-2667` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار → ابي عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌»
- Isnad ends / matn begins at: "لَا بَأْسَ أَنْ تَشَمَّ الْإِذْخِرَ وَ الْقَيْصُومَ وَ الْخُزَامَى"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 94 · `faqih-2668`
- **Location:** vol. 2, p. 352 · seq 2676 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ عَبْدِ اللَّهِ بْنِ الْمُغِيرَةِ قَالَ‌ قُلْتُ لِأَبِي الْحَسَنِ الْأَوَّلِ ع‌
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ عَبْدِ اللَّهِ بْنِ الْمُغِيرَةِ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن عبد الله بن المغیرة | روی |  |

### Chain 94 · `faqih-2668` — CLARIFIED
- Transmitters (student → teacher): عبد الله بن المغيرة → ابي الحسن الاول ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ عَبْدِ اللَّهِ بْنِ الْمُغِيرَةِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي الْحَسَنِ الْأَوَّلِ ع‌"
- Mursal opening: al-Ṣadūq → عبد الله بن المغيرة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 95 · `faqih-2671`
- **Location:** vol. 2, p. 354 · seq 2679 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى الْبَزَنْطِيُّ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُهُ عَنِ الْمَرْأَةِ تَضْرِبُ عَلَيْهَا الظِّلَالَ وَ هِيَ مُحْرِمَةٌ فَقَالَ نَعَمْ قُلْتُ فَالرَّجُلُ يَضْرِبُ عَلَيْهِ الظِّلَالَ وَ هُوَ مُحْرِمٌ قَالَ نَعَمْ إِذَا كَانَتْ بِهِ شَقِيقَةٌ[2] وَ يَتَصَدَّقُ بِمُدٍّ لِكُلِّ يَوْمٍ.
- **Isnad as currently extracted:**
  > وَ رَوَى الْبَزَنْطِيُّ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُهُ عَنِ الْمَرْأَةِ تَضْرِبُ عَلَيْهَا الظِّلَالَ وَ هِيَ مُحْرِمَةٌ فَقَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | البزنطی | روی |  |
  | 1 | named_narrator | علی بن ابی حمزة | عن |  |
  | 2 | named_narrator | ابی بصیر | عن |  |

### Chain 95 · `faqih-2671` — CLARIFIED
- Transmitters (student → teacher): البزنطي → علي بن ابي حمزة → ابي بصير
- Corrected isnad (Arabic): «وَ رَوَى الْبَزَنْطِيُّ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْمَرْأَةِ تَضْرِبُ عَلَيْهَا الظِّلَالَ وَ هِيَ مُحْرِمَةٌ"
- Mursal opening: al-Ṣadūq → البزنطي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 96 · `faqih-2671`
- **Location:** vol. 2, p. 354 · seq 2679 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى الْبَزَنْطِيُّ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُهُ عَنِ الْمَرْأَةِ تَضْرِبُ عَلَيْهَا الظِّلَالَ وَ هِيَ مُحْرِمَةٌ فَقَالَ نَعَمْ قُلْتُ فَالرَّجُلُ يَضْرِبُ عَلَيْهِ الظِّلَالَ وَ هُوَ مُحْرِمٌ قَالَ نَعَمْ إِذَا كَانَتْ بِهِ شَقِيقَةٌ[2] وَ يَتَصَدَّقُ بِمُدٍّ لِكُلِّ يَوْمٍ.
- **Isnad as currently extracted:**
  > وَ رَوَى الْبَزَنْطِيُّ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُهُ عَنِ الْمَرْأَةِ تَضْرِبُ عَلَيْهَا الظِّلَالَ وَ هِيَ مُحْرِمَةٌ فَقَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | البزنطی | روی |  |
  | 1 | named_narrator | علی بن ابی حمزة | عن |  |
  | 2 | named_narrator | ابی بصیر | عن |  |

### Chain 96 · `faqih-2671` — CLARIFIED
- Transmitters (student → teacher): البزنطي → علي بن ابي حمزة → ابي بصير
- Corrected isnad (Arabic): «وَ رَوَى الْبَزَنْطِيُّ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْمَرْأَةِ تَضْرِبُ عَلَيْهَا الظِّلَالَ وَ هِيَ مُحْرِمَةٌ"
- Mursal opening: al-Ṣadūq → البزنطي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 97 · `faqih-2676`
- **Location:** vol. 2, p. 355 · seq 2684 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`
- **Full report (Arabic):**
  > أَنَّ حَفْصَ بْنَ الْبَخْتَرِيِّ وَ هِشَامَ بْنَ الْحَكَمِ رَوَيَا عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌ يُكْرَهُ لِلْمُحْرِمِ أَنْ يَجُوزَ ثَوْبُهُ أَنْفَهُ مِنْ أَسْفَلَ وَ قَالَ اضْحَ لِمَنْ أَحْرَمْتَ لَهُ‌[2].
- **Isnad as currently extracted:**
  > أَنَّ حَفْصَ بْنَ الْبَخْتَرِيِّ وَ هِشَامَ بْنَ الْحَكَمِ رَوَيَا عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌ يُكْرَهُ لِلْمُحْرِمِ أَنْ يَجُوزَ ثَوْبُهُ أَنْفَهُ مِنْ أَسْفَلَ وَ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حفص بن البختری |  |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 97 · `faqih-2676` — CLARIFIED
- Transmitters (student → teacher): حفص بن البختري → ابي عبد الله ع
- Corrected isnad (Arabic): «أَنَّ حَفْصَ بْنَ الْبَخْتَرِيِّ وَ هِشَامَ بْنَ الْحَكَمِ رَوَيَا عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌»
- Isnad ends / matn begins at: "يُكْرَهُ لِلْمُحْرِمِ أَنْ يَجُوزَ ثَوْبُهُ أَنْفَهُ مِنْ أَسْفَلَ وَ"
- Mursal opening: al-Ṣadūq → حفص بن البختري; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim.

---

### Chain 98 · `faqih-2676`
- **Location:** vol. 2, p. 355 · seq 2684 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`
- **Full report (Arabic):**
  > أَنَّ حَفْصَ بْنَ الْبَخْتَرِيِّ وَ هِشَامَ بْنَ الْحَكَمِ رَوَيَا عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌ يُكْرَهُ لِلْمُحْرِمِ أَنْ يَجُوزَ ثَوْبُهُ أَنْفَهُ مِنْ أَسْفَلَ وَ قَالَ اضْحَ لِمَنْ أَحْرَمْتَ لَهُ‌[2].
- **Isnad as currently extracted:**
  > أَنَّ حَفْصَ بْنَ الْبَخْتَرِيِّ وَ هِشَامَ بْنَ الْحَكَمِ رَوَيَا عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌ يُكْرَهُ لِلْمُحْرِمِ أَنْ يَجُوزَ ثَوْبُهُ أَنْفَهُ مِنْ أَسْفَلَ وَ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | هشام بن الحکم رویا |  |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 98 · `faqih-2676` — CLARIFIED
- Transmitters (student → teacher): هشام بن الحكم رويا → ابي عبد الله ع
- Corrected isnad (Arabic): «أَنَّ حَفْصَ بْنَ الْبَخْتَرِيِّ وَ هِشَامَ بْنَ الْحَكَمِ رَوَيَا عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌»
- Isnad ends / matn begins at: "يُكْرَهُ لِلْمُحْرِمِ أَنْ يَجُوزَ ثَوْبُهُ أَنْفَهُ مِنْ أَسْفَلَ وَ"
- Mursal opening: al-Ṣadūq → هشام بن الحكم رويا; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim.

---

### Chain 99 · `faqih-2677`
- **Location:** vol. 2, p. 355 · seq 2685 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ عَبْدِ اللَّهِ بْنِ سِنَانٍ قَالَ‌ سَمِعْتُ أَبَا عَبْدِ اللَّهِ ع يَقُولُ لِأَبِي وَ شَكَا إِلَيْهِ حَرَّ الشَّمْسِ وَ هُوَ مُحْرِمٌ وَ هُوَ يَتَأَذَّى بِهِ وَ قَالَ تَرَى أَنْ أَسْتَتِرَ بِطَرَفِ ثَوْبِي قَالَ لَا بَأْسَ بِذَلِكَ مَا لَمْ يُصِبْ رَأْسَكَ‌[3].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ عَبْدِ اللَّهِ بْنِ سِنَانٍ قَالَ‌ سَمِعْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن عبد الله بن سنان | روی |  |

### Chain 99 · `faqih-2677` — CLARIFIED
- Transmitters (student → teacher): عبد الله بن سنان → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ عَبْدِ اللَّهِ بْنِ سِنَانٍ قَالَ‌»
- Isnad ends / matn begins at: "سَمِعْتُ أَبَا عَبْدِ اللَّهِ ع يَقُولُ لِأَبِي وَ شَكَا"
- Mursal opening: al-Ṣadūq → عبد الله بن سنان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 100 · `faqih-2684`
- **Location:** vol. 2, p. 356 · seq 2692 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ رِئَابٍ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ قَلَّمَ ظُفُراً مِنْ أَظَافِيرِهِ وَ هُوَ مُحْرِمٌ قَالَ عَلَيْهِ مُدٌّ مِنْ طَعَامٍ حَتَّى يَبْلُغَ عَشَرَةً فَإِنْ قَلَّمَ أَصَابِعَ يَدَيْهِ كُلَّهَا فَعَلَيْهِ دَمُ شَاةٍ قُلْتُ فَإِنْ قَلَّمَ أَظَافِيرَ يَدَيْهِ وَ رِجْلَيْهِ جَمِيعاً فَقَالَ إِنْ كَانَ فَعَلَ ذَلِكَ فِي مَجْلِسٍ وَاحِدٍ فَعَلَيْهِ دَمٌ وَ إِنْ كَانَ فَعَلَهُ مُتَفَرِّقاً فِي مَجْلِسَيْنِ فَعَلَيْهِ دَمَانِ‌[4].
- **Isnad as currently extracted:**
  > وَ رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ رِئَابٍ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | علی بن رئاب | عن |  |
  | 2 | named_narrator | ابی بصیر | عن |  |

### Chain 100 · `faqih-2684` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → علي بن رئاب → ابي بصير → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ رِئَابٍ عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ قَلَّمَ ظُفُراً"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 101 · `faqih-2700`
- **Location:** vol. 2, p. 360 · seq 2708 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى أَبَانٌ عَنْ زُرَارَةَ قَالَ‌ سَأَلْتُهُ عَنِ الْمُحْرِمِ هَلْ يَحُكُّ رَأْسَهُ أَوْ يَغْسِلُ بِالْمَاءِ فَقَالَ يَحُكُّ رَأْسَهُ مَا لَمْ يَتَعَمَّدْ قَتْلَ دَابَّةٍ وَ لَا بَأْسَ بِأَنْ يَغْتَسِلَ بِالْمَاءِ وَ يَصُبَّ عَلَى رَأْسَهُ مَا لَمْ يَكُنْ مُلَبِّداً فَإِنْ كَانَ مُلَبِّداً[3] فَلَا يُفِيضُ عَلَى رَأْسِهِ الْمَاءَ إِلَّا مِنِ احْتِلَامٍ.
- **Isnad as currently extracted:**
  > وَ رَوَى أَبَانٌ عَنْ زُرَارَةَ قَالَ‌ سَأَلْتُهُ عَنِ الْمُحْرِمِ هَلْ يَحُكُّ رَأْسَهُ أَوْ يَغْسِلُ بِالْمَاءِ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابان | روی |  |
  | 1 | named_narrator | زرارة | عن |  |

### Chain 101 · `faqih-2700` — CLARIFIED
- Transmitters (student → teacher): أبان → زرارة → أبو عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى أَبَانٌ عَنْ زُرَارَةَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْمُحْرِمِ هَلْ يَحُكُّ رَأْسَهُ أَوْ يَغْسِلُ بِالْمَاءِ"
- Mursal opening: al-Ṣadūq → أبان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The full parallel gives «أَبَان، عَنْ زُرَارَةَ قَالَ: سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع». Source: [Wasāʾil al-Shīʿa, vol. 12, report 17007](https://alkafeel.net/islamiclibrary/hadith/wasael-12/wasael-12/v21.html).
---

### Chain 102 · `faqih-2710`
- **Location:** vol. 2, p. 362 · seq 2718 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ مُحَمَّدٍ الْحَلَبِيِّ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الْمُحْرِمُ يَنْظُرُ إِلَى امْرَأَتِهِ وَ هِيَ مُحْرِمَةٌ قَالَ لَا بَأْسَ‌[5].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ مُحَمَّدٍ الْحَلَبِيِّ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن محمد الحلبی | روی |  |

### Chain 102 · `faqih-2710` — CLARIFIED
- Transmitters (student → teacher): محمد الحلبي → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ مُحَمَّدٍ الْحَلَبِيِّ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الْمُحْرِمُ يَنْظُرُ إِلَى امْرَأَتِهِ"
- Mursal opening: al-Ṣadūq → محمد الحلبي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 103 · `faqih-2711`
- **Location:** vol. 2, p. 363 · seq 2719 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ خَالِدٍ بَيَّاعِ الْقَلَانِسِ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ أَتَى أَهْلَهُ وَ عَلَيْهِ طَوَافُ النِّسَاءِ قَالَ عَلَيْهِ بَدَنَةٌ ثُمَّ جَاءَهُ آخَرُ فَسَأَلَهُ عَنْهَا فَقَالَ عَلَيْهِ بَقَرَةٌ ثُمَّ جَاءَهُ آخَرُ فَسَأَلَهُ عَنْهَا فَقَالَ عَلَيْهِ شَاةٌ فَقُلْتُ بَعْدَ مَا قَامُوا أَصْلَحَكَ اللَّهُ كَيْفَ قُلْتَ عَلَيْهِ بَدَنَةٌ فَقَالَ أَنْتَ مُوسِرٌ[1] وَ عَلَيْكَ بَدَنَةٌ وَ عَلَى الْوَسَطِ بَقَرَةٌ وَ عَلَى الْفَقِيرِ شَاةٌ[2].
مَا يَجُوزُ لِلْمُحْرِمِ قَتْلُهُ‌
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ خَالِدٍ بَيَّاعِ الْقَلَانِسِ قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن خالد بیاع القلانس | روی |  |

### Chain 103 · `faqih-2711` — CLARIFIED
- Transmitters (student → teacher): خالد بياع القلانس → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ خَالِدٍ بَيَّاعِ الْقَلَانِسِ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ أَتَى أَهْلَهُ"
- Mursal opening: al-Ṣadūq → خالد بياع القلانس; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 104 · `faqih-2716`
- **Location:** vol. 2, p. 364 · seq 2724 · chain 1
- **Flags:** `matn_spill`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ فِي رِوَايَةِ عَلِيِّ بْنِ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُهُ عَنِ الْمُحْرِمِ يَنْزِعُ الْحَلَمَةَ عَنِ الْبَعِيرِ فَقَالَ لَا هِيَ بِمَنْزِلَةِ الْقَمْلَةِ مِنْ جَسَدِكَ‌[3].
- **Isnad as currently extracted:**
  > وَ فِي رِوَايَةِ عَلِيِّ بْنِ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُهُ عَنِ الْمُحْرِمِ يَنْزِعُ الْحَلَمَةَ عَنِ الْبَعِيرِ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | فی روایة علی بن ابی حمزة |  |  |
  | 1 | named_narrator | ابی بصیر | عن |  |

### Chain 104 · `faqih-2716` — CLARIFIED
- Transmitters (student → teacher): علي بن أبي حمزة → أبو بصير → إمامٌ غير مصرّح باسمه في هذا الطريق (مضمرة أبي بصير)
- Corrected isnad (Arabic): «وَ فِي رِوَايَةِ عَلِيِّ بْنِ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْمُحْرِمِ يَنْزِعُ الْحَلَمَةَ عَنِ الْبَعِيرِ فَقَالَ لَا"
- Mursal opening: al-Ṣadūq → علي بن أبي حمزة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The exact report remains pronominal in the surviving parallel («سألته»), so the Imam’s personal name is not inserted without evidence. The structure itself is resolved as a muḍmar report: Abū Baṣīr asks an unnamed Imam. Source preserving the wording: [Wasāʾil al-Shīʿa, vol. 12, report 17030](https://alkafeel.net/islamiclibrary/hadith/wasael-12/wasael-12/v22.html).
---

### Chain 105 · `faqih-2717`
- **Location:** vol. 2, p. 364 · seq 2725 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ سَأَلْتُهُ عَنِ الْمُحْرِمِ وَ مَا يَقْتُلُ مِنَ الدَّوَابِّ قَالَ يَقْتُلُ الْأَسْوَدَ وَ الْأَفْعَى وَ الْفَأْرَةَ وَ الْعَقْرَبَ وَ كُلَّ حَيَّةٍ وَ إِنْ أَرَادَكَ السَّبُعُ فَاقْتُلْهُ وَ إِنْ لَمْ يُرِدْكَ فَلَا تَقْتُلْهُ وَ الْكَلْبُ الْعَقُورُ إِنْ أَرَادَكَ فَاقْتُلْهُ وَ لَا بَأْسَ لِلْمُحْرِمِ أَنْ يَرْمِيَ الْحِدَأَةَ وَ إِنْ عَرَضَ لَهُ اللُّصُوصُ امْتَنَعَ مِنْهُمْ‌[4].
- **Isnad as currently extracted:**
  > وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ سَأَلْتُهُ عَنِ الْمُحْرِمِ وَ مَا يَقْتُلُ مِنَ الدَّوَابِّ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن الفضیل | روی |  |
  | 1 | imam | ابی الحسن ع | عن |  |

### Chain 105 · `faqih-2717` — CLARIFIED
- Transmitters (student → teacher): محمد بن الفضيل → ابي الحسن ع
- Corrected isnad (Arabic): «وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الْحَسَنِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْمُحْرِمِ وَ مَا يَقْتُلُ مِنَ الدَّوَابِّ قَالَ"
- Mursal opening: al-Ṣadūq → محمد بن الفضيل; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 106 · `faqih-2717`
- **Location:** vol. 2, p. 364 · seq 2725 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ سَأَلْتُهُ عَنِ الْمُحْرِمِ وَ مَا يَقْتُلُ مِنَ الدَّوَابِّ قَالَ يَقْتُلُ الْأَسْوَدَ وَ الْأَفْعَى وَ الْفَأْرَةَ وَ الْعَقْرَبَ وَ كُلَّ حَيَّةٍ وَ إِنْ أَرَادَكَ السَّبُعُ فَاقْتُلْهُ وَ إِنْ لَمْ يُرِدْكَ فَلَا تَقْتُلْهُ وَ الْكَلْبُ الْعَقُورُ إِنْ أَرَادَكَ فَاقْتُلْهُ وَ لَا بَأْسَ لِلْمُحْرِمِ أَنْ يَرْمِيَ الْحِدَأَةَ وَ إِنْ عَرَضَ لَهُ اللُّصُوصُ امْتَنَعَ مِنْهُمْ‌[4].
- **Isnad as currently extracted:**
  > وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ سَأَلْتُهُ عَنِ الْمُحْرِمِ وَ مَا يَقْتُلُ مِنَ الدَّوَابِّ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن الفضیل | روی |  |
  | 1 | imam | ابی الحسن ع | عن |  |

### Chain 106 · `faqih-2717` — CLARIFIED
- Transmitters (student → teacher): محمد بن الفضيل → ابي الحسن ع
- Corrected isnad (Arabic): «وَ رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ عَنْ أَبِي الْحَسَنِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْمُحْرِمِ وَ مَا يَقْتُلُ مِنَ الدَّوَابِّ قَالَ"
- Mursal opening: al-Ṣadūq → محمد بن الفضيل; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 107 · `faqih-2720`
- **Location:** vol. 2, p. 365 · seq 2728 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى عَبْدُ اللَّهِ بْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ[3] قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ مُحْرِمٍ أَصَابَ نَعَامَةً أَوْ حِمَارَ وَحْشٍ قَالَ عَلَيْهِ بَدَنَةٌ قُلْتُ فَإِنْ لَمْ يَقْدِرْ قَالَ يُطْعِمُ سِتِّينَ مِسْكِيناً قُلْتُ فَإِنْ لَمْ يَقْدِرْ عَلَى مَا يَتَصَدَّقُ بِهِ مَا عَلَيْهِ قَالَ فَلْيَصُمْ ثَمَانِيَةَ عَشَرَ يَوْماً قُلْتُ فَإِنْ أَصَابَ بَقَرَةً مَا عَلَيْهِ قَالَ عَلَيْهِ بَقَرَةٌ قُلْتُ فَإِنْ لَمْ يَقْدِرْ قَالَ فَلْيُطْعِمْ ثَلَاثِينَ مِسْكِيناً قُلْتُ فَإِنْ لَمْ يَقْدِرْ عَلَى مَا يَتَصَدَّقُ بِهِ قَالَ فَلْيَصُمْ تِسْعَةَ أَيَّامٍ قُلْتُ فَإِنْ أَصَابَ ظَبْياً مَا عَلَيْهِ قَالَ عَلَيْهِ شَاةٌ قُلْتُ فَإِنْ لَمْ يَجِدْ قَالَ فَعَلَيْهِ إِطْعَامُ عَشَرَةِ مَسَاكِينَ قُلْتُ فَإِنْ لَمْ يَجِدْ مَا يَتَصَدَّقُ بِهِ قَالَ فَعَلَيْهِ صِيَامُ ثَلَاثَةِ أَيَّامٍ‌[4].
- **Isnad as currently extracted:**
  > وَ رَوَى عَبْدُ اللَّهِ بْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ[3] قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عبد الله بن مسکان | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |

### Chain 107 · `faqih-2720` — CLARIFIED
- Transmitters (student → teacher): عبد الله بن مسكان → ابي بصير → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى عَبْدُ اللَّهِ بْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ[3] قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ مُحْرِمٍ أَصَابَ نَعَامَةً"
- Mursal opening: al-Ṣadūq → عبد الله بن مسكان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 108 · `faqih-2721`
- **Location:** vol. 2, p. 366 · seq 2729 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى ابْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ رَمَى صَيْداً وَ هُوَ مُحْرِمٌ فَكَسَرَ يَدَهُ أَوْ رِجْلَهُ فَذَهَبَ عَلَى وَجْهِهِ فَلَا يَدْرِي مَا صَنَعَ قَالَ عَلَيْهِ فِدَاؤُهُ قُلْتُ فَإِنْ رَآهُ بَعْدَ ذَلِكَ قَدْ رَعَى وَ مَشَى قَالَ عَلَيْهِ رُبُعُ قِيمَتِهِ.
- **Isnad as currently extracted:**
  > وَ رَوَى ابْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن مسکان | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |

### Chain 108 · `faqih-2721` — CLARIFIED
- Transmitters (student → teacher): ابن مسكان → ابي بصير → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى ابْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ رَمَى صَيْداً وَ"
- Mursal opening: al-Ṣadūq → ابن مسكان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 109 · `faqih-2722`
- **Location:** vol. 2, p. 366 · seq 2730 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى الْبَزَنْطِيُّ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ سَأَلْتُهُ عَنْ مُحْرِمٍ أَصَابَ أَرْنَباً أَوْ ثَعْلَباً قَالَ فِي الْأَرْنَبِ دَمُ شَاةٍ[1].
- **Isnad as currently extracted:**
  > وَ رَوَى الْبَزَنْطِيُّ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ سَأَلْتُهُ عَنْ مُحْرِمٍ أَصَابَ أَرْنَباً أَوْ ثَعْلَباً قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | البزنطی | روی |  |
  | 1 | imam | ابی الحسن ع | عن |  |

### Chain 109 · `faqih-2722` — CLARIFIED
- Transmitters (student → teacher): البزنطي → ابي الحسن ع
- Corrected isnad (Arabic): «وَ رَوَى الْبَزَنْطِيُّ عَنْ أَبِي الْحَسَنِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ مُحْرِمٍ أَصَابَ أَرْنَباً أَوْ ثَعْلَباً قَالَ فِي"
- Mursal opening: al-Ṣadūq → البزنطي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 110 · `faqih-2723`
- **Location:** vol. 2, p. 366 · seq 2731 · chain 1
- **Flags:** `matn_spill`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ فِي رِوَايَةِ ابْنِ مُسْكَانَ عَنِ الْحَلَبِيِّ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الْأَرْنَبِ يُصِيبُهُ الْمُحْرِمُ فَقَالَ شَاةٌ هَدْياً بَالِغَ الْكَعْبَةِ.
- **Isnad as currently extracted:**
  > وَ فِي رِوَايَةِ ابْنِ مُسْكَانَ عَنِ الْحَلَبِيِّ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | فی روایة ابن مسکان |  |  |
  | 1 | named_narrator | الحلبی | عن |  |

### Chain 110 · `faqih-2723` — CLARIFIED
- Transmitters (student → teacher): ابن مسكان → الحلبي → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ فِي رِوَايَةِ ابْنِ مُسْكَانَ عَنِ الْحَلَبِيِّ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الْأَرْنَبِ يُصِيبُهُ الْمُحْرِمُ"
- Mursal opening: al-Ṣadūq → ابن مسكان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 111 · `faqih-2730`
- **Location:** vol. 2, p. 373 · seq 2738 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى يُوسُفُ الطَّاطَرِيُ‌[6] قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع صَيْدٌ
أَكَلَهُ قَوْمٌ مُحْرِمُونَ قَالَ عَلَيْهِمْ شَاةٌ شَاةٌ وَ لَيْسَ عَلَى الَّذِي ذَبَحَهُ إِلَّا شَاةٌ[1].
- **Isnad as currently extracted:**
  > وَ رَوَى يُوسُفُ الطَّاطَرِيُ‌[6] قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | یوسف الطاطری | روی |  |

### Chain 111 · `faqih-2730` — CLARIFIED
- Transmitters (student → teacher): يوسف الطاطري → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى يُوسُفُ الطَّاطَرِيُ‌[6] قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع صَيْدٌ أَكَلَهُ قَوْمٌ مُحْرِمُونَ"
- Mursal opening: al-Ṣadūq → يوسف الطاطري; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 112 · `faqih-2731`
- **Location:** vol. 2, p. 374 · seq 2739 · chain 1
- **Flags:** `multi_route`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى عَلِيُّ بْنُ رِئَابٍ عَنْ أَبَانِ بْنِ تَغْلِبَ عَنْ أَبِي عَبْدِ اللَّهِ ع‌ فِي قَوْمٍ حُجَّاجٍ مُحْرِمِينَ أَصَابُوا أَفْرَاخَ نَعَامٍ فَأَكَلُوا جَمِيعاً قَالَ عَلَيْهِمْ مَكَانَ كُلِّ فَرْخٍ أَكَلُوهُ بَدَنَةٌ يَشْتَرِكُونَ فِيهَا جَمِيعاً فَيَشْتَرُونَهَا عَلَى عَدَدِ الْفِرَاخِ وَ عَلَى عَدَدِ الرِّجَالِ‌[2].
- **Isnad as currently extracted:**
  > وَ رَوَى عَلِيُّ بْنُ رِئَابٍ عَنْ أَبَانِ بْنِ تَغْلِبَ عَنْ أَبِي عَبْدِ اللَّهِ ع‌ فِي قَوْمٍ حُجَّاجٍ مُحْرِمِينَ أَصَابُوا أَفْرَاخَ نَعَامٍ فَأَكَلُوا جَمِيعاً قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن رئاب | روی |  |
  | 1 | named_narrator | ابان بن تغلب | عن |  |
  | 2 | named_narrator | ابی عبد الله ع فی قوم حجاج محرمین اصابوا افراخ نعام فاکلوا | عن |  |

### Chain 112 · `faqih-2731` — CLARIFIED
- Transmitters (student → teacher): علي بن رئاب → أبان بن تغلب → أبو عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى عَلِيُّ بْنُ رِئَابٍ عَنْ أَبَانِ بْنِ تَغْلِبَ عَنْ أَبِي عَبْدِ اللَّهِ ع‌»
- Isnad ends / matn begins at: "فِي قَوْمٍ حُجَّاجٍ مُحْرِمِينَ أَصَابُوا أَفْرَاخَ نَعَامٍ فَأَكَلُوا جَمِيعاً"
- Mursal opening: al-Ṣadūq → علي بن رئاب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The Arabic syntax gives one linear route ending at Abū ʿAbd Allāh. The automatic fork flag was a false positive caused by material inside the legal case, not by the isnād.
---

### Chain 113 · `faqih-2737`
- **Location:** vol. 2, p. 375 · seq 2745 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ أَبِي إِبْرَاهِيمَ ع قَالَ‌ قُلْتُ لَهُ الرَّجُلُ يَتَمَتَّعُ فَيَنْسَى أَنْ يُقَصِّرَ حَتَّى يُهِلَّ بِالْحَجِّ فَقَالَ عَلَيْهِ دَمٌ.
وَ فِي رِوَايَةِ عَبْدِ اللَّهِ بْنِ سِنَانٍ عَنْ أَبِي عَبْدِ اللَّهِ ع‌ يَسْتَغْفِرُ اللَّهَ تَعَالَى‌[4].
- **Isnad as currently extracted:**
  > وَ رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ أَبِي إِبْرَاهِيمَ ع قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | اسحاق بن عمار | روی |  |
  | 1 | imam | ابی ابراهیم ع | عن |  |

### Chain 113 · `faqih-2737` — CLARIFIED
- Transmitters (student → teacher): اسحاق بن عمار → ابي ابراهيم ع
- Corrected isnad (Arabic): «وَ رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ أَبِي إِبْرَاهِيمَ ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ الرَّجُلُ يَتَمَتَّعُ فَيَنْسَى أَنْ يُقَصِّرَ حَتَّى يُهِلَّ"
- Mursal opening: al-Ṣadūq → اسحاق بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 114 · `faqih-2741`
- **Location:** vol. 2, p. 377 · seq 2749 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى أَبُو بَصِيرٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ مُتَمَتِّعٍ أَرَادَ أَنْ يُقَصِّرَ فَحَلَقَ رَأْسَهُ قَالَ عَلَيْهِ دَمٌ يُهَرِيقُهُ فَإِذَا كَانَ يَوْمُ النَّحْرِ أَمَرَّ الْمُوسَى عَلَى رَأْسِهِ حِينَ يُرِيدُ أَنْ يَحْلِقَ‌[2].
- **Isnad as currently extracted:**
  > وَ رَوَى أَبُو بَصِيرٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ مُتَمَتِّعٍ أَرَادَ أَنْ يُقَصِّرَ فَحَلَقَ رَأْسَهُ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابو بصیر | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 114 · `faqih-2741` — CLARIFIED
- Transmitters (student → teacher): ابو بصير → ابي عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى أَبُو بَصِيرٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ مُتَمَتِّعٍ أَرَادَ أَنْ يُقَصِّرَ فَحَلَقَ رَأْسَهُ قَالَ"
- Mursal opening: al-Ṣadūq → ابو بصير; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 115 · `faqih-2742`
- **Location:** vol. 2, p. 377 · seq 2750 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى أَبُو الْمَغْرَاءِ[3] عَنْ أَبِي بَصِيرٍ قَالَ‌ قُلْتُ لِأَبِي جَعْفَرٍ ع رَجُلٌ أَحَلَّ مِنْ إِحْرَامِهِ وَ لَمْ تَحِلَّ امْرَأَتُهُ فَوَقَعَ عَلَيْهَا قَالَ عَلَيْهَا بَدَنَةٌ يَغْرَمُهَا زَوْجُهَا.
- **Isnad as currently extracted:**
  > وَ رَوَى أَبُو الْمَغْرَاءِ[3] عَنْ أَبِي بَصِيرٍ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابو المغراء | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |

### Chain 115 · `faqih-2742` — CLARIFIED
- Transmitters (student → teacher): ابو المغراء → ابي بصير → ابي جعفر ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى أَبُو الْمَغْرَاءِ[3] عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي جَعْفَرٍ ع رَجُلٌ أَحَلَّ مِنْ إِحْرَامِهِ وَ"
- Mursal opening: al-Ṣadūq → ابو المغراء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 116 · `faqih-2749`
- **Location:** vol. 2, p. 379 · seq 2757 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى الْقَاسِمُ بْنُ مُحَمَّدٍ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ قَالَ‌ سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنْ رَجُلٍ يَدْخُلُ مَكَّةَ فِي السَّنَةِ الْمَرَّةَ وَ الْمَرَّتَيْنِ وَ الثَّلَاثَ كَيْفَ يَصْنَعُ قَالَ إِذَا دَخَلَ فَلْيَدْخُلْ مُلَبِّياً وَ إِذَا خَرَجَ فَلْيَخْرُجْ مُحِلًّا.
- **Isnad as currently extracted:**
  > وَ رَوَى الْقَاسِمُ بْنُ مُحَمَّدٍ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | القاسم بن محمد | روی |  |
  | 1 | named_narrator | علی بن ابی حمزة | عن |  |

### Chain 116 · `faqih-2749` — CLARIFIED
- Transmitters (student → teacher): القاسم بن محمد → علي بن ابي حمزة → ابا ابراهيم ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى الْقَاسِمُ بْنُ مُحَمَّدٍ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنْ رَجُلٍ يَدْخُلُ مَكَّةَ فِي"
- Mursal opening: al-Ṣadūq → القاسم بن محمد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 117 · `faqih-2751`
- **Location:** vol. 2, p. 380 · seq 2759 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ دُرُسْتَ‌[2] عَنْ عَجْلَانَ أَبِي صَالِحٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ مُتَمَتِّعَةٍ دَخَلَتْ مَكَّةَ فَحَاضَتْ فَقَالَ تَسْعَى بَيْنَ الصَّفَا وَ الْمَرْوَةِ ثُمَّ تَخْرُجُ مَعَ النَّاسِ حَتَّى تَقْضِيَ طَوَافَهَا بَعْدُ.
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ دُرُسْتَ‌[2] عَنْ عَجْلَانَ أَبِي صَالِحٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن درست | روی |  |
  | 1 | named_narrator | عجلان ابی صالح | عن |  |

### Chain 117 · `faqih-2751` — CLARIFIED
- Transmitters (student → teacher): درست → عجلان ابي صالح → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ دُرُسْتَ‌[2] عَنْ عَجْلَانَ أَبِي صَالِحٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ مُتَمَتِّعَةٍ دَخَلَتْ مَكَّةَ"
- Mursal opening: al-Ṣadūq → درست; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 118 · `faqih-2753`
- **Location:** vol. 2, p. 380 · seq 2761 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنِ الْمُحْرِمَةِ إِذَا
طَهُرَتْ تَغْسِلُ رَأْسَهَا بِالْخِطْمِيِّ فَقَالَ يُجْزِيهَا الْمَاءُ[1].
- **Isnad as currently extracted:**
  > وَ رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنِ الْمُحْرِمَةِ إِذَا طَهُرَتْ تَغْسِلُ رَأْسَهَا بِالْخِطْمِيِّ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن مسلم | روی |  |
  | 1 | imam | احدهما ع | عن | ambiguous |

### Chain 118 · `faqih-2753` — CLARIFIED
- Transmitters (student → teacher): محمد بن مسلم → احدهما ع
- Corrected isnad (Arabic): «وَ رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْمُحْرِمَةِ إِذَا طَهُرَتْ تَغْسِلُ رَأْسَهَا بِالْخِطْمِيِّ فَقَالَ"
- Mursal opening: al-Ṣadūq → محمد بن مسلم; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 119 · `faqih-2755`
- **Location:** vol. 2, p. 381 · seq 2763 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى صَفْوَانُ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنِ الْمَرْأَةِ تَجِي‌ءُ مُتَمَتِّعَةً فَتَطْمَثُ قَبْلَ أَنْ تَطُوفَ بِالْبَيْتِ حَتَّى تَخْرُجَ إِلَى عَرَفَاتٍ فَقَالَ تَصِيرُ حَجَّةً مُفْرَدَةً وَ عَلَيْهَا دَمُ أُضْحِيَّتِهَا[3].
- **Isnad as currently extracted:**
  > وَ رَوَى صَفْوَانُ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان | روی |  |
  | 1 | named_narrator | اسحاق بن عمار | عن |  |

### Chain 119 · `faqih-2755` — CLARIFIED
- Transmitters (student → teacher): صفوان → اسحاق بن عمار
- Corrected isnad (Arabic): «وَ رَوَى صَفْوَانُ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنِ الْمَرْأَةِ تَجِي‌ءُ مُتَمَتِّعَةً فَتَطْمَثُ"
- Mursal opening: al-Ṣadūq → صفوان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 120 · `faqih-2756`
- **Location:** vol. 2, p. 381 · seq 2764 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى صَفْوَانُ عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ قَالَ‌ سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنْ رَجُلٍ كَانَتْ مَعَهُ امْرَأَةٌ فَقَدِمَتْ مَكَّةَ وَ هِيَ لَا تُصَلِّي فَلَمْ تَطْهُرْ إِلَّا يَوْمَ التَّرْوِيَةِ وَ طَهُرَتْ وَ طَافَتْ بِالْبَيْتِ وَ لَمْ تَسْعَ بَيْنَ الصَّفَا وَ الْمَرْوَةِ[4] حَتَّى شَخَصَتْ إِلَى عَرَفَاتٍ هَلْ تَعْتَدُّ بِذَلِكَ الطَّوَافِ أَوْ تُعِيدُ قَبْلَ الصَّفَا وَ الْمَرْوَةِ قَالَ تَعْتَدُّ بِذَلِكَ الطَّوَافِ الْأَوَّلِ وَ تَبْنِي عَلَيْهِ‌[5].
- **Isnad as currently extracted:**
  > وَ رَوَى صَفْوَانُ عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان | روی |  |
  | 1 | named_narrator | عبد الرحمن بن الحجاج | عن |  |

### Chain 120 · `faqih-2756` — CLARIFIED
- Transmitters (student → teacher): صفوان → عبد الرحمن بن الحجاج → ابا ابراهيم ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى صَفْوَانُ عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنْ رَجُلٍ كَانَتْ مَعَهُ امْرَأَةٌ"
- Mursal opening: al-Ṣadūq → صفوان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 121 · `faqih-2757`
- **Location:** vol. 2, p. 381 · seq 2765 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى أَبَانٌ عَنْ زُرَارَةَ قَالَ‌ سَأَلْتُهُ عَنِ امْرَأَةٍ طَافَتْ بِالْبَيْتِ فَحَاضَتْ‌
قَبْلَ أَنْ تُصَلِّيَ الرَّكْعَتَيْنِ فَقَالَ لَيْسَ عَلَيْهَا إِذَا طَهُرَتْ إِلَّا الرَّكْعَتَيْنِ وَ قَدْ قَضَتِ الطَّوَافَ‌[1].
- **Isnad as currently extracted:**
  > وَ رَوَى أَبَانٌ عَنْ زُرَارَةَ قَالَ‌ سَأَلْتُهُ عَنِ امْرَأَةٍ طَافَتْ بِالْبَيْتِ فَحَاضَتْ‌ قَبْلَ أَنْ تُصَلِّيَ الرَّكْعَتَيْنِ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابان | روی |  |
  | 1 | named_narrator | زرارة | عن |  |

### Chain 121 · `faqih-2757` — CLARIFIED
- Transmitters (student → teacher): أبان → زرارة → إمامٌ غير مصرّح باسمه في هذا الطريق (مضمرة زرارة)
- Corrected isnad (Arabic): «وَ رَوَى أَبَانٌ عَنْ زُرَارَةَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ امْرَأَةٍ طَافَتْ بِالْبَيْتِ فَحَاضَتْ‌ قَبْلَ أَنْ تُصَلِّيَ"
- Mursal opening: al-Ṣadūq → أبان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: This report is treated in the juristic literature as «مضمرة زرارة». The exact route does not name the Imam, and the nearby explicit report from Abū ʿAbd Allāh is a separate parallel, so it is not silently substituted into this chain. Sources: [Wasāʾil al-Shīʿa, vol. 13](https://alkafeel.net/islamiclibrary/hadith/wasael-13/wasael-13/v23.html); [juristic identification as a muḍmar](https://ar.lib.eshia.ir/13196/2/383).
---

### Chain 122 · `faqih-2759`
- **Location:** vol. 2, p. 382 · seq 2767 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى صَفْوَانُ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنْ جَارِيَةٍ لَمْ تَحِضْ خَرَجَتْ مَعَ زَوْجِهَا وَ أَهْلِهَا فَحَاضَتْ فَاسْتَحْيَتْ أَنْ تُعْلِمَ أَهْلَهَا وَ زَوْجَهَا حَتَّى قَضَتِ الْمَنَاسِكَ وَ هِيَ عَلَى تِلْكَ الْحَالَةِ وَ وَاقَعَهَا زَوْجُهَا وَ رَجَعَتْ إِلَى الْكُوفَةِ فَقَالَتْ لِأَهْلِهَا قَدْ كَانَ مِنَ الْأَمْرِ كَذَا وَ كَذَا فَقَالَ عَلَيْهَا سَوْقُ بَدَنَةٍ وَ الْحَجُّ مِنْ قَابِلٍ‌[3] وَ لَيْسَ عَلَى زَوْجِهَا شَيْ‌ءٌ.
- **Isnad as currently extracted:**
  > وَ رَوَى صَفْوَانُ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان | روی |  |
  | 1 | named_narrator | اسحاق بن عمار | عن |  |

### Chain 122 · `faqih-2759` — CLARIFIED
- Transmitters (student → teacher): صفوان → اسحاق بن عمار
- Corrected isnad (Arabic): «وَ رَوَى صَفْوَانُ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنْ جَارِيَةٍ لَمْ تَحِضْ خَرَجَتْ"
- Mursal opening: al-Ṣadūq → صفوان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 123 · `faqih-2760`
- **Location:** vol. 2, p. 382 · seq 2768 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى فَضَالَةُ بْنُ أَيُّوبَ عَنِ الْكَاهِلِيِّ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ النِّسَاءِ فِي إِحْرَامِهِنَّ فَقَالَ يُصْلِحْنَ مَا أَرَدْنَ أَنْ يُصْلِحْنَ‌[4] فَإِذَا وَرَدْنَ الشَّجَرَةَ أَهْلَلْنَ بِالْحَجِّ وَ لَبَّيْنَ عِنْدَ الْمِيلِ أَوَّلَ الْبَيْدَاءِ ثُمَّ يُؤْتَى بِهِنَّ مَكَّةَ يُبَادَرُ بِهِنَّ الطَّوَافَ وَ السَّعْيَ‌[5] فَإِذَا قَضَيْنَ طَوَافَهُنَّ وَ سَعْيَهُنَّ قَصَّرْنَ وَ جَازَتْ‌[6] مُتْعَةٌ ثُمَّ أَهْلَلْنَ يَوْمَ التَّرْوِيَةِ بِالْحَجِّ-
وَ كَانَتْ عُمْرَةً وَ حَجَّةً وَ إِنِ اعْتَلَلْنَ كُنَّ عَلَى حَجِّهِنَ‌[1] وَ لَمْ يُفْرِدْنَ حَجَّهُنَّ.
- **Isnad as currently extracted:**
  > وَ رَوَى فَضَالَةُ بْنُ أَيُّوبَ عَنِ الْكَاهِلِيِّ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | فضالة بن ایوب | روی |  |
  | 1 | named_narrator | الکاهلی | عن |  |

### Chain 123 · `faqih-2760` — CLARIFIED
- Transmitters (student → teacher): فضالة بن ايوب → الكاهلي → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى فَضَالَةُ بْنُ أَيُّوبَ عَنِ الْكَاهِلِيِّ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ النِّسَاءِ فِي إِحْرَامِهِنَّ"
- Mursal opening: al-Ṣadūq → فضالة بن ايوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 124 · `faqih-2761`
- **Location:** vol. 2, p. 383 · seq 2769 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ امْرَأَةٍ طَافَتْ ثَلَاثَةَ أَطْوَافٍ أَوْ أَقَلَّ مِنْ ذَلِكَ ثُمَّ رَأَتْ دَماً فَقَالَ تَحْفَظُ مَكَانَهَا فَإِذَا طَهُرَتْ طَافَتْ مِنْهُ وَ اعْتَدَّتْ بِمَا مَضَى‌[2].
- وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع‌ مِثْلَهُ قَالَ مُصَنِّفُ هَذَا الْكِتَابِ رَضِيَ اللَّهُ عَنْهُ وَ بِهَذَا الْحَدِيثِ أُفْتِي دُونَ الْحَدِيثِ الَّذِي رَوَاهُ.
- **Isnad as currently extracted:**
  > وَ رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حریز | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |

### Chain 124 · `faqih-2761` — CLARIFIED
- Transmitters (student → teacher): حريز → محمد بن مسلم → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ امْرَأَةٍ طَافَتْ ثَلَاثَةَ"
- Mursal opening: al-Ṣadūq → حريز; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 125 · `faqih-2765`
- **Location:** vol. 2, p. 385 · seq 2773 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ أَبِي بَصِيرٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الْمَرْأَةُ تَجِي‌ءُ مُتَمَتِّعَةً فَتَطْمَثُ قَبْلَ أَنْ تَطُوفَ بِالْبَيْتِ فَيَكُونُ طُهْرُهَا لَيْلَةَ عَرَفَةَ فَقَالَ ع إِنْ كَانَتْ تَعْلَمُ أَنَّهَا تَطْهُرُ وَ تَطُوفُ بِالْبَيْتِ وَ تَحِلُّ مِنْ إِحْرَامِهَا وَ تَلْحَقُ النَّاسَ بِمِنًى فَلْتَفْعَلْ.
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ أَبِي بَصِيرٍ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن ابی بصیر | روی |  |

### Chain 125 · `faqih-2765` — CLARIFIED
- Transmitters (student → teacher): ابي بصير → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الْمَرْأَةُ تَجِي‌ءُ مُتَمَتِّعَةً فَتَطْمَثُ"
- Mursal opening: al-Ṣadūq → ابي بصير; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 126 · `faqih-2766`
- **Location:** vol. 2, p. 385 · seq 2774 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى النَّضْرُ عَنْ شُعَيْبٍ الْعَقَرْقُوفِيِّ قَالَ‌ خَرَجْتُ أَنَا وَ حَدِيدٌ فَانْتَهَيْنَا إِلَى الْبُسْتَانِ‌[2]- يَوْمَ التَّرْوِيَةِ- فَتَقَدَّمْتُ عَلَى حِمَارٍ فَقَدِمْتُ مَكَّةَ وَ طُفْتُ وَ سَعَيْتُ وَ أَحْلَلْتُ مِنْ تَمَتُّعِي ثُمَّ أَحْرَمْتُ بِالْحَجِّ وَ قَدِمَ حَدِيدٌ مِنَ اللَّيْلِ فَكَتَبْتُ إِلَى أَبِي الْحَسَنِ ع اسْتَفْتَيْتُهُ فِي أَمْرِهِ فَكَتَبَ إِلَيَّ مُرْهُ يَطُوفُ وَ يَسْعَى وَ يَحِلُّ مِنْ مُتْعَتِهِ وَ يُحْرِمُ بِالْحَجِّ وَ يَلْحَقُ النَّاسَ بِمِنًى وَ لَا يَبِيتَنَّ بِمَكَّةَ[3].
- **Isnad as currently extracted:**
  > وَ رَوَى النَّضْرُ عَنْ شُعَيْبٍ الْعَقَرْقُوفِيِّ قَالَ‌ خَرَجْتُ أَنَا وَ حَدِيدٌ فَانْتَهَيْنَا إِلَى الْبُسْتَانِ‌[2]- يَوْمَ التَّرْوِيَةِ- فَتَقَدَّمْتُ عَلَى حِمَارٍ فَقَدِمْتُ مَكَّةَ وَ طُفْتُ وَ سَعَيْتُ وَ أَحْلَلْتُ مِنْ تَمَتُّعِي ثُمَّ أَحْرَمْتُ بِالْحَجِّ وَ قَدِمَ حَدِيدٌ مِنَ اللَّيْلِ فَكَتَبْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | النضر | روی |  |
  | 1 | named_narrator | شعیب العقرقوفی | عن |  |

### Chain 126 · `faqih-2766` — CLARIFIED
- Transmitters (student → teacher): النضر → شعيب العقرقوفي → ابي الحسن ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى النَّضْرُ عَنْ شُعَيْبٍ الْعَقَرْقُوفِيِّ قَالَ‌»
- Isnad ends / matn begins at: "خَرَجْتُ أَنَا وَ حَدِيدٌ فَانْتَهَيْنَا إِلَى الْبُسْتَانِ‌[2]- يَوْمَ التَّرْوِيَةِ-"
- Mursal opening: al-Ṣadūq → النضر; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 127 · `faqih-2767`
- **Location:** vol. 2, p. 385 · seq 2775 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ رِئَابٍ عَنْ ضُرَيْسٍ الْكُنَاسِيِّ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ خَرَجَ مُتَمَتِّعاً بِعُمْرَةٍ إِلَى الْحَجِّ فَلَمْ يَبْلُغْ مَكَّةَ إِلَّا يَوْمَ النَّحْرِ فَقَالَ يُقِيمُ بِمَكَّةَ عَلَى إِحْرَامِهِ وَ يَقْطَعُ التَّلْبِيَةَ حِينَ يَدْخُلُ الْحَرَمَ فَيَطُوفُ بِالْبَيْتِ وَ يَسْعَى وَ يَحْلِقُ رَأْسَهُ وَ يَذْبَحُ شَاتَهُ ثُمَّ يَنْصَرِفُ إِلَى أَهْلِهِ ثُمَّ قَالَ هَذَا لِمَنِ اشْتَرَطَ عَلَى رَبِّهِ عِنْدَ إِحْرَامِهِ أَنْ يَحُلَّهُ حَيْثُ حَبَسَهُ فَإِنْ لَمْ يَشْتَرِطْ فَإِنَّ عَلَيْهِ الْحَجَّ وَ الْعُمْرَةَ مِنْ قَابِلٍ‌[4].
- **Isnad as currently extracted:**
  > وَ رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ رِئَابٍ عَنْ ضُرَيْسٍ الْكُنَاسِيِّ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ خَرَجَ مُتَمَتِّعاً بِعُمْرَةٍ إِلَى الْحَجِّ فَلَمْ يَبْلُغْ مَكَّةَ إِلَّا يَوْمَ النَّحْرِ فَقَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | علی بن رئاب | عن |  |
  | 2 | named_narrator | ضریس الکناسی | عن |  |
  | 3 | imam | ابی جعفر ع | عن |  |

### Chain 127 · `faqih-2767` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → علي بن رئاب → ضريس الكناسي → ابي جعفر ع
- Corrected isnad (Arabic): «وَ رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ رِئَابٍ عَنْ ضُرَيْسٍ الْكُنَاسِيِّ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ خَرَجَ مُتَمَتِّعاً بِعُمْرَةٍ إِلَى الْحَجِّ فَلَمْ"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 128 · `faqih-2772`
- **Location:** vol. 2, p. 387 · seq 2780 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ سَمَاعَةَ بْنِ مِهْرَانَ عَنْ أَبِي الْحَسَنِ الْمَاضِي ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ طَافَ طَوَافَ الْحَجِّ وَ طَوَافَ النِّسَاءِ قَبْلَ أَنْ يَسْعَى بَيْنَ الصَّفَا وَ الْمَرْوَةِ قَالَ لَا يَضُرُّهُ يَطُوفُ بَيْنَ الصَّفَا وَ الْمَرْوَةِ وَ قَدْ فَرَغَ مِنْ حَجِّهِ‌[2].
- **Isnad as currently extracted:**
  > رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ سَمَاعَةَ بْنِ مِهْرَانَ عَنْ أَبِي الْحَسَنِ الْمَاضِي ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ طَافَ طَوَافَ الْحَجِّ وَ طَوَافَ النِّسَاءِ قَبْلَ أَنْ يَسْعَى بَيْنَ الصَّفَا وَ الْمَرْوَةِ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | اسحاق بن عمار | روی |  |
  | 1 | named_narrator | سماعة بن مهران | عن |  |
  | 2 | imam | ابی الحسن الماضی ع | عن |  |

### Chain 128 · `faqih-2772` — CLARIFIED
- Transmitters (student → teacher): اسحاق بن عمار → سماعة بن مهران → ابي الحسن الماضي ع
- Corrected isnad (Arabic): «رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ سَمَاعَةَ بْنِ مِهْرَانَ عَنْ أَبِي الْحَسَنِ الْمَاضِي ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ طَافَ طَوَافَ الْحَجِّ وَ طَوَافَ النِّسَاءِ"
- Mursal opening: al-Ṣadūq → اسحاق بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 129 · `faqih-2772`
- **Location:** vol. 2, p. 387 · seq 2780 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ سَمَاعَةَ بْنِ مِهْرَانَ عَنْ أَبِي الْحَسَنِ الْمَاضِي ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ طَافَ طَوَافَ الْحَجِّ وَ طَوَافَ النِّسَاءِ قَبْلَ أَنْ يَسْعَى بَيْنَ الصَّفَا وَ الْمَرْوَةِ قَالَ لَا يَضُرُّهُ يَطُوفُ بَيْنَ الصَّفَا وَ الْمَرْوَةِ وَ قَدْ فَرَغَ مِنْ حَجِّهِ‌[2].
- **Isnad as currently extracted:**
  > رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ سَمَاعَةَ بْنِ مِهْرَانَ عَنْ أَبِي الْحَسَنِ الْمَاضِي ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ طَافَ طَوَافَ الْحَجِّ وَ طَوَافَ النِّسَاءِ قَبْلَ أَنْ يَسْعَى بَيْنَ الصَّفَا وَ الْمَرْوَةِ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | اسحاق بن عمار | روی |  |
  | 1 | named_narrator | سماعة بن مهران | عن |  |
  | 2 | imam | ابی الحسن الماضی ع | عن |  |

### Chain 129 · `faqih-2772` — CLARIFIED
- Transmitters (student → teacher): اسحاق بن عمار → سماعة بن مهران → ابي الحسن الماضي ع
- Corrected isnad (Arabic): «رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ سَمَاعَةَ بْنِ مِهْرَانَ عَنْ أَبِي الْحَسَنِ الْمَاضِي ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ طَافَ طَوَافَ الْحَجِّ وَ طَوَافَ النِّسَاءِ"
- Mursal opening: al-Ṣadūq → اسحاق بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 130 · `faqih-2772`
- **Location:** vol. 2, p. 387 · seq 2780 · chain 3
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ سَمَاعَةَ بْنِ مِهْرَانَ عَنْ أَبِي الْحَسَنِ الْمَاضِي ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ طَافَ طَوَافَ الْحَجِّ وَ طَوَافَ النِّسَاءِ قَبْلَ أَنْ يَسْعَى بَيْنَ الصَّفَا وَ الْمَرْوَةِ قَالَ لَا يَضُرُّهُ يَطُوفُ بَيْنَ الصَّفَا وَ الْمَرْوَةِ وَ قَدْ فَرَغَ مِنْ حَجِّهِ‌[2].
- **Isnad as currently extracted:**
  > رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ سَمَاعَةَ بْنِ مِهْرَانَ عَنْ أَبِي الْحَسَنِ الْمَاضِي ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ طَافَ طَوَافَ الْحَجِّ وَ طَوَافَ النِّسَاءِ قَبْلَ أَنْ يَسْعَى بَيْنَ الصَّفَا وَ الْمَرْوَةِ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | اسحاق بن عمار | روی |  |
  | 1 | named_narrator | سماعة بن مهران | عن |  |
  | 2 | imam | ابی الحسن الماضی ع | عن |  |

### Chain 130 · `faqih-2772` — CLARIFIED
- Transmitters (student → teacher): اسحاق بن عمار → سماعة بن مهران → ابي الحسن الماضي ع
- Corrected isnad (Arabic): «رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ سَمَاعَةَ بْنِ مِهْرَانَ عَنْ أَبِي الْحَسَنِ الْمَاضِي ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ طَافَ طَوَافَ الْحَجِّ وَ طَوَافَ النِّسَاءِ"
- Mursal opening: al-Ṣadūq → اسحاق بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 131 · `faqih-2775`
- **Location:** vol. 2, p. 387 · seq 2783 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى صَفْوَانُ بْنُ يَحْيَى عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ أَبَا إِبْرَاهِيمَ‌
ع عَنِ الْمُتَمَتِّعِ إِذَا كَانَ شَيْخاً كَبِيراً أَوِ امْرَأَةً تَخَافُ الْحَيْضَ يُعَجِّلُ الطَّوَافَ لِلْحَجِّ قَبْلَ أَنْ يَأْتِيَ مِنًى قَالَ نَعَمْ مَنْ هُوَ هَكَذَا يُعَجِّلُ قَالَ وَ سَأَلْتُهُ عَنْ رَجُلٍ يُحْرِمُ بِالْحَجِّ مِنْ مَكَّةَ ثُمَّ يَرَى الْبَيْتَ خَالِياً فَيَطُوفُ بِهِ قَبْلَ أَنْ يَخْرُجَ عَلَيْهِ شَيْ‌ءٌ فَقَالَ لَا[1].
- **Isnad as currently extracted:**
  > وَ رَوَى صَفْوَانُ بْنُ يَحْيَى عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان بن یحیی | روی |  |
  | 1 | named_narrator | اسحاق بن عمار | عن |  |

### Chain 131 · `faqih-2775` — CLARIFIED
- Transmitters (student → teacher): صفوان بن يحيي → اسحاق بن عمار
- Corrected isnad (Arabic): «وَ رَوَى صَفْوَانُ بْنُ يَحْيَى عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا إِبْرَاهِيمَ‌ ع عَنِ الْمُتَمَتِّعِ إِذَا كَانَ شَيْخاً"
- Mursal opening: al-Ṣadūq → صفوان بن يحيي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 132 · `faqih-2776`
- **Location:** vol. 2, p. 388 · seq 2784 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنْ زِيَارَةِ الْبَيْتِ تُؤَخَّرُ إِلَى يَوْمِ الثَّالِثِ‌[3] فَقَالَ تَعْجِيلُهَا أَحَبُّ إِلَيَّ وَ لَيْسَ بِهِ بَأْسٌ إِنْ أَخَّرْتَهُ‌[4].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن اسحاق بن عمار | روی |  |

### Chain 132 · `faqih-2776` — CLARIFIED
- Transmitters (student → teacher): اسحاق بن عمار
- Corrected isnad (Arabic): «رُوِيَ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنْ زِيَارَةِ الْبَيْتِ تُؤَخَّرُ إِلَى"
- Mursal opening: al-Ṣadūq → اسحاق بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 133 · `faqih-2778`
- **Location:** vol. 2, p. 388 · seq 2786 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى عُبَيْدُ اللَّهِ بْنُ عَلِيٍّ الْحَلَبِيُّ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ‌
عَنْ رَجُلٍ نَسِيَ أَنْ يَزُورَ الْبَيْتَ حَتَّى أَصْبَحَ فَقَالَ لَا بَأْسَ أَنَا رُبَّمَا أَخَّرْتُهُ حَتَّى تَذْهَبَ أَيَّامُ التَّشْرِيقِ وَ لَكِنْ لَا يَقْرَبِ النِّسَاءَ وَ الطِّيبَ‌[1].
- **Isnad as currently extracted:**
  > وَ رَوَى عُبَيْدُ اللَّهِ بْنُ عَلِيٍّ الْحَلَبِيُّ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ‌ عَنْ رَجُلٍ نَسِيَ أَنْ يَزُورَ الْبَيْتَ حَتَّى أَصْبَحَ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عبید الله بن علی الحلبی | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 133 · `faqih-2778` — CLARIFIED
- Transmitters (student → teacher): عبيد الله بن علي الحلبي → ابي عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى عُبَيْدُ اللَّهِ بْنُ عَلِيٍّ الْحَلَبِيُّ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ‌ عَنْ رَجُلٍ نَسِيَ أَنْ يَزُورَ الْبَيْتَ حَتَّى أَصْبَحَ"
- Mursal opening: al-Ṣadūq → عبيد الله بن علي الحلبي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 134 · `faqih-2779`
- **Location:** vol. 2, p. 389 · seq 2787 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى هِشَامُ بْنُ سَالِمٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَمَّنْ نَسِيَ زِيَارَةَ الْبَيْتِ حَتَّى يَرْجِعَ إِلَى أَهْلِهِ فَقَالَ لَا يَضُرُّهُ إِذَا كَانَ قَدْ قَضَى مَنَاسِكَهُ‌[2].
- **Isnad as currently extracted:**
  > وَ رَوَى هِشَامُ بْنُ سَالِمٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَمَّنْ نَسِيَ زِيَارَةَ الْبَيْتِ حَتَّى يَرْجِعَ إِلَى أَهْلِهِ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | هشام بن سالم | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 134 · `faqih-2779` — CLARIFIED
- Transmitters (student → teacher): هشام بن سالم → ابي عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى هِشَامُ بْنُ سَالِمٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَمَّنْ نَسِيَ زِيَارَةَ الْبَيْتِ حَتَّى يَرْجِعَ إِلَى أَهْلِهِ"
- Mursal opening: al-Ṣadūq → هشام بن سالم; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 135 · `faqih-2781`
- **Location:** vol. 2, p. 389 · seq 2789 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ لَهُ رَجُلٌ نَسِيَ طَوَافَ النِّسَاءِ حَتَّى رَجَعَ إِلَى أَهْلِهِ قَالَ يَأْمُرُ أَنْ يُقْضَى عَنْهُ إِنْ لَمْ يَحُجَّ فَإِنَّهُ لَا تَحِلُّ لَهُ النِّسَاءُ حَتَّى يَطُوفَ بِالْبَيْتِ‌[3].
- **Isnad as currently extracted:**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن عمار | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 135 · `faqih-2781` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ رَجُلٌ نَسِيَ طَوَافَ النِّسَاءِ حَتَّى رَجَعَ إِلَى"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 136 · `faqih-2783`
- **Location:** vol. 2, p. 390 · seq 2791 · chain 1
- **Flags:** `mursal_opening`, `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > وَ رَوَى ابْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ رِئَابٍ عَنْ حُمْرَانَ بْنِ أَعْيَنَ عَنْ أَبِي جَعْفَرٍ ع‌ فِي رَجُلٍ كَانَ عَلَيْهِ طَوَافُ النِّسَاءِ وَحْدَهُ فَطَافَ مِنْهُ خَمْسَةَ أَشْوَاطٍ بِالْبَيْتِ ثُمَّ غَمَزَهُ بَطْنُهُ فَخَافَ أَنْ يَبْدُرَهُ فَخَرَجَ إِلَى مَنْزِلِهِ فَنَفَضَ‌[2] ثُمَّ غَشِيَ جَارِيَتَهُ قَالَ يَغْتَسِلُ ثُمَّ يَرْجِعُ فَيَطُوفُ بِالْبَيْتِ تَمَامَ مَا بَقِيَ عَلَيْهِ مِنْ طَوَافِهِ وَ يَسْتَغْفِرُ رَبَّهُ وَ لَا يَعُودُ[3].
- **Isnad as currently extracted:**
  > وَ رَوَى ابْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ رِئَابٍ عَنْ حُمْرَانَ بْنِ أَعْيَنَ عَنْ أَبِي جَعْفَرٍ ع‌ فِي رَجُلٍ كَانَ عَلَيْهِ طَوَافُ النِّسَاءِ وَحْدَهُ فَطَافَ مِنْهُ خَمْسَةَ أَشْوَاطٍ بِالْبَيْتِ ثُمَّ غَمَزَهُ بَطْنُهُ فَخَافَ أَنْ يَبْدُرَهُ فَخَرَجَ إِلَى مَنْزِلِهِ فَنَفَضَ‌[2] ثُمَّ غَشِيَ جَارِيَتَهُ قَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن محبوب | روی |  |
  | 1 | named_narrator | علی بن رئاب | عن |  |
  | 2 | named_narrator | حمران بن اعین | عن |  |
  | 3 | named_narrator | ابی جعفر ع فی رجل کان علیه طواف النساء وحده فطاف منه خمسة اشواط بالبیت ثم غمزه بطنه فخاف ان یبدره فخرج الی منزله فنفض ثم غشی جاریته | عن |  |

### Chain 136 · `faqih-2783` — CLARIFIED
- Transmitters (student → teacher): ابن محبوب → علي بن رئاب → حمران بن أعين → أبو جعفر ع
- Corrected isnad (Arabic): «وَ رَوَى ابْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ رِئَابٍ عَنْ حُمْرَانَ بْنِ أَعْيَنَ عَنْ أَبِي جَعْفَرٍ ع‌»
- Isnad ends / matn begins at: "فِي رَجُلٍ كَانَ عَلَيْهِ طَوَافُ النِّسَاءِ وَحْدَهُ فَطَافَ مِنْهُ"
- Mursal opening: al-Ṣadūq → ابن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name.

---

### Chain 137 · `faqih-2788`
- **Location:** vol. 2, p. 392 · seq 2796 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى يُونُسُ بْنُ يَعْقُوبَ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَأَيْتُ فِي ثَوْبِي شَيْئاً مِنْ دَمٍ وَ أَنَا أَطُوفُ قَالَ فَاعْرِفِ الْمَوْضِعَ ثُمَّ اخْرُجْ فَاغْسِلْهُ ثُمَّ عُدْ فَابْنِ‌
- **Isnad as currently extracted:**
  > رَوَى يُونُسُ بْنُ يَعْقُوبَ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | یونس بن یعقوب | روی |  |

### Chain 137 · `faqih-2788` — CLARIFIED
- Transmitters (student → teacher): يونس بن يعقوب → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى يُونُسُ بْنُ يَعْقُوبَ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَأَيْتُ فِي ثَوْبِي شَيْئاً"
- Mursal opening: al-Ṣadūq → يونس بن يعقوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 138 · `faqih-2789`
- **Location:** vol. 2, p. 393 · seq 2797 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى ابْنُ الْمُغِيرَةِ عَنْ عَبْدِ اللَّهِ بْنِ سِنَانٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ كَانَ فِي طَوَافِ النِّسَاءِ[2] فَأُقِيمَتِ الصَّلَاةُ- قَالَ يُصَلِّي مَعَهُمُ الْفَرِيضَةَ[3] فَإِذَا فَرَغَ بَنَى مِنْ حَيْثُ بَلَغَ‌[4].
- **Isnad as currently extracted:**
  > وَ رَوَى ابْنُ الْمُغِيرَةِ عَنْ عَبْدِ اللَّهِ بْنِ سِنَانٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن المغیرة | روی |  |
  | 1 | named_narrator | عبد الله بن سنان | عن |  |

### Chain 138 · `faqih-2789` — CLARIFIED
- Transmitters (student → teacher): ابن المغيرة → عبد الله بن سنان → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى ابْنُ الْمُغِيرَةِ عَنْ عَبْدِ اللَّهِ بْنِ سِنَانٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ كَانَ فِي"
- Mursal opening: al-Ṣadūq → ابن المغيرة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 139 · `faqih-2790`
- **Location:** vol. 2, p. 393 · seq 2798 · chain 1
- **Flags:** `matn_spill`
- **Full report (Arabic):**
  > وَ فِي نَوَادِرِ ابْنِ أَبِي عُمَيْرٍ عَنْ بَعْضِ أَصْحَابِنَا عَنْ أَحَدِهِمَا ع أَنَّهُ‌
قَالَ‌ فِي الرَّجُلِ يَطُوفُ فَتَعْرِضُ لَهُ الْحَاجَةُ قَالَ لَا بَأْسَ بِأَنْ يَذْهَبَ فِي حَاجَتِهِ أَوْ حَاجَةِ غَيْرِهِ وَ يَقْطَعَ الطَّوَافَ وَ إِذَا أَرَادَ أَنْ يَسْتَرِيحَ فِي طَوَافِهِ‌[1] وَ يَقْعُدَ فَلَا بَأْسَ بِهِ فَإِذَا رَجَعَ بَنَى عَلَى طَوَافِهِ وَ إِنْ كَانَ أَقَلَّ مِنَ النِّصْفِ‌[2].
- **Isnad as currently extracted:**
  > وَ فِي نَوَادِرِ ابْنِ أَبِي عُمَيْرٍ عَنْ بَعْضِ أَصْحَابِنَا عَنْ أَحَدِهِمَا ع أَنَّهُ‌ قَالَ‌ فِي الرَّجُلِ يَطُوفُ فَتَعْرِضُ لَهُ الْحَاجَةُ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | فی نوادر ابن ابی عمیر |  |  |
  | 1 | collective_phrase | بعض اصحابنا | عن |  |
  | 2 | imam | احدهما ع | عن | ambiguous |

### Chain 139 · `faqih-2790` — CLARIFIED
- Transmitters (student → teacher): في نوادر ابن ابي عمير → بعض اصحابنا → احدهما ع
- Corrected isnad (Arabic): «وَ فِي نَوَادِرِ ابْنِ أَبِي عُمَيْرٍ عَنْ بَعْضِ أَصْحَابِنَا عَنْ أَحَدِهِمَا ع أَنَّهُ‌ قَالَ‌»
- Isnad ends / matn begins at: "فِي الرَّجُلِ يَطُوفُ فَتَعْرِضُ لَهُ الْحَاجَةُ قَالَ لَا بَأْسَ"
- Mursal opening: al-Ṣadūq → في نوادر ابن ابي عمير; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 140 · `faqih-2791`
- **Location:** vol. 2, p. 394 · seq 2799 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ قَالَ‌ سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنِ الرَّجُلِ يَكُونُ فِي الطَّوَافِ قَدْ طَافَ بَعْضَهُ وَ بَقِيَ عَلَيْهِ بَعْضُهُ‌[3] فَيَخْرُجُ مِنَ الطَّوَافِ إِلَى الْحِجْرِ أَوْ إِلَى بَعْضِ الْمَسْجِدِ إِذَا كَانَ لَمْ يُوتِرْ فَيُوتِرُ فَيَرْجِعُ فَيُتِمُّ طَوَافَهُ أَ فَتَرَى ذَلِكَ أَفْضَلُ أَمْ يُتِمُّ الطَّوَافَ ثُمَّ يُوتِرُ وَ إِنْ أَسْفَرَ بَعْضَ الْإِسْفَارِ فَقَالَ ابْدَأْ بِالْوَتْرِ وَ اقْطَعِ الطَّوَافَ إِذَا خِفْتَ ثُمَّ ائْتِ الطَّوَافَ‌[4].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن عبد الرحمن بن الحجاج | روی |  |

### Chain 140 · `faqih-2791` — CLARIFIED
- Transmitters (student → teacher): عبد الرحمن بن الحجاج → ابا ابراهيم ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنِ الرَّجُلِ يَكُونُ فِي الطَّوَافِ"
- Mursal opening: al-Ṣadūq → عبد الرحمن بن الحجاج; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 141 · `faqih-2793`
- **Location:** vol. 2, p. 395 · seq 2801 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى حَمَّادُ بْنُ عُثْمَانَ عَنْ حَبِيبِ بْنِ مُظَاهِرٍ[1] قَالَ‌ ابْتَدَأْتُ فِي طَوَافِ الْفَرِيضَةِ فَطُفْتُ شَوْطاً وَاحِداً فَإِذَا إِنْسَانٌ قَدْ أَصَابَ أَنْفِي فَأَدْمَاهُ فَخَرَجْتُ فَغَسَلْتُهُ ثُمَّ جِئْتُ فَابْتَدَأْتُ الطَّوَافَ فَذَكَرْتُ ذَلِكَ لِأَبِي عَبْدِ اللَّهِ ع فَقَالَ بِئْسَمَا صَنَعْتَ كَانَ يَنْبَغِي لَكَ أَنْ تَبْنِيَ عَلَى مَا طُفْتَ ثُمَّ قَالَ أَمَا إِنَّهُ لَيْسَ عَلَيْكَ شَيْ‌ءٌ[2].
- **Isnad as currently extracted:**
  > وَ رَوَى حَمَّادُ بْنُ عُثْمَانَ عَنْ حَبِيبِ بْنِ مُظَاهِرٍ[1] قَالَ‌ ابْتَدَأْتُ فِي طَوَافِ الْفَرِيضَةِ فَطُفْتُ شَوْطاً وَاحِداً فَإِذَا إِنْسَانٌ قَدْ أَصَابَ أَنْفِي فَأَدْمَاهُ فَخَرَجْتُ فَغَسَلْتُهُ ثُمَّ جِئْتُ فَابْتَدَأْتُ الطَّوَافَ فَذَكَرْتُ ذَلِكَ لِأَبِي عَبْدِ اللَّهِ ع فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حماد بن عثمان | روی |  |
  | 1 | named_narrator | حبیب بن مظاهر | عن |  |

### Chain 141 · `faqih-2793` — CLARIFIED
- Transmitters (student → teacher): حماد بن عثمان → حبيب بن مظاهر
- Corrected isnad (Arabic): «وَ رَوَى حَمَّادُ بْنُ عُثْمَانَ عَنْ حَبِيبِ بْنِ مُظَاهِرٍ[1] قَالَ‌»
- Isnad ends / matn begins at: "ابْتَدَأْتُ فِي طَوَافِ الْفَرِيضَةِ فَطُفْتُ شَوْطاً وَاحِداً فَإِذَا إِنْسَانٌ"
- Mursal opening: al-Ṣadūq → حماد بن عثمان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 142 · `faqih-2794`
- **Location:** vol. 2, p. 395 · seq 2802 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ صَفْوَانَ الْجَمَّالِ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الرَّجُلُ يَأْتِي أَخَاهُ وَ هُوَ فِي الطَّوَافِ فَقَالَ يَخْرُجُ مَعَهُ فِي حَاجَتِهِ ثُمَّ يَرْجِعُ وَ يَبْنِي عَلَى طَوَافِهِ‌[3].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ صَفْوَانَ الْجَمَّالِ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن صفوان الجمال | روی |  |

### Chain 142 · `faqih-2794` — CLARIFIED
- Transmitters (student → teacher): صفوان الجمال → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ صَفْوَانَ الْجَمَّالِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الرَّجُلُ يَأْتِي أَخَاهُ وَ"
- Mursal opening: al-Ṣadūq → صفوان الجمال; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 143 · `faqih-2795`
- **Location:** vol. 2, p. 395 · seq 2803 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى صَفْوَانُ بْنُ يَحْيَى عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ طَافَ بِالْكَعْبَةِ ثُمَّ خَرَجَ فَطَافَ بَيْنَ الصَّفَا وَ الْمَرْوَةِ فَبَيْنَا هُوَ يَطُوفُ إِذْ ذَكَرَ أَنَّهُ قَدْ تَرَكَ بَعْضَ طَوَافِهِ بِالْبَيْتِ قَالَ يَرْجِعُ إِلَى الْبَيْتِ وَ يُتِمُّ طَوَافَهُ ثُمَّ يَرْجِعُ إِلَى الصَّفَا وَ الْمَرْوَةِ فَيُتِمُّ مَا بَقِيَ‌[4].
- **Isnad as currently extracted:**
  > رَوَى صَفْوَانُ بْنُ يَحْيَى عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان بن یحیی | روی |  |
  | 1 | named_narrator | اسحاق بن عمار | عن |  |

### Chain 143 · `faqih-2795` — CLARIFIED
- Transmitters (student → teacher): صفوان بن يحيي → اسحاق بن عمار
- Corrected isnad (Arabic): «رَوَى صَفْوَانُ بْنُ يَحْيَى عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ طَافَ بِالْكَعْبَةِ ثُمَّ"
- Mursal opening: al-Ṣadūq → صفوان بن يحيي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 144 · `faqih-2796`
- **Location:** vol. 2, p. 396 · seq 2804 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ أَبِي أَيُّوبَ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ طَافَ بِالْبَيْتِ ثَمَانِيَةَ أَشْوَاطٍ طَوَافَ الْفَرِيضَةِ قَالَ فَلْيَضُمَّ إِلَيْهَا سِتّاً ثُمَّ يُصَلِّي أَرْبَعَ رَكَعَاتٍ‌[1].
- وَ فِي خَبَرٍ آخَرَ[2] إِنَّ الْفَرِيضَةَ هِيَ الطَّوَافُ الثَّانِي وَ الرَّكْعَتَانِ الْأُولَيَانِ لِطَوَافِ الْفَرِيضَةِ وَ الرَّكْعَتَانِ الْأُخْرَيَانِ وَ الطَّوَافُ الْأَوَّلُ تَطَوُّعٌ‌[3].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ أَبِي أَيُّوبَ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن ابی ایوب | روی |  |

### Chain 144 · `faqih-2796` — CLARIFIED
- Transmitters (student → teacher): ابي ايوب → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ أَبِي أَيُّوبَ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ طَافَ بِالْبَيْتِ ثَمَانِيَةَ"
- Mursal opening: al-Ṣadūq → ابي ايوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 145 · `faqih-2797`
- **Location:** vol. 2, p. 396 · seq 2805 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`
- **Full report (Arabic):**
  > وَ فِي رِوَايَةِ الْقَاسِمِ بْنِ مُحَمَّدٍ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سُئِلَ وَ أَنَا حَاضِرٌ عَنْ رَجُلٍ طَافَ بِالْبَيْتِ ثَمَانِيَةَ أَشْوَاطٍ فَقَالَ نَافِلَةً أَوْ فَرِيضَةً فَقَالَ فَرِيضَةً قَالَ يُضِيفُ إِلَيْهَا سِتَّةً فَإِذَا فَرَغَ صَلَّى رَكْعَتَيْنِ عِنْدَ مَقَامِ إِبْرَاهِيمَ ع ثُمَّ يَخْرُجُ إِلَى الصَّفَا وَ الْمَرْوَةِ وَ يَطُوفُ بِهِمَا فَإِذَا فَرَغَ صَلَّى رَكْعَتَيْنِ أُخْرَاوَيْنِ فَكَانَ طَوَافَ نَافِلَةٍ وَ طَوَافَ فَرِيضَةٍ.
- **Isnad as currently extracted:**
  > وَ فِي رِوَايَةِ الْقَاسِمِ بْنِ مُحَمَّدٍ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سُئِلَ وَ أَنَا حَاضِرٌ عَنْ رَجُلٍ طَافَ بِالْبَيْتِ ثَمَانِيَةَ أَشْوَاطٍ فَقَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | فی روایة القاسم بن محمد |  |  |
  | 1 | named_narrator | علی بن ابی حمزة | عن |  |
  | 2 | imam | ابی عبد الله ع | عن |  |

### Chain 145 · `faqih-2797` — CLARIFIED
- Transmitters (student → teacher): القاسم بن محمد → علي بن ابي حمزة → ابي عبد الله ع
- Corrected isnad (Arabic): «وَ فِي رِوَايَةِ الْقَاسِمِ بْنِ مُحَمَّدٍ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سُئِلَ وَ أَنَا حَاضِرٌ عَنْ رَجُلٍ طَافَ بِالْبَيْتِ ثَمَانِيَةَ"
- Mursal opening: al-Ṣadūq → القاسم بن محمد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim.

---

### Chain 146 · `faqih-2799`
- **Location:** vol. 2, p. 397 · seq 2807 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى عَنْهُ رِفَاعَةُ أَنَّهُ قَالَ‌ فِي رَجُلٍ لَا يَدْرِي سِتَّةً طَافَ أَوْ سَبْعَةً قَالَ يَبْنِي عَلَى يَقِينِهِ‌[3].
- **Isnad as currently extracted:**
  > وَ رَوَى عَنْهُ رِفَاعَةُ أَنَّهُ قَالَ‌ فِي رَجُلٍ لَا يَدْرِي سِتَّةً طَافَ أَوْ سَبْعَةً قَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عنه رفاعة | روی |  |

### Chain 146 · `faqih-2799` — CLARIFIED
- Transmitters (student → teacher): رفاعة → أبو عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى عَنْهُ رِفَاعَةُ أَنَّهُ قَالَ‌»
- Isnad ends / matn begins at: "فِي رَجُلٍ لَا يَدْرِي سِتَّةً طَافَ أَوْ سَبْعَةً قَالَ"
- Mursal opening: al-Ṣadūq → رفاعة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: Wasāʾil expands the continuation as «بِإِسْنَادِهِ عَنْ رِفَاعَةَ، عَنْ أَبِي عَبْدِ اللَّهِ ع». Source: [Wasāʾil al-Shīʿa, vol. 13, report 17948](https://alkafeel.net/islamiclibrary/hadith/wasael-13/wasael-13/v18.html).
---

### Chain 147 · `faqih-2801`
- **Location:** vol. 2, p. 398 · seq 2809 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى ابْنُ مُسْكَانَ عَنِ الْحَلَبِيِّ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ طَافَ بِالْبَيْتِ فَاخْتَصَرَ شَوْطاً وَاحِداً فِي الْحِجْرِ كَيْفَ يَصْنَعُ قَالَ يُعِيدُ الطَّوَافَ الْوَاحِدَ[2].
- **Isnad as currently extracted:**
  > رَوَى ابْنُ مُسْكَانَ عَنِ الْحَلَبِيِّ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن مسکان | روی |  |
  | 1 | named_narrator | الحلبی | عن |  |

### Chain 147 · `faqih-2801` — CLARIFIED
- Transmitters (student → teacher): ابن مسكان → الحلبي → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى ابْنُ مُسْكَانَ عَنِ الْحَلَبِيِّ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ طَافَ بِالْبَيْتِ فَاخْتَصَرَ"
- Mursal opening: al-Ṣadūq → ابن مسكان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 148 · `faqih-2803`
- **Location:** vol. 2, p. 399 · seq 2811 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى الْحُسَيْنُ بْنُ سَعِيدٍ عَنْ إِبْرَاهِيمَ بْنِ سُفْيَانَ قَالَ‌ كَتَبْتُ إِلَى أَبِي الْحَسَنِ الرِّضَا ع امْرَأَةٌ طَافَتْ طَوَافَ الْحَجِّ فَلَمَّا كَانَتْ فِي الشَّوْطِ السَّابِعِ اخْتَصَرَتْ فَطَافَتْ فِي الْحِجْرِ وَ صَلَّتْ رَكْعَتَيِ الْفَرِيضَةِ وَ سَعَتْ وَ طَافَتْ طَوَافَ النِّسَاءِ ثُمَّ أَتَتْ مِنًى فَكَتَبَ ع تُعِيدُ[2].
- **Isnad as currently extracted:**
  > وَ رَوَى الْحُسَيْنُ بْنُ سَعِيدٍ عَنْ إِبْرَاهِيمَ بْنِ سُفْيَانَ قَالَ‌ كَتَبْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسین بن سعید | روی |  |
  | 1 | named_narrator | ابراهیم بن سفیان | عن |  |

### Chain 148 · `faqih-2803` — CLARIFIED
- Transmitters (student → teacher): الحسين بن سعيد → ابراهيم بن سفيان → ابي الحسن الرضا ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى الْحُسَيْنُ بْنُ سَعِيدٍ عَنْ إِبْرَاهِيمَ بْنِ سُفْيَانَ قَالَ‌»
- Isnad ends / matn begins at: "كَتَبْتُ إِلَى أَبِي الْحَسَنِ الرِّضَا ع امْرَأَةٌ طَافَتْ طَوَافَ"
- Mursal opening: al-Ṣadūq → الحسين بن سعيد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 149 · `faqih-2804`
- **Location:** vol. 2, p. 399 · seq 2812 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى أَبَانٌ عَنْ مُحَمَّدِ بْنِ عَلِيٍّ الْحَلَبِيِّ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الطَّوَافِ خَلْفَ الْمَقَامِ قَالَ مَا أُحِبُّ ذَلِكَ وَ مَا أَرَى بِهِ بَأْساً فَلَا تَفْعَلْهُ إِلَّا أَنْ لَا تَجِدَ مِنْهُ بُدّاً[4].
- **Isnad as currently extracted:**
  > رَوَى أَبَانٌ عَنْ مُحَمَّدِ بْنِ عَلِيٍّ الْحَلَبِيِّ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابان | روی |  |
  | 1 | named_narrator | محمد بن علی الحلبی | عن |  |

### Chain 149 · `faqih-2804` — CLARIFIED
- Transmitters (student → teacher): ابان → محمد بن علي الحلبي
- Corrected isnad (Arabic): «رَوَى أَبَانٌ عَنْ مُحَمَّدِ بْنِ عَلِيٍّ الْحَلَبِيِّ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الطَّوَافِ خَلْفَ الْمَقَامِ"
- Mursal opening: al-Ṣadūq → ابان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 150 · `faqih-2806`
- **Location:** vol. 2, p. 400 · seq 2814 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ طَافَ الْفَرِيضَةَ وَ هُوَ عَلَى غَيْرِ طُهْرٍ قَالَ يَتَوَضَّأُ وَ يُعِيدُ طَوَافَهُ فَإِنْ كَانَ تَطَوُّعاً تَوَضَّأَ[2] وَ صَلَّى رَكْعَتَيْنِ.
- **Isnad as currently extracted:**
  > وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ طَافَ الْفَرِيضَةَ وَ هُوَ عَلَى غَيْرِ طُهْرٍ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | العلاء | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |
  | 2 | imam | احدهما ع | عن | ambiguous |

### Chain 150 · `faqih-2806` — CLARIFIED
- Transmitters (student → teacher): العلاء → محمد بن مسلم → احدهما ع
- Corrected isnad (Arabic): «وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ طَافَ الْفَرِيضَةَ وَ هُوَ عَلَى غَيْرِ"
- Mursal opening: al-Ṣadūq → العلاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 151 · `faqih-2806`
- **Location:** vol. 2, p. 400 · seq 2814 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ طَافَ الْفَرِيضَةَ وَ هُوَ عَلَى غَيْرِ طُهْرٍ قَالَ يَتَوَضَّأُ وَ يُعِيدُ طَوَافَهُ فَإِنْ كَانَ تَطَوُّعاً تَوَضَّأَ[2] وَ صَلَّى رَكْعَتَيْنِ.
- **Isnad as currently extracted:**
  > وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ طَافَ الْفَرِيضَةَ وَ هُوَ عَلَى غَيْرِ طُهْرٍ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | العلاء | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |
  | 2 | imam | احدهما ع | عن | ambiguous |

### Chain 151 · `faqih-2806` — CLARIFIED
- Transmitters (student → teacher): العلاء → محمد بن مسلم → احدهما ع
- Corrected isnad (Arabic): «وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ طَافَ الْفَرِيضَةَ وَ هُوَ عَلَى غَيْرِ"
- Mursal opening: al-Ṣadūq → العلاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 152 · `faqih-2808`
- **Location:** vol. 2, p. 400 · seq 2816 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى صَفْوَانُ عَنْ يَحْيَى الْأَزْرَقِ قَالَ‌ قُلْتُ لِأَبِي الْحَسَنِ ع رَجُلٌ سَعَى بَيْنَ الصَّفَا وَ الْمَرْوَةِ فَسَعَى ثَلَاثَةَ أَشْوَاطٍ أَوْ أَرْبَعَةً ثُمَّ بَالَ ثُمَّ أَتَمَّ سَعْيَهُ بِغَيْرِ وُضُوءٍ فَقَالَ لَا بَأْسَ وَ لَوْ أَتَمَّ مَنَاسِكَهُ بِوُضُوءٍ كَانَ أَحَبَّ إِلَيَ‌[4].
- **Isnad as currently extracted:**
  > وَ رَوَى صَفْوَانُ عَنْ يَحْيَى الْأَزْرَقِ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان | روی |  |
  | 1 | named_narrator | یحیی الازرق | عن |  |

### Chain 152 · `faqih-2808` — CLARIFIED
- Transmitters (student → teacher): صفوان → يحيي الازرق → ابي الحسن ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى صَفْوَانُ عَنْ يَحْيَى الْأَزْرَقِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي الْحَسَنِ ع رَجُلٌ سَعَى بَيْنَ الصَّفَا وَ"
- Mursal opening: al-Ṣadūq → صفوان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 153 · `faqih-2819`
- **Location:** vol. 2, p. 404 · seq 2827 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى صَفْوَانُ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ طَافَ بِالْكَعْبَةِ ثُمَّ خَرَجَ فَطَافَ بَيْنَ الصَّفَا وَ الْمَرْوَةِ فَبَيْنَا هُوَ يَطُوفُ إِذْ ذَكَرَ أَنَّهُ قَدْ تَرَكَ مِنْ طَوَافِهِ بِالْبَيْتِ فَقَالَ يَرْجِعُ إِلَى الْبَيْتِ فَيُتِمُّ طَوَافَهُ ثُمَّ يَرْجِعُ إِلَى الصَّفَا وَ الْمَرْوَةِ فَيُتِمُّ مَا بَقِيَ قُلْتُ فَإِنَّهُ بَدَأَ بِالصَّفَا وَ الْمَرْوَةِ قَبْلَ أَنْ يَبْدَأَ بِالْبَيْتِ قَالَ يَأْتِي الْبَيْتَ فَيَطُوفُ بِهِ ثُمَّ يَسْتَأْنِفُ طَوَافَهُ بَيْنَ الصَّفَا وَ الْمَرْوَةِ قُلْتُ فَمَا الْفَرْقُ بَيْنَ هَذَيْنِ قَالَ لِأَنَّ هَذَا قَدْ دَخَلَ فِي شَيْ‌ءٍ مِنَ الطَّوَافِ وَ هَذَا لَمْ يَدْخُلْ فِي شَيْ‌ءٍ مِنْهُ‌[4].
- **Isnad as currently extracted:**
  > رَوَى صَفْوَانُ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان | روی |  |
  | 1 | named_narrator | اسحاق بن عمار | عن |  |

### Chain 153 · `faqih-2819` — CLARIFIED
- Transmitters (student → teacher): صفوان → اسحاق بن عمار
- Corrected isnad (Arabic): «رَوَى صَفْوَانُ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ طَافَ بِالْكَعْبَةِ ثُمَّ"
- Mursal opening: al-Ṣadūq → صفوان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 154 · `faqih-2822`
- **Location:** vol. 2, p. 405 · seq 2830 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ طَافَ بِالْبَيْتِ فَأَعْيَا أَ يُؤَخِّرُ الطَّوَافَ بَيْنَ الصَّفَا وَ الْمَرْوَةِ إِلَى غَدٍ قَالَ لَا[3].
- **Isnad as currently extracted:**
  > وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ طَافَ بِالْبَيْتِ فَأَعْيَا أَ يُؤَخِّرُ الطَّوَافَ بَيْنَ الصَّفَا وَ الْمَرْوَةِ إِلَى غَدٍ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | العلاء | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |
  | 2 | imam | احدهما ع | عن | ambiguous |

### Chain 154 · `faqih-2822` — CLARIFIED
- Transmitters (student → teacher): العلاء → محمد بن مسلم → احدهما ع
- Corrected isnad (Arabic): «وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ طَافَ بِالْبَيْتِ فَأَعْيَا أَ يُؤَخِّرُ الطَّوَافَ"
- Mursal opening: al-Ṣadūq → العلاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 155 · `faqih-2830`
- **Location:** vol. 2, p. 409 · seq 2839 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى عَاصِمُ بْنُ حُمَيْدٍ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ أَبَا جَعْفَرٍ ع عَنِ الرَّجُلِ يَطُوفُ وَ يَسْعَى ثُمَّ يَطُوفُ بِالْبَيْتِ تَطَوُّعاً قَبْلَ أَنْ يُقَصِّرَ قَالَ مَا يُعْجِبُنِي‌[2].
- **Isnad as currently extracted:**
  > رَوَى عَاصِمُ بْنُ حُمَيْدٍ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عاصم بن حمید | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |

### Chain 155 · `faqih-2830` — CLARIFIED
- Transmitters (student → teacher): عاصم بن حميد → محمد بن مسلم → ابا جعفر ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى عَاصِمُ بْنُ حُمَيْدٍ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا جَعْفَرٍ ع عَنِ الرَّجُلِ يَطُوفُ وَ يَسْعَى"
- Mursal opening: al-Ṣadūq → عاصم بن حميد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 156 · `faqih-2831`
- **Location:** vol. 2, p. 409 · seq 2840 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى صَفْوَانُ بْنُ يَحْيَى عَنْ هَيْثَمٍ التَّمِيمِيِّ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ كَانَتْ مَعَهُ صَاحِبَتُهُ لَا تَسْتَطِيعُ الْقِيَامَ عَلَى رِجْلِهَا فَحَمَلَهَا زَوْجُهَا فِي مَحْمِلٍ فَطَافَ بِهَا طَوَافَ الْفَرِيضَةِ بِالْبَيْتِ وَ بِالصَّفَا وَ الْمَرْوَةِ أَ يُجْزِيهِ ذَلِكَ الطَّوَافُ عَنْ نَفْسِهِ طَوَافُهُ بِهَا فَقَالَ إِيهاً وَ اللَّهِ إِذاً[3].
- **Isnad as currently extracted:**
  > وَ رَوَى صَفْوَانُ بْنُ يَحْيَى عَنْ هَيْثَمٍ التَّمِيمِيِّ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان بن یحیی | روی |  |
  | 1 | named_narrator | هیثم التمیمی | عن |  |

### Chain 156 · `faqih-2831` — CLARIFIED
- Transmitters (student → teacher): صفوان بن يحيي → هيثم التميمي → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى صَفْوَانُ بْنُ يَحْيَى عَنْ هَيْثَمٍ التَّمِيمِيِّ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ كَانَتْ مَعَهُ صَاحِبَتُهُ"
- Mursal opening: al-Ṣadūq → صفوان بن يحيي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 157 · `faqih-2838`
- **Location:** vol. 2, p. 411 · seq 2847 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى عَلِيُّ بْنُ النُّعْمَانِ عَنْ يَحْيَى الْأَزْرَقِ قَالَ‌ قُلْتُ لِأَبِي الْحَسَنِ ع إِنِّي طُفْتُ أَرْبَعَةَ أَسَابِيعَ فَعَيِيتُ أَ فَأُصَلِّي رَكَعَاتِهَا وَ أَنَا جَالِسٌ‌[5] قَالَ لَا قُلْتُ وَ كَيْفَ يُصَلِّي الرَّجُلُ صَلَاةَ اللَّيْلِ إِذَا أَعْيَا أَوْ وَجَدَ فَتْرَةً وَ هُوَ جَالِسٌ فَقَالَ‌
يَطُوفُ الرَّجُلُ جَالِساً[1] فَقُلْتُ لَا قَالَ فَتُصَلِّيهِمَا وَ أَنْتَ قَائِمٌ.
- **Isnad as currently extracted:**
  > وَ رَوَى عَلِيُّ بْنُ النُّعْمَانِ عَنْ يَحْيَى الْأَزْرَقِ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن النعمان | روی |  |
  | 1 | named_narrator | یحیی الازرق | عن |  |

### Chain 157 · `faqih-2838` — CLARIFIED
- Transmitters (student → teacher): علي بن النعمان → يحيي الازرق → ابي الحسن ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى عَلِيُّ بْنُ النُّعْمَانِ عَنْ يَحْيَى الْأَزْرَقِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي الْحَسَنِ ع إِنِّي طُفْتُ أَرْبَعَةَ أَسَابِيعَ فَعَيِيتُ"
- Mursal opening: al-Ṣadūq → علي بن النعمان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 158 · `faqih-2842`
- **Location:** vol. 2, p. 412 · seq 2851 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى صَفْوَانُ عَنْ عَبْدِ الْحَمِيدِ بْنِ سَعْدٍ قَالَ‌ سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنْ بَابِ الصَّفَا[5] فَقُلْتُ إِنَّ أَصْحَابَنَا قَدِ اخْتَلَفُوا فِيهِ فَبَعْضُهُمْ يَقُولُ الَّذِي يَلِي السِّقَايَةَ وَ بَعْضُهُمْ يَقُولُ الَّذِي يَسْتَقْبِلُ الْحَجَرَ الْأَسْوَدَ فَقَالَ هُوَ الَّذِي يَسْتَقْبِلُ الْحَجَرَ وَ الَّذِي‌
يَلِي السِّقَايَةَ مُحْدَثٌ صَنَعَهُ دَاوُدُ[1] وَ فَتَحَهُ دَاوُدُ.
- **Isnad as currently extracted:**
  > وَ رَوَى صَفْوَانُ عَنْ عَبْدِ الْحَمِيدِ بْنِ سَعْدٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان | روی |  |
  | 1 | named_narrator | عبد الحمید بن سعد | عن |  |

### Chain 158 · `faqih-2842` — CLARIFIED
- Transmitters (student → teacher): صفوان → عبد الحميد بن سعد → ابا ابراهيم ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى صَفْوَانُ عَنْ عَبْدِ الْحَمِيدِ بْنِ سَعْدٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنْ بَابِ الصَّفَا[5] فَقُلْتُ إِنَّ"
- Mursal opening: al-Ṣadūq → صفوان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 159 · `faqih-2843`
- **Location:** vol. 2, p. 413 · seq 2852 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ نَسِيَ أَنْ يَطُوفُ بَيْنَ الصَّفَا وَ الْمَرْوَةِ قَالَ يُطَافُ عَنْهُ‌[2].
- **Isnad as currently extracted:**
  > رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ نَسِيَ أَنْ يَطُوفُ بَيْنَ الصَّفَا وَ الْمَرْوَةِ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | العلاء | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |
  | 2 | imam | احدهما ع | عن | ambiguous |

### Chain 159 · `faqih-2843` — CLARIFIED
- Transmitters (student → teacher): العلاء → محمد بن مسلم → احدهما ع
- Corrected isnad (Arabic): «رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ نَسِيَ أَنْ يَطُوفُ بَيْنَ الصَّفَا وَ"
- Mursal opening: al-Ṣadūq → العلاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 160 · `faqih-2843`
- **Location:** vol. 2, p. 413 · seq 2852 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ نَسِيَ أَنْ يَطُوفُ بَيْنَ الصَّفَا وَ الْمَرْوَةِ قَالَ يُطَافُ عَنْهُ‌[2].
- **Isnad as currently extracted:**
  > رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ نَسِيَ أَنْ يَطُوفُ بَيْنَ الصَّفَا وَ الْمَرْوَةِ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | العلاء | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |
  | 2 | imam | احدهما ع | عن | ambiguous |

### Chain 160 · `faqih-2843` — CLARIFIED
- Transmitters (student → teacher): العلاء → محمد بن مسلم → احدهما ع
- Corrected isnad (Arabic): «رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ نَسِيَ أَنْ يَطُوفُ بَيْنَ الصَّفَا وَ"
- Mursal opening: al-Ṣadūq → العلاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 161 · `faqih-2846`
- **Location:** vol. 2, p. 416 · seq 2855 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ لَهُ الْمَرْأَةُ تَسْعَى بَيْنَ الصَّفَا وَ الْمَرْوَةِ عَلَى دَابَّةٍ أَوْ عَلَى بَعِيرٍ قَالَ لَا بَأْسَ بِذَلِكَ قَالَ وَ سَأَلْتُهُ عَنِ الرَّجُلِ يَفْعَلُ ذَلِكَ قَالَ لَا بَأْسَ بِهِ وَ الْمَشْيُ أَفْضَلُ‌[2].
- **Isnad as currently extracted:**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن عمار | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 161 · `faqih-2846` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ الْمَرْأَةُ تَسْعَى بَيْنَ الصَّفَا وَ الْمَرْوَةِ عَلَى"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 162 · `faqih-2850`
- **Location:** vol. 2, p. 417 · seq 2859 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الرَّجُلُ يَدْخُلُ فِي السَّعْيِ بَيْنَ الصَّفَا وَ الْمَرْوَةِ فَيَدْخُلُ وَقْتُ الصَّلَاةِ أَ يُخَفِّفُ أَوْ يُصَلِّي ثُمَّ يَعُودُ أَوْ يَلْبَثُ كَمَا هُوَ عَلَى حَالِهِ حَتَّى يَفْرُغَ فَقَالَ أَ وَ لَيْسَ عَلَيْهِمَا مَسْجِدٌ لَهُ‌[2] لَا بَلْ يُصَلِّي ثُمَّ يَعُودُ قُلْتُ وَ يَجْلِسُ عَلَى الصَّفَا وَ الْمَرْوَةِ قَالَ نَعَمْ‌[3].
- **Isnad as currently extracted:**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن عمار | روی |  |

### Chain 162 · `faqih-2850` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار
- Corrected isnad (Arabic): «رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الرَّجُلُ يَدْخُلُ فِي السَّعْيِ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 163 · `faqih-2851`
- **Location:** vol. 2, p. 417 · seq 2860 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى عَلِيُّ بْنُ النُّعْمَانِ وَ صَفْوَانُ عَنْ يَحْيَى الْأَزْرَقِ‌[4] قَالَ‌ سَأَلْتُ أَبَا الْحَسَنِ ع عَنِ الرَّجُلِ يَسْعَى بَيْنَ الصَّفَا وَ الْمَرْوَةِ فَيَسْعَى ثَلَاثَةَ أَشْوَاطٍ أَوْ أَرْبَعَةً فَيَلْقَاهُ الصَّدِيقُ فَيَدْعُوهُ إِلَى الْحَاجَةِ أَوْ إِلَى الطَّعَامِ قَالَ إِنْ أَجَابَهُ فَلَا بَأْسَ وَ لَكِنْ يَقْضِي حَقَّ اللَّهِ عَزَّ وَ جَلَّ أَحَبُّ إِلَيَّ مِنْ أَنْ يَقْضِيَ حَقَّ صَاحِبِهِ‌[5].
- **Isnad as currently extracted:**
  > وَ رَوَى عَلِيُّ بْنُ النُّعْمَانِ وَ صَفْوَانُ عَنْ يَحْيَى الْأَزْرَقِ‌[4] قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن النعمان | روی |  |
  | 1 | named_narrator | یحیی الازرق | عن |  |

### Chain 163 · `faqih-2851` — CLARIFIED
- Transmitters (student → teacher): علي بن النعمان → يحيي الازرق → ابا الحسن ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى عَلِيُّ بْنُ النُّعْمَانِ وَ صَفْوَانُ عَنْ يَحْيَى الْأَزْرَقِ‌[4] قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا الْحَسَنِ ع عَنِ الرَّجُلِ يَسْعَى بَيْنَ الصَّفَا"
- Mursal opening: al-Ṣadūq → علي بن النعمان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim.

---

### Chain 164 · `faqih-2851`
- **Location:** vol. 2, p. 417 · seq 2860 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى عَلِيُّ بْنُ النُّعْمَانِ وَ صَفْوَانُ عَنْ يَحْيَى الْأَزْرَقِ‌[4] قَالَ‌ سَأَلْتُ أَبَا الْحَسَنِ ع عَنِ الرَّجُلِ يَسْعَى بَيْنَ الصَّفَا وَ الْمَرْوَةِ فَيَسْعَى ثَلَاثَةَ أَشْوَاطٍ أَوْ أَرْبَعَةً فَيَلْقَاهُ الصَّدِيقُ فَيَدْعُوهُ إِلَى الْحَاجَةِ أَوْ إِلَى الطَّعَامِ قَالَ إِنْ أَجَابَهُ فَلَا بَأْسَ وَ لَكِنْ يَقْضِي حَقَّ اللَّهِ عَزَّ وَ جَلَّ أَحَبُّ إِلَيَّ مِنْ أَنْ يَقْضِيَ حَقَّ صَاحِبِهِ‌[5].
- **Isnad as currently extracted:**
  > وَ رَوَى عَلِيُّ بْنُ النُّعْمَانِ وَ صَفْوَانُ عَنْ يَحْيَى الْأَزْرَقِ‌[4] قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان | روی |  |
  | 1 | named_narrator | یحیی الازرق | عن |  |

### Chain 164 · `faqih-2851` — CLARIFIED
- Transmitters (student → teacher): صفوان → يحيي الازرق → ابا الحسن ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى عَلِيُّ بْنُ النُّعْمَانِ وَ صَفْوَانُ عَنْ يَحْيَى الْأَزْرَقِ‌[4] قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا الْحَسَنِ ع عَنِ الرَّجُلِ يَسْعَى بَيْنَ الصَّفَا"
- Mursal opening: al-Ṣadūq → صفوان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim.

---

### Chain 165 · `faqih-2863`
- **Location:** vol. 2, p. 422 · seq 2872 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى سَعْدُ بْنُ عَبْدِ اللَّهِ عَنْ مُوسَى بْنِ الْحَسَنِ عَنْ أَبِي عَلِيٍّ أَحْمَدَ بْنِ مُحَمَّدِ بْنِ مُطَهَّرٍ[3] قَالَ‌ كَتَبْتُ إِلَى أَبِي مُحَمَّدٍ ع إِنِّي دَفَعْتُ إِلَى سِتَّةِ أَنْفُسٍ مِائَةَ دِينَارٍ
وَ خَمْسِينَ دِينَاراً لِيَحُجُّوا بِهَا فَرَجَعُوا وَ لَمْ يَشْخَصْ بَعْضُهُمْ‌[1] وَ أَتَانِي بَعْضٌ فَذَكَرَ أَنَّهُ قَدْ أَنْفَقَ بَعْضَ الدَّنَانِيرِ وَ بَقِيَتْ بَقِيَّةٌ وَ أَنَّهُ يَرُدُّ عَلَيَّ مَا بَقِيَ وَ إِنِّي قَدْ رُمْتُ مُطَالَبَةَ مَنْ لَمْ يَأْتِنِي‌[2] بِمَا دَفَعْتُ إِلَيْهِ فَكَتَبَ ع لَا تَعَرَّضْ لِمَنْ لَمْ يَأْتِكَ وَ لَا تَأْخُذْ مِمَّنْ أَتَاكَ شَيْئاً مِمَّا يَأْتِيكَ بِهِ وَ الْأَجْرُ قَدْ وَقَعَ عَلَى اللَّهِ عَزَّ وَ جَلَ‌[3].
- **Isnad as currently extracted:**
  > وَ رَوَى سَعْدُ بْنُ عَبْدِ اللَّهِ عَنْ مُوسَى بْنِ الْحَسَنِ عَنْ أَبِي عَلِيٍّ أَحْمَدَ بْنِ مُحَمَّدِ بْنِ مُطَهَّرٍ[3] قَالَ‌ كَتَبْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | سعد بن عبد الله | روی |  |
  | 1 | named_narrator | موسی بن الحسن | عن |  |
  | 2 | named_narrator | ابی علی احمد بن محمد بن مطهر | عن |  |

### Chain 165 · `faqih-2863` — CLARIFIED
- Transmitters (student → teacher): سعد بن عبد الله → موسي بن الحسن → ابي علي احمد بن محمد بن مطهر
- Corrected isnad (Arabic): «وَ رَوَى سَعْدُ بْنُ عَبْدِ اللَّهِ عَنْ مُوسَى بْنِ الْحَسَنِ عَنْ أَبِي عَلِيٍّ أَحْمَدَ بْنِ مُحَمَّدِ بْنِ مُطَهَّرٍ[3] قَالَ‌»
- Isnad ends / matn begins at: "كَتَبْتُ إِلَى أَبِي مُحَمَّدٍ ع إِنِّي دَفَعْتُ إِلَى سِتَّةِ"
- Mursal opening: al-Ṣadūq → سعد بن عبد الله; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 166 · `faqih-2864`
- **Location:** vol. 2, p. 423 · seq 2873 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى الْبَزَنْطِيُّ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ أَخَذَ حَجَّةً مِنْ رَجُلٍ فَقُطِعَ عَلَيْهِ الطَّرِيقُ فَأَعْطَاهُ رَجُلٌ حَجَّةً أُخْرَى أَ يَجُوزُ لَهُ ذَلِكَ‌[4] فَقَالَ جَائِزٌ لَهُ ذَلِكَ مَحْسُوبٌ لِلْأَوَّلِ وَ الْآخِرُ[5] وَ مَا كَانَ يَسَعُهُ غَيْرُ الَّذِي فَعَلَ إِذَا وَجَدَ مَنْ يُعْطِيهِ الْحَجَّةَ.
- **Isnad as currently extracted:**
  > وَ رَوَى الْبَزَنْطِيُّ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ أَخَذَ حَجَّةً مِنْ رَجُلٍ فَقُطِعَ عَلَيْهِ الطَّرِيقُ فَأَعْطَاهُ رَجُلٌ حَجَّةً أُخْرَى أَ يَجُوزُ لَهُ ذَلِكَ‌[4] فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | البزنطی | روی |  |
  | 1 | imam | ابی الحسن ع | عن |  |

### Chain 166 · `faqih-2864` — CLARIFIED
- Transmitters (student → teacher): البزنطي → ابي الحسن ع
- Corrected isnad (Arabic): «وَ رَوَى الْبَزَنْطِيُّ عَنْ أَبِي الْحَسَنِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ أَخَذَ حَجَّةً مِنْ رَجُلٍ فَقُطِعَ عَلَيْهِ"
- Mursal opening: al-Ṣadūq → البزنطي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 167 · `faqih-2874`
- **Location:** vol. 2, p. 427 · seq 2883 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الصَّرُورَةِ أَ يَحُجُّ مِنْ مَالِ الزَّكَاةِ قَالَ نَعَمْ‌[2].
- **Isnad as currently extracted:**
  > وَ رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حریز | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |

### Chain 167 · `faqih-2874` — CLARIFIED
- Transmitters (student → teacher): حريز → محمد بن مسلم → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الصَّرُورَةِ أَ يَحُجُّ"
- Mursal opening: al-Ṣadūq → حريز; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 168 · `faqih-2875`
- **Location:** vol. 2, p. 428 · seq 2884 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > و روي عن معاوية بن عمار قال‌ قلت لأبي عبد الله ع الرجل يخرج في تجارة إلى مكة أو يكون له إبل فيكريها حجتُهُ نَاقِصَةٌ أَوْ تَامَّةٌ قَالَ لَا بَلْ حَجَّتُهُ تَامَّةٌ[1].
- **Isnad as currently extracted:**
  > و روي عن معاوية بن عمار قال‌ قلت
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن معاویة بن عمار | روی |  |

### Chain 168 · `faqih-2875` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار
- Corrected isnad (Arabic): «و روي عن معاوية بن عمار قال‌»
- Isnad ends / matn begins at: "قلت لأبي عبد الله ع الرجل يخرج في تجارة"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 169 · `faqih-2876`
- **Location:** vol. 2, p. 428 · seq 2885 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع حَجَّةُ الْجَمَّالِ تَامَّةٌ أَمْ نَاقِصَةٌ[2] قَالَ تَامَّةٌ قُلْتُ حَجَّةُ الْأَجِيرِ تَامَّةٌ أَوْ نَاقِصَةٌ قَالَ تَامَّةٌ[3].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن معاویة بن عمار | روی |  |

### Chain 169 · `faqih-2876` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار
- Corrected isnad (Arabic): «رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع حَجَّةُ الْجَمَّالِ تَامَّةٌ أَمْ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 170 · `faqih-2878`
- **Location:** vol. 2, p. 429 · seq 2887 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى عُمَرُ بْنُ أُذَيْنَةَ قَالَ‌ كَتَبْتُ إِلَى أَبِي عَبْدِ اللَّهِ ع أَسْأَلُهُ عَنْ رَجُلٍ حَجَّ وَ لَا يَدْرِي وَ لَا يَعْرِفُ هَذَا الْأَمْرَ ثُمَّ مَنَّ اللَّهُ عَلَيْهِ بِمَعْرِفَتِهِ وَ الدَّيْنُونَةِ بِهِ أَ عَلَيْهِ حَجَّةُ الْإِسْلَامِ قَالَ قَدْ قَضَى فَرِيضَةَ اللَّهِ عَزَّ وَ جَلَّ وَ الْحَجُّ أَحَبُّ إِلَيَ‌[3].
- **Isnad as currently extracted:**
  > رَوَى عُمَرُ بْنُ أُذَيْنَةَ قَالَ‌ كَتَبْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عمر بن اذینة | روی |  |

### Chain 170 · `faqih-2878` — CLARIFIED
- Transmitters (student → teacher): عمر بن اذينة → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى عُمَرُ بْنُ أُذَيْنَةَ قَالَ‌»
- Isnad ends / matn begins at: "كَتَبْتُ إِلَى أَبِي عَبْدِ اللَّهِ ع أَسْأَلُهُ عَنْ رَجُلٍ"
- Mursal opening: al-Ṣadūq → عمر بن اذينة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 171 · `faqih-2879`
- **Location:** vol. 2, p. 430 · seq 2888 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ أَبِي عَبْدِ اللَّهِ الْخُرَاسَانِيِّ عَنْ أَبِي جَعْفَرٍ الثَّانِي ع قَالَ‌ قُلْتُ لَهُ إِنِّي حَجَجْتُ وَ أَنَا مُخَالِفٌ وَ حَجَجْتُ حَجَّتِي هَذِهِ وَ قَدْ مَنَّ اللَّهُ عَزَّ وَ جَلَّ عَلَيَّ بِمَعْرِفَتِكُمْ وَ عَلِمْتُ أَنَّ الَّذِي كُنْتُ فِيهِ كَانَ بَاطِلًا فَمَا تَرَى فِي حَجَّتِي قَالَ اجْعَلْ هَذِهِ حَجَّةَ الْإِسْلَامِ وَ تِلْكَ نَافِلَةً[1].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ أَبِي عَبْدِ اللَّهِ الْخُرَاسَانِيِّ عَنْ أَبِي جَعْفَرٍ الثَّانِي ع قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن ابی عبد الله الخراسانی | روی |  |
  | 1 | imam | ابی جعفر الثانی ع | عن |  |

### Chain 171 · `faqih-2879` — CLARIFIED
- Transmitters (student → teacher): ابي عبد الله الخراساني → ابي جعفر الثاني ع
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ أَبِي عَبْدِ اللَّهِ الْخُرَاسَانِيِّ عَنْ أَبِي جَعْفَرٍ الثَّانِي ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ إِنِّي حَجَجْتُ وَ أَنَا مُخَالِفٌ وَ حَجَجْتُ"
- Mursal opening: al-Ṣadūq → ابي عبد الله الخراساني; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 172 · `faqih-2880`
- **Location:** vol. 2, p. 430 · seq 2889 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الرَّجُلُ يَمُرُّ مُجْتَازاً يُرِيدُ الْيَمَنَ أَوْ غَيْرَهَا مِنَ الْبُلْدَانِ وَ طَرِيقُهُ بِمَكَّةَ فَيُدْرِكُ النَّاسَ وَ هُمْ يَخْرُجُونَ إِلَى الْحَجِّ فَيَخْرُجُ مَعَهُمْ إِلَى الْمَشَاهِدِ أَ يُجْزِيهِ ذَلِكَ عَنْ حَجَّةِ الْإِسْلَامِ قَالَ نَعَمْ‌[2].
- **Isnad as currently extracted:**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن عمار | روی |  |

### Chain 172 · `faqih-2880` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار
- Corrected isnad (Arabic): «رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الرَّجُلُ يَمُرُّ مُجْتَازاً يُرِيدُ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 173 · `faqih-2882`
- **Location:** vol. 2, p. 431 · seq 2891 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنِ الْفَضْلِ بْنِ يُونُسَ قَالَ‌ سَأَلْتُ أَبَا الْحَسَنِ ع فَقُلْتُ تَكُونُ عِنْدِي الْجَوَارِي وَ أَنَا بِمَكَّةَ فَآمُرُهُنَّ أَنْ يَعْقِدْنَ بِالْحَجِ‌[1] يَوْمَ التَّرْوِيَةِ فَأَخْرُجُ بِهِنَّ فَيَشْهَدْنَ الْمَنَاسِكَ أَوْ أُخَلِّفُهُنَّ بِمَكَّةَ قَالَ فَقَالَ إِنْ خَرَجْتَ بِهِنَّ فَهُوَ أَفْضَلُ وَ إِنْ خَلَّفْتَهُنَّ عِنْدَ ثِقَةٍ فَلَا بَأْسَ فَلَيْسَ عَلَى الْمَمْلُوكِ حَجٌّ وَ لَا عُمْرَةٌ حَتَّى يُعْتَقَ‌[2].
- **Isnad as currently extracted:**
  > وَ رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنِ الْفَضْلِ بْنِ يُونُسَ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | الفضل بن یونس | عن |  |

### Chain 173 · `faqih-2882` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → الفضل بن يونس → ابا الحسن ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنِ الْفَضْلِ بْنِ يُونُسَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا الْحَسَنِ ع فَقُلْتُ تَكُونُ عِنْدِي الْجَوَارِي وَ"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 174 · `faqih-2885`
- **Location:** vol. 2, p. 432 · seq 2894 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى إِسْحَاقُ بْنُ عَمَّارٍ[1] قَالَ‌ سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنْ أُمِّ وَلَدٍ تَكُونُ لِلرَّجُلِ قَدْ أَحَجَّهَا أَ يَجُوزُ ذَلِكَ عَنْهَا مِنْ حَجَّةِ الْإِسْلَامِ قَالَ لَا قُلْتُ لَهَا أَجْرٌ فِي حَجِّهَا قَالَ نَعَمْ.
- **Isnad as currently extracted:**
  > رَوَى إِسْحَاقُ بْنُ عَمَّارٍ[1] قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | اسحاق بن عمار | روی |  |

### Chain 174 · `faqih-2885` — CLARIFIED
- Transmitters (student → teacher): اسحاق بن عمار
- Corrected isnad (Arabic): «رَوَى إِسْحَاقُ بْنُ عَمَّارٍ[1] قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنْ أُمِّ وَلَدٍ تَكُونُ لِلرَّجُلِ"
- Mursal opening: al-Ṣadūq → اسحاق بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 175 · `faqih-2887`
- **Location:** vol. 2, p. 432 · seq 2896 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع مَمْلُوكٌ أُعْتِقَ يَوْمَ عَرَفَةَ قَالَ إِذَا أَدْرَكَ أَحَدَ الْمَوْقِفَيْنِ فَقَدْ أَدْرَكَ الْحَجَ‌[3].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن معاویة بن عمار | روی |  |

### Chain 175 · `faqih-2887` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع مَمْلُوكٌ أُعْتِقَ يَوْمَ عَرَفَةَ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 176 · `faqih-2888`
- **Location:** vol. 2, p. 433 · seq 2897 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى زُرَارَةُ[1] عَنْ أَحَدِهِمَا ع قَالَ‌ إِذَا حَجَّ الرَّجُلُ بِابْنِهِ وَ هُوَ صَغِيرٌ- فَإِنَّهُ يَأْمُرُهُ أَنْ يُلَبِّيَ وَ يَفْرِضَ الْحَجَّ فَإِنْ لَمْ يُحْسِنْ أَنْ يُلَبِّيَ لَبَّى عَنْهُ‌[2] وَ يُطَافُ بِهِ وَ يُصَلَّى عَنْهُ قُلْتُ لَيْسَ لَهُمْ مَا يَذْبَحُونَ عَنْهُ‌[3] قَالَ يُذْبَحُ عَنِ الصِّغَارِ وَ يَصُومُ الْكِبَارُ[4] وَ يُتَّقَى عَلَيْهِمْ‌[5] مَا يُتَّقَى عَلَى الْمُحْرِمِ مِنَ الثِّيَابِ وَ الطِّيبِ فَإِنْ قَتَلَ صَيْداً فَعَلَى أَبِيهِ‌[6].
- **Isnad as currently extracted:**
  > رَوَى زُرَارَةُ[1] عَنْ أَحَدِهِمَا ع قَالَ‌ إِذَا حَجَّ الرَّجُلُ بِابْنِهِ وَ هُوَ صَغِيرٌ- فَإِنَّهُ يَأْمُرُهُ أَنْ يُلَبِّيَ وَ يَفْرِضَ الْحَجَّ فَإِنْ لَمْ يُحْسِنْ أَنْ يُلَبِّيَ لَبَّى عَنْهُ‌[2] وَ يُطَافُ بِهِ وَ يُصَلَّى عَنْهُ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | زرارة | روی |  |
  | 1 | imam | احدهما ع | عن | ambiguous |

### Chain 176 · `faqih-2888` — CLARIFIED
- Transmitters (student → teacher): زرارة → احدهما ع
- Corrected isnad (Arabic): «رَوَى زُرَارَةُ[1] عَنْ أَحَدِهِمَا ع قَالَ‌»
- Isnad ends / matn begins at: "إِذَا حَجَّ الرَّجُلُ بِابْنِهِ وَ هُوَ صَغِيرٌ- فَإِنَّهُ يَأْمُرُهُ"
- Mursal opening: al-Ṣadūq → زرارة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 177 · `faqih-2890`
- **Location:** vol. 2, p. 434 · seq 2899 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ يُونُسَ بْنِ يَعْقُوبَ‌[1] عَنْ أَبِيهِ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ مَعِي صِبْيَةً صِغَاراً وَ أَنَا أَخَافُ عَلَيْهِمُ الْبَرْدَ فَمِنْ أَيْنَ يُحْرِمُونَ فَقَالَ ائْتِ بِهِمُ الْعَرْجَ‌[2] فَلْيُحْرِمُوا مِنْهَا فَإِنَّكَ إِذَا أَتَيْتَ الْعَرْجَ وَقَعْتَ فِي تِهَامَةَ[3] ثُمَّ قَالَ فَإِنْ خِفْتَ عَلَيْهِمْ فَائْتِ بِهِمُ الْجُحْفَةَ[4].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ يُونُسَ بْنِ يَعْقُوبَ‌[1] عَنْ أَبِيهِ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن یونس بن یعقوب | روی |  |
  | 1 | pronoun_relation | ابیه | عن | father |

### Chain 177 · `faqih-2890` — CLARIFIED
- Transmitters (student → teacher): يونس بن يعقوب → أبيه (غير مسمّى في النص) → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ يُونُسَ بْنِ يَعْقُوبَ‌[1] عَنْ أَبِيهِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ مَعِي صِبْيَةً صِغَاراً"
- Mursal opening: al-Ṣadūq → يونس بن يعقوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 178 · `faqih-2893`
- **Location:** vol. 2, p. 435 · seq 2902 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى صَفْوَانُ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ أَبَا الْحَسَنِ ع عَنِ ابْنِ عَشْرِ سِنِينَ يَحُجُّ قَالَ عَلَيْهِ حَجَّةُ الْإِسْلَامِ إِذَا احْتَلَمَ وَ كَذَلِكَ الْجَارِيَةُ عَلَيْهَا الْحَجُّ إِذَا طَمِثَتْ‌[4].
- **Isnad as currently extracted:**
  > وَ رَوَى صَفْوَانُ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان | روی |  |
  | 1 | named_narrator | اسحاق بن عمار | عن |  |

### Chain 178 · `faqih-2893` — CLARIFIED
- Transmitters (student → teacher): صفوان → اسحاق بن عمار
- Corrected isnad (Arabic): «وَ رَوَى صَفْوَانُ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا الْحَسَنِ ع عَنِ ابْنِ عَشْرِ سِنِينَ يَحُجُّ"
- Mursal opening: al-Ṣadūq → صفوان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 179 · `faqih-2894`
- **Location:** vol. 2, p. 435 · seq 2903 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ عَلِيِّ بْنِ مَهْزِيَارَ عَنْ مُحَمَّدِ بْنِ الْفُضَيْلِ قَالَ‌ سَأَلْتُ أَبَا جَعْفَرٍ الثَّانِيَ عَنِ الصَّبِيِّ مَتَى يُحْرَمُ بِهِ قَالَ إِذَا اثَّغَرَ[5].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ عَلِيِّ بْنِ مَهْزِيَارَ عَنْ مُحَمَّدِ بْنِ الْفُضَيْلِ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن علی بن مهزیار | روی |  |
  | 1 | named_narrator | محمد بن الفضیل | عن |  |

### Chain 179 · `faqih-2894` — CLARIFIED
- Transmitters (student → teacher): علي بن مهزيار → محمد بن الفضيل → ابا جعفر الثاني ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ عَلِيِّ بْنِ مَهْزِيَارَ عَنْ مُحَمَّدِ بْنِ الْفُضَيْلِ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا جَعْفَرٍ الثَّانِيَ عَنِ الصَّبِيِّ مَتَى يُحْرَمُ بِهِ"
- Mursal opening: al-Ṣadūq → علي بن مهزيار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 180 · `faqih-2896`
- **Location:** vol. 2, p. 436 · seq 2905 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ يَعْقُوبَ بْنِ شُعَيْبٍ‌[1] قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ يَحُجُّ بِدَيْنٍ وَ قَدْ حَجَّ حَجَّةَ الْإِسْلَامِ قَالَ نَعَمْ إِنَّ اللَّهَ عَزَّ وَ جَلَّ سَيَقْضِي عَنْهُ إِنْ شَاءَ اللَّهُ تَعَالَى‌[2].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ يَعْقُوبَ بْنِ شُعَيْبٍ‌[1] قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن یعقوب بن شعیب | روی |  |

### Chain 180 · `faqih-2896` — CLARIFIED
- Transmitters (student → teacher): يعقوب بن شعيب → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنْ يَعْقُوبَ بْنِ شُعَيْبٍ‌[1] قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ يَحُجُّ بِدَيْنٍ"
- Mursal opening: al-Ṣadūq → يعقوب بن شعيب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 181 · `faqih-2897`
- **Location:** vol. 2, p. 436 · seq 2906 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ عَبْدِ الْمَلِكِ بْنِ عُتْبَةَ[3] قَالَ‌ سَأَلْتُ أَبَا الْحَسَنِ ع عَنِ الرَّجُلِ عَلَيْهِ دَيْنٌ يَسْتَقْرِضُ وَ يَحُجُّ قَالَ إِنْ كَانَ لَهُ وَجْهٌ فِي مَالٍ فَلَا بَأْسَ‌[4].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ عَبْدِ الْمَلِكِ بْنِ عُتْبَةَ[3] قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن عبد الملک بن عتبة | روی |  |

### Chain 181 · `faqih-2897` — CLARIFIED
- Transmitters (student → teacher): عبد الملك بن عتبة
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ عَبْدِ الْمَلِكِ بْنِ عُتْبَةَ[3] قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا الْحَسَنِ ع عَنِ الرَّجُلِ عَلَيْهِ دَيْنٌ يَسْتَقْرِضُ"
- Mursal opening: al-Ṣadūq → عبد الملك بن عتبة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 182 · `faqih-2898`
- **Location:** vol. 2, p. 436 · seq 2907 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى مُوسَى بْنُ بَكْرٍ[5] عَنْهُ ع قَالَ‌ قُلْتُ لَهُ هَلْ يَسْتَقْرِضُ الرَّجُلُ وَ يَحُجُّ إِذَا كَانَ خَلْفَ ظَهْرِهِ مَا يُؤَدَّى بِهِ عَنْهُ إِذَا حَدَثَ بِهِ حَدَثٌ قَالَ نَعَمْ.
- **Isnad as currently extracted:**
  > وَ رَوَى مُوسَى بْنُ بَكْرٍ[5] عَنْهُ ع قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | imam | موسی بن بکر عنه ع | روی |  |

### Chain 182 · `faqih-2898` — CLARIFIED
- Transmitters (student → teacher): موسي بن بكر عنه ع
- Corrected isnad (Arabic): «وَ رَوَى مُوسَى بْنُ بَكْرٍ[5] عَنْهُ ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ هَلْ يَسْتَقْرِضُ الرَّجُلُ وَ يَحُجُّ إِذَا كَانَ"
- Mursal opening: al-Ṣadūq → موسي بن بكر عنه ع; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 183 · `faqih-2899`
- **Location:** vol. 2, p. 436 · seq 2908 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ أَبِي هَمَّامٍ‌[6] قَالَ‌ قُلْتُ لِلرِّضَا ع الرَّجُلُ يَكُونُ عَلَيْهِ الدَّيْنُ وَ يَحْضُرُهُ الشَّيْ‌ءُ[7] أَ يَقْضِي دَيْنَهُ أَوْ يَحُجُّ قَالَ يَقْضِي بِبَعْضٍ وَ يَحُجُّ بِبَعْضٍ قُلْتُ فَإِنَّهُ لَا يَكُونُ إِلَّا بِقَدْرِ نَفَقَةِ الْحَجِّ قَالَ يَقْضِي سَنَةً وَ يَحُجُّ سَنَةً قُلْتُ أُعْطِيَ‌
الْمَالَ مِنْ نَاحِيَةِ السُّلْطَانِ قَالَ لَا بَأْسَ عَلَيْكُمْ‌[1].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ أَبِي هَمَّامٍ‌[6] قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن ابی همام | روی |  |

### Chain 183 · `faqih-2899` — CLARIFIED
- Transmitters (student → teacher): ابي همام
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ أَبِي هَمَّامٍ‌[6] قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِلرِّضَا ع الرَّجُلُ يَكُونُ عَلَيْهِ الدَّيْنُ وَ يَحْضُرُهُ"
- Mursal opening: al-Ṣadūq → ابي همام; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 184 · `faqih-2901`
- **Location:** vol. 2, p. 437 · seq 2910 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى ابْنُ مَحْبُوبٍ عَنْ أَبَانٍ عَنِ الْحَسَنِ بْنِ زِيَادٍ الْعَطَّارِ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع يَكُونُ عَلَيَّ الدَّيْنُ فَيَقَعُ فِي يَدِيَ الدَّرَاهِمُ فَإِنْ وَزَّعْتُهَا بَيْنَهُمْ لَمْ يَقَعْ شَيْئاً[3] أَ فَأَحُجُّ أَوْ أُوَزِّعُهَا بَيْنَ الْغُرَمَاءِ قَالَ حُجَّ بِهَا وَ ادْعُ اللَّهَ أَنْ يَقْضِيَ عَنْكَ دَيْنَكَ إِنْ شَاءَ اللَّهُ تَعَالَى‌[4].
- **Isnad as currently extracted:**
  > وَ رَوَى ابْنُ مَحْبُوبٍ عَنْ أَبَانٍ عَنِ الْحَسَنِ بْنِ زِيَادٍ الْعَطَّارِ قَالَ‌ قُلْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن محبوب | روی |  |
  | 1 | named_narrator | ابان | عن |  |
  | 2 | named_narrator | الحسن بن زیاد العطار | عن |  |

### Chain 184 · `faqih-2901` — CLARIFIED
- Transmitters (student → teacher): ابن محبوب → ابان → الحسن بن زياد العطار → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى ابْنُ مَحْبُوبٍ عَنْ أَبَانٍ عَنِ الْحَسَنِ بْنِ زِيَادٍ الْعَطَّارِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع يَكُونُ عَلَيَّ الدَّيْنُ فَيَقَعُ"
- Mursal opening: al-Ṣadūq → ابن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 185 · `faqih-2902`
- **Location:** vol. 2, p. 437 · seq 2911 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى أَبَانٌ عَنْ زُرَارَةَ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنِ امْرَأَةٍ لَهَا
زَوْجٌ وَ هِيَ صَرُورَةٌ وَ لَا يَأْذَنُ لَهَا فِي الْحَجِّ قَالَ تَحُجُّ وَ إِنْ لَمْ يَأْذَنْ لَهَا[1].
- **Isnad as currently extracted:**
  > رَوَى أَبَانٌ عَنْ زُرَارَةَ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنِ امْرَأَةٍ لَهَا زَوْجٌ وَ هِيَ صَرُورَةٌ وَ لَا يَأْذَنُ لَهَا فِي الْحَجِّ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابان | روی |  |
  | 1 | named_narrator | زرارة | عن |  |
  | 2 | imam | ابی جعفر ع | عن |  |

### Chain 185 · `faqih-2902` — CLARIFIED
- Transmitters (student → teacher): ابان → زرارة → ابي جعفر ع
- Corrected isnad (Arabic): «رَوَى أَبَانٌ عَنْ زُرَارَةَ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ امْرَأَةٍ لَهَا زَوْجٌ وَ هِيَ صَرُورَةٌ وَ"
- Mursal opening: al-Ṣadūq → ابان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 186 · `faqih-2902`
- **Location:** vol. 2, p. 437 · seq 2911 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى أَبَانٌ عَنْ زُرَارَةَ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنِ امْرَأَةٍ لَهَا
زَوْجٌ وَ هِيَ صَرُورَةٌ وَ لَا يَأْذَنُ لَهَا فِي الْحَجِّ قَالَ تَحُجُّ وَ إِنْ لَمْ يَأْذَنْ لَهَا[1].
- **Isnad as currently extracted:**
  > رَوَى أَبَانٌ عَنْ زُرَارَةَ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنِ امْرَأَةٍ لَهَا زَوْجٌ وَ هِيَ صَرُورَةٌ وَ لَا يَأْذَنُ لَهَا فِي الْحَجِّ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابان | روی |  |
  | 1 | named_narrator | زرارة | عن |  |
  | 2 | imam | ابی جعفر ع | عن |  |

### Chain 186 · `faqih-2902` — CLARIFIED
- Transmitters (student → teacher): ابان → زرارة → ابي جعفر ع
- Corrected isnad (Arabic): «رَوَى أَبَانٌ عَنْ زُرَارَةَ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ امْرَأَةٍ لَهَا زَوْجٌ وَ هِيَ صَرُورَةٌ وَ"
- Mursal opening: al-Ṣadūq → ابان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 187 · `faqih-2902`
- **Location:** vol. 2, p. 437 · seq 2911 · chain 3
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى أَبَانٌ عَنْ زُرَارَةَ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنِ امْرَأَةٍ لَهَا
زَوْجٌ وَ هِيَ صَرُورَةٌ وَ لَا يَأْذَنُ لَهَا فِي الْحَجِّ قَالَ تَحُجُّ وَ إِنْ لَمْ يَأْذَنْ لَهَا[1].
- **Isnad as currently extracted:**
  > رَوَى أَبَانٌ عَنْ زُرَارَةَ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنِ امْرَأَةٍ لَهَا زَوْجٌ وَ هِيَ صَرُورَةٌ وَ لَا يَأْذَنُ لَهَا فِي الْحَجِّ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابان | روی |  |
  | 1 | named_narrator | زرارة | عن |  |
  | 2 | imam | ابی جعفر ع | عن |  |

### Chain 187 · `faqih-2902` — CLARIFIED
- Transmitters (student → teacher): ابان → زرارة → ابي جعفر ع
- Corrected isnad (Arabic): «رَوَى أَبَانٌ عَنْ زُرَارَةَ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ امْرَأَةٍ لَهَا زَوْجٌ وَ هِيَ صَرُورَةٌ وَ"
- Mursal opening: al-Ṣadūq → ابان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 188 · `faqih-2904`
- **Location:** vol. 2, p. 438 · seq 2913 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ أَبِي إِبْرَاهِيمَ ع قَالَ‌ سَأَلْتُهُ عَنِ الْمَرْأَةِ الْمُوسِرَةِ قَدْ حَجَّتْ حَجَّةَ الْإِسْلَامِ فَتَقُولُ لِزَوْجِهَا أَ حِجَّنِي مَرَّةً أُخْرَى أَ لَهُ أَنْ يَمْنَعَهَا قَالَ نَعَمْ‌[4] يَقُولُ لَهَا حَقِّي عَلَيْكِ أَعْظَمُ مِنْ حَقِّكِ عَلَيَّ فِي ذَا[5].
- **Isnad as currently extracted:**
  > وَ رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ أَبِي إِبْرَاهِيمَ ع قَالَ‌ سَأَلْتُهُ عَنِ الْمَرْأَةِ الْمُوسِرَةِ قَدْ حَجَّتْ حَجَّةَ الْإِسْلَامِ فَتَقُولُ لِزَوْجِهَا أَ حِجَّنِي مَرَّةً أُخْرَى أَ لَهُ أَنْ يَمْنَعَهَا قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | اسحاق بن عمار | روی |  |
  | 1 | imam | ابی ابراهیم ع | عن |  |

### Chain 188 · `faqih-2904` — CLARIFIED
- Transmitters (student → teacher): اسحاق بن عمار → ابي ابراهيم ع
- Corrected isnad (Arabic): «وَ رَوَى إِسْحَاقُ بْنُ عَمَّارٍ عَنْ أَبِي إِبْرَاهِيمَ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْمَرْأَةِ الْمُوسِرَةِ قَدْ حَجَّتْ حَجَّةَ الْإِسْلَامِ فَتَقُولُ"
- Mursal opening: al-Ṣadūq → اسحاق بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 189 · `faqih-2905`
- **Location:** vol. 2, p. 438 · seq 2914 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الْمَرْأَةِ تَخْرُجُ إِلَى مَكَّةَ بِغَيْرِ وَلِيٍّ فَقَالَ لَا بَأْسَ تَخْرُجُ مَعَ قَوْمٍ ثِقَاتٍ.
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن معاویة بن عمار | روی |  |

### Chain 189 · `faqih-2905` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار
- Corrected isnad (Arabic): «رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الْمَرْأَةِ تَخْرُجُ إِلَى"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 190 · `faqih-2907`
- **Location:** vol. 2, p. 439 · seq 2916 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى الْبَزَنْطِيُّ عَنْ صَفْوَانَ الْجَمَّالِ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع قَدْ عَرَفْتَنِي بِعَمَلِي‌[2] تَأْتِينِي الْمَرْأَةُ أَعْرِفُهَا بِإِسْلَامِهَا وَ حُبِّهَا إِيَّاكُمْ وَ وَلَايَتِهَا لَكُمْ لَيْسَ لَهَا مَحْرَمٌ قَالَ إِذَا جَاءَتِ الْمَرْأَةُ الْمُسْلِمَةُ فَاحْمِلْهَا[3] فَإِنَّ الْمُؤْمِنَ مَحْرَمُ الْمُؤْمِنَةِ ثُمَّ تَلَا هَذِهِ الْآيَةَ وَ الْمُؤْمِنُونَ وَ الْمُؤْمِناتُ بَعْضُهُمْ أَوْلِياءُ بَعْضٍ‌.
- **Isnad as currently extracted:**
  > وَ رَوَى الْبَزَنْطِيُّ عَنْ صَفْوَانَ الْجَمَّالِ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | البزنطی | روی |  |
  | 1 | named_narrator | صفوان الجمال | عن |  |

### Chain 190 · `faqih-2907` — CLARIFIED
- Transmitters (student → teacher): البزنطي → صفوان الجمال → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى الْبَزَنْطِيُّ عَنْ صَفْوَانَ الْجَمَّالِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع قَدْ عَرَفْتَنِي بِعَمَلِي‌[2] تَأْتِينِي"
- Mursal opening: al-Ṣadūq → البزنطي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 191 · `faqih-2909`
- **Location:** vol. 2, p. 440 · seq 2918 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى ابْنُ بُكَيْرٍ عَنْ زُرَارَةَ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الْمَرْأَةِ الَّتِي يُتَوَفَّى عَنْهَا زَوْجُهَا أَ تَحُجُّ فِي عِدَّتِهَا قَالَ نَعَمْ.
- **Isnad as currently extracted:**
  > وَ رَوَى ابْنُ بُكَيْرٍ عَنْ زُرَارَةَ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن بکیر | روی |  |
  | 1 | named_narrator | زرارة | عن |  |

### Chain 191 · `faqih-2909` — CLARIFIED
- Transmitters (student → teacher): ابن بكير → زرارة → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى ابْنُ بُكَيْرٍ عَنْ زُرَارَةَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الْمَرْأَةِ الَّتِي يُتَوَفَّى"
- Mursal opening: al-Ṣadūq → ابن بكير; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 192 · `faqih-2911`
- **Location:** vol. 2, p. 440 · seq 2920 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى عَلِيُّ بْنُ رِئَابٍ‌[2] عَنْ بُرَيْدٍ الْعِجْلِيِ‌[3] قَالَ‌ سَأَلْتُ أَبَا جَعْفَرٍ ع عَنْ رَجُلٍ خَرَجَ حَاجّاً وَ مَعَهُ جَمَلٌ لَهُ وَ نَفَقَةٌ وَ زَادٌ فَمَاتَ فِي الطَّرِيقِ قَالَ إِنْ كَانَ صَرُورَةً ثُمَّ مَاتَ فِي الْحَرَمِ فَقَدْ أَجْزَأَتْ عَنْهُ حَجَّةُ الْإِسْلَامِ وَ إِنْ كَانَ مَاتَ وَ هُوَ صَرُورَةٌ قَبْلَ أَنْ يُحْرِمَ‌[4] جُعِلَ جَمَلُهُ وَ زَادُهُ وَ نَفَقَتُهُ وَ مَا مَعَهُ فِي حَجَّةِ الْإِسْلَامِ-
فَإِنْ فَضَلَ مِنْ ذَلِكَ شَيْ‌ءٌ فَهُوَ لِلْوَرَثَةِ إِنْ لَمْ يَكُنْ عَلَيْهِ دَيْنٌ قُلْتُ أَ رَأَيْتَ إِنْ كَانَتِ الْحَجَّةُ تَطَوُّعاً ثُمَّ مَاتَ فِي الطَّرِيقِ قَبْلَ أَنْ يُحْرِمَ لِمَنْ يَكُونُ جَمَلُهُ وَ نَفَقَتُهُ وَ مَا مَعَهُ قَالَ يَكُونُ جَمِيعُ مَا مَعَهُ وَ مَا تَرَكَ لِلْوَرَثَةِ إِلَّا أَنْ يَكُونَ عَلَيْهِ دَيْنٌ فَيُقْضَى عَنْهُ أَوْ يَكُونَ أَوْصَى بِوَصِيَّةٍ فَيَنْفُذَ ذَلِكَ لِمَنْ أَوْصَى لَهُ وَ يُجْعَلَ ذَلِكَ مِنْ ثُلُثِهِ.
- **Isnad as currently extracted:**
  > وَ رَوَى عَلِيُّ بْنُ رِئَابٍ‌[2] عَنْ بُرَيْدٍ الْعِجْلِيِ‌[3] قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن رئاب | روی |  |
  | 1 | named_narrator | برید العجلی | عن |  |

### Chain 192 · `faqih-2911` — CLARIFIED
- Transmitters (student → teacher): علي بن رئاب → بريد العجلي → ابا جعفر ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى عَلِيُّ بْنُ رِئَابٍ‌[2] عَنْ بُرَيْدٍ الْعِجْلِيِ‌[3] قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا جَعْفَرٍ ع عَنْ رَجُلٍ خَرَجَ حَاجّاً وَ"
- Mursal opening: al-Ṣadūq → علي بن رئاب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 193 · `faqih-2914`
- **Location:** vol. 2, p. 442 · seq 2923 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنِ الْحَارِثِ بْنِ الْمُغِيرَةِ[1] قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ ابْنَتِي أَوْصَتْ بِحَجَّةٍ وَ لَمْ تَحُجَّ قَالَ فَحُجَّ عَنْهَا فَإِنَّهَا لَكَ وَ لَهَا قُلْتُ إِنَّ أُمِّي مَاتَتْ وَ لَمْ تَحُجَّ قَالَ حُجَّ عَنْهَا فَإِنَّهَا لَكَ وَ لَهَا[2].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنِ الْحَارِثِ بْنِ الْمُغِيرَةِ[1] قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن الحارث بن المغیرة | روی |  |

### Chain 193 · `faqih-2914` — CLARIFIED
- Transmitters (student → teacher): الحارث بن المغيرة → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنِ الْحَارِثِ بْنِ الْمُغِيرَةِ[1] قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ ابْنَتِي أَوْصَتْ بِحَجَّةٍ"
- Mursal opening: al-Ṣadūq → الحارث بن المغيرة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 194 · `faqih-2915`
- **Location:** vol. 2, p. 442 · seq 2924 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ امْرَأَةٍ أَوْصَتْ بِمَالٍ فِي الصَّدَقَةِ وَ الْحَجِّ وَ الْعِتْقِ فَقَالَ ابْدَأْ بِالْحَجِّ فَإِنَّهُ مَفْرُوضٌ فَإِنْ بَقِيَ شَيْ‌ءٌ فَاجْعَلْ فِي الصَّدَقَةِ طَائِفَةً وَ فِي الْعِتْقِ طَائِفَةً[3].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن معاویة بن عمار | روی |  |

### Chain 194 · `faqih-2915` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ امْرَأَةٍ أَوْصَتْ بِمَالٍ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 195 · `faqih-2916`
- **Location:** vol. 2, p. 442 · seq 2925 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ بَشِيرٍ النَّبَّالِ‌[4] قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ وَالِدَتِي تُوُفِّيَتْ وَ لَمْ تَحُجَّ قَالَ يَحُجُّ عَنْهَا رَجُلٌ أَوِ امْرَأَةٌ قَالَ قُلْتُ أَيُّهُمْ أَحَبُّ إِلَيْكَ قَالَ رَجُلٌ أَحَبُّ إِلَيَ‌[5].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ بَشِيرٍ النَّبَّالِ‌[4] قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن بشیر النبال | روی |  |

### Chain 195 · `faqih-2916` — CLARIFIED
- Transmitters (student → teacher): بشير النبال → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ بَشِيرٍ النَّبَّالِ‌[4] قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ وَالِدَتِي تُوُفِّيَتْ وَ"
- Mursal opening: al-Ṣadūq → بشير النبال; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 196 · `faqih-2917`
- **Location:** vol. 2, p. 442 · seq 2926 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ عَاصِمِ بْنِ حُمَيْدٍ[6] عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ أَبَا جَعْفَرٍ ع عَنْ رَجُلٍ مَاتَ وَ لَمْ يَحُجَّ حَجَّةَ الْإِسْلَامِ وَ لَمْ يُوصِ بِهَا أَ يُقْضَى عَنْهُ قَالَ نَعَمْ‌[7].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ عَاصِمِ بْنِ حُمَيْدٍ[6] عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن عاصم بن حمید | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |

### Chain 196 · `faqih-2917` — CLARIFIED
- Transmitters (student → teacher): عاصم بن حميد → محمد بن مسلم → ابا جعفر ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ عَاصِمِ بْنِ حُمَيْدٍ[6] عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا جَعْفَرٍ ع عَنْ رَجُلٍ مَاتَ وَ لَمْ"
- Mursal opening: al-Ṣadūq → عاصم بن حميد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 197 · `faqih-2921`
- **Location:** vol. 2, p. 444 · seq 2930 · chain 1
- **Flags:** `multi_route`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى عَلِيُّ بْنُ مَهْزِيَارَ[2] عَنْ مُحَمَّدِ بْنِ إِسْمَاعِيلَ قَالَ‌ أَمَرْتُ رَجُلًا أَنْ يَسْأَلَ أَبَا الْحَسَنِ ع عَنِ الرَّجُلِ يَأْخُذُ مِنَ الرَّجُلِ حَجَّةً فَلَا تَكْفِيهِ أَ لَهُ أَنْ يَأْخُذَ مِنْ رَجُلٍ آخَرَ حَجَّةً أُخْرَى فَيَتَّسِعَ بِهَا فَتُجْزِيَ عَنْهُمَا جَمِيعاً أَوْ يَتْرُكُهُمَا جَمِيعاً إِنْ لَمْ تَكْفِهِ إِحْدَاهُمَا فَذَكَرَ أَنَّهُ قَالَ أَحَبُّ إِلَيَّ أَنْ تَكُونَ خَالِصَةً لِوَاحِدٍ فَإِنْ كَانَتْ لَا تَكْفِيهِ فَلَا يَأْخُذْهَا.
- **Isnad as currently extracted:**
  > رَوَى عَلِيُّ بْنُ مَهْزِيَارَ[2] عَنْ مُحَمَّدِ بْنِ إِسْمَاعِيلَ قَالَ‌ أَمَرْتُ رَجُلًا أَنْ يَسْأَلَ أَبَا الْحَسَنِ ع عَنِ الرَّجُلِ يَأْخُذُ مِنَ الرَّجُلِ حَجَّةً فَلَا تَكْفِيهِ أَ لَهُ أَنْ يَأْخُذَ مِنْ رَجُلٍ آخَرَ حَجَّةً أُخْرَى فَيَتَّسِعَ بِهَا فَتُجْزِيَ عَنْهُمَا جَمِيعاً أَوْ يَتْرُكُهُمَا جَمِيعاً إِنْ لَمْ تَكْفِهِ إِحْدَاهُمَا فَذَكَرَ أَنَّهُ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن مهزیار | روی |  |
  | 1 | named_narrator | محمد بن اسماعیل | عن |  |
  | 2 | imam | ابا الحسن ع |  |  |

### Chain 197 · `faqih-2921` — CLARIFIED
- Transmitters (student → teacher): علي بن مهزيار → محمد بن إسماعيل → رجل غير مسمّى → أبو الحسن ع
- Corrected isnad (Arabic): «رَوَى عَلِيُّ بْنُ مَهْزِيَارَ[2] عَنْ مُحَمَّدِ بْنِ إِسْمَاعِيلَ قَالَ‌»
- Isnad ends / matn begins at: "أَمَرْتُ رَجُلًا أَنْ يَسْأَلَ أَبَا الْحَسَنِ ع عَنِ الرَّجُلِ"
- Mursal opening: al-Ṣadūq → علي بن مهزيار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The intermediary is genuinely anonymous because the source itself says «رَجُلًا». Resolution therefore means retaining an explicit `unnamed_intermediary`, not inventing his identity. The route is also catalogued with this wording in [Jāmiʿ al-Ruwāt, vol. 2, p. 74](https://lib.eshia.ir/14021/2/74).
---

### Chain 198 · `faqih-2922`
- **Location:** vol. 2, p. 444 · seq 2931 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى ابْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ[3] عَمَّنْ سَأَلَهُ قَالَ‌ قُلْتُ لَهُ رَجُلٌ أَوْصَى بِعِشْرِينَ دِينَاراً فِي حَجَّةٍ فَقَالَ يَحُجُّ بِهَا رَجُلٌ مِنْ حَيْثُ يَبْلُغُهُ‌[4].
- **Isnad as currently extracted:**
  > رَوَى ابْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ[3] عَمَّنْ سَأَلَهُ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن مسکان | روی |  |
  | 1 | named_narrator | ابی بصیر عمن ساله | عن |  |

### Chain 198 · `faqih-2922` — CLARIFIED
- Transmitters (student → teacher): ابن مسكان → ابي بصير عمن ساله
- Corrected isnad (Arabic): «رَوَى ابْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ[3] عَمَّنْ سَأَلَهُ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ رَجُلٌ أَوْصَى بِعِشْرِينَ دِينَاراً فِي حَجَّةٍ فَقَالَ"
- Mursal opening: al-Ṣadūq → ابن مسكان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 199 · `faqih-2925`
- **Location:** vol. 2, p. 445 · seq 2934 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى سُوَيْدٌ الْقَلَّاءُ عَنْ أَيُّوبَ بْنِ حُرٍّ عَنْ بُرَيْدٍ الْعِجْلِيِ‌[2] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ اسْتَوْدَعَنِي مَالًا فَهَلَكَ وَ لَيْسَ لِوُلْدِهِ شَيْ‌ءٌ وَ لَمْ يَحُجَّ حَجَّةَ الْإِسْلَامِ قَالَ حُجَّ عَنْهُ وَ مَا فَضَلَ فَأَعْطِهِمْ‌[3].
- **Isnad as currently extracted:**
  > رَوَى سُوَيْدٌ الْقَلَّاءُ عَنْ أَيُّوبَ بْنِ حُرٍّ عَنْ بُرَيْدٍ الْعِجْلِيِ‌[2] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ اسْتَوْدَعَنِي مَالًا فَهَلَكَ وَ لَيْسَ لِوُلْدِهِ شَيْ‌ءٌ وَ لَمْ يَحُجَّ حَجَّةَ الْإِسْلَامِ قَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | سوید القلاء | روی |  |
  | 1 | named_narrator | ایوب بن حر | عن |  |
  | 2 | named_narrator | برید العجلی | عن |  |
  | 3 | imam | ابی عبد الله ع | عن |  |

### Chain 199 · `faqih-2925` — CLARIFIED
- Transmitters (student → teacher): سويد القلاء → ايوب بن حر → بريد العجلي → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى سُوَيْدٌ الْقَلَّاءُ عَنْ أَيُّوبَ بْنِ حُرٍّ عَنْ بُرَيْدٍ الْعِجْلِيِ‌[2] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ اسْتَوْدَعَنِي مَالًا فَهَلَكَ وَ لَيْسَ لِوُلْدِهِ"
- Mursal opening: al-Ṣadūq → سويد القلاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 200 · `faqih-2925`
- **Location:** vol. 2, p. 445 · seq 2934 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى سُوَيْدٌ الْقَلَّاءُ عَنْ أَيُّوبَ بْنِ حُرٍّ عَنْ بُرَيْدٍ الْعِجْلِيِ‌[2] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ اسْتَوْدَعَنِي مَالًا فَهَلَكَ وَ لَيْسَ لِوُلْدِهِ شَيْ‌ءٌ وَ لَمْ يَحُجَّ حَجَّةَ الْإِسْلَامِ قَالَ حُجَّ عَنْهُ وَ مَا فَضَلَ فَأَعْطِهِمْ‌[3].
- **Isnad as currently extracted:**
  > رَوَى سُوَيْدٌ الْقَلَّاءُ عَنْ أَيُّوبَ بْنِ حُرٍّ عَنْ بُرَيْدٍ الْعِجْلِيِ‌[2] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ اسْتَوْدَعَنِي مَالًا فَهَلَكَ وَ لَيْسَ لِوُلْدِهِ شَيْ‌ءٌ وَ لَمْ يَحُجَّ حَجَّةَ الْإِسْلَامِ قَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | سوید القلاء | روی |  |
  | 1 | named_narrator | ایوب بن حر | عن |  |
  | 2 | named_narrator | برید العجلی | عن |  |
  | 3 | imam | ابی عبد الله ع | عن |  |

### Chain 200 · `faqih-2925` — CLARIFIED
- Transmitters (student → teacher): سويد القلاء → ايوب بن حر → بريد العجلي → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى سُوَيْدٌ الْقَلَّاءُ عَنْ أَيُّوبَ بْنِ حُرٍّ عَنْ بُرَيْدٍ الْعِجْلِيِ‌[2] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ اسْتَوْدَعَنِي مَالًا فَهَلَكَ وَ لَيْسَ لِوُلْدِهِ"
- Mursal opening: al-Ṣadūq → سويد القلاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 201 · `faqih-2925`
- **Location:** vol. 2, p. 445 · seq 2934 · chain 3
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى سُوَيْدٌ الْقَلَّاءُ عَنْ أَيُّوبَ بْنِ حُرٍّ عَنْ بُرَيْدٍ الْعِجْلِيِ‌[2] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ اسْتَوْدَعَنِي مَالًا فَهَلَكَ وَ لَيْسَ لِوُلْدِهِ شَيْ‌ءٌ وَ لَمْ يَحُجَّ حَجَّةَ الْإِسْلَامِ قَالَ حُجَّ عَنْهُ وَ مَا فَضَلَ فَأَعْطِهِمْ‌[3].
- **Isnad as currently extracted:**
  > رَوَى سُوَيْدٌ الْقَلَّاءُ عَنْ أَيُّوبَ بْنِ حُرٍّ عَنْ بُرَيْدٍ الْعِجْلِيِ‌[2] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ اسْتَوْدَعَنِي مَالًا فَهَلَكَ وَ لَيْسَ لِوُلْدِهِ شَيْ‌ءٌ وَ لَمْ يَحُجَّ حَجَّةَ الْإِسْلَامِ قَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | سوید القلاء | روی |  |
  | 1 | named_narrator | ایوب بن حر | عن |  |
  | 2 | named_narrator | برید العجلی | عن |  |
  | 3 | imam | ابی عبد الله ع | عن |  |

### Chain 201 · `faqih-2925` — CLARIFIED
- Transmitters (student → teacher): سويد القلاء → ايوب بن حر → بريد العجلي → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى سُوَيْدٌ الْقَلَّاءُ عَنْ أَيُّوبَ بْنِ حُرٍّ عَنْ بُرَيْدٍ الْعِجْلِيِ‌[2] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ اسْتَوْدَعَنِي مَالًا فَهَلَكَ وَ لَيْسَ لِوُلْدِهِ"
- Mursal opening: al-Ṣadūq → سويد القلاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 202 · `faqih-2927`
- **Location:** vol. 2, p. 446 · seq 2936 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى جَعْفَرُ بْنُ بَشِيرٍ[3] عَنِ الْعَلَاءِ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ
ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ يَحُجُّ عَنْ أَبِيهِ أَ يَتَمَتَّعُ‌[1] قَالَ نَعَمْ الْمُتْعَةُ لَهُ وَ الْحَجُّ عَنْ أَبِيهِ‌[2].
- **Isnad as currently extracted:**
  > رَوَى جَعْفَرُ بْنُ بَشِيرٍ[3] عَنِ الْعَلَاءِ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ يَحُجُّ عَنْ أَبِيهِ أَ يَتَمَتَّعُ‌[1] قَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | جعفر بن بشیر | روی |  |
  | 1 | named_narrator | العلاء | عن |  |
  | 2 | named_narrator | محمد بن مسلم | عن |  |
  | 3 | imam | ابی جعفر ع | عن |  |

### Chain 202 · `faqih-2927` — CLARIFIED
- Transmitters (student → teacher): جعفر بن بشير → العلاء → محمد بن مسلم → ابي جعفر ع
- Corrected isnad (Arabic): «رَوَى جَعْفَرُ بْنُ بَشِيرٍ[3] عَنِ الْعَلَاءِ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ يَحُجُّ عَنْ أَبِيهِ أَ يَتَمَتَّعُ‌[1] قَالَ"
- Mursal opening: al-Ṣadūq → جعفر بن بشير; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 203 · `faqih-2928`
- **Location:** vol. 2, p. 447 · seq 2937 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ قَالَ‌ سَأَلْتُ أَبَا الْحَسَنِ ع عَنْ قَوْلِ اللَّهِ عَزَّ وَ جَلَ‌ وَ مَنْ كانَ فِي هذِهِ أَعْمى‌ فَهُوَ فِي الْآخِرَةِ أَعْمى‌ وَ أَضَلُّ سَبِيلًا فَقَالَ نَزَلَتْ فِيمَنْ سَوَّفَ الْحَجَ‌[3] حَجَّةَ الْإِسْلَامِ وَ عِنْدَهُ مَا يَحُجُّ بِهِ فَقَالَ الْعَامَ أَحُجُّ الْعَامَ أَحُجُّ حَتَّى يَمُوتَ قَبْلَ أَنْ يَحُجَّ.
- **Isnad as currently extracted:**
  > رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن الفضیل | روی |  |

### Chain 203 · `faqih-2928` — CLARIFIED
- Transmitters (student → teacher): محمد بن الفضيل → ابا الحسن ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى مُحَمَّدُ بْنُ الْفُضَيْلِ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا الْحَسَنِ ع عَنْ قَوْلِ اللَّهِ عَزَّ وَ"
- Mursal opening: al-Ṣadūq → محمد بن الفضيل; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 204 · `faqih-2929`
- **Location:** vol. 2, p. 447 · seq 2938 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ لَمْ يَحُجَّ قَطُّ وَ لَهُ مَالٌ فَقَالَ هُوَ مِمَّنْ قَالَ اللَّهُ عَزَّ وَ جَلَ‌ وَ نَحْشُرُهُ يَوْمَ الْقِيامَةِ أَعْمى‌ فَقُلْتُ سُبْحَانَ اللَّهِ أَعْمَى فَقَالَ أَعْمَاهُ اللَّهُ عَزَّ وَ جَلَّ عَنْ طَرِيقِ الْخَيْرِ.
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن معاویة بن عمار | روی |  |

### Chain 204 · `faqih-2929` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ لَمْ يَحُجَّ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 205 · `faqih-2940`
- **Location:** vol. 2, p. 452 · seq 2949 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى عَنْهُ ع أَنَّهُ قَالَ‌ مَنْ سَاقَ هَدْياً فِي عُمْرَةٍ فَلْيَنْحَرْ قَبْلَ أَنْ يَحْلِقَ رَأْسَهُ قَالَ وَ مَنْ سَاقَ هَدْياً وَ هُوَ مُعْتَمِرٌ نَحَرَ هَدْيَهُ عِنْدَ الْمَنْحَرِ وَ هُوَ بَيْنَ الصَّفَا وَ الْمَرْوَةِ وَ هِيَ الْحَزْوَرَةُ[1].
- **Isnad as currently extracted:**
  > وَ رَوَى عَنْهُ ع أَنَّهُ قَالَ‌ مَنْ سَاقَ هَدْياً فِي عُمْرَةٍ فَلْيَنْحَرْ قَبْلَ أَنْ يَحْلِقَ رَأْسَهُ قَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | imam | عنه ع | روی |  |

### Chain 205 · `faqih-2940` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار → أبو عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى عَنْهُ ع أَنَّهُ قَالَ‌»
- Isnad ends / matn begins at: "مَنْ سَاقَ هَدْياً فِي عُمْرَةٍ فَلْيَنْحَرْ قَبْلَ أَنْ يَحْلِقَ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The omitted subject is resolved by the parallel as Muʿāwiya b. ʿAmmār transmitting the statement of Abū ʿAbd Allāh: «صحيح معاوية بن عمار قال: قال أبو عبد الله ع...». The full al-Kāfī parallel gives the route through Muʿāwiya b. ʿAmmār and explicitly names Abū ʿAbd Allāh. Source: [al-Kāfī, vol. 4, p. 539](https://ar.lib.eshia.ir/11026/4/539).
---

### Chain 206 · `faqih-2951`
- **Location:** vol. 2, p. 455 · seq 2960 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ يُونُسَ بْنِ يَعْقُوبَ‌[5] قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الرَّجُلِ يَعْتَمِرُ عُمْرَةً مُفْرَدَةً فَقَالَ إِذَا رَأَيْتَ ذَا طُوًى فَاقْطَعِ التَّلْبِيَةَ[6].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ يُونُسَ بْنِ يَعْقُوبَ‌[5] قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن یونس بن یعقوب | روی |  |

### Chain 206 · `faqih-2951` — CLARIFIED
- Transmitters (student → teacher): يونس بن يعقوب → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ يُونُسَ بْنِ يَعْقُوبَ‌[5] قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الرَّجُلِ يَعْتَمِرُ عُمْرَةً"
- Mursal opening: al-Ṣadūq → يونس بن يعقوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 207 · `faqih-2960`
- **Location:** vol. 2, p. 458 · seq 2969 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى عَلِيُّ بْنُ أَبِي حَمْزَةَ[5] عَنْ أَبِي الْحَسَنِ مُوسَى ع قَالَ‌ لِكُلِّ شَهْرٍ عُمْرَةٌ قَالَ فَقُلْتُ لَهُ أَ يَكُونُ أَقَلَّ مِنْ ذَلِكَ قَالَ لِكُلِّ عَشَرَةِ أَيَّامٍ عُمْرَةٌ[6].
- **Isnad as currently extracted:**
  > وَ رَوَى عَلِيُّ بْنُ أَبِي حَمْزَةَ[5] عَنْ أَبِي الْحَسَنِ مُوسَى ع قَالَ‌ لِكُلِّ شَهْرٍ عُمْرَةٌ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن ابی حمزة | روی |  |
  | 1 | imam | ابی الحسن موسی ع | عن |  |

### Chain 207 · `faqih-2960` — CLARIFIED
- Transmitters (student → teacher): علي بن ابي حمزة → ابي الحسن موسي ع
- Corrected isnad (Arabic): «وَ رَوَى عَلِيُّ بْنُ أَبِي حَمْزَةَ[5] عَنْ أَبِي الْحَسَنِ مُوسَى ع قَالَ‌»
- Isnad ends / matn begins at: "لِكُلِّ شَهْرٍ عُمْرَةٌ قَالَ فَقُلْتُ لَهُ أَ يَكُونُ أَقَلَّ"
- Mursal opening: al-Ṣadūq → علي بن ابي حمزة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 208 · `faqih-2961`
- **Location:** vol. 2, p. 459 · seq 2970 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى أَبَانٌ عَنْ أَبِي الْجَارُودِ[1] عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنِ الْعُمْرَةِ بَعْدَ الْحَجِّ فِي ذِي الْحِجَّةِ قَالَ حَسَنٌ‌[2].
- **Isnad as currently extracted:**
  > وَ رَوَى أَبَانٌ عَنْ أَبِي الْجَارُودِ[1] عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنِ الْعُمْرَةِ بَعْدَ الْحَجِّ فِي ذِي الْحِجَّةِ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابان | روی |  |
  | 1 | named_narrator | ابی الجارود | عن |  |
  | 2 | imam | احدهما ع | عن | ambiguous |

### Chain 208 · `faqih-2961` — CLARIFIED
- Transmitters (student → teacher): ابان → ابي الجارود → احدهما ع
- Corrected isnad (Arabic): «وَ رَوَى أَبَانٌ عَنْ أَبِي الْجَارُودِ[1] عَنْ أَحَدِهِمَا ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْعُمْرَةِ بَعْدَ الْحَجِّ فِي ذِي الْحِجَّةِ قَالَ"
- Mursal opening: al-Ṣadūq → ابان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 209 · `faqih-2962`
- **Location:** vol. 2, p. 459 · seq 2971 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى ابْنُ مُسْكَانَ عَنِ الْحَلَبِيِّ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنِ الرَّجُلِ يَقْضِي عَنْ أَخِيهِ أَوْ عَنْ أَبِيهِ أَوْ عَنْ رَجُلٍ مِنَ النَّاسِ الْحَجَّ هَلْ يَنْبَغِي لَهُ أَنْ يَتَكَلَّمَ بِشَيْ‌ءٍ قَالَ نَعَمْ يَقُولُ عِنْدَ إِحْرَامِهِ بَعْدَ مَا يُحْرِمُ اللَّهُمَّ مَا أَصَابَنِي فِي سَفَرِي هَذَا مِنْ نَصَبٍ أَوْ شِدَّةٍ أَوْ بَلَاءٍ أَوْ شَعَثٍ‌[3] فَأْجُرْ فُلَاناً فِيهِ وَ أْجُرْنِي فِي قَضَائِي عَنْهُ‌[4].
- **Isnad as currently extracted:**
  > رَوَى ابْنُ مُسْكَانَ عَنِ الْحَلَبِيِّ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنِ الرَّجُلِ يَقْضِي عَنْ أَخِيهِ أَوْ عَنْ أَبِيهِ أَوْ عَنْ رَجُلٍ مِنَ النَّاسِ الْحَجَّ هَلْ يَنْبَغِي لَهُ أَنْ يَتَكَلَّمَ بِشَيْ‌ءٍ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن مسکان | روی |  |
  | 1 | named_narrator | الحلبی | عن |  |
  | 2 | imam | ابی عبد الله ع | عن |  |

### Chain 209 · `faqih-2962` — CLARIFIED
- Transmitters (student → teacher): ابن مسكان → الحلبي → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى ابْنُ مُسْكَانَ عَنِ الْحَلَبِيِّ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الرَّجُلِ يَقْضِي عَنْ أَخِيهِ أَوْ عَنْ أَبِيهِ"
- Mursal opening: al-Ṣadūq → ابن مسكان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 210 · `faqih-2966`
- **Location:** vol. 2, p. 460 · seq 2975 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ أَبِي قَدْ حَجَّ وَ وَالِدَتِي قَدْ حَجَّتْ وَ إِنَّ أَخَوَيَّ قَدْ حَجَّا وَ قَدْ أَرَدْتُ أَنْ أُدْخِلَهُمْ فِي حَجَّتِي كَأَنِّي قَدْ أَحْبَبْتُ أَنْ يَكُونُوا مَعِي فَقَالَ اجْعَلْهُمْ مَعَكَ فَإِنَّ اللَّهَ عَزَّ وَ جَلَّ جَاعِلٌ لَهُمْ حَجّاً وَ لَكَ حَجّاً وَ لَكَ أَجْراً بِصِلَتِكَ إِيَّاهُمْ‌[5].
- **Isnad as currently extracted:**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن عمار | روی |  |

### Chain 210 · `faqih-2966` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار
- Corrected isnad (Arabic): «رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ أَبِي قَدْ حَجَّ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 211 · `faqih-2969`
- **Location:** vol. 2, p. 462 · seq 2978 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ[2] قَالَ‌ قُلْتُ لِأَبِي الْحَسَنِ ع يَتَعَجَّلُ الرَّجُلُ قَبْلَ التَّرْوِيَةِ بِيَوْمٍ أَوْ يَوْمَيْنِ مِنْ أَجْلِ الزِّحَامِ وَ ضِغَاطِ النَّاسِ فَقَالَ لَا بَأْسَ‌[3].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ[2] قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن اسحاق بن عمار | روی |  |

### Chain 211 · `faqih-2969` — CLARIFIED
- Transmitters (student → teacher): اسحاق بن عمار
- Corrected isnad (Arabic): «رُوِيَ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ[2] قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي الْحَسَنِ ع يَتَعَجَّلُ الرَّجُلُ قَبْلَ التَّرْوِيَةِ بِيَوْمٍ"
- Mursal opening: al-Ṣadūq → اسحاق بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 212 · `faqih-2979`
- **Location:** vol. 2, p. 466 · seq 2988 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ أَهْلَ مَكَّةَ
- **Isnad as currently extracted:**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن عمار | روی |  |

### Chain 212 · `faqih-2979` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار
- Corrected isnad (Arabic): «رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ أَهْلَ مَكَّةَ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 213 · `faqih-2982`
- **Location:** vol. 2, p. 468 · seq 2991 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ إِذَا مَرَرْتَ بِوَادِي مُحَسِّرٍ[1] وَ هُوَ وَادٍ عَظِيمٌ بَيْنَ جَمْعٍ وَ مِنًى وَ هُوَ إِلَى مِنًى أَقْرَبُ فَاسْعَ فِيهِ حَتَّى تُجَاوِزَهُ فَإِنَّ رَسُولَ اللَّهِ ص حَرَّكَ نَاقَتَهُ فِيهِ وَ قَالَ اللَّهُمَّ سَلِّمْ عَهْدِي‌[2] وَ اقْبَلْ تَوْبَتِي وَ أَجِبْ دَعْوَتِي وَ اخْلُفْنِي بِخَيْرٍ فِيمَنْ تَرَكْتُ بَعْدِي‌[3].
- **Isnad as currently extracted:**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ إِذَا مَرَرْتَ بِوَادِي مُحَسِّرٍ[1] وَ هُوَ وَادٍ عَظِيمٌ بَيْنَ جَمْعٍ وَ مِنًى وَ هُوَ إِلَى مِنًى أَقْرَبُ فَاسْعَ فِيهِ حَتَّى تُجَاوِزَهُ فَإِنَّ رَسُولَ اللَّهِ ص حَرَّكَ نَاقَتَهُ فِيهِ وَ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن عمار | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 213 · `faqih-2982` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "إِذَا مَرَرْتَ بِوَادِي مُحَسِّرٍ[1] وَ هُوَ وَادٍ عَظِيمٌ بَيْنَ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 214 · `faqih-2986`
- **Location:** vol. 2, p. 469 · seq 2995 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى يُونُسُ بْنُ يَعْقُوبَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ لَهُ رَجُلٌ أَفَاضَ مِنْ عَرَفَاتٍ فَمَرَّ بِالْمَشْعَرِ فَلَمْ يَقِفْ حَتَّى انْتَهَى إِلَى مِنًى فَرَمَى الْجَمْرَةَ وَ لَمْ يَعْلَمْ‌
حَتَّى ارْتَفَعَ النَّهَارُ قَالَ يَرْجِعُ إِلَى الْمَشْعَرِ فَيَقِفُ ثُمَّ يَرْمِي الْجَمْرَةَ[1].
- **Isnad as currently extracted:**
  > وَ رَوَى يُونُسُ بْنُ يَعْقُوبَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | یونس بن یعقوب | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 214 · `faqih-2986` — CLARIFIED
- Transmitters (student → teacher): يونس بن يعقوب → ابي عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى يُونُسُ بْنُ يَعْقُوبَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ رَجُلٌ أَفَاضَ مِنْ عَرَفَاتٍ فَمَرَّ بِالْمَشْعَرِ فَلَمْ"
- Mursal opening: al-Ṣadūq → يونس بن يعقوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 215 · `faqih-2993`
- **Location:** vol. 2, p. 474 · seq 3002 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى عَلِيُّ بْنُ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع ذَهَبْتُ أَرْمِي فَإِذَا فِي يَدِي سِتُّ حَصَيَاتٍ فَقَالَ خُذْ وَاحِدَةً مِنْ تَحْتِ رِجْلَيْكَ‌[1].
- **Isnad as currently extracted:**
  > رَوَى عَلِيُّ بْنُ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن ابی حمزة | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |

### Chain 215 · `faqih-2993` — CLARIFIED
- Transmitters (student → teacher): علي بن ابي حمزة → ابي بصير → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى عَلِيُّ بْنُ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع ذَهَبْتُ أَرْمِي فَإِذَا فِي"
- Mursal opening: al-Ṣadūq → علي بن ابي حمزة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 216 · `faqih-2999`
- **Location:** vol. 2, p. 476 · seq 3008 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى وُهَيْبُ بْنُ حَفْصٍ‌[2] عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الَّذِي يَنْبَغِي لَهُ أَنْ يَرْمِيَ بِاللَّيْلِ مَنْ هُوَ قَالَ الْحَاطِبَةُ[3] وَ الْمَمْلُوكُ الَّذِي لَا يَمْلِكُ مِنْ أَمْرِهِ شَيْئاً وَ الْخَائِفُ وَ الْمَدِينُ وَ الْمَرِيضُ الَّذِي لَا يَسْتَطِيعُ أَنْ يَرْمِيَ يُحْمَلُ إِلَى الْجِمَارِ فَإِنْ قَدَرَ عَلَى أَنْ يَرْمِيَ وَ إِلَّا فَارْمِ عَنْهُ وَ هُوَ حَاضِرٌ[4].
- **Isnad as currently extracted:**
  > رَوَى وُهَيْبُ بْنُ حَفْصٍ‌[2] عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | وهیب بن حفص | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |

### Chain 216 · `faqih-2999` — CLARIFIED
- Transmitters (student → teacher): وهيب بن حفص → ابي بصير → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى وُهَيْبُ بْنُ حَفْصٍ‌[2] عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الَّذِي يَنْبَغِي لَهُ"
- Mursal opening: al-Ṣadūq → وهيب بن حفص; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 217 · `faqih-3000`
- **Location:** vol. 2, p. 476 · seq 3009 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ وَ عَبْدُ الرَّحْمَنِ بْنُ الْحَجَّاجِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ الْكَسِيرُ وَ الْمَبْطُونُ يُرْمَى عَنْهُمَا قَالَ وَ الصِّبْيَانُ يُرْمَى عَنْهُمْ.
- **Isnad as currently extracted:**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ وَ عَبْدُ الرَّحْمَنِ بْنُ الْحَجَّاجِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ الْكَسِيرُ وَ الْمَبْطُونُ يُرْمَى عَنْهُمَا قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن عمار | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 217 · `faqih-3000` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ وَ عَبْدُ الرَّحْمَنِ بْنُ الْحَجَّاجِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "الْكَسِيرُ وَ الْمَبْطُونُ يُرْمَى عَنْهُمَا قَالَ وَ الصِّبْيَانُ يُرْمَى"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim.

---

### Chain 218 · `faqih-3000`
- **Location:** vol. 2, p. 476 · seq 3009 · chain 3
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ وَ عَبْدُ الرَّحْمَنِ بْنُ الْحَجَّاجِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ الْكَسِيرُ وَ الْمَبْطُونُ يُرْمَى عَنْهُمَا قَالَ وَ الصِّبْيَانُ يُرْمَى عَنْهُمْ.
- **Isnad as currently extracted:**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ وَ عَبْدُ الرَّحْمَنِ بْنُ الْحَجَّاجِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ الْكَسِيرُ وَ الْمَبْطُونُ يُرْمَى عَنْهُمَا قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عبد الرحمن بن الحجاج | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 218 · `faqih-3000` — CLARIFIED
- Transmitters (student → teacher): عبد الرحمن بن الحجاج → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ وَ عَبْدُ الرَّحْمَنِ بْنُ الْحَجَّاجِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "الْكَسِيرُ وَ الْمَبْطُونُ يُرْمَى عَنْهُمَا قَالَ وَ الصِّبْيَانُ يُرْمَى"
- Mursal opening: al-Ṣadūq → عبد الرحمن بن الحجاج; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim.

---

### Chain 219 · `faqih-3002`
- **Location:** vol. 2, p. 477 · seq 3011 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى ابْنُ مُسْكَانَ عَنْ جَعْفَرِ بْنِ نَاجِيَةَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَمَّنْ بَاتَ لَيَالِيَ مِنًى بِمَكَّةَ فَقَالَ عَلَيْهِ ثَلَاثَةٌ مِنَ الْغَنَمِ يَذْبَحُهُنَ‌[3].
- **Isnad as currently extracted:**
  > رَوَى ابْنُ مُسْكَانَ عَنْ جَعْفَرِ بْنِ نَاجِيَةَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَمَّنْ بَاتَ لَيَالِيَ مِنًى بِمَكَّةَ فَقَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن مسکان | روی |  |
  | 1 | named_narrator | جعفر بن ناجیة | عن |  |
  | 2 | imam | ابی عبد الله ع | عن |  |

### Chain 219 · `faqih-3002` — CLARIFIED
- Transmitters (student → teacher): ابن مسكان → جعفر بن ناجية → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى ابْنُ مُسْكَانَ عَنْ جَعْفَرِ بْنِ نَاجِيَةَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَمَّنْ بَاتَ لَيَالِيَ مِنًى بِمَكَّةَ فَقَالَ عَلَيْهِ ثَلَاثَةٌ"
- Mursal opening: al-Ṣadūq → ابن مسكان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 220 · `faqih-3020`
- **Location:** vol. 2, p. 481 · seq 3029 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى عَنْهُ جَمِيلُ بْنُ دَرَّاجٍ أَنَّهُ قَالَ‌ لَا بَأْسَ أَنْ يَنْفِرَ الرَّجُلُ فِي النَّفْرِ الْأَوَّلِ ثُمَّ يُقِيمَ بِمَكَّةَ[5] وَ قَالَ كَانَ أَبِي ع يَقُولُ مَنْ شَاءَ رَمَى الْجِمَارَ-
ارْتِفَاعَ النَّهَارِ[1] ثُمَّ يَنْفِرُ قَالَ فَقُلْتُ لَهُ‌[2] إِلَى مَتَى يَكُونُ رَمْيُ الْجِمَارِ فَقَالَ مِنِ ارْتِفَاعِ النَّهَارِ إِلَى غُرُوبِ الشَّمْسِ‌[3] وَ مَنْ أَصَابَ الصَّيْدَ فَلَيْسَ لَهُ أَنْ يَنْفِرَ فِي النَّفْرِ الْأَوَّلِ.
- **Isnad as currently extracted:**
  > وَ رَوَى عَنْهُ جَمِيلُ بْنُ دَرَّاجٍ أَنَّهُ قَالَ‌ لَا بَأْسَ أَنْ يَنْفِرَ الرَّجُلُ فِي النَّفْرِ الْأَوَّلِ ثُمَّ يُقِيمَ بِمَكَّةَ[5] وَ قَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عنه جمیل بن دراج | روی |  |

### Chain 220 · `faqih-3020` — CLARIFIED
- Transmitters (student → teacher): جميل بن دراج → أبو عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى عَنْهُ جَمِيلُ بْنُ دَرَّاجٍ أَنَّهُ قَالَ‌»
- Isnad ends / matn begins at: "لَا بَأْسَ أَنْ يَنْفِرَ الرَّجُلُ فِي النَّفْرِ الْأَوَّلِ ثُمَّ"
- Mursal opening: al-Ṣadūq → جميل بن دراج; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The complete al-Kāfī route explicitly reads ابن أبي عمير → جميل بن دراج → أبي عبد الله ع with the same opening ruling. Sources: [al-Kāfī, vol. 4, p. 521](https://najafdesertlibrary.com/book/%D8%A7%D9%84%D9%83%D8%A7%D9%81%D9%8A/v/4/p/521); [Thaqalayn, al-Kāfī 4:3:198, h. 6](https://thaqalayn.net/chapter/4/3/198).
---

### Chain 221 · `faqih-3032`
- **Location:** vol. 2, p. 486 · seq 3041 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى عَمَّارُ بْنُ مُوسَى السَّابَاطِيُ‌[2] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنِ الْأَضْحَى بِمِنًى قَالَ أَرْبَعَةُ أَيَّامٍ وَ عَنِ الْأَضْحَى فِي سَائِرِ الْبُلْدَانِ قَالَ ثَلَاثَةُ أَيَّامٍ وَ قَالَ لَوْ أَنَّ رَجُلًا قَدِمَ إِلَى أَهْلِهِ بَعْدَ الْأَضْحَى بِيَوْمَيْنِ ضَحَّى الْيَوْمَ الثَّالِثَ الَّذِي يَقْدَمُ فِيهِ‌[3].
- **Isnad as currently extracted:**
  > رَوَى عَمَّارُ بْنُ مُوسَى السَّابَاطِيُ‌[2] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنِ الْأَضْحَى بِمِنًى قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عمار بن موسی الساباطی | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 221 · `faqih-3032` — CLARIFIED
- Transmitters (student → teacher): عمار بن موسي الساباطي → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى عَمَّارُ بْنُ مُوسَى السَّابَاطِيُ‌[2] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْأَضْحَى بِمِنًى قَالَ أَرْبَعَةُ أَيَّامٍ وَ عَنِ"
- Mursal opening: al-Ṣadūq → عمار بن موسي الساباطي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 222 · `faqih-3035`
- **Location:** vol. 2, p. 488 · seq 3045 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > روي عن معاوية بن عمار قال‌ سألت أبا عبد الله ع عن يوم‌ الحج الأكبر فقال هو يوم النحر و الأصغر هو العمرة[1].
- **Isnad as currently extracted:**
  > روي عن معاوية بن عمار قال‌ سألت
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن معاویة بن عمار | روی |  |

### Chain 222 · `faqih-3035` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار
- Corrected isnad (Arabic): «روي عن معاوية بن عمار قال‌»
- Isnad ends / matn begins at: "سألت أبا عبد الله ع عن يوم‌ الحج الأكبر"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 223 · `faqih-3043`
- **Location:** vol. 2, p. 490 · seq 3053 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ دَاوُدَ الرَّقِّيِّ قَالَ‌ سَأَلَنِي بَعْضُ الْخَوَارِجِ عَنْ هَذِهِ الْآيَةِ مِنْ كِتَابِ اللَّهِ تَعَالَى‌ ثَمانِيَةَ أَزْواجٍ مِنَ الضَّأْنِ اثْنَيْنِ وَ مِنَ الْمَعْزِ اثْنَيْنِ‌ إِلَى قَوْلِهِ تَعَالَى- وَ مِنَ الْإِبِلِ اثْنَيْنِ وَ مِنَ الْبَقَرِ اثْنَيْنِ‌ مَا الَّذِي أَحَلَّ اللَّهُ عَزَّ وَ جَلَّ مِنْ ذَلِكَ وَ مَا الَّذِي حَرَّمَ فَلَمْ يَكُنْ عِنْدِي فِيهِ شَيْ‌ءٌ فَدَخَلْتُ عَلَى أَبِي عَبْدِ اللَّهِ ع وَ أَنَا حَاجٌّ فَأَخْبَرْتُهُ بِمَا كَانَ فَقَالَ إِنَّ اللَّهَ تَبَارَكَ وَ تَعَالَى أَحَلَّ فِي الْأُضْحِيَّةِ بِمِنًى الضَّأْنَ وَ الْمَعْزَ الْأَهْلِيَّةَ وَ حَرَّمَ أَنْ يُضَحَّى فِيهِ بِالْجَبَلِيَّةِ وَ أَمَّا قَوْلُهُ عَزَّ وَ جَلَ‌ وَ مِنَ الْإِبِلِ اثْنَيْنِ وَ مِنَ الْبَقَرِ اثْنَيْنِ‌ فَإِنَّ اللَّهَ تَبَارَكَ وَ تَعَالَى أَحَلَّ فِي الْأُضْحِيَّةِ بِمِنًى الْإِبِلَ الْعِرَابَ وَ حَرَّمَ فِيهَا الْبَخَاتِيَ‌[2]
وَ أَحَلَّ الْبَقَرَ الْأَهْلِيَّةَ أَنْ يُضَحَّى بِهَا وَ حَرَّمَ الْجَبَلِيَّةَ فَانْصَرَفْتُ إِلَى الرَّجُلِ وَ أَخْبَرْتُهُ بِهَذَا الْجَوَابِ فَقَالَ هَذَا شَيْ‌ءٌ حَمَلَتْهُ الْإِبِلُ مِنَ الْحِجَازِ[1].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ دَاوُدَ الرَّقِّيِّ قَالَ‌ سَأَلَنِي بَعْضُ الْخَوَارِجِ عَنْ هَذِهِ الْآيَةِ مِنْ كِتَابِ اللَّهِ تَعَالَى‌ ثَمانِيَةَ أَزْواجٍ مِنَ الضَّأْنِ اثْنَيْنِ وَ مِنَ الْمَعْزِ اثْنَيْنِ‌ إِلَى قَوْلِهِ تَعَالَى- وَ مِنَ الْإِبِلِ اثْنَيْنِ وَ مِنَ الْبَقَرِ اثْنَيْنِ‌ مَا الَّذِي أَحَلَّ اللَّهُ عَزَّ وَ جَلَّ مِنْ ذَلِكَ وَ مَا الَّذِي حَرَّمَ فَلَمْ يَكُنْ عِنْدِي فِيهِ شَيْ‌ءٌ فَدَخَلْتُ عَلَى أَبِي عَبْدِ اللَّهِ ع وَ أَنَا حَاجٌّ فَأَخْبَرْتُهُ بِمَا كَانَ فَقَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن داود الرقی | روی |  |

### Chain 223 · `faqih-3043` — CLARIFIED
- Transmitters (student → teacher): داود الرقي
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ دَاوُدَ الرَّقِّيِّ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلَنِي بَعْضُ الْخَوَارِجِ عَنْ هَذِهِ الْآيَةِ مِنْ كِتَابِ اللَّهِ"
- Mursal opening: al-Ṣadūq → داود الرقي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 224 · `faqih-3062`
- **Location:** vol. 2, p. 498 · seq 3072 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى الْبَزَنْطِيُّ عَنْ عَبْدِ الْكَرِيمِ بْنِ عَمْرٍو عَنْ سَعِيدِ بْنِ يَسَارٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَمَّنِ اشْتَرَى شَاةً وَ لَمْ يُعَرِّفْ بِهَا فَقَالَ لَا بَأْسَ عَرَّفَ بِهَا-
أَوْ لَمْ يُعَرِّفْ بِهَا[1].
- **Isnad as currently extracted:**
  > وَ رَوَى الْبَزَنْطِيُّ عَنْ عَبْدِ الْكَرِيمِ بْنِ عَمْرٍو عَنْ سَعِيدِ بْنِ يَسَارٍ قَالَ‌ سَأَلْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | البزنطی | روی |  |
  | 1 | named_narrator | عبد الکریم بن عمرو | عن |  |
  | 2 | named_narrator | سعید بن یسار | عن |  |

### Chain 224 · `faqih-3062` — CLARIFIED
- Transmitters (student → teacher): البزنطي → عبد الكريم بن عمرو → سعيد بن يسار
- Corrected isnad (Arabic): «وَ رَوَى الْبَزَنْطِيُّ عَنْ عَبْدِ الْكَرِيمِ بْنِ عَمْرٍو عَنْ سَعِيدِ بْنِ يَسَارٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَمَّنِ اشْتَرَى شَاةً وَ"
- Mursal opening: al-Ṣadūq → البزنطي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 225 · `faqih-3066`
- **Location:** vol. 2, p. 500 · seq 3076 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ حَفْصِ بْنِ الْبَخْتَرِيِ‌[3] قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ سَاقَ الْهَدْيَ فَعَطِبَ‌[4] فِي مَوْضِعٍ لَا يَقْدِرُ عَلَى مَنْ يَتَصَدَّقُ بِهِ عَلَيْهِ وَ لَا يَعْلَمُ أَنَّهُ هَدْيٌ فَقَالَ يَنْحَرُهُ وَ يَكْتُبُ كِتَاباً يَضَعُهُ عَلَيْهِ لِيَعْلَمَ مَنْ مَرَّ بِهِ أَنَّهُ صَدَقَةٌ[5].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ حَفْصِ بْنِ الْبَخْتَرِيِ‌[3] قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن حفص بن البختری | روی |  |

### Chain 225 · `faqih-3066` — CLARIFIED
- Transmitters (student → teacher): حفص بن البختري → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ حَفْصِ بْنِ الْبَخْتَرِيِ‌[3] قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ سَاقَ الْهَدْيَ فَعَطِبَ‌[4]"
- Mursal opening: al-Ṣadūq → حفص بن البختري; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 226 · `faqih-3067`
- **Location:** vol. 2, p. 500 · seq 3077 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى الْقَاسِمُ بْنُ مُحَمَّدٍ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ[6] قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ سَاقَ بَدَنَةً فَانْكَسَرَتْ قَبْلَ أَنْ تَبْلُغَ مَحِلَّهَا أَوْ عَرَضَ لَهَا مَوْتٌ أَوْ هَلَاكٌ قَالَ يُذَكِّيهَا إِنْ قَدَرَ عَلَى ذَلِكَ وَ يَلْطَخُ نَعْلَهَا الَّتِي قُلِّدَتْ بِهَا حَتَّى يَعْلَمَ مَنْ مَرَّ
بِهَا أَنَّهَا قَدْ ذُكِّيَتْ فَيَأْكُلَ مِنْ لَحْمِهَا إِنْ أَرَادَ فَإِنْ كَانَ الْهَدْيُ مَضْمُوناً فَإِنَّ عَلَيْهِ أَنْ يُعِيدَهُ يَبْتَاعُ مَكَانَ الْهَدْيِ إِذَا انْكَسَرَ أَوْ هَلَكَ وَ الْمَضْمُونُ الْوَاجِبُ عَلَيْهِ فِي نَذْرٍ أَوْ غَيْرِهِ فَإِنْ لَمْ يَكُنْ مَضْمُوناً وَ إِنَّمَا هُوَ شَيْ‌ءٌ تَطَوَّعَ بِهِ فَلَيْسَ عَلَيْهِ أَنْ يَبْتَاعَ مَكَانَهُ إِلَّا أَنْ يَشَاءَ أَنْ يَتَطَوَّعَ.
- **Isnad as currently extracted:**
  > وَ رَوَى الْقَاسِمُ بْنُ مُحَمَّدٍ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ[6] قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | القاسم بن محمد | روی |  |
  | 1 | named_narrator | علی بن ابی حمزة | عن |  |

### Chain 226 · `faqih-3067` — CLARIFIED
- Transmitters (student → teacher): القاسم بن محمد → علي بن ابي حمزة → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى الْقَاسِمُ بْنُ مُحَمَّدٍ عَنْ عَلِيِّ بْنِ أَبِي حَمْزَةَ[6] قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ سَاقَ بَدَنَةً"
- Mursal opening: al-Ṣadūq → القاسم بن محمد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 227 · `faqih-3068`
- **Location:** vol. 2, p. 501 · seq 3078 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ قَالَ‌ سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنْ رَجُلٍ اشْتَرَى هَدْياً لِمُتْعَتِهِ فَأَتَى بِهِ مَنْزِلَهُ فَرَبَطَهُ ثُمَّ انْحَلَّ فَهَلَكَ هَلْ يُجْزِيهِ أَوْ يُعِيدُ قَالَ لَا يُجْزِيهِ إِلَّا أَنْ يَكُونَ لَا قُوَّةَ بِهِ عَلَيْهِ‌[1].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن عبد الرحمن بن الحجاج | روی |  |

### Chain 227 · `faqih-3068` — CLARIFIED
- Transmitters (student → teacher): عبد الرحمن بن الحجاج → ابا ابراهيم ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنْ رَجُلٍ اشْتَرَى هَدْياً لِمُتْعَتِهِ"
- Mursal opening: al-Ṣadūq → عبد الرحمن بن الحجاج; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 228 · `faqih-3069`
- **Location:** vol. 2, p. 501 · seq 3079 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى ابْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ اشْتَرَى كَبْشاً فَهَلَكَ مِنْهُ قَالَ يَشْتَرِي مَكَانَهُ آخَرَ قُلْتُ فَإِنِ اشْتَرَى مَكَانَهُ ثُمَّ وَجَدَ الْأَوَّلَ قَالَ إِنْ كَانَا جَمِيعاً قَائِمَيْنِ فَلْيَذْبَحِ الْأَوَّلَ وَ لْيَبِعِ الْآخَرَ وَ إِنْ شَاءَ ذَبَحَهُ وَ إِنْ كَانَ قَدْ ذَبَحَ الْآخَرَ فَلْيَذْبَحِ الْأَوَّلَ مَعَهُ‌[2].
- **Isnad as currently extracted:**
  > وَ رَوَى ابْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن مسکان | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |

### Chain 228 · `faqih-3069` — CLARIFIED
- Transmitters (student → teacher): ابن مسكان → ابي بصير → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى ابْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ اشْتَرَى كَبْشاً"
- Mursal opening: al-Ṣadūq → ابن مسكان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 229 · `faqih-3071`
- **Location:** vol. 2, p. 502 · seq 3081 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنِ الْهَدْيِ الْوَاجِبِ إِنْ أَصَابَهُ كَسْرٌ أَوْ عَطَبٌ أَ يَبِيعُهُ وَ إِنْ بَاعَهُ مَا يَصْنَعُ بِثَمَنِهِ قَالَ إِنْ بَاعَهُ فَلْيَتَصَدَّقْ بِثَمَنِهِ وَ يُهْدِي هَدْياً آخَرَ[1].
- **Isnad as currently extracted:**
  > وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنِ الْهَدْيِ الْوَاجِبِ إِنْ أَصَابَهُ كَسْرٌ أَوْ عَطَبٌ أَ يَبِيعُهُ وَ إِنْ بَاعَهُ مَا يَصْنَعُ بِثَمَنِهِ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | العلاء | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |
  | 2 | imam | احدهما ع | عن | ambiguous |

### Chain 229 · `faqih-3071` — CLARIFIED
- Transmitters (student → teacher): العلاء → محمد بن مسلم → احدهما ع
- Corrected isnad (Arabic): «وَ رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْهَدْيِ الْوَاجِبِ إِنْ أَصَابَهُ كَسْرٌ أَوْ عَطَبٌ"
- Mursal opening: al-Ṣadūq → العلاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 230 · `faqih-3084`
- **Location:** vol. 2, p. 505 · seq 3094 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى ابْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الرَّجُلُ يُوصِي مَنْ يَذْبَحُ عَنْهُ وَ يُلْقِي هُوَ شَعْرَهُ بِمَكَّةَ فَقَالَ لَيْسَ لَهُ أَنْ يُلْقِيَ شَعْرَهُ إِلَّا بِمِنًى‌[3].
- **Isnad as currently extracted:**
  > رَوَى ابْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن مسکان | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |

### Chain 230 · `faqih-3084` — CLARIFIED
- Transmitters (student → teacher): ابن مسكان → ابي بصير → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى ابْنُ مُسْكَانَ عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الرَّجُلُ يُوصِي مَنْ يَذْبَحُ"
- Mursal opening: al-Ṣadūq → ابن مسكان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 231 · `faqih-3085`
- **Location:** vol. 2, p. 505 · seq 3095 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى ابْنُ أَبِي عُمَيْرٍ[4] عَنْ جَمِيلِ بْنِ دَرَّاجٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌
سَأَلْتُهُ عَنِ الرَّجُلِ يَزُورُ الْبَيْتَ قَبْلَ أَنْ يَحْلِقَ قَالَ لَا يَنْبَغِي إِلَّا أَنْ يَكُونَ نَاسِياً ثُمَّ قَالَ إِنَّ رَسُولَ اللَّهِ ص أَتَاهُ أُنَاسٌ- يَوْمَ النَّحْرِ فَقَالَ بَعْضُهُمْ يَا رَسُولَ اللَّهِ حَلَقْتُ قَبْلَ أَنْ أَذْبَحَ وَ قَالَ بَعْضُهُمْ حَلَقْتُ قَبْلَ أَنْ أَرْمِيَ فَلَمْ يَتْرُكُوا شَيْئاً كَانَ يَنْبَغِي لَهُمْ أَنْ يُقَدِّمُوهُ إِلَّا أَخَّرُوهُ وَ لَا شَيْئاً كَانَ يَنْبَغِي لَهُمْ أَنْ يُؤَخِّرُوهُ إِلَّا قَدَّمُوهُ فَقَالَ لَا حَرَجَ‌[1].
- **Isnad as currently extracted:**
  > رَوَى ابْنُ أَبِي عُمَيْرٍ[4] عَنْ جَمِيلِ بْنِ دَرَّاجٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنِ الرَّجُلِ يَزُورُ الْبَيْتَ قَبْلَ أَنْ يَحْلِقَ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن ابی عمیر | روی |  |
  | 1 | named_narrator | جمیل بن دراج | عن |  |
  | 2 | imam | ابی عبد الله ع | عن |  |

### Chain 231 · `faqih-3085` — CLARIFIED
- Transmitters (student → teacher): ابن ابي عمير → جميل بن دراج → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى ابْنُ أَبِي عُمَيْرٍ[4] عَنْ جَمِيلِ بْنِ دَرَّاجٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الرَّجُلِ يَزُورُ الْبَيْتَ قَبْلَ أَنْ يَحْلِقَ قَالَ"
- Mursal opening: al-Ṣadūq → ابن ابي عمير; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 232 · `faqih-3087`
- **Location:** vol. 2, p. 506 · seq 3097 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى عَلِيُّ بْنُ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ جَهِلَ أَنْ يُقَصِّرَ مِنْ شَعْرِهِ أَوْ يَحْلِقَهُ حَتَّى ارْتَحَلَ مِنْ مِنًى قَالَ فَلْيَرْجِعْ إِلَى مِنًى حَتَّى يُلْقِيَ شَعْرَهُ بِهَا حَلْقاً كَانَ أَوْ تَقْصِيراً وَ عَلَى الصَّرُورَةِ الْحَلْقُ‌[2].
وَ رُوِيَ أَنَّهُ يَحْلِقُ بِمَكَّةَ وَ يَحْمِلُ شَعْرَهُ إِلَى مِنًى‌[1].
- **Isnad as currently extracted:**
  > رَوَى عَلِيُّ بْنُ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن ابی حمزة | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |

### Chain 232 · `faqih-3087` — CLARIFIED
- Transmitters (student → teacher): علي بن ابي حمزة → ابي بصير → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى عَلِيُّ بْنُ أَبِي حَمْزَةَ عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ جَهِلَ أَنْ"
- Mursal opening: al-Ṣadūq → علي بن ابي حمزة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 233 · `faqih-3093`
- **Location:** vol. 2, p. 511 · seq 3103 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنِ ابْنِ مُسْكَانَ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ تَمَتَّعَ فَلَمْ يَجِدْ مَا يُهْدِي فَصَامَ ثَلَاثَةَ أَيَّامٍ فَلَمَّا قَضَى نُسُكَهُ بَدَا لَهُ أَنْ يُقِيمَ سَنَةً قَالَ فَلْيَنْظُرْ مَنْهَلَ أَهْلِ بَلَدِهِ‌[1] فَإِذَا ظَنَّ أَنَّهُمْ قَدْ دَخَلُوا بَلَدَهُمْ فَلْيَصُمِ السَّبْعَةَ الْأَيَّامِ‌[2].
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنِ ابْنِ مُسْكَانَ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ تَمَتَّعَ فَلَمْ يَجِدْ مَا يُهْدِي فَصَامَ ثَلَاثَةَ أَيَّامٍ فَلَمَّا قَضَى نُسُكَهُ بَدَا لَهُ أَنْ يُقِيمَ سَنَةً قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن ابن مسکان | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |

### Chain 233 · `faqih-3093` — CLARIFIED
- Transmitters (student → teacher): ابن مسكان → أبو بصير → إمامٌ غير مصرّح باسمه في هذا الطريق (مضمرة أبي بصير)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنِ ابْنِ مُسْكَانَ عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ تَمَتَّعَ فَلَمْ يَجِدْ مَا يُهْدِي فَصَامَ"
- Mursal opening: al-Ṣadūq → ابن مسكان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: This is explicitly discussed as «صحيحة أبي بصير المضمرة». The chain is therefore represented with an unnamed Imam rather than assigned to a specific Imam without an explicit parallel. Sources: [al-Tahdhīb, vol. 4, p. 314](https://ar.lib.eshia.ir/10083/4/314); [juristic discussion](https://lib.eshia.ir/10598/5/306).
---

### Chain 234 · `faqih-3104`
- **Location:** vol. 2, p. 517 · seq 3114 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الرَّجُلِ يَبْعَثُ بِالْهَدْيِ تَطَوُّعاً وَ لَيْسَ بِوَاجِبٍ‌[3] فَقَالَ يُوَاعِدُ أَصْحَابَهُ يَوْماً فَيُقَلِّدُونَهُ‌[4] فَإِذَا كَانَ تِلْكَ السَّاعَةُ اجْتَنَبَ مَا يَجْتَنِبُهُ الْمُحْرِمُ إِلَى يَوْمِ النَّحْرِ فَإِذَا كَانَ يَوْمُ النَّحْرِ أَجْزَأَ عَنْهُ‌[5] فَإِنَّ رَسُولَ اللَّهِ ص حِينَ صَدَّهُ الْمُشْرِكُونَ يَوْمَ الْحُدَيْبِيَةِ نَحَرَ وَ أَحَلَّ وَ رَجَعَ‌
إِلَى الْمَدِينَةِ[1].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن معاویة بن عمار | روی |  |

### Chain 234 · `faqih-3104` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار
- Corrected isnad (Arabic): «رُوِيَ عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الرَّجُلِ يَبْعَثُ بِالْهَدْيِ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 235 · `faqih-3106`
- **Location:** vol. 2, p. 519 · seq 3116 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ بُكَيْرِ بْنِ أَعْيَنَ عَنْ أَخِيهِ زُرَارَةَ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع جَعَلَنِيَ اللَّهُ فِدَاكَ أَسْأَلُكَ فِي الْحَجِّ مُنْذُ أَرْبَعِينَ عَاماً فَتُفْتِينِي‌[1] فَقَالَ يَا زُرَارَةُ بَيْتٌ يُحَجُّ قَبْلَ آدَمَ ع بِأَلْفَيْ عَامٍ‌[2] تُرِيدُ أَنْ تَفْنَى مَسَائِلُهُ فِي أَرْبَعِينَ عَاماً.
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ بُكَيْرِ بْنِ أَعْيَنَ عَنْ أَخِيهِ زُرَارَةَ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن بکیر بن اعین | روی |  |
  | 1 | named_narrator | اخیه زرارة | عن |  |

### Chain 235 · `faqih-3106` — CLARIFIED
- Transmitters (student → teacher): بكير بن اعين → اخيه زرارة → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنْ بُكَيْرِ بْنِ أَعْيَنَ عَنْ أَخِيهِ زُرَارَةَ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع جَعَلَنِيَ اللَّهُ فِدَاكَ أَسْأَلُكَ"
- Mursal opening: al-Ṣadūq → بكير بن اعين; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 236 · `faqih-3113`
- **Location:** vol. 2, p. 521 · seq 3123 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى سَعْدُ بْنُ سَعْدٍ الْأَشْعَرِيُّ عَنِ الرِّضَا ع قَالَ‌ قُلْتُ الْمُحْرِمُ يَشْتَرِي الْجَوَارِيَ أَوْ يَبِيعُ فَقَالَ نَعَمْ‌[3].
- **Isnad as currently extracted:**
  > وَ رَوَى سَعْدُ بْنُ سَعْدٍ الْأَشْعَرِيُّ عَنِ الرِّضَا ع قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | سعد بن سعد الاشعری | روی |  |
  | 1 | imam | الرضا ع | عن |  |

### Chain 236 · `faqih-3113` — CLARIFIED
- Transmitters (student → teacher): سعد بن سعد الاشعري → الرضا ع
- Corrected isnad (Arabic): «وَ رَوَى سَعْدُ بْنُ سَعْدٍ الْأَشْعَرِيُّ عَنِ الرِّضَا ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ الْمُحْرِمُ يَشْتَرِي الْجَوَارِيَ أَوْ يَبِيعُ فَقَالَ نَعَمْ‌[3]."
- Mursal opening: al-Ṣadūq → سعد بن سعد الاشعري; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 237 · `faqih-3119`
- **Location:** vol. 2, p. 522 · seq 3129 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى أَحْمَدُ بْنُ مُحَمَّدِ بْنِ أَبِي نَصْرٍ الْبَزَنْطِيُّ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ قُلْتُ لَهُ إِنَّ أَصْحَابَنَا يَرْوُونَ أَنَّ حَلْقَ الرَّأْسِ فِي غَيْرِ حَجٍّ وَ لَا عُمْرَةٍ مُثْلَةٌ فَقَالَ‌
- **Isnad as currently extracted:**
  > وَ رَوَى أَحْمَدُ بْنُ مُحَمَّدِ بْنِ أَبِي نَصْرٍ الْبَزَنْطِيُّ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | احمد بن محمد بن ابی نصر البزنطی | روی |  |
  | 1 | imam | ابی الحسن ع | عن |  |

### Chain 237 · `faqih-3119` — CLARIFIED
- Transmitters (student → teacher): احمد بن محمد بن ابي نصر البزنطي → ابي الحسن ع
- Corrected isnad (Arabic): «وَ رَوَى أَحْمَدُ بْنُ مُحَمَّدِ بْنِ أَبِي نَصْرٍ الْبَزَنْطِيُّ عَنْ أَبِي الْحَسَنِ ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ إِنَّ أَصْحَابَنَا يَرْوُونَ أَنَّ حَلْقَ الرَّأْسِ فِي"
- Mursal opening: al-Ṣadūq → احمد بن محمد بن ابي نصر البزنطي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 238 · `faqih-3122`
- **Location:** vol. 2, p. 524 · seq 3133 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ أَفْرَدَ الْحَجَّ فَلَمَّا دَخَلَ مَكَّةَ طَافَ بِالْبَيْتِ ثُمَّ أَتَى أَصْحَابَهُ وَ هُمْ يُقَصِّرُونَ فَقَصَّرَ مَعَهُمْ ثُمَّ ذَكَرَ بَعْدَ مَا قَصَّرَ أَنَّهُ مُفْرِدٌ لِلْحَجِّ فَقَالَ لَيْسَ عَلَيْهِ شَيْ‌ءٌ إِذَا صَلَّى فَلْيُجَدِّدِ التَّلْبِيَةَ[1].
- **Isnad as currently extracted:**
  > وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ أَفْرَدَ الْحَجَّ فَلَمَّا دَخَلَ مَكَّةَ طَافَ بِالْبَيْتِ ثُمَّ أَتَى أَصْحَابَهُ وَ هُمْ يُقَصِّرُونَ فَقَصَّرَ مَعَهُمْ ثُمَّ ذَكَرَ بَعْدَ مَا قَصَّرَ أَنَّهُ مُفْرِدٌ لِلْحَجِّ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن عمار | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 238 · `faqih-3122` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار → ابي عبد الله ع
- Corrected isnad (Arabic): «وَ رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ أَفْرَدَ الْحَجَّ فَلَمَّا دَخَلَ مَكَّةَ طَافَ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 239 · `faqih-3123`
- **Location:** vol. 2, p. 524 · seq 3134 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنْ عَلِيِّ بْنِ يَقْطِينٍ قَالَ‌ سَأَلْتُ أَبَا الْحَسَنِ الْأَوَّلَ ع عَنْ رَجُلٍ يُعْطِي خَمْسَةَ نَفَرٍ حَجَّةً وَاحِدَةً يَخْرُجُ فِيهَا وَاحِدٌ مِنْهُمْ أَ لَهُمْ أَجْرٌ قَالَ نَعَمْ لِكُلِّ وَاحِدٍ مِنْهُمْ أَجْرُ حَاجٍّ قَالَ فَقُلْتُ فَأَيُّهُمْ أَعْظَمُ أَجْراً فَقَالَ الَّذِي نَابَهُ الْحَرُّ وَ الْبَرْدُ[2] وَ إِنْ كَانَ صَرُورَةً لَمْ يُجْزِ ذَلِكَ عَنْهُمْ وَ الْحَجُّ لِمَنْ حَجَّ.
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنْ عَلِيِّ بْنِ يَقْطِينٍ قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن علی بن یقطین | روی |  |

### Chain 239 · `faqih-3123` — CLARIFIED
- Transmitters (student → teacher): علي بن يقطين → ابا الحسن الاول ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رُوِيَ عَنْ عَلِيِّ بْنِ يَقْطِينٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا الْحَسَنِ الْأَوَّلَ ع عَنْ رَجُلٍ يُعْطِي خَمْسَةَ"
- Mursal opening: al-Ṣadūq → علي بن يقطين; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 240 · `faqih-3137`
- **Location:** vol. 2, p. 559 · seq 3148 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى صَفْوَانُ عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ قَالَ‌ سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنِ الصَّلَاةِ فِي مَسْجِدِ غَدِيرِ خُمٍّ بِالنَّهَارِ وَ أَنَا مُسَافِرٌ فَقَالَ صَلِّ فِيهِ فَإِنَّ فِيهِ فَضْلًا وَ قَدْ كَانَ أَبِي ع يَأْمُرُ بِذَلِكَ.
- **Isnad as currently extracted:**
  > وَ رَوَى صَفْوَانُ عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان | روی |  |
  | 1 | named_narrator | عبد الرحمن بن الحجاج | عن |  |

### Chain 240 · `faqih-3137` — CLARIFIED
- Transmitters (student → teacher): صفوان → عبد الرحمن بن الحجاج → ابا ابراهيم ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى صَفْوَانُ عَنْ عَبْدِ الرَّحْمَنِ بْنِ الْحَجَّاجِ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا إِبْرَاهِيمَ ع عَنِ الصَّلَاةِ فِي مَسْجِدِ غَدِيرِ"
- Mursal opening: al-Ṣadūq → صفوان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 241 · `faqih-3140`
- **Location:** vol. 2, p. 560 · seq 3151 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى عَلِيُّ بْنُ مَهْزِيَارَ عَنْ مُحَمَّدِ بْنِ الْقَاسِمِ بْنِ الْفُضَيْلِ قَالَ‌ قُلْتُ لِأَبِي الْحَسَنِ ع جُعِلْتُ فِدَاكَ إِنَّ جَمَّالَنَا مَرَّ بِنَا وَ لَمْ يَنْزِلِ الْمُعَرَّسَ فَقَالَ لَا بُدَّ أَنْ تَرْجِعُوا إِلَيْهِ فَرَجَعْنَا إِلَيْهِ‌[2].
- **Isnad as currently extracted:**
  > وَ رَوَى عَلِيُّ بْنُ مَهْزِيَارَ عَنْ مُحَمَّدِ بْنِ الْقَاسِمِ بْنِ الْفُضَيْلِ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن مهزیار | روی |  |
  | 1 | named_narrator | محمد بن القاسم بن الفضیل | عن |  |

### Chain 241 · `faqih-3140` — CLARIFIED
- Transmitters (student → teacher): علي بن مهزيار → محمد بن القاسم بن الفضيل → ابي الحسن ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «وَ رَوَى عَلِيُّ بْنُ مَهْزِيَارَ عَنْ مُحَمَّدِ بْنِ الْقَاسِمِ بْنِ الْفُضَيْلِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي الْحَسَنِ ع جُعِلْتُ فِدَاكَ إِنَّ جَمَّالَنَا مَرَّ"
- Mursal opening: al-Ṣadūq → علي بن مهزيار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 242 · `faqih-3148`
- **Location:** vol. 2, p. 563 · seq 3159 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى أَبَانٌ عَنْ أَبِي الْعَبَّاسِ يَعْنِي الْفَضْلَ بْنَ عَبْدِ الْمَلِكِ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع حَرَّمَ رَسُولُ اللَّهِ ص الْمَدِينَةَ فَقَالَ نَعَمْ حَرَّمَ بَرِيداً فِي بَرِيدٍ عِضَاهاً قُلْتُ صَيْدَهَا قَالَ لَا يَكْذِبُ النَّاسُ‌[3].
- **Isnad as currently extracted:**
  > وَ رَوَى أَبَانٌ عَنْ أَبِي الْعَبَّاسِ يَعْنِي الْفَضْلَ بْنَ عَبْدِ الْمَلِكِ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابان | روی |  |
  | 1 | named_narrator | ابی العباس یعنی الفضل بن عبد الملک | عن |  |

### Chain 242 · `faqih-3148` — CLARIFIED
- Transmitters (student → teacher): ابان → ابي العباس يعني الفضل بن عبد الملك
- Corrected isnad (Arabic): «وَ رَوَى أَبَانٌ عَنْ أَبِي الْعَبَّاسِ يَعْنِي الْفَضْلَ بْنَ عَبْدِ الْمَلِكِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع حَرَّمَ رَسُولُ اللَّهِ ص"
- Mursal opening: al-Ṣadūq → ابان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 243 · `faqih-3157`
- **Location:** vol. 2, p. 578 · seq 3168 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى صَالِحُ بْنُ عُقْبَةَ عَنْ زَيْدٍ الشَّحَّامِ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع مَا لِمَنْ زَارَ وَاحِداً مِنْكُمْ قَالَ كَمَنْ زَارَ رَسُولَ اللَّهِ ص.
- **Isnad as currently extracted:**
  > وَ رَوَى صَالِحُ بْنُ عُقْبَةَ عَنْ زَيْدٍ الشَّحَّامِ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صالح بن عقبة | روی |  |
  | 1 | named_narrator | زید الشحام | عن |  |

### Chain 243 · `faqih-3157` — CLARIFIED
- Transmitters (student → teacher): صالح بن عقبة → زيد الشحام
- Corrected isnad (Arabic): «وَ رَوَى صَالِحُ بْنُ عُقْبَةَ عَنْ زَيْدٍ الشَّحَّامِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع مَا لِمَنْ زَارَ وَاحِداً"
- Mursal opening: al-Ṣadūq → صالح بن عقبة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 244 · `faqih-3163`
- **Location:** vol. 2, p. 580 · seq 3174 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > وَ رَوَى صَالِحُ بْنُ عُقْبَةَ عَنْ بَشِيرٍ الدَّهَّانِ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رُبَّمَا فَاتَنِي الْحَجُّ فَأُعَرِّفُ عِنْدَ قَبْرِ الْحُسَيْنِ ع‌[1] قَالَ أَحْسَنْتَ يَا بَشِيرُ أَيُّمَا مُؤْمِنٍ أَتَى قَبْرَ الْحُسَيْنِ ع عَارِفاً بِحَقِّهِ فِي غَيْرِ يَوْمِ عِيدٍ كُتِبَتْ لَهُ عِشْرُونَ حَجَّةً وَ عِشْرُونَ عُمْرَةً مَبْرُورَاتٍ مُتَقَبَّلَاتٍ وَ عِشْرُونَ غَزْوَةً مَعَ نَبِيٍّ مُرْسَلٍ أَوْ إِمَامٍ عَادِلٍ وَ مَنْ أَتَاهُ فِي يَوْمِ عِيدٍ كُتِبَتْ لَهُ أَلْفُ حَجَّةٍ وَ أَلْفُ عُمْرَةٍ مَبْرُورَاتٍ مُتَقَبَّلَاتٍ وَ أَلْفُ غَزْوَةٍ مَعَ نَبِيٍّ مُرْسَلٍ أَوْ إِمَامٍ عَادِلٍ قَالَ فَقُلْتُ لَهُ وَ كَيْفَ لِي بِمِثْلِ الْمَوْقِفِ قَالَ فَنَظَرَ إِلَيَّ شِبْهَ الْمُغْضَبِ ثُمَّ قَالَ يَا بَشِيرُ إِنَّ الْمُؤْمِنَ إِذَا أَتَى قَبْرَ الْحُسَيْنِ ع- يَوْمَ عَرَفَةَ عَارِفاً بِحَقِّهِ فَاغْتَسَلَ بِالْفُرَاتِ ثُمَّ تَوَجَّهَ إِلَيْهِ كَتَبَ اللَّهُ عَزَّ وَ جَلَّ لَهُ بِكُلِّ خُطْوَةٍ حَجَّةً بِمَنَاسِكِهَا وَ لَا أَعْلَمُهُ إِلَّا قَالَ وَ عُمْرَةً.
- **Isnad as currently extracted:**
  > وَ رَوَى صَالِحُ بْنُ عُقْبَةَ عَنْ بَشِيرٍ الدَّهَّانِ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صالح بن عقبة | روی |  |
  | 1 | named_narrator | بشیر الدهان | عن |  |

### Chain 244 · `faqih-3163` — CLARIFIED
- Transmitters (student → teacher): صالح بن عقبة → بشير الدهان
- Corrected isnad (Arabic): «وَ رَوَى صَالِحُ بْنُ عُقْبَةَ عَنْ بَشِيرٍ الدَّهَّانِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رُبَّمَا فَاتَنِي الْحَجُّ فَأُعَرِّفُ"
- Mursal opening: al-Ṣadūq → صالح بن عقبة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 245 · `faqih-3174`
- **Location:** vol. 2, p. 582 · seq 3185 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رُوِيَ عَنِ الْحَسَنِ بْنِ عَلِيٍّ الْوَشَّاءِ عَنْ أَبِي الْحَسَنِ الرِّضَا ع قَالَ‌ سَأَلْتُهُ عَنْ زِيَارَةِ قَبْرِ أَبِي الْحَسَنِ مُوسَى بْنِ جَعْفَرٍ ع مِثْلُ زِيَارَةِ الْحُسَيْنِ ع قَالَ نَعَمْ.
- **Isnad as currently extracted:**
  > وَ رُوِيَ عَنِ الْحَسَنِ بْنِ عَلِيٍّ الْوَشَّاءِ عَنْ أَبِي الْحَسَنِ الرِّضَا ع قَالَ‌ سَأَلْتُهُ عَنْ زِيَارَةِ قَبْرِ أَبِي الْحَسَنِ مُوسَى بْنِ جَعْفَرٍ ع مِثْلُ زِيَارَةِ الْحُسَيْنِ ع قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن الحسن بن علی الوشاء | روی |  |
  | 1 | imam | ابی الحسن الرضا ع | عن |  |

### Chain 245 · `faqih-3174` — CLARIFIED
- Transmitters (student → teacher): الحسن بن علي الوشاء → ابي الحسن الرضا ع
- Corrected isnad (Arabic): «وَ رُوِيَ عَنِ الْحَسَنِ بْنِ عَلِيٍّ الْوَشَّاءِ عَنْ أَبِي الْحَسَنِ الرِّضَا ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ زِيَارَةِ قَبْرِ أَبِي الْحَسَنِ مُوسَى بْنِ جَعْفَرٍ"
- Mursal opening: al-Ṣadūq → الحسن بن علي الوشاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 246 · `faqih-3175`
- **Location:** vol. 2, p. 582 · seq 3186 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى عَلِيُّ بْنُ مَهْزِيَارَ عَنْ أَبِي جَعْفَرٍ مُحَمَّدِ بْنِ عَلِيٍّ الثَّانِي ع قَالَ‌ قُلْتُ لَهُ جُعِلْتُ فِدَاكَ زِيَارَةُ الرِّضَا ع أَفْضَلُ أَمْ زِيَارَةُ أَبِي عَبْدِ اللَّهِ الْحُسَيْنِ ع قَالَ زِيَارَةُ أَبِي ع أَفْضَلُ وَ ذَلِكَ أَنَّ أَبَا عَبْدِ اللَّهِ ع يَزُورُهُ كُلُّ النَّاسِ وَ أَبِي ع لَا يَزُورُهُ إِلَّا الْخَوَاصُّ مِنَ الشِّيعَةِ[3].
- **Isnad as currently extracted:**
  > وَ رَوَى عَلِيُّ بْنُ مَهْزِيَارَ عَنْ أَبِي جَعْفَرٍ مُحَمَّدِ بْنِ عَلِيٍّ الثَّانِي ع قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن مهزیار | روی |  |
  | 1 | imam | ابی جعفر محمد بن علی الثانی ع | عن |  |

### Chain 246 · `faqih-3175` — CLARIFIED
- Transmitters (student → teacher): علي بن مهزيار → ابي جعفر محمد بن علي الثاني ع
- Corrected isnad (Arabic): «وَ رَوَى عَلِيُّ بْنُ مَهْزِيَارَ عَنْ أَبِي جَعْفَرٍ مُحَمَّدِ بْنِ عَلِيٍّ الثَّانِي ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ جُعِلْتُ فِدَاكَ زِيَارَةُ الرِّضَا ع أَفْضَلُ أَمْ"
- Mursal opening: al-Ṣadūq → علي بن مهزيار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 247 · `faqih-3187`
- **Location:** vol. 2, p. 585 · seq 3198 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > وَ رَوَى الْحَسَنُ بْنُ عَلِيِّ بْنِ فَضَّالٍ عَنْ أَبِي الْحَسَنِ الرِّضَا ع أَنَّهُ قَالَ‌ إِنَّ بِخُرَاسَانَ لَبُقْعَةً يَأْتِي عَلَيْهَا زَمَانٌ تَصِيرُ مُخْتَلَفَ الْمَلَائِكَةِ فَقَالَ فَلَا يَزَالُ فَوْجٌ يَنْزِلُ مِنَ السَّمَاءِ وَ فَوْجٌ يَصْعَدُ إِلَى أَنْ يُنْفَخَ فِي الصُّورِ فَقِيلَ لَهُ يَا ابْنَ رَسُولِ اللَّهِ وَ أَيَّةُ بُقْعَةٍ هَذِهِ قَالَ هِيَ بِأَرْضِ طُوسَ فَهِيَ وَ اللَّهِ رَوْضَةٌ مِنْ رِيَاضِ الْجَنَّةِ مَنْ زَارَنِي فِي تِلْكَ الْبُقْعَةِ كَانَ كَمَنْ زَارَ رَسُولَ اللَّهِ ص وَ كَتَبَ اللَّهُ تَبَارَكَ وَ تَعَالَى لَهُ ثَوَابَ أَلْفِ حَجَّةٍ مَبْرُورَةٍ وَ أَلْفِ عُمْرَةٍ مَقْبُولَةٍ وَ كُنْتُ أَنَا وَ آبَائِي شُفَعَاءَهُ يَوْمَ الْقِيَامَةِ.
- **Isnad as currently extracted:**
  > وَ رَوَى الْحَسَنُ بْنُ عَلِيِّ بْنِ فَضَّالٍ عَنْ أَبِي الْحَسَنِ الرِّضَا ع أَنَّهُ قَالَ‌ إِنَّ بِخُرَاسَانَ لَبُقْعَةً يَأْتِي عَلَيْهَا زَمَانٌ تَصِيرُ مُخْتَلَفَ الْمَلَائِكَةِ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن علی بن فضال | روی |  |
  | 1 | imam | ابی الحسن الرضا ع | عن |  |

### Chain 247 · `faqih-3187` — CLARIFIED
- Transmitters (student → teacher): الحسن بن علي بن فضال → ابي الحسن الرضا ع
- Corrected isnad (Arabic): «وَ رَوَى الْحَسَنُ بْنُ عَلِيِّ بْنِ فَضَّالٍ عَنْ أَبِي الْحَسَنِ الرِّضَا ع أَنَّهُ قَالَ‌»
- Isnad ends / matn begins at: "إِنَّ بِخُرَاسَانَ لَبُقْعَةً يَأْتِي عَلَيْهَا زَمَانٌ تَصِيرُ مُخْتَلَفَ الْمَلَائِكَةِ"
- Mursal opening: al-Ṣadūq → الحسن بن علي بن فضال; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 248 · `faqih-3189`
- **Location:** vol. 2, p. 586 · seq 3200 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى صَفْوَانُ بْنُ مِهْرَانَ الْجَمَّالُ عَنِ الصَّادِقِ جَعْفَرِ بْنِ مُحَمَّدٍ ع قَالَ‌ سَارَ وَ أَنَا مَعَهُ فِي الْقَادِسِيَّةِ حَتَّى أَشْرَفَ عَلَى النَّجَفِ فَقَالَ هُوَ الْجَبَلُ الَّذِي اعْتَصَمَ بِهِ ابْنُ جَدِّي نُوحٍ ع فَقَالَ‌ سَآوِي إِلى‌ جَبَلٍ يَعْصِمُنِي مِنَ الْماءِ فَأَوْحَى اللَّهُ عَزَّ وَ جَلَّ إِلَيْهِ يَا جَبَلُ أَ يَعْتَصِمُ بِكَ مِنِّي أَحَدٌ فَغَارَ فِي الْأَرْضِ وَ تَقَطَّعَ إِلَى الشَّامِ ثُمَّ قَالَ ع اعْدِلْ بِنَا قَالَ فَعَدَلْتُ بِهِ فَلَمْ يَزَلْ سَائِراً حَتَّى أَتَى الْغَرِيَّ فَوَقَفَ عَلَى الْقَبْرِ فَسَاقَ السَّلَامَ مِنْ آدَمَ عَلَى نَبِيٍّ نَبِيٍّ ع وَ أَنَا أَسُوقُ السَّلَامَ مَعَهُ حَتَّى وَصَلَ السَّلَامَ إِلَى النَّبِيِّ ص ثُمَّ خَرَّ عَلَى الْقَبْرِ فَسَلَّمَ عَلَيْهِ وَ عَلَا نَحِيبُهُ ثُمَّ قَامَ فَصَلَّى أَرْبَعَ رَكَعَاتٍ وَ فِي خَبَرٍ آخَرَ سِتَّ رَكَعَاتٍ وَ صَلَّيْتُ مَعَهُ وَ قُلْتُ لَهُ يَا ابْنَ رَسُولِ اللَّهِ مَا هَذَا الْقَبْرُ قَالَ هَذَا الْقَبْرُ قَبْرُ جَدِّي عَلِيِّ بْنِ أَبِي طَالِبٍ ع‌[1].
زِيَارَةُ قَبْرِ أَمِيرِ الْمُؤْمِنِينَ ص‌
- **Isnad as currently extracted:**
  > رَوَى صَفْوَانُ بْنُ مِهْرَانَ الْجَمَّالُ عَنِ الصَّادِقِ جَعْفَرِ بْنِ مُحَمَّدٍ ع قَالَ‌ سَارَ وَ أَنَا مَعَهُ فِي الْقَادِسِيَّةِ حَتَّى أَشْرَفَ عَلَى النَّجَفِ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان بن مهران الجمال | روی |  |
  | 1 | imam | الصادق جعفر بن محمد ع | عن |  |

### Chain 248 · `faqih-3189` — CLARIFIED
- Transmitters (student → teacher): صفوان بن مهران الجمال → الصادق جعفر بن محمد ع
- Corrected isnad (Arabic): «رَوَى صَفْوَانُ بْنُ مِهْرَانَ الْجَمَّالُ عَنِ الصَّادِقِ جَعْفَرِ بْنِ مُحَمَّدٍ ع قَالَ‌»
- Isnad ends / matn begins at: "سَارَ وَ أَنَا مَعَهُ فِي الْقَادِسِيَّةِ حَتَّى أَشْرَفَ عَلَى"
- Mursal opening: al-Ṣadūq → صفوان بن مهران الجمال; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 249 · `faqih-3211`
- **Location:** vol. 3, p. 3 · seq 3223 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى مُعَلَّى بْنُ خُنَيْسٍ عَنِ الصَّادِقِ ع قَالَ‌ قُلْتُ لَهُ قَوْلُ اللَّهِ عَزَّ وَ جَلَ‌ إِنَّ اللَّهَ يَأْمُرُكُمْ أَنْ تُؤَدُّوا الْأَماناتِ إِلى‌ أَهْلِها وَ إِذا حَكَمْتُمْ بَيْنَ النَّاسِ أَنْ تَحْكُمُوا بِالْعَدْلِ‌ قَالَ عَلَى الْإِمَامِ‌[2] أَنْ يَدْفَعَ مَا عِنْدَهُ إِلَى الْإِمَامِ الَّذِي بَعْدَهُ وَ أُمِرَتِ الْأَئِمَّةُ أَنْ يَحْكُمُوا بِالْعَدْلِ وَ أُمِرَ النَّاسُ أَنْ يَتَّبِعُوهُمْ.
- **Isnad as currently extracted:**
  > رَوَى مُعَلَّى بْنُ خُنَيْسٍ عَنِ الصَّادِقِ ع قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معلی بن خنیس | روی |  |
  | 1 | imam | الصادق ع | عن |  |

### Chain 249 · `faqih-3211` — CLARIFIED
- Transmitters (student → teacher): معلي بن خنيس → الصادق ع
- Corrected isnad (Arabic): «رَوَى مُعَلَّى بْنُ خُنَيْسٍ عَنِ الصَّادِقِ ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ قَوْلُ اللَّهِ عَزَّ وَ جَلَ‌ إِنَّ اللَّهَ"
- Mursal opening: al-Ṣadūq → معلي بن خنيس; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 250 · `faqih-3214`
- **Location:** vol. 3, p. 4 · seq 3226 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى حَرِيزٌ عَنْ أَبِي بَصِيرٍ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌ أَيُّمَا رَجُلٍ كَانَ بَيْنَهُ وَ بَيْنَ أَخٍ لَهُ- مُمَارَاةٌ فِي حَقٍّ فَدَعَاهُ إِلَى رَجُلٍ مِنْ إِخْوَانِكُمْ لِيَحْكُمَ بَيْنَهُ وَ بَيْنَهُ فَأَبَى إِلَّا أَنْ يُرَافِعَهُ إِلَى هَؤُلَاءِ كَانَ بِمَنْزِلَةِ الَّذِينَ قَالَ اللَّهُ عَزَّ وَ جَلَّ- أَ لَمْ تَرَ إِلَى الَّذِينَ يَزْعُمُونَ أَنَّهُمْ آمَنُوا بِما أُنْزِلَ إِلَيْكَ وَ ما أُنْزِلَ مِنْ قَبْلِكَ‌ يُرِيدُونَ أَنْ يَتَحاكَمُوا إِلَى الطَّاغُوتِ‌ وَ قَدْ أُمِرُوا أَنْ يَكْفُرُوا بِهِ‌ الْآيَةَ[3].
- **Isnad as currently extracted:**
  > رَوَى حَرِيزٌ عَنْ أَبِي بَصِيرٍ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌ أَيُّمَا رَجُلٍ كَانَ بَيْنَهُ وَ بَيْنَ أَخٍ لَهُ- مُمَارَاةٌ فِي حَقٍّ فَدَعَاهُ إِلَى رَجُلٍ مِنْ إِخْوَانِكُمْ لِيَحْكُمَ بَيْنَهُ وَ بَيْنَهُ فَأَبَى إِلَّا أَنْ يُرَافِعَهُ إِلَى هَؤُلَاءِ كَانَ بِمَنْزِلَةِ الَّذِينَ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حریز | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |
  | 2 | imam | ابی عبد الله ع | عن |  |

### Chain 250 · `faqih-3214` — CLARIFIED
- Transmitters (student → teacher): حريز → ابي بصير → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى حَرِيزٌ عَنْ أَبِي بَصِيرٍ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌»
- Isnad ends / matn begins at: "أَيُّمَا رَجُلٍ كَانَ بَيْنَهُ وَ بَيْنَ أَخٍ لَهُ- مُمَارَاةٌ"
- Mursal opening: al-Ṣadūq → حريز; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 251 · `faqih-3226`
- **Location:** vol. 3, p. 8 · seq 3238 · chain 1
- **Flags:** `mursal_opening`, `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > رُوِيَ عَنْ دَاوُدَ بْنِ الْحُصَيْنِ‌[1] عَنْ أَبِي عَبْدِ اللَّهِ ع‌ فِي رَجُلَيْنِ اتَّفَقَا عَلَى عَدْلَيْنِ جَعَلَاهُمَا بَيْنَهُمَا فِي حُكْمٍ وَقَعَ بَيْنَهُمَا فِيهِ خِلَافٌ فَرَضِيَا بِالْعَدْلَيْنِ فَاخْتَلَفَ الْعَدْلَانِ بَيْنَهُمَا عَلَى قَوْلِ أَيِّهِمَا يَمْضِي الْحُكْمُ‌[2] قَالَ يُنْظَرُ إِلَى أَفْقَهِهِمَا وَ أَعْلَمِهِمَا بِأَحَادِيثِنَا وَ أَوْرَعِهِمَا فَيَنْفُذُ حُكْمُهُ وَ لَا يُلْتَفَتُ إِلَى الْآخَرِ[3].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ دَاوُدَ بْنِ الْحُصَيْنِ‌[1] عَنْ أَبِي عَبْدِ اللَّهِ ع‌ فِي رَجُلَيْنِ اتَّفَقَا عَلَى عَدْلَيْنِ جَعَلَاهُمَا بَيْنَهُمَا فِي حُكْمٍ وَقَعَ بَيْنَهُمَا فِيهِ خِلَافٌ فَرَضِيَا بِالْعَدْلَيْنِ فَاخْتَلَفَ الْعَدْلَانِ بَيْنَهُمَا عَلَى قَوْلِ أَيِّهِمَا يَمْضِي الْحُكْمُ‌[2] قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن داود بن الحصین | روی |  |
  | 1 | named_narrator | ابی عبد الله ع فی رجلین اتفقا علی عدلین جعلاهما بینهما فی حکم وقع بینهما فیه خلاف فرضیا بالعدلین فاختلف العدلان بینهما علی قول ایهما یمضی الحکم | عن |  |

### Chain 251 · `faqih-3226` — CLARIFIED
- Transmitters (student → teacher): داود بن الحصين → أبو عبد الله ع
- Corrected isnad (Arabic): «رُوِيَ عَنْ دَاوُدَ بْنِ الْحُصَيْنِ‌[1] عَنْ أَبِي عَبْدِ اللَّهِ ع‌»
- Isnad ends / matn begins at: "فِي رَجُلَيْنِ اتَّفَقَا عَلَى عَدْلَيْنِ جَعَلَاهُمَا بَيْنَهُمَا فِي حُكْمٍ"
- Mursal opening: al-Ṣadūq → داود بن الحصين; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name.

---

### Chain 252 · `faqih-3238`
- **Location:** vol. 3, p. 16 · seq 3250 · chain 1
- **Flags:** `matn_spill`
- **Full report (Arabic):**
  > فِي رِوَايَةِ يُونُسَ بْنِ عَبْدِ الرَّحْمَنِ عَنْ بَعْضِ رِجَالِهِ‌[3] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنِ الْبَيِّنَةِ إِذَا أُقِيمَتْ عَلَى الْحَقِّ أَ يَحِلُّ لِلْقَاضِي أَنْ يَقْضِيَ بِقَوْلِ الْبَيِّنَةِ فَقَالَ خَمْسَةُ أَشْيَاءَ يَجِبُ عَلَى النَّاسِ الْأَخْذُ فِيهَا بِظَاهِرِ الْحُكْمِ الْوِلَايَاتُ وَ الْمَنَاكِحُ‌
وَ الذَّبَائِحُ وَ الشَّهَادَاتُ وَ الْأَنْسَابُ فَإِذَا كَانَ ظَاهِرُ الرَّجُلِ ظَاهِراً مَأْمُوناً- جَازَتْ شَهَادَتُهُ وَ لَا يُسْأَلُ عَنْ بَاطِنِهِ‌[1].
- **Isnad as currently extracted:**
  > فِي رِوَايَةِ يُونُسَ بْنِ عَبْدِ الرَّحْمَنِ عَنْ بَعْضِ رِجَالِهِ‌[3] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنِ الْبَيِّنَةِ إِذَا أُقِيمَتْ عَلَى الْحَقِّ أَ يَحِلُّ لِلْقَاضِي أَنْ يَقْضِيَ بِقَوْلِ الْبَيِّنَةِ فَقَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | فی روایة یونس بن عبد الرحمن |  |  |
  | 1 | unknown_person | بعض رجاله | عن |  |
  | 2 | imam | ابی عبد الله ع | عن |  |

### Chain 252 · `faqih-3238` — CLARIFIED
- Transmitters (student → teacher): يونس بن عبد الرحمن → بعض رجاله → ابي عبد الله ع
- Corrected isnad (Arabic): «فِي رِوَايَةِ يُونُسَ بْنِ عَبْدِ الرَّحْمَنِ عَنْ بَعْضِ رِجَالِهِ‌[3] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْبَيِّنَةِ إِذَا أُقِيمَتْ عَلَى الْحَقِّ أَ يَحِلُّ"
- Mursal opening: al-Ṣadūq → يونس بن عبد الرحمن; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 253 · `faqih-3240`
- **Location:** vol. 3, p. 17 · seq 3252 · chain 1
- **Flags:** `matn_spill`, `no_imam_terminal`
- **Full report (Arabic):**
  > فِي رِوَايَةِ عَمْرِو بْنِ شِمْرٍ عَنْ جَعْفَرِ بْنِ غَالِبٍ الْأَسَدِيِّ رَفَعَ الْحَدِيثَ قَالَ‌ بَيْنَمَا رَجُلَانِ جَالِسَانِ فِي زَمَنِ عُمَرَ بْنِ الْخَطَّابِ إِذْ مَرَّ بِهِمَا رَجُلٌ مُقَيَّدٌ فَقَالَ أَحَدُ الرَّجُلَيْنِ إِنْ لَمْ يَكُنْ فِي قَيْدِهِ كَذَا وَ كَذَا فَامْرَأَتُهُ طَالِقٌ ثَلَاثاً فَقَالَ الْآخَرُ إِنْ كَانَ فِيهِ كَمَا قُلْتَ فَامْرَأَتُهُ طَالِقٌ ثَلَاثاً فَذَهَبَا إِلَى مَوْلَى الْعَبْدِ وَ هُوَ الْمُقَيِّدُ فَقَالا لَهُ إِنَّا حَلَفْنَا عَلَى كَذَا وَ كَذَا فَحُلَّ قَيْدَ غُلَامِكَ حَتَّى نَزِنَهُ فَقَالَ مَوْلَى الْعَبْدِ امْرَأَتُهُ طَالِقٌ إِنْ حَلَلْتُ قَيْدَ غُلَامِي فَارْتَفَعُوا إِلَى عُمَرَ فَقَصُّوا عَلَيْهِ الْقِصَّةَ فَقَالَ عُمَرُ مَوْلَاهُ أَحَقُّ بِهِ اذْهَبُوا بِهِ إِلَى عَلِيِّ بْنِ أَبِي طَالِبٍ لَعَلَّهُ يَكُونُ عِنْدَهُ فِي هَذَا شَيْ‌ءٌ فَأَتَوْا عَلِيّاً ع فَقَصُّوا عَلَيْهِ الْقِصَّةَ فَقَالَ مَا أَهْوَنَ هَذَا فَدَعَا بِجَفْنَةٍ[2] وَ أَمَرَ بِقَيْدِهِ فَشُدَّ فِيهِ خَيْطٌ وَ أَدْخَلَ رِجْلَيْهِ وَ الْقَيْدَ فِي الْجَفْنَةِ ثُمَّ صَبَّ عَلَيْهِ الْمَاءَ حَتَّى امْتَلَأَتْ ثُمَّ قَالَ ع ارْفَعُوا الْقَيْدَ فَرَفَعُوا الْقَيْدَ حَتَّى أُخْرِجَ مِنَ الْمَاءِ فَلَمَّا أُخْرِجَ نَقَصَ الْمَاءُ ثُمَ‌
دَعَا بِزُبَرِ الْحَدِيدِ فَأَرْسَلَهُ فِي الْمَاءِ حَتَّى تَرَاجَعَ الْمَاءُ إِلَى مَوْضِعِهِ وَ الْقَيْدُ فِي الْمَاءِ ثُمَّ قَالَ زِنُوا هَذَا الزُّبَرَ فَهُوَ وَزْنُهُ.
- **Isnad as currently extracted:**
  > فِي رِوَايَةِ عَمْرِو بْنِ شِمْرٍ عَنْ جَعْفَرِ بْنِ غَالِبٍ الْأَسَدِيِّ رَفَعَ الْحَدِيثَ قَالَ‌ بَيْنَمَا رَجُلَانِ جَالِسَانِ فِي زَمَنِ عُمَرَ بْنِ الْخَطَّابِ إِذْ مَرَّ بِهِمَا رَجُلٌ مُقَيَّدٌ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | فی روایة عمرو بن شمر |  |  |
  | 1 | named_narrator | جعفر بن غالب الاسدی رفع الحدیث | عن |  |

### Chain 253 · `faqih-3240` — CLARIFIED
- Transmitters (student → teacher): عمرو بن شمر → جعفر بن غالب الاسدي رفع الحديث
- Corrected isnad (Arabic): «فِي رِوَايَةِ عَمْرِو بْنِ شِمْرٍ عَنْ جَعْفَرِ بْنِ غَالِبٍ الْأَسَدِيِّ رَفَعَ الْحَدِيثَ قَالَ‌»
- Isnad ends / matn begins at: "بَيْنَمَا رَجُلَانِ جَالِسَانِ فِي زَمَنِ عُمَرَ بْنِ الْخَطَّابِ إِذْ"
- Mursal opening: al-Ṣadūq → عمرو بن شمر; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 254 · `faqih-3241`
- **Location:** vol. 3, p. 18 · seq 3253 · chain 1
- **Flags:** `mursal_opening`, `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > رَوَى أَحْمَدُ بْنُ عَائِذٍ عَنْ أَبِي سَلَمَةَ[2] عَنْ أَبِي عَبْدِ اللَّهِ ع‌ فِي رَجُلَيْنِ مَمْلُوكَيْنِ مُفَوَّضٍ إِلَيْهِمَا يَشْتَرِيَانِ وَ يَبِيعَانِ بِأَمْوَالِ مَوَالِيهِمَا فَكَانَ بَيْنَهُمَا كَلَامٌ فَاقْتَتَلَا فَخَرَجَ هَذَا يَعْدُو إِلَى مَوْلَى هَذَا وَ هَذَا إِلَى مَوْلَى هَذَا وَ هُمَا فِي الْقُوَّةِ سَوَاءٌ فَاشْتَرَى هَذَا مِنْ مَوْلَى هَذَا الْعَبْدِ وَ ذَهَبَ هَذَا فَاشْتَرَى هَذَا مِنْ مَوْلَاهُ وَ جَاءَ هَذَا وَ أَخَذَ بِتَلْبِيبِ هَذَا وَ أَخَذَ هَذَا بِتَلْبِيبِ هَذَا[3] وَ قَالَ كُلُّ وَاحِدٍ مِنْهُمَا لِصَاحِبِهِ أَنْتَ عَبْدِي قَدِ اشْتَرَيْتُكَ قَالَ يُحْكَمُ بَيْنَهُمَا مِنْ حَيْثُ افْتَرَقَا فَيُذْرَعُ الطَّرِيقُ فَأَيُّهُمَا كَانَ أَقْرَبَ فَالَّذِي أَخَذَ فِيهِ هُوَ الَّذِي سَبَقَ الَّذِي هُوَ أَبْعَدُ[4] وَ إِنْ كَانَا سَوَاءً فَهُمَا رَدٌّ عَلَى مَوَالِيهِمَا[5].
- **Isnad as currently extracted:**
  > رَوَى أَحْمَدُ بْنُ عَائِذٍ عَنْ أَبِي سَلَمَةَ[2] عَنْ أَبِي عَبْدِ اللَّهِ ع‌ فِي رَجُلَيْنِ مَمْلُوكَيْنِ مُفَوَّضٍ إِلَيْهِمَا يَشْتَرِيَانِ وَ يَبِيعَانِ بِأَمْوَالِ مَوَالِيهِمَا فَكَانَ بَيْنَهُمَا كَلَامٌ فَاقْتَتَلَا فَخَرَجَ هَذَا يَعْدُو إِلَى مَوْلَى هَذَا وَ هَذَا إِلَى مَوْلَى هَذَا وَ هُمَا فِي الْقُوَّةِ سَوَاءٌ فَاشْتَرَى هَذَا مِنْ مَوْلَى هَذَا الْعَبْدِ وَ ذَهَبَ هَذَا فَاشْتَرَى هَذَا مِنْ مَوْلَاهُ وَ جَاءَ هَذَا وَ أَخَذَ بِتَلْبِيبِ هَذَا وَ أَخَذَ هَذَا بِتَلْبِيبِ هَذَا[3] وَ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | احمد بن عائذ | روی |  |
  | 1 | named_narrator | ابی سلمة | عن |  |
  | 2 | named_narrator | ابی عبد الله ع فی رجلین مملوکین مفوض الیهما یشتریان و یبیعان باموال موالیهما فکان بینهما کلام فاقتتلا فخرج هذا یعدو الی مولی هذا و هذا الی مولی هذا و هما فی القوة سواء فاشتری هذا من مولی هذا العبد و ذهب هذا فاشتری هذا من مولاه و جاء هذا و اخذ بتلبیب هذا و اخذ هذا بتلبیب هذا | عن |  |

### Chain 254 · `faqih-3241` — CLARIFIED
- Transmitters (student → teacher): أحمد بن عائذ → أبو سلمة → أبو عبد الله ع
- Corrected isnad (Arabic): «رَوَى أَحْمَدُ بْنُ عَائِذٍ عَنْ أَبِي سَلَمَةَ[2] عَنْ أَبِي عَبْدِ اللَّهِ ع‌»
- Isnad ends / matn begins at: "فِي رَجُلَيْنِ مَمْلُوكَيْنِ مُفَوَّضٍ إِلَيْهِمَا يَشْتَرِيَانِ وَ يَبِيعَانِ بِأَمْوَالِ"
- Mursal opening: al-Ṣadūq → أحمد بن عائذ; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name.

---

### Chain 255 · `faqih-3242`
- **Location:** vol. 3, p. 19 · seq 3254 · chain 1
- **Flags:** `matn_spill`, `no_imam_terminal`
- **Full report (Arabic):**
  > فِي رِوَايَةِ إِبْرَاهِيمَ بْنِ مُحَمَّدٍ الثَّقَفِيِّ قَالَ‌ اسْتَوْدَعَ رَجُلَانِ امْرَأَةً وَدِيعَةً وَ قَالا لَهَا لَا تَدْفَعِي إِلَى وَاحِدٍ مِنَّا حَتَّى نَجْتَمِعَ عِنْدَكِ ثُمَّ انْطَلَقَا فَغَابَا فَجَاءَ أَحَدُهُمَا إِلَيْهَا وَ قَالَ أَعْطِينِي وَدِيعَتِي فَإِنَّ صَاحِبِي قَدْ مَاتَ فَأَبَتْ حَتَّى كَثُرَ اخْتِلَافُهُ إِلَيْهَا ثُمَّ أَعْطَتْهُ ثُمَّ جَاءَ الْآخَرُ فَقَالَ هَاتِي وَدِيعَتِي قَالَتْ أَخَذَهَا صَاحِبُكَ وَ ذَكَرَ أَنَّكَ قَدْ مِتَّ فَارْتَفَعَا إِلَى عُمَرَ فَقَالَ لَهَا عُمَرُ مَا أَرَاكِ إِلَّا وَ قَدْ ضَمِنْتِ فَقَالَتِ الْمَرْأَةُ اجْعَلْ عَلِيّاً ع بَيْنِي وَ بَيْنَهُ فَقَالَ لَهُ اقْضِ بَيْنَهُمَا فَقَالَ عَلِيٌّ ع هَذِهِ الْوَدِيعَةُ عِنْدَهَا[1] وَ قَدْ أَمَرْتُمَاهَا أَلَّا تَدْفَعَهَا إِلَى وَاحِدٍ مِنْكُمَا حَتَّى تَجْتَمِعَا عِنْدَهَا فَائْتِنِي بِصَاحِبِكَ وَ لَمْ يُضَمِّنْهَا وَ قَالَ عَلِيٌّ ع إِنَّمَا أَرَادَا أَنْ يَذْهَبَا بِمَالِ الْمَرْأَةِ.
- **Isnad as currently extracted:**
  > فِي رِوَايَةِ إِبْرَاهِيمَ بْنِ مُحَمَّدٍ الثَّقَفِيِّ قَالَ‌ اسْتَوْدَعَ رَجُلَانِ امْرَأَةً وَدِيعَةً وَ قَالا لَهَا لَا تَدْفَعِي إِلَى وَاحِدٍ مِنَّا حَتَّى نَجْتَمِعَ عِنْدَكِ ثُمَّ انْطَلَقَا فَغَابَا فَجَاءَ أَحَدُهُمَا إِلَيْهَا وَ قَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | فی روایة ابراهیم بن محمد الثقفی |  |  |

### Chain 255 · `faqih-3242` — CLARIFIED
- Transmitters (student → teacher): ابراهيم بن محمد الثقفي
- Corrected isnad (Arabic): «فِي رِوَايَةِ إِبْرَاهِيمَ بْنِ مُحَمَّدٍ الثَّقَفِيِّ قَالَ‌»
- Isnad ends / matn begins at: "اسْتَوْدَعَ رَجُلَانِ امْرَأَةً وَدِيعَةً وَ قَالا لَهَا لَا تَدْفَعِي"
- Mursal opening: al-Ṣadūq → ابراهيم بن محمد الثقفي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 256 · `faqih-3243`
- **Location:** vol. 3, p. 19 · seq 3255 · chain 1
- **Flags:** `multi_route`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى عَاصِمُ بْنُ حُمَيْدٍ عَنْ مُحَمَّدِ بْنِ قَيْسٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ كَانَ لِرَجُلٍ عَلَى عَهْدِ عَلِيٍّ ع جَارِيَتَانِ فَوَلَدَتَا جَمِيعاً فِي لَيْلَةٍ وَاحِدَةٍ إِحْدَاهُمَا ابْناً وَ الْأُخْرَى بِنْتاً فَعَمَدَتْ‌[2] صَاحِبَةُ الِابْنَةِ فَوَضَعَتِ ابْنَتَهَا فِي الْمَهْدِ الَّذِي كَانَ فِيهِ الِابْنُ وَ أَخَذَتِ ابْنَهَا فَقَالَتْ صَاحِبَةُ الِابْنَةِ الِابْنُ ابْنِي وَ قَالَتْ صَاحِبَةُ الِابْنِ الِابْنُ ابْنِي فَتَحَاكَمَا[3] إِلَى أَمِيرِ الْمُؤْمِنِينَ ع فَأَمَرَ أَنْ يُوزَنَ لَبَنُهُمَا وَ قَالَ أَيَّتُهُمَا كَانَتْ أَثْقَلَ لَبَناً فَالابْنُ لَهَا.
- **Isnad as currently extracted:**
  > رَوَى عَاصِمُ بْنُ حُمَيْدٍ عَنْ مُحَمَّدِ بْنِ قَيْسٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ كَانَ لِرَجُلٍ عَلَى عَهْدِ عَلِيٍّ ع جَارِيَتَانِ فَوَلَدَتَا جَمِيعاً فِي لَيْلَةٍ وَاحِدَةٍ إِحْدَاهُمَا ابْناً وَ الْأُخْرَى بِنْتاً فَعَمَدَتْ‌[2] صَاحِبَةُ الِابْنَةِ فَوَضَعَتِ ابْنَتَهَا فِي الْمَهْدِ الَّذِي كَانَ فِيهِ الِابْنُ وَ أَخَذَتِ ابْنَهَا فَقَالَتْ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عاصم بن حمید | روی |  |
  | 1 | named_narrator | محمد بن قیس | عن |  |
  | 2 | imam | ابی جعفر ع | عن |  |
  | 3 | imam | کان لرجل علی عهد علی ع |  |  |

### Chain 256 · `faqih-3243` — CLARIFIED
- Transmitters (student → teacher): عاصم بن حميد → محمد بن قيس → أبو جعفر ع
- Corrected isnad (Arabic): «رَوَى عَاصِمُ بْنُ حُمَيْدٍ عَنْ مُحَمَّدِ بْنِ قَيْسٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "كَانَ لِرَجُلٍ عَلَى عَهْدِ عَلِيٍّ ع جَارِيَتَانِ فَوَلَدَتَا جَمِيعاً"
- Mursal opening: al-Ṣadūq → عاصم بن حميد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: This is a single linear chain. The multiple persons in the judicial narrative belong to the matn and do not create multiple isnād routes.
---

### Chain 257 · `faqih-3245`
- **Location:** vol. 3, p. 20 · seq 3257 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى سَعْدُ بْنُ طَرِيفٍ عَنِ الْأَصْبَغِ بْنِ نُبَاتَةَ قَالَ‌ أُتِيَ عُمَرُ بْنُ الْخَطَّابِ بِجَارِيَةٍ فَشَهِدَ عَلَيْهَا شُهُودٌ أَنَّهَا بَغَتْ وَ كَانَ مِنْ قِصَّتِهَا أَنَّهَا كَانَتْ يَتِيمَةً عِنْدَ رَجُلٍ وَ كَانَ لِلرَّجُلِ امْرَأَةٌ وَ كَانَ الرَّجُلُ كَثِيراً مَا يَغِيبُ عَنْ أَهْلِهِ فَشَبَّتِ الْيَتِيمَةُ وَ كَانَتْ جَمِيلَةً فَتَخَوَّفَتِ‌
الْمَرْأَةُ أَنْ يَتَزَوَّجَهَا زَوْجُهَا إِذَا رَجَعَ إِلَى مَنْزِلِهِ فَدَعَتْ بِنِسْوَةٍ مِنْ جِيرَانِهَا فَأَمْسَكْنَهَا ثُمَّ اقْتَضَّتْهَا بِإِصْبَعِهَا[1] فَلَمَّا قَدِمَ زَوْجُهَا سَأَلَ امْرَأَتَهُ عَنِ الْيَتِيمَةِ فَرَمَتْهَا بِالْفَاحِشَةِ وَ أَقَامَتِ الْبَيِّنَةَ مِنْ جِيرَانِهَا عَلَى ذَلِكَ قَالَ فَرُفِعَ ذَلِكَ إِلَى عُمَرَ بْنِ الْخَطَّابِ فَلَمْ يَدْرِ كَيْفَ يَقْضِي فِي ذَلِكَ فَقَالَ لِلرَّجُلِ اذْهَبْ بِهَا إِلَى عَلِيِّ بْنِ أَبِي طَالِبٍ فَأَتَوْا عَلِيّاً وَ قَصُّوا عَلَيْهِ الْقِصَّةَ فَقَالَ لِامْرَأَةِ الرَّجُلِ أَ لَكِ بَيِّنَةٌ قَالَتْ نَعَمْ هَؤُلَاءِ جِيرَانِي‌[2] يَشْهَدْنَ عَلَيْهَا بِمَا أَقُولُ فَأَخْرَجَ عَلِيٌّ ع السَّيْفَ مِنْ غِمْدِهِ وَ طَرَحَهُ بَيْنَ يَدَيْهِ ثُمَّ أَمَرَ بِكُلِّ وَاحِدَةٍ مِنَ الشُّهُودِ فَأُدْخِلَتْ بَيْتاً ثُمَّ دَعَا بِامْرَأَةِ الرَّجُلِ فَأَدَارَهَا بِكُلِّ وَجْهٍ فَأَبَتْ أَنْ تَزُولَ عَنْ قَوْلِهَا فَرَدَّهَا إِلَى الْبَيْتِ الَّذِي كَانَتْ فِيهِ ثُمَّ دَعَا بِإِحْدَى الشُّهُودِ وَ جَثَا عَلَى رُكْبَتَيْهِ وَ قَالَ لَهَا أَ تَعْرِفِينِي أَنَا عَلِيُّ بْنُ أَبِي طَالِبٍ وَ هَذَا سَيْفِي وَ قَدْ قَالَتِ امْرَأَةُ الرَّجُلِ مَا قَالَتْ وَ رَجَعَتْ إِلَى الْحَقِّ وَ أَعْطَيْتُهَا الْأَمَانَ فَاصْدُقِينِي وَ إِلَّا مَلَأْتُ سَيْفِي مِنْكِ فَالْتَفَتَتِ الْمَرْأَةُ إِلَى عَلِيٍ‌[3] فَقَالَتْ يَا أَمِيرَ الْمُؤْمِنِينَ الْأَمَانَ عَلَى الصِّدْقِ فَقَالَ لَهَا عَلِيٌّ ع فَاصْدُقِي فَقَالَتْ لَا وَ اللَّهِ مَا زَنَتِ الْيَتِيمَةُ وَ لَكِنِ امْرَأَةُ الرَّجُلِ لَمَّا رَأَتْ حُسْنَهَا وَ جَمَالَهَا وَ هَيْئَتَهَا خَافَتْ فَسَادَ زَوْجِهَا فَسَقَتْهَا الْمُسْكِرَ وَ دَعَتْنَا فَأَمْسَكْنَاهَا فَاقْتَضَّتْهَا بِإِصْبَعِهَا فَقَالَ عَلِيٌّ ع اللَّهُ أَكْبَرُ ا …[truncated]
- **Isnad as currently extracted:**
  > رَوَى سَعْدُ بْنُ طَرِيفٍ عَنِ الْأَصْبَغِ بْنِ نُبَاتَةَ قَالَ‌ أُتِيَ عُمَرُ بْنُ الْخَطَّابِ بِجَارِيَةٍ فَشَهِدَ عَلَيْهَا شُهُودٌ أَنَّهَا بَغَتْ وَ كَانَ مِنْ قِصَّتِهَا أَنَّهَا كَانَتْ يَتِيمَةً عِنْدَ رَجُلٍ وَ كَانَ لِلرَّجُلِ امْرَأَةٌ وَ كَانَ الرَّجُلُ كَثِيراً مَا يَغِيبُ عَنْ أَهْلِهِ فَشَبَّتِ الْيَتِيمَةُ وَ كَانَتْ جَمِيلَةً فَتَخَوَّفَتِ‌ الْمَرْأَةُ أَنْ يَتَزَوَّجَهَا زَوْجُهَا إِذَا رَجَعَ إِلَى مَنْزِلِهِ فَدَعَتْ بِنِسْوَةٍ مِنْ جِيرَانِهَا فَأَمْسَكْنَهَا ثُمَّ اقْتَضَّتْهَا بِإِصْبَعِهَا[1] فَلَمَّا قَدِمَ زَوْجُهَا سَأَلَ امْرَأَتَهُ عَنِ الْيَتِيمَةِ فَرَمَتْهَا بِالْفَاحِشَةِ وَ أَقَامَتِ الْبَيِّنَةَ مِنْ جِيرَانِهَا عَلَى ذَلِكَ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | سعد بن طریف | روی |  |
  | 1 | named_narrator | الاصبغ بن نباتة | عن |  |

### Chain 257 · `faqih-3245` — CLARIFIED
- Transmitters (student → teacher): سعد بن طريف → الاصبغ بن نباتة
- Corrected isnad (Arabic): «رَوَى سَعْدُ بْنُ طَرِيفٍ عَنِ الْأَصْبَغِ بْنِ نُبَاتَةَ قَالَ‌»
- Isnad ends / matn begins at: "أُتِيَ عُمَرُ بْنُ الْخَطَّابِ بِجَارِيَةٍ فَشَهِدَ عَلَيْهَا شُهُودٌ أَنَّهَا"
- Mursal opening: al-Ṣadūq → سعد بن طريف; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 258 · `faqih-3245`
- **Location:** vol. 3, p. 20 · seq 3257 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى سَعْدُ بْنُ طَرِيفٍ عَنِ الْأَصْبَغِ بْنِ نُبَاتَةَ قَالَ‌ أُتِيَ عُمَرُ بْنُ الْخَطَّابِ بِجَارِيَةٍ فَشَهِدَ عَلَيْهَا شُهُودٌ أَنَّهَا بَغَتْ وَ كَانَ مِنْ قِصَّتِهَا أَنَّهَا كَانَتْ يَتِيمَةً عِنْدَ رَجُلٍ وَ كَانَ لِلرَّجُلِ امْرَأَةٌ وَ كَانَ الرَّجُلُ كَثِيراً مَا يَغِيبُ عَنْ أَهْلِهِ فَشَبَّتِ الْيَتِيمَةُ وَ كَانَتْ جَمِيلَةً فَتَخَوَّفَتِ‌
الْمَرْأَةُ أَنْ يَتَزَوَّجَهَا زَوْجُهَا إِذَا رَجَعَ إِلَى مَنْزِلِهِ فَدَعَتْ بِنِسْوَةٍ مِنْ جِيرَانِهَا فَأَمْسَكْنَهَا ثُمَّ اقْتَضَّتْهَا بِإِصْبَعِهَا[1] فَلَمَّا قَدِمَ زَوْجُهَا سَأَلَ امْرَأَتَهُ عَنِ الْيَتِيمَةِ فَرَمَتْهَا بِالْفَاحِشَةِ وَ أَقَامَتِ الْبَيِّنَةَ مِنْ جِيرَانِهَا عَلَى ذَلِكَ قَالَ فَرُفِعَ ذَلِكَ إِلَى عُمَرَ بْنِ الْخَطَّابِ فَلَمْ يَدْرِ كَيْفَ يَقْضِي فِي ذَلِكَ فَقَالَ لِلرَّجُلِ اذْهَبْ بِهَا إِلَى عَلِيِّ بْنِ أَبِي طَالِبٍ فَأَتَوْا عَلِيّاً وَ قَصُّوا عَلَيْهِ الْقِصَّةَ فَقَالَ لِامْرَأَةِ الرَّجُلِ أَ لَكِ بَيِّنَةٌ قَالَتْ نَعَمْ هَؤُلَاءِ جِيرَانِي‌[2] يَشْهَدْنَ عَلَيْهَا بِمَا أَقُولُ فَأَخْرَجَ عَلِيٌّ ع السَّيْفَ مِنْ غِمْدِهِ وَ طَرَحَهُ بَيْنَ يَدَيْهِ ثُمَّ أَمَرَ بِكُلِّ وَاحِدَةٍ مِنَ الشُّهُودِ فَأُدْخِلَتْ بَيْتاً ثُمَّ دَعَا بِامْرَأَةِ الرَّجُلِ فَأَدَارَهَا بِكُلِّ وَجْهٍ فَأَبَتْ أَنْ تَزُولَ عَنْ قَوْلِهَا فَرَدَّهَا إِلَى الْبَيْتِ الَّذِي كَانَتْ فِيهِ ثُمَّ دَعَا بِإِحْدَى الشُّهُودِ وَ جَثَا عَلَى رُكْبَتَيْهِ وَ قَالَ لَهَا أَ تَعْرِفِينِي أَنَا عَلِيُّ بْنُ أَبِي طَالِبٍ وَ هَذَا سَيْفِي وَ قَدْ قَالَتِ امْرَأَةُ الرَّجُلِ مَا قَالَتْ وَ رَجَعَتْ إِلَى الْحَقِّ وَ أَعْطَيْتُهَا الْأَمَانَ فَاصْدُقِينِي وَ إِلَّا مَلَأْتُ سَيْفِي مِنْكِ فَالْتَفَتَتِ الْمَرْأَةُ إِلَى عَلِيٍ‌[3] فَقَالَتْ يَا أَمِيرَ الْمُؤْمِنِينَ الْأَمَانَ عَلَى الصِّدْقِ فَقَالَ لَهَا عَلِيٌّ ع فَاصْدُقِي فَقَالَتْ لَا وَ اللَّهِ مَا زَنَتِ الْيَتِيمَةُ وَ لَكِنِ امْرَأَةُ الرَّجُلِ لَمَّا رَأَتْ حُسْنَهَا وَ جَمَالَهَا وَ هَيْئَتَهَا خَافَتْ فَسَادَ زَوْجِهَا فَسَقَتْهَا الْمُسْكِرَ وَ دَعَتْنَا فَأَمْسَكْنَاهَا فَاقْتَضَّتْهَا بِإِصْبَعِهَا فَقَالَ عَلِيٌّ ع اللَّهُ أَكْبَرُ ا …[truncated]
- **Isnad as currently extracted:**
  > رَوَى سَعْدُ بْنُ طَرِيفٍ عَنِ الْأَصْبَغِ بْنِ نُبَاتَةَ قَالَ‌ أُتِيَ عُمَرُ بْنُ الْخَطَّابِ بِجَارِيَةٍ فَشَهِدَ عَلَيْهَا شُهُودٌ أَنَّهَا بَغَتْ وَ كَانَ مِنْ قِصَّتِهَا أَنَّهَا كَانَتْ يَتِيمَةً عِنْدَ رَجُلٍ وَ كَانَ لِلرَّجُلِ امْرَأَةٌ وَ كَانَ الرَّجُلُ كَثِيراً مَا يَغِيبُ عَنْ أَهْلِهِ فَشَبَّتِ الْيَتِيمَةُ وَ كَانَتْ جَمِيلَةً فَتَخَوَّفَتِ‌ الْمَرْأَةُ أَنْ يَتَزَوَّجَهَا زَوْجُهَا إِذَا رَجَعَ إِلَى مَنْزِلِهِ فَدَعَتْ بِنِسْوَةٍ مِنْ جِيرَانِهَا فَأَمْسَكْنَهَا ثُمَّ اقْتَضَّتْهَا بِإِصْبَعِهَا[1] فَلَمَّا قَدِمَ زَوْجُهَا سَأَلَ امْرَأَتَهُ عَنِ الْيَتِيمَةِ فَرَمَتْهَا بِالْفَاحِشَةِ وَ أَقَامَتِ الْبَيِّنَةَ مِنْ جِيرَانِهَا عَلَى ذَلِكَ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | سعد بن طریف | روی |  |
  | 1 | named_narrator | الاصبغ بن نباتة | عن |  |

### Chain 258 · `faqih-3245` — CLARIFIED
- Transmitters (student → teacher): سعد بن طريف → الاصبغ بن نباتة
- Corrected isnad (Arabic): «رَوَى سَعْدُ بْنُ طَرِيفٍ عَنِ الْأَصْبَغِ بْنِ نُبَاتَةَ قَالَ‌»
- Isnad ends / matn begins at: "أُتِيَ عُمَرُ بْنُ الْخَطَّابِ بِجَارِيَةٍ فَشَهِدَ عَلَيْهَا شُهُودٌ أَنَّهَا"
- Mursal opening: al-Ṣadūq → سعد بن طريف; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 259 · `faqih-3248`
- **Location:** vol. 3, p. 24 · seq 3260 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى عَمْرُو بْنُ ثَابِتٍ عَنْ أَبِيهِ عَنْ سَعْدِ بْنِ طَرِيفٍ عَنِ الْأَصْبَغِ بْنِ نُبَاتَةَ قَالَ‌ أُتِيَ عُمَرُ بْنُ الْخَطَّابِ بِامْرَأَةٍ تَزَوَّجَهَا شَيْخٌ فَلَمَّا أَنْ وَاقَعَهَا مَاتَ عَلَى بَطْنِهَا فَجَاءَتْ بِوَلَدٍ فَادَّعَى بَنُوهُ أَنَّهَا فَجَرَتْ وَ تَشَاهَدُوا عَلَيْهَا فَأَمَرَ بِهَا عُمَرُ أَنْ تُرْجَمَ فَمَرُّوا بِهَا عَلَى عَلِيِّ بْنِ أَبِي طَالِبٍ ع فَقَالَتْ يَا ابْنَ عَمِّ رَسُولِ اللَّهِ إِنِّي مَظْلُومَةٌ وَ هَذِهِ حُجَّتِي فَقَالَ هَاتِي حُجَّتَكِ فَدَفَعَتْ إِلَيْهِ كِتَاباً فَقَرَأَهُ فَقَالَ هَذِهِ الْمَرْأَةُ تُعْلِمُكُمْ بِيَوْمَ تَزَوَّجَهَا وَ يَوْمَ وَاقَعَهَا وَ كَيْفَ كَانَ جِمَاعُهُ لَهَا[2] رُدُّوا الْمَرْأَةَ فَلَمَّا كَانَ مِنَ الْغَدِ دَعَا عَلِيٌّ ع بِصِبْيَانٍ يَلْعَبُونَ أَتْرَابٍ‌[3] وَ فِيهِمُ ابْنُهَا فَقَالَ لَهُمُ الْعَبُوا فَلَعِبُوا حَتَّى إِذَا أَلْهَاهُمُ اللَّعِبُ فَصَاحَ بِهِمْ فَقَامُوا وَ قَامَ الْغُلَامُ الَّذِي هُوَ ابْنُ الْمَرْأَةِ مُتَّكِئاً عَلَى رَاحَتَيْهِ فَدَعَا بِهِ عَلِيٌّ ع فَوَرَّثَهُ مِنْ أَبِيهِ وَ جَلَدَ إِخْوَتَهُ الْمُفْتَرِينَ حَدّاً حَدّاً فَقَالَ لَهُ عُمَرُ كَيْفَ صَنَعْتَ قَالَ عَرَفْتُ ضَعْفَ الشَّيْخِ فِي تُكَأَةِ الْغُلَامِ عَلَى رَاحَتَيْهِ‌[4].
- **Isnad as currently extracted:**
  > رَوَى عَمْرُو بْنُ ثَابِتٍ عَنْ أَبِيهِ عَنْ سَعْدِ بْنِ طَرِيفٍ عَنِ الْأَصْبَغِ بْنِ نُبَاتَةَ قَالَ‌ أُتِيَ عُمَرُ بْنُ الْخَطَّابِ بِامْرَأَةٍ تَزَوَّجَهَا شَيْخٌ فَلَمَّا أَنْ وَاقَعَهَا مَاتَ عَلَى بَطْنِهَا فَجَاءَتْ بِوَلَدٍ فَادَّعَى بَنُوهُ أَنَّهَا فَجَرَتْ وَ تَشَاهَدُوا عَلَيْهَا فَأَمَرَ بِهَا عُمَرُ أَنْ تُرْجَمَ فَمَرُّوا بِهَا عَلَى عَلِيِّ بْنِ أَبِي طَالِبٍ ع فَقَالَتْ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عمرو بن ثابت | روی |  |
  | 1 | pronoun_relation | ابیه | عن | father |
  | 2 | named_narrator | سعد بن طریف | عن |  |
  | 3 | named_narrator | الاصبغ بن نباتة | عن |  |

### Chain 259 · `faqih-3248` — CLARIFIED
- Transmitters (student → teacher): عمرو بن ثابت → أبيه (غير مسمّى في النص) → سعد بن طريف → الاصبغ بن نباتة
- Corrected isnad (Arabic): «رَوَى عَمْرُو بْنُ ثَابِتٍ عَنْ أَبِيهِ عَنْ سَعْدِ بْنِ طَرِيفٍ عَنِ الْأَصْبَغِ بْنِ نُبَاتَةَ قَالَ‌»
- Isnad ends / matn begins at: "أُتِيَ عُمَرُ بْنُ الْخَطَّابِ بِامْرَأَةٍ تَزَوَّجَهَا شَيْخٌ فَلَمَّا أَنْ"
- Mursal opening: al-Ṣadūq → عمرو بن ثابت; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 260 · `faqih-3256`
- **Location:** vol. 3, p. 29 · seq 3268 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى السَّكُونِيُّ بِإِسْنَادِهِ‌[4] أَنَّ أَمِيرَ الْمُؤْمِنِينَ ع قَالَ‌ فِي رَجُلٍ أَمَرَ
عَبْدَهُ أَنْ يَقْتُلَ رَجُلًا فَقَتَلَهُ قَالَ هَلْ عَبْدُ الرَّجُلِ إِلَّا كَسَوْطِهِ وَ سَيْفِهِ فَقُتِلَ السَّيِّدُ وَ اسْتُودِعَ الْعَبْدُ السِّجْنَ‌[1].
- **Isnad as currently extracted:**
  > رَوَى السَّكُونِيُّ بِإِسْنَادِهِ‌[4] أَنَّ أَمِيرَ الْمُؤْمِنِينَ ع قَالَ‌ فِي رَجُلٍ أَمَرَ عَبْدَهُ أَنْ يَقْتُلَ رَجُلًا فَقَتَلَهُ قَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | imam | السکونی باسناده ان امیر المؤمنین ع | روی |  |

### Chain 260 · `faqih-3256` — CLARIFIED
- Transmitters (student → teacher): السكوني باسناده ان امير المؤمنين ع
- Corrected isnad (Arabic): «رَوَى السَّكُونِيُّ بِإِسْنَادِهِ‌[4] أَنَّ أَمِيرَ الْمُؤْمِنِينَ ع قَالَ‌»
- Isnad ends / matn begins at: "فِي رَجُلٍ أَمَرَ عَبْدَهُ أَنْ يَقْتُلَ رَجُلًا فَقَتَلَهُ قَالَ"
- Mursal opening: al-Ṣadūq → السكوني باسناده ان امير المؤمنين ع; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 261 · `faqih-3260`
- **Location:** vol. 3, p. 31 · seq 3272 · chain 1
- **Flags:** `matn_spill`
- **Full report (Arabic):**
  > فِي رِوَايَةِ أَحْمَدَ بْنِ أَبِي عَبْدِ اللَّهِ الْبَرْقِيِّ عَنْ عَلِيٍّ ع أَنَّهُ قَالَ‌ يَجِبُ عَلَى الْإِمَامِ أَنْ يَحْبِسَ الْفُسَّاقَ مِنَ الْعُلَمَاءِ وَ الْجُهَّالَ مِنَ الْأَطِبَّاءِ وَ الْمَفَالِيسَ‌[7] مِنَ‌
الْأَكْرِيَاءِ[1] وَ قَالَ ع حَبْسُ الْإِمَامِ بَعْدَ الْحَدِّ ظُلْمٌ‌[2].
- **Isnad as currently extracted:**
  > فِي رِوَايَةِ أَحْمَدَ بْنِ أَبِي عَبْدِ اللَّهِ الْبَرْقِيِّ عَنْ عَلِيٍّ ع أَنَّهُ قَالَ‌ يَجِبُ عَلَى الْإِمَامِ أَنْ يَحْبِسَ الْفُسَّاقَ مِنَ الْعُلَمَاءِ وَ الْجُهَّالَ مِنَ الْأَطِبَّاءِ وَ الْمَفَالِيسَ‌[7] مِنَ‌ الْأَكْرِيَاءِ[1] وَ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | فی روایة احمد بن ابی عبد الله البرقی |  |  |
  | 1 | imam | علی ع | عن |  |

### Chain 261 · `faqih-3260` — CLARIFIED
- Transmitters (student → teacher): احمد بن ابي عبد الله البرقي → علي ع
- Corrected isnad (Arabic): «فِي رِوَايَةِ أَحْمَدَ بْنِ أَبِي عَبْدِ اللَّهِ الْبَرْقِيِّ عَنْ عَلِيٍّ ع أَنَّهُ قَالَ‌»
- Isnad ends / matn begins at: "يَجِبُ عَلَى الْإِمَامِ أَنْ يَحْبِسَ الْفُسَّاقَ مِنَ الْعُلَمَاءِ وَ"
- Mursal opening: al-Ṣadūq → احمد بن ابي عبد الله البرقي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 262 · `faqih-3262`
- **Location:** vol. 3, p. 33 · seq 3274 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ فِي رَجُلَيْنِ كَانَ لِكُلِّ وَاحِدٍ مِنْهُمَا طَعَامٌ عِنْدَ صَاحِبِهِ وَ لَا يَدْرِي كُلُّ وَاحِدٍ مِنْهُمَا كَمْ لَهُ عِنْدَ صَاحِبِهِ فَقَالَ كُلُّ وَاحِدٍ مِنْهُمَا لِصَاحِبِهِ لَكَ مَا عِنْدَكَ وَ لِي مَا عِنْدِي فَقَالَ لَا بَأْسَ بِذَلِكَ إِذَا تَرَاضَيَا وَ طَابَتْ أَنْفُسُهُمَا[1].
- **Isnad as currently extracted:**
  > رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ فِي رَجُلَيْنِ كَانَ لِكُلِّ وَاحِدٍ مِنْهُمَا طَعَامٌ عِنْدَ صَاحِبِهِ وَ لَا يَدْرِي كُلُّ وَاحِدٍ مِنْهُمَا كَمْ لَهُ عِنْدَ صَاحِبِهِ فَقَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | العلاء | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |
  | 2 | imam | ابی جعفر ع | عن |  |

### Chain 262 · `faqih-3262` — CLARIFIED
- Transmitters (student → teacher): العلاء → محمد بن مسلم → ابي جعفر ع
- Corrected isnad (Arabic): «رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "فِي رَجُلَيْنِ كَانَ لِكُلِّ وَاحِدٍ مِنْهُمَا طَعَامٌ عِنْدَ صَاحِبِهِ"
- Mursal opening: al-Ṣadūq → العلاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim.

---

### Chain 263 · `faqih-3263`
- **Location:** vol. 3, p. 33 · seq 3275 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى عَلِيُّ بْنُ أَبِي حَمْزَةَ قَالَ‌ قُلْتُ لِأَبِي الْحَسَنِ ع رَجُلٌ يَهُودِيٌّ أَوْ نَصْرَانِيٌّ كَانَتْ لَهُ عِنْدِي أَرْبَعَةُ آلَافِ دِرْهَمٍ فَمَاتَ أَ لِي أَنْ أُصَالِحَ وَرَثَتَهُ وَ لَا أُعْلِمَهُمْ كَمْ كَانَ قَالَ لَا يَجُوزُ حَتَّى تُخْبِرَهُمْ‌[2].
- **Isnad as currently extracted:**
  > رَوَى عَلِيُّ بْنُ أَبِي حَمْزَةَ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن ابی حمزة | روی |  |

### Chain 263 · `faqih-3263` — CLARIFIED
- Transmitters (student → teacher): علي بن ابي حمزة → ابي الحسن ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى عَلِيُّ بْنُ أَبِي حَمْزَةَ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي الْحَسَنِ ع رَجُلٌ يَهُودِيٌّ أَوْ نَصْرَانِيٌّ كَانَتْ"
- Mursal opening: al-Ṣadūq → علي بن ابي حمزة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 264 · `faqih-3265`
- **Location:** vol. 3, p. 34 · seq 3277 · chain 1
- **Flags:** `mursal_opening`, `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > رَوَى حَمَّادٌ عَنِ الْحَلَبِيِّ عَنْ أَبِي عَبْدِ اللَّهِ ع‌ فِي الرَّجُلِ يُعْطِي أَقْفِزَةً مِنْ حِنْطَةٍ مَعْلُومَةٍ يَطْحَنُونَ بِالدَّرَاهِمِ فَلَمَّا فَرَغَ الطَّحَّانُ مِنْ طَحْنِهِ نَقَدَهُ الدَّرَاهِمَ وَ قَفِيزاً مِنْهُ وَ هُوَ شَيْ‌ءٌ قَدِ اصْطَلَحُوا عَلَيْهِ فِيمَا بَيْنَهُمْ‌[2] قَالَ لَا بَأْسَ بِهِ وَ إِنْ لَمْ يَكُنْ سَاعَرَهُ عَلَى ذَلِكَ‌[3].
- **Isnad as currently extracted:**
  > رَوَى حَمَّادٌ عَنِ الْحَلَبِيِّ عَنْ أَبِي عَبْدِ اللَّهِ ع‌ فِي الرَّجُلِ يُعْطِي أَقْفِزَةً مِنْ حِنْطَةٍ مَعْلُومَةٍ يَطْحَنُونَ بِالدَّرَاهِمِ فَلَمَّا فَرَغَ الطَّحَّانُ مِنْ طَحْنِهِ نَقَدَهُ الدَّرَاهِمَ وَ قَفِيزاً مِنْهُ وَ هُوَ شَيْ‌ءٌ قَدِ اصْطَلَحُوا عَلَيْهِ فِيمَا بَيْنَهُمْ‌[2] قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حماد | روی |  |
  | 1 | named_narrator | الحلبی | عن |  |
  | 2 | named_narrator | ابی عبد الله ع فی الرجل یعطی اقفزة من حنطة معلومة یطحنون بالدراهم فلما فرغ الطحان من طحنه نقده الدراهم و قفیزا منه و هو شی ء قد اصطلحوا علیه فیما بینهم | عن |  |

### Chain 264 · `faqih-3265` — CLARIFIED
- Transmitters (student → teacher): حماد → الحلبي → أبو عبد الله ع
- Corrected isnad (Arabic): «رَوَى حَمَّادٌ عَنِ الْحَلَبِيِّ عَنْ أَبِي عَبْدِ اللَّهِ ع‌»
- Isnad ends / matn begins at: "فِي الرَّجُلِ يُعْطِي أَقْفِزَةً مِنْ حِنْطَةٍ مَعْلُومَةٍ يَطْحَنُونَ بِالدَّرَاهِمِ"
- Mursal opening: al-Ṣadūq → حماد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name.

---

### Chain 265 · `faqih-3267`
- **Location:** vol. 3, p. 35 · seq 3279 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى مَنْصُورُ بْنُ يُونُسَ عَنْ مُحَمَّدٍ الْحَلَبِيِ‌[1] قَالَ‌ كُنْتُ قَاعِداً عِنْدَ قَاضٍ وَ عِنْدَهُ أَبُو جَعْفَرٍ ع جَالِسٌ فَأَتَاهُ رَجُلَانِ فَقَالَ أَحَدُهُمَا إِنِّي تَكَارَيْتُ إِبِلَ هَذَا الرَّجُلِ لِيَحْمِلَ لِي مَتَاعاً إِلَى بَعْضِ الْمَعَادِنِ فَاشْتَرَطْتُ أَنْ يُدْخِلَنِي الْمَعْدِنَ يَوْمَ كَذَا وَ كَذَا لِأَنَّ بِهَا سُوقاً أَتَخَوَّفُ أَنْ يَفُوتَنِي فَإِنِ احْتُبِسْتُ عَنْ ذَلِكَ حَطَطْتُ مِنَ الْكِرَاءِ عَنْ كُلِّ يَوْمٍ احْتَبَسْتُهُ كَذَا وَ كَذَا وَ إِنَّهُ حَبَسَنِي عَنْ ذَلِكَ الْوَقْتِ كَذَا وَ كَذَا يَوْماً فَقَالَ الْقَاضِي هَذَا شَرْطٌ فَاسِدٌ وَفِّهِ كِرَاهُ فَلَمَّا قَامَ الرَّجُلُ أَقْبَلَ إِلَيَّ أَبُو جَعْفَرٍ ع وَ قَالَ شَرْطُهُ هَذَا جَائِزٌ مَا لَمْ يَحُطَّ بِجَمِيعِ كِرَاهُ‌[2].
- **Isnad as currently extracted:**
  > رَوَى مَنْصُورُ بْنُ يُونُسَ عَنْ مُحَمَّدٍ الْحَلَبِيِ‌[1] قَالَ‌ كُنْتُ قَاعِداً عِنْدَ قَاضٍ وَ عِنْدَهُ أَبُو جَعْفَرٍ ع جَالِسٌ فَأَتَاهُ رَجُلَانِ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | منصور بن یونس | روی |  |
  | 1 | named_narrator | محمد الحلبی | عن |  |

### Chain 265 · `faqih-3267` — CLARIFIED
- Transmitters (student → teacher): منصور بن يونس → محمد الحلبي
- Corrected isnad (Arabic): «رَوَى مَنْصُورُ بْنُ يُونُسَ عَنْ مُحَمَّدٍ الْحَلَبِيِ‌[1] قَالَ‌»
- Isnad ends / matn begins at: "كُنْتُ قَاعِداً عِنْدَ قَاضٍ وَ عِنْدَهُ أَبُو جَعْفَرٍ ع"
- Mursal opening: al-Ṣadūq → منصور بن يونس; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim.

---

### Chain 266 · `faqih-3269`
- **Location:** vol. 3, p. 35 · seq 3281 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى عَبْدُ اللَّهِ بْنُ مُسْكَانَ عَنْ سُلَيْمَانَ بْنِ خَالِدٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ‌
ع عَنْ رَجُلَيْنِ كَانَ لَهُمَا مَالٌ مِنْهُ بِأَيْدِيهِمَا وَ مِنْهُ مُتَفَرِّقٌ عَنْهُمَا فَاقْتَسَمَا بِالسَّوِيَّةِ مَا كَانَ فِي أَيْدِيهِمَا وَ مَا كَانَ غَائِباً فَهَلَكَ نَصِيبُ أَحَدِهِمَا مِمَّا كَانَ عَنْهُ غَائِباً وَ اسْتَوْفَى الْآخَرُ أَ يَرُدُّ عَلَى صَاحِبِهِ قَالَ نَعَمْ مَا يَذْهَبُ بِمَالِهِ‌[1].
- **Isnad as currently extracted:**
  > رَوَى عَبْدُ اللَّهِ بْنُ مُسْكَانَ عَنْ سُلَيْمَانَ بْنِ خَالِدٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عبد الله بن مسکان | روی |  |
  | 1 | named_narrator | سلیمان بن خالد | عن |  |

### Chain 266 · `faqih-3269` — CLARIFIED
- Transmitters (student → teacher): عبد الله بن مسكان → سليمان بن خالد → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى عَبْدُ اللَّهِ بْنُ مُسْكَانَ عَنْ سُلَيْمَانَ بْنِ خَالِدٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ‌ ع عَنْ رَجُلَيْنِ كَانَ لَهُمَا"
- Mursal opening: al-Ṣadūq → عبد الله بن مسكان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 267 · `faqih-3274`
- **Location:** vol. 3, p. 38 · seq 3286 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ عَبْدِ اللَّهِ بْنِ أَبِي يَعْفُورٍ[1] قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع بِمَ تُعْرَفُ عَدَالَةُ الرَّجُلِ بَيْنَ الْمُسْلِمِينَ حَتَّى تُقْبَلَ شَهَادَتُهُ لَهُمْ وَ عَلَيْهِمْ فَقَالَ أَنْ تَعْرِفُوهُ بِالسِّتْرِ[2] وَ الْعَفَافِ- وَ كَفِّ الْبَطْنِ وَ الْفَرْجِ وَ الْيَدِ وَ اللِّسَانِ‌[3] وَ تُعْرَفُ بِاجْتِنَابِ الْكَبَائِرِ الَّتِي أَوْعَدَ اللَّهُ عَزَّ وَ جَلَّ عَلَيْهَا النَّارَ مِنْ شُرْبِ الْخُمُورِ وَ الزِّنَا وَ الرِّبَا وَ عُقُوقِ الْوَالِدَيْنِ وَ الْفِرَارِ مِنَ الزَّحْفِ وَ غَيْرِ ذَلِكَ وَ الدَّلَالَةُ عَلَى ذَلِكَ كُلِّهِ أَنْ يَكُونَ سَاتِراً لِجَمِيعِ عُيُوبِهِ حَتَّى يَحْرُمَ عَلَى الْمُسْلِمِينَ مَا وَرَاءَ ذَلِكَ مِنْ عَثَرَاتِهِ وَ عُيُوبِهِ وَ تَفْتِيشُ مَا وَرَاءَ ذَلِكَ وَ يَجِبَ عَلَيْهِمْ تَزْكِيَتُهُ وَ إِظْهَارُ عَدَالَتِهِ فِي النَّاسِ وَ يَكُونَ مَعَهُ التَّعَاهُدُ لِلصَّلَوَاتِ الْخَمْسِ إِذَا وَاظَبَ عَلَيْهِنَّ وَ حَفِظَ مَوَاقِيتَهُنَّ بِحُضُورِ جَمَاعَةٍ مِنَ الْمُسْلِمِينَ‌[4] وَ أَنْ لَا يَتَخَلَّفَ عَنْ جَمَاعَتِهِمْ فِي مُصَلَّاهُمْ إِلَّا مِنْ عِلَّةٍ فَإِذَا[5] كَانَ كَذَلِكَ لَازِماً لِمُصَلَّاهُ عِنْدَ حُضُورِ الصَّلَوَاتِ الْخَمْسِ فَإِذَا سُئِلَ عَنْهُ فِي قَبِيلَتِهِ وَ مَحَلَّتِهِ قَالُوا مَا رَأَيْنَا مِنْهُ إِلَّا خَيْراً- مُوَاظِباً عَلَى الصَّلَوَاتِ مُتَعَاهِداً لِأَوْقَاتِهَا فِي مُصَلَّاهُ فَإِنَّ ذَلِكَ يُجِيزُ شَهَادَتَهُ وَ عَدَالَتَهُ‌
بَيْنَ الْمُسْلِمِينَ وَ ذَلِكَ أَنَّ الصَّلَاةَ سِتْرٌ وَ كَفَّارَةٌ لِلذُّنُوبِ‌[1] وَ لَيْسَ يُمْكِنُ الشَّهَادَةُ عَلَى الرَّجُلِ بِأَنَّهُ يُصَلِّي إِذَا كَانَ لَا يَحْضُرُ مُصَلَّاهُ وَ يَتَعَاهَدُ جَمَاعَةَ الْمُسْلِمِينَ وَ إِنَّمَا جُعِلَ الْجَمَاعَةُ وَ الِاجْتِمَاعُ إِلَى الصَّلَاةِ لِكَيْ يُعْرَفَ مَنْ يُصَلِّي مِمَّنْ لَا يُصَلِّي وَ مَنْ يَحْفَظُ مَوَاقِيتَ الصَّلَوَاتِ مِمَّنْ يُضَيِّعُ وَ لَوْ لَا ذَلِكَ لَمْ يُمْكِنْ أَحَداً أَنْ يَشْهَدَ عَلَى آخَرَ بِصَلَاحٍ لِأَنَّ مَنْ لَا يُصَلِّي لَا صَلَاحَ لَهُ بَيْنَ الْمُسْلِمِينَ فَإِنَّ رَسُولَ اللَّهِ ص هَمَّ بِأَنْ يُحْرِقَ قَوْماً فِي مَنَازِلِهِمْ- لِتَرْكِهِمُ الْحُضُورَ لِجَمَاعَةِ الْمُسْ …[truncated]
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ عَبْدِ اللَّهِ بْنِ أَبِي يَعْفُورٍ[1] قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن عبد الله بن ابی یعفور | روی |  |

### Chain 267 · `faqih-3274` — CLARIFIED
- Transmitters (student → teacher): عبد الله بن ابي يعفور → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنْ عَبْدِ اللَّهِ بْنِ أَبِي يَعْفُورٍ[1] قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع بِمَ تُعْرَفُ عَدَالَةُ الرَّجُلِ"
- Mursal opening: al-Ṣadūq → عبد الله بن ابي يعفور; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 268 · `faqih-3277`
- **Location:** vol. 3, p. 40 · seq 3289 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى عَلِيُّ بْنُ أَسْبَاطٍ[5] عَنْ مُحَمَّدِ بْنِ الصَّلْتِ قَالَ‌ سَأَلْتُ أَبَا الْحَسَنِ‌
الرِّضَا ع- عَنْ رِفْقَةٍ كَانُوا فِي طَرِيقٍ فَقُطِعَ عَلَيْهِمُ الطَّرِيقُ فَأُخِذَ اللُّصُوصُ‌[1] فَشَهِدَ بَعْضُهُمْ لِبَعْضٍ فَقَالَ لَا تُقْبَلُ شَهَادَتُهُمْ إِلَّا بِالْإِقْرَارِ مِنَ اللُّصُوصِ أَوْ شَهَادَةٍ مِنْ غَيْرِهِمْ عَلَيْهِمْ‌[2].
- **Isnad as currently extracted:**
  > رَوَى عَلِيُّ بْنُ أَسْبَاطٍ[5] عَنْ مُحَمَّدِ بْنِ الصَّلْتِ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن اسباط | روی |  |
  | 1 | named_narrator | محمد بن الصلت | عن |  |

### Chain 268 · `faqih-3277` — CLARIFIED
- Transmitters (student → teacher): علي بن اسباط → محمد بن الصلت → ابا الحسن الرضا ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى عَلِيُّ بْنُ أَسْبَاطٍ[5] عَنْ مُحَمَّدِ بْنِ الصَّلْتِ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا الْحَسَنِ‌ الرِّضَا ع- عَنْ رِفْقَةٍ كَانُوا فِي"
- Mursal opening: al-Ṣadūq → علي بن اسباط; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 269 · `faqih-3281`
- **Location:** vol. 3, p. 42 · seq 3293 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ زَيْدٍ نَحْواً مِمَّا ذَكَرَهُ‌[2] عَنْ جَعْفَرِ بْنِ مُحَمَّدٍ عَنْ أَبِيهِ ع قَالَ‌ أُتِيَ عُمَرُ بْنُ الْخَطَّابِ بِقُدَامَةَ بْنِ مَظْعُونٍ قَدْ شَرِبَ الْخَمْرَ فَشَهِدَ عَلَيْهِ رَجُلَانِ أَحَدُهُمَا خَصِيٌّ وَ هُوَ عَمْرٌو التَّمِيمِيُّ وَ الْآخَرُ الْمُعَلَّى بْنُ الْجَارُودِ[3] فَشَهِدَ أَحَدُهُمَا أَنَّهُ رَآهُ يَشْرَبُ وَ شَهِدَ الْآخَرُ أَنَّهُ رَآهُ يَقِي‌ءُ الْخَمْرَ فَأَرْسَلَ عُمَرُ إِلَى أُنَاسٍ مِنْ أَصْحَابِ رَسُولِ اللَّهِ ص فِيهِمْ عَلِيُّ بْنُ أَبِي طَالِبٍ ع فَقَالَ لِعَلِيٍّ ع مَا تَقُولُ يَا أَبَا الْحَسَنِ فَإِنَّكَ الَّذِي قَالَ رَسُولُ اللَّهِ ص أَعْلَمُ هَذِهِ الْأُمَّةِ وَ أَقْضَاهَا بِالْحَقِّ فَإِنَّ هَذَيْنِ قَدِ اخْتَلَفَا فِي شَهَادَتِهِمَا فَقَالَ عَلِيٌّ ع مَا اخْتَلَفَا فِي شَهَادَتِهِمَا وَ مَا قَاءَهَا حَتَّى شَرِبَهَا[4] فَقَالَ هَلْ تَجُوزُ شَهَادَةُ الْخَصِيِّ فَقَالَ ع مَا ذَهَابُ أُنْثَيَيْهِ‌[5] إِلَّا كَذَهَابِ بَعْضِ أَعْضَائِهِ.
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ زَيْدٍ نَحْواً مِمَّا ذَكَرَهُ‌[2] عَنْ جَعْفَرِ بْنِ مُحَمَّدٍ عَنْ أَبِيهِ ع قَالَ‌ أُتِيَ عُمَرُ بْنُ الْخَطَّابِ بِقُدَامَةَ بْنِ مَظْعُونٍ قَدْ شَرِبَ الْخَمْرَ فَشَهِدَ عَلَيْهِ رَجُلَانِ أَحَدُهُمَا خَصِيٌّ وَ هُوَ عَمْرٌو التَّمِيمِيُّ وَ الْآخَرُ الْمُعَلَّى بْنُ الْجَارُودِ[3] فَشَهِدَ أَحَدُهُمَا أَنَّهُ رَآهُ يَشْرَبُ وَ شَهِدَ الْآخَرُ أَنَّهُ رَآهُ يَقِي‌ءُ الْخَمْرَ فَأَرْسَلَ عُمَرُ إِلَى أُنَاسٍ مِنْ أَصْحَابِ رَسُولِ اللَّهِ ص فِيهِمْ عَلِيُّ بْنُ أَبِي طَالِبٍ ع فَقَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن زید نحوا مما ذکره | روی |  |
  | 1 | named_narrator | جعفر بن محمد | عن |  |
  | 2 | imam | ابیه ع | عن |  |

### Chain 269 · `faqih-3281` — CLARIFIED
- Transmitters (student → teacher): الحسن بن زيد نحوا مما ذكره → جعفر بن محمد → ابيه ع
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ زَيْدٍ نَحْواً مِمَّا ذَكَرَهُ‌[2] عَنْ جَعْفَرِ بْنِ مُحَمَّدٍ عَنْ أَبِيهِ ع قَالَ‌»
- Isnad ends / matn begins at: "أُتِيَ عُمَرُ بْنُ الْخَطَّابِ بِقُدَامَةَ بْنِ مَظْعُونٍ قَدْ شَرِبَ"
- Mursal opening: al-Ṣadūq → الحسن بن زيد نحوا مما ذكره; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 270 · `faqih-3285`
- **Location:** vol. 3, p. 43 · seq 3297 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى الْعَلَاءُ بْنُ سَيَابَةَ[5] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ لَا تُقْبَلُ شَهَادَةُ صَاحِبِ النَّرْدِ وَ الْأَرْبَعَةَ عَشَرَ وَ صَاحِبِ الشَّاهَيْنِ‌[6] يَقُولُ لَا وَ اللَّهِ وَ بَلَى وَ اللَّهِ مَاتَ وَ اللَّهِ شَاهُهُ وَ قُتِلَ وَ اللَّهِ شَاهُهُ وَ اللَّهُ تَعَالَى ذِكْرُهُ شَاهُهُ مَا مَاتَ وَ لَا قُتِلَ‌[7].
- **Isnad as currently extracted:**
  > رَوَى الْعَلَاءُ بْنُ سَيَابَةَ[5] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ لَا تُقْبَلُ شَهَادَةُ صَاحِبِ النَّرْدِ وَ الْأَرْبَعَةَ عَشَرَ وَ صَاحِبِ الشَّاهَيْنِ‌[6] يَقُولُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | العلاء بن سیابة | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 270 · `faqih-3285` — CLARIFIED
- Transmitters (student → teacher): العلاء بن سيابة → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى الْعَلَاءُ بْنُ سَيَابَةَ[5] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "لَا تُقْبَلُ شَهَادَةُ صَاحِبِ النَّرْدِ وَ الْأَرْبَعَةَ عَشَرَ وَ"
- Mursal opening: al-Ṣadūq → العلاء بن سيابة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 271 · `faqih-3292`
- **Location:** vol. 3, p. 46 · seq 3304 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ عَبْدِ اللَّهِ بْنِ الْمُغِيرَةِ قَالَ‌ قُلْتُ لِلرِّضَا ع رَجُلٌ طَلَّقَ امْرَأَتَهُ وَ أَشْهَدَ شَاهِدَيْنِ نَاصِبِيَّيْنِ قَالَ كُلُّ مَنْ وُلِدَ عَلَى الْفِطْرَةِ وَ عُرِفَ بِالصَّلَاحِ فِي نَفْسِهِ جَازَتْ شَهَادَتُهُ‌[3].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ عَبْدِ اللَّهِ بْنِ الْمُغِيرَةِ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن عبد الله بن المغیرة | روی |  |

### Chain 271 · `faqih-3292` — CLARIFIED
- Transmitters (student → teacher): عبد الله بن المغيرة
- Corrected isnad (Arabic): «رُوِيَ عَنْ عَبْدِ اللَّهِ بْنِ الْمُغِيرَةِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِلرِّضَا ع رَجُلٌ طَلَّقَ امْرَأَتَهُ وَ أَشْهَدَ شَاهِدَيْنِ"
- Mursal opening: al-Ṣadūq → عبد الله بن المغيرة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 272 · `faqih-3293`
- **Location:** vol. 3, p. 47 · seq 3305 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ عُبَيْدِ اللَّهِ بْنِ عَلِيٍّ الْحَلَبِيِّ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع هَلْ تَجُوزُ شَهَادَةُ أَهْلِ الذِّمَّةِ عَلَى غَيْرِ أَهْلِ مِلَّتِهِمْ‌[1] قَالَ نَعَمْ إِنْ لَمْ يُوجَدْ مِنْ أَهْلِ مِلَّتِهِمْ جَازَتْ شَهَادَةُ غَيْرِهِمْ إِنَّهُ لَا يَصْلُحُ ذَهَابُ حَقِّ أَحَدٍ[2].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ عُبَيْدِ اللَّهِ بْنِ عَلِيٍّ الْحَلَبِيِّ قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن عبید الله بن علی الحلبی | روی |  |

### Chain 272 · `faqih-3293` — CLARIFIED
- Transmitters (student → teacher): عبيد الله بن علي الحلبي
- Corrected isnad (Arabic): «رُوِيَ عَنْ عُبَيْدِ اللَّهِ بْنِ عَلِيٍّ الْحَلَبِيِّ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع هَلْ تَجُوزُ شَهَادَةُ أَهْلِ"
- Mursal opening: al-Ṣadūq → عبيد الله بن علي الحلبي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 273 · `faqih-3294`
- **Location:** vol. 3, p. 47 · seq 3306 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ عَلِيٍّ الْوَشَّاءُ عَنْ أَحْمَدَ بْنِ عُمَرَ قَالَ‌ سَأَلْتُهُ عَنْ قَوْلِ اللَّهِ عَزَّ وَ جَلَّ- ذَوا عَدْلٍ مِنْكُمْ أَوْ آخَرانِ مِنْ غَيْرِكُمْ‌ قَالَ اللَّذَانِ مِنْكُمْ مُسْلِمَانِ وَ اللَّذَانِ مِنْ غَيْرِكُمْ مِنْ أَهْلِ الْكِتَابِ فَإِنْ لَمْ تَجِدْ مِنْ أَهْلِ الْكِتَابِ فَمِنَ الْمَجُوسِ لِأَنَّ رَسُولَ اللَّهِ ص قَالَ سُنُّوا بِهِمْ سُنَّةَ أَهْلِ الْكِتَابِ وَ ذَلِكَ إِذَا مَاتَ الرَّجُلُ بِأَرْضِ‌
غُرْبَةٍ فَلَمْ يَجِدْ مُسْلِمَيْنِ يُشْهِدُهُمَا فَرَجُلَانِ مِنْ أَهْلِ الْكِتَابِ‌[1].
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ عَلِيٍّ الْوَشَّاءُ عَنْ أَحْمَدَ بْنِ عُمَرَ قَالَ‌ سَأَلْتُهُ عَنْ قَوْلِ اللَّهِ عَزَّ وَ جَلَّ- ذَوا عَدْلٍ مِنْكُمْ أَوْ آخَرانِ مِنْ غَيْرِكُمْ‌ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن علی الوشاء | روی |  |
  | 1 | named_narrator | احمد بن عمر | عن |  |

### Chain 273 · `faqih-3294` — CLARIFIED
- Transmitters (student → teacher): الحسن بن علي الوشاء → احمد بن عمر
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ عَلِيٍّ الْوَشَّاءُ عَنْ أَحْمَدَ بْنِ عُمَرَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ قَوْلِ اللَّهِ عَزَّ وَ جَلَّ- ذَوا عَدْلٍ"
- Mursal opening: al-Ṣadūq → الحسن بن علي الوشاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 274 · `faqih-3294`
- **Location:** vol. 3, p. 47 · seq 3306 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ عَلِيٍّ الْوَشَّاءُ عَنْ أَحْمَدَ بْنِ عُمَرَ قَالَ‌ سَأَلْتُهُ عَنْ قَوْلِ اللَّهِ عَزَّ وَ جَلَّ- ذَوا عَدْلٍ مِنْكُمْ أَوْ آخَرانِ مِنْ غَيْرِكُمْ‌ قَالَ اللَّذَانِ مِنْكُمْ مُسْلِمَانِ وَ اللَّذَانِ مِنْ غَيْرِكُمْ مِنْ أَهْلِ الْكِتَابِ فَإِنْ لَمْ تَجِدْ مِنْ أَهْلِ الْكِتَابِ فَمِنَ الْمَجُوسِ لِأَنَّ رَسُولَ اللَّهِ ص قَالَ سُنُّوا بِهِمْ سُنَّةَ أَهْلِ الْكِتَابِ وَ ذَلِكَ إِذَا مَاتَ الرَّجُلُ بِأَرْضِ‌
غُرْبَةٍ فَلَمْ يَجِدْ مُسْلِمَيْنِ يُشْهِدُهُمَا فَرَجُلَانِ مِنْ أَهْلِ الْكِتَابِ‌[1].
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ عَلِيٍّ الْوَشَّاءُ عَنْ أَحْمَدَ بْنِ عُمَرَ قَالَ‌ سَأَلْتُهُ عَنْ قَوْلِ اللَّهِ عَزَّ وَ جَلَّ- ذَوا عَدْلٍ مِنْكُمْ أَوْ آخَرانِ مِنْ غَيْرِكُمْ‌ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن علی الوشاء | روی |  |
  | 1 | named_narrator | احمد بن عمر | عن |  |

### Chain 274 · `faqih-3294` — CLARIFIED
- Transmitters (student → teacher): الحسن بن علي الوشاء → احمد بن عمر
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ عَلِيٍّ الْوَشَّاءُ عَنْ أَحْمَدَ بْنِ عُمَرَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ قَوْلِ اللَّهِ عَزَّ وَ جَلَّ- ذَوا عَدْلٍ"
- Mursal opening: al-Ṣadūq → الحسن بن علي الوشاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 275 · `faqih-3297`
- **Location:** vol. 3, p. 48 · seq 3309 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنِ الْعَلَاءِ بْنِ سَيَابَةَ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ شَهَادَةِ مَنْ يَلْعَبُ بِالْحَمَامِ قَالَ لَا بَأْسَ إِذَا كَانَ لَا يُعْرَفُ بِفِسْقٍ قُلْتُ فَإِنَّ مَنْ قِبَلَنَا يَقُولُونَ-
قَالَ عُمَرُ هُوَ شَيْطَانٌ‌[1] فَقَالَ سُبْحَانَ اللَّهِ أَ مَا عَلِمْتَ أَنَّ رَسُولَ اللَّهِ ص قَالَ إِنَّ الْمَلَائِكَةَ لَتَنْفِرُ عِنْدَ الرِّهَانِ وَ تَلْعَنُ صَاحِبَهُ مَا خَلَا الْحَافِرَ وَ الْخُفَّ وَ الرِّيشَ وَ النَّصْلَ‌[2] فَإِنَّهَا تَحْضُرُهَا الْمَلَائِكَةُ وَ قَدْ سَابَقَ رَسُولُ اللَّهِ ص- أُسَامَةَ بْنَ زَيْدٍ وَ أَجْرَى الْخَيْلَ‌[3].
- **Isnad as currently extracted:**
  > رُوِيَ عَنِ الْعَلَاءِ بْنِ سَيَابَةَ قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن العلاء بن سیابة | روی |  |

### Chain 275 · `faqih-3297` — CLARIFIED
- Transmitters (student → teacher): العلاء بن سيابة → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنِ الْعَلَاءِ بْنِ سَيَابَةَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ شَهَادَةِ مَنْ يَلْعَبُ"
- Mursal opening: al-Ṣadūq → العلاء بن سيابة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 276 · `faqih-3303`
- **Location:** vol. 3, p. 51 · seq 3315 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى صَفْوَانُ بْنُ يَحْيَى عَنْ مُحَمَّدِ بْنِ الْفُضَيْلِ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ سَأَلْتُهُ عَنْ شَهَادَةِ النِّسَاءِ هَلْ تَجُوزُ فِي نِكَاحٍ أَوْ طَلَاقٍ أَوْ رَجْمٍ قَالَ تَجُوزُ شَهَادَةُ النِّسَاءِ فِيمَا لَا يَسْتَطِيعُ الرِّجَالُ النَّظَرَ إِلَيْهِ‌[4] وَ تَجُوزُ فِي النِّكَاحِ إِذَا كَانَ مَعَهُنَّ رَجُلٌ-
وَ لَا تَجُوزُ فِي الطَّلَاقِ وَ لَا فِي الدَّمِ وَ تَجُوزُ فِي حَدِّ الزِّنَا- إِذَا كَانَ ثَلَاثَةَ رِجَالٍ وَ امْرَأَتَيْنِ وَ لَا تَجُوزُ شَهَادَةُ رَجُلَيْنِ وَ أَرْبَعِ نِسْوَةٍ[1].
- **Isnad as currently extracted:**
  > رَوَى صَفْوَانُ بْنُ يَحْيَى عَنْ مُحَمَّدِ بْنِ الْفُضَيْلِ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ سَأَلْتُهُ عَنْ شَهَادَةِ النِّسَاءِ هَلْ تَجُوزُ فِي نِكَاحٍ أَوْ طَلَاقٍ أَوْ رَجْمٍ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان بن یحیی | روی |  |
  | 1 | named_narrator | محمد بن الفضیل | عن |  |
  | 2 | imam | ابی الحسن ع | عن |  |

### Chain 276 · `faqih-3303` — CLARIFIED
- Transmitters (student → teacher): صفوان بن يحيي → محمد بن الفضيل → ابي الحسن ع
- Corrected isnad (Arabic): «رَوَى صَفْوَانُ بْنُ يَحْيَى عَنْ مُحَمَّدِ بْنِ الْفُضَيْلِ عَنْ أَبِي الْحَسَنِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ شَهَادَةِ النِّسَاءِ هَلْ تَجُوزُ فِي نِكَاحٍ أَوْ"
- Mursal opening: al-Ṣadūq → صفوان بن يحيي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 277 · `faqih-3308`
- **Location:** vol. 3, p. 53 · seq 3320 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى ابْنُ أَبِي عُمَيْرٍ عَنِ الْحُسَيْنِ بْنِ خَالِدٍ الصَّيْرَفِيِ‌[1] عَنْ أَبِي الْحَسَنِ الْمَاضِي ع قَالَ‌ كَتَبْتُ إِلَيْهِ فِي رَجُلٍ مَاتَ وَ لَهُ أُمُّ وَلَدٍ وَ قَدْ جَعَلَ لَهَا سَيِّدُهَا شَيْئاً فِي حَيَاتِهِ ثُمَّ مَاتَ قَالَ فَكَتَبَ ع لَهَا مَا آتَاهَا بِهِ سَيِّدُهَا فِي حَيَاتِهِ مَعْرُوفٌ ذَلِكَ لَهَا[2] تُقْبَلُ عَلَى ذَلِكَ شَهَادَةُ الرَّجُلِ وَ الْمَرْأَةِ وَ الْخَدَمِ غَيْرِ الْمُتَّهَمِينَ‌[3].
- **Isnad as currently extracted:**
  > رَوَى ابْنُ أَبِي عُمَيْرٍ عَنِ الْحُسَيْنِ بْنِ خَالِدٍ الصَّيْرَفِيِ‌[1] عَنْ أَبِي الْحَسَنِ الْمَاضِي ع قَالَ‌ كَتَبْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن ابی عمیر | روی |  |
  | 1 | named_narrator | الحسین بن خالد الصیرفی | عن |  |
  | 2 | imam | ابی الحسن الماضی ع | عن |  |

### Chain 277 · `faqih-3308` — CLARIFIED
- Transmitters (student → teacher): ابن ابي عمير → الحسين بن خالد الصيرفي → ابي الحسن الماضي ع
- Corrected isnad (Arabic): «رَوَى ابْنُ أَبِي عُمَيْرٍ عَنِ الْحُسَيْنِ بْنِ خَالِدٍ الصَّيْرَفِيِ‌[1] عَنْ أَبِي الْحَسَنِ الْمَاضِي ع قَالَ‌»
- Isnad ends / matn begins at: "كَتَبْتُ إِلَيْهِ فِي رَجُلٍ مَاتَ وَ لَهُ أُمُّ وَلَدٍ"
- Mursal opening: al-Ṣadūq → ابن ابي عمير; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 278 · `faqih-3310`
- **Location:** vol. 3, p. 53 · seq 3322 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ عُمَرَ بْنِ يَزِيدَ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ مَاتَ وَ تَرَكَ امْرَأَةً وَ هِيَ حَامِلٌ فَوَضَعَتْ بَعْدَ مَوْتِهِ غُلَاماً ثُمَّ مَاتَ الْغُلَامُ بَعْدَ مَا وَقَعَ إِلَى الْأَرْضِ فَشَهِدَتِ الْمَرْأَةُ الَّتِي قَبِلَتْهَا بِهِ أَنَّهُ اسْتَهَلَ‌[5] وَ صَاحَ حِينَ وَقَعَ إِلَى الْأَرْضِ ثُمَّ مَاتَ بَعْدُ فَقَالَ عَلَى الْإِمَامِ أَنْ يُجِيزَ شَهَادَتَهَا فِي رُبُعِ مِيرَاثِ الْغُلَامِ‌[6].
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ عُمَرَ بْنِ يَزِيدَ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | عمر بن یزید | عن |  |

### Chain 278 · `faqih-3310` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → عمر بن يزيد → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ عُمَرَ بْنِ يَزِيدَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ مَاتَ وَ"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 279 · `faqih-3318`
- **Location:** vol. 3, p. 56 · seq 3330 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى عَلِيُّ بْنُ أَحْمَدَ بْنِ أَشْيَمَ‌[1] قَالَ‌ سَأَلْتُ أَبَا الْحَسَنِ ع عَنْ رَجُلٍ طَهُرَتِ امْرَأَتُهُ مِنْ حَيْضِهَا فَقَالَ فُلَانَةُ طَالِقٌ وَ قَوْمٌ يَسْمَعُونَ كَلَامَهُ وَ لَمْ يَقُلْ لَهُمُ اشْهَدُوا أَ يَقَعُ الطَّلَاقُ عَلَيْهَا قَالَ نَعَمْ هَذِهِ شَهَادَةٌ[2] أَ فَتَتْرُكُهَا مُعَلَّقَةً[3].
- **Isnad as currently extracted:**
  > رَوَى عَلِيُّ بْنُ أَحْمَدَ بْنِ أَشْيَمَ‌[1] قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن احمد بن اشیم | روی |  |

### Chain 279 · `faqih-3318` — CLARIFIED
- Transmitters (student → teacher): علي بن احمد بن اشيم → ابا الحسن ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى عَلِيُّ بْنُ أَحْمَدَ بْنِ أَشْيَمَ‌[1] قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا الْحَسَنِ ع عَنْ رَجُلٍ طَهُرَتِ امْرَأَتُهُ مِنْ"
- Mursal opening: al-Ṣadūq → علي بن احمد بن اشيم; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 280 · `faqih-3322`
- **Location:** vol. 3, p. 57 · seq 3334 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى عُثْمَانُ بْنُ عِيسَى عَنْ بَعْضِ أَصْحَابِنَا عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌
قُلْتُ لَهُ يَكُونُ لِلرَّجُلِ مِنْ إِخْوَانِي عِنْدِي الشَّهَادَةُ لَيْسَ كُلُّهَا تُجِيزُهَا الْقُضَاةُ عِنْدَنَا قَالَ إِذَا عَلِمْتَ أَنَّهَا حَقٌّ فَصَحِّحْهَا بِكُلِّ وَجْهٍ حَتَّى يَصِحَّ لَهُ حَقُّهُ‌[1].
- **Isnad as currently extracted:**
  > رَوَى عُثْمَانُ بْنُ عِيسَى عَنْ بَعْضِ أَصْحَابِنَا عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عثمان بن عیسی | روی |  |
  | 1 | collective_phrase | بعض اصحابنا | عن |  |
  | 2 | imam | ابی عبد الله ع | عن |  |

### Chain 280 · `faqih-3322` — CLARIFIED
- Transmitters (student → teacher): عثمان بن عيسي → بعض اصحابنا → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى عُثْمَانُ بْنُ عِيسَى عَنْ بَعْضِ أَصْحَابِنَا عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ يَكُونُ لِلرَّجُلِ مِنْ إِخْوَانِي عِنْدِي الشَّهَادَةُ لَيْسَ"
- Mursal opening: al-Ṣadūq → عثمان بن عيسي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 281 · `faqih-3326`
- **Location:** vol. 3, p. 59 · seq 3338 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى سَمَاعَةُ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ شُهُودُ الزُّورِ يُجْلَدُونَ حَدّاً وَ لَيْسَ لَهُ وَقْتٌ‌[4] ذَلِكَ إِلَى الْإِمَامِ وَ يُطَافُ بِهِمْ حَتَّى يُعْرَفُوا وَ لَا يَعُودُوا قَالَ قُلْتُ فَإِنْ تَابُوا وَ أَصْلَحُوا أَ تُقْبَلُ شَهَادَتُهُمْ بَعْدُ فَقَالَ إِذَا تَابُوا تَابَ اللَّهُ عَلَيْهِمْ وَ قُبِلَتْ شَهَادَتُهُمْ بَعْدُ.
- **Isnad as currently extracted:**
  > رَوَى سَمَاعَةُ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ شُهُودُ الزُّورِ يُجْلَدُونَ حَدّاً وَ لَيْسَ لَهُ وَقْتٌ‌[4] ذَلِكَ إِلَى الْإِمَامِ وَ يُطَافُ بِهِمْ حَتَّى يُعْرَفُوا وَ لَا يَعُودُوا قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | سماعة | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 281 · `faqih-3326` — CLARIFIED
- Transmitters (student → teacher): سماعة → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى سَمَاعَةُ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "شُهُودُ الزُّورِ يُجْلَدُونَ حَدّاً وَ لَيْسَ لَهُ وَقْتٌ‌[4] ذَلِكَ"
- Mursal opening: al-Ṣadūq → سماعة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 282 · `faqih-3329`
- **Location:** vol. 3, p. 60 · seq 3341 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `mursal_opening`, `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنِ الْعَلَاءِ وَ أَبِي أَيُّوبَ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع‌ فِي رَجُلَيْنِ شَهِدَا عَلَى رَجُلٍ غَائِبٍ عِنْدَ امْرَأَتِهِ بِأَنَّهُ طَلَّقَهَا فَاعْتَدَّتِ الْمَرْأَةُ وَ تَزَوَّجَتْ ثُمَّ إِنَّ الزَّوْجَ الْغَائِبَ قَدِمَ فَزَعَمَ أَنَّهُ لَمْ يُطَلِّقْهَا وَ أَكْذَبَ نَفْسَهُ أَحَدُ الشَّاهِدَيْنِ فَقَالَ لَا سَبِيلَ لِلْأَخِيرِ عَلَيْهَا وَ يُؤْخَذُ الصَّدَاقُ مِنَ الَّذِي شَهِدَ وَ رَجَعَ فَيُرَدُّ عَلَى الْأَخِيرِ[3] وَ يُفَرَّقُ بَيْنَهُمَا وَ تَعْتَدُّ مِنَ الْأَخِيرِ وَ لَا يَقْرَبُهَا الْأَوَّلُ حَتَّى تَنْقَضِيَ عِدَّتُهَا.
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنِ الْعَلَاءِ وَ أَبِي أَيُّوبَ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع‌ فِي رَجُلَيْنِ شَهِدَا عَلَى رَجُلٍ غَائِبٍ عِنْدَ امْرَأَتِهِ بِأَنَّهُ طَلَّقَهَا فَاعْتَدَّتِ الْمَرْأَةُ وَ تَزَوَّجَتْ ثُمَّ إِنَّ الزَّوْجَ الْغَائِبَ قَدِمَ فَزَعَمَ أَنَّهُ لَمْ يُطَلِّقْهَا وَ أَكْذَبَ نَفْسَهُ أَحَدُ الشَّاهِدَيْنِ فَقَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | العلاء | عن |  |
  | 2 | named_narrator | محمد بن مسلم | عن |  |
  | 3 | named_narrator | ابی جعفر ع فی رجلین شهدا علی رجل غائب عند امراته بانه طلقها فاعتدت المراة و تزوجت ثم ان الزوج الغائب قدم فزعم انه لم یطلقها و اکذب نفسه احد الشاهدین فقال | عن |  |

### Chain 282 · `faqih-3329` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → العلاء → محمد بن مسلم → أبو جعفر ع
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنِ الْعَلَاءِ وَ أَبِي أَيُّوبَ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع‌»
- Isnad ends / matn begins at: "فِي رَجُلَيْنِ شَهِدَا عَلَى رَجُلٍ غَائِبٍ عِنْدَ امْرَأَتِهِ بِأَنَّهُ"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim.

---

### Chain 283 · `faqih-3329`
- **Location:** vol. 3, p. 60 · seq 3341 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `mursal_opening`, `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنِ الْعَلَاءِ وَ أَبِي أَيُّوبَ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع‌ فِي رَجُلَيْنِ شَهِدَا عَلَى رَجُلٍ غَائِبٍ عِنْدَ امْرَأَتِهِ بِأَنَّهُ طَلَّقَهَا فَاعْتَدَّتِ الْمَرْأَةُ وَ تَزَوَّجَتْ ثُمَّ إِنَّ الزَّوْجَ الْغَائِبَ قَدِمَ فَزَعَمَ أَنَّهُ لَمْ يُطَلِّقْهَا وَ أَكْذَبَ نَفْسَهُ أَحَدُ الشَّاهِدَيْنِ فَقَالَ لَا سَبِيلَ لِلْأَخِيرِ عَلَيْهَا وَ يُؤْخَذُ الصَّدَاقُ مِنَ الَّذِي شَهِدَ وَ رَجَعَ فَيُرَدُّ عَلَى الْأَخِيرِ[3] وَ يُفَرَّقُ بَيْنَهُمَا وَ تَعْتَدُّ مِنَ الْأَخِيرِ وَ لَا يَقْرَبُهَا الْأَوَّلُ حَتَّى تَنْقَضِيَ عِدَّتُهَا.
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنِ الْعَلَاءِ وَ أَبِي أَيُّوبَ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع‌ فِي رَجُلَيْنِ شَهِدَا عَلَى رَجُلٍ غَائِبٍ عِنْدَ امْرَأَتِهِ بِأَنَّهُ طَلَّقَهَا فَاعْتَدَّتِ الْمَرْأَةُ وَ تَزَوَّجَتْ ثُمَّ إِنَّ الزَّوْجَ الْغَائِبَ قَدِمَ فَزَعَمَ أَنَّهُ لَمْ يُطَلِّقْهَا وَ أَكْذَبَ نَفْسَهُ أَحَدُ الشَّاهِدَيْنِ فَقَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | ابی ایوب | عن |  |
  | 2 | named_narrator | محمد بن مسلم | عن |  |
  | 3 | named_narrator | ابی جعفر ع فی رجلین شهدا علی رجل غائب عند امراته بانه طلقها فاعتدت المراة و تزوجت ثم ان الزوج الغائب قدم فزعم انه لم یطلقها و اکذب نفسه احد الشاهدین فقال | عن |  |

### Chain 283 · `faqih-3329` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → أبو أيوب → محمد بن مسلم → أبو جعفر ع
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنِ الْعَلَاءِ وَ أَبِي أَيُّوبَ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع‌»
- Isnad ends / matn begins at: "فِي رَجُلَيْنِ شَهِدَا عَلَى رَجُلٍ غَائِبٍ عِنْدَ امْرَأَتِهِ بِأَنَّهُ"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim.

---

### Chain 284 · `faqih-3330`
- **Location:** vol. 3, p. 60 · seq 3342 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى عَلِيُّ بْنُ مَطَرٍ[4] عَنْ عَبْدِ اللَّهِ بْنِ سِنَانٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ إِنَّ شُهُودَ الزُّورِ يُجْلَدُونَ حَدّاً لَيْسَ لَهُ وَقْتٌ ذَلِكَ إِلَى الْإِمَامِ وَ يُطَافُ بِهِمْ حَتَّى يَعْرِفَهُمُ النَّاسُ وَ قَوْلُهُ عَزَّ وَ جَلَّ-[5] وَ لا تَقْبَلُوا لَهُمْ شَهادَةً أَبَداً وَ أُولئِكَ هُمُ الْفاسِقُونَ إِلَّا الَّذِينَ تابُوا قُلْتُ بِمَ تُعْرَفُ تَوْبَتُهُ قَالَ يُكَذِّبُ نَفْسَهُ عَلَى رُءُوسِ الْأَشْهَادِ حَيْثُ يُضْرَبُ وَ يَسْتَغْفِرُ رَبَّهُ عَزَّ وَ جَلَّ فَإِنْ هُوَ فَعَلَ ذَلِكَ فَثَمَّ ظَهَرَتْ تَوْبَتُهُ.
- **Isnad as currently extracted:**
  > رَوَى عَلِيُّ بْنُ مَطَرٍ[4] عَنْ عَبْدِ اللَّهِ بْنِ سِنَانٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ إِنَّ شُهُودَ الزُّورِ يُجْلَدُونَ حَدّاً لَيْسَ لَهُ وَقْتٌ ذَلِكَ إِلَى الْإِمَامِ وَ يُطَافُ بِهِمْ حَتَّى يَعْرِفَهُمُ النَّاسُ وَ قَوْلُهُ عَزَّ وَ جَلَّ-[5] وَ لا تَقْبَلُوا لَهُمْ شَهادَةً أَبَداً وَ أُولئِكَ هُمُ الْفاسِقُونَ إِلَّا الَّذِينَ تابُوا قُلْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن مطر | روی |  |
  | 1 | named_narrator | عبد الله بن سنان | عن |  |
  | 2 | imam | ابی عبد الله ع | عن |  |

### Chain 284 · `faqih-3330` — CLARIFIED
- Transmitters (student → teacher): علي بن مطر → عبد الله بن سنان → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى عَلِيُّ بْنُ مَطَرٍ[4] عَنْ عَبْدِ اللَّهِ بْنِ سِنَانٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "إِنَّ شُهُودَ الزُّورِ يُجْلَدُونَ حَدّاً لَيْسَ لَهُ وَقْتٌ ذَلِكَ"
- Mursal opening: al-Ṣadūq → علي بن مطر; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 285 · `faqih-3334`
- **Location:** vol. 3, p. 61 · seq 3346 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى عَبْدُ اللَّهِ بْنُ أَبِي يَعْفُورٍ[5] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ إِذَا رَضِيَ صَاحِبُ الْحَقِّ بِيَمِينِ الْمُنْكِرِ لِحَقِّهِ فَاسْتَحْلَفَهُ فَحَلَفَ أَنْ لَا حَقَّ لَهُ قِبَلَهُ ذَهَبَتِ الْيَمِينُ بِحَقِّ الْمُدَّعِي وَ لَا دَعْوَى لَهُ قُلْتُ وَ إِنْ كَانَتْ لَهُ بَيِّنَةٌ عَادِلَةٌ قَالَ نَعَمْ وَ إِنْ أَقَامَ بَعْدَ
مَا اسْتَحْلَفَهُ بِاللَّهِ خَمْسِينَ قَسَامَةً[1] مَا كَانَ لَهُ حَقٌّ فَإِنَّ الْيَمِينَ قَدْ أَبْطَلَتْ كُلَّ مَا ادَّعَاهُ قَبْلَهُ مِمَّا قَدِ اسْتَحْلَفَهُ عَلَيْهِ‌[2].
- **Isnad as currently extracted:**
  > رَوَى عَبْدُ اللَّهِ بْنُ أَبِي يَعْفُورٍ[5] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ إِذَا رَضِيَ صَاحِبُ الْحَقِّ بِيَمِينِ الْمُنْكِرِ لِحَقِّهِ فَاسْتَحْلَفَهُ فَحَلَفَ أَنْ لَا حَقَّ لَهُ قِبَلَهُ ذَهَبَتِ الْيَمِينُ بِحَقِّ الْمُدَّعِي وَ لَا دَعْوَى لَهُ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عبد الله بن ابی یعفور | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 285 · `faqih-3334` — CLARIFIED
- Transmitters (student → teacher): عبد الله بن ابي يعفور → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى عَبْدُ اللَّهِ بْنُ أَبِي يَعْفُورٍ[5] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "إِذَا رَضِيَ صَاحِبُ الْحَقِّ بِيَمِينِ الْمُنْكِرِ لِحَقِّهِ فَاسْتَحْلَفَهُ فَحَلَفَ"
- Mursal opening: al-Ṣadūq → عبد الله بن ابي يعفور; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 286 · `faqih-3337`
- **Location:** vol. 3, p. 63 · seq 3349 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ يَاسِينَ الضَّرِيرِ عَنْ عَبْدِ الرَّحْمَنِ بْنِ أَبِي عَبْدِ اللَّهِ قَالَ‌ قُلْتُ لِلشَّيْخِ يَعْنِي مُوسَى بْنَ جَعْفَرٍ ع‌[2] أَخْبِرْنِي عَنِ الرَّجُلِ يَدَّعِي قِبَلَ الرَّجُلِ الْحَقَّ فَلَا يَكُونُ لَهُ بَيِّنَةٌ بِمَا لَهُ قَالَ فَيَمِينُ الْمُدَّعَى عَلَيْهِ‌[3] فَإِنْ حَلَفَ فَلَا حَقَّ لَهُ-
وَ إِنْ رَدَّ الْيَمِينَ عَلَى الْمُدَّعِي فَلَمْ يَحْلِفْ فَلَا حَقَّ لَهُ فَإِنْ كَانَ الْمَطْلُوبُ بِالْحَقِّ قَدْ مَاتَ وَ أُقِيمَتْ عَلَيْهِ الْبَيِّنَةُ فَعَلَى الْمُدَّعِي الْيَمِينُ بِاللَّهِ الَّذِي لَا إِلَهَ إِلَّا هُوَ لَقَدْ مَاتَ فُلَانٌ وَ إِنَّ حَقَّهُ لَعَلَيْهِ فَإِنْ حَلَفَ وَ إِلَّا فَلَا حَقَّ لَهُ لِأَنَّا لَا نَدْرِي لَعَلَّهُ قَدْ أَوْفَاهُ بِبَيِّنَةٍ لَا نَعْلَمُ مَوْضِعَهُمْ أَوْ بِغَيْرِ بَيِّنَةٍ قَبْلَ الْمَوْتِ فَمِنْ ثَمَّ صَارَتْ عَلَيْهِ الْيَمِينُ مَعَ الْبَيِّنَةِ وَ إِنِ ادَّعَى بِلَا بَيِّنَةٍ فَلَا حَقَّ لَهُ لِأَنَّ الْمُدَّعَى عَلَيْهِ لَيْسَ بِحَيٍّ وَ لَوْ كَانَ حَيّاً لَأُلْزِمَ الْيَمِينَ أَوِ الْحَقَّ أَوْ يَرُدُّ الْيَمِينَ‌[1] فَمِنْ ثَمَّ لَمْ يَثْبُتْ لَهُ حَقٌ‌[2].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ يَاسِينَ الضَّرِيرِ عَنْ عَبْدِ الرَّحْمَنِ بْنِ أَبِي عَبْدِ اللَّهِ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن یاسین الضریر | روی |  |
  | 1 | named_narrator | عبد الرحمن بن ابی عبد الله | عن |  |

### Chain 286 · `faqih-3337` — CLARIFIED
- Transmitters (student → teacher): ياسين الضرير → عبد الرحمن بن ابي عبد الله
- Corrected isnad (Arabic): «رُوِيَ عَنْ يَاسِينَ الضَّرِيرِ عَنْ عَبْدِ الرَّحْمَنِ بْنِ أَبِي عَبْدِ اللَّهِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِلشَّيْخِ يَعْنِي مُوسَى بْنَ جَعْفَرٍ ع‌[2] أَخْبِرْنِي عَنِ"
- Mursal opening: al-Ṣadūq → ياسين الضرير; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 287 · `faqih-3349`
- **Location:** vol. 3, p. 70 · seq 3361 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ أَبَا جَعْفَرٍ ع عَنِ الذِّمِّيِّ وَ الْعَبْدِ يُشْهَدَانِ عَلَى شَهَادَةٍ ثُمَّ يُسْلِمُ الذِّمِّيُّ وَ يُعْتَقُ الْعَبْدُ أَ تَجُوزُ شَهَادَتُهُمَا عَلَى مَا كَانَا أُشْهِدَا عَلَيْهِ قَالَ نَعَمْ إِذَا عُلِمَ مِنْهُمَا بَعْدَ ذَلِكَ خَيْرٌ جَازَتْ شَهَادَتُهُمَا.
- **Isnad as currently extracted:**
  > رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | العلاء | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |

### Chain 287 · `faqih-3349` — CLARIFIED
- Transmitters (student → teacher): العلاء → محمد بن مسلم → ابا جعفر ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا جَعْفَرٍ ع عَنِ الذِّمِّيِّ وَ الْعَبْدِ يُشْهَدَانِ"
- Mursal opening: al-Ṣadūq → العلاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 288 · `faqih-3352`
- **Location:** vol. 3, p. 71 · seq 3364 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى عَمْرُو بْنُ جُمَيْعٍ عَنْ أَبِي عَبْدِ اللَّهِ عَنْ أَبِيهِ ع قَالَ‌ أَشْهِدْ عَلَى شَهَادَتِكَ مَنْ يَنْصَحُكَ قَالُوا أَصْلَحَكَ اللَّهُ كَيْفَ يَزِيدُ وَ يَنْقُصُ قَالَ لَا وَ لَكِنْ مَنْ يَحْفَظُهَا عَلَيْكَ‌[3].
وَ لَا تَجُوزُ شَهَادَةٌ عَلَى شَهَادَةٍ عَلَى شَهَادَةٍ[4].
- **Isnad as currently extracted:**
  > رَوَى عَمْرُو بْنُ جُمَيْعٍ عَنْ أَبِي عَبْدِ اللَّهِ عَنْ أَبِيهِ ع قَالَ‌ أَشْهِدْ عَلَى شَهَادَتِكَ مَنْ يَنْصَحُكَ قَالُوا أَصْلَحَكَ اللَّهُ كَيْفَ يَزِيدُ وَ يَنْقُصُ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عمرو بن جمیع | روی |  |
  | 1 | named_narrator | ابی عبد الله | عن |  |
  | 2 | imam | ابیه ع | عن |  |

### Chain 288 · `faqih-3352` — CLARIFIED
- Transmitters (student → teacher): عمرو بن جميع → ابي عبد الله → ابيه ع
- Corrected isnad (Arabic): «رَوَى عَمْرُو بْنُ جُمَيْعٍ عَنْ أَبِي عَبْدِ اللَّهِ عَنْ أَبِيهِ ع قَالَ‌»
- Isnad ends / matn begins at: "أَشْهِدْ عَلَى شَهَادَتِكَ مَنْ يَنْصَحُكَ قَالُوا أَصْلَحَكَ اللَّهُ كَيْفَ"
- Mursal opening: al-Ṣadūq → عمرو بن جميع; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 289 · `faqih-3354`
- **Location:** vol. 3, p. 72 · seq 3366 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ عَلِيِّ بْنِ سُوَيْدٍ قَالَ‌ قُلْتُ لِأَبِي الْحَسَنِ الْمَاضِي ع يُشْهِدُنِي هَؤُلَاءِ عَلَى إِخْوَانِي قَالَ نَعَمْ أَقِمِ الشَّهَادَةَ لَهُمْ وَ إِنْ خِفْتَ عَلَى أَخِيكَ ضَرَراً.
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ عَلِيِّ بْنِ سُوَيْدٍ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن علی بن سوید | روی |  |

### Chain 289 · `faqih-3354` — CLARIFIED
- Transmitters (student → teacher): علي بن سويد → ابي الحسن الماضي ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنْ عَلِيِّ بْنِ سُوَيْدٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي الْحَسَنِ الْمَاضِي ع يُشْهِدُنِي هَؤُلَاءِ عَلَى إِخْوَانِي"
- Mursal opening: al-Ṣadūq → علي بن سويد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 290 · `faqih-3372`
- **Location:** vol. 3, p. 80 · seq 3384 · chain 1
- **Flags:** `matn_spill`, `no_imam_terminal`
- **Full report (Arabic):**
  > أَحْمَدُ بْنُ مُحَمَّدِ بْنِ أَبِي نَصْرٍ عَنْ عَبْدِ اللَّهِ بْنِ سِنَانٍ قَالَ‌ سَأَلْتُهُ عَنْ مَمْلُوكٍ بَيْنَ شُرَكَاءَ أَرَادَ أَحَدُهُمْ بَيْعَ نَصِيبِهِ قَالَ يَبِيعُهُ قَالَ قُلْتُ فَإِنَّهُمَا كَانَا اثْنَيْنِ فَأَرَادَ أَحَدُهُمَا بَيْعَ نَصِيبِهِ فَلَمَّا أَقْدَمَ عَلَى الْبَيْعِ قَالَ لَهُ شَرِيكُهُ أَعْطِنِي قَالَ هُوَ أَحَقُّ بِهِ ثُمَّ قَالَ ع لَا شُفْعَةَ فِي حَيَوَانٍ إِلَّا أَنْ يَكُونَ الشَّرِيكُ فِيهِ وَاحِداً[2].
- **Isnad as currently extracted:**
  > أَحْمَدُ بْنُ مُحَمَّدِ بْنِ أَبِي نَصْرٍ عَنْ عَبْدِ اللَّهِ بْنِ سِنَانٍ قَالَ‌ سَأَلْتُهُ عَنْ مَمْلُوكٍ بَيْنَ شُرَكَاءَ أَرَادَ أَحَدُهُمْ بَيْعَ نَصِيبِهِ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | احمد بن محمد بن ابی نصر |  |  |
  | 1 | named_narrator | عبد الله بن سنان | عن |  |

### Chain 290 · `faqih-3372` — CLARIFIED
- Transmitters (student → teacher): احمد بن محمد بن ابي نصر → عبد الله بن سنان
- Corrected isnad (Arabic): «أَحْمَدُ بْنُ مُحَمَّدِ بْنِ أَبِي نَصْرٍ عَنْ عَبْدِ اللَّهِ بْنِ سِنَانٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ مَمْلُوكٍ بَيْنَ شُرَكَاءَ أَرَادَ أَحَدُهُمْ بَيْعَ نَصِيبِهِ"
- Mursal opening: al-Ṣadūq → احمد بن محمد بن ابي نصر; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 291 · `faqih-3374`
- **Location:** vol. 3, p. 83 · seq 3386 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ مَالِكِ بْنِ عَطِيَّةَ عَنْ أَبِي بَصِيرٍ عَنْ أَبِي جَعْفَرٍ ع‌[3] قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ تَزَوَّجَ امْرَأَةً عَلَى بَيْتٍ فِي دَارٍ لَهُ وَ لَهُ فِي تِلْكَ الدَّارِ شُرَكَاءُ قَالَ جَائِزٌ لَهُ وَ لَهَا وَ لَا شُفْعَةَ لِأَحَدٍ مِنَ الشُّرَكَاءِ عَلَيْهَا[4].
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ مَالِكِ بْنِ عَطِيَّةَ عَنْ أَبِي بَصِيرٍ عَنْ أَبِي جَعْفَرٍ ع‌[3] قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ تَزَوَّجَ امْرَأَةً عَلَى بَيْتٍ فِي دَارٍ لَهُ وَ لَهُ فِي تِلْكَ الدَّارِ شُرَكَاءُ قَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | مالک بن عطیة | عن |  |
  | 2 | named_narrator | ابی بصیر | عن |  |
  | 3 | imam | ابی جعفر ع | عن |  |

### Chain 291 · `faqih-3374` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → مالك بن عطية → ابي بصير → ابي جعفر ع
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ مَالِكِ بْنِ عَطِيَّةَ عَنْ أَبِي بَصِيرٍ عَنْ أَبِي جَعْفَرٍ ع‌[3] قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ تَزَوَّجَ امْرَأَةً عَلَى بَيْتٍ فِي دَارٍ"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 292 · `faqih-3374`
- **Location:** vol. 3, p. 83 · seq 3386 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ مَالِكِ بْنِ عَطِيَّةَ عَنْ أَبِي بَصِيرٍ عَنْ أَبِي جَعْفَرٍ ع‌[3] قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ تَزَوَّجَ امْرَأَةً عَلَى بَيْتٍ فِي دَارٍ لَهُ وَ لَهُ فِي تِلْكَ الدَّارِ شُرَكَاءُ قَالَ جَائِزٌ لَهُ وَ لَهَا وَ لَا شُفْعَةَ لِأَحَدٍ مِنَ الشُّرَكَاءِ عَلَيْهَا[4].
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ مَالِكِ بْنِ عَطِيَّةَ عَنْ أَبِي بَصِيرٍ عَنْ أَبِي جَعْفَرٍ ع‌[3] قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ تَزَوَّجَ امْرَأَةً عَلَى بَيْتٍ فِي دَارٍ لَهُ وَ لَهُ فِي تِلْكَ الدَّارِ شُرَكَاءُ قَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | مالک بن عطیة | عن |  |
  | 2 | named_narrator | ابی بصیر | عن |  |
  | 3 | imam | ابی جعفر ع | عن |  |

### Chain 292 · `faqih-3374` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → مالك بن عطية → ابي بصير → ابي جعفر ع
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ مَالِكِ بْنِ عَطِيَّةَ عَنْ أَبِي بَصِيرٍ عَنْ أَبِي جَعْفَرٍ ع‌[3] قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ تَزَوَّجَ امْرَأَةً عَلَى بَيْتٍ فِي دَارٍ"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 293 · `faqih-3376`
- **Location:** vol. 3, p. 83 · seq 3388 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ عَبْدِ اللَّهِ بْنِ مُسْكَانَ عَنْ أَبِي هِلَالٍ الرَّازِيِّ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ وَكَّلَ رَجُلًا بِطَلَاقِ امْرَأَتِهِ إِذَا حَاضَتْ وَ طَهُرَتْ وَ خَرَجَ الرَّجُلُ‌
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ عَبْدِ اللَّهِ بْنِ مُسْكَانَ عَنْ أَبِي هِلَالٍ الرَّازِيِّ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن عبد الله بن مسکان | روی |  |
  | 1 | named_narrator | ابی هلال الرازی | عن |  |

### Chain 293 · `faqih-3376` — CLARIFIED
- Transmitters (student → teacher): عبد الله بن مسكان → ابي هلال الرازي → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنْ عَبْدِ اللَّهِ بْنِ مُسْكَانَ عَنْ أَبِي هِلَالٍ الرَّازِيِّ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ وَكَّلَ رَجُلًا بِطَلَاقِ"
- Mursal opening: al-Ṣadūq → عبد الله بن مسكان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 294 · `faqih-3377`
- **Location:** vol. 3, p. 84 · seq 3389 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ عَلَاءِ بْنِ سَيَابَةَ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ امْرَأَةٍ وَكَّلَتْ رَجُلًا بِأَنْ يُزَوِّجَهَا مِنْ رَجُلٍ فَقَبِلَ الْوَكَالَةَ فَأَشْهَدَتْ لَهُ بِذَلِكَ فَذَهَبَ الْوَكِيلُ فَزَوَّجَهَا ثُمَّ إِنَّهَا أَنْكَرَتْ ذَلِكَ الْوَكِيلَ وَ زَعَمَتْ أَنَّهَا عَزَلَتْهُ عَنِ الْوَكَالَةِ فَأَقَامَتْ شَاهِدَيْنِ أَنَّهَا عَزَلَتْهُ فَقَالَ مَا يَقُولُ مَنْ قِبَلَكُمْ فِي ذَلِكَ قَالَ قُلْتُ يَقُولُونَ يُنْظَرُ فِي ذَلِكَ فَإِنْ كَانَتْ عَزَلَتْهُ قَبْلَ أَنْ يُزَوِّجَ فَالْوَكَالَةُ بَاطِلَةٌ وَ التَّزْوِيجُ بَاطِلٌ وَ إِنْ عَزَلَتْهُ وَ قَدْ زَوَّجَهَا فَالتَّزْوِيجُ ثَابِتٌ عَلَى مَا زَوَّجَ الْوَكِيلُ وَ عَلَى مَا اتَّفَقَ مَعَهَا مِنَ الْوَكَالَةِ إِذَا لَمْ يَتَعَدَّ شَيْئاً مِمَّا أَمَرَتْ بِهِ وَ اشْتَرَطَتْ عَلَيْهِ فِي الْوَكَالَةِ قَالَ ثُمَّ قَالَ يَعْزِلُونَ الْوَكِيلَ عَنْ وَكَالَتِهَا وَ لَمْ تُعْلِمْهُ بِالْعَزْلِ فَقُلْتُ نَعَمْ يَزْعُمُونَ أَنَّهَا لَوْ وَكَّلَتْ رَجُلًا وَ أَشْهَدَتْ فِي الْمَلَإِ وَ قَالَتْ فِي الْمَلَإِ اشْهَدُوا أَنِّي قَدْ عَزَلْتُهُ وَ أَبْطَلْتُ وَكَالَتَهُ بِلَا أَنْ يَعْلَمَ بِالْعَزْلِ وَ يَنْقُضُونَ جَمِيعَ مَا فَعَلَ الْوَكِيلُ فِي النِّكَاحِ خَاصَّةً وَ فِي غَيْرِهِ لَا يُبْطِلُونَ الْوَكَالَةَ إِلَّا أَنْ يَعْلَمَ الْوَكِيلُ بِالْعَزْلِ وَ يَقُولُونَ الْمَالُ مِنْهُ عِوَضٌ لِصَاحِبِهِ‌[2] وَ الْفَرْجُ لَيْسَ مِنْهُ عِوَضٌ إِذَا وَقَعَ مِنْهُ وَلَدٌ[3] فَقَالَ ع سُبْحَانَ اللَّهِ مَا أَجْوَرَ هَذَا الْحُكْمَ وَ أَفْسَدَهُ إِنَّ النِّكَاحَ أَحْرَى وَ أَحْرَى أَنْ يُحْتَاطَ فِيهِ وَ هُوَ فَرْجٌ وَ مِنْهُ يَكُونُ الْوَلَدُ إِنَّ عَلِيّاً ع أَتَتْهُ امْرَأَةٌ اسْتَعْدَتْهُ عَلَى أَخِيهَا[4] فَقَالَتْ يَا أَمِيرَ الْمُؤْمِنِينَ وَكَّلْتُ أَخِي هَذَا بِأَنْ يُزَوِّجَنِي رَجُلًا وَ أَشْهَدْتُ لَهُ ثُمَّ عَزَلْتُهُ مِنْ سَاعَتِهِ تِلْكَ فَذَهَبَ فَزَوَّجَنِي وَ لِي بَيِّنَةٌ أَنِّي عَزَلْتُهُ قَبْلَ أَنْ يُزَوِّجَنِي فَأَقَامَتِ الْبَيِّنَةَ فَقَالَ الْأَخُ يَا أَمِيرَ الْمُؤْمِنِينَ إِنَّهَا وَكَّلَتْنِي وَ لَمْ تُعْلِمْنِي أَنَّهَا عَزَلَتْنِي‌
عَنِ الْوَكَالَةِ حَتَّى زَوَّجْتُهَا كَمَا أَمَرَتْنِي ف …[truncated]
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ عَلَاءِ بْنِ سَيَابَةَ قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن علاء بن سیابة | روی |  |

### Chain 294 · `faqih-3377` — CLARIFIED
- Transmitters (student → teacher): علاء بن سيابة → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنْ عَلَاءِ بْنِ سَيَابَةَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ امْرَأَةٍ وَكَّلَتْ رَجُلًا"
- Mursal opening: al-Ṣadūq → علاء بن سيابة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 295 · `faqih-3378`
- **Location:** vol. 3, p. 85 · seq 3390 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رُوِيَ عَنْ دَاوُدَ بْنِ الْحُصَيْنِ عَنْ عُمَرَ بْنِ حَنْظَلَةَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ قَالَ لآِخَرَ اخْطُبْ لِي فُلَانَةَ فَمَا فَعَلْتَ شَيْئاً مِمَّا قَاوَلْتَ مِنْ صَدَاقٍ أَوْ ضَمِنْتَ مِنْ شَيْ‌ءٍ أَوْ شَرَطْتَ فَذَلِكَ لِي رِضًا وَ هُوَ لَازِمٌ لِي وَ لَمْ يُشْهِدْ عَلَى ذَلِكَ فَذَهَبَ فَخَطَبَ لَهُ وَ بَذَلَ عَنْهُ الصَّدَاقَ وَ غَيْرَ ذَلِكَ مِمَّا طَالَبُوهُ وَ سَأَلُوهُ فَلَمَّا رَجَعَ أَنْكَرَ ذَلِكَ كُلَّهُ قَالَ يُغَرَّمُ لَهَا نِصْفَ الصَّدَاقِ عَنْهُ‌[2] وَ ذَلِكَ أَنَّهُ هُوَ
الَّذِي ضَيَّعَ حَقَّهَا[1] فَلَمَّا لَمْ يُشْهِدْ لَهَا عَلَيْهِ بِذَلِكَ الَّذِي قَالَ لَهُ‌[2] حَلَّ لَهَا أَنْ تَتَزَوَّجَ وَ لَا تَحِلُّ لِلْأَوَّلِ فِيمَا بَيْنَهُ وَ بَيْنَ اللَّهِ عَزَّ وَ جَلَّ إِلَّا أَنْ يُطَلِّقَهَا[3] لِأَنَّ اللَّهَ تَعَالَى يَقُولُ- فَإِمْساكٌ بِمَعْرُوفٍ أَوْ تَسْرِيحٌ بِإِحْسانٍ‌ فَإِنْ لَمْ يَفْعَلْ فَإِنَّهُ مَأْثُومٌ فِيمَا بَيْنَهُ وَ بَيْنَ اللَّهِ عَزَّ وَ جَلَّ وَ كَانَ الْحُكْمُ الظَّاهِرُ حُكْمَ الْإِسْلَامِ وَ قَدْ أَبَاحَ اللَّهُ عَزَّ وَ جَلَّ لَهَا أَنْ تَتَزَوَّجَ.
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ دَاوُدَ بْنِ الْحُصَيْنِ عَنْ عُمَرَ بْنِ حَنْظَلَةَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن داود بن الحصین | روی |  |
  | 1 | named_narrator | عمر بن حنظلة | عن |  |
  | 2 | imam | ابی عبد الله ع | عن |  |

### Chain 295 · `faqih-3378` — CLARIFIED
- Transmitters (student → teacher): داود بن الحصين → عمر بن حنظلة → ابي عبد الله ع
- Corrected isnad (Arabic): «رُوِيَ عَنْ دَاوُدَ بْنِ الْحُصَيْنِ عَنْ عُمَرَ بْنِ حَنْظَلَةَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ قَالَ لآِخَرَ اخْطُبْ لِي فُلَانَةَ فَمَا"
- Mursal opening: al-Ṣadūq → داود بن الحصين; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 296 · `faqih-3380`
- **Location:** vol. 3, p. 87 · seq 3392 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى حَمَّادٌ عَنِ الْحَلَبِيِ‌[4] عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌ فِي رَجُلٍ وَلَّتْهُ امْرَأَةٌ أَمْرَهَا[5] إِمَّا ذَاتُ قَرَابَةٍ أَوْ جَارَةٌ لَهُ لَا يَعْلَمُ دَخِيلَةَ أَمْرِهَا فَوَجَدَهَا قَدْ دَلَّسَتْ عَيْباً هُوَ بِهَا قَالَ يُؤْخَذُ الْمَهْرُ مِنْهَا[6] وَ لَا يَكُونُ عَلَى الَّذِي زَوَّجَهَا شَيْ‌ءٌ وَ قَالَ فِي امْرَأَةٍ وَلَّتْ أَمْرَهَا رَجُلًا فَقَالَتْ زَوِّجْنِي فُلَاناً قَالَ لَا زَوَّجْتُكِ حَتَّى تُشْهِدِي-
بِأَنَّ أَمْرَكِ بِيَدِي فَأَشْهَدَتْ لَهُ فَقَالَ عِنْدَ التَّزْوِيجِ لِلَّذِي يَخْطُبُهَا يَا فُلَانُ عَلَيْكَ كَذَا وَ كَذَا قَالَ نَعَمْ فَقَالَ هُوَ لِلْقَوْمِ‌[1] اشْهَدُوا أَنَّ ذَلِكَ لَهَا عِنْدِي وَ قَدْ زَوَّجْتُهَا مِنْ نَفْسِي فَقَالَتِ الْمَرْأَةُ مَا كُنْتُ أَتَزَوَّجُكَ وَ لَا كَرَامَةَ وَ لَا أَمْرِي إِلَّا بِيَدِي وَ مَا وَلَّيْتُكَ أَمْرِي إِلَّا حَيَاءً مِنَ الْكَلَامِ قَالَ تُنْزَعُ مِنْهُ وَ يُوجَعُ رَأْسُهُ‌[2].
- **Isnad as currently extracted:**
  > رَوَى حَمَّادٌ عَنِ الْحَلَبِيِ‌[4] عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌ فِي رَجُلٍ وَلَّتْهُ امْرَأَةٌ أَمْرَهَا[5] إِمَّا ذَاتُ قَرَابَةٍ أَوْ جَارَةٌ لَهُ لَا يَعْلَمُ دَخِيلَةَ أَمْرِهَا فَوَجَدَهَا قَدْ دَلَّسَتْ عَيْباً هُوَ بِهَا قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حماد | روی |  |
  | 1 | named_narrator | الحلبی | عن |  |
  | 2 | imam | ابی عبد الله ع | عن |  |

### Chain 296 · `faqih-3380` — CLARIFIED
- Transmitters (student → teacher): حماد → الحلبي → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى حَمَّادٌ عَنِ الْحَلَبِيِ‌[4] عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌»
- Isnad ends / matn begins at: "فِي رَجُلٍ وَلَّتْهُ امْرَأَةٌ أَمْرَهَا[5] إِمَّا ذَاتُ قَرَابَةٍ أَوْ"
- Mursal opening: al-Ṣadūq → حماد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 297 · `faqih-3382`
- **Location:** vol. 3, p. 89 · seq 3394 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى حَمَّادُ بْنُ عِيسَى عَمَّنْ أَخْبَرَهُ عَنْ حَرِيزٍ[1] عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ أَوَّلُ مَنْ سُوهِمَ عَلَيْهِ مَرْيَمُ بِنْتُ عِمْرَانَ وَ هُوَ قَوْلُ اللَّهِ عَزَّ وَ جَلَّ- وَ ما كُنْتَ لَدَيْهِمْ إِذْ يُلْقُونَ أَقْلامَهُمْ أَيُّهُمْ يَكْفُلُ مَرْيَمَ‌ وَ السِّهَامُ سِتَّةٌ ثُمَّ اسْتَهَمُوا فِي يُونُسَ ع لَمَّا رَكِبَ مَعَ الْقَوْمِ فَوَقَعَتِ‌[2] السَّفِينَةُ فِي اللُّجَّةِ فَاسْتَهَمُوا فَوَقَعَ السَّهْمُ عَلَى يُونُسَ ثَلَاثَ مَرَّاتٍ قَالَ فَمَضَى يُونُسُ ع إِلَى صَدْرِ السَّفِينَةِ فَإِذَا الْحُوتُ فَاتِحٌ فَاهُ فَرَمَى نَفْسَهُ ثُمَّ كَانَ عِنْدَ عَبْدِ الْمُطَّلِبِ تِسْعَةُ بَنِينَ فَنَذَرَ فِي الْعَاشِرِ إِنْ رَزَقَهُ اللَّهُ غُلَاماً أَنْ يَذْبَحَهُ- فَلَمَّا وُلِدَ عَبْدُ اللَّهِ لَمْ يَكُنْ يَقْدِرُ أَنْ يَذْبَحَهُ‌[3] وَ رَسُولُ اللَّهِ ص فِي صُلْبِهِ-
- **Isnad as currently extracted:**
  > رَوَى حَمَّادُ بْنُ عِيسَى عَمَّنْ أَخْبَرَهُ عَنْ حَرِيزٍ[1] عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ أَوَّلُ مَنْ سُوهِمَ عَلَيْهِ مَرْيَمُ بِنْتُ عِمْرَانَ وَ هُوَ قَوْلُ اللَّهِ عَزَّ وَ جَلَّ- وَ ما كُنْتَ لَدَيْهِمْ إِذْ يُلْقُونَ أَقْلامَهُمْ أَيُّهُمْ يَكْفُلُ مَرْيَمَ‌ وَ السِّهَامُ سِتَّةٌ ثُمَّ اسْتَهَمُوا فِي يُونُسَ ع لَمَّا رَكِبَ مَعَ الْقَوْمِ فَوَقَعَتِ‌[2] السَّفِينَةُ فِي اللُّجَّةِ فَاسْتَهَمُوا فَوَقَعَ السَّهْمُ عَلَى يُونُسَ ثَلَاثَ مَرَّاتٍ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حماد بن عیسی عمن | روی |  |
  | 1 | named_narrator | عن حریز | اخبره |  |
  | 2 | imam | ابی جعفر ع | عن |  |

### Chain 297 · `faqih-3382` — CLARIFIED
- Transmitters (student → teacher): حماد بن عيسي عمن → حريز → ابي جعفر ع
- Corrected isnad (Arabic): «رَوَى حَمَّادُ بْنُ عِيسَى عَمَّنْ أَخْبَرَهُ عَنْ حَرِيزٍ[1] عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "أَوَّلُ مَنْ سُوهِمَ عَلَيْهِ مَرْيَمُ بِنْتُ عِمْرَانَ وَ هُوَ"
- Mursal opening: al-Ṣadūq → حماد بن عيسي عمن; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 298 · `faqih-3383`
- **Location:** vol. 3, p. 92 · seq 3395 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ مُحَمَّدِ بْنِ الْحَكِيمِ‌[1] قَالَ‌ سَأَلْتُ أَبَا الْحَسَنِ مُوسَى بْنَ جَعْفَرٍ ع عَنْ شَيْ‌ءٍ فَقَالَ لِي كُلُّ مَجْهُولٍ فَفِيهِ الْقُرْعَةُ فَقُلْتُ إِنَّ الْقُرْعَةَ تُخْطِئُ وَ تُصِيبُ فَقَالَ كُلُّ مَا حَكَمَ اللَّهُ عَزَّ وَ جَلَّ بِهِ فَلَيْسَ بِمُخْطِئٍ.
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ مُحَمَّدِ بْنِ الْحَكِيمِ‌[1] قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن محمد بن الحکیم | روی |  |

### Chain 298 · `faqih-3383` — CLARIFIED
- Transmitters (student → teacher): محمد بن الحكيم → ابا الحسن موسي بن جعفر ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنْ مُحَمَّدِ بْنِ الْحَكِيمِ‌[1] قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا الْحَسَنِ مُوسَى بْنَ جَعْفَرٍ ع عَنْ شَيْ‌ءٍ"
- Mursal opening: al-Ṣadūq → محمد بن الحكيم; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 299 · `faqih-3386`
- **Location:** vol. 3, p. 92 · seq 3398 · chain 1
- **Flags:** `matn_spill`, `multi_route`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى الْحَكَمُ بْنُ مِسْكِينٍ‌[4] عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ إِذَا وَطِئَ رَجُلَانِ أَوْ ثَلَاثَةٌ جَارِيَةً فِي طُهْرٍ وَاحِدٍ فَوَلَدَتْ فَادَّعَوْهُ جَمِيعاً أَقْرَعَ الْوَالِي بَيْنَهُمْ فَمَنْ قَرَعَ‌[5] كَانَ الْوَلَدُ وَلَدَهُ وَ يَرُدُّ قِيمَةَ الْوَلَدِ عَلَى صَاحِبِ الْجَارِيَةِ[6] قَالَ فَإِنِ اشْتَرَى رَجُلٌ جَارِيَةً فَجَاءَ رَجُلٌ فَاسْتَحَقَّهَا وَ قَدْ وَلَدَتْ مِنَ الْمُشْتَرِي رَدَّ
الْجَارِيَةَ عَلَيْهِ وَ كَانَ لَهُ وَلَدُهَا بِقِيمَتِهِ‌[1].
- **Isnad as currently extracted:**
  > رَوَى الْحَكَمُ بْنُ مِسْكِينٍ‌[4] عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ إِذَا وَطِئَ رَجُلَانِ أَوْ ثَلَاثَةٌ جَارِيَةً فِي طُهْرٍ وَاحِدٍ فَوَلَدَتْ فَادَّعَوْهُ جَمِيعاً أَقْرَعَ الْوَالِي بَيْنَهُمْ فَمَنْ قَرَعَ‌[5] كَانَ الْوَلَدُ وَلَدَهُ وَ يَرُدُّ قِيمَةَ الْوَلَدِ عَلَى صَاحِبِ الْجَارِيَةِ[6] قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحکم بن مسکین | روی |  |
  | 1 | named_narrator | معاویة بن عمار | عن |  |
  | 2 | imam | ابی عبد الله ع | عن |  |

### Chain 299 · `faqih-3386` — CLARIFIED
- Transmitters (student → teacher): الحكم بن مسكين → معاوية بن عمار → أبو عبد الله ع
- Corrected isnad (Arabic): «رَوَى الْحَكَمُ بْنُ مِسْكِينٍ‌[4] عَنْ مُعَاوِيَةَ بْنِ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "إِذَا وَطِئَ رَجُلَانِ أَوْ ثَلَاثَةٌ جَارِيَةً فِي طُهْرٍ وَاحِدٍ"
- Mursal opening: al-Ṣadūq → الحكم بن مسكين; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The route is grammatically complete. The tokenizer’s `multi_route` flag was triggered by successive rulings and multiple actors inside the matn, not by a fork in transmission.
---

### Chain 300 · `faqih-3390`
- **Location:** vol. 3, p. 94 · seq 3402 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ أَبَا جَعْفَرٍ ع عَنْ رَجُلٍ يَكُونُ لَهُ الْمَمْلُوكُونَ فَيُوصِي بِعِتْقِ ثُلُثِهِمْ قَالَ كَانَ عَلِيٌّ ع يُسْهِمُ بَيْنَهُمْ.
- **Isnad as currently extracted:**
  > رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حریز | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |

### Chain 300 · `faqih-3390` — CLARIFIED
- Transmitters (student → teacher): حريز → محمد بن مسلم → ابا جعفر ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا جَعْفَرٍ ع عَنْ رَجُلٍ يَكُونُ لَهُ الْمَمْلُوكُونَ"
- Mursal opening: al-Ṣadūq → حريز; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 301 · `faqih-3392`
- **Location:** vol. 3, p. 94 · seq 3404 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ جَمِيلٍ عَنْ فُضَيْلِ بْنِ يَسَارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ مَوْلُودٍ لَيْسَ لَهُ مَا لِلرِّجَالِ وَ لَيْسَ لَهُ مَا لِلنِّسَاءِ قَالَ هَذَا يُقْرِعُ عَلَيْهِ الْإِمَامُ يَكْتُبُ عَلَى سَهْمٍ عَبْدُ اللَّهِ وَ عَلَى سَهْمٍ آخَرَ أَمَةُ اللَّهِ ثُمَّ يَقُولُ الْإِمَامُ أَوِ الْمُقْرِعُ اللَّهُمَّ أَنْتَ اللَّهُ لَا إِلَهَ إِلَّا أَنْتَ‌ عالِمَ الْغَيْبِ وَ الشَّهادَةِ أَنْتَ تَحْكُمُ بَيْنَ عِبادِكَ فِي ما كانُوا فِيهِ يَخْتَلِفُونَ‌ بَيِّنْ لَنَا أَمْرَ هَذَا الْمَوْلُودِ حَتَّى يُوَرَّثَ مَا فَرَضْتَ لَهُ فِي كِتَابِكَ ثُمَّ يَطْرَحُ السَّهْمَيْنِ فِي سِهَامٍ مُبْهَمَةٍ ثُمَّ تُجَالُ فَأَيُّهُمَا خَرَجَ وُرِّثَ عَلَيْهِ.
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ جَمِيلٍ عَنْ فُضَيْلِ بْنِ يَسَارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ مَوْلُودٍ لَيْسَ لَهُ مَا لِلرِّجَالِ وَ لَيْسَ لَهُ مَا لِلنِّسَاءِ قَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | جمیل | عن |  |
  | 2 | named_narrator | فضیل بن یسار | عن |  |
  | 3 | imam | ابی عبد الله ع | عن |  |

### Chain 301 · `faqih-3392` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → جميل → فضيل بن يسار → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ جَمِيلٍ عَنْ فُضَيْلِ بْنِ يَسَارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ مَوْلُودٍ لَيْسَ لَهُ مَا لِلرِّجَالِ وَ لَيْسَ"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 302 · `faqih-3392`
- **Location:** vol. 3, p. 94 · seq 3404 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ جَمِيلٍ عَنْ فُضَيْلِ بْنِ يَسَارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ مَوْلُودٍ لَيْسَ لَهُ مَا لِلرِّجَالِ وَ لَيْسَ لَهُ مَا لِلنِّسَاءِ قَالَ هَذَا يُقْرِعُ عَلَيْهِ الْإِمَامُ يَكْتُبُ عَلَى سَهْمٍ عَبْدُ اللَّهِ وَ عَلَى سَهْمٍ آخَرَ أَمَةُ اللَّهِ ثُمَّ يَقُولُ الْإِمَامُ أَوِ الْمُقْرِعُ اللَّهُمَّ أَنْتَ اللَّهُ لَا إِلَهَ إِلَّا أَنْتَ‌ عالِمَ الْغَيْبِ وَ الشَّهادَةِ أَنْتَ تَحْكُمُ بَيْنَ عِبادِكَ فِي ما كانُوا فِيهِ يَخْتَلِفُونَ‌ بَيِّنْ لَنَا أَمْرَ هَذَا الْمَوْلُودِ حَتَّى يُوَرَّثَ مَا فَرَضْتَ لَهُ فِي كِتَابِكَ ثُمَّ يَطْرَحُ السَّهْمَيْنِ فِي سِهَامٍ مُبْهَمَةٍ ثُمَّ تُجَالُ فَأَيُّهُمَا خَرَجَ وُرِّثَ عَلَيْهِ.
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ جَمِيلٍ عَنْ فُضَيْلِ بْنِ يَسَارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ مَوْلُودٍ لَيْسَ لَهُ مَا لِلرِّجَالِ وَ لَيْسَ لَهُ مَا لِلنِّسَاءِ قَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | جمیل | عن |  |
  | 2 | named_narrator | فضیل بن یسار | عن |  |
  | 3 | imam | ابی عبد الله ع | عن |  |

### Chain 302 · `faqih-3392` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → جميل → فضيل بن يسار → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ جَمِيلٍ عَنْ فُضَيْلِ بْنِ يَسَارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ مَوْلُودٍ لَيْسَ لَهُ مَا لِلرِّجَالِ وَ لَيْسَ"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 303 · `faqih-3396`
- **Location:** vol. 3, p. 96 · seq 3408 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنِ الْحُسَيْنِ بْنِ خَالِدٍ[2] قَالَ‌ قُلْتُ لِأَبِي الْحَسَنِ ع جُعِلْتُ فِدَاكَ قَوْلُ النَّاسِ الضَّامِنُ غَارِمٌ فَقَالَ لَيْسَ عَلَى الضَّامِنِ غُرْمٌ إِنَّمَا الْغُرْمُ عَلَى مَنْ أَكَلَ الْمَالَ‌[3].
- **Isnad as currently extracted:**
  > رُوِيَ عَنِ الْحُسَيْنِ بْنِ خَالِدٍ[2] قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن الحسین بن خالد | روی |  |

### Chain 303 · `faqih-3396` — CLARIFIED
- Transmitters (student → teacher): الحسين بن خالد → ابي الحسن ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنِ الْحُسَيْنِ بْنِ خَالِدٍ[2] قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي الْحَسَنِ ع جُعِلْتُ فِدَاكَ قَوْلُ النَّاسِ الضَّامِنُ"
- Mursal opening: al-Ṣadūq → الحسين بن خالد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 304 · `faqih-3397`
- **Location:** vol. 3, p. 96 · seq 3409 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى دَاوُدُ بْنُ الْحُصَيْنِ عَنْ أَبِي الْعَبَّاسِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنِ الرَّجُلِ يَتَكَفَّلُ بِنَفْسِ الرَّجُلِ إِلَى أَجَلٍ فَإِنْ لَمْ يَأْتِ بِهِ فَعَلَيْهِ كَذَا وَ كَذَا دِرْهَماً قَالَ إِنْ جَاءَ بِهِ إِلَى الْأَجَلِ فَلَيْسَ عَلَيْهِ مَا قَالَ وَ هُوَ كَفِيلٌ بِنَفْسِهِ أَبَداً إِلَّا أَنْ يَبْدَأَ بِالدَّرَاهِمِ فَإِنْ بَدَأَ بِالدَّرَاهِمِ فَهُوَ لَهَا ضَامِنٌ إِنْ لَمْ يَأْتِ بِهِ إِلَى الْأَجَلِ الَّذِي أَجَّلَهُ‌[4].
- **Isnad as currently extracted:**
  > رَوَى دَاوُدُ بْنُ الْحُصَيْنِ عَنْ أَبِي الْعَبَّاسِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنِ الرَّجُلِ يَتَكَفَّلُ بِنَفْسِ الرَّجُلِ إِلَى أَجَلٍ فَإِنْ لَمْ يَأْتِ بِهِ فَعَلَيْهِ كَذَا وَ كَذَا دِرْهَماً قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | داود بن الحصین | روی |  |
  | 1 | named_narrator | ابی العباس | عن |  |
  | 2 | imam | ابی عبد الله ع | عن |  |

### Chain 304 · `faqih-3397` — CLARIFIED
- Transmitters (student → teacher): داود بن الحصين → ابي العباس → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى دَاوُدُ بْنُ الْحُصَيْنِ عَنْ أَبِي الْعَبَّاسِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الرَّجُلِ يَتَكَفَّلُ بِنَفْسِ الرَّجُلِ إِلَى أَجَلٍ فَإِنْ"
- Mursal opening: al-Ṣadūq → داود بن الحصين; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 305 · `faqih-3403`
- **Location:** vol. 3, p. 99 · seq 3415 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى الْبَزَنْطِيُّ عَنْ دَاوُدَ بْنِ سِرْحَانَ‌[1] قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ كَانَتْ لَهُ عِنْدَ رَجُلٍ دَنَانِيرُ فَأَحَالَ لَهُ عَلَى رَجُلٍ آخَرَ بِدَنَانِيرِهِ فَيَأْخُذُ بِهَا دَرَاهِمَ أَ يَجُوزُ ذَلِكَ قَالَ نَعَمْ.
- **Isnad as currently extracted:**
  > رَوَى الْبَزَنْطِيُّ عَنْ دَاوُدَ بْنِ سِرْحَانَ‌[1] قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | البزنطی | روی |  |
  | 1 | named_narrator | داود بن سرحان | عن |  |

### Chain 305 · `faqih-3403` — CLARIFIED
- Transmitters (student → teacher): البزنطي → داود بن سرحان → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى الْبَزَنْطِيُّ عَنْ دَاوُدَ بْنِ سِرْحَانَ‌[1] قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ كَانَتْ لَهُ"
- Mursal opening: al-Ṣadūq → البزنطي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 306 · `faqih-3409`
- **Location:** vol. 3, p. 101 · seq 3421 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى الْوَشَّاءُ عَنْ أَحْمَدَ بْنِ عُمَرَ الْحَلَبِيِّ قَالَ‌ سَأَلْتُ أَبَا الْحَسَنِ ع عَنْ قَوْلِ اللَّهِ عَزَّ وَ جَلَّ- وَ داوُدَ وَ سُلَيْمانَ إِذْ يَحْكُمانِ فِي الْحَرْثِ‌ قَالَ كَانَ حُكْمُ دَاوُدَ ع رِقَابَ الْغَنَمِ وَ الَّذِي فَهَّمَ اللَّهُ عَزَّ وَ جَلَّ سُلَيْمَانَ ع أَنْ حَكَمَ لِصَاحِبِ الْحَرْثِ بِاللَّبَنِ وَ الصُّوفِ ذَلِكَ الْعَامَ كُلَّهُ‌[2].
- **Isnad as currently extracted:**
  > رَوَى الْوَشَّاءُ عَنْ أَحْمَدَ بْنِ عُمَرَ الْحَلَبِيِّ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الوشاء | روی |  |
  | 1 | named_narrator | احمد بن عمر الحلبی | عن |  |

### Chain 306 · `faqih-3409` — CLARIFIED
- Transmitters (student → teacher): الوشاء → احمد بن عمر الحلبي
- Corrected isnad (Arabic): «رَوَى الْوَشَّاءُ عَنْ أَحْمَدَ بْنِ عُمَرَ الْحَلَبِيِّ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا الْحَسَنِ ع عَنْ قَوْلِ اللَّهِ عَزَّ وَ"
- Mursal opening: al-Ṣadūq → الوشاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 307 · `faqih-3414`
- **Location:** vol. 3, p. 102 · seq 3426 · chain 1
- **Flags:** `mursal_opening`, `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > رَوَى عُقْبَةُ بْنُ خَالِدٍ عَنْ أَبِي عَبْدِ اللَّهِ ع‌ فِي رَجُلٍ أَتَى جَبَلًا فَشَقَّ مِنْهُ قَنَاةً جَرَى مَاؤُهَا سَنَةً ثُمَّ إِنَّ رَجُلًا أَتَى ذَلِكَ الْجَبَلَ فَشَقَّ مِنْهُ قَنَاةً أُخْرَى فَذَهَبَتْ قَنَاةُ الْآخَرِ بِمَاءِ قَنَاةِ الْأَوَّلِ قَالَ يُقَايَسَانِ بِحَقَائِبِ الْبِئْرِ لَيْلَةً لَيْلَةً فَيُنْظَرُ أَيَّتُهَا أَضَرَّتْ بِصَاحِبَتِهَا فَإِنْ كَانَتِ الْأَخِيرَةُ أَضَرَّتْ بِالْأُولَى فَلْيَتَعَوَّرْ[2] وَ قَضَى رَسُولُ اللَّهِ ص بِذَلِكَ وَ قَالَ إِنْ كَانَتِ الْأُولَى أَخَذَتْ مَاءَ الْأَخِيرَةِ لَمْ يَكُنْ لِصَاحِبِ الْأَخِيرَةِ عَلَى الْأُولَى سَبِيلٌ.
- **Isnad as currently extracted:**
  > رَوَى عُقْبَةُ بْنُ خَالِدٍ عَنْ أَبِي عَبْدِ اللَّهِ ع‌ فِي رَجُلٍ أَتَى جَبَلًا فَشَقَّ مِنْهُ قَنَاةً جَرَى مَاؤُهَا سَنَةً ثُمَّ إِنَّ رَجُلًا أَتَى ذَلِكَ الْجَبَلَ فَشَقَّ مِنْهُ قَنَاةً أُخْرَى فَذَهَبَتْ قَنَاةُ الْآخَرِ بِمَاءِ قَنَاةِ الْأَوَّلِ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عقبة بن خالد | روی |  |
  | 1 | named_narrator | ابی عبد الله ع فی رجل اتی جبلا فشق منه قناة جری ماؤها سنة ثم ان رجلا اتی ذلک الجبل فشق منه قناة اخری فذهبت قناة الاخر بماء قناة الاول | عن |  |

### Chain 307 · `faqih-3414` — CLARIFIED
- Transmitters (student → teacher): عقبة بن خالد → أبو عبد الله ع
- Corrected isnad (Arabic): «رَوَى عُقْبَةُ بْنُ خَالِدٍ عَنْ أَبِي عَبْدِ اللَّهِ ع‌»
- Isnad ends / matn begins at: "فِي رَجُلٍ أَتَى جَبَلًا فَشَقَّ مِنْهُ قَنَاةً جَرَى مَاؤُهَا"
- Mursal opening: al-Ṣadūq → عقبة بن خالد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name.

---

### Chain 308 · `faqih-3418`
- **Location:** vol. 3, p. 105 · seq 3430 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى مُحَمَّدُ بْنُ عَلِيٍّ الْحَلَبِيُّ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ لَهُ مَنِ الَّذِي أُجْبَرُ عَلَى نَفَقَتِهِ قَالَ الْوَالِدَانِ وَ الْوَلَدُ وَ الزَّوْجَةُ[1] وَ الْوَارِثُ الصَّغِيرُ يَعْنِي الْأَخَ وَ ابْنَ الْأَخِ وَ غَيْرَهُ‌[2].
- **Isnad as currently extracted:**
  > رَوَى مُحَمَّدُ بْنُ عَلِيٍّ الْحَلَبِيُّ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن علی الحلبی | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 308 · `faqih-3418` — CLARIFIED
- Transmitters (student → teacher): محمد بن علي الحلبي → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى مُحَمَّدُ بْنُ عَلِيٍّ الْحَلَبِيُّ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ مَنِ الَّذِي أُجْبَرُ عَلَى نَفَقَتِهِ قَالَ الْوَالِدَانِ"
- Mursal opening: al-Ṣadūq → محمد بن علي الحلبي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 309 · `faqih-3423`
- **Location:** vol. 3, p. 110 · seq 3435 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى مُحَمَّدُ بْنُ عِيسَى بْنِ عُبَيْدٍ عَنْ أَخِيهِ جَعْفَرِ بْنِ عِيسَى قَالَ‌ كَتَبْتُ إِلَى أَبِي الْحَسَنِ ع جُعِلْتُ فِدَاكَ الْمَرْأَةُ تَمُوتُ فَيَدَّعِي أَبُوهَا أَنَّهُ أَعَارَهَا بَعْضَ مَا كَانَ عِنْدَهَا مِنَ الْمَتَاعِ وَ الْخَدَمِ أَ تُقْبَلُ دَعْوَاهُ بِلَا بَيِّنَةٍ أَمْ لَا تُقْبَلُ دَعْوَاهُ إِلَّا بِبَيِّنَةٍ فَكَتَبَ ع تَجُوزُ بِلَا بَيِّنَةٍ قَالَ وَ كَتَبْتُ إِلَى أَبِي الْحَسَنِ يَعْنِي عَلِيَّ بْنَ مُحَمَّدٍ ع جُعِلْتُ فِدَاكَ إِنِ ادَّعَى زَوْجُ الْمَرْأَةِ الْمَيِّتَةِ أَوْ أَبُو زَوْجِهَا أَوْ أُمُّ زَوْجِهَا فِي مَتَاعِهَا أَوْ فِي خَدَمِهَا مِثْلَ الَّذِي ادَّعَى أَبُوهَا مِنْ عَارِيَّةِ بَعْضِ الْمَتَاعِ وَ الْخَدَمِ أَ يَكُونُ بِمَنْزِلَةِ الْأَبِ‌
- **Isnad as currently extracted:**
  > رَوَى مُحَمَّدُ بْنُ عِيسَى بْنِ عُبَيْدٍ عَنْ أَخِيهِ جَعْفَرِ بْنِ عِيسَى قَالَ‌ كَتَبْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن عیسی بن عبید | روی |  |
  | 1 | named_narrator | اخیه جعفر بن عیسی | عن |  |

### Chain 309 · `faqih-3423` — CLARIFIED
- Transmitters (student → teacher): محمد بن عيسي بن عبيد → اخيه جعفر بن عيسي
- Corrected isnad (Arabic): «رَوَى مُحَمَّدُ بْنُ عِيسَى بْنِ عُبَيْدٍ عَنْ أَخِيهِ جَعْفَرِ بْنِ عِيسَى قَالَ‌»
- Isnad ends / matn begins at: "كَتَبْتُ إِلَى أَبِي الْحَسَنِ ع جُعِلْتُ فِدَاكَ الْمَرْأَةُ تَمُوتُ"
- Mursal opening: al-Ṣadūq → محمد بن عيسي بن عبيد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 310 · `faqih-3426`
- **Location:** vol. 3, p. 112 · seq 3438 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى عَلِيُّ بْنُ عَبْدِ اللَّهِ الْوَرَّاقُ رَحِمَهُ اللَّهُ عَنْ سَعْدِ بْنِ عَبْدِ اللَّهِ عَنْ أَحْمَدَ بْنِ مُحَمَّدِ بْنِ عِيسَى عَنْ مُحَمَّدِ بْنِ أَبِي عُمَيْرٍ عَنْ حَمَّادٍ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الْأَخْرَسِ كَيْفَ يَحْلِفُ إِذَا ادُّعِيَ عَلَيْهِ دَيْنٌ وَ لَمْ يَكُنْ لِلْمُدَّعِي بَيِّنَةٌ فَقَالَ إِنَّ أَمِيرَ الْمُؤْمِنِينَ ع أُتِيَ بِأَخْرَسَ وَ ادُّعِيَ عَلَيْهِ دَيْنٌ فَأَنْكَرَهُ وَ لَمْ يَكُنْ لِلْمُدَّعِي عَلَيْهِ بَيِّنَةٌ فَقَالَ أَمِيرُ الْمُؤْمِنِينَ ع الْحَمْدُ لِلَّهِ الَّذِي لَمْ يُخْرِجْنِي مِنَ الدُّنْيَا حَتَّى بَيَّنْتُ لِلْأُمَّةِ جَمِيعَ مَا يَحْتَاجُ إِلَيْهِ ثُمَّ قَالَ ائْتُونِي بِمُصْحَفٍ فَأُتِيَ بِهِ فَقَالَ لِلْأَخْرَسِ مَا هَذَا فَرَفَعَ رَأْسَهُ إِلَى السَّمَاءِ وَ أَشَارَ أَنَّهُ كِتَابُ اللَّهِ ثُمَّ قَالَ ائْتُونِي بِوَلِيِّهِ فَأَتَوْهُ بِأَخٍ لَهُ فَأَقْعَدَهُ إِلَى جَنْبِهِ ثُمَّ قَالَ يَا قَنْبَرُ عَلَيَّ بِدَوَاةٍ وَ صِينِيَّةٍ فَأَتَاهُ بِهِمَا[1] ثُمَّ قَالَ لِأَخِ الْأَخْرَسِ قُلْ لِأَخِيكَ هَذَا بَيْنَكَ وَ بَيْنَهُ إِنَّهُ عَلِيٌّ فَتَقَدَّمَ إِلَيْهِ بِذَلِكَ ثُمَّ كَتَبَ أَمِيرُ الْمُؤْمِنِينَ ع وَ اللَّهِ‌ الَّذِي لا إِلهَ إِلَّا هُوَ عالِمُ الْغَيْبِ وَ الشَّهادَةِ- .. الرَّحْمنُ الرَّحِيمُ‌ الطَّالِبُ الْغَالِبُ الضَّارُّ النَّافِعُ الْمُهْلِكُ الْمُدْرِكُ الَّذِي يَعْلَمُ السِّرَّ وَ الْعَلَانِيَةَ إِنَّ فُلَانَ بْنَ فُلَانٍ الْمُدَّعِيَ لَيْسَ لَهُ قِبَلَ فُلَانِ بْنِ فُلَانٍ أَعْنِي الْأَخْرَسَ حَقٌّ وَ لَا طِلْبَةٌ بِوَجْهٍ مِنَ‌
الْوُجُوهِ وَ لَا سَبَبٍ مِنَ الْأَسْبَابِ ثُمَّ غَسَلَهُ وَ أَمَرَ الْأَخْرَسَ أَنْ يَشْرَبَهُ فَامْتَنَعَ فَأَلْزَمَهُ الدَّيْنَ‌[1].
- **Isnad as currently extracted:**
  > رَوَى عَلِيُّ بْنُ عَبْدِ اللَّهِ الْوَرَّاقُ رَحِمَهُ اللَّهُ عَنْ سَعْدِ بْنِ عَبْدِ اللَّهِ عَنْ أَحْمَدَ بْنِ مُحَمَّدِ بْنِ عِيسَى عَنْ مُحَمَّدِ بْنِ أَبِي عُمَيْرٍ عَنْ حَمَّادٍ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُ
- **Current node split (6 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن عبد الله الوراق | روی |  |
  | 1 | named_narrator | سعد بن عبد الله | عن |  |
  | 2 | named_narrator | احمد بن محمد بن عیسی | عن |  |
  | 3 | named_narrator | محمد بن ابی عمیر | عن |  |
  | 4 | named_narrator | حماد | عن |  |
  | 5 | named_narrator | محمد بن مسلم | عن |  |

### Chain 310 · `faqih-3426` — CLARIFIED
- Transmitters (student → teacher): علي بن عبد الله الوراق → سعد بن عبد الله → احمد بن محمد بن عيسي → محمد بن ابي عمير → حماد → محمد بن مسلم
- Corrected isnad (Arabic): «رَوَى عَلِيُّ بْنُ عَبْدِ اللَّهِ الْوَرَّاقُ رَحِمَهُ اللَّهُ عَنْ سَعْدِ بْنِ عَبْدِ اللَّهِ عَنْ أَحْمَدَ بْنِ مُحَمَّدِ بْنِ عِيسَى عَنْ مُحَمَّدِ بْنِ أَبِي عُمَيْرٍ عَنْ حَمَّادٍ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الْأَخْرَسِ كَيْفَ يَحْلِفُ"
- Mursal opening: al-Ṣadūq → علي بن عبد الله الوراق; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 311 · `faqih-3434`
- **Location:** vol. 3, p. 115 · seq 3446 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ وَرِثَ غُلَاماً وَ لَهُ فِيهِ شُرَكَاءُ فَأَعْتَقَ لِوَجْهِ اللَّهِ نَصِيبَهُ فَقَالَ إِذَا أَعْتَقَ نَصِيبَهُ مُضَارَّةً وَ هُوَ مُوسِرٌ ضَمِنَ لِلْوَرَثَةِ وَ إِذَا أَعْتَقَ نَصِيبَهُ لِوَجْهِ اللَّهِ عَزَّ وَ جَلَّ كَانَ الْغُلَامُ قَدْ أُعْتِقَ مِنْهُ حِصَّةُ مَنْ أَعْتَقَ وَ يَسْتَعْمِلُونَهُ عَلَى قَدْرِ مَا لَهُمْ فِيهِ فَإِنْ كَانَ فِيهِ نِصْفُهُ عَمِلَ لَهُمْ يَوْماً وَ لَهُ يَوْمٌ وَ إِنْ أَعْتَقَ الشَّرِيكُ مُضَارّاً فَلَا عِتْقَ لَهُ لِأَنَّهُ أَرَادَ أَنْ يُفْسِدَ عَلَى الْقَوْمِ وَ يَرْجِعُ الْقَوْمُ عَلَى حِصَّتِهِمْ.
- **Isnad as currently extracted:**
  > رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حریز | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |

### Chain 311 · `faqih-3434` — CLARIFIED
- Transmitters (student → teacher): حريز → محمد بن مسلم → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ وَرِثَ غُلَاماً وَ"
- Mursal opening: al-Ṣadūq → حريز; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 312 · `faqih-3436`
- **Location:** vol. 3, p. 115 · seq 3448 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنِ الرَّجُلِ تَكُونُ لَهُ الْأَمَةُ فَيَقُولُ مَتَى آتِيهَا فَهِيَ حُرَّةٌ ثُمَّ يَبِيعُهَا مِنْ رَجُلٍ ثُمَّ يَشْتَرِيهَا بَعْدَ ذَلِكَ قَالَ لَا بَأْسَ بِأَنْ يَأْتِيَهَا قَدْ خَرَجَتْ مِنْ مِلْكِهِ.
- **Isnad as currently extracted:**
  > رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنِ الرَّجُلِ تَكُونُ لَهُ الْأَمَةُ فَيَقُولُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | العلاء | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |
  | 2 | imam | احدهما ع | عن | ambiguous |

### Chain 312 · `faqih-3436` — CLARIFIED
- Transmitters (student → teacher): العلاء → محمد بن مسلم → احدهما ع
- Corrected isnad (Arabic): «رَوَى الْعَلَاءُ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الرَّجُلِ تَكُونُ لَهُ الْأَمَةُ فَيَقُولُ مَتَى آتِيهَا"
- Mursal opening: al-Ṣadūq → العلاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 313 · `faqih-3437`
- **Location:** vol. 3, p. 115 · seq 3449 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ سَمَاعَةَ قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ قَالَ لِثَلَاثَةِ مَمَالِيكَ لَهُ أَنْتُمْ أَحْرَارٌ وَ كَانَ لَهُ أَرْبَعَةٌ فَقَالَ لَهُ رَجُلٌ مِنَ النَّاسِ أَعْتَقْتَ مَمَالِيكَكَ قَالَ نَعَمْ أَ يَجِبُ‌
عِتْقُ الْأَرْبَعَةِ حِينَ أَجْمَلَهُمْ أَوْ هُوَ لِلثَّلَاثَةِ الَّذِينَ أَعْتَقَ قَالَ إِنَّمَا يَجِبُ الْعِتْقُ لِمَنْ أَعْتَقَ.
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ سَمَاعَةَ قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ قَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن سماعة | روی |  |

### Chain 313 · `faqih-3437` — CLARIFIED
- Transmitters (student → teacher): سماعة → إمامٌ غير مصرّح باسمه في هذا الطريق (مضمرة سماعة)
- Corrected isnad (Arabic): «رُوِيَ عَنْ سَمَاعَةَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ قَالَ لِثَلَاثَةِ مَمَالِيكَ لَهُ أَنْتُمْ أَحْرَارٌ"
- Mursal opening: al-Ṣadūq → سماعة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The full al-Tahdhīb route reaches Samāʿa through al-Ḥusayn b. Saʿīd → al-Ḥasan → Zurʿa, but the final wording remains «سألته» without naming the Imam. It is therefore encoded as a muḍmar, not guessed. Source: [Wasāʾil al-Shīʿa, vol. 23, report 29258](https://ar.lib.eshia.ir/11025/23/94).
---

### Chain 314 · `faqih-3438`
- **Location:** vol. 3, p. 116 · seq 3450 · chain 1
- **Flags:** `mursal_opening`, `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > رَوَى حَمَّادٌ عَنِ الْحَلَبِيِّ عَنْ أَبِي عَبْدِ اللَّهِ ع‌ فِي رَجُلٍ زَوَّجَ أَمَتَهُ مِنْ رَجُلٍ وَ شَرَطَ لَهُ أَنَّ مَا وَلَدَتْ مِنْ وَلَدٍ فَهُوَ حُرٌّ فَطَلَّقَهَا زَوْجُهَا أَوْ مَاتَ عَنْهَا فَزَوَّجَهَا مِنْ رَجُلٍ آخَرَ مَا مَنْزِلَةُ وَلَدِهَا قَالَ بِمَنْزِلَتِهَا إِنَّمَا جَعَلَ ذَلِكَ لِلْأَوَّلِ‌[1] وَ هُوَ فِي الْآخَرِ بِالْخِيَارِ إِنْ شَاءَ أَعْتَقَ وَ إِنْ شَاءَ أَمْسَكَ.
- **Isnad as currently extracted:**
  > رَوَى حَمَّادٌ عَنِ الْحَلَبِيِّ عَنْ أَبِي عَبْدِ اللَّهِ ع‌ فِي رَجُلٍ زَوَّجَ أَمَتَهُ مِنْ رَجُلٍ وَ شَرَطَ لَهُ أَنَّ مَا وَلَدَتْ مِنْ وَلَدٍ فَهُوَ حُرٌّ فَطَلَّقَهَا زَوْجُهَا أَوْ مَاتَ عَنْهَا فَزَوَّجَهَا مِنْ رَجُلٍ آخَرَ مَا مَنْزِلَةُ وَلَدِهَا قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حماد | روی |  |
  | 1 | named_narrator | الحلبی | عن |  |
  | 2 | named_narrator | ابی عبد الله ع فی رجل زوج امته من رجل و شرط له ان ما ولدت من ولد فهو حر فطلقها زوجها او مات عنها فزوجها من رجل اخر ما منزلة ولدها | عن |  |

### Chain 314 · `faqih-3438` — CLARIFIED
- Transmitters (student → teacher): حماد → الحلبي → أبو عبد الله ع
- Corrected isnad (Arabic): «رَوَى حَمَّادٌ عَنِ الْحَلَبِيِّ عَنْ أَبِي عَبْدِ اللَّهِ ع‌»
- Isnad ends / matn begins at: "فِي رَجُلٍ زَوَّجَ أَمَتَهُ مِنْ رَجُلٍ وَ شَرَطَ لَهُ"
- Mursal opening: al-Ṣadūq → حماد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name.

---

### Chain 315 · `faqih-3447`
- **Location:** vol. 3, p. 119 · seq 3459 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى حَمَّادٌ عَنِ الْحَلَبِيِّ عَنْهُ ع أَنَّهُ قَالَ‌ فِي الرَّجُلِ يَقُولُ إِنْ مِتُّ فَعَبْدِي حُرٌّ وَ عَلَى الرَّجُلِ دَيْنٌ قَالَ إِنْ تُوُفِّيَ وَ عَلَيْهِ دَيْنٌ قَدْ أَحَاطَ بِثَمَنِ الْعَبْدِ بِيعَ الْعَبْدُ وَ إِنْ لَمْ يَكُنْ أَحَاطَ بِثَمَنِ الْعَبْدِ اسْتُسْعِيَ الْعَبْدُ فِي قَضَاءِ دَيْنِ مَوْلَاهُ وَ هُوَ حُرٌّ بِهِ إِذَا أَوْفَاهُ‌[1].
- **Isnad as currently extracted:**
  > رَوَى حَمَّادٌ عَنِ الْحَلَبِيِّ عَنْهُ ع أَنَّهُ قَالَ‌ فِي الرَّجُلِ يَقُولُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حماد | روی |  |
  | 1 | imam | الحلبی عنه ع | عن |  |

### Chain 315 · `faqih-3447` — CLARIFIED
- Transmitters (student → teacher): حماد → الحلبي عنه ع
- Corrected isnad (Arabic): «رَوَى حَمَّادٌ عَنِ الْحَلَبِيِّ عَنْهُ ع أَنَّهُ قَالَ‌»
- Isnad ends / matn begins at: "فِي الرَّجُلِ يَقُولُ إِنْ مِتُّ فَعَبْدِي حُرٌّ وَ عَلَى"
- Mursal opening: al-Ṣadūq → حماد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 316 · `faqih-3449`
- **Location:** vol. 3, p. 119 · seq 3461 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ تَرَكَ مَمْلُوكاً بَيْنَ نَفَرٍ فَشَهِدَ أَحَدُهُمْ أَنَّ الْمَيِّتَ أَعْتَقَهُ قَالَ إِنْ كَانَ الشَّاهِدُ مَرْضِيّاً لَمْ يَضْمَنْ وَ جَازَتْ شَهَادَتُهُ فِي نَصِيبِهِ وَ اسْتُسْعِيَ الْعَبْدُ فِيمَا كَانَ لِلْوَرَثَةِ[3].
- **Isnad as currently extracted:**
  > رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ تَرَكَ مَمْلُوكاً بَيْنَ نَفَرٍ فَشَهِدَ أَحَدُهُمْ أَنَّ الْمَيِّتَ أَعْتَقَهُ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حریز | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |
  | 2 | imam | احدهما ع | عن | ambiguous |

### Chain 316 · `faqih-3449` — CLARIFIED
- Transmitters (student → teacher): حريز → محمد بن مسلم → احدهما ع
- Corrected isnad (Arabic): «رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَحَدِهِمَا ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ تَرَكَ مَمْلُوكاً بَيْنَ نَفَرٍ فَشَهِدَ أَحَدُهُمْ"
- Mursal opening: al-Ṣadūq → حريز; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 317 · `faqih-3451`
- **Location:** vol. 3, p. 120 · seq 3463 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى جَمِيلٌ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنِ الْمُدَبَّرِ أَ يُبَاعُ قَالَ إِنِ احْتَاجَ صَاحِبُهُ إِلَى ثَمَنِهِ وَ رَضِيَ الْمَمْلُوكُ فَلَا بَأْسَ‌[3].
- **Isnad as currently extracted:**
  > رَوَى جَمِيلٌ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنِ الْمُدَبَّرِ أَ يُبَاعُ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | جمیل | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 317 · `faqih-3451` — CLARIFIED
- Transmitters (student → teacher): جميل → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى جَمِيلٌ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْمُدَبَّرِ أَ يُبَاعُ قَالَ إِنِ احْتَاجَ صَاحِبُهُ"
- Mursal opening: al-Ṣadūq → جميل; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 318 · `faqih-3457`
- **Location:** vol. 3, p. 122 · seq 3469 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى عَاصِمٌ‌[2] عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُهُ عَنِ الْعَبْدِ وَ الْأَمَةِ يُعْتَقَانِ عَنْ دُبُرٍ فَقَالَ لِمَوْلَاهُ أَنْ يُكَاتِبَهُ إِنْ شَاءَ[3] وَ لَيْسَ لَهُ أَنْ يَبِيعَهُ إِلَّا أَنْ يَشَاءَ الْعَبْدُ أَنْ يَبِيعَهُ مُدَّةَ حَيَاتِهِ‌[4] وَ لَهُ أَنْ يَأْخُذَ مَالَهُ إِنْ كَانَ لَهُ مَالٌ‌[5].
- **Isnad as currently extracted:**
  > رَوَى عَاصِمٌ‌[2] عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُهُ عَنِ الْعَبْدِ وَ الْأَمَةِ يُعْتَقَانِ عَنْ دُبُرٍ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عاصم | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |

### Chain 318 · `faqih-3457` — CLARIFIED
- Transmitters (student → teacher): عاصم → أبو بصير → أبو عبد الله ع
- Corrected isnad (Arabic): «رَوَى عَاصِمٌ‌[2] عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْعَبْدِ وَ الْأَمَةِ يُعْتَقَانِ عَنْ دُبُرٍ فَقَالَ"
- Mursal opening: al-Ṣadūq → عاصم; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The full parallel explicitly reads «عَاصِم، عَنْ أَبِي بَصِيرٍ قَالَ: سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع». Source: [Wasāʾil al-Shīʿa, vol. 23, p. 120](https://ar.lib.eshia.ir/11025/23/120). This and Chain 319 are duplicate tokenizer records of one report.
---

### Chain 319 · `faqih-3457`
- **Location:** vol. 3, p. 122 · seq 3469 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى عَاصِمٌ‌[2] عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُهُ عَنِ الْعَبْدِ وَ الْأَمَةِ يُعْتَقَانِ عَنْ دُبُرٍ فَقَالَ لِمَوْلَاهُ أَنْ يُكَاتِبَهُ إِنْ شَاءَ[3] وَ لَيْسَ لَهُ أَنْ يَبِيعَهُ إِلَّا أَنْ يَشَاءَ الْعَبْدُ أَنْ يَبِيعَهُ مُدَّةَ حَيَاتِهِ‌[4] وَ لَهُ أَنْ يَأْخُذَ مَالَهُ إِنْ كَانَ لَهُ مَالٌ‌[5].
- **Isnad as currently extracted:**
  > رَوَى عَاصِمٌ‌[2] عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُهُ عَنِ الْعَبْدِ وَ الْأَمَةِ يُعْتَقَانِ عَنْ دُبُرٍ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عاصم | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |

### Chain 319 · `faqih-3457` — CLARIFIED
- Transmitters (student → teacher): عاصم → أبو بصير → أبو عبد الله ع
- Corrected isnad (Arabic): «رَوَى عَاصِمٌ‌[2] عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْعَبْدِ وَ الْأَمَةِ يُعْتَقَانِ عَنْ دُبُرٍ فَقَالَ"
- Mursal opening: al-Ṣadūq → عاصم; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: Duplicate tokenizer record of Chain 318, not a second route. The parallel names Abū ʿAbd Allāh explicitly: [Wasāʾil al-Shīʿa, vol. 23, p. 120](https://ar.lib.eshia.ir/11025/23/120).
---

### Chain 320 · `faqih-3459`
- **Location:** vol. 3, p. 122 · seq 3471 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى أَبَانٌ عَنْ عَبْدِ الرَّحْمَنِ قَالَ‌ سَأَلْتُهُ عَنِ الرَّجُلِ قَالَ لِعَبْدِهِ-
إِنْ حَدَثَ بِي حَدَثٌ فَهُوَ حُرٌّ وَ عَلَى الرَّجُلِ تَحْرِيرُ رَقَبَةٍ فِي كَفَّارَةِ يَمِينٍ أَوْ ظِهَارٍ أَ لَهُ أَنْ يُعْتِقَ عَبْدَهُ الَّذِي جَعَلَ لَهُ الْعِتْقَ إِنْ حَدَثَ بِهِ حَدَثٌ فِي كَفَّارَةِ تِلْكَ الْيَمِينِ قَالَ لَا يَجُوزُ الَّذِي يَجْعَلُ لَهُ فِي ذَلِكَ‌[1].
- **Isnad as currently extracted:**
  > رَوَى أَبَانٌ عَنْ عَبْدِ الرَّحْمَنِ قَالَ‌ سَأَلْتُهُ عَنِ الرَّجُلِ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابان | روی |  |
  | 1 | named_narrator | عبد الرحمن | عن |  |

### Chain 320 · `faqih-3459` — CLARIFIED
- Transmitters (student → teacher): ابان → عبد الرحمن
- Corrected isnad (Arabic): «رَوَى أَبَانٌ عَنْ عَبْدِ الرَّحْمَنِ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الرَّجُلِ قَالَ لِعَبْدِهِ- إِنْ حَدَثَ بِي حَدَثٌ"
- Mursal opening: al-Ṣadūq → ابان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 321 · `faqih-3460`
- **Location:** vol. 3, p. 123 · seq 3472 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى وُهَيْبُ بْنُ حَفْصٍ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ دَبَّرَ غُلَامَهُ وَ عَلَيْهِ دَيْنٌ فِرَاراً مِنَ الدَّيْنِ قَالَ لَا تَدْبِيرَ لَهُ وَ إِنْ كَانَ دَبَّرَهُ فِي صِحَّةٍ مِنْهُ وَ سَلَامَةٍ فَلَا سَبِيلَ لِلدُّيَّانِ عَلَيْهِ‌[2].
- **Isnad as currently extracted:**
  > رَوَى وُهَيْبُ بْنُ حَفْصٍ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | وهیب بن حفص | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |

### Chain 321 · `faqih-3460` — CLARIFIED
- Transmitters (student → teacher): وهيب بن حفص → ابي بصير → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى وُهَيْبُ بْنُ حَفْصٍ عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ دَبَّرَ غُلَامَهُ"
- Mursal opening: al-Ṣadūq → وهيب بن حفص; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 322 · `faqih-3461`
- **Location:** vol. 3, p. 123 · seq 3473 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى ابْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ رِئَابٍ عَنْ بُرَيْدِ بْنِ مُعَاوِيَةَ قَالَ‌ سَأَلْتُ أَبَا جَعْفَرٍ ع عَنْ رَجُلٍ دَبَّرَ مَمْلُوكاً لَهُ تَاجِراً مُوسِراً[3] فَاشْتَرَى الْمُدَبَّرُ جَارِيَةً بِأَمْرِ مَوْلَاهُ فَوَلَدَتْ مِنْهُ أَوْلَاداً ثُمَّ إِنَّ الْمُدَبَّرَ مَاتَ قَبْلَ سَيِّدِهِ فَقَالَ أَرَى‌
- **Isnad as currently extracted:**
  > رَوَى ابْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ رِئَابٍ عَنْ بُرَيْدِ بْنِ مُعَاوِيَةَ قَالَ‌ سَأَلْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن محبوب | روی |  |
  | 1 | named_narrator | علی بن رئاب | عن |  |
  | 2 | named_narrator | برید بن معاویة | عن |  |

### Chain 322 · `faqih-3461` — CLARIFIED
- Transmitters (student → teacher): ابن محبوب → علي بن رئاب → بريد بن معاوية → ابا جعفر ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى ابْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ رِئَابٍ عَنْ بُرَيْدِ بْنِ مُعَاوِيَةَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا جَعْفَرٍ ع عَنْ رَجُلٍ دَبَّرَ مَمْلُوكاً لَهُ"
- Mursal opening: al-Ṣadūq → ابن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 323 · `faqih-3464`
- **Location:** vol. 3, p. 125 · seq 3476 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى عَمْرُو بْنُ شِمْرٍ عَنْ جَابِرٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنِ الْمُكَاتَبِ يُشْتَرَطُ عَلَيْهِ إِنْ عَجَزَ فَهُوَ رَدٌّ فِي الرِّقِّ فَعَجَزَ قَبْلَ أَنْ يُؤَدِّيَ شَيْئاً قَالَ لَا يُرَدُّ فِي الرِّقِّ حَتَّى يَمْضِيَ لَهُ ثَلَاثُ سِنِينَ‌[1] وَ يُعْتَقُ مِنْهُ مِقْدَارُ مَا أَدَّى صَدْراً[2] فَإِذَا أَدَّى صَدْراً فَلَيْسَ لَهُمْ أَنْ يَرُدُّوهُ فِي الرِّقِّ.
- **Isnad as currently extracted:**
  > رَوَى عَمْرُو بْنُ شِمْرٍ عَنْ جَابِرٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنِ الْمُكَاتَبِ يُشْتَرَطُ عَلَيْهِ إِنْ عَجَزَ فَهُوَ رَدٌّ فِي الرِّقِّ فَعَجَزَ قَبْلَ أَنْ يُؤَدِّيَ شَيْئاً قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عمرو بن شمر | روی |  |
  | 1 | named_narrator | جابر | عن |  |
  | 2 | imam | ابی جعفر ع | عن |  |

### Chain 323 · `faqih-3464` — CLARIFIED
- Transmitters (student → teacher): عمرو بن شمر → جابر → ابي جعفر ع
- Corrected isnad (Arabic): «رَوَى عَمْرُو بْنُ شِمْرٍ عَنْ جَابِرٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْمُكَاتَبِ يُشْتَرَطُ عَلَيْهِ إِنْ عَجَزَ فَهُوَ رَدٌّ"
- Mursal opening: al-Ṣadūq → عمرو بن شمر; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 324 · `faqih-3468`
- **Location:** vol. 3, p. 126 · seq 3480 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى ابْنُ مَحْبُوبٍ عَنْ عُمَرَ بْنِ يَزِيدَ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ أَرَادَ أَنْ يُعْتِقَ مَمْلُوكاً لَهُ وَ قَدْ كَانَ مَوْلَاهُ يَأْخُذُ مِنْهُ ضَرِيبَةً فَرَضَهَا عَلَيْهِ‌[4] فِي كُلِّ سَنَةٍ وَ رَضِيَ بِذَلِكَ مِنْهُ الْمَوْلَى فَأَصَابَ الْمَمْلُوكُ فِي تِجَارَتِهِ مَالًا سِوَى مَا كَانَ يُعْطِي مَوْلَاهُ مِنَ الضَّرِيبَةِ فَقَالَ إِذَا أَدَّى إِلَى سَيِّدِهِ مَا كَانَ فَرَضَ عَلَيْهِ فَمَا اكْتَسَبَ بَعْدَ الْفَرِيضَةِ فَهُوَ لِلْمَمْلُوكِ قَالَ ثُمَّ قَالَ أَبُو عَبْدِ اللَّهِ ع أَ لَيْسَ قَدْ فَرَضَ اللَّهُ عَزَّ وَ جَلَّ عَلَى الْعِبَادِ فَرَائِضَ فَإِذَا أَدَّوْهَا إِلَيْهِ لَمْ يَسْأَلْهُمْ عَمَّا سِوَاهَا قُلْتُ لَهُ فَلِلْمَمْلُوكِ أَنْ يَتَصَدَّقَ مِمَّا اكْتَسَبَ وَ يُعْتَقُ بَعْدَ الْفَرِيضَةِ الَّتِي يُؤَدِّيهَا إِلَى سَيِّدِهِ قَالَ نَعَمْ‌[5] وَ أَجْرُ
ذَلِكَ لَهُ قُلْتُ فَإِنْ أَعْتَقَ مَمْلُوكاً مِمَّا كَانَ اكْتَسَبَ سِوَى الْفَرِيضَةِ[1] لِمَنْ يَكُونُ وَلَاءُ الْمُعْتَقِ فَقَالَ يَذْهَبُ فَيَتَوَلَّى إِلَى مَنْ أَحَبَّ فَإِذَا ضَمِنَ جَرِيرَتَهُ وَ عَقْلَهُ‌[2] كَانَ مَوْلَاهُ وَ وَرِثَهُ قُلْتُ لَهُ أَ لَيْسَ قَالَ رَسُولُ اللَّهِ ص الْوَلَاءُ لِمَنْ أَعْتَقَ فَقَالَ هَذَا سَائِبَةٌ[3] لَا يَكُونُ وَلَاؤُهُ لِعَبْدٍ مِثْلِهِ قُلْتُ فَإِنْ ضَمِنَ الْعَبْدُ الَّذِي أَعْتَقَهُ جَرِيرَتَهُ وَ حَدَثَهُ يَلْزَمُهُ ذَلِكَ وَ يَكُونُ مَوْلَاهُ وَ يَرِثُهُ فَقَالَ لَا يَجُوزُ ذَلِكَ لَا يَرِثُ عَبْدٌ حُرّاً.
- **Isnad as currently extracted:**
  > رَوَى ابْنُ مَحْبُوبٍ عَنْ عُمَرَ بْنِ يَزِيدَ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن محبوب | روی |  |
  | 1 | named_narrator | عمر بن یزید | عن |  |

### Chain 324 · `faqih-3468` — CLARIFIED
- Transmitters (student → teacher): ابن محبوب → عمر بن يزيد → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى ابْنُ مَحْبُوبٍ عَنْ عُمَرَ بْنِ يَزِيدَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ أَرَادَ أَنْ"
- Mursal opening: al-Ṣadūq → ابن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 325 · `faqih-3469`
- **Location:** vol. 3, p. 127 · seq 3481 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى أَبَانٌ عَنْ أَبِي الْعَبَّاسِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ قَالَ غُلَامِي حُرٌّ وَ عَلَيْهِ عُمَالَةُ[4] كَذَا وَ كَذَا سَنَةً قَالَ هُوَ حُرٌّ وَ عَلَيْهِ الْعُمَالَةُ قُلْتُ إِنَّ ابْنَ أَبِي لَيْلَى يَزْعُمُ أَنَّهُ حُرٌّ وَ لَيْسَ عَلَيْهِ شَيْ‌ءٌ قَالَ كَذَبَ إِنَّ عَلِيّاً ع أَعْتَقَ- أَبَا نَيْزَرَ وَ عِيَاضاً وَ رِيَاحاً[5] وَ عَلَيْهِمْ عُمَالَةُ كَذَا وَ كَذَا سَنَةً وَ لَهُمْ رِزْقُهُمْ وَ كِسْوَتُهُمْ بِالْمَعْرُوفِ فِي تِلْكَ السِّنِينَ‌[6].
- **Isnad as currently extracted:**
  > رَوَى أَبَانٌ عَنْ أَبِي الْعَبَّاسِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابان | روی |  |
  | 1 | named_narrator | ابی العباس | عن |  |
  | 2 | imam | ابی عبد الله ع | عن |  |

### Chain 325 · `faqih-3469` — CLARIFIED
- Transmitters (student → teacher): ابان → ابي العباس → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى أَبَانٌ عَنْ أَبِي الْعَبَّاسِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ قَالَ غُلَامِي حُرٌّ وَ عَلَيْهِ عُمَالَةُ[4]"
- Mursal opening: al-Ṣadūq → ابان; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 326 · `faqih-3478`
- **Location:** vol. 3, p. 130 · seq 3490 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى مُعَاوِيَةُ بْنُ وَهْبٍ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌ فِي مَمْلُوكٍ كَاتَبَ عَلَى نَفْسِهِ وَ مَالِهِ‌[2] وَ لَهُ أَمَةٌ وَ قَدْ شُرِطَ عَلَيْهِ أَنْ لَا يَتَزَوَّجَ فَأَعْتَقَ الْأَمَةَ وَ تَزَوَّجَهَا قَالَ لَا يَصْلُحُ لَهُ أَنْ يُحْدِثَ فِي مَالِهِ إِلَّا الْأَكْلَةَ مِنَ الطَّعَامِ وَ نِكَاحُهُ فَاسِدٌ مَرْدُودٌ قِيلَ فَإِنَّ سَيِّدَهُ عَلِمَ بِنِكَاحِهِ وَ لَمْ يَقُلْ شَيْئاً قَالَ إِذَا صَمَتَ حِينَ يَعْلَمُ ذَلِكَ فَقَدْ أَقَرَّ[3] قِيلَ فَإِنْ كَانَ الْمُكَاتَبُ أُعْتِقَ أَ فَتَرَى أَنْ يُجَدِّدَ نِكَاحَهُ أَوْ يَمْضِيَ عَلَى النِّكَاحِ الْأَوَّلِ قَالَ يَمْضِي عَلَى نِكَاحِهِ‌[4].
- **Isnad as currently extracted:**
  > رَوَى مُعَاوِيَةُ بْنُ وَهْبٍ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌ فِي مَمْلُوكٍ كَاتَبَ عَلَى نَفْسِهِ وَ مَالِهِ‌[2] وَ لَهُ أَمَةٌ وَ قَدْ شُرِطَ عَلَيْهِ أَنْ لَا يَتَزَوَّجَ فَأَعْتَقَ الْأَمَةَ وَ تَزَوَّجَهَا قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن وهب | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 326 · `faqih-3478` — CLARIFIED
- Transmitters (student → teacher): معاوية بن وهب → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى مُعَاوِيَةُ بْنُ وَهْبٍ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ‌»
- Isnad ends / matn begins at: "فِي مَمْلُوكٍ كَاتَبَ عَلَى نَفْسِهِ وَ مَالِهِ‌[2] وَ لَهُ"
- Mursal opening: al-Ṣadūq → معاوية بن وهب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 327 · `faqih-3481`
- **Location:** vol. 3, p. 131 · seq 3493 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى جَمِيلُ بْنُ دَرَّاجٍ عَنْ مِهْزَمٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الْمُكَاتَبِ يَمُوتُ وَ لَهُ وُلْدٌ فَقَالَ إِنْ كَانَ اشْتُرِطَ عَلَيْهِ‌[1] فَوُلْدُهُ مَمَالِيكُ وَ إِنْ لَمْ يَكُنِ اشْتُرِطَ عَلَيْهِ سَعَى وُلْدُهُ فِي مُكَاتَبَةِ أَبِيهِمْ وَ عَتَقُوا إِذَا أَدَّوْا.
- **Isnad as currently extracted:**
  > رَوَى جَمِيلُ بْنُ دَرَّاجٍ عَنْ مِهْزَمٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | جمیل بن دراج | روی |  |
  | 1 | named_narrator | مهزم | عن |  |

### Chain 327 · `faqih-3481` — CLARIFIED
- Transmitters (student → teacher): جميل بن دراج → مهزم → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى جَمِيلُ بْنُ دَرَّاجٍ عَنْ مِهْزَمٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الْمُكَاتَبِ يَمُوتُ وَ"
- Mursal opening: al-Ṣadūq → جميل بن دراج; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 328 · `faqih-3482`
- **Location:** vol. 3, p. 131 · seq 3494 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى مُحَمَّدُ بْنُ قَيْسٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ إِنِ اشْتَرَطَ الْمَمْلُوكُ الْمُكَاتَبُ عَلَى مَوْلَاهُ أَنَّهُ لَا وَلَاءَ لِأَحَدٍ عَلَيْهِ‌[2] أَوِ اشْتَرَطَ السَّيِّدُ وَلَاءَ الْمُكَاتَبِ فَأَقَرَّ الْمُكَاتَبُ الَّذِي كُوتِبَ فَلَهُ وَلَاؤُهُ‌[3] قَالَ وَ قَضَى أَمِيرُ الْمُؤْمِنِينَ ع فِي مُكَاتَبٍ اشْتُرِطَ عَلَيْهِ وَلَاؤُهُ إِذَا أُعْتِقَ فَنَكَحَ وَلِيدَةً لِرَجُلٍ آخَرَ فَوَلَدَتْ لَهُ وَلَداً فَحُرِّرَ وَلَدُهُ‌[4] ثُمَّ تُوُفِّيَ الْمُكَاتَبُ فَوَرِثَهُ وَلَدُهُ فَاخْتَلَفُوا فِي وَلَدِهِ مَنْ يَرِثُهُ فَأَلْحَقَ وَلَدَهُ‌
- **Isnad as currently extracted:**
  > رَوَى مُحَمَّدُ بْنُ قَيْسٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ إِنِ اشْتَرَطَ الْمَمْلُوكُ الْمُكَاتَبُ عَلَى مَوْلَاهُ أَنَّهُ لَا وَلَاءَ لِأَحَدٍ عَلَيْهِ‌[2] أَوِ اشْتَرَطَ السَّيِّدُ وَلَاءَ الْمُكَاتَبِ فَأَقَرَّ الْمُكَاتَبُ الَّذِي كُوتِبَ فَلَهُ وَلَاؤُهُ‌[3] قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن قیس | روی |  |
  | 1 | imam | ابی جعفر ع | عن |  |

### Chain 328 · `faqih-3482` — CLARIFIED
- Transmitters (student → teacher): محمد بن قيس → ابي جعفر ع
- Corrected isnad (Arabic): «رَوَى مُحَمَّدُ بْنُ قَيْسٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "إِنِ اشْتَرَطَ الْمَمْلُوكُ الْمُكَاتَبُ عَلَى مَوْلَاهُ أَنَّهُ لَا وَلَاءَ"
- Mursal opening: al-Ṣadūq → محمد بن قيس; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 329 · `faqih-3490`
- **Location:** vol. 3, p. 133 · seq 3502 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ عَاصِمِ بْنِ حُمَيْدٍ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الرَّجُلِ يُعْتِقُ الرَّجُلَ فِي كَفَّارَةِ يَمِينٍ أَوْ ظِهَارٍ لِمَنْ يَكُونُ الْوَلَاءُ قَالَ لِلَّذِي أَعْتَقَ‌[3].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ عَاصِمِ بْنِ حُمَيْدٍ عَنْ أَبِي بَصِيرٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن عاصم بن حمید | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |

### Chain 329 · `faqih-3490` — CLARIFIED
- Transmitters (student → teacher): عاصم بن حميد → ابي بصير → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنْ عَاصِمِ بْنِ حُمَيْدٍ عَنْ أَبِي بَصِيرٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الرَّجُلِ يُعْتِقُ الرَّجُلَ"
- Mursal opening: al-Ṣadūq → عاصم بن حميد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 330 · `faqih-3491`
- **Location:** vol. 3, p. 134 · seq 3503 · chain 1
- **Flags:** `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > فِي رِوَايَةِ عُبَيْدِ اللَّهِ بْنِ عَلِيٍّ الْحَلَبِيِّ عَنْ أَبِي عَبْدِ اللَّهِ ع‌ أَنَّهُ ذَكَرَ أَنَّ بَرِيرَةَ كَانَتْ عِنْدَ زَوْجٍ لَهَا وَ هِيَ مَمْلُوكَةٌ فَاشْتَرَتْهَا عَائِشَةُ فَأَعْتَقَتْهَا فَخَيَّرَهَا رَسُولُ اللَّهِ ص إِنْ شَاءَتْ تَقِرُّ عِنْدَ زَوْجِهَا وَ إِنْ شَاءَتْ فَارَقَتْهُ وَ كَانَ مَوَالِيهَا الَّذِينَ بَاعُوهَا قَدِ اشْتَرَطُوا وَلَاءَهَا عَلَى عَائِشَةَ فَقَالَ رَسُولُ اللَّهِ ص الْوَلَاءُ لِمَنْ أَعْتَقَ‌[1] وَ صُدِّقَ عَلَى بَرِيرَةَ بِلَحْمٍ فَأَهْدَتْهُ إِلَى رَسُولِ اللَّهِ ص فَعَلَّقَتْهُ عَائِشَةُ وَ قَالَتْ إِنَّ رَسُولَ اللَّهِ ص لَا يَأْكُلُ الصَّدَقَةَ فَجَاءَ رَسُولُ اللَّهِ ص وَ اللَّحْمُ مُعَلَّقٌ فَقَالَ مَا شَأْنُ هَذَا اللَّحْمِ لَمْ يُطْبَخْ قَالَتْ يَا رَسُولَ اللَّهِ صُدِّقَ بِهِ عَلَى بَرِيرَةَ وَ أَنْتَ لَا تَأْكُلُ الصَّدَقَةَ فَقَالَ ص هُوَ لَهَا صَدَقَةٌ وَ لَنَا هَدِيَّةٌ ثُمَّ أَمَرَ بِطَبْخِهِ فَجَرَتْ فِيهَا ثَلَاثٌ مِنَ السُّنَنِ‌[2].
- **Isnad as currently extracted:**
  > فِي رِوَايَةِ عُبَيْدِ اللَّهِ بْنِ عَلِيٍّ الْحَلَبِيِّ عَنْ أَبِي عَبْدِ اللَّهِ ع‌ أَنَّهُ ذَكَرَ أَنَّ بَرِيرَةَ كَانَتْ عِنْدَ زَوْجٍ لَهَا وَ هِيَ مَمْلُوكَةٌ فَاشْتَرَتْهَا عَائِشَةُ فَأَعْتَقَتْهَا فَخَيَّرَهَا رَسُولُ اللَّهِ ص إِنْ شَاءَتْ تَقِرُّ عِنْدَ زَوْجِهَا وَ إِنْ شَاءَتْ فَارَقَتْهُ وَ كَانَ مَوَالِيهَا الَّذِينَ بَاعُوهَا قَدِ اشْتَرَطُوا وَلَاءَهَا عَلَى عَائِشَةَ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | فی روایة عبید الله بن علی الحلبی |  |  |
  | 1 | named_narrator | ابی عبد الله ع انه ذکر ان بریرة کانت عند زوج لها و هی مملوکة فاشترتها عائشة فاعتقتها فخیرها رسول الله ص ان شاءت تقر عند زوجها و ان شاءت فارقته و کان موالیها الذین باعوها قد اشترطوا ولاءها علی عائشة فقال | عن |  |

### Chain 330 · `faqih-3491` — CLARIFIED
- Transmitters (student → teacher): عبيد الله بن علي الحلبي → أبو عبد الله ع
- Corrected isnad (Arabic): «فِي رِوَايَةِ عُبَيْدِ اللَّهِ بْنِ عَلِيٍّ الْحَلَبِيِّ عَنْ أَبِي عَبْدِ اللَّهِ ع‌ أَنَّهُ ذَكَرَ»
- Isnad ends / matn begins at: "أَنَّ بَرِيرَةَ كَانَتْ عِنْدَ زَوْجٍ لَهَا وَ هِيَ مَمْلُوكَةٌ"
- Mursal opening: al-Ṣadūq → عبيد الله بن علي الحلبي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name.

---

### Chain 331 · `faqih-3492`
- **Location:** vol. 3, p. 134 · seq 3504 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى صَفْوَانُ بْنُ يَحْيَى عَنِ الْعِيصِ بْنِ الْقَاسِمِ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ اشْتَرَى عَبْداً وَ لَهُ أَوْلَادٌ مِنِ امْرَأَةٍ حُرَّةٍ فَأَعْتَقَهُ قَالَ وَلَاءُ أَوْلَادِهِ لِمَنْ أَعْتَقَهُ‌[3].
- **Isnad as currently extracted:**
  > رَوَى صَفْوَانُ بْنُ يَحْيَى عَنِ الْعِيصِ بْنِ الْقَاسِمِ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | صفوان بن یحیی | روی |  |
  | 1 | named_narrator | العیص بن القاسم | عن |  |

### Chain 331 · `faqih-3492` — CLARIFIED
- Transmitters (student → teacher): صفوان بن يحيي → العيص بن القاسم → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى صَفْوَانُ بْنُ يَحْيَى عَنِ الْعِيصِ بْنِ الْقَاسِمِ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ اشْتَرَى عَبْداً"
- Mursal opening: al-Ṣadūq → صفوان بن يحيي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 332 · `faqih-3498`
- **Location:** vol. 3, p. 136 · seq 3510 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى ابْنُ مَحْبُوبٍ عَنْ عَمَّارِ بْنِ أَبِي الْأَحْوَصِ‌[3] قَالَ‌ سَأَلْتُ أَبَا جَعْفَرٍ ع عَنِ السَّائِبَةِ قَالَ انْظُرْ فِي الْقُرْآنِ فَمَا كَانَ فِيهِ تَحْرِيرُ رَقَبَةٍ فَذَلِكَ يَا عَمَّارُ السَّائِبَةُ الَّتِي لَا وَلَاءَ لِأَحَدٍ مِنَ الْمُسْلِمِينَ عَلَيْهِ إِلَّا اللَّهَ عَزَّ وَ جَلَّ فَمَا كَانَ وَلَاؤُهُ لِلَّهِ عَزَّ وَ جَلَّ فَهُوَ لِرَسُولِهِ وَ مَا كَانَ لِرَسُولِهِ ص فَإِنَّ وَلَاءَهُ لِلْإِمَامِ وَ جِنَايَتَهُ عَلَى الْإِمَامِ وَ مِيرَاثَهُ لَهُ.
- **Isnad as currently extracted:**
  > رَوَى ابْنُ مَحْبُوبٍ عَنْ عَمَّارِ بْنِ أَبِي الْأَحْوَصِ‌[3] قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن محبوب | روی |  |
  | 1 | named_narrator | عمار بن ابی الاحوص | عن |  |

### Chain 332 · `faqih-3498` — CLARIFIED
- Transmitters (student → teacher): ابن محبوب → عمار بن ابي الاحوص → ابا جعفر ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى ابْنُ مَحْبُوبٍ عَنْ عَمَّارِ بْنِ أَبِي الْأَحْوَصِ‌[3] قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا جَعْفَرٍ ع عَنِ السَّائِبَةِ قَالَ انْظُرْ فِي"
- Mursal opening: al-Ṣadūq → ابن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 333 · `faqih-3499`
- **Location:** vol. 3, p. 136 · seq 3511 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى يَاسِينُ عَنْ حَرِيزٍ عَنْ سُلَيْمَانَ بْنِ خَالِدٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ مَمْلُوكٍ أَرَادَ أَنْ يَشْتَرِيَ نَفْسَهُ فَدَسَّ إِنْسَاناً[4] هَلْ لِلْمَدْسُوسِ أَنْ يَشْتَرِيَهُ‌
كُلَّهُ مِنْ مَالِ الْعَبْدِ وَ لَا يُخْبِرَ السَّيِّدَ أَنَّهُ إِنَّمَا يَشْتَرِيهِ مِنْ مَالِ الْعَبْدِ قَالَ لَا يَنْبَغِي وَ إِنْ أَرَادَ أَنْ يَسْتَحِلَّ ذَلِكَ فِيمَا بَيْنَهُ وَ بَيْنَ اللَّهِ عَزَّ وَ جَلَّ حَتَّى يَكُونَ وَلَاؤُهُ لَهُ فَلْيَزِدْ هُوَ مَا يَشَاءُ[1] بَعْدَ أَنْ يَكُونَ زِيَادَةٌ مِنْ مَالِهِ فِي ثَمَنِ الْعَبْدِ يَسْتَحِلُّ بِهِ الْوَلَاءَ فَيَكُونُ وَلَاءُ الْعَبْدِ لَهُ.
- **Isnad as currently extracted:**
  > رَوَى يَاسِينُ عَنْ حَرِيزٍ عَنْ سُلَيْمَانَ بْنِ خَالِدٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ مَمْلُوكٍ أَرَادَ أَنْ يَشْتَرِيَ نَفْسَهُ فَدَسَّ إِنْسَاناً[4] هَلْ لِلْمَدْسُوسِ أَنْ يَشْتَرِيَهُ‌ كُلَّهُ مِنْ مَالِ الْعَبْدِ وَ لَا يُخْبِرَ السَّيِّدَ أَنَّهُ إِنَّمَا يَشْتَرِيهِ مِنْ مَالِ الْعَبْدِ قَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | یاسین | روی |  |
  | 1 | named_narrator | حریز | عن |  |
  | 2 | named_narrator | سلیمان بن خالد | عن |  |
  | 3 | imam | ابی عبد الله ع | عن |  |

### Chain 333 · `faqih-3499` — CLARIFIED
- Transmitters (student → teacher): ياسين → حريز → سليمان بن خالد → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى يَاسِينُ عَنْ حَرِيزٍ عَنْ سُلَيْمَانَ بْنِ خَالِدٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ مَمْلُوكٍ أَرَادَ أَنْ يَشْتَرِيَ نَفْسَهُ فَدَسَّ إِنْسَاناً[4]"
- Mursal opening: al-Ṣadūq → ياسين; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 334 · `faqih-3500`
- **Location:** vol. 3, p. 137 · seq 3512 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ أَبِي أَيُّوبَ عَنْ بُرَيْدٍ الْعِجْلِيِّ قَالَ‌ سَأَلْتُ أَبَا جَعْفَرٍ ع عَنْ رَجُلٍ كَانَ عَلَيْهِ عِتْقُ رَقَبَةٍ فَمَاتَ مِنْ قَبْلِ أَنْ يُعْتِقَ رَقَبَةً فَانْطَلَقَ ابْنُهُ فَابْتَاعَ رَجُلًا مِنْ كَسْبِهِ فَأَعْتَقَهُ عَنْ أَبِيهِ وَ إِنَّ الْمُعْتَقَ أَصَابَ بَعْدَ ذَلِكَ مَالًا ثُمَّ مَاتَ وَ تَرَكَهُ لِمَنْ يَكُونُ مِيرَاثُهُ قَالَ فَقَالَ إِنْ كَانَتِ الرَّقَبَةُ الَّتِي كَانَتْ عَلَى أَبِيهِ فِي نَذْرٍ أَوْ شُكْرٍ أَوْ كَانَتْ وَاجِبَةً عَلَيْهِ‌[2] فَإِنَّ الْمُعْتَقَ سَائِبَةٌ لَا سَبِيلَ لِأَحَدٍ عَلَيْهِ قَالَ فَإِنْ كَانَ تَوَلَّى قَبْلَ أَنْ يَمُوتَ إِلَى أَحَدٍ مِنَ الْمُسْلِمِينَ فَضَمِنَ جِنَايَتَهُ وَ جَرِيرَتَهُ‌[3] كَانَ مَوْلَاهُ وَ وَارِثَهُ إِنْ لَمْ يَكُنْ لَهُ قَرِيبٌ مِنَ الْمُسْلِمِينَ يَرِثُهُ وَ إِنْ لَمْ يَكُنْ تَوَالَى إِلَى أَحَدٍ حَتَّى مَاتَ فَإِنَّ مِيرَاثَهُ لِلْإِمَامِ إِمَامِ الْمُسْلِمِينَ إِنْ لَمْ يَكُنْ لَهُ قَرِيبٌ يَرِثُهُ مِنَ الْمُسْلِمِينَ قَالَ وَ إِنْ كَانَتِ الرَّقَبَةُ الَّتِي عَلَى أَبِيهِ تَطَوُّعاً وَ قَدْ كَانَ أَبُوهُ أَمَرَهُ أَنْ يُعْتِقُ عَنْهُ نَسَمَةً فَإِنَّ وَلَاءَ الْمُعْتَقِ هُوَ مِيرَاثٌ لِجَمِيعِ وُلْدِ الْمَيِّتِ‌[4] قَالَ وَ يَكُونُ الَّذِي اشْتَرَاهُ فَأَعْتَقَهُ بِأَمْرِ أَبِيهِ كَوَاحِدٍ مِنَ الْوَرَثَةِ إِذَا لَمْ يَكُنْ لِلْمُعْتَقِ قَرَابَةٌ مِنَ الْمُسْلِمِينَ أَحْرَارٌ يَرِثُونَهُ قَالَ وَ إِنْ كَانَ ابْنُهُ الَّذِي اشْتَرَى الرَّقَبَةَ فَأَعْتَقَهَا
عَنْ أَبِيهِ مِنْ مَالِهِ بَعْدَ مَوْتِ أَبِيهِ تَطَوُّعاً مِنْهُ مِنْ غَيْرِ أَنْ يَكُونَ أَبُوهُ أَمَرَهُ بِذَلِكَ فَإِنَّ وَلَاءَهُ وَ مِيرَاثَهُ لِلَّذِي اشْتَرَاهُ مِنْ مَالِهِ فَأَعْتَقَهُ عَنْ أَبِيهِ إِذَا لَمْ يَكُنْ لِلْمُعْتَقِ وَارِثٌ مِنْ قَرَابَتِهِ‌[1].
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ أَبِي أَيُّوبَ عَنْ بُرَيْدٍ الْعِجْلِيِّ قَالَ‌ سَأَلْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | ابی ایوب | عن |  |
  | 2 | named_narrator | برید العجلی | عن |  |

### Chain 334 · `faqih-3500` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → ابي ايوب → بريد العجلي → ابا جعفر ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ أَبِي أَيُّوبَ عَنْ بُرَيْدٍ الْعِجْلِيِّ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا جَعْفَرٍ ع عَنْ رَجُلٍ كَانَ عَلَيْهِ عِتْقُ"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 335 · `faqih-3501`
- **Location:** vol. 3, p. 138 · seq 3513 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ رِئَابٍ عَنْ زُرَارَةَ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنْ أُمِّ الْوَلَدِ قَالَ أَمَةٌ تُبَاعُ وَ تُورَثُ وَ تُوهَبُ وَ حَدُّهَا حَدُّ الْأَمَةِ[2].
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ رِئَابٍ عَنْ زُرَارَةَ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنْ أُمِّ الْوَلَدِ قَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | علی بن رئاب | عن |  |
  | 2 | named_narrator | زرارة | عن |  |
  | 3 | imam | ابی جعفر ع | عن |  |

### Chain 335 · `faqih-3501` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → علي بن رئاب → زرارة → ابي جعفر ع
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ رِئَابٍ عَنْ زُرَارَةَ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ أُمِّ الْوَلَدِ قَالَ أَمَةٌ تُبَاعُ وَ تُورَثُ"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 336 · `faqih-3503`
- **Location:** vol. 3, p. 138 · seq 3515 · chain 1
- **Flags:** `matn_spill`, `no_imam_terminal`
- **Full report (Arabic):**
  > فِي رِوَايَةِ مُحَمَّدِ بْنِ عَلِيِّ بْنِ مَحْبُوبٍ عَنْ أَحْمَدَ بْنِ مُحَمَّدِ بْنِ عِيسَى عَنِ الْبَزَنْطِيِّ عَنْ عَبْدِ اللَّهِ بْنِ سِنَانٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الرَّجُلِ يَمُوتُ وَ لَهُ أُمُّ وَلَدٍ وَ لَهُ مِنْهَا وَلَدٌ أَ يَصْلُحُ لِلرَّجُلِ‌[4] أَنْ يَتَزَوَّجَهَا فَقَالَ أُخْبِرْتُ أَنَّ عَلِيّاً ع-
أَوْصَى فِي أُمَّهَاتِ الْأَوْلَادِ اللَّاتِي كَانَ يَطُوفُ عَلَيْهِنَّ مَنْ كَانَ مِنْهُنَ‌[1] لَهَا وَلَدٌ فَهِيَ مِنْ نَصِيبِ وَلَدِهَا وَ مَنْ لَمْ يَكُنْ لَهَا وَلَدٌ فَهِيَ حُرَّةٌ وَ إِنَّمَا جُعِلَ مَنْ كَانَ مِنْهُنَّ لَهَا وَلَدٌ مِنْ نَصِيبِ وَلَدِهَا لِكَيْلَا تَنْكِحَ إِلَّا بِإِذْنِ أَهْلِهَا[2].
- **Isnad as currently extracted:**
  > فِي رِوَايَةِ مُحَمَّدِ بْنِ عَلِيِّ بْنِ مَحْبُوبٍ عَنْ أَحْمَدَ بْنِ مُحَمَّدِ بْنِ عِيسَى عَنِ الْبَزَنْطِيِّ عَنْ عَبْدِ اللَّهِ بْنِ سِنَانٍ قَالَ‌ سَأَلْتُ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | فی روایة محمد بن علی بن محبوب |  |  |
  | 1 | named_narrator | احمد بن محمد بن عیسی | عن |  |
  | 2 | named_narrator | البزنطی | عن |  |
  | 3 | named_narrator | عبد الله بن سنان | عن |  |

### Chain 336 · `faqih-3503` — CLARIFIED
- Transmitters (student → teacher): محمد بن علي بن محبوب → احمد بن محمد بن عيسي → البزنطي → عبد الله بن سنان
- Corrected isnad (Arabic): «فِي رِوَايَةِ مُحَمَّدِ بْنِ عَلِيِّ بْنِ مَحْبُوبٍ عَنْ أَحْمَدَ بْنِ مُحَمَّدِ بْنِ عِيسَى عَنِ الْبَزَنْطِيِّ عَنْ عَبْدِ اللَّهِ بْنِ سِنَانٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنِ الرَّجُلِ يَمُوتُ وَ"
- Mursal opening: al-Ṣadūq → محمد بن علي بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 337 · `faqih-3506`
- **Location:** vol. 3, p. 139 · seq 3518 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى عُمَرُ بْنُ يَزِيدَ عَنْ أَبِي إِبْرَاهِيمَ ع‌[5] قَالَ‌ قُلْتُ لَهُ أَسْأَلُكَ قَالَ سَلْ قُلْتُ لِمَ بَاعَ أَمِيرُ الْمُؤْمِنِينَ ع أُمَّهَاتِ الْأَوْلَادِ فَقَالَ فِي فَكَاكِ رِقَابِهِنَّ قُلْتُ وَ كَيْفَ ذَاكَ قَالَ أَيُّمَا رَجُلٍ اشْتَرَى جَارِيَةً فَأَوْلَدَهَا ثُمَّ لَمْ يُؤَدِّ ثَمَنَهَا وَ لَمْ يَدَعْ مِنَ الْمَالِ مَا يُؤَدَّى عَنْهُ أُخِذَ وَلَدُهَا مِنْهَا وَ بِيعَتْ‌[6] وَ أُدِّيَ ثَمَنُهَا قُلْتُ فَتُبَاعُ فِيمَا
سِوَى ذَلِكَ مِنَ الدَّيْنِ قَالَ لَا.
- **Isnad as currently extracted:**
  > رَوَى عُمَرُ بْنُ يَزِيدَ عَنْ أَبِي إِبْرَاهِيمَ ع‌[5] قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عمر بن یزید | روی |  |
  | 1 | imam | ابی ابراهیم ع | عن |  |

### Chain 337 · `faqih-3506` — CLARIFIED
- Transmitters (student → teacher): عمر بن يزيد → ابي ابراهيم ع
- Corrected isnad (Arabic): «رَوَى عُمَرُ بْنُ يَزِيدَ عَنْ أَبِي إِبْرَاهِيمَ ع‌[5] قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ أَسْأَلُكَ قَالَ سَلْ قُلْتُ لِمَ بَاعَ أَمِيرُ"
- Mursal opening: al-Ṣadūq → عمر بن يزيد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 338 · `faqih-3508`
- **Location:** vol. 3, p. 140 · seq 3520 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى الْحُسَيْنُ بْنُ سَعِيدٍ عَنْ صَفْوَانَ بْنِ يَحْيَى عَنِ الْوَلِيدِ بْنِ هِشَامٍ قَالَ‌ قَدِمْتُ مِنْ مِصْرَ وَ مَعِي رَقِيقٌ فَمَرَرْتُ بِالْعَاشِرِ[4] فَسَأَلَنِي فَقُلْتُ هُمْ أَحْرَارٌ كُلُّهُمْ فَقَدِمْتُ الْمَدِينَةَ فَدَخَلْتُ عَلَى أَبِي الْحَسَنِ ع فَأَخْبَرْتُهُ بِقَوْلِي لِلْعَاشِرِ فَقَالَ لَيْسَ عَلَيْكَ شَيْ‌ءٌ[5] فَقُلْتُ إِنَّ فِيهِمْ جَارِيَةً قَدْ وَقَعْتُ عَلَيْهَا وَ بِهَا حَمْلٌ قَالَ لَا أَ لَيْسَ وَلَدُهَا بِالَّذِي يُعْتِقُهَا إِذَا هَلَكَ سَيِّدُهَا صَارَتْ مِنْ نَصِيبِ وَلَدِهَا[6].
- **Isnad as currently extracted:**
  > رَوَى الْحُسَيْنُ بْنُ سَعِيدٍ عَنْ صَفْوَانَ بْنِ يَحْيَى عَنِ الْوَلِيدِ بْنِ هِشَامٍ قَالَ‌ قَدِمْتُ مِنْ مِصْرَ وَ مَعِي رَقِيقٌ فَمَرَرْتُ بِالْعَاشِرِ[4] فَسَأَلَنِي فَقُلْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسین بن سعید | روی |  |
  | 1 | named_narrator | صفوان بن یحیی | عن |  |
  | 2 | named_narrator | الولید بن هشام | عن |  |

### Chain 338 · `faqih-3508` — CLARIFIED
- Transmitters (student → teacher): الحسين بن سعيد → صفوان بن يحيي → الوليد بن هشام → ابي الحسن ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى الْحُسَيْنُ بْنُ سَعِيدٍ عَنْ صَفْوَانَ بْنِ يَحْيَى عَنِ الْوَلِيدِ بْنِ هِشَامٍ قَالَ‌»
- Isnad ends / matn begins at: "قَدِمْتُ مِنْ مِصْرَ وَ مَعِي رَقِيقٌ فَمَرَرْتُ بِالْعَاشِرِ[4] فَسَأَلَنِي"
- Mursal opening: al-Ṣadūq → الحسين بن سعيد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim.

---

### Chain 339 · `faqih-3510`
- **Location:** vol. 3, p. 141 · seq 3522 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنِ الْعَبَّاسِ بْنِ عَامِرٍ عَنْ أَبَانٍ عَنْ مُحَمَّدِ بْنِ الْفَضْلِ الْهَاشِمِيِّ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ أَقَرَّ أَنَّهُ عَبْدٌ قَالَ يَأْخُذُهُ بِمَا قَالَ أَوْ يَرُدَّ الْمَالَ‌[1].
- **Isnad as currently extracted:**
  > رُوِيَ عَنِ الْعَبَّاسِ بْنِ عَامِرٍ عَنْ أَبَانٍ عَنْ مُحَمَّدِ بْنِ الْفَضْلِ الْهَاشِمِيِّ قَالَ‌ قُلْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن العباس بن عامر | روی |  |
  | 1 | named_narrator | ابان | عن |  |
  | 2 | named_narrator | محمد بن الفضل الهاشمی | عن |  |

### Chain 339 · `faqih-3510` — CLARIFIED
- Transmitters (student → teacher): العباس بن عامر → ابان → محمد بن الفضل الهاشمي
- Corrected isnad (Arabic): «رُوِيَ عَنِ الْعَبَّاسِ بْنِ عَامِرٍ عَنْ أَبَانٍ عَنْ مُحَمَّدِ بْنِ الْفَضْلِ الْهَاشِمِيِّ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ أَقَرَّ أَنَّهُ عَبْدٌ"
- Mursal opening: al-Ṣadūq → العباس بن عامر; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 340 · `faqih-3517`
- **Location:** vol. 3, p. 142 · seq 3529 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ سَيْفِ بْنِ عَمِيرَةَ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع أَ يَجُوزُ
لِلْمُسْلِمِ أَنْ يُعْتِقَ مَمْلُوكاً مُشْرِكاً قَالَ لَا[1].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ سَيْفِ بْنِ عَمِيرَةَ قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن سیف بن عمیرة | روی |  |

### Chain 340 · `faqih-3517` — CLARIFIED
- Transmitters (student → teacher): سيف بن عميرة
- Corrected isnad (Arabic): «رُوِيَ عَنْ سَيْفِ بْنِ عَمِيرَةَ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع أَ يَجُوزُ لِلْمُسْلِمِ أَنْ"
- Mursal opening: al-Ṣadūq → سيف بن عميرة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 341 · `faqih-3519`
- **Location:** vol. 3, p. 143 · seq 3531 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رُوِيَ عَنْ عَلِيِّ بْنِ جَعْفَرٍ عَنْ أَخِيهِ مُوسَى بْنِ جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ عَلَيْهِ عِتْقُ رَقَبَةٍ فَأَرَادَ أَنْ يُعْتِقَ نَسَمَةً أَيُّهُمَا أَفْضَلُ أَنْ يُعْتِقَ شَيْخاً كَبِيراً أَوْ شَابّاً أَجْرَدَ قَالَ أَعْتَقَ مَنْ أَغْنَى نَفْسَهُ‌[3] الشَّيْخُ الْكَبِيرُ أَفْضَلُ مِنَ الشَّابِّ الْأَجْرَدِ[4].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ عَلِيِّ بْنِ جَعْفَرٍ عَنْ أَخِيهِ مُوسَى بْنِ جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ عَلَيْهِ عِتْقُ رَقَبَةٍ فَأَرَادَ أَنْ يُعْتِقَ نَسَمَةً أَيُّهُمَا أَفْضَلُ أَنْ يُعْتِقَ شَيْخاً كَبِيراً أَوْ شَابّاً أَجْرَدَ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن علی بن جعفر | روی |  |
  | 1 | imam | اخیه موسی بن جعفر ع | عن |  |

### Chain 341 · `faqih-3519` — CLARIFIED
- Transmitters (student → teacher): علي بن جعفر → اخيه موسي بن جعفر ع
- Corrected isnad (Arabic): «رُوِيَ عَنْ عَلِيِّ بْنِ جَعْفَرٍ عَنْ أَخِيهِ مُوسَى بْنِ جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ عَلَيْهِ عِتْقُ رَقَبَةٍ فَأَرَادَ أَنْ يُعْتِقَ"
- Mursal opening: al-Ṣadūq → علي بن جعفر; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 342 · `faqih-3520`
- **Location:** vol. 3, p. 143 · seq 3532 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ أَحْمَدَ بْنِ هِلَالٍ قَالَ‌ كَتَبْتُ إِلَى أَبِي الْحَسَنِ ع‌[5] كَانَ‌
عَلَيَّ عِتْقُ رَقَبَةٍ فَهَرَبَ لِي مَمْلُوكٌ لَسْتُ أَعْلَمُ أَيْنَ هُوَ أَ يُجْزِينِي عِتْقُهُ فَكَتَبَ ع نَعَمْ.
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ أَحْمَدَ بْنِ هِلَالٍ قَالَ‌ كَتَبْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن احمد بن هلال | روی |  |

### Chain 342 · `faqih-3520` — CLARIFIED
- Transmitters (student → teacher): احمد بن هلال → ابي الحسن ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنْ أَحْمَدَ بْنِ هِلَالٍ قَالَ‌»
- Isnad ends / matn begins at: "كَتَبْتُ إِلَى أَبِي الْحَسَنِ ع‌[5] كَانَ‌ عَلَيَّ عِتْقُ رَقَبَةٍ"
- Mursal opening: al-Ṣadūq → احمد بن هلال; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 343 · `faqih-3521`
- **Location:** vol. 3, p. 144 · seq 3533 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ أَبِي هَاشِمٍ الْجَعْفَرِيِّ قَالَ‌ سَأَلْتُ أَبَا الْحَسَنِ ع عَنْ رَجُلٍ لَهُ مَمْلُوكٌ قَدْ أَبَقَ مِنْهُ يَجُوزُ أَنْ يُعْتِقَهُ فِي كَفَّارَةِ الظِّهَارِ قَالَ لَا بَأْسَ بِهِ مَا لَمْ يَعْرِفْ مِنْهُ مَوْتاً[1].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ أَبِي هَاشِمٍ الْجَعْفَرِيِّ قَالَ‌ سَأَلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن ابی هاشم الجعفری | روی |  |

### Chain 343 · `faqih-3521` — CLARIFIED
- Transmitters (student → teacher): ابي هاشم الجعفري → ابا الحسن ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنْ أَبِي هَاشِمٍ الْجَعْفَرِيِّ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا الْحَسَنِ ع عَنْ رَجُلٍ لَهُ مَمْلُوكٌ قَدْ"
- Mursal opening: al-Ṣadūq → ابي هاشم الجعفري; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 344 · `faqih-3523`
- **Location:** vol. 3, p. 144 · seq 3535 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى عَنْبَسَةُ بْنُ مُصْعَبٍ‌[3] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ لَهُ جَارِيَةٌ لِي زَنَتْ أَبِيعُ وَلَدَهَا قَالَ نَعَمْ قُلْتُ أَحُجُّ بِثَمَنِهِ قَالَ نَعَمْ‌[4].
- **Isnad as currently extracted:**
  > رَوَى عَنْبَسَةُ بْنُ مُصْعَبٍ‌[3] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عنبسة بن مصعب | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 344 · `faqih-3523` — CLARIFIED
- Transmitters (student → teacher): عنبسة بن مصعب → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى عَنْبَسَةُ بْنُ مُصْعَبٍ‌[3] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ جَارِيَةٌ لِي زَنَتْ أَبِيعُ وَلَدَهَا قَالَ نَعَمْ"
- Mursal opening: al-Ṣadūq → عنبسة بن مصعب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 345 · `faqih-3527`
- **Location:** vol. 3, p. 145 · seq 3539 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى زُرَارَةُ عَنْ أَحَدِهِمَا ع أَنَّهُ قَالَ‌ فِي لَقِيطَةٍ وُجِدَتْ فَقَالَ حُرَّةٌ لَا تُشْتَرَى وَ لَا تُبَاعُ وَ إِنْ كَانَ وُلِدَ مَمْلُوكٌ لَكَ مِنَ الزِّنَا فَأَمْسِكْ أَوْ بِعْ إِنْ أَحْبَبْتَ هُوَ مَمْلُوكٌ لَكَ.
- **Isnad as currently extracted:**
  > رَوَى زُرَارَةُ عَنْ أَحَدِهِمَا ع أَنَّهُ قَالَ‌ فِي لَقِيطَةٍ وُجِدَتْ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | زرارة | روی |  |
  | 1 | imam | احدهما ع | عن | ambiguous |

### Chain 345 · `faqih-3527` — CLARIFIED
- Transmitters (student → teacher): زرارة → احدهما ع
- Corrected isnad (Arabic): «رَوَى زُرَارَةُ عَنْ أَحَدِهِمَا ع أَنَّهُ قَالَ‌»
- Isnad ends / matn begins at: "فِي لَقِيطَةٍ وُجِدَتْ فَقَالَ حُرَّةٌ لَا تُشْتَرَى وَ لَا"
- Mursal opening: al-Ṣadūq → زرارة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim.

---

### Chain 346 · `faqih-3531`
- **Location:** vol. 3, p. 146 · seq 3543 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنْ جَارِيَةٍ مُدَبَّرَةٍ أَبَقَتْ مِنْ سَيِّدِهَا سِنِينَ ثُمَّ إِنَّهَا جَاءَتْ بَعْدَ مَا مَاتَ سَيِّدُهَا بِأَوْلَادٍ وَ مَتَاعٍ كَثِيرٍ وَ شَهِدَ لَهَا شَاهِدَانِ أَنَّ سَيِّدَهَا كَانَ قَدْ دَبَّرَهَا فِي حَيَاتِهِ مِنْ قَبْلِ أَنْ تَأْبِقَ قَالَ أَرَى أَنَّ جَمِيعَ مَا مَعَهَا لِلْوَرَثَةِ[5] قُلْتُ وَ لَا تُعْتَقُ مِنْ ثُلُثِ سَيِّدِهَا قَالَ لَا إِنَّهَا أَبَقَتْ عَاصِيَةً لِلَّهِ وَ لِسَيِّدِهَا فَأَبْطَلَ الْإِبَاقُ التَّدْبِيرَ[6].
- **Isnad as currently extracted:**
  > رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنْ جَارِيَةٍ مُدَبَّرَةٍ أَبَقَتْ مِنْ سَيِّدِهَا سِنِينَ ثُمَّ إِنَّهَا جَاءَتْ بَعْدَ مَا مَاتَ سَيِّدُهَا بِأَوْلَادٍ وَ مَتَاعٍ كَثِيرٍ وَ شَهِدَ لَهَا شَاهِدَانِ أَنَّ سَيِّدَهَا كَانَ قَدْ دَبَّرَهَا فِي حَيَاتِهِ مِنْ قَبْلِ أَنْ تَأْبِقَ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن مسلم | روی |  |
  | 1 | imam | ابی جعفر ع | عن |  |

### Chain 346 · `faqih-3531` — CLARIFIED
- Transmitters (student → teacher): محمد بن مسلم → ابي جعفر ع
- Corrected isnad (Arabic): «رَوَى مُحَمَّدُ بْنُ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ جَارِيَةٍ مُدَبَّرَةٍ أَبَقَتْ مِنْ سَيِّدِهَا سِنِينَ ثُمَّ"
- Mursal opening: al-Ṣadūq → محمد بن مسلم; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 347 · `faqih-3535`
- **Location:** vol. 3, p. 147 · seq 3547 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنِ الْحَسَنِ بْنِ صَالِحٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ أَصَابَ دَابَّةً[3] قَدْ سُرِقَتْ مِنْ جَارٍ لَهُ فَأَخَذَهَا لِيَأْتِيَهُ بِهَا فَنَفَقَتْ قَالَ لَيْسَ عَلَيْهِ شَيْ‌ءٌ[4].
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنِ الْحَسَنِ بْنِ صَالِحٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ أَصَابَ دَابَّةً[3] قَدْ سُرِقَتْ مِنْ جَارٍ لَهُ فَأَخَذَهَا لِيَأْتِيَهُ بِهَا فَنَفَقَتْ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | الحسن بن صالح | عن |  |
  | 2 | imam | ابی عبد الله ع | عن |  |

### Chain 347 · `faqih-3535` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → الحسن بن صالح → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنِ الْحَسَنِ بْنِ صَالِحٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ أَصَابَ دَابَّةً[3] قَدْ سُرِقَتْ مِنْ جَارٍ"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 348 · `faqih-3537`
- **Location:** vol. 3, p. 148 · seq 3549 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى ابْنُ أَبِي عُمَيْرٍ عَنْ أَبِي حَبِيبٍ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ اشْتَرَى مِنْ رَجُلٍ عَبْداً وَ كَانَ عِنْدَهُ عَبْدَانِ فَقَالَ لِلْمُشْتَرِي اذْهَبْ بِهِمَا فَاخْتَرْ أَحَدَهُمَا وَ رُدَّ الْآخَرَ وَ قَدْ قَبَضَ الْمَالَ فَذَهَبَ بِهِمَا الْمُشْتَرِي فَأَبَقَ أَحَدُهُمَا مِنْ عِنْدِهِ قَالَ لِيَرُدَّ الَّذِي عِنْدَهُ مِنْهُمَا وَ يَقْبِضُ نِصْفَ ثَمَنِ مَا أَعْطَى مِنَ الْبَائِعِ وَ يَذْهَبُ فِي طَلَبِ الْغُلَامِ فَإِنْ وَجَدَهُ اخْتَارَ أَيَّهُمَا شَاءَ وَ رَدَّ الْآخَرَ وَ إِنْ لَمْ يَجِدْهُ كَانَ الْعَبْدُ بَيْنَهُمَا نِصْفُهُ لِلْبَائِعِ وَ نِصْفُهُ لِلْمُبْتَاعِ‌[1].
- **Isnad as currently extracted:**
  > رَوَى ابْنُ أَبِي عُمَيْرٍ عَنْ أَبِي حَبِيبٍ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ اشْتَرَى مِنْ رَجُلٍ عَبْداً وَ كَانَ عِنْدَهُ عَبْدَانِ فَقَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن ابی عمیر | روی |  |
  | 1 | named_narrator | ابی حبیب | عن |  |
  | 2 | named_narrator | محمد بن مسلم | عن |  |
  | 3 | imam | ابی جعفر ع | عن |  |

### Chain 348 · `faqih-3537` — CLARIFIED
- Transmitters (student → teacher): ابن ابي عمير → ابي حبيب → محمد بن مسلم → ابي جعفر ع
- Corrected isnad (Arabic): «رَوَى ابْنُ أَبِي عُمَيْرٍ عَنْ أَبِي حَبِيبٍ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ اشْتَرَى مِنْ رَجُلٍ عَبْداً وَ كَانَ"
- Mursal opening: al-Ṣadūq → ابن ابي عمير; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 349 · `faqih-3537`
- **Location:** vol. 3, p. 148 · seq 3549 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى ابْنُ أَبِي عُمَيْرٍ عَنْ أَبِي حَبِيبٍ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ اشْتَرَى مِنْ رَجُلٍ عَبْداً وَ كَانَ عِنْدَهُ عَبْدَانِ فَقَالَ لِلْمُشْتَرِي اذْهَبْ بِهِمَا فَاخْتَرْ أَحَدَهُمَا وَ رُدَّ الْآخَرَ وَ قَدْ قَبَضَ الْمَالَ فَذَهَبَ بِهِمَا الْمُشْتَرِي فَأَبَقَ أَحَدُهُمَا مِنْ عِنْدِهِ قَالَ لِيَرُدَّ الَّذِي عِنْدَهُ مِنْهُمَا وَ يَقْبِضُ نِصْفَ ثَمَنِ مَا أَعْطَى مِنَ الْبَائِعِ وَ يَذْهَبُ فِي طَلَبِ الْغُلَامِ فَإِنْ وَجَدَهُ اخْتَارَ أَيَّهُمَا شَاءَ وَ رَدَّ الْآخَرَ وَ إِنْ لَمْ يَجِدْهُ كَانَ الْعَبْدُ بَيْنَهُمَا نِصْفُهُ لِلْبَائِعِ وَ نِصْفُهُ لِلْمُبْتَاعِ‌[1].
- **Isnad as currently extracted:**
  > رَوَى ابْنُ أَبِي عُمَيْرٍ عَنْ أَبِي حَبِيبٍ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ اشْتَرَى مِنْ رَجُلٍ عَبْداً وَ كَانَ عِنْدَهُ عَبْدَانِ فَقَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن ابی عمیر | روی |  |
  | 1 | named_narrator | ابی حبیب | عن |  |
  | 2 | named_narrator | محمد بن مسلم | عن |  |
  | 3 | imam | ابی جعفر ع | عن |  |

### Chain 349 · `faqih-3537` — CLARIFIED
- Transmitters (student → teacher): ابن ابي عمير → ابي حبيب → محمد بن مسلم → ابي جعفر ع
- Corrected isnad (Arabic): «رَوَى ابْنُ أَبِي عُمَيْرٍ عَنْ أَبِي حَبِيبٍ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ اشْتَرَى مِنْ رَجُلٍ عَبْداً وَ كَانَ"
- Mursal opening: al-Ṣadūq → ابن ابي عمير; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 350 · `faqih-3548`
- **Location:** vol. 3, p. 152 · seq 3560 · chain 1
- **Flags:** `matn_spill`, `multi_route`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى فَضَالَةُ عَنْ أَبَانٍ أَنَّ أَبَا عَبْدِ اللَّهِ ع قَالَ‌ فِي الصَّبِيِّ إِذَا شَبَّ فَاخْتَارَ النَّصْرَانِيَّةَ وَ أَحَدُ أَبَوَيْهِ نَصْرَانِيٌّ أَوْ جَمِيعاً مُسْلِمَيْنِ قَالَ لَا يُتْرَكُ وَ لَكِنْ يُضْرَبُ عَلَى الْإِسْلَامِ‌[5].
- **Isnad as currently extracted:**
  > رَوَى فَضَالَةُ عَنْ أَبَانٍ أَنَّ أَبَا عَبْدِ اللَّهِ ع قَالَ‌ فِي الصَّبِيِّ إِذَا شَبَّ فَاخْتَارَ النَّصْرَانِيَّةَ وَ أَحَدُ أَبَوَيْهِ نَصْرَانِيٌّ أَوْ جَمِيعاً مُسْلِمَيْنِ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | فضالة | روی |  |
  | 1 | imam | ابان ان ابا عبد الله ع | عن |  |

### Chain 350 · `faqih-3548` — CLARIFIED
- Transmitters (student → teacher): فضالة → أبان → أبو عبد الله ع
- Corrected isnad (Arabic): «رَوَى فَضَالَةُ عَنْ أَبَانٍ أَنَّ أَبَا عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "فِي الصَّبِيِّ إِذَا شَبَّ فَاخْتَارَ النَّصْرَانِيَّةَ وَ أَحَدُ أَبَوَيْهِ"
- Mursal opening: al-Ṣadūq → فضالة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: «أَنَّ أَبَا عَبْدِ اللَّهِ» attaches directly to Abān and gives a single complete route. The previous automatic fork warning was a parser false positive.
---

### Chain 351 · `faqih-3549`
- **Location:** vol. 3, p. 152 · seq 3561 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى ابْنُ فَضَّالٍ عَنْ أَبَانٍ‌[6] أَنَّ أَبَا عَبْدِ اللَّهِ ع قَالَ‌ فِي الرَّجُلِ يَمُوتُ مُرْتَدّاً عَنِ الْإِسْلَامِ وَ لَهُ أَوْلَادٌ وَ مَالٌ قَالَ مَالُهُ لِوُلْدِهِ الْمُسْلِمِينَ‌[7].
- **Isnad as currently extracted:**
  > رَوَى ابْنُ فَضَّالٍ عَنْ أَبَانٍ‌[6] أَنَّ أَبَا عَبْدِ اللَّهِ ع قَالَ‌ فِي الرَّجُلِ يَمُوتُ مُرْتَدّاً عَنِ الْإِسْلَامِ وَ لَهُ أَوْلَادٌ وَ مَالٌ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن فضال | روی |  |
  | 1 | imam | ابان ان ابا عبد الله ع | عن |  |

### Chain 351 · `faqih-3549` — CLARIFIED
- Transmitters (student → teacher): ابن فضال → ابان ان ابا عبد الله ع
- Corrected isnad (Arabic): «رَوَى ابْنُ فَضَّالٍ عَنْ أَبَانٍ‌[6] أَنَّ أَبَا عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "فِي الرَّجُلِ يَمُوتُ مُرْتَدّاً عَنِ الْإِسْلَامِ وَ لَهُ أَوْلَادٌ"
- Mursal opening: al-Ṣadūq → ابن فضال; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 352 · `faqih-3549`
- **Location:** vol. 3, p. 152 · seq 3561 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى ابْنُ فَضَّالٍ عَنْ أَبَانٍ‌[6] أَنَّ أَبَا عَبْدِ اللَّهِ ع قَالَ‌ فِي الرَّجُلِ يَمُوتُ مُرْتَدّاً عَنِ الْإِسْلَامِ وَ لَهُ أَوْلَادٌ وَ مَالٌ قَالَ مَالُهُ لِوُلْدِهِ الْمُسْلِمِينَ‌[7].
- **Isnad as currently extracted:**
  > رَوَى ابْنُ فَضَّالٍ عَنْ أَبَانٍ‌[6] أَنَّ أَبَا عَبْدِ اللَّهِ ع قَالَ‌ فِي الرَّجُلِ يَمُوتُ مُرْتَدّاً عَنِ الْإِسْلَامِ وَ لَهُ أَوْلَادٌ وَ مَالٌ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن فضال | روی |  |
  | 1 | imam | ابان ان ابا عبد الله ع | عن |  |

### Chain 352 · `faqih-3549` — CLARIFIED
- Transmitters (student → teacher): ابن فضال → ابان ان ابا عبد الله ع
- Corrected isnad (Arabic): «رَوَى ابْنُ فَضَّالٍ عَنْ أَبَانٍ‌[6] أَنَّ أَبَا عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "فِي الرَّجُلِ يَمُوتُ مُرْتَدّاً عَنِ الْإِسْلَامِ وَ لَهُ أَوْلَادٌ"
- Mursal opening: al-Ṣadūq → ابن فضال; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 353 · `faqih-3549`
- **Location:** vol. 3, p. 152 · seq 3561 · chain 3
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى ابْنُ فَضَّالٍ عَنْ أَبَانٍ‌[6] أَنَّ أَبَا عَبْدِ اللَّهِ ع قَالَ‌ فِي الرَّجُلِ يَمُوتُ مُرْتَدّاً عَنِ الْإِسْلَامِ وَ لَهُ أَوْلَادٌ وَ مَالٌ قَالَ مَالُهُ لِوُلْدِهِ الْمُسْلِمِينَ‌[7].
- **Isnad as currently extracted:**
  > رَوَى ابْنُ فَضَّالٍ عَنْ أَبَانٍ‌[6] أَنَّ أَبَا عَبْدِ اللَّهِ ع قَالَ‌ فِي الرَّجُلِ يَمُوتُ مُرْتَدّاً عَنِ الْإِسْلَامِ وَ لَهُ أَوْلَادٌ وَ مَالٌ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابن فضال | روی |  |
  | 1 | imam | ابان ان ابا عبد الله ع | عن |  |

### Chain 353 · `faqih-3549` — CLARIFIED
- Transmitters (student → teacher): ابن فضال → ابان ان ابا عبد الله ع
- Corrected isnad (Arabic): «رَوَى ابْنُ فَضَّالٍ عَنْ أَبَانٍ‌[6] أَنَّ أَبَا عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "فِي الرَّجُلِ يَمُوتُ مُرْتَدّاً عَنِ الْإِسْلَامِ وَ لَهُ أَوْلَادٌ"
- Mursal opening: al-Ṣadūq → ابن فضال; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 354 · `faqih-3551`
- **Location:** vol. 3, p. 153 · seq 3563 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى سَعْدُ بْنُ سَعْدٍ عَنْ حَرِيزٍ[2] قَالَ‌ سَأَلْتُ أَبَا الْحَسَنِ ع عَنْ رَجُلٍ قَالَ لِمَمْلُوكِهِ أَنْتَ حُرٌّ وَ لِي مَالُكَ قَالَ يَبْدَأُ بِالْمَالِ قَبْلَ الْعِتْقِ يَقُولُ لِي مَالُكَ وَ أَنْتَ حُرٌّ بِرِضاً مِنَ الْمَمْلُوكِ‌[3].
- **Isnad as currently extracted:**
  > رَوَى سَعْدُ بْنُ سَعْدٍ عَنْ حَرِيزٍ[2] قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | سعد بن سعد | روی |  |
  | 1 | named_narrator | حریز | عن |  |

### Chain 354 · `faqih-3551` — CLARIFIED
- Transmitters (student → teacher): سعد بن سعد → حريز → ابا الحسن ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى سَعْدُ بْنُ سَعْدٍ عَنْ حَرِيزٍ[2] قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا الْحَسَنِ ع عَنْ رَجُلٍ قَالَ لِمَمْلُوكِهِ أَنْتَ"
- Mursal opening: al-Ṣadūq → سعد بن سعد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 355 · `faqih-3553`
- **Location:** vol. 3, p. 153 · seq 3565 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى إِبْرَاهِيمُ بْنُ مَهْزِيَارَ عَنْ أَخِيهِ عَلِيِّ بْنِ مَهْزِيَارَ قَالَ‌ كَتَبْتُ إِلَيْهِ‌[5] أَسْأَلُهُ عَنِ الْمَمْلُوكِ يَحْضُرُهُ الْمَوْتُ فَيُعْتِقُهُ مَوْلَاهُ فِي تِلْكَ السَّاعَةِ فَيَخْرُجُ مِنَ الدُّنْيَا حُرّاً هَلْ لِلْمَوْلَى فِي عِتْقِهِ ذَلِكَ أَجْرٌ أَوْ يَتْرُكُهُ مَمْلُوكاً فَيَكُونُ لَهُ أَجْرٌ إِذَا مَاتَ وَ هُوَ مَمْلُوكٌ لَهُ أَفْضَلُ فَكَتَبَ ع يُتْرَكُ الْعَبْدُ مَمْلُوكاً فِي حَالِ مَوْتِهِ فَهُوَ آجَرُ لِمَوْلَاهُ‌[6] وَ هَذَا الْعِتْقُ فِي تِلْكَ السَّاعَةِ[7] لَمْ يَكُنْ نَافِعاً لَهُ.
- **Isnad as currently extracted:**
  > رَوَى إِبْرَاهِيمُ بْنُ مَهْزِيَارَ عَنْ أَخِيهِ عَلِيِّ بْنِ مَهْزِيَارَ قَالَ‌ كَتَبْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابراهیم بن مهزیار | روی |  |
  | 1 | named_narrator | اخیه علی بن مهزیار | عن |  |

### Chain 355 · `faqih-3553` — CLARIFIED
- Transmitters (student → teacher): ابراهيم بن مهزيار → اخيه علي بن مهزيار
- Corrected isnad (Arabic): «رَوَى إِبْرَاهِيمُ بْنُ مَهْزِيَارَ عَنْ أَخِيهِ عَلِيِّ بْنِ مَهْزِيَارَ قَالَ‌»
- Isnad ends / matn begins at: "كَتَبْتُ إِلَيْهِ‌[5] أَسْأَلُهُ عَنِ الْمَمْلُوكِ يَحْضُرُهُ الْمَوْتُ فَيُعْتِقُهُ مَوْلَاهُ"
- Mursal opening: al-Ṣadūq → ابراهيم بن مهزيار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 356 · `faqih-3554`
- **Location:** vol. 3, p. 154 · seq 3566 · chain 1
- **Flags:** `mursal_opening`, `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > رَوَى مُحَمَّدُ بْنُ عِيسَى الْعُبَيْدِيُّ عَنِ الْفَضْلِ بْنِ الْمُبَارَكِ‌ أَنَّهُ كَتَبَ إِلَى أَبِي الْحَسَنِ عَلِيِّ بْنِ مُحَمَّدٍ ع فِي رَجُلٍ لَهُ مَمْلُوكٌ فَمَرِضَ أَ يُعْتِقُهُ فِي مَرَضِهِ أَعْظَمُ لِأَجْرِهِ أَوْ يَتْرُكُهُ مَمْلُوكاً فَقَالَ إِنْ كَانَ فِي مَرَضٍ فَالْعِتْقُ أَفْضَلُ لَهُ لِأَنَّهُ يُعْتِقُ اللَّهُ عَزَّ وَ جَلَّ بِكُلِّ عُضْوٍ مِنْهُ عُضْواً مِنَ النَّارِ وَ إِنْ كَانَ فِي حَالِ حُضُورِ الْمَوْتِ فَيَتْرُكُهُ مَمْلُوكاً أَفْضَلُ لَهُ مِنْ عِتْقِهِ.
- **Isnad as currently extracted:**
  > رَوَى مُحَمَّدُ بْنُ عِيسَى الْعُبَيْدِيُّ عَنِ الْفَضْلِ بْنِ الْمُبَارَكِ‌ أَنَّهُ كَتَبَ إِلَى أَبِي الْحَسَنِ عَلِيِّ بْنِ مُحَمَّدٍ ع فِي رَجُلٍ لَهُ مَمْلُوكٌ فَمَرِضَ أَ يُعْتِقُهُ فِي مَرَضِهِ أَعْظَمُ لِأَجْرِهِ أَوْ يَتْرُكُهُ مَمْلُوكاً فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن عیسی العبیدی | روی |  |
  | 1 | named_narrator | الفضل بن المبارک انه کتب الی ابی الحسن علی بن محمد ع فی رجل له مملوک فمرض ا یعتقه فی مرضه اعظم لاجره او یترکه مملوکا فقال | عن |  |

### Chain 356 · `faqih-3554` — CLARIFIED
- Transmitters (student → teacher): محمد بن عيسى العبيدي → الفضل بن المبارك → أبو الحسن علي بن محمد ع (مكاتبة)
- Corrected isnad (Arabic): «رَوَى مُحَمَّدُ بْنُ عِيسَى الْعُبَيْدِيُّ عَنِ الْفَضْلِ بْنِ الْمُبَارَكِ‌ أَنَّهُ كَتَبَ إِلَى أَبِي الْحَسَنِ عَلِيِّ بْنِ مُحَمَّدٍ ع»
- Isnad ends / matn begins at: "فِي رَجُلٍ لَهُ مَمْلُوكٌ فَمَرِضَ أَ يُعْتِقُهُ فِي مَرَضِهِ"
- Mursal opening: al-Ṣadūq → محمد بن عيسى العبيدي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name.

---

### Chain 357 · `faqih-3555`
- **Location:** vol. 3, p. 154 · seq 3567 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى مُحَمَّدُ بْنُ عِيسَى الْعُبَيْدِيُّ عَنِ الْفَضْلِ بْنِ الْمُبَارَكِ الْبَصْرِيِّ عَنْ أَبِيهِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ لَهُ جُعِلْتُ فِدَاكَ الرَّجُلُ يَجِبُ عَلَيْهِ عِتْقُ رَقَبَةٍ مُؤْمِنَةٍ فَلَا يَجِدُهَا كَيْفَ يَصْنَعُ فَقَالَ عَلَيْكُمْ بِالْأَطْفَالِ فَأَعْتِقُوهُمْ فَإِنْ خَرَجَتْ مُؤْمِنَةً فَذَاكَ وَ إِنْ لَمْ تَخْرُجْ مُؤْمِنَةً فَلَيْسَ عَلَيْكُمْ شَيْ‌ءٌ[1].
- **Isnad as currently extracted:**
  > رَوَى مُحَمَّدُ بْنُ عِيسَى الْعُبَيْدِيُّ عَنِ الْفَضْلِ بْنِ الْمُبَارَكِ الْبَصْرِيِّ عَنْ أَبِيهِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن عیسی العبیدی | روی |  |
  | 1 | named_narrator | الفضل بن المبارک البصری | عن |  |
  | 2 | pronoun_relation | ابیه | عن | father |
  | 3 | imam | ابی عبد الله ع | عن |  |

### Chain 357 · `faqih-3555` — CLARIFIED
- Transmitters (student → teacher): محمد بن عيسي العبيدي → الفضل بن المبارك البصري → أبيه (غير مسمّى في النص) → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى مُحَمَّدُ بْنُ عِيسَى الْعُبَيْدِيُّ عَنِ الْفَضْلِ بْنِ الْمُبَارَكِ الْبَصْرِيِّ عَنْ أَبِيهِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ جُعِلْتُ فِدَاكَ الرَّجُلُ يَجِبُ عَلَيْهِ عِتْقُ رَقَبَةٍ"
- Mursal opening: al-Ṣadūq → محمد بن عيسي العبيدي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 358 · `faqih-3556`
- **Location:** vol. 3, p. 154 · seq 3568 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى مُعَاوِيَةُ بْنُ مَيْسَرَةَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنِ الرَّجُلِ يَبِيعُ عَبْدَهُ بِنُقْصَانٍ مِنْ ثَمَنِهِ لِيُعْتَقَ فَقَالَ لَهُ الْعَبْدُ فِيمَا بَيْنَهُمَا لَكَ عَلَيَّ كَذَا وَ كَذَا أَ لَهُ أَنْ يَأْخُذَهُ مِنْهُ‌[2] قَالَ يَأْخُذُهُ مِنْهُ عَفْواً وَ يَسْأَلُهُ إِيَّاهُ فِي عَفْوٍ فَإِنْ أَبَى فَلْيَدَعْهُ‌[3].
- **Isnad as currently extracted:**
  > رَوَى مُعَاوِيَةُ بْنُ مَيْسَرَةَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنِ الرَّجُلِ يَبِيعُ عَبْدَهُ بِنُقْصَانٍ مِنْ ثَمَنِهِ لِيُعْتَقَ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن میسرة | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 358 · `faqih-3556` — CLARIFIED
- Transmitters (student → teacher): معاوية بن ميسرة → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى مُعَاوِيَةُ بْنُ مَيْسَرَةَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الرَّجُلِ يَبِيعُ عَبْدَهُ بِنُقْصَانٍ مِنْ ثَمَنِهِ لِيُعْتَقَ"
- Mursal opening: al-Ṣadūq → معاوية بن ميسرة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 359 · `faqih-3559`
- **Location:** vol. 3, p. 155 · seq 3571 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ هِشَامِ بْنِ سَالِمٍ عَنْ أَبِي الْوَرْدِ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنْ مَمْلُوكٍ نَصْرَانِيٍّ لِرَجُلٍ مُسْلِمٍ عَلَيْهِ جِزْيَةٌ قَالَ نَعَمْ إِنَّمَا هُوَ مَالِكُهُ يَفْتَدِيهِ‌[4] إِذَا أُخِذَ يُؤَدِّي عَنْهُ.
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ هِشَامِ بْنِ سَالِمٍ عَنْ أَبِي الْوَرْدِ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنْ مَمْلُوكٍ نَصْرَانِيٍّ لِرَجُلٍ مُسْلِمٍ عَلَيْهِ جِزْيَةٌ قَالَ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | هشام بن سالم | عن |  |
  | 2 | named_narrator | ابی الورد | عن |  |
  | 3 | imam | ابی جعفر ع | عن |  |

### Chain 359 · `faqih-3559` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → هشام بن سالم → ابي الورد → ابي جعفر ع
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ هِشَامِ بْنِ سَالِمٍ عَنْ أَبِي الْوَرْدِ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ مَمْلُوكٍ نَصْرَانِيٍّ لِرَجُلٍ مُسْلِمٍ عَلَيْهِ جِزْيَةٌ قَالَ"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 360 · `faqih-3580`
- **Location:** vol. 3, p. 160 · seq 3592 · chain 1
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رُوِيَ عَنْ عَلِيِّ بْنِ جَعْفَرٍ[3] عَنْ أَخِيهِ مُوسَى بْنِ جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنِ النُّثَارِ مِنَ السُّكَّرِ وَ اللَّوْزِ وَ أَشْبَاهِهِ أَ يَحِلُّ أَكْلُهُ فَقَالَ يُكْرَهُ كُلُّ مَالٍ يُنْتَهَبُ‌[4].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ عَلِيِّ بْنِ جَعْفَرٍ[3] عَنْ أَخِيهِ مُوسَى بْنِ جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنِ النُّثَارِ مِنَ السُّكَّرِ وَ اللَّوْزِ وَ أَشْبَاهِهِ أَ يَحِلُّ أَكْلُهُ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن علی بن جعفر | روی |  |
  | 1 | imam | اخیه موسی بن جعفر ع | عن |  |

### Chain 360 · `faqih-3580` — CLARIFIED
- Transmitters (student → teacher): علي بن جعفر → اخيه موسي بن جعفر ع
- Corrected isnad (Arabic): «رُوِيَ عَنْ عَلِيِّ بْنِ جَعْفَرٍ[3] عَنْ أَخِيهِ مُوسَى بْنِ جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ النُّثَارِ مِنَ السُّكَّرِ وَ اللَّوْزِ وَ أَشْبَاهِهِ"
- Mursal opening: al-Ṣadūq → علي بن جعفر; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 361 · `faqih-3580`
- **Location:** vol. 3, p. 160 · seq 3592 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رُوِيَ عَنْ عَلِيِّ بْنِ جَعْفَرٍ[3] عَنْ أَخِيهِ مُوسَى بْنِ جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنِ النُّثَارِ مِنَ السُّكَّرِ وَ اللَّوْزِ وَ أَشْبَاهِهِ أَ يَحِلُّ أَكْلُهُ فَقَالَ يُكْرَهُ كُلُّ مَالٍ يُنْتَهَبُ‌[4].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ عَلِيِّ بْنِ جَعْفَرٍ[3] عَنْ أَخِيهِ مُوسَى بْنِ جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنِ النُّثَارِ مِنَ السُّكَّرِ وَ اللَّوْزِ وَ أَشْبَاهِهِ أَ يَحِلُّ أَكْلُهُ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن علی بن جعفر | روی |  |
  | 1 | imam | اخیه موسی بن جعفر ع | عن |  |

### Chain 361 · `faqih-3580` — CLARIFIED
- Transmitters (student → teacher): علي بن جعفر → اخيه موسي بن جعفر ع
- Corrected isnad (Arabic): «رُوِيَ عَنْ عَلِيِّ بْنِ جَعْفَرٍ[3] عَنْ أَخِيهِ مُوسَى بْنِ جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ النُّثَارِ مِنَ السُّكَّرِ وَ اللَّوْزِ وَ أَشْبَاهِهِ"
- Mursal opening: al-Ṣadūq → علي بن جعفر; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 362 · `faqih-3580`
- **Location:** vol. 3, p. 160 · seq 3592 · chain 3
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رُوِيَ عَنْ عَلِيِّ بْنِ جَعْفَرٍ[3] عَنْ أَخِيهِ مُوسَى بْنِ جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنِ النُّثَارِ مِنَ السُّكَّرِ وَ اللَّوْزِ وَ أَشْبَاهِهِ أَ يَحِلُّ أَكْلُهُ فَقَالَ يُكْرَهُ كُلُّ مَالٍ يُنْتَهَبُ‌[4].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ عَلِيِّ بْنِ جَعْفَرٍ[3] عَنْ أَخِيهِ مُوسَى بْنِ جَعْفَرٍ ع قَالَ‌ سَأَلْتُهُ عَنِ النُّثَارِ مِنَ السُّكَّرِ وَ اللَّوْزِ وَ أَشْبَاهِهِ أَ يَحِلُّ أَكْلُهُ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن علی بن جعفر | روی |  |
  | 1 | imam | اخیه موسی بن جعفر ع | عن |  |

### Chain 362 · `faqih-3580` — CLARIFIED
- Transmitters (student → teacher): علي بن جعفر → اخيه موسي بن جعفر ع
- Corrected isnad (Arabic): «رُوِيَ عَنْ عَلِيِّ بْنِ جَعْفَرٍ[3] عَنْ أَخِيهِ مُوسَى بْنِ جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ النُّثَارِ مِنَ السُّكَّرِ وَ اللَّوْزِ وَ أَشْبَاهِهِ"
- Mursal opening: al-Ṣadūq → علي بن جعفر; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The tokenizer produced duplicate expanded entries for the same textual route; this block does not invent a second route.

---

### Chain 363 · `faqih-3581`
- **Location:** vol. 3, p. 160 · seq 3593 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى عَمْرُو بْنُ شِمْرٍ عَنْ جَابِرٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ لَمَّا أَنْزَلَ اللَّهُ تَبَارَكَ وَ تَعَالَى- إِنَّمَا الْخَمْرُ وَ الْمَيْسِرُ وَ الْأَنْصابُ وَ الْأَزْلامُ رِجْسٌ مِنْ عَمَلِ الشَّيْطانِ فَاجْتَنِبُوهُ‌ قِيلَ يَا رَسُولَ اللَّهِ مَا الْمَيْسِرُ قَالَ كُلُّ مَا تُقُومِرَ بِهِ حَتَّى الْكِعَابُ وَ الْجَوْزُ-
قِيلَ فَمَا الْأَنْصَابُ قَالَ مَا ذَبَحُوا لآِلِهَتِهِمْ‌[1] قِيلَ فَمَا الْأَزْلَامُ قَالَ قِدَاحُهُمُ الَّتِي يَسْتَقْسِمُونَ بِهَا[2].
- **Isnad as currently extracted:**
  > رَوَى عَمْرُو بْنُ شِمْرٍ عَنْ جَابِرٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ لَمَّا أَنْزَلَ اللَّهُ تَبَارَكَ وَ تَعَالَى- إِنَّمَا الْخَمْرُ وَ الْمَيْسِرُ وَ الْأَنْصابُ وَ الْأَزْلامُ رِجْسٌ مِنْ عَمَلِ الشَّيْطانِ فَاجْتَنِبُوهُ‌ قِيلَ يَا رَسُولَ اللَّهِ مَا الْمَيْسِرُ قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عمرو بن شمر | روی |  |
  | 1 | named_narrator | جابر | عن |  |
  | 2 | imam | ابی جعفر ع | عن |  |

### Chain 363 · `faqih-3581` — CLARIFIED
- Transmitters (student → teacher): عمرو بن شمر → جابر → ابي جعفر ع
- Corrected isnad (Arabic): «رَوَى عَمْرُو بْنُ شِمْرٍ عَنْ جَابِرٍ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "لَمَّا أَنْزَلَ اللَّهُ تَبَارَكَ وَ تَعَالَى- إِنَّمَا الْخَمْرُ وَ"
- Mursal opening: al-Ṣadūq → عمرو بن شمر; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 364 · `faqih-3588`
- **Location:** vol. 3, p. 162 · seq 3600 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى شَرِيفُ بْنُ سَابِقٍ التَّفْلِيسِيُّ عَنِ الْفَضْلِ بْنِ أَبِي قُرَّةَ السَّمَنْدِيِّ الْكُوفِيِّ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّ أَمِيرَ الْمُؤْمِنِينَ ع قَالَ‌ أَوْحَى اللَّهُ عَزَّ وَ جَلَّ إِلَى دَاوُدَ ع أَنَّكَ نِعْمَ الْعَبْدُ لَوْ لَا أَنَّكَ تَأْكُلُ مِنْ بَيْتِ الْمَالِ وَ لَا تَعْمَلُ بِيَدِكَ شَيْئاً قَالَ فَبَكَى دَاوُدُ ع فَأَوْحَى اللَّهُ عَزَّ وَ جَلَّ إِلَى الْحَدِيدِ أَنْ لِنْ لِعَبْدِي دَاوُدَ فَلَانَ‌
فَأَلَانَ اللَّهُ تَعَالَى لَهُ الْحَدِيدَ[1] فَكَانَ يَعْمَلُ كُلَّ يَوْمٍ دِرْعاً فَيَبِيعُهَا بِأَلْفِ دِرْهَمٍ فَعَمِلَ ع ثَلَاثَمِائَةٍ وَ سِتِّينَ دِرْعاً فَبَاعَهَا بِثَلَاثِمِائَةٍ وَ سِتِّينَ أَلْفاً وَ اسْتَغْنَى عَنْ بَيْتِ الْمَالِ.
- **Isnad as currently extracted:**
  > رَوَى شَرِيفُ بْنُ سَابِقٍ التَّفْلِيسِيُّ عَنِ الْفَضْلِ بْنِ أَبِي قُرَّةَ السَّمَنْدِيِّ الْكُوفِيِّ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّ أَمِيرَ الْمُؤْمِنِينَ ع قَالَ‌ أَوْحَى اللَّهُ عَزَّ وَ جَلَّ إِلَى دَاوُدَ ع أَنَّكَ نِعْمَ الْعَبْدُ لَوْ لَا أَنَّكَ تَأْكُلُ مِنْ بَيْتِ الْمَالِ وَ لَا تَعْمَلُ بِيَدِكَ شَيْئاً قَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | شریف بن سابق التفلیسی | روی |  |
  | 1 | named_narrator | الفضل بن ابی قرة السمندی الکوفی | عن |  |
  | 2 | imam | ابی عبد الله ع ان امیر المؤمنین ع | عن |  |

### Chain 364 · `faqih-3588` — CLARIFIED
- Transmitters (student → teacher): شريف بن سابق التفليسي → الفضل بن أبي قرة السمندي الكوفي → أبو عبد الله ع
- Corrected isnad (Arabic): «رَوَى شَرِيفُ بْنُ سَابِقٍ التَّفْلِيسِيُّ عَنِ الْفَضْلِ بْنِ أَبِي قُرَّةَ السَّمَنْدِيِّ الْكُوفِيِّ عَنْ أَبِي عَبْدِ اللَّهِ ع»
- Isnad ends / matn begins at: "أَنَّ أَمِيرَ الْمُؤْمِنِينَ ع قَالَ‌ أَوْحَى اللَّهُ عَزَّ وَ"
- Mursal opening: al-Ṣadūq → شريف بن سابق التفليسي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 365 · `faqih-3591`
- **Location:** vol. 3, p. 163 · seq 3603 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رُوِيَ عَنِ الْفَضْلِ بْنِ أَبِي قُرَّةَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ لَهُ إِنَّ هَؤُلَاءِ يَقُولُونَ إِنَّ كَسْبَ الْمُعَلِّمِ سُحْتٌ فَقَالَ كَذَبَ أَعْدَاءُ اللَّهِ إِنَّمَا أَرَادُوا أَنْ لَا يُعَلِّمُوا أَوْلَادَهُمُ الْقُرْآنَ لَوْ أَنَّ رَجُلًا أَعْطَى الْمُعَلِّمَ دِيَةَ وَلَدِهِ كَانَ لِلْمُعَلِّمِ مُبَاحاً.
- **Isnad as currently extracted:**
  > رُوِيَ عَنِ الْفَضْلِ بْنِ أَبِي قُرَّةَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن الفضل بن ابی قرة | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 365 · `faqih-3591` — CLARIFIED
- Transmitters (student → teacher): الفضل بن ابي قرة → ابي عبد الله ع
- Corrected isnad (Arabic): «رُوِيَ عَنِ الْفَضْلِ بْنِ أَبِي قُرَّةَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ إِنَّ هَؤُلَاءِ يَقُولُونَ إِنَّ كَسْبَ الْمُعَلِّمِ سُحْتٌ"
- Mursal opening: al-Ṣadūq → الفضل بن ابي قرة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 366 · `faqih-3593`
- **Location:** vol. 3, p. 164 · seq 3605 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ عَبْدِ الْحَمِيدِ بْنِ عَوَّاضٍ الطَّائِيِّ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنِّي اتَّخَذْتُ رَحًى فِيهَا مَجْلِسِي وَ يَجْلِسُ إِلَيَّ فِيهَا أَصْحَابِي قَالَ ذَاكَ رِفْقُ اللَّهِ عَزَّ وَ جَلَ‌[1].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ عَبْدِ الْحَمِيدِ بْنِ عَوَّاضٍ الطَّائِيِّ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن عبد الحمید بن عواض الطائی | روی |  |

### Chain 366 · `faqih-3593` — CLARIFIED
- Transmitters (student → teacher): عبد الحميد بن عواض الطائي
- Corrected isnad (Arabic): «رُوِيَ عَنْ عَبْدِ الْحَمِيدِ بْنِ عَوَّاضٍ الطَّائِيِّ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنِّي اتَّخَذْتُ رَحًى فِيهَا"
- Mursal opening: al-Ṣadūq → عبد الحميد بن عواض الطائي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 367 · `faqih-3600`
- **Location:** vol. 3, p. 165 · seq 3612 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنِ الْفُضَيْلِ بْنِ يَسَارٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنِّي قَدْ تَرَكْتُ التِّجَارَةَ فَقَالَ لَا تَفْعَلْ افْتَحْ بَابَكَ وَ ابْسُطْ بِسَاطَكَ وَ اسْتَرْزِقِ اللَّهَ رَبَّكَ‌[2].
- **Isnad as currently extracted:**
  > رُوِيَ عَنِ الْفُضَيْلِ بْنِ يَسَارٍ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن الفضیل بن یسار | روی |  |

### Chain 367 · `faqih-3600` — CLARIFIED
- Transmitters (student → teacher): الفضيل بن يسار → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنِ الْفُضَيْلِ بْنِ يَسَارٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنِّي قَدْ تَرَكْتُ التِّجَارَةَ"
- Mursal opening: al-Ṣadūq → الفضيل بن يسار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 368 · `faqih-3621`
- **Location:** vol. 3, p. 168 · seq 3633 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى الْوَلِيدُ بْنُ صَبِيحٍ عَنِ الصَّادِقِ ع أَنَّهُ قَالَ‌ ثَلَاثَةٌ يَدْعُونَ فَلَا يُسْتَجَابُ لَهُمْ أَوْ قَالَ يُرَدُّ عَلَيْهِمْ دُعَاؤُهُمْ‌[1] رَجُلٌ كَانَ لَهُ مَالٌ كَثِيرٌ يَبْلُغُ ثَلَاثِينَ أَلْفاً أَوْ أَرْبَعِينَ أَلْفاً فَأَنْفَقَهُ فِي وُجُوهِهِ فَيَقُولُ اللَّهُمَّ ارْزُقْنِي فَيَقُولُ اللَّهُ تَعَالَى أَ لَمْ أَرْزُقْكَ وَ رَجُلٌ أَمْسَكَ عَنِ الطَّلَبِ‌[2] فَيَقُولُ اللَّهُمَّ ارْزُقْنِي فَيَقُولُ اللَّهُ تَعَالَى أَ لَمْ أَجْعَلْ لَكَ السَّبِيلَ إِلَى الطَّلَبِ وَ رَجُلٌ كَانَتْ عِنْدَهُ امْرَأَةٌ فَقَالَ اللَّهُمَّ فَرِّقْ بَيْنِي وَ بَيْنَهَا فَيَقُولُ اللَّهُ عَزَّ وَ جَلَّ أَ لَمْ أَجْعَلْ ذَلِكَ إِلَيْكَ.
- **Isnad as currently extracted:**
  > رَوَى الْوَلِيدُ بْنُ صَبِيحٍ عَنِ الصَّادِقِ ع أَنَّهُ قَالَ‌ ثَلَاثَةٌ يَدْعُونَ فَلَا يُسْتَجَابُ لَهُمْ أَوْ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الولید بن صبیح | روی |  |
  | 1 | imam | الصادق ع | عن |  |

### Chain 368 · `faqih-3621` — CLARIFIED
- Transmitters (student → teacher): الوليد بن صبيح → الصادق ع
- Corrected isnad (Arabic): «رَوَى الْوَلِيدُ بْنُ صَبِيحٍ عَنِ الصَّادِقِ ع أَنَّهُ قَالَ‌»
- Isnad ends / matn begins at: "ثَلَاثَةٌ يَدْعُونَ فَلَا يُسْتَجَابُ لَهُمْ أَوْ قَالَ يُرَدُّ عَلَيْهِمْ"
- Mursal opening: al-Ṣadūq → الوليد بن صبيح; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 369 · `faqih-3636`
- **Location:** vol. 3, p. 170 · seq 3648 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى زُرَارَةُ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ مَا يُخَلِّفُ الرَّجُلُ بَعْدَهُ شَيْئاً أَشَدَّ عَلَيْهِ مِنَ الْمَالِ الصَّامِتِ‌[1] قَالَ قُلْتُ لَهُ كَيْفَ يَصْنَعُ قَالَ يَضَعُهُ فِي الْحَائِطِ وَ الْبُسْتَانِ وَ الدَّارِ.
- **Isnad as currently extracted:**
  > رَوَى زُرَارَةُ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ مَا يُخَلِّفُ الرَّجُلُ بَعْدَهُ شَيْئاً أَشَدَّ عَلَيْهِ مِنَ الْمَالِ الصَّامِتِ‌[1] قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | زرارة | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 369 · `faqih-3636` — CLARIFIED
- Transmitters (student → teacher): زرارة → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى زُرَارَةُ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "مَا يُخَلِّفُ الرَّجُلُ بَعْدَهُ شَيْئاً أَشَدَّ عَلَيْهِ مِنَ الْمَالِ"
- Mursal opening: al-Ṣadūq → زرارة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 370 · `faqih-3639`
- **Location:** vol. 3, p. 170 · seq 3651 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ كَسْبِ الْحَجَّامِ فَقَالَ لَا بَأْسَ بِهِ‌[4].
- **Isnad as currently extracted:**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ كَسْبِ الْحَجَّامِ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن عمار | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 370 · `faqih-3639` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ كَسْبِ الْحَجَّامِ فَقَالَ لَا بَأْسَ بِهِ‌[4]."
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 371 · `faqih-3645`
- **Location:** vol. 3, p. 172 · seq 3657 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنِ الْحُسَيْنِ بْنِ الْمُخْتَارِ الْقَلَانِسِيِّ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّا نَعْمَلُ الْقَلَانِسَ فَنَجْعَلُ فِيهَا الْقُطْنَ الْعَتِيقَ فَنَبِيعُهَا وَ لَا نُبَيِّنُ لَهُمْ مَا فِيهَا فَقَالَ‌
إِنِّي لَأُحِبُّ لَكَ أَنْ تُبَيِّنَ لَهُمْ مَا فِيهَا[1].
- **Isnad as currently extracted:**
  > رُوِيَ عَنِ الْحُسَيْنِ بْنِ الْمُخْتَارِ الْقَلَانِسِيِّ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن الحسین بن المختار القلانسی | روی |  |

### Chain 371 · `faqih-3645` — CLARIFIED
- Transmitters (student → teacher): الحسين بن المختار القلانسي → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنِ الْحُسَيْنِ بْنِ الْمُخْتَارِ الْقَلَانِسِيِّ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّا نَعْمَلُ الْقَلَانِسَ فَنَجْعَلُ"
- Mursal opening: al-Ṣadūq → الحسين بن المختار القلانسي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 372 · `faqih-3648`
- **Location:** vol. 3, p. 173 · seq 3660 · chain 1
- **Flags:** `no_imam_terminal`, `suspicious_token`
- **Full report (Arabic):**
  > كَتَبَ مُحَمَّدُ بْنُ عِيسَى بْنِ عُبَيْدٍ الْيَقْطِينِيُّ إِلَى أَبِي الْحَسَنِ عَلِيِّ بْنِ مُحَمَّدٍ الْعَسْكَرِيِّ ع‌ فِي رَجُلٍ دَفَعَ ابْنَهُ إِلَى رَجُلٍ وَ سَلَّمَهُ مِنْهُ سَنَةً بِأُجْرَةٍ مَعْلُومَةٍ لِيَخِيطَ لَهُ ثُمَّ جَاءَ رَجُلٌ آخَرُ فَقَالَ لَهُ سَلِّمْ ابْنَكَ مِنِّي سَنَةً بِزِيَادَةٍ هَلْ لَهُ الْخِيَارُ فِي ذَلِكَ وَ هَلْ يَجُوزُ لَهُ أَنْ يَفْسَخَ مَا وَافَقَ عَلَيْهِ الْأَوَّلُ أَمْ لَا فَكَتَبَ ع بِخَطِّهِ يَجِبُ عَلَيْهِ الْوَفَاءُ لِلْأَوَّلِ مَا لَمْ يَعْرِضْ لِابْنِهِ مَرَضٌ أَوْ ضَعْفٌ‌[3].
- **Isnad as currently extracted:**
  > كَتَبَ مُحَمَّدُ بْنُ عِيسَى بْنِ عُبَيْدٍ الْيَقْطِينِيُّ إِلَى أَبِي الْحَسَنِ عَلِيِّ بْنِ مُحَمَّدٍ الْعَسْكَرِيِّ ع‌ فِي رَجُلٍ دَفَعَ ابْنَهُ إِلَى رَجُلٍ وَ سَلَّمَهُ مِنْهُ سَنَةً بِأُجْرَةٍ مَعْلُومَةٍ لِيَخِيطَ لَهُ ثُمَّ جَاءَ رَجُلٌ آخَرُ فَقَالَ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | کتب محمد بن عیسی بن عبید الیقطینی الی ابی الحسن علی بن محمد العسکری ع فی رجل دفع ابنه الی رجل و سلمه منه سنة باجرة معلومة لیخیط له ثم جاء رجل اخر فقال |  |  |

### Chain 372 · `faqih-3648` — CLARIFIED
- Transmitters (student → teacher): محمد بن عيسى بن عبيد اليقطيني → أبو الحسن علي بن محمد العسكري ع (مكاتبة)
- Corrected isnad (Arabic): «كَتَبَ مُحَمَّدُ بْنُ عِيسَى بْنِ عُبَيْدٍ الْيَقْطِينِيُّ إِلَى أَبِي الْحَسَنِ عَلِيِّ بْنِ مُحَمَّدٍ الْعَسْكَرِيِّ ع‌»
- Isnad ends / matn begins at: "فِي رَجُلٍ دَفَعَ ابْنَهُ إِلَى رَجُلٍ وَ سَلَّمَهُ مِنْهُ"
- Mursal opening: al-Ṣadūq → محمد بن عيسى بن عبيد اليقطيني; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. The suspicious token was matn spill or an epistolary/narrative formula, not an additional narrator name.

---

### Chain 373 · `faqih-3649`
- **Location:** vol. 3, p. 173 · seq 3661 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى مُحَمَّدُ بْنُ خَالِدٍ الْبَرْقِيُّ عَنْ مُحَمَّدِ بْنِ سِنَانٍ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ سَأَلْتُهُ عَنِ الْإِجَارَةِ فَقَالَ صَالِحٌ لَا بَأْسَ بِهَا إِذَا نَصَحَ قَدْرَ طَاقَتِهِ‌[4] قَدْ آجَرَ
- **Isnad as currently extracted:**
  > رَوَى مُحَمَّدُ بْنُ خَالِدٍ الْبَرْقِيُّ عَنْ مُحَمَّدِ بْنِ سِنَانٍ عَنْ أَبِي الْحَسَنِ ع قَالَ‌ سَأَلْتُهُ عَنِ الْإِجَارَةِ فَقَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن خالد البرقی | روی |  |
  | 1 | named_narrator | محمد بن سنان | عن |  |
  | 2 | imam | ابی الحسن ع | عن |  |

### Chain 373 · `faqih-3649` — CLARIFIED
- Transmitters (student → teacher): محمد بن خالد البرقي → محمد بن سنان → ابي الحسن ع
- Corrected isnad (Arabic): «رَوَى مُحَمَّدُ بْنُ خَالِدٍ الْبَرْقِيُّ عَنْ مُحَمَّدِ بْنِ سِنَانٍ عَنْ أَبِي الْحَسَنِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنِ الْإِجَارَةِ فَقَالَ صَالِحٌ لَا بَأْسَ بِهَا إِذَا"
- Mursal opening: al-Ṣadūq → محمد بن خالد البرقي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 374 · `faqih-3650`
- **Location:** vol. 3, p. 174 · seq 3662 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى مُحَمَّدُ بْنُ عَمْرِو بْنِ أَبِي الْمِقْدَامِ عَنْ عَمَّارٍ السَّابَاطِيِّ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الرَّجُلُ يَتَّجِرُ وَ إِنْ هُوَ آجَرَ نَفْسَهُ أُعْطِيَ أَكْثَرَ مِمَّا يُصِيبُ فِي تِجَارَتِهِ قَالَ لَا يُؤَاجِرْ نَفْسَهُ وَ لَكِنْ يَسْتَرْزِقُ اللَّهَ تَعَالَى وَ يَتَّجِرُ فَإِنَّهُ إِذَا آجَرَ نَفْسَهُ حَظَرَ عَلَى نَفْسِهِ الرِّزْقَ‌[2].
- **Isnad as currently extracted:**
  > رَوَى مُحَمَّدُ بْنُ عَمْرِو بْنِ أَبِي الْمِقْدَامِ عَنْ عَمَّارٍ السَّابَاطِيِّ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | محمد بن عمرو بن ابی المقدام | روی |  |
  | 1 | named_narrator | عمار الساباطی | عن |  |

### Chain 374 · `faqih-3650` — CLARIFIED
- Transmitters (student → teacher): محمد بن عمرو بن ابي المقدام → عمار الساباطي
- Corrected isnad (Arabic): «رَوَى مُحَمَّدُ بْنُ عَمْرِو بْنِ أَبِي الْمِقْدَامِ عَنْ عَمَّارٍ السَّابَاطِيِّ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الرَّجُلُ يَتَّجِرُ وَ إِنْ"
- Mursal opening: al-Ṣadūq → محمد بن عمرو بن ابي المقدام; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 375 · `faqih-3652`
- **Location:** vol. 3, p. 174 · seq 3664 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى هَارُونُ بْنُ حَمْزَةَ الْغَنَوِيُّ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ اسْتَأْجَرَ أَجِيراً فَلَمْ يَأْمَنْ أَحَدُهُمَا صَاحِبَهُ فَوَضَعَ الْأَجْرَ عَلَى يَدَيْ رَجُلٍ فَهَلَكَ ذَلِكَ الرَّجُلُ وَ لَمْ يَدَعْ وَفَاءً[4] وَ اسْتُهْلِكَ الْأَجْرُ فَقَالَ الْمُسْتَأْجِرُ ضَامِنٌ لِأَجْرِ الْأَجِيرِ حَتَّى يَقْضِيَ إِلَّا أَنْ يَكُونَ الْأَجِيرُ دَعَاهُ إِلَى ذَلِكَ فَرَضِيَ بِهِ فَإِنْ فَعَلَ فَحَقُّهُ حَيْثُ وَضَعَهُ وَ رَضِيَ بِهِ.
- **Isnad as currently extracted:**
  > رَوَى هَارُونُ بْنُ حَمْزَةَ الْغَنَوِيُّ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ اسْتَأْجَرَ أَجِيراً فَلَمْ يَأْمَنْ أَحَدُهُمَا صَاحِبَهُ فَوَضَعَ الْأَجْرَ عَلَى يَدَيْ رَجُلٍ فَهَلَكَ ذَلِكَ الرَّجُلُ وَ لَمْ يَدَعْ وَفَاءً[4] وَ اسْتُهْلِكَ الْأَجْرُ فَقَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | هارون بن حمزة الغنوی | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 375 · `faqih-3652` — CLARIFIED
- Transmitters (student → teacher): هارون بن حمزة الغنوي → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى هَارُونُ بْنُ حَمْزَةَ الْغَنَوِيُّ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ اسْتَأْجَرَ أَجِيراً فَلَمْ يَأْمَنْ أَحَدُهُمَا صَاحِبَهُ"
- Mursal opening: al-Ṣadūq → هارون بن حمزة الغنوي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 376 · `faqih-3655`
- **Location:** vol. 3, p. 175 · seq 3667 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ الْحَسَنِ بْنِ رِبَاطٍ عَنْ أَبِي سَارَةَ عَنْ هِنْدٍ السَّرَّاجِ قَالَ‌ قُلْتُ لِأَبِي جَعْفَرٍ ع أَصْلَحَكَ اللَّهُ إِنِّي كُنْتُ أَحْمِلُ السِّلَاحَ إِلَى أَهْلِ الشَّامِ فَأَبِيعُهُ مِنْهُمْ فَلَمَّا عَرَّفَنِيَ اللَّهُ هَذَا الْأَمْرَ ضِقْتُ بِذَلِكَ السِّلَاحِ قُلْتُ لَا أَحْمِلُ إِلَى أَعْدَاءِ اللَّهِ قَالَ احْمِلْ إِلَيْهِمْ وَ بِعْهُمْ فَإِنَّ اللَّهَ تَعَالَى يَدْفَعُ بِهِمْ عَدُوَّنَا وَ عَدُوَّكُمْ يَعْنِي الرُّومَ قَالَ فَإِذَا كَانَتِ الْحَرْبُ بَيْنَنَا وَ بَيْنَهُمْ فَمَنْ حَمَلَ إِلَى عَدُوِّنَا سِلَاحاً يَسْتَعِينُونَ بِهِ عَلَيْنَا فَهُوَ مُشْرِكٌ‌[2].
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ الْحَسَنِ بْنِ رِبَاطٍ عَنْ أَبِي سَارَةَ عَنْ هِنْدٍ السَّرَّاجِ قَالَ‌ قُلْتُ
- **Current node split (4 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | علی بن الحسن بن رباط | عن |  |
  | 2 | named_narrator | ابی سارة | عن |  |
  | 3 | named_narrator | هند السراج | عن |  |

### Chain 376 · `faqih-3655` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → علي بن الحسن بن رباط → ابي سارة → هند السراج → ابي جعفر ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ عَلِيِّ بْنِ الْحَسَنِ بْنِ رِبَاطٍ عَنْ أَبِي سَارَةَ عَنْ هِنْدٍ السَّرَّاجِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي جَعْفَرٍ ع أَصْلَحَكَ اللَّهُ إِنِّي كُنْتُ أَحْمِلُ"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 377 · `faqih-3656`
- **Location:** vol. 3, p. 175 · seq 3668 · chain 2
- **Flags:** `co_narrator_expanded`, `expanded`, `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ أَبِي وَلَّادٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع مَا تَرَى فِي الرَّجُلِ يَلِي أَعْمَالَ السُّلْطَانِ لَيْسَ لَهُ مَكْسَبٌ إِلَّا مِنْ أَعْمَالِهِمْ وَ أَنَا أَمُرُّ بِهِ وَ أَنْزِلُ عَلَيْهِ فَيُضِيفُنِي وَ يُحْسِنُ إِلَيَّ وَ رُبَّمَا أَمَرَ لِي بِالدَّرَاهِمِ وَ الْكِسْوَةِ وَ قَدْ ضَاقَ صَدْرِي مِنْ ذَلِكَ فَقَالَ لِي خُذْ وَ كُلْ مِنْهُ فَلَكَ الْمَهْنَأُ وَ عَلَيْهِ الْوِزْرُ[3].
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ أَبِي وَلَّادٍ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | لاد | عن |  |

### Chain 377 · `faqih-3656` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → لاد → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ أَبِي وَلَّادٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع مَا تَرَى فِي الرَّجُلِ"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula. This block records the route represented by this expanded chain entry; the corrected Arabic keeps the source’s joint/co-narrator wording verbatim.

---

### Chain 378 · `faqih-3662`
- **Location:** vol. 3, p. 176 · seq 3674 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ لِابْنِهِ مَالٌ فَاحْتَاجَ إِلَيْهِ الْأَبُ قَالَ يَأْكُلُ مِنْهُ وَ أَمَّا الْأُمُّ فَلَا تَأْخُذْ مِنْهُ إِلَّا قَرْضاً عَلَى نَفْسِهَا[5].
- **Isnad as currently extracted:**
  > رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌ سَأَلْتُهُ عَنْ رَجُلٍ لِابْنِهِ مَالٌ فَاحْتَاجَ إِلَيْهِ الْأَبُ قَالَ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حریز | روی |  |
  | 1 | named_narrator | محمد بن مسلم | عن |  |

### Chain 378 · `faqih-3662` — CLARIFIED
- Transmitters (student → teacher): حريز → محمد بن مسلم → أبو عبد الله ع
- Corrected isnad (Arabic): «رَوَى حَرِيزٌ عَنْ مُحَمَّدِ بْنِ مُسْلِمٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُهُ عَنْ رَجُلٍ لِابْنِهِ مَالٌ فَاحْتَاجَ إِلَيْهِ الْأَبُ قَالَ"
- Mursal opening: al-Ṣadūq → حريز; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The full parallel reads Ḥarīz → Muḥammad b. Muslim → Abū ʿAbd Allāh and preserves the same question. Sources: [al-Tahdhīb, full route](https://ito.lib.eshia.ir/86298/6/344); [al-Istibṣār, vol. 3, p. 49](https://ar.lib.eshia.ir/11002/3/49).
---

### Chain 379 · `faqih-3663`
- **Location:** vol. 3, p. 177 · seq 3675 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى الْحُسَيْنُ بْنُ أَبِي الْعَلَاءِ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع مَا يَحِلُّ لِلرَّجُلِ مِنْ مَالِ وُلْدِهِ قَالَ قُوتُهُ بِغَيْرِ سَرَفٍ إِذَا اضْطُرَّ إِلَيْهِ قَالَ فَقُلْتُ لَهُ فَقَوْلُ رَسُولِ اللَّهِ ص أَنْتَ وَ مَالُكَ لِأَبِيكَ فَقَالَ إِنَّمَا جَاءَ بِأَبِيهِ إِلَى رَسُولِ اللَّهِ ص فَقَالَ يَا رَسُولَ اللَّهِ هَذَا أَبِي وَ قَدْ ظَلَمَنِي مِيرَاثِي مِنْ أُمِّي فَأَخْبَرَهُ الْأَبُ أَنَّهُ قَدْ أَنْفَقَهُ عَلَيْهِ وَ عَلَى نَفْسِهِ فَقَالَ أَنْتَ وَ مَالُكَ لِأَبِيكَ وَ لَمْ يَكُنْ عِنْدَ الرَّجُلِ شَيْ‌ءٌ[1] أَ فَكَانَ رَسُولُ اللَّهِ ص يَحْبِسُ أَباً لِابْنٍ.
- **Isnad as currently extracted:**
  > رَوَى الْحُسَيْنُ بْنُ أَبِي الْعَلَاءِ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسین بن ابی العلاء | روی |  |

### Chain 379 · `faqih-3663` — CLARIFIED
- Transmitters (student → teacher): الحسين بن ابي العلاء → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى الْحُسَيْنُ بْنُ أَبِي الْعَلَاءِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع مَا يَحِلُّ لِلرَّجُلِ مِنْ"
- Mursal opening: al-Ṣadūq → الحسين بن ابي العلاء; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 380 · `faqih-3670`
- **Location:** vol. 3, p. 179 · seq 3682 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى الْحَكَمُ بْنُ مِسْكِينٍ عَنْ قُتَيْبَةَ بْنِ الْأَعْشَى‌[1] قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنِّي أَقْرَأُ الْقُرْآنَ فَتُهْدَى إِلَيَّ الْهَدِيَّةُ فَأَقْبَلُهَا قَالَ لَا قُلْتُ إِنْ‌
لَمْ أُشَارِطْهُ قَالَ أَ رَأَيْتَ إِنْ لَمْ تَقْرَأْهُ أَ كَانَ يُهْدِي لَكَ قَالَ قُلْتُ لَا قَالَ فَلَا تَقْبَلْهُ‌[1].
- **Isnad as currently extracted:**
  > رَوَى الْحَكَمُ بْنُ مِسْكِينٍ عَنْ قُتَيْبَةَ بْنِ الْأَعْشَى‌[1] قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحکم بن مسکین | روی |  |
  | 1 | named_narrator | قتیبة بن الاعشی | عن |  |

### Chain 380 · `faqih-3670` — CLARIFIED
- Transmitters (student → teacher): الحكم بن مسكين → قتيبة بن الاعشي → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى الْحَكَمُ بْنُ مِسْكِينٍ عَنْ قُتَيْبَةَ بْنِ الْأَعْشَى‌[1] قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنِّي أَقْرَأُ الْقُرْآنَ فَتُهْدَى"
- Mursal opening: al-Ṣadūq → الحكم بن مسكين; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 381 · `faqih-3677`
- **Location:** vol. 3, p. 182 · seq 3689 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ مُعَاوِيَةَ بْنِ وَهْبٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّهُ ذُكِرَ لَنَا أَنَّ رَجُلًا مِنَ الْأَنْصَارِ مَاتَ وَ عَلَيْهِ دِينَارَانِ دَيْناً فَلَمْ يُصَلِّ عَلَيْهِ النَّبِيُّ ص وَ قَالَ صَلُّوا عَلَى أَخِيكُمْ حَتَّى ضَمِنَهُمَا عَنْهُ بَعْضُ قَرَابَاتِهِ‌[3] فَقَالَ أَبُو عَبْدِ اللَّهِ ع ذَاكَ الْحَقُّ ثُمَّ قَالَ إِنَّ رَسُولَ اللَّهِ ص إِنَّمَا فَعَلَ ذَلِكَ لِيَتَّعِظُوا[4] وَ لِيَرُدَّ بَعْضُهُمْ عَلَى بَعْضٍ وَ لِئَلَّا يَسْتَخِفُّوا بِالدَّيْنِ‌[5] وَ قَدْ مَاتَ رَسُولُ اللَّهِ ص وَ عَلَيْهِ دَيْنٌ وَ قُتِلَ أَمِيرُ الْمُؤْمِنِينَ ع وَ عَلَيْهِ دَيْنٌ وَ مَاتَ الْحَسَنُ ع وَ عَلَيْهِ دَيْنٌ وَ قُتِلَ الْحُسَيْنُ ع وَ عَلَيْهِ دَيْنٌ.
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ مُعَاوِيَةَ بْنِ وَهْبٍ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن معاویة بن وهب | روی |  |

### Chain 381 · `faqih-3677` — CLARIFIED
- Transmitters (student → teacher): معاوية بن وهب → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنْ مُعَاوِيَةَ بْنِ وَهْبٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّهُ ذُكِرَ لَنَا أَنَّ"
- Mursal opening: al-Ṣadūq → معاوية بن وهب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 382 · `faqih-3679`
- **Location:** vol. 3, p. 182 · seq 3691 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى الْمِيثَمِيُ‌[7] عَنْ أَبِي مُوسَى قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع-
جُعِلْتُ فِدَاكَ يَسْتَقْرِضُ الرَّجُلُ وَ يَحُجُّ قَالَ نَعَمْ قُلْتُ يَسْتَقْرِضُ وَ يَتَزَوَّجُ قَالَ نَعَمْ إِنَّهُ يَنْتَظِرُ رِزْقَ اللَّهِ غُدْوَةً وَ عَشِيَّةً.
- **Isnad as currently extracted:**
  > رَوَى الْمِيثَمِيُ‌[7] عَنْ أَبِي مُوسَى قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | المیثمی | روی |  |
  | 1 | named_narrator | ابی موسی | عن |  |

### Chain 382 · `faqih-3679` — CLARIFIED
- Transmitters (student → teacher): الميثمي → ابي موسي → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى الْمِيثَمِيُ‌[7] عَنْ أَبِي مُوسَى قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع- جُعِلْتُ فِدَاكَ يَسْتَقْرِضُ الرَّجُلُ"
- Mursal opening: al-Ṣadūq → الميثمي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 383 · `faqih-3680`
- **Location:** vol. 3, p. 183 · seq 3692 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ أَبِي ثُمَامَةَ[1] قَالَ‌ قُلْتُ لِأَبِي جَعْفَرٍ الثَّانِي ع إِنِّي أُرِيدُ أَنْ أُلَازِمَ مَكَّةَ وَ الْمَدِينَةَ وَ عَلَيَّ دَيْنٌ فَمَا تَقُولُ قَالَ ارْجِعْ إِلَى مُؤَدَّى دَيْنِكَ‌[2] وَ انْظُرْ أَنْ تَلْقَى اللَّهَ عَزَّ وَ جَلَّ وَ لَيْسَ عَلَيْكَ دَيْنٌ فَإِنَّ الْمُؤْمِنَ لَا يَخُونُ.
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ أَبِي ثُمَامَةَ[1] قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن ابی ثمامة | روی |  |

### Chain 383 · `faqih-3680` — CLARIFIED
- Transmitters (student → teacher): ابي ثمامة → ابي جعفر الثاني ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنْ أَبِي ثُمَامَةَ[1] قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي جَعْفَرٍ الثَّانِي ع إِنِّي أُرِيدُ أَنْ أُلَازِمَ"
- Mursal opening: al-Ṣadūq → ابي ثمامة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 384 · `faqih-3684`
- **Location:** vol. 3, p. 184 · seq 3696 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى سَمَاعَةُ بْنُ مِهْرَانَ‌[1] قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الرَّجُلُ مِنَّا يَكُونُ عِنْدَهُ الشَّيْ‌ءُ يَتَبَلَّغُ بِهِ‌[2] وَ عَلَيْهِ دَيْنٌ أَ يُطْعِمُهُ عِيَالَهُ حَتَّى يَأْتِيَهُ اللَّهُ عَزَّ وَ جَلَّ بِمَيْسَرَةٍ فَيَقْضِيَ دَيْنَهُ أَوْ يَسْتَقْرِضُ عَلَى ظَهْرِهِ فِي خُبْثِ الزَّمَانِ وَ شِدَّةِ الْمَكَاسِبِ أَوْ يَقْبَلُ الصَّدَقَةَ[3] فَقَالَ يَقْضِي بِمَا عِنْدَهُ دَيْنَهُ وَ لَا يَأْكُلُ أَمْوَالَ النَّاسِ إِلَّا وَ عِنْدَهُ مَا يُؤَدِّي إِلَيْهِمْ إِنَّ اللَّهَ عَزَّ وَ جَلَّ يَقُولُ- وَ لا تَأْكُلُوا أَمْوالَكُمْ بَيْنَكُمْ بِالْباطِلِ‌.
- **Isnad as currently extracted:**
  > رَوَى سَمَاعَةُ بْنُ مِهْرَانَ‌[1] قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | سماعة بن مهران | روی |  |

### Chain 384 · `faqih-3684` — CLARIFIED
- Transmitters (student → teacher): سماعة بن مهران → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى سَمَاعَةُ بْنُ مِهْرَانَ‌[1] قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع الرَّجُلُ مِنَّا يَكُونُ عِنْدَهُ"
- Mursal opening: al-Ṣadūq → سماعة بن مهران; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 385 · `faqih-3687`
- **Location:** vol. 3, p. 184 · seq 3699 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ بُرَيْدٍ الْعِجْلِيِّ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ عَلَيَّ دَيْناً لِأَيْتَامٍ وَ أَخَافُ إِنْ بِعْتُ ضَيْعَتِي بَقِيتُ وَ مَا لِيَ شَيْ‌ءٌ قَالَ لَا تَبِعْ ضَيْعَتَكَ وَ لَكِنْ‌
أَعْطِ بَعْضاً وَ أَمْسِكْ بَعْضاً[1].
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ بُرَيْدٍ الْعِجْلِيِّ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن برید العجلی | روی |  |

### Chain 385 · `faqih-3687` — CLARIFIED
- Transmitters (student → teacher): بريد العجلي → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنْ بُرَيْدٍ الْعِجْلِيِّ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ عَلَيَّ دَيْناً لِأَيْتَامٍ"
- Mursal opening: al-Ṣadūq → بريد العجلي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 386 · `faqih-3690`
- **Location:** vol. 3, p. 185 · seq 3702 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى عَلِيُّ بْنُ رِئَابٍ عَنْ سُلَيْمَانَ بْنِ خَالِدٍ قَالَ‌ سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ وَقَعَ لِي عِنْدَهُ مَالٌ فَكَابَرَنِي عَلَيْهِ وَ حَلَفَ ثُمَّ وَقَعَ لَهُ عِنْدِي مَالٌ أَ فَآخُذُهُ مَكَانَ مَالِيَ الَّذِي أَخَذَهُ وَ أَحْلِفُ عَلَيْهِ كَمَا صَنَعَ هُوَ فَقَالَ إِنْ خَانَكَ فَلَا تَخُنْهُ وَ لَا
تَدْخُلْ فِيمَا عِبْتَهُ عَلَيْهِ‌[1].
- **Isnad as currently extracted:**
  > رَوَى عَلِيُّ بْنُ رِئَابٍ عَنْ سُلَيْمَانَ بْنِ خَالِدٍ قَالَ‌ سَأَلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | علی بن رئاب | روی |  |
  | 1 | named_narrator | سلیمان بن خالد | عن |  |

### Chain 386 · `faqih-3690` — CLARIFIED
- Transmitters (student → teacher): علي بن رئاب → سليمان بن خالد → ابا عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى عَلِيُّ بْنُ رِئَابٍ عَنْ سُلَيْمَانَ بْنِ خَالِدٍ قَالَ‌»
- Isnad ends / matn begins at: "سَأَلْتُ أَبَا عَبْدِ اللَّهِ ع عَنْ رَجُلٍ وَقَعَ لِي"
- Mursal opening: al-Ṣadūq → علي بن رئاب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 387 · `faqih-3691`
- **Location:** vol. 3, p. 186 · seq 3703 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ لَهُ الرَّجُلُ يَكُونُ لِي عَلَيْهِ حَقٌّ فَيَجْحَدُنِيهِ ثُمَّ يَسْتَوْدِعُنِي مَالًا أَ لِي أَنْ آخُذَ مَالِي عِنْدَهُ قَالَ لَا هَذِهِ الْخِيَانَةُ[2].
- **Isnad as currently extracted:**
  > رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | معاویة بن عمار | روی |  |
  | 1 | imam | ابی عبد الله ع | عن |  |

### Chain 387 · `faqih-3691` — CLARIFIED
- Transmitters (student → teacher): معاوية بن عمار → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى مُعَاوِيَةُ بْنُ عَمَّارٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ الرَّجُلُ يَكُونُ لِي عَلَيْهِ حَقٌّ فَيَجْحَدُنِيهِ ثُمَّ"
- Mursal opening: al-Ṣadūq → معاوية بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 388 · `faqih-3693`
- **Location:** vol. 3, p. 186 · seq 3705 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ سَيْفِ بْنِ عَمِيرَةَ عَنْ أَبِي بَكْرٍ الْحَضْرَمِيِّ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ كَانَ لَهُ عَلَى رَجُلٍ مَالٌ فَجَحَدَهُ إِيَّاهُ وَ ذَهَبَ بِهِ مِنْهُ ثُمَّ صَارَ إِلَيْهِ بَعْدَ ذَلِكَ مِنْهُ‌[3] لِلرَّجُلِ الَّذِي ذَهَبَ بِمَالِهِ مَالٌ مِثْلُهُ أَ يَأْخُذُهُ مَكَانَ مَالِهِ الَّذِي ذَهَبَ بِهِ مِنْهُ قَالَ نَعَمْ يَقُولُ اللَّهُمَّ إِنِّي إِنَّمَا آخُذُ هَذَا مَكَانَ مَالِيَ الَّذِي أَخَذَهُ مِنِّي‌[4].
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ سَيْفِ بْنِ عَمِيرَةَ عَنْ أَبِي بَكْرٍ الْحَضْرَمِيِّ قَالَ‌ قُلْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | سیف بن عمیرة | عن |  |
  | 2 | named_narrator | ابی بکر الحضرمی | عن |  |

### Chain 388 · `faqih-3693` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → سيف بن عميرة → ابي بكر الحضرمي
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ سَيْفِ بْنِ عَمِيرَةَ عَنْ أَبِي بَكْرٍ الْحَضْرَمِيِّ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع رَجُلٌ كَانَ لَهُ عَلَى"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 389 · `faqih-3697`
- **Location:** vol. 3, p. 187 · seq 3709 · chain 1
- **Flags:** `matn_spill`, `no_imam_terminal`
- **Full report (Arabic):**
  > قَدْ رَوَى مُحَمَّدُ بْنُ أَبِي عُمَيْرٍ عَنْ دَاوُدَ بْنِ زُرْبِيٍّ قَالَ‌ قُلْتُ لِأَبِي الْحَسَنِ ع إِنِّي أُعَامِلُ قَوْماً فَرُبَّمَا أَرْسَلُوا إِلَيَّ فَأَخَذُوا مِنِّي الْجَارِيَةَ وَ الدَّابَّةَ فَذَهَبُوا بِهَا مِنِّي ثُمَّ يَدُورُ لَهُمُ الْمَالُ عِنْدِي فَآخُذُ مِنْهُ بِقَدْرِ مَا أَخَذُوا مِنِّي فَقَالَ خُذْ مِنْهُمْ بِقَدْرِ مَا أَخَذُوا مِنْكَ وَ لَا تَزِدْ عَلَيْهِ.
- **Isnad as currently extracted:**
  > قَدْ رَوَى مُحَمَّدُ بْنُ أَبِي عُمَيْرٍ عَنْ دَاوُدَ بْنِ زُرْبِيٍّ قَالَ‌ قُلْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | قد |  |  |
  | 1 | named_narrator | محمد بن ابی عمیر | روی |  |
  | 2 | named_narrator | داود بن زربی | عن |  |

### Chain 389 · `faqih-3697` — CLARIFIED
- Transmitters (student → teacher): محمد بن ابي عمير → داود بن زربي
- Corrected isnad (Arabic): «قَدْ رَوَى مُحَمَّدُ بْنُ أَبِي عُمَيْرٍ عَنْ دَاوُدَ بْنِ زُرْبِيٍّ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي الْحَسَنِ ع إِنِّي أُعَامِلُ قَوْماً فَرُبَّمَا أَرْسَلُوا"
- Mursal opening: al-Ṣadūq → محمد بن ابي عمير; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 390 · `faqih-3698`
- **Location:** vol. 3, p. 187 · seq 3710 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ هُذَيْلِ بْنِ حَنَانٍ أَخِي جَعْفَرِ بْنِ حَنَانٍ الصَّيْرَفِيِّ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنِّي دَفَعْتُ إِلَى أَخِي جَعْفَرٍ مَالًا فَهُوَ يُعْطِينِي مَا أُنْفِقُهُ وَ أَحُجُّ مِنْهُ وَ أَتَصَدَّقُ وَ قَدْ سَأَلْتُ مَنْ عِنْدَنَا فَذَكَرُوا أَنَّ ذَلِكَ فَاسِدٌ لَا يَحِلُّ وَ أَنَا أُحِبُّ أَنْ أَنْتَهِيَ فِي ذَلِكَ إِلَى قَوْلِكَ فَقَالَ أَ كَانَ يَصِلُكَ قَبْلَ أَنْ تَدْفَعَ إِلَيْهِ مَالَكَ قُلْتُ نَعَمْ قَالَ خُذْ مِنْهُ مَا يُعْطِيكَ وَ كُلْ وَ اشْرَبْ وَ حُجَّ وَ تَصَدَّقْ فَإِذَا قَدِمْتَ الْعِرَاقَ‌
فَقُلْ- جَعْفَرُ بْنُ مُحَمَّدٍ أَفْتَانِي بِهَذَا[1].
- **Isnad as currently extracted:**
  > رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ هُذَيْلِ بْنِ حَنَانٍ أَخِي جَعْفَرِ بْنِ حَنَانٍ الصَّيْرَفِيِّ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | الحسن بن محبوب | روی |  |
  | 1 | named_narrator | هذیل بن حنان اخی جعفر بن حنان الصیرفی | عن |  |

### Chain 390 · `faqih-3698` — CLARIFIED
- Transmitters (student → teacher): الحسن بن محبوب → هذيل بن حنان اخي جعفر بن حنان الصيرفي → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى الْحَسَنُ بْنُ مَحْبُوبٍ عَنْ هُذَيْلِ بْنِ حَنَانٍ أَخِي جَعْفَرِ بْنِ حَنَانٍ الصَّيْرَفِيِّ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنِّي دَفَعْتُ إِلَى أَخِي"
- Mursal opening: al-Ṣadūq → الحسن بن محبوب; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 391 · `faqih-3701`
- **Location:** vol. 3, p. 188 · seq 3713 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنِ الصَّبَّاحِ بْنِ سَيَابَةَ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ عَبْدَ اللَّهِ بْنَ أَبِي يَعْفُورٍ أَمَرَنِي أَنْ أَسْأَلَكَ قَالَ إِنَّا نَسْتَقْرِضُ الْخُبْزَ مِنَ الْجِيرَانِ فَنَرُدُّ أَصْغَرَ مِنْهُ أَوْ أَكْبَرَ فَقَالَ ع نَحْنُ نَسْتَقْرِضُ الْجَوْزَ السِّتِّينَ وَ السَّبْعِينَ عَدَداً فَيَكُونُ فِيهِ الصَّغِيرَةُ وَ الْكَبِيرَةُ فَلَا بَأْسَ‌[4].
- **Isnad as currently extracted:**
  > رُوِيَ عَنِ الصَّبَّاحِ بْنِ سَيَابَةَ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن الصباح بن سیابة | روی |  |

### Chain 391 · `faqih-3701` — CLARIFIED
- Transmitters (student → teacher): الصباح بن سيابة → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رُوِيَ عَنِ الصَّبَّاحِ بْنِ سَيَابَةَ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ عَبْدَ اللَّهِ بْنَ"
- Mursal opening: al-Ṣadūq → الصباح بن سيابة; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 392 · `faqih-3706`
- **Location:** vol. 3, p. 189 · seq 3718 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى إِبْرَاهِيمُ بْنُ عَبْدِ الْحَمِيدِ عَنِ الْحَسَنِ بْنِ خُنَيْسٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ لِعَبْدِ الرَّحْمَنِ بْنِ سَيَابَةَ دَيْناً عَلَى رَجُلٍ وَ قَدْ مَاتَ فَكَلَّمْنَاهُ أَنْ يُحَلِّلَهُ فَأَبَى قَالَ وَيْحَهُ أَ مَا يَعْلَمُ أَنَّ لَهُ بِكُلِّ دِرْهَمٍ عَشَرَةً إِذَا حَلَّلَهُ وَ إِذَا لَمْ يُحَلِّلْهُ فَإِنَّمَا لَهُ دِرْهَمٌ بَدَلَ دِرْهَمٍ‌[2].
- **Isnad as currently extracted:**
  > رَوَى إِبْرَاهِيمُ بْنُ عَبْدِ الْحَمِيدِ عَنِ الْحَسَنِ بْنِ خُنَيْسٍ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابراهیم بن عبد الحمید | روی |  |
  | 1 | named_narrator | الحسن بن خنیس | عن |  |

### Chain 392 · `faqih-3706` — CLARIFIED
- Transmitters (student → teacher): ابراهيم بن عبد الحميد → الحسن بن خنيس
- Corrected isnad (Arabic): «رَوَى إِبْرَاهِيمُ بْنُ عَبْدِ الْحَمِيدِ عَنِ الْحَسَنِ بْنِ خُنَيْسٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع إِنَّ لِعَبْدِ الرَّحْمَنِ بْنِ"
- Mursal opening: al-Ṣadūq → ابراهيم بن عبد الحميد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 393 · `faqih-3709`
- **Location:** vol. 3, p. 190 · seq 3721 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى إِبْرَاهِيمُ بْنُ هَاشِمٍ أَنَّ مُحَمَّدَ بْنَ أَبِي عُمَيْرٍ رَضِيَ اللَّهُ عَنْهُ كَانَ رَجُلًا بَزَّازاً فَذَهَبَ مَالُهُ وَ افْتَقَرَ وَ كَانَ لَهُ عَلَى رَجُلٍ عَشَرَةُ آلَافِ دِرْهَمٍ فَبَاعَ دَاراً لَهُ كَانَ يَسْكُنُهَا بِعَشَرَةِ آلَافِ دِرْهَمٍ وَ حَمَلَ الْمَالَ إِلَى بَابِهِ فَخَرَجَ إِلَيْهِ مُحَمَّدُ بْنُ أَبِي عُمَيْرٍ فَقَالَ مَا هَذَا قَالَ هَذَا مَالُكَ الَّذِي لَكَ عَلَيَّ قَالَ وَرِثْتَهُ قَالَ لَا قَالَ وُهِبَ لَكَ قَالَ لَا قَالَ فَقَالَ فَهُوَ ثَمَنُ ضَيْعَةٍ بِعْتَهَا قَالَ لَا قَالَ فَمَا هُوَ قَالَ بِعْتُ دَارِيَ الَّتِي أَسْكُنُهَا لِأَقْضِيَ دَيْنِي فَقَالَ مُحَمَّدُ بْنُ أَبِي عُمَيْرٍ رَضِيَ اللَّهُ عَنْهُ حَدَّثَنِي ذَرِيحٌ الْمُحَارِبِيُّ عَنْ أَبِي عَبْدِ اللَّهِ ع أَنَّهُ قَالَ: لَا يُخْرَجُ الرَّجُلُ عَنْ مَسْقَطِ رَأْسِهِ بِالدَّيْنِ ارْفَعْهَا فَلَا حَاجَةَ لِي فِيهَا وَ اللَّهِ إِنِّي مُحْتَاجٌ فِي وَقْتِي هَذَا إِلَى دِرْهَمٍ وَ مَا يَدْخُلُ مِلْكِي مِنْهَا دِرْهَمٌ‌[3].
وَ كَانَ شَيْخُنَا مُحَمَّدُ بْنُ الْحَسَنِ رَضِيَ اللَّهُ عَنْهُ يَرْوِي أَنَّهَا إِنْ كَانَتِ الدَّارُ وَاسِعَةً يَكْتَفِي صَاحِبُهَا بِبَعْضِهَا فَعَلَيْهِ أَنْ يَسْكُنَ مِنْهَا مَا يَحْتَاجُ إِلَيْهِ وَ يَقْضِيَ بِبَقِيَّتِهَا دَيْنَهُ وَ كَذَلِكَ إِنْ كَفَتْهُ دَارٌ بِدُونِ ثَمَنِهَا بَاعَهَا وَ اشْتَرَى بِثَمَنِهَا دَاراً لِيَسْكُنَهَا وَ يَقْضِيَ‌
بِبَاقِي الثَّمَنِ دَيْنَهُ‌[1].
- **Isnad as currently extracted:**
  > وَ رَوَى إِبْرَاهِيمُ بْنُ هَاشِمٍ أَنَّ مُحَمَّدَ بْنَ أَبِي عُمَيْرٍ رَضِيَ اَللَّهُ عَنْهُ كَانَ رَجُلاً بَزَّازاً فَذَهَبَ مَالُهُ وَ اِفْتَقَرَ وَ كَانَ لَهُ عَلَى رَجُلٍ عَشَرَةُ آلاَفِ دِرْهَمٍ فَبَاعَ دَاراً لَهُ كَانَ يَسْكُنُهَا بِعَشَرَةِ آلاَفِ دِرْهَمٍ وَ حَمَلَ اَلْمَالَ إِلَى بَابِهِ فَخَرَجَ إِلَيْهِ مُحَمَّدُ بْنُ أَبِي عُمَيْرٍ فَقَالَ مَا هَذَا قَالَ هَذَا مَالُكَ اَلَّذِي لَكَ عَلَيَّ قَالَ وَرِثْتَهُ قَالَ لاَ قَالَ وُهِبَ لَكَ قَالَ لاَ قَالَ فَقَالَ فَهُوَ ثَمَنُ ضَيْعَةٍ بِعْتَهَا قَالَ لاَ قَالَ فَمَا هُوَ قَالَ بِعْتُ دَارِيَ اَلَّتِي أَسْكُنُهَا لِأَقْضِيَ دَيْنِي فَقَالَ مُحَمَّدُ بْنُ أَبِي عُمَيْرٍ رَضِيَ اَللَّهُ عَنْهُ حَدَّثَنِي ذَرِيحٌ اَلْمُحَارِبِيُّ عَنْ أَبِي عَبْدِ اَللَّهِ عَلَيْهِ اَلسَّلاَمُ أَنَّهُ قَالَ:
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | ابراهیم بن هاشم ان محمد بن ابی عمیر کان رجلا بزازا فذهب ماله و افتقر و کان له علی رجل عشرة الاف درهم فباع دارا له کان یسکنها بعشرة الاف درهم و حمل المال الی بابه فخرج الیه محمد بن ابی عمیر فقال ما هذا | روی |  |

### Chain 393 · `faqih-3709` — CLARIFIED
- Transmitters (student → teacher): إبراهيم بن هاشم → [خبرٌ تاريخي عن محمد بن أبي عمير]; embedded isnad inside the matn: محمد بن أبي عمير → ذريح المحاربي → أبو عبد الله ع
- Corrected isnad (Arabic): «رَوَى إِبْرَاهِيمُ بْنُ هَاشِمٍ»
- Isnad ends / matn begins at: "أَنَّ مُحَمَّدَ بْنَ أَبِي عُمَيْرٍ رَضِيَ اللَّهُ عَنْهُ كَانَ"
- Mursal opening: al-Ṣadūq → إبراهيم بن هاشم; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The outer report is Ibrāhīm b. Hāshim’s biographical account; it does not syntactically transmit from Ibn Abī ʿUmayr by «عن». A separate embedded hadith appears later in the matn with its own route, Ibn Abī ʿUmayr → Dharīḥ al-Muḥāribī → Abū ʿAbd Allāh. Keeping the two layers separate resolves the apparent chain spill.
---

### Chain 394 · `faqih-3726`
- **Location:** vol. 3, p. 195 · seq 3738 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى حَفْصُ بْنُ الْبَخْتَرِيِّ عَنِ الْحُسَيْنِ بْنِ الْمُنْذِرِ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع دَفَعَتْ إِلَيَّ امْرَأَتِي مَالًا أَعْمَلُ بِهِ مَا شِئْتُ فَأَشْتَرِي مِنْ مَالِهَا الْجَارِيَةَ أَطَأُهَا قَالَ لَا إِنَّمَا دَفَعَتْ إِلَيْكَ لِتَقَرَّ عَيْنُهَا وَ أَنْتَ تُرِيدُ أَنْ تُسْخِنَ عَيْنَهَا[3].
- **Isnad as currently extracted:**
  > رَوَى حَفْصُ بْنُ الْبَخْتَرِيِّ عَنِ الْحُسَيْنِ بْنِ الْمُنْذِرِ قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | حفص بن البختری | روی |  |
  | 1 | named_narrator | الحسین بن المنذر | عن |  |

### Chain 394 · `faqih-3726` — CLARIFIED
- Transmitters (student → teacher): حفص بن البختري → الحسين بن المنذر → ابي عبد الله ع (مذكور بصيغة السماع/السؤال في صدر المتن)
- Corrected isnad (Arabic): «رَوَى حَفْصُ بْنُ الْبَخْتَرِيِّ عَنِ الْحُسَيْنِ بْنِ الْمُنْذِرِ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع دَفَعَتْ إِلَيَّ امْرَأَتِي مَالًا"
- Mursal opening: al-Ṣadūq → حفص بن البختري; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 395 · `faqih-3727`
- **Location:** vol. 3, p. 195 · seq 3739 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رَوَى عُثْمَانُ بْنُ عِيسَى عَنْ مُيَسِّرٍ[4] قَالَ‌ قُلْتُ لَهُ يَجِيئُنِي الرَّجُلُ فَيَقُولُ تَشْتَرِي لِي فَيَكُونُ مَا عِنْدِي خَيْراً مِنْ مَتَاعِ السُّوقِ قَالَ إِنْ أَمِنْتَ أَلَّا يَتَّهِمَكَ فَأَعْطِهِ مِنْ عِنْدِكَ وَ إِنْ خِفْتَ أَنْ يَتَّهِمَكَ فَاشْتَرِ لَهُ مِنَ السُّوقِ.
- **Isnad as currently extracted:**
  > رَوَى عُثْمَانُ بْنُ عِيسَى عَنْ مُيَسِّرٍ[4] قَالَ‌ قُلْتُ
- **Current node split (2 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عثمان بن عیسی | روی |  |
  | 1 | named_narrator | میسر | عن |  |

### Chain 395 · `faqih-3727` — CLARIFIED
- Transmitters (student → teacher): عثمان بن عيسي → ميسر
- Corrected isnad (Arabic): «رَوَى عُثْمَانُ بْنُ عِيسَى عَنْ مُيَسِّرٍ[4] قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ يَجِيئُنِي الرَّجُلُ فَيَقُولُ تَشْتَرِي لِي فَيَكُونُ مَا"
- Mursal opening: al-Ṣadūq → عثمان بن عيسي; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 396 · `faqih-3739`
- **Location:** vol. 3, p. 197 · seq 3751 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى مُيَسِّرٌ عَنْ حَفْصٍ‌[4] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ لَهُ رَجُلٌ مِنْ نِيَّتِهِ الْوَفَاءُ وَ هُوَ إِذَا كَالَ لَمْ يُحْسِنْ أَنْ يَكِيلَ فَقَالَ مَا يَقُولُ الَّذِينَ حَوْلَهُ قَالَ قُلْتُ يَقُولُونَ لَا يُوفِي قَالَ هُوَ مِمَّنْ لَا يَنْبَغِي لَهُ أَنْ يَكِيلَ‌[5].
- **Isnad as currently extracted:**
  > رَوَى مُيَسِّرٌ عَنْ حَفْصٍ‌[4] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ قُلْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | میسر | روی |  |
  | 1 | named_narrator | حفص | عن |  |
  | 2 | imam | ابی عبد الله ع | عن |  |

### Chain 396 · `faqih-3739` — CLARIFIED
- Transmitters (student → teacher): ميسر → حفص → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى مُيَسِّرٌ عَنْ حَفْصٍ‌[4] عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ رَجُلٌ مِنْ نِيَّتِهِ الْوَفَاءُ وَ هُوَ إِذَا"
- Mursal opening: al-Ṣadūq → ميسر; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 397 · `faqih-3743`
- **Location:** vol. 3, p. 198 · seq 3755 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`, `no_imam_terminal`
- **Full report (Arabic):**
  > رُوِيَ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع آخُذُ الدَّرَاهِمَ مِنَ الرَّجُلِ فَأَزِنُهَا ثُمَّ أُفَرِّقُهَا وَ يَفْضُلُ فِي يَدِي مِنْهَا فَضْلٌ قَالَ أَ لَيْسَ تَحَرَّى الْوَفَاءَ قُلْتُ بَلَى قَالَ لَا بَأْسَ‌[4].
العربون‌[5]
- **Isnad as currently extracted:**
  > رُوِيَ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌ قُلْتُ
- **Current node split (1 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عن اسحاق بن عمار | روی |  |

### Chain 397 · `faqih-3743` — CLARIFIED
- Transmitters (student → teacher): اسحاق بن عمار
- Corrected isnad (Arabic): «رُوِيَ عَنْ إِسْحَاقَ بْنِ عَمَّارٍ قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لِأَبِي عَبْدِ اللَّهِ ع آخُذُ الدَّرَاهِمَ مِنَ الرَّجُلِ"
- Mursal opening: al-Ṣadūq → اسحاق بن عمار; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād. The `no_imam_terminal` flag is a tokenizer false negative: the Imam is identifiable in the attribution or in the opening audition/question formula.

---

### Chain 398 · `faqih-3747`
- **Location:** vol. 3, p. 199 · seq 3759 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى عَاصِمُ بْنُ حُمَيْدٍ عَنْ أَبِي بَصِيرٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ مَنْ دَخَلَ سُوقاً أَوْ مَسْجِدَ جَمَاعَةٍ فَقَالَ مَرَّةً وَاحِدَةً- أَشْهَدُ أَنْ لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ‌
لَا شَرِيكَ لَهُ وَ اللَّهُ أَكْبَرُ كَبِيراً وَ الْحَمْدُ لِلَّهِ كَثِيراً وَ سُبْحَانَ اللَّهِ بُكْرَةً وَ أَصِيلًا وَ لَا حَوْلَ وَ لَا قُوَّةَ إِلَّا بِاللَّهِ الْعَلِيِّ الْعَظِيمِ وَ صَلَّى اللَّهُ عَلَى مُحَمَّدٍ وَ آلِهِ عَدَلَتْ لَهُ حَجَّةً مَبْرُورَةً.
- **Isnad as currently extracted:**
  > رَوَى عَاصِمُ بْنُ حُمَيْدٍ عَنْ أَبِي بَصِيرٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌ مَنْ دَخَلَ سُوقاً أَوْ مَسْجِدَ جَمَاعَةٍ فَقَالَ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | عاصم بن حمید | روی |  |
  | 1 | named_narrator | ابی بصیر | عن |  |
  | 2 | imam | ابی عبد الله ع | عن |  |

### Chain 398 · `faqih-3747` — CLARIFIED
- Transmitters (student → teacher): عاصم بن حميد → ابي بصير → ابي عبد الله ع
- Corrected isnad (Arabic): «رَوَى عَاصِمُ بْنُ حُمَيْدٍ عَنْ أَبِي بَصِيرٍ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ‌»
- Isnad ends / matn begins at: "مَنْ دَخَلَ سُوقاً أَوْ مَسْجِدَ جَمَاعَةٍ فَقَالَ مَرَّةً وَاحِدَةً-"
- Mursal opening: al-Ṣadūq → عاصم بن حميد; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---

### Chain 399 · `faqih-3760`
- **Location:** vol. 3, p. 202 · seq 3772 · chain 1
- **Flags:** `matn_spill`, `mursal_opening`
- **Full report (Arabic):**
  > رَوَى جَمِيلٌ عَنْ زُرَارَةَ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ قُلْتُ لَهُ الرَّجُلُ يَشْتَرِي مِنَ الرَّجُلِ الْمَتَاعَ ثُمَّ يَدَعُهُ عِنْدَهُ يَقُولُ حَتَّى آتِيَكَ بِثَمَنِهِ فَقَالَ إِنْ جَاءَ
فِيمَا بَيْنَهُ وَ بَيْنَ ثَلَاثَةِ أَيَّامٍ وَ إِلَّا فَلَا بَيْعَ لَهُ‌[1].
- **Isnad as currently extracted:**
  > رَوَى جَمِيلٌ عَنْ زُرَارَةَ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌ قُلْتُ
- **Current node split (3 nodes):**

  | pos | type | token | phrase | rel |
  | --- | --- | --- | --- | --- |
  | 0 | named_narrator | جمیل | روی |  |
  | 1 | named_narrator | زرارة | عن |  |
  | 2 | imam | ابی جعفر ع | عن |  |

### Chain 399 · `faqih-3760` — CLARIFIED
- Transmitters (student → teacher): جميل → زرارة → ابي جعفر ع
- Corrected isnad (Arabic): «رَوَى جَمِيلٌ عَنْ زُرَارَةَ عَنْ أَبِي جَعْفَرٍ ع قَالَ‌»
- Isnad ends / matn begins at: "قُلْتُ لَهُ الرَّجُلُ يَشْتَرِي مِنَ الرَّجُلِ الْمَتَاعَ ثُمَّ يَدَعُهُ"
- Mursal opening: al-Ṣadūq → جميل; full path via Mashyakha = omitted
- Verdict: needs_mashyakha_expansion
- Notes: The corrected boundary excludes the substantive question, ruling, narrative, or letter text from the isnād.

---
