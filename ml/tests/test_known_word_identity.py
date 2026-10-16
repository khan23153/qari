"""Different Quran words cannot become confirmed matches through fuzzy spelling."""
import pytest

from ml.alignment.streaming_matcher import StreamingMatcher, WordStatus


@pytest.mark.parametrize('expected,spoken', [
    ('عليهم','عليكم'),
    ('عليهم','عليه'),
    ('الذين','الذي'),
    ('يكن','يقل'),
])
def test_confident_distinct_known_word_is_error_with_later_anchor(expected, spoken):
    reference = ['انعمت', expected, 'غير']
    vocabulary = {*reference, spoken}
    matcher = StreamingMatcher(reference, known_error_words=vocabulary)
    states = {state.index: state for state in matcher.evaluate(
        ['انعمت',spoken,'غير'], [.95,.841,.95]
    )}
    assert states[1].status == WordStatus.ERROR
    assert states[1].spoken == spoken
    assert states[2].status == WordStatus.MATCHED
    assert matcher._cursor == 3


@pytest.mark.parametrize('expected,spoken', [
    ('عليهم','عليكم'),
    ('عليهم','عليه'),
    ('الذين','الذي'),
])
def test_final_review_does_not_fuzzy_confirm_distinct_known_word(expected, spoken):
    reference = ['انعمت',expected,'غير']
    matcher = StreamingMatcher(reference,known_error_words={*reference,spoken})
    states = matcher.finalize(['انعمت',spoken,'غير'],[.95,.841,.95])
    assert states[1].status == WordStatus.ERROR
    assert states[1].spoken == spoken
    assert states[2].status == WordStatus.MATCHED


def test_partial_known_word_waits_for_revision_before_later_anchor():
    matcher = StreamingMatcher(
        ['انعمت','عليهم','غير'],known_error_words={'انعمت','عليهم','عليه','غير'}
    )
    first = matcher.evaluate(['انعمت','عليه'],[.95,.788])
    assert [(state.index,state.status) for state in first] == [(0,WordStatus.MATCHED)]
    assert matcher._cursor == 1
    revised = matcher.evaluate(['انعمت','عليهم','غير'],[.95,.894,.95])
    assert all(state.status == WordStatus.MATCHED for state in revised)


@pytest.mark.parametrize('expected,spoken', [
    ('الرحمان','الرحمن'),
    ('صرط','صراط'),
    ('الصرط','صرط'),
    ('الحمد','حمد'),
])
def test_known_spelling_variants_remain_confirmable(expected,spoken):
    matcher = StreamingMatcher([expected],known_error_words={expected,spoken})
    states = matcher.evaluate([spoken],[.95])
    assert states[0].status == WordStatus.MATCHED


def test_missing_confidence_cannot_confirm_known_word_substitution():
    matcher = StreamingMatcher(
        ['انعمت','عليهم','غير'],known_error_words={'انعمت','عليهم','عليكم','غير'}
    )
    states = matcher.evaluate(['انعمت','عليكم','غير'],[.95])
    assert [state.index for state in states if state.status == WordStatus.MATCHED] == [0]
    assert not any(state.status == WordStatus.ERROR for state in states)


def test_final_substitution_cannot_borrow_same_word_from_later_position():
    reference = ['انعمت','عليهم','غير','المغضوب','عليهم','ولا']
    spoken = ['انعمت','عليكم','غير','المغضوب','عليهم','ولا']
    matcher = StreamingMatcher(reference,known_error_words={*reference,*spoken})
    states = matcher.finalize(spoken,[.95]*len(spoken))
    assert states[1].status == WordStatus.ERROR
    assert states[1].spoken == 'عليكم'
    assert all(states[i].status == WordStatus.MATCHED for i in [0,2,3,4,5])


def test_unknown_gap_cannot_borrow_same_word_from_later_position():
    reference = ['انعمت','عليهم','غير','المغضوب','عليهم','ولا']
    spoken = ['انعمت','مبهم','غير','المغضوب','عليهم','ولا']
    matcher = StreamingMatcher(reference,known_error_words=set(reference))
    states = matcher.finalize(spoken,[.95]*len(spoken))
    assert states[1].status == WordStatus.SKIPPED
    assert states[1].confidence == 0
    assert all(states[i].status == WordStatus.MATCHED for i in [0,2,3,4,5])


@pytest.mark.parametrize('prefix',['اعوذ','سبحان'])
def test_final_inserted_prefix_does_not_become_a_spoken_substitution(prefix):
    reference = ['بسم','الله','الرحمن','الرحيم']
    spoken = [prefix,'الله',*reference]
    matcher = StreamingMatcher(reference,known_error_words={*reference,prefix})
    states = matcher.finalize(spoken,[.95]*len(spoken))
    assert all(state.status == WordStatus.MATCHED for state in states)
    assert [state.spoken for state in states] == reference


def test_final_repeated_phrase_cannot_repair_earlier_wrong_word():
    reference = ['بذكر','الله','الا','بذكر','الله','تطمين','القلوب']
    spoken = ['ذكر',*reference[1:]]
    matcher = StreamingMatcher(reference,known_error_words={*reference,'ذكر'})
    states = matcher.finalize(spoken,[.95]*len(spoken))
    assert states[0].status == WordStatus.ERROR
    assert states[0].spoken == 'ذكر'
    assert all(state.status == WordStatus.MATCHED for state in states[1:])


def test_final_prefix_recovery_uses_later_anchors_without_promoting_uncertain_word():
    reference = ['بسم','الله','الرحمن','الرحيم']
    spoken = ['سبحان','الله',*reference]
    matcher = StreamingMatcher(reference,known_error_words={*reference,'سبحان'})
    states = matcher.finalize(spoken,[.95,.95,.95,.2,.95,.95])
    assert states[0].status == WordStatus.MATCHED
    assert states[0].spoken == 'بسم'
    assert states[1].status == WordStatus.SKIPPED
    assert states[1].confidence == 0
    assert all(states[i].status == WordStatus.MATCHED for i in [2,3])


@pytest.mark.parametrize('expected,spoken',[
    ('ابراهيم','ابرهم'),
    ('والمنافقات','والمنفقت'),
])
def test_explicit_corpus_orthographic_alias_preserves_word_identity(expected,spoken):
    matcher = StreamingMatcher(
        ['في',expected,'قال'],known_error_words={'في',expected,spoken,'قال'},
        word_aliases={spoken:expected},
    )
    live = matcher.evaluate(['في',spoken,'قال'],[.95]*3)
    assert all(state.status == WordStatus.MATCHED for state in live)
    final = matcher.finalize(['في',spoken,'قال'],[.95]*3)
    assert all(state.status == WordStatus.MATCHED for state in final)
