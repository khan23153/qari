"""The phonemizer must write what IqraEval's references write (checked on their data)."""
from ml.alignment.quran_g2p import ayah_word_phonemes, phonemize, phonemize_words
from ml.inference.pronunciation_verifier import VerifierResult, word_verdicts


def test_quranmb_reference_verse_is_reproduced_exactly():
    # QuranMB.v2 reference for 35:28 (part).
    ref = "< i nn a m aa y a x $ aa ll a h a m i n E i b aa d i h i l E u l a m aa < u"
    assert " ".join(phonemize("إِنَّمَا يَخْشَى اللَّهَ مِنْ عِبَادِهِ الْعُلَمَاءُ")) == ref


def test_iqra_train_sentence_style():
    # Iqra_train references: tanween dropped, last word in pause.
    assert " ".join(phonemize("فِيهِنَّ خَيْرَاتٌ حِسَانٌ", style="sentence")) == "f ii h i nn a x A y r aa t H i s aa n"
    assert (" ".join(phonemize("أَضَاعَ الطِّفْلُ الصَّغِيرُ النُّقُودَ", style="sentence"))
            == "< A D AA E a TT I f l u SS A g II r u nn U q UU d")


def test_quran_style_reads_tanween_and_keeps_the_last_vowel():
    assert phonemize("زَوْجًا غَيْرَهُ") == "z a w j a n aa g A y r a h u".split()


def test_sun_letters_hamzat_wasl_and_emphatic_vowels():
    assert phonemize("الصِّرَاطَ الْمُسْتَقِيمَ") == "< A SS I r AA T A l m u s t A q II m a".split()
    assert phonemize("بِسْمِ اللَّهِ") == "b i s m i ll a h i".split()


def test_words_keep_their_own_phonemes():
    per = phonemize_words(["إِيَّاكَ", "نَعْبُدُ"])
    assert per == [["<", "ii", "y", "aa", "k", "a"], ["n", "a", "E", "b", "u", "d", "u"]]


def test_lexicon_covers_the_whole_quran():
    assert ayah_word_phonemes(1, 1) == [["b", "i", "s", "m", "i"], ["ll", "a", "h", "i"],
                                         ["rr", "a", "H", "m", "a", "n", "i"], ["rr", "a", "H", "ii", "m", "i"]]
    assert len(ayah_word_phonemes(2, 255)) == 50
    assert ayah_word_phonemes(115, 1) is None


def test_word_verdicts_take_the_worst_phoneme():
    result = VerifierResult([.1, .2, .9, .05, .3], threshold=.35)
    assert word_verdicts([["a", "b"], ["c", "d", "e"], []], result) == [.2, .9, None]
    assert result.flags() == [False, False, True, False, False]
