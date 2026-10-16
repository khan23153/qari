# Published spellings at the recognition boundary

Qari displays Uthmani text. The independent Arabic recognizer can emit Imla'i
spellings and separate `يا` from the following word. These are representation
differences, not evidence of a pronunciation mistake.

The three explicit spelling pairs in `streaming_session.py` are independently
published in the `quran-simple-clean` Quran edition:
<https://api.alquran.cloud/v1/quran/quran-simple-clean>.
The locally verified complete edition has SHA256
`e9f87186120851fbf1e04813a423076850e1b6b9ad769a797117dca623aad4af`.

| Imla'i | Uthmani | Example |
| --- | --- | --- |
| نحيي | نُحْىِ | 36:12 |
| يحيي | يُحْىِ | 36:78 |
| شيئا | شَيْـًٔا | 36:23, 36:54, 36:82 |

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
