# Published spellings at the recognition boundary

Qari displays Uthmani text. The independent Arabic recognizer can emit Imla'i
spellings and separate `يا` from the following word. These are representation
differences, not evidence of a pronunciation mistake.

The representation identities below are independently published in the
`quran-simple-clean` Quran edition:
<https://api.alquran.cloud/v1/quran/quran-simple-clean>.
The locally verified complete edition has SHA256
`e9f87186120851fbf1e04813a423076850e1b6b9ad769a797117dca623aad4af`.

| Imla'i | Uthmani | Example |
| --- | --- | --- |
| نحيي | نُحْىِ | 36:12 |
| يحيي | يُحْىِ | 36:78 |
| شيئا | شَيْـًٔا | 36:23, 36:54, 36:82 |
| الصلاة | ٱلصَّلَوٰةَ | 2:3 |
| إيلافهم | إِۦلَـٰفِهِمْ | 106:2 |
| أأنذرتهم | ءَأَنذَرْتَهُمْ | 2:6, 36:10 |
| أأتخذ | ءَأَتَّخِذُ | 36:23 |
| يستهزئون | يَسْتَهْزِءُونَ | 36:30 |
| مستهزئون | مُسْتَهْزِءُونَ | 2:14 |
| متكئون | مُتَّكِـُٔونَ | 36:56 |
| أقصى | أَقْصَا | 36:20 |

These pairs compare actual recognized words; they never enter the recognizer.
Each pair uses the published Imla'i spelling as its common comparison key when
the verified Uthmani form exists in the complete loaded corpus. These explicit
spelling identities also block lossy legacy aliases from assigning either key
another identity. An original final `يى` retains maqsura, so `يحيى`
(Yahya / yahya) and `يحيي` (yuhyi) remain distinct. Protection precedes small-high
ya expansion: Uthmani `يُحْـِۧىَ` still becomes `يحيي`. Punctuation and Persian
ya variants are handled before this distinction.
Other existing maqsura comparison keys remain compatible.

A native `يا` and its following native word may be grouped when their joined
form is one of the independently verified vocatives `ياقوم`, `ياليت`,
`ياحسرة`, `ياويلنا`, `يابني`, occurs in the complete Quran corpus, and their emission gap is at most
0.8 seconds. The result keeps the minimum of both original confidence scores
and their combined emission span. A missing or weak particle cannot be supplied
by expected text. Untimed outputs are never grouped. Ordinary verbs such as `يأمن`, `يأكل`
and `يأمر` cannot authorize a join even though their lossy keys start with `يا`. No thresholds, models,
speech budgets or final-recording chunk bounds are changed.

Recognition may still confuse these pronunciations. Spelling conversion does
not prove phonetic correctness or tajweed quality.

Production word confirmation uses strict identity after exact printed-word
canonicalization and established printed alef spelling families. Generic character
distance, article removal and text-derived phonetic similarity no longer prove
a production match. Close unknown text remains an unconfirmed recognition gap;
known different Quran words retain the existing supported-error behavior.
The legacy approximate matcher and legacy clean-word aliases are available to
explicit test/development callers; production does not use those lossy aliases.
Neither the confidence threshold nor the speech/cursor guards are lowered.

The immutable `app/data/published_word_spellings.json` contains 660 exact raw
Uthmani forms, including case-ending variants, and their Imla'i spellings. The
compiler `scripts/build_published_word_spellings.py` verifies the complete source
edition's hash and compares same-ayah lexical units. It groups vocative boundaries
only while comparing the two printed editions; runtime conversion remains one
token to one token and never manufactures a missing `يا` or confidence score.
Unaligned verses and ambiguous raw spellings supply no conversion.

Conversion occurs per token before diacritic/hamza carrier normalization. This
retains `يَسْـَٔلُكُمْ` as `يسالكم`, without rewriting bare `يسلكم`. Initial
interrogative `ءَأَتَّخِذُ` retains two alefs and cannot become ordinary `اتخذ`.
Normalizing first and globally aliasing the lossy key would erase this distinction.

Sequence placement and correctness are separate. The existing approximate
comparison can score a live DP path or locate a final-review token; it cannot
supply a live anchor, consume a trailing unconfirmed token, confirm a revision,
or create a `MATCHED` verdict. Final placed tokens undergo strict identity
classification independently. This preserves the position of later exact words
without awarding near words correctness. Existing word/ayah ceilings and native
confidence, timing and speech guards still apply.
