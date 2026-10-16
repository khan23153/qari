"""An already read phrase cannot establish a jump across unheard words."""
from ml.alignment.streaming_matcher import StreamingMatcher, WordStatus


def matched_indices(states):
    return {s.index for s in states if s.status == WordStatus.MATCHED}


def prime(matcher, words):
    matcher.evaluate(words[:2], [.95] * 2)
    matcher.evaluate(words, [.95] * len(words))
    assert matcher._cursor == len(words)


def test_repeated_completed_pair_cannot_skip_an_unheard_reference_word():
    matcher = StreamingMatcher(['start', 'x', 'a', 'b', 'gap', 'a', 'b', 'next'], use_phonetic=False)
    prefix = ['start', 'x', 'a', 'b']
    prime(matcher, prefix)
    states = matcher.evaluate(prefix + ['a', 'b'], [.95] * 6)
    assert matched_indices(states) == {0, 1, 2, 3}
    assert matcher._cursor == 4
    assert matcher._hyp_cursor == 4


def test_distinct_following_context_can_identify_the_new_occurrence():
    matcher = StreamingMatcher(['start', 'x', 'a', 'b', 'gap', 'a', 'b', 'next'], use_phonetic=False)
    prefix = ['start', 'x', 'a', 'b']
    prime(matcher, prefix)
    matcher.evaluate(prefix + ['a', 'b'], [.95] * 6)
    matcher.evaluate(prefix + ['a', 'b', 'next'], [.95] * 7)
    states = matcher.evaluate(prefix + ['a', 'b', 'next'], [.95] * 7)
    assert matched_indices(states) == {0, 1, 2, 3, 5, 6, 7}


def test_expected_repeated_phrase_after_reading_intervening_text_still_matches():
    words = ['start', 'x', 'a', 'b', 'gap', 'a', 'b', 'next']
    matcher = StreamingMatcher(words, use_phonetic=False)
    prime(matcher, words[:4])
    matcher.evaluate(words[:5], [.95] * 5)
    assert matched_indices(matcher.evaluate(words, [.95] * len(words))) == set(range(8))


def test_a_previously_unheard_pair_can_establish_the_later_occurrence():
    matcher = StreamingMatcher(['start', 'x', 'a', 'b', 'gap', 'a', 'b', 'next'], use_phonetic=False)
    prefix = ['start', 'x', 'a', 'b']
    matcher.evaluate(prefix[:2], [.95] * 2)
    matcher.evaluate(prefix, [.95, .95, .2, .95])
    states = matcher.evaluate(prefix + ['a', 'b'], [.95] * 6)
    assert {5, 6} <= matched_indices(states)


def test_actual_fatihah_alias_pair_cannot_native_reanchor_to_an_unread_ayah():
    reference = ['بسم', 'الله', 'الرحمان', 'الرحيم', 'الحمد', 'لله', 'رب', 'العالمين',
                 'الرحمان', 'الرحيم', 'مالك', 'يوم', 'الدين']
    boundaries = [{'word_index_end': 3, 'word_count': 4}, {'word_index_end': 7, 'word_count': 4},
                  {'word_index_end': 9, 'word_count': 2}, {'word_index_end': 12, 'word_count': 3}]
    matcher = StreamingMatcher(reference, ayah_boundaries=boundaries,
                               word_aliases={'الرحمن': 'الرحمان'}, known_error_words=set(reference) | {'الرحمن'}, use_phonetic=False)
    words = ['بسم', 'الله', 'الرحمن', 'الرحيم']
    prime(matcher, words)
    matcher._stall_passes = 2
    assert not matcher.recover_native_anchor(8, 4, words + ['الرحمن', 'الرحيم'], [.95] * 6)
    assert matcher._cursor == 4
    assert matched_indices(matcher._resolved_states) == {0, 1, 2, 3}


def test_an_unmatched_inserted_token_does_not_identify_a_new_reference_occurrence():
    matcher = StreamingMatcher(['start', 'x', 'a', 'b', 'gap', 'a', 'b', 'next'], use_phonetic=False)
    prefix = ['start', 'x', 'a', 'b']
    prime(matcher, prefix)
    states = matcher.evaluate(prefix + ['a', 'noise', 'b'], [.95] * 7)
    assert matched_indices(states) == {0, 1, 2, 3}
    assert matcher._cursor == 4


def test_an_accepted_article_variant_does_not_bypass_completed_phrase_identity():
    reference = ['start', 'x', 'الرحمان', 'الرحيم', 'gap', 'الرحمان', 'الرحيم', 'next']
    matcher = StreamingMatcher(reference, use_phonetic=False)
    prime(matcher, reference[:4])
    states = matcher.evaluate(reference[:4] + ['رحمان', 'رحيم'], [.95] * 6)
    assert matched_indices(states) == {0, 1, 2, 3}
    assert matcher._cursor == 4
