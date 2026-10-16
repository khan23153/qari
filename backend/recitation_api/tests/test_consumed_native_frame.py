"""A past word whose emission span grows must not become another occurrence."""
from app.services.streaming_session import _stitch_timed_hypothesis


def stitch(words, scores, times):
    return _stitch_timed_hypothesis(['لي'],[.65],[(212.62,212.62)],
        words,scores,times,consumed=1,consumed_end=212.62,
        window_start=212.,window_seconds=3.1,confidence_threshold=.55,right_context_seconds=.24)


def test_native_same_word_starting_on_an_earlier_frame_is_not_new_speech():
    words,confs,times=stitch(['لي','اعبد'],[.75,.95],[(.56,.72),(2.08,2.72)])
    assert words==['لي','اعبد']
    assert confs==[.65,.95]
    assert times==[(212.62,212.62),(214.08,214.72)]


def test_real_later_repetition_survives_past_span_growth():
    words,confs,times=stitch(['لي','لي','اعبد'],[.75,.91,.95],[(.56,.72),(.88,1.04),(2.08,2.72)])
    assert words==['لي','لي','اعبد']
    assert confs==[.65,.91,.95]
    assert times[1]==(212.88,213.04)


def test_long_offset_float32_rounding_does_not_duplicate_the_same_word():
    words,_,_=_stitch_timed_hypothesis(['الكافرين'],[.94],[(682.3999996,683.12)],
        ['الكافرين','اولم'],[.94,.98],[(16.6400015,17.52),(18.96,19.44)],
        consumed=1,consumed_end=683.12,window_start=665.76,window_seconds=21.,
        confidence_threshold=.55,right_context_seconds=.24)
    assert words==['الكافرين','اولم']
