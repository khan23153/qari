"""A confident first reference word must survive unrelated invocation text."""
import pytest
from ml.alignment.streaming_matcher import StreamingMatcher, WordStatus

INTRO = ['بسم','الله','الرحمن','الرحيم'] * 2
REFERENCE = ['الم','ذالك','الكتاب']


def matcher():
    return StreamingMatcher(REFERENCE,
        known_error_words=set(REFERENCE + INTRO + ['المص','قال']))


def test_captured_long_invocation_does_not_hide_confident_alif_lam_mim():
    m = matcher()
    words = INTRO + ['الم']
    scores = [.849,1.,.768,.757,.981,.658,.966,.999,.854]
    states = m.evaluate(words,scores)
    assert [(s.index,s.spoken,s.status)for s in states] == [(0,'الم',WordStatus.MATCHED)]
    assert m._live_hyp_indices == {0:8}
    assert m._hyp_cursor == 9


@pytest.mark.parametrize('word,confidence', [('الم',.2),('المص',.95),('قال',.99), ('الم',float('nan')), ('الم',float('inf')), ('الم',1.01)])
def test_invocation_cannot_promote_weak_or_different_first_word(word,confidence):
    m = matcher()
    assert m.evaluate(INTRO+[word],[.99]*8+[confidence]) == []
    assert m._cursor == 0


def test_invocation_alone_never_starts_the_selected_recitation():
    m = matcher()
    assert m.evaluate(INTRO*3,[.99]*24) == []
    assert m._cursor == 0


def test_later_first_word_cannot_discard_earlier_adjacent_opening_anchor():
    reference = ['alpha', 'beta', 'gamma']
    words = ['beta', 'gamma', 'noise', 'alpha']
    m = StreamingMatcher(reference, known_error_words=set(reference + words))
    states = m.evaluate(words, [.9] * len(words))
    assert [(s.index, s.spoken) for s in states if s.status == WordStatus.MATCHED] == [
        (1, 'beta'), (2, 'gamma')]
    assert m._live_hyp_indices == {1: 0, 2: 1}


def test_stalled_opening_uses_existing_corpus_alias_without_changing_slots():
    m = StreamingMatcher(['الرحمان', 'الرحيم'],
        word_aliases={'الرحمن': 'الرحمان'},
        known_error_words=set(INTRO + ['الرحمان', 'الرحيم', 'noise']))
    words = ['noise'] * 8 + ['الرحمن']
    states = m.evaluate(words, [.9] * len(words))
    assert [(s.index, s.spoken, s.status) for s in states] == [
        (0, 'الرحمن', WordStatus.MATCHED)]
    assert m._live_hyp_indices == {0: 8}
