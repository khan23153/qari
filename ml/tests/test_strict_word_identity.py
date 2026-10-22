"""Strict confirmation keeps spelling identities, not fuzzy consonant guesses."""
import pytest
from ml.alignment.streaming_matcher import StreamingMatcher, WordStatus


@pytest.mark.parametrize('expected,heard',[
    ('الرحمان','الرحمن'),('صراط','صرط'),
    ('ابراهيم','ابرهم'),('نحيي','نحي'),
])
def test_verified_spelling_aliases_remain_confirmed(expected,heard):
    m=StreamingMatcher([expected],strict_word_identity=True,
                       word_aliases={heard:expected},known_error_words={expected,heard})
    states=m.evaluate([heard],[.91])
    assert [(s.index,s.status,s.confidence)for s in states]==[(0,WordStatus.MATCHED,.91)]


def test_strict_unknown_gap_does_not_become_a_spoken_error_or_halt_following_words():
    ref=['بسم','الكتاب','الرحيم']
    m=StreamingMatcher(ref,known_error_words=set(ref),strict_word_identity=True)
    states=m.finalize(['بسم','الختام','الرحيم'],[.95]*3)
    assert states[0].status==WordStatus.MATCHED
    assert states[1].status==WordStatus.SKIPPED and states[1].confidence==0
    assert states[2].status==WordStatus.MATCHED


def test_strict_known_substitution_stays_an_error_with_later_progress():
    ref=['انعمت','عليهم','غير']
    m=StreamingMatcher(ref,known_error_words=set(ref)|{'عليكم'},strict_word_identity=True)
    states=m.finalize(['انعمت','عليكم','غير'],[.95]*3)
    assert states[1].status==WordStatus.ERROR
    assert states[1].spoken=='عليكم'
    assert states[2].status==WordStatus.MATCHED


@pytest.mark.parametrize('expected,heard', [('الحمد','حمد'),('السمد','الصمد'),('عبدتم','اعبدتم')])
def test_unverified_article_consonant_or_added_alef_cannot_confirm_a_word(expected,heard):
    m=StreamingMatcher([expected],known_error_words={expected},strict_word_identity=True)
    assert not m._is_match(heard,expected)


def test_garbled_near_words_do_not_displace_the_exact_final_phrase():
    import json
    from pathlib import Path
    case=json.loads((Path(__file__).parent/'fixtures/strict_baqarah_final_alignment.json').read_text())
    matcher=StreamingMatcher(case['reference'],strict_word_identity=True,
                             known_error_words=set(case['reference']))
    states=matcher.finalize(case['hypothesis'],case['confidences'])
    matches={s.index for s in states if s.status==WordStatus.MATCHED}
    assert {224,225,226,227,229} <= matches
    assert all(matcher._is_match(s.spoken,s.expected) for s in states if s.status==WordStatus.MATCHED)


def test_approximate_placement_cannot_start_or_complete_a_page():
    reference=['الكافرون','الكتاب','المغضوب','اهدنا','انعمت','فليعبدوا','الصمد']
    heard=['القافلون','الختام','المغدوم','اهدينا','انعمك','فليغدوا','السمد']
    matcher=StreamingMatcher(reference,strict_word_identity=True,
                             known_error_words=set(reference))
    for _ in range(5):
        assert not matcher.evaluate(heard,[.95]*len(heard))
        assert matcher._cursor==0
    assert not any(s.status==WordStatus.MATCHED for s in matcher.finalize(heard,[.95]*len(heard)))


def test_approximate_tail_cannot_consume_past_the_last_strict_native_slot():
    matcher=StreamingMatcher(['بسم','الله','الكتاب'],strict_word_identity=True,
                             known_error_words={'بسم','الله','الكتاب'})
    states=matcher.evaluate(['بسم','الله','الختام'],[.95]*3)
    assert [(s.index,s.status) for s in states]==[(0,WordStatus.MATCHED),(1,WordStatus.MATCHED)]
    assert matcher._cursor==2
    assert matcher._hyp_cursor==2
    assert matcher._live_hyp_indices=={0:0,1:1}


def test_confirmed_repeated_phrase_does_not_shift_following_final_words():
    reference=['الحمد','لله','رب','العالمين','الرحمن','الرحيم','مالك','يوم','الدين']
    hypothesis=reference[:4]+reference
    matcher=StreamingMatcher(reference,strict_word_identity=True,known_error_words=set(reference))
    states=matcher.finalize(hypothesis,[.95]*len(hypothesis))
    assert [(s.index,s.status) for s in states]==[(i,WordStatus.MATCHED) for i in range(len(reference))]
    assert all(s.spoken==s.expected for s in states)


def test_later_exact_rereading_cannot_replace_the_earlier_native_occurrence():
    matcher=StreamingMatcher(['بسم','الكتاب','الرحيم'],strict_word_identity=True,
                             known_error_words={'بسم','الكتاب','الرحيم'})
    states=matcher.evaluate(['بسم','الختام','الرحيم','الكتاب','الرحيم'],[.95]*5)
    assert [(s.index,s.status) for s in states]==[(0,WordStatus.MATCHED),(1,WordStatus.SKIPPED),(2,WordStatus.MATCHED)]
    assert matcher._live_hyp_indices=={0:0,2:2}
    assert matcher._hyp_cursor==3


@pytest.mark.parametrize('violation',[
    'fuzzy_repeat','prior_error','prior_skipped','weak_repeat','nan_repeat',
    'infinite_repeat','weak_context','nan_context','infinite_context',
    'overconfident_context','short_context','identical_context',
])
def test_rereading_insertion_requires_exact_source_and_both_strong_distinct_anchors(violation):
    reference=['الحمد','لله','رب','العالمين','الرحمن','الرحيم','مالك']
    matcher=StreamingMatcher(reference,strict_word_identity=True,known_error_words=set(reference))
    matcher.evaluate(reference[:4],[.95]*4,full=True)
    words=reference.copy();scores=[.95]*len(words)
    if violation=='fuzzy_repeat': words[0]='الهمد'
    if violation=='prior_error': matcher._resolved_states[0].status=WordStatus.ERROR
    if violation=='prior_skipped': matcher._resolved_states[0].status=WordStatus.SKIPPED
    if violation=='weak_repeat': scores[0]=.2
    if violation=='nan_repeat': scores[0]=float('nan')
    if violation=='infinite_repeat': scores[0]=float('inf')
    if violation=='weak_context': scores[4]=.2
    if violation=='nan_context': scores[4]=float('nan')
    if violation=='infinite_context': scores[4]=float('inf')
    if violation=='overconfident_context': scores[5]=1.1
    if violation=='short_context': words=words[:5]
    if violation=='identical_context':
        matcher.reference[5]=matcher.reference[4];words[5]=words[4]
    assert matcher._completed_repetition_end(4,0,words,scores) is None
