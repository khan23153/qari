"""Correct independent ending words must retain their actual reference positions."""
import json
from pathlib import Path

from app import main
from ml.alignment.streaming_matcher import StreamingMatcher, WordStatus

DATA = json.loads((Path(__file__).parent / 'fixtures/baqarah_full_native_final.json').read_text())


def test_captured_confident_ending_phrase_is_not_consumed_as_earlier_errors():
    delegate = StreamingMatcher(
        DATA['reference'], ayah_boundaries=DATA['ayah_boundaries'],
        known_error_words=DATA['known_error_words'],
        word_aliases=DATA['word_aliases'],
    )
    matcher = main._ConservativeLiveMatcher(DATA['reference'], delegate=delegate)
    matcher.max_live_words = 230
    states = matcher.finalize_independent(DATA['words'], DATA['confidences'])
    ending = [(s.index, s.spoken) for s in states
              if s.index >= 224 and s.status == WordStatus.MATCHED]
    assert ending == [(224, 'ان'), (225, 'الله'), (226, 'علي'), (227, 'كل'), (229, 'قدير')]
    assert not any(s.index == 228 for s in states)  # Native شي .483 is uncertain.


def test_final_recovery_keeps_independent_live_confirmations():
    from ml.alignment.streaming_matcher import WordState
    delegate = StreamingMatcher(DATA['reference'],
        ayah_boundaries=DATA['ayah_boundaries'],
        known_error_words=DATA['known_error_words'], word_aliases=DATA['word_aliases'])
    delegate._resolved_states = [WordState(
        row['index'], DATA['reference'][row['index']], WordStatus(row['status']),
        row['spoken'], row['confidence']) for row in DATA['live_states']]
    matcher = main._ConservativeLiveMatcher(DATA['reference'], delegate=delegate)
    matcher.max_live_words = 230
    states = matcher.finalize_independent(DATA['words'], DATA['confidences'])
    confirmed = {s.index for s in states if s.status == WordStatus.MATCHED}
    prior = {row['index'] for row in DATA['live_states'] if row['status'] == 'matched'}
    assert prior <= confirmed
    assert {224, 225, 226, 227, 229} <= confirmed
    assert 228 not in confirmed
