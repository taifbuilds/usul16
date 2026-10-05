# Case 8 — Aṣḥāb al-Ijmāʿ and blanket authentication

**Research state:** case-study complete; primary-source and corpus audit dated 2026-08-24

**Question:** what, exactly, is authenticated by the three consensus notices transmitted by al-Kashshī, and how is that claim related to al-Ṭūsī's rule about the *marāsīl* of Ibn Abī ʿUmayr, Ṣafwān, and al-Bazanṭī?
**Database scope:** read-only analysis of the local Four Books corpus; no production code, schema, or data was changed.

## 1. Result at a glance

The expression “Aṣḥāb al-Ijmāʿ” is useful later shorthand, but it conceals several propositions that the sources do not state in the same place or in the same words.

1. Al-Kashshī transmits three roster notices praising named jurists/transmitters and reporting communal agreement about them. The formulas differ, the first and third rosters contain variant names, and the third roster is textually awkward.
2. Al-Ṭūsī's *ʿUddat al-uṣūl* states a distinct rule about treating the *mursal* reports of Ibn Abī ʿUmayr, Ṣafwān b. Yaḥyā, Aḥmad b. Muḥammad b. Abī Naṣr, and comparable trustworthy transmitters like supported reports because they were known not to narrate or omit an intermediary except from one trusted. It is not a fourth Kashshī roster.
3. Neither text, without an additional interpretive premise, says that every named or unnamed person on the **Imam-side** of a roster member is personally `thiqa`.
4. Later scholars disagree about the additional premise. A broad line represented clearly by Mīr Dāmād and al-Ḥurr al-ʿĀmilī treats qualifying reports as sound or established even across weak, unknown, or omitted Imam-side intermediaries. Al-Fayḍ al-Kāshānī and al-Khūʾī reject that reading of al-Kashshī's syntax. Al-Khūʾī also rejects the exceptionless “three narrate only from trustworthy persons” rule, notwithstanding al-Ṭūsī's wording.
5. A report-level rule is not automatically a person-level grade. Even some broad users preserve this distinction. Al-Māmaqānī, for example, can leave a transmitter personally unknown while accepting the particular report carried through Ṣafwān.
6. The local Four Books corpus contains both explicit anonymous links after Ibn Abī ʿUmayr and numerous transmissions by roster members from Abū Jamīla/al-Mufaḍḍal b. Ṣāliḥ, a narrator adversely assessed in early material. Those observations test an exceptionless empirical rule; they do not by themselves disprove a special report-level legal convention.

The defensible default for Usul16 is therefore **claim separation plus method-indexed adjudication**, not a global boolean called `ashab_al_ijma = trusted_everything`.

| Question | Strict source-sensitive result | Broader historical result that must also be representable |
|---|---|---|
| Are the named roster members themselves authenticated? | Strong positive evidence; al-Khūʾī reads the consensus as directed to their reliability, learning, and truthfulness. | Same, subject to ordinary identity and textual-variant controls. |
| Is every Imam-side narrator personally trustworthy? | No: not established by the formula alone, and contradicted as an exceptionless inference by known weak examples. | Some later arguments infer reliability or at least good standing in selected cases from such narration plus corroborating indicators. |
| Is every qualifying report sound/acceptable? | No automatic result; inspect route, wording, identity, opposition, and each scholar's uṣūl. | Mīr Dāmād and al-Ḥurr articulate a broad report-level convention, including omitted or unknown links. |
| Are the trio's *marāsīl* equivalent to *masānīd*? | Al-Ṭūsī reports that practice; al-Khūʾī disputes its universal factual and probative basis. | A method may adopt al-Ṭūsī's convention without grading every omitted individual. |
| Does *Kāmil al-ziyārāt* or *Tafsīr al-Qummī* prove the same rule? | No. Each depends on its own preface, textual history, and scope. | Al-Khūʾī accepted a chain-wide reading for *Tafsīr al-Qummī* and narrowed his late position on *Kāmil* to direct teachers. |

## 2. Four objects that must not be collapsed

In a compiler-to-Imam chain such as:

```text
compiler → ... → Ṣafwān → Abū Jamīla → named transmitter → Imam
```

the following are logically different objects:

| Object | Possible proposition | Proper evidence target |
|---|---|---|
| roster member | Ṣafwān is trustworthy / a jurist / truthful in what he transmits | person-level judgment about Ṣafwān |
| Imam-side intermediary | Abū Jamīla is trustworthy | person-level judgment about Abū Jamīla |
| route or report | this report through Ṣafwān is accepted or “counted among the sound” | occurrence/report-level judgment |
| transmission practice | Ṣafwān's omissions are treated like connected reports under stated conditions | class/rule-level judgment |

“Compiler-side” and “Imam-side” are used here instead of “above” and “below,” whose meanings reverse between diagrams and Arabic isnād prose. A valid inference must name its object. In particular:

```text
member is thiqa
    does not entail
every Imam-side source is thiqa

report is accepted by convention
    does not entail
every omitted person receives a recoverable personal tawthīq
```

This guardrail is the central adjudicative result of the case.

## 3. The three Kashshī notices

### 3.1 Edition and source status

The citations use al-Ṭūsī's surviving selection, *Ikhtiyār maʿrifat al-rijāl*, corrected and annotated by Mīr Dāmād al-Astarābādī, ed. al-Sayyid Mahdī al-Rajāʾī, Muʾassasat Āl al-Bayt, Qum, first ed. 1404 AH, 2 vols. The authorial notices are al-Kashshī material transmitted within al-Ṭūsī's selection; Mīr Dāmād's annotations are a later layer and are not silently attributed to al-Kashshī. [The complete work and metadata are available here](https://usul.ai/ar/t/ikhtiyar-macrifat-rijal).

The section headings speak of naming the jurists among the companions. “Aṣḥāb al-Ijmāʿ” is a later convenient label for the people gathered from these notices, not a phrase that should be retrojected into every line of the source.

### 3.2 First stratum: companions of al-Bāqir and al-Ṣādiq

