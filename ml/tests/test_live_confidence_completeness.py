"""Explicit ASR confidence arrays may not silently imply certainty."""

import pytest

from ml.alignment.streaming_matcher import StreamingMatcher, WordStatus


@pytest.mark.parametrize("confidences,confirmed", [([], []), ([.95], [0]), ([.95, .2], [0])])
def test_missing_live_scores_are_unconfirmed(confidences, confirmed):
    reference = ["بسم", "الله", "الرحمن"]
    matcher = StreamingMatcher(reference)
    states = matcher.evaluate(reference, confidences)
    assert [state.index for state in states if state.status == WordStatus.MATCHED] == confirmed
    assert matcher._cursor == len(confirmed)


def test_legacy_trusted_text_without_confidence_array_retains_behavior():
    reference = ["بسم", "الله", "الرحمن"]
    states = StreamingMatcher(reference).evaluate(reference)
    assert [state.index for state in states if state.status == WordStatus.MATCHED] == [0, 1, 2]
