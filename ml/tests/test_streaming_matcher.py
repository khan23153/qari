"""Unit tests for the real-time streaming word matcher."""

from ml.alignment.streaming_matcher import (
    StreamingMatcher,
    WordStatus,
)

# Al-Fatiha 1:1 (normalized, no diacritics)
BISMILLAH = ["بسم", "الله", "الرحمن", "الرحيم"]


def _statuses(states):
    return {s.index: s.status for s in states}


def test_progressive_reveal_word_by_word():
    """As hypothesis words arrive one at a time, each reference word resolves."""
    m = StreamingMatcher(BISMILLAH)

    s = m.evaluate(["بسم"])
    assert _statuses(s) == {0: WordStatus.MATCHED}

    s = m.evaluate(["بسم", "الله"])
    assert _statuses(s) == {0: WordStatus.MATCHED, 1: WordStatus.MATCHED}

    s = m.evaluate(["بسم", "الله", "الرحمن", "الرحيم"])
    assert _statuses(s) == {
        0: WordStatus.MATCHED,
        1: WordStatus.MATCHED,
        2: WordStatus.MATCHED,
        3: WordStatus.MATCHED,
    }


def test_pending_words_are_not_returned():
    """Words ahead of the recitation stay unresolved (masked)."""
    m = StreamingMatcher(BISMILLAH)
    s = m.evaluate(["بسم", "الله"])
    resolved = {st.index for st in s}
    assert resolved == {0, 1}
    assert 2 not in resolved  # الرحمن still pending / hidden
    assert 3 not in resolved


def test_mispronounced_word_flagged_error():
    """A clearly different word at a position is flagged as an error (red)."""
    m = StreamingMatcher(BISMILLAH)
    s = m.evaluate(["بسم", "الله", "السلام"])  # wrong 3rd word
    st = _statuses(s)
    assert st[0] == WordStatus.MATCHED
    assert st[1] == WordStatus.MATCHED
    assert st[2] == WordStatus.ERROR


def test_skipped_word_detected():
    """Jumping over a word marks it skipped and matches the later word."""
    m = StreamingMatcher(BISMILLAH)
    # User recites 1st, 2nd, then jumps straight to the 4th word.
    s = m.evaluate(["بسم", "الله", "الرحيم"])
    st = _statuses(s)
    assert st[0] == WordStatus.MATCHED
    assert st[1] == WordStatus.MATCHED
    assert st[2] == WordStatus.SKIPPED  # الرحمن skipped
    assert st[3] == WordStatus.MATCHED  # الرحيم matched


def test_inserted_extra_word_ignored():
    """An extra ASR word (repeat/hallucination) does not misalign the rest."""
    m = StreamingMatcher(BISMILLAH)
    s = m.evaluate(["بسم", "بسم", "الله", "الرحمن"])
    st = _statuses(s)
    assert st[0] == WordStatus.MATCHED
    assert st[1] == WordStatus.MATCHED
    assert st[2] == WordStatus.MATCHED


def test_near_match_absorbs_asr_noise():
    """A near-identical long word (one char off) is matched, not flagged red."""
    m = StreamingMatcher(BISMILLAH)
    # الرحمن recognised as الرحمان (extra alef) → similarity 6/7 ≈ 0.86 >= 0.80.
    s = m.evaluate(["بسم", "الله", "الرحمان"])
    st = _statuses(s)
    assert st[2] == WordStatus.MATCHED


def test_finalize_marks_unrecited_as_skipped():
    """At end-of-session, un-recited trailing words are skipped."""
    m = StreamingMatcher(BISMILLAH)
    s = m.finalize(["بسم", "الله"])
    st = _statuses(s)
    assert len(s) == 4
    assert st[2] == WordStatus.SKIPPED
    assert st[3] == WordStatus.SKIPPED


def test_empty_hypothesis():
    m = StreamingMatcher(BISMILLAH)
    assert m.evaluate([]) == []
    fin = m.finalize([])
    assert all(s.status == WordStatus.SKIPPED for s in fin)