Al-Kashshī, *Ikhtiyār*, vol. 2, p. 507, no. 431 ([exact scan page](https://www.masaha.org/book/view/525/page/507)):

> `اجتمعت العصابة على تصديق هؤلاء الأولين من أصحاب أبي جعفر (ع) وأصحاب أبي عبد الله (ع) وانقادوا لهم بالفقه، فقالوا: أفقه الأولين ستة: زرارة، ومعروف بن خربوذ، وبريد، وأبو بصير الأسدي، والفضيل بن يسار، ومحمد بن مسلم الطائفي ... وقال بعضهم مكان أبي بصير الأسدي أبو بصير المرادي وهو ليث بن البختري`

The stable five are Zurāra, Maʿrūf b. Kharrabūdh, Burayd, al-Fuḍayl b. Yasār, and Muḥammad b. Muslim. The sixth position varies between Abū Baṣīr al-Asadī and Abū Baṣīr al-Murādī/Layth b. al-Bakhtarī. The wording reports truthfulness and submission to their jurisprudential authority; it does not contain the later technical sentence “all persons from whom they narrated are trustworthy.”

### 3.3 Second stratum: six after the first six

Al-Kashshī, *Ikhtiyār*, vol. 2, p. 673, no. 705 ([exact scan page](https://www.masaha.org/book/view/525/page/673)):

> `أجمعت العصابة على تصحيح ما يصح من هؤلاء وتصديقهم لما يقولون، وأقروا لهم بالفقه من دون أولئك الستة الذين عددناهم وسميناهم، وهم ستة نفر: جميل بن دراج، وعبد الله بن مسكان، وعبد الله بن بكير، وحماد بن عثمان، وحماد بن عيسى، وأبان بن عثمان`

This roster is textually stable at six: Jamīl b. Darrāj, ʿAbd Allāh b. Muskān, ʿAbd Allāh b. Bukayr, Ḥammād b. ʿUthmān, Ḥammād b. ʿĪsā, and Abān b. ʿUthmān. The contested phrase is `تصحيح ما يصح من هؤلاء`. Whether `ما يصح` points to the reliably established **transmission from them** or authenticates the full **content and Imam-side route** is precisely the later dispute; a database must not decide the syntax by expanding the label.

### 3.4 Third stratum: companions of al-Kāẓim and al-Riḍā

Al-Kashshī, *Ikhtiyār*, vol. 2, p. 830, no. 1050 ([exact scan page](https://www.masaha.org/book/view/525/page/830)):

> `أجمع أصحابنا على تصحيح ما يصح من هؤلاء وتصديقهم وأقروا لهم بالفقه والعلم، وهم ستة نفر آخر دون الستة نفر الذين ذكرناهم في أصحاب أبي عبد الله (ع)، منهم: يونس بن عبد الرحمن، وصفوان بن يحيى بياع السابري، ومحمد بن أبي عمير، وعبد الله بن المغيرة، والحسن بن محبوب، وأحمد بن محمد بن أبي نصر، وقال بعضهم مكان الحسن بن محبوب الحسن بن علي بن فضال وفضالة بن أيوب، وقال بعضهم مكان فضالة بن أيوب عثمان بن عيسى، وأفقه هؤلاء يونس بن عبد الرحمن وصفوان بن يحيى`

The six named first are Yūnus b. ʿAbd al-Raḥmān, Ṣafwān b. Yaḥyā, Muḥammad b. Abī ʿUmayr, ʿAbd Allāh b. al-Mughīra, al-Ḥasan b. Maḥbūb, and Aḥmad b. Muḥammad b. Abī Naṣr. Variant reporters substitute al-Ḥasan b. ʿAlī b. Faḍḍāl and Faḍāla b. Ayyūb for al-Ḥasan b. Maḥbūb, then ʿUthmān b. ʿĪsā for Faḍāla. The surface grammar can appear to produce seven names in one variant while insisting upon six; that is a textual fact to preserve, not an invitation to normalize silently.

### 3.5 What “the eighteen” contains

The conventional total eighteen is three positions of six, not eighteen invariant identities. Across the three notices:

- sixteen persons occupy stable positions;
- the first roster contributes two alternatives for one position;
- the third contributes a more complex set of alternatives;
- across all transmitted alternatives, twenty-two names can be enumerated, while later discussions also speak of twenty-one depending on how the third formula is parsed.

Mīr Dāmād himself concludes that the people at issue are `أحد وعشرون بل اثنان وعشرون رجلا`; see *al-Rawāshiḥ al-samāwiyya*, pp. 78–80 ([p. 80](https://ablibrary.net/book_content/4064/80)). Accordingly, membership must be represented as `roster_notice + slot/variant + attributed reporter`, not as one timeless yes/no property.

## 4. Al-Ṭūsī's *ʿUdda*: a separate proposition

Al-Ṭūsī, *ʿUddat al-uṣūl*, ed. Muḥammad Riḍā al-Anṣārī al-Qummī, Tīzhūsh, Qum, first ed. 1417 AH, displayed print p. 154 ([exact text and page](https://usul.ai/ar/t/uddat-al-usul/149)):

> `وإذا كان أحد الراويين مسندا والآخر مرسلا، نظر في حال المرسل، فإن كان ممن يعلم أنه لا يرسل إلا عن ثقة موثوق به، فلا ترجح لخبر غيره على خبره، ولأجل ذلك سوت الطائفة بين ما يرويه محمد بن أبي عمير، وصفوان بن يحيى، وأحمد بن محمد بن أبي نصر وغيرهم من الثقات الذين عرفوا بأنهم لا يروون ولا يرسلون إلا عمن يوثق به وبين ما أسنده غيرهم، ولذلك عملوا بمراسيلهم إذا انفردوا عن رواية غيرهم.`

This states a comparative rule for a connected report and a *mursal* report, grounds it in a claimed known practice, names a trio, extends it to comparable trustworthy transmitters, and adds a condition about the absence of another narration. Its natural scope is broader than “the three men themselves are trustworthy,” but it still needs careful modeling:

- **speaker:** al-Ṭūsī;
- **reported actor:** `الطائفة`;
- **class:** the named trio and comparable transmitters known for the practice;
- **rule object:** narrated and omitted-link reports, especially preference/equivalence;
- **stated rationale:** they narrate and omit only from a trusted person;
- **condition:** the *mursal* stands alone from another narration in the final clause;
- **not stated:** that an unidentified omitted person can be added to the person authority table as individually identified and `thiqa`.

Al-Khūʾī later suggests that al-Ṭūsī may have inferred this claim from the Kashshī consensus formula. That is al-Khūʾī's historical hypothesis, not an explicit cross-reference by al-Ṭūsī. The dependency should therefore be an `inferred_possible_source` edge, not a fact.

## 5. Early individual controls

### 5.1 Ibn Abī ʿUmayr himself

Al-Ṭūsī's *Fihrist*, ed. Jawād al-Qayyūmī, entry 607, pp. 142–143 ([scan beginning at the entry](https://www.masaha.org/book/view/2324/page/141)), describes Muḥammad b. Abī ʿUmayr as:

> `وكان من أوثق الناس عند الخاصة والعامة، وأنسكهم نسكا، وأورعهم وأعبدهم`

This is explicit personal authentication of Ibn Abī ʿUmayr. It does not grade every source he names.

Al-Najāshī, *Rijāl al-Najāshī*, ed. Mūsā al-Shubayrī al-Zanjānī, entry 887, printed p. 326 (the digitized viewer displays it at [scan p. 322](https://www.masaha.org/book/view/2198/page/322)), describes his high standing, imprisonment, and the loss of his books, then says:

> `فحدث من حفظه ومما كان سلف له في أيدي الناس، فلهذا أصحابنا يسكنون إلى مراسيله`

This is important independent biographical context for communal confidence in his *marāsīl*. It explains a particular transmitter's book history and reception; it does not reproduce the universal trio formula, and it should not be expanded automatically to all roster members.

### 5.2 Abū Jamīla/al-Mufaḍḍal b. Ṣāliḥ as an adverse control

Al-Najāshī, *Rijāl al-Najāshī*, ed. Mūsā al-Shubayrī al-Zanjānī, Muʾassasat al-Nashr al-Islāmī, Qum, in the entry on Jābir b. Yazīd, entry 332, printed pp. 128–129 ([exact host page](https://usul.ai/ar/t/rijal-2/129)), reports:

> `روى عنه جماعة غمز فيهم وضعفوا، منهم: عمرو بن شمر، ومفضل بن صالح، ومنخل بن جميل، ويوسف بن يعقوب`

This is a class-level adverse report that expressly includes al-Mufaḍḍal b. Ṣāliḥ. The neutral early controls are equally important:

- Al-Ṭūsī, *al-Fihrist*, ed. Jawād al-Qayyūmī, entry 764, p. 252 ([exact page](https://ablibrary.net/book_content/b/2684/252)): `مفضل بن صالح، يكنى أبا جميلة، له كتاب، وكان نخاسا يبيع الرقيق، ويقال إنه كان حدادا`. He then gives a route to the book but no reliability grade.
- Al-Ṭūsī, *Rijāl al-Ṭūsī*, ed. Jawād al-Qayyūmī al-Iṣfahānī, Muʾassasat al-Nashr al-Islāmī, entry 566 in the companions of al-Ṣādiq, p. 307 ([exact page](https://ablibrary.net/book_content/b/5232/307)): `مفضل بن صالح، أبو علي، مولى بني أسد، يكنى أبا جميلة أيضا، مات في حياة الرضا عليه السلام`. This is identification and ṭabaqah/death information, not taʿdīl.
- Al-Barqī, *Rijāl al-Barqī*, companions of al-Ṣādiq, displayed p. 18 ([exact page](https://usul.ai/ar/t/rijal-al-barqi/18)): `أبو جميل المفضل بن صالح`. List membership is not an express tawthīq.

The attributed *Kitāb al-Ḍuʿafāʾ* of Ibn al-Ghaḍāʾirī gives a much harsher notice—`ضعيف، كذاب، يضع الحديث`—and transmits an accusation of fabrication ([exact page](https://usul.ai/ar/t/rijal-4/54)). Because the book's attribution and transmission are themselves contested, its proposition must remain separately sourced. It is corroborative only for methods that accept that source; it may not be silently fused with al-Najāshī's earlier class statement.

Abū Jamīla is useful here not because this case must settle his final grade, but because roster members demonstrably transmit from him. Any rule claiming an exceptionless observable practice must explain that evidence.

## 6. The major interpretive positions

### 6.1 Mīr Dāmād: broad report-level validation

Mīr Dāmād reads the formula broadly in *al-Rawāshiḥ al-samāwiyya*. At pp. 78–80 ([p. 78](https://ablibrary.net/book_content/4064/78), [p. 79](https://ablibrary.net/book_content/4064/79), [p. 80](https://ablibrary.net/book_content/4064/80)), he includes reports that are sent, raised, interrupted, or transmitted through a named person whose condition is unknown, and concludes:

> `ومراسيلهم ومرافيعهم ومقاطيعهم ومسانيدهم إلى من يسمونه من غير المعروفين معدودة عند الأصحاب ... من الصحاح`

The object is the reports “counted among the sound.” This is powerful evidence for the historical breadth of one reception line, but it does not require the system to manufacture a personal Najāshī-style `thiqa` statement for each unknown intermediary.

### 6.2 Al-Ḥurr al-ʿĀmilī: the clearest blanket report claim

Al-Ḥurr, *Wasāʾil al-shīʿa*, vol. 30, p. 225 ([exact scan page](https://www.masaha.org/book/view/2024/page/225)), calls the consensus a decisive indicator for every report narrated by one of the named men:

> `مرسلا، أو مسندا، عن ثقة، أو ضعيف، أو مجهول، لإطلاق النص والإجماع`

This is an explicit broad later interpretation: connected or mursal, through a trustworthy, weak, or unknown source. It is best modeled as `report_authentication_rule`, with al-Ḥurr as claimant and the Kashshī formula as asserted basis. It is not early direct tawthīq of each weak or unknown person.

### 6.3 Al-Fayḍ al-Kāshānī: grammar blocks the expansion

Al-Fayḍ, *al-Wāfī*, vol. 1, printed p. 27 ([exact page](https://ablibrary.net/book_content/b/7693/125); host item 125 displays the printed page), records that a group of later scholars understood the formula to authenticate reports without considering the justice of Imam-side sources, then answers:

> `هذه العبارة ليست صريحة في ذلك ولا ظاهرة فيه، فإن ما يصح عنهم إنما هو الرواية لا المروي`

For him, what is reliably established **from** the members is the act of transmission, not automatically the transmitted content and its entire route. This is not a denial of the roster members' standing; it is a denial of the inferential leap.

### 6.4 Al-Khūʾī on the Kashshī notices

Al-Khūʾī lays out and rejects the blanket reading in *Muʿjam rijāl al-ḥadīth*, vol. 1, pp. 57–60 ([p. 57](https://lib.eshia.ir/14036/1/57), [p. 58](https://lib.eshia.ir/14036/1/58), [p. 59](https://lib.eshia.ir/14036/1/59), [p. 60](https://lib.eshia.ir/14036/1/60)). He notes that the expansive position would cover even a known sinner or fabricator, an unknown intermediary, and an omitted link. His positive reading is:

> `إن كلام الكشي لا ينظر إلى الحكم بصحة ما رواه أحد المذكورين عن المعصومين ... وإنما ينظر إلى بيان جلالة هؤلاء، وأن الإجماع قد انعقد على وثاقتهم وفقههم وتصديقهم فيما يروونه`

He then makes the grammatical point also found in al-Fayḍ:

> `فإن ما يصح عنهم إنما هو الرواية لا المروي`

He adds two independent barriers. First, even a transmitted consensus about a legal/uṣūlī rule would not automatically be probative under his theory of consensus. Second, the roster members do in fact narrate from weak persons in multiple places. Thus his conclusion is not based only on one lexical preference.

The practical consequence recurs in individual entries. On Ṣabāḥ b. Ṣiyāba, *Muʿjam*, vol. 10, p. 100 ([exact page](https://lib.eshia.ir/14036/10/100)), he says:

> `الإجماع لم يقم إلا على وثاقة هؤلاء أنفسهم، دون من يروون عنه`

On Marzubān b. ʿImrān, vol. 19, p. 127 ([exact page](https://lib.eshia.ir/14036/19/127)), he says the consensus about what is soundly established from Ṣafwān does not establish the reliability of the person from whom Ṣafwān narrates.

### 6.5 Al-Khūʾī on the trio and al-Ṭūsī's *ʿUdda*

Al-Khūʾī separately analyzes the trio at vol. 1, pp. 61–63 ([p. 61](https://lib.eshia.ir/14036/1/61), [p. 62](https://lib.eshia.ir/14036/1/62), [p. 63](https://lib.eshia.ir/14036/1/63)). After quoting al-Ṭūsī's rule, he says `ولكن هذه الدعوى باطلة`. His reasons include:

- the claimed communal practice is not established merely by al-Ṭūsī's report;
- al-Ṭūsī himself rejects particular *mursal* reports of Ibn Abī ʿUmayr and ʿAbd Allāh b. al-Mughīra in his applied works;
- soundly transmitted examples show Ṣafwān or Ibn Abī ʿUmayr narrating from persons al-Khūʾī considers weak, including ʿAlī b. Abī Ḥamza, Yūnus b. Ẓabyān, and Abū Jamīla.

At p. 63 he explicitly identifies the last example:

> `وروى بسند صحيح عن صفوان بن يحيى عن أبي جميلة، وأبو جميلة هو المفضل بن صالح ضعفه النجاشي`

This rejects both an exceptionless empirical premise and its automatic personal-tawthīq consequence. It does not erase the historical fact that al-Ṭūsī stated and used a special rule.

Al-Khūʾī applies the distinction again in al-Mufaḍḍal b. Ṣāliḥ's entry, vol. 19, pp. 311–312 ([p. 311](https://lib.eshia.ir/14036/19/311), [p. 312](https://lib.eshia.ir/14036/19/312)). Here the upstream view can also be checked directly. Al-Waḥīd al-Bihbahānī, *Taʿlīqa ʿalā Manhaj al-maqāl*, displayed p. 340 in the digitized al-Maktaba al-Shīʿiyya text ([exact page; the URL index is 342](https://usul.ai/ms/t/tacliqa-cala-manhaj/342); the host exposes no full print imprint), writes:

> `ورواية الأجلة ومن أجمعت العصابة على تصحيح ما يصح عنه كابن أبي عمير وابن المغيرة والحسن بن محبوب والبزنطي في الصحيح والحسن بن علي بن فضال يشهد بوثاقته والاعتماد عليه، ويؤيده كونه كثير الرواية سديدة مفتى بها`

Thus al-Bihbahānī combines narration by leading/consensus figures with frequency, soundness of the material, and juristic reception; he does not rest on roster membership alone. Al-Khūʾī responds:

> `مر غير مرة أن كثرة الرواية، ورواية الأجلة وأصحاب الإجماع عن رجل لا تدلان على وثاقته`

For al-Khūʾī, even a possible indication cannot overcome what he treats as al-Najāshī's transmitted agreement on weakness. The dependency is now explicit: al-Khūʾī quotes and rejects an independently located argument of al-Bihbahānī, rather than supplying the only witness to that argument.

### 6.6 Al-Māmaqānī: broad utility with object-sensitive nuance

Al-Māmaqānī cannot be encoded safely as simply “accepts blanket tawthīq.” In the old *Tanqīḥ al-maqāl*, vol. 3, printed p. 253, entry on Mūsā b. Burayd ([exact page](https://ablibrary.net/book_content/b/18294/159); the URL uses an internal item index), he leaves the man's personal condition unknown and says Ṣafwān's narration does not put him among the *ḥasan* transmitters, yet adds in substance that the report Ṣafwān narrates from him is taken because Ṣafwān belongs to the consensus group. That is explicitly **report-specific benefit without personal reclassification**.

The expanded *Tanqīḥ*, vol. 32, p. 354, entry on Salama b. Mihriz ([exact page](https://ablibrary.net/book_content/b/13822/354)), preserves a broader argument in the base discussion: narration by Ṣafwān and Jamīl makes the subject trustworthy or “in the ruling of trustworthy,” rendering the report sound. The separately marked `حصيلة البحث` concludes that reflection on his reports plus narration by leading and consensus transmitters, if it does not prove reliability, at least proves *ḥusn*.

Authorship layers matter. The volume title page identifies ʿAbd Allāh al-Māmaqānī as the original author and Muḥyī al-Dīn al-Māmaqānī and Muḥammad Riḍā al-Māmaqānī with `تحقيق واستدراك` ([vol. 32 title page](https://ablibrary.net/book_content/b/13822/1)). A `حصيلة البحث` marked as an editorial/research addition cannot be silently assigned to the original author's voice. Usul16 should store the base statement and the later *ḥaṣīla* separately.

### 6.7 Al-Tustarī: source criticism before rule application

Al-Tustarī's *Qāmūs al-rijāl*, vol. 9, pp. 101–102 ([p. 101](https://ablibrary.net/book_content/b/13929/101), [p. 102](https://ablibrary.net/book_content/b/13929/102)), reviews an argument that one may act on a report from a disputed man when Ibn Maḥbūb transmits it, because Ibn Maḥbūb is of the consensus group, but not when Ḥarīz or Saʿd transmits it. Al-Tustarī first corrects a source error—`ما ذكره من رواية سعد عنه خبط`—and then asks why the other transmission should not also be acted on. The passage demonstrates resistance to a mechanical transmitter switch and insistence on checking the actual routes; it is not, by itself, a universal blanket theorem.

In *al-Najʿa fī sharḥ al-Lumʿa*, vol. 9, pp. 249–250 ([p. 249](https://ablibrary.net/book_content/b/7439/249), [p. 250](https://ablibrary.net/book_content/b/7439/250)), he insists that al-Ṭūsī did not himself claim the Kashshī consensus and distinguishes al-Ṭūsī's applied acceptance of non-Imāmī reports in the absence of an Imāmī opponent or communal rejection. He further proposes an upstream dependency from al-Kashshī to al-ʿAyyāshī and then to ʿAlī b. al-Ḥasan b. Faḍḍāl. That dependency is al-Tustarī's historical inference, not an independently verified chain for all three notices. Its value is methodological: identify who is making the consensus claim before treating “the companions agreed” as an unmediated observation.

## 7. *Kāmil al-ziyārāt* and *Tafsīr al-Qummī* are independent blanket claims

These two prefaces are often placed beside Aṣḥāb al-Ijmāʿ, but their evidence graphs do not begin with al-Kashshī.

### 7.1 *Kāmil al-ziyārāt*

Ibn Qūlawayh's preface, *Kāmil al-ziyārāt*, ed. Jawād al-Qayyūmī and committee, Muʾassasat Nashr al-Fiqāha, p. 37 ([exact page](https://ablibrary.net/book_content/b/3273/37)), says that the author cannot encompass everything narrated on the subject, but includes what reached him:

> `من جهة الثقات من أصحابنا ... ولا أخرجت فيه حديثا روي عن الشذاذ من الرجال`

The dispute is whether this certifies every person in every chain, only Ibn Qūlawayh's direct teachers, or the material selected under the work's chapter purposes. Al-Nūrī, *Khātimat Mustadrak al-wasāʾil*, ed. Muʾassasat Āl al-Bayt li-Iḥyāʾ al-Turāth, Qum, first ed. 1416 AH, vol. 3, pp. 522–523 ([p. 522](https://www.masaha.org/book/view/3528/page/522), [p. 523](https://www.masaha.org/book/view/3528/page/523)), treats the preface as authentication of the bounded group from whom Ibn Qūlawayh directly narrated:

> `فتراه رحمه الله نصّ على توثيق كلّ من روى عنه فيه ... ولا فرق في التوثيق بين النص على أحد بخصوصه أو توثيق جمع محصورين بعنوان خاص`

The *Kāmil* edition's introduction points to this same passage and reading; see p. 28 ([exact page](https://ablibrary.net/book_content/b/3273/28)). This is a verified direct source plus an editorial cross-reference, not two independent arguments.

Al-Khūʾī's position is time-dependent. The early printed methodological discussion uses the preface broadly; see *Muʿjam*, vol. 1, p. 50 ([exact page](https://lib.eshia.ir/14036/1/50)). In the later *Ṣirāṭ al-najāh*, vol. 2, “Masāʾil rijāliyya,” question 1427, p. 457 ([exact page](https://najafdesertlibrary.com/book/%D8%B5%D8%B1%D8%A7%D8%B7-%D8%A7%D9%84%D9%86%D8%AC%D8%A7%D8%A9-%D8%AA%D8%B9%D9%84%D9%8A%D9%82-%D8%A7%D9%84%D9%85%D9%8A%D8%B1%D8%B2%D8%A7-%D8%A7%D9%84%D8%AA%D8%A8%D8%B1%D9%8A%D8%B2%D9%8A/v/2/p/457)), he states:

> `فقد رأينا أخيرا اختصاص التوثيق بخصوص المشايخ المروي عنهم بلا واسطة`

That is, he finally restricted its authentication to direct teachers. The implementation must attach effective chronology/version to a scholar judgment instead of overwriting his earlier published reasoning or treating both as simultaneous.

### 7.2 *Tafsīr al-Qummī*

The extant preface to *Tafsīr al-Qummī*, Muʾassasat Dār al-Kitāb li-l-Ṭibāʿa wa-l-Nashr, Qum, vol. 1, printed p. 4 / digital p. 30 ([exact page](https://ablibrary.net/book_content/b/5124/30)), states:

> `ونحن ذاكرون ومخبرون بما ينتهي إلينا ورواه مشايخنا وثقاتنا عن الذين فرض الله طاعتهم`

Al-Khūʾī accepts a chain-wide inference for reports in the Tafsīr that terminate at the Imams, arguing there is no basis for restricting the certification to direct teachers; *Muʿjam*, vol. 1, p. 49 ([exact page](https://lib.eshia.ir/14036/1/49)). This shows that his rejection of a broad Kashshī inference is not a general hostility to collective tawthīq. He distinguishes the wording and scope of each source.

The extant Tafsīr's composite textual history, including Abū al-Jārūd material and differing strata, makes attribution and preface scope prior questions. Thus the rule should be conditional on `passage belongs to certified stratum` and on the selected scholar's theory. It must not be merged with the Kashshī roster or transferred to unrelated chains.

## 8. Four Books corpus audit

### 8.1 Method and limits

The read-only audit used `eshia-research/eshia_research.db` and the parsed `chains`/`chain_nodes` tables for the Four Books only:

| Work | local `books.id` |
|---|---:|
| *Tahdhīb al-aḥkām* | 420 |
| *al-Istibṣār* | 1160 |
| *al-Kāfī* | 1178 |
| *Man lā yaḥḍuruhu al-faqīh* | 1294 |

Counts below are parser observations, not critical-edition stemmata. One hadith may contain multiple branches, one chain may contain multiple roster members, and the same ancient report may recur in more than one collection. Consequently, node, parsed-chain, and hadith-row counts are reported separately and are never labeled “independent traditions.” Arabic token normalization can also join or split aliases; every doctrinally significant example was checked against the displayed isnād.

### 8.2 Ibn Abī ʿUmayr and explicit anonymity

Normalized tokens matching Ibn Abī ʿUmayr produced:

- 5,200 chain nodes;
- 5,132 distinct parsed chains;
- 4,402 hadith rows.

The immediate Imam-side next-node classification was:

| next node type | nodes | hadith rows |
|---|---:|---:|
| named narrator | 4,913 | 4,140 |
| collective phrase | 122 | 120 |
| unknown person | 109 | 102 |
| Imam | 21 | 20 |
| pronoun | 2 | 2 |

Two normalized collective surfaces, `بعض أصحابه` and `بعض أصحابنا`, together occurred as the immediate next link in 157 nodes/chains across 151 hadith rows (79/75 and 78/76 respectively before union). This establishes that explicit anonymity is a real structural feature after Ibn Abī ʿUmayr; it does not identify the missing persons or decide the ancient convention's legal effect.

Literal samples include:

- *al-Kāfī*, vol. 1, p. 38, **alkafi-74**: `عَلِيُّ بْنُ إِبْرَاهِيمَ عَنْ أَبِيهِ عَنِ ابْنِ أَبِي عُمَيْرٍ عَنْ بَعْضِ أَصْحَابِهِ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ` ([exact page](https://lib.eshia.ir/11005/1/38)).
- *al-Kāfī*, vol. 1, p. 40, **alkafi-84**: `... ابْنِ أَبِي عُمَيْرٍ عَنْ بَعْضِ أَصْحَابِنَا عَنْ أَبِي عَبْدِ اللَّهِ ...` ([exact page](https://lib.eshia.ir/11005/1/40)).
- *Tahdhīb al-aḥkām*, vol. 1, p. 41, **tahdhib-113**: `... يعقوب بن يزيد عن ابن أبي عمير عن بعض أصحابنا عن أبي عبد الله ...` ([exact page](https://lib.eshia.ir/10083/1/41)).

A naïve resolver that replaces each `بعض أصحابنا` with a synthetic “trusted person” corrupts both identity and epistemic status. The node must remain anonymous; a method-specific report rule may be applied on top of it.

### 8.3 Consensus transmitters narrating from Abū Jamīla

A targeted alias query for the stable third-stratum names most relevant to the later trio claim—Yūnus, Ṣafwān, Ibn Abī ʿUmayr, Ibn al-Mughīra, Ibn Maḥbūb/al-Ḥasan b. Maḥbūb, and al-Bazanṭī—followed immediately Imam-side by Abū Jamīla/al-Mufaḍḍal b. Ṣāliḥ found **61 matched member nodes in 59 Four Books hadith rows**. The two-count difference includes more than one relevant member in a branch; cross-work parallels also mean the 59 rows are not 59 independent ancient reports.

Checked examples:

- *Tahdhīb*, vol. 6, p. 266, **tahdhib-7695**: `يونس بن عبد الرحمن عن المفضل بن صالح عن زيد الشحام` ([exact page](https://lib.eshia.ir/10083/6/266)); compare the parallel *al-Istibṣār*, vol. 3, p. 27, **istibsar-3163** ([exact page](https://lib.eshia.ir/11010/3/27)).
- *al-Istibṣār*, vol. 4, p. 242, **istibsar-5343**: `يونس ... عن المفضل بن صالح عن بعض أصحابه` ([exact page](https://lib.eshia.ir/11010/4/242)).
- *al-Kāfī*, vol. 4, p. 188, **alkafi-6686**: `... أحمد بن محمد بن أبي نصر وابن محبوب جميعا عن المفضل بن صالح عن محمد بن مروان` ([exact page](https://lib.eshia.ir/11005/4/188)).
- *al-Kāfī*, vol. 6, p. 531, **alkafi-12915**: `... صفوان بن يحيى عن أبي جميلة عن حميد الصيرفي ...` ([exact page](https://lib.eshia.ir/11005/6/531)).
- *al-Kāfī*, vol. 7, p. 44, **alkafi-13208**: `... أحمد بن محمد بن أبي نصر عن أبي جميلة المفضل بن صالح` ([exact page](https://lib.eshia.ir/11005/7/44)).

These are high-value falsification tests. If al-Najāshī's adverse class notice is accepted, the proposition “these men never narrate from a weak person” cannot describe the extant corpus without qualification. The observation does **not** settle three different questions: whether Abū Jamīla's adverse evidence is finally decisive; whether a roster member transmitted before learning of a defect; and whether a jurist may nevertheless accept a particular report by special convention or corroboration.

### 8.4 What the corpus can and cannot infer

| Corpus observation | Licensed inference | Unlicensed inference |
|---|---|---|
| explicit `بعض أصحابنا` after Ibn Abī ʿUmayr | anonymity/irsāl exists and needs special treatment | the missing person has been individually identified and graded |
| roster member → adversely assessed narrator | exceptionless “only narrates from thiqa” needs a qualification or rejection | every such report is false |
| many transmissions from one person | frequency and network centrality are corroborative indicators | frequency alone equals early tawthīq |
| parallel in two Four Books | reception and textual comparison become possible | two independent witnesses automatically exist |

## 9. Evidence-dependency graph

```text
Kashshī roster notice 1 ──> member truthfulness/fiqh claim + first-slot variant
Kashshī roster notice 2 ──> disputed semantics of "taṣḥīḥ mā yaṣiḥḥ"
Kashshī roster notice 3 ──> same semantic dispute + complex third-slot variants
          │
          ├──> broad reading: Mīr Dāmād; al-Ḥurr
          └──> narrow/member reading: al-Fayḍ; al-Khūʾī

Ṭūsī, ʿUdda ──> separate trio/comparable-transmitter mursal convention
          ├──> supported context: Najāshī on confidence in Ibn Abī ʿUmayr's marāsīl
          ├──> challenged by: Ṭūsī's applied rejections, according to Khūʾī
          └──> challenged empirically: named weak-source examples

Kāmil preface ──> its own bounded-class dispute
          └──> Khūʾī position changes: broad published use → late direct-shaykh restriction

Tafsīr al-Qummī preface ──> its own attribution/scope dispute
          └──> Khūʾī accepts chain-wide certification for qualifying chains

Four Books corpus ──> structural evidence and counterexamples
          └──> never itself creates an ancient consensus or personal tawthīq
```

Important dependency discounts:

1. Mīr Dāmād, al-Ḥurr, al-Fayḍ, and al-Khūʾī are rival readings of the same Kashshī words, not four independent early attestations.
2. A later biographical entry quoting al-Ṭūsī or al-Kashshī is a transmission/interpretation node, not a fresh observation.
3. The individual Ibn Abī ʿUmayr evidence is partly independent of the roster formula and should remain separately weighted.
4. Al-Khūʾī's Abū Jamīla argument depends both on chain identification and on his acceptance/reading of al-Najāshī's adverse statement.
5. The Kāmil and Tafsīr prefaces are neither consequences nor confirmations of the Kashshī notices. Their apparent similarity is taxonomic, not genealogical.

## 10. Method-indexed adjudication

### 10.1 Strict early-biographical method

- Give the stable named members the positive predicates the Kashshī notices actually support, with wording and source preserved.
- Keep disputed roster slots conditional on textual variant.
- Do not infer a personal `thiqa` grade for every Imam-side narrator.
- Treat al-Ṭūsī's *ʿUdda* as important early methodological testimony, but do not turn a mursal-equivalence rule into identified-person tawthīq.
- For any concrete report, apply the ordinary chain analysis unless the selected method independently adopts the special convention.

### 10.2 Broad consensus-report method

A method following Mīr Dāmād or al-Ḥurr may mark a report as acceptable/“counted sound” when a securely identified roster member is the relevant transmission point, even with an unknown, omitted, or adversely graded Imam-side link. The result must say:

```text
accepted_by = broad_ashab_al_ijma_rule
object = report_occurrence
member_identity = resolved
roster_variant = applicable
ordinary_chain_grade = retained separately
```

It must not overwrite the weak/unknown narrator's person record, because the cited authors' report convention and person authentication are not identical claims.

### 10.3 Al-Ṭūsī-*ʿUdda* mursal method

This is narrower in membership and more specific in rationale. It should require:

- an authenticated identity as Ibn Abī ʿUmayr, Ṣafwān, al-Bazanṭī, or a separately justified comparable transmitter;
- an actual omitted/anonymous link or other route shape to which the rule is directed;
- preservation of al-Ṭūsī's stated contextual condition;
- a separate ordinary structural label such as `mursal`;
- no synthetic person for the omission.

### 10.4 Al-Khūʾī's method

- The roster notices establish the named members' own reliability/standing, not that of their sources.
- Narration by leading or consensus transmitters and frequency do not independently prove the source reliable.
- The trio rule is rejected as a general proof.
- Independent general tawthīq remains possible where the wording warrants it: notably his chain-wide reading of qualifying *Tafsīr al-Qummī* chains.
- *Kāmil al-ziyārāt* must be time-indexed: broad earlier application; late restriction to Ibn Qūlawayh's direct teachers.

### 10.5 Cumulative-qarāʾin method

Narration by a roster member can contribute a weighted indicator alongside frequency, multiple independent leading transmitters, content reception, absence/presence of adverse evidence, book-route history, and explicit statements. The output may be `ḥasan` or probable reliability under a named scholar's calculus. The evidence must be discounted for shared dependencies and must never be described as an explicit early tawthīq.

### 10.6 Tawaqquf conditions

Suspend rather than force a verdict when:

- the surface form does not securely identify the roster member;
- the relevant roster membership depends on an unresolved variant;
- chain direction or parser segmentation is uncertain;
- the chosen method does not accept a blanket rule and the Imam-side person lacks independent evidence;
- a preface-based rule is invoked but the passage's textual stratum or scope is disputed;
- the decisive later opinion cannot be tied to a precise authorial layer or date.

## 11. Implementation consequences and naïve-database traps

### 11.1 Required record types

| Record | Minimum fields |
|---|---|
| `collective_notice` | source, exact Arabic, edition/page/link, claimant, reported collective, claim type |
| `roster_slot` | notice, stratum, stable/variant, person candidate, variant attribution, textual note |
| `rule_interpretation` | scholar, date/version, source passage, scope, object (`person`/`report`/`route`), conditions |
| `rule_application` | report/chain occurrence, resolved member node, method, result, confidence, exception flags |
| `person_judgment` | subject person, scholar/source, grade, direct/inferred, evidence dependencies |
| `structural_observation` | chain node(s), direction, surface form, parser version, checked/not checked |
| `method_revision` | scholar, earlier proposition, later proposition, chronology and source |

### 11.2 Inference rules that should fail closed

```text
IF person is in any roster variant
THEN do not automatically grade every Imam-side node.

IF report is accepted under a blanket rule
THEN retain its ordinary chain defects and person grades.

IF anonymous node follows Ibn Abi Umayr
THEN keep node anonymous; attach only a method-specific route judgment.

IF scholar changes position
THEN add a later superseding judgment for that scholar/method;
     do not delete the historical earlier judgment.

IF source is an editorial footnote, quoted extract, or hasila layer
THEN preserve that authorship/provenance layer.
```

### 11.3 Common traps

1. **Static eighteen-person table.** It erases the Abū Baṣīr and third-roster variants.
2. **Consensus-member propagation.** It turns an inference about reports into thousands of fabricated early person grades.
3. **Merging Kashshī and *ʿUdda*.** It attributes al-Ṭūsī's trio rationale to all three rosters.
4. **Synthetic anonymous thiqa.** It pretends `بعض أصحابنا` is an identified authority.
5. **Ignoring direction.** It applies the rule to a compiler-side teacher rather than the member's Imam-side source.
6. **Overwriting ordinary chain quality.** Users can no longer see why two methods disagree.
7. **Counting parallels as independence.** Tahdhīb/Istibṣār duplicates inflate corroboration.
8. **Treating leading narration as express tawthīq.** Cumulative evidence becomes a false quotation.
9. **Collapsing Kāmil, Tafsīr, and the rosters.** Three different source prefaces/notices become one imaginary universal rule.
10. **Timeless al-Khūʾī flag.** His late Kāmil restriction disappears.
11. **Misattributing `حصيلة البحث`.** A later editorial/research conclusion becomes ʿAbd Allāh al-Māmaqānī's verbatim judgment.
12. **Unqualified counterexample logic.** Narration from Abū Jamīla is made to prove either that the report is false or that Abū Jamīla is certainly reliable; neither follows without more premises.

## 12. Source register and bounded limitations

| Source | Located evidence | Status/limitation |
|---|---|---|
| al-Kashshī/al-Ṭūsī, *Ikhtiyār* | three exact roster pages | primary authorial text within surviving selection; variant grammar preserved |
| al-Ṭūsī, *ʿUdda* | exact mursal rule | primary methodological text; relation to Kashshī is disputed/inferred |
| al-Ṭūsī, *Fihrist* | explicit Ibn Abī ʿUmayr praise | primary person-level control |
| al-Najāshī | Ibn Abī ʿUmayr marāsīl context; Abū Jamīla class criticism | primary early biographical evidence; distinguish author report from quoted collective |
| attributed Ibn al-Ghaḍāʾirī | harsh Abū Jamīla entry | exact text located; book attribution/transmission disputed |
| Mīr Dāmād | broad report reading and 21/22 count | later interpretation, not fresh early consensus |
| al-Ḥurr | explicit weak/unknown-inclusive report rule | later broad interpretation |
| al-Fayḍ | grammatical rejection | later narrow interpretation |
| al-Khūʾī | full roster/trio reasoning and applications | direct text located; Kāmil position must be chronological |
| al-Māmaqānī corpus | report/person nuance | base author and later *ḥaṣīla* layers must remain distinct |
| al-Tustarī | route correction and source-dependency critique | direct pages located; not reducible to one universal verdict |
| al-Bihbahānī | Abū Jamīla cumulative reasoning | direct p. 340 text located; combines consensus narration with other indicators |
| al-Nūrī | bounded Kāmil direct-shaykh claim | original *Khātima*, vol. 3, pp. 522–523 directly verified; *Kāmil* introduction is a dependent cross-reference |
| Four Books | checked literal chains and structural counts | local parsed-corpus evidence; not a substitute for critical-edition collation |

The remaining limitations are bounded rather than outcome-changing: the digitized *Taʿlīqa* does not expose a full print imprint; no manuscript stemma for the Kashshī roster variants was attempted; and the corpus figures describe the current parsed project snapshot rather than a deduplicated critical edition. None is concealed as certainty or converted into a missing quotation.

## 13. Final resolution

The Aṣḥāb al-Ijmāʿ material is genuine high-value collective evidence, but “blanket tawthīq” is not one indivisible doctrine. The three Kashshī notices authenticate and rank named transmitters through textually variant rosters; al-Ṭūsī's *ʿUdda* adds a separate special rule for the *marāsīl* of a named trio and comparable persons; later scholars then disagree over whether either source validates whole reports across weak, unknown, or omitted intermediaries.

For Usul16, the correct resolution is:

- **person level:** strong positive judgment for securely identified roster members, with variant membership explicit;
- **Imam-side person level:** no automatic tawthīq from roster transmission alone;
- **report level:** broad acceptance is available only under a named historical methodology and must coexist with the ordinary chain analysis;
- **mursal level:** al-Ṭūsī's convention is stored independently and can be enabled or rejected by method;
- **preface level:** Kāmil and Tafsīr claims remain source-specific, scoped, and chronological;
- **uncertain cases:** tawaqquf is a first-class result.

This representation explains why careful scholars can agree on the Arabic source texts yet reach different report grades. It also prevents the most damaging implementation error: converting a disputed report-level convention into thousands of fictitious early personal tawthīqs.
