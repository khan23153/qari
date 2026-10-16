"""Independent RNNT spaces around waw must not shift Quran reference alignment."""
import math
from types import SimpleNamespace
import pytest
from ml.inference.fastconformer_transcriber import decode_result


def native(words,confidences,times):
    return SimpleNamespace(tokens=['▁'+w for w in words],ys_log_probs=[math.log(c)for c in confidences],timestamps=times)


def test_split_waw_merges_with_conservative_native_score_and_full_time_span():
    result=decode_result(native(['سمعهم','و','على','أبصارهم'],[.98,.79,.931,.74],[117.28,118.96,119.36,121.36]))
    assert result.words==['سمعهم','وعلى','أبصارهم']
    assert result.confidences==pytest.approx([.98,.79,.74])
    assert result.timings==[(117.28,117.28),(118.96,119.36),(121.36,121.36)]


def test_weak_waw_does_not_gain_confidence_from_strong_following_word():
    result=decode_result(native(['و','الله'],[.2,.99],[.1,.3]))
    assert result.words==['والله']
    assert result.confidences==pytest.approx([.2])
    assert result.timings==[(.1,.3)]


@pytest.mark.parametrize('words,times',[
    (['و','على'],[.1,1.6]),
    (['و','ا'],[.1,.3]),
    (['و','hello'],[.1,.3]),
    (['و'],[.1]),
])
def test_separated_letters_foreign_text_and_distant_words_are_not_joined(words,times):
    result=decode_result(native(words,[.9]*len(words),times))
    assert result.words==words


def test_joined_word_and_unrelated_native_confidences_stay_unchanged():
    result=decode_result(native(['وعلى','قلوبهم'],[.9,.8],[.1,.5]))
    assert result.words==['وعلى','قلوبهم']
    assert result.confidences==pytest.approx([.9,.8])

def test_tatweel_is_not_a_second_base_letter():
    result=decode_result(native(['و','اـ'],[.9,.8],[.1,.3]))
    assert result.words==['و','اـ']
