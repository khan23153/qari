from types import SimpleNamespace

from app.workers.fast_inference_worker import _reference_only_verdicts


def _word(
    *,
    reference,
    hypothesis,
    verdict,
    confidence=0.9,
):
    return SimpleNamespace(
        reference=reference,
        hypothesis=hypothesis,
        verdict=verdict,
        confidence=confidence,
        tajweed_issues=[],
    )


def test_asr_insertion_does_not_increase_quran_word_count():
    rows = [
        _word(reference="الحمد", hypothesis="الحمد", verdict="correct"),
        _word(reference="لله", hypothesis="لله", verdict="correct"),
        _word(reference="رب", hypothesis="رب", verdict="correct"),
        _word(reference=None, hypothesis="فيه", verdict="inserted_extra"),
        _word(reference="العلمين", hypothesis="العلمين", verdict="correct"),
    ]

    verdicts, next_index, correct, confidences = _reference_only_verdicts(
        rows,
        start_index=0,
        reference_audio_url="https://example.test/reference.mp3",
        user_audio_url="https://example.test/user.wav",
    )

    assert len(verdicts) == 4
    assert next_index == 4
    assert correct == 4
    assert len(confidences) == 4
    assert [item["word"] for item in verdicts] == [
        "الحمد",
        "لله",
        "رب",
        "العلمين",
    ]
    assert all(item["actual_text"] != "فيه" for item in verdicts)


def test_low_confidence_is_not_a_confirmed_pronunciation_error():
    rows = [
        _word(
            reference="الرحمن",
            hypothesis="الرحيم",
            verdict="mispronounced",
            confidence=0.2,
        )
    ]

    verdicts, _, correct, _ = _reference_only_verdicts(
        rows,
        start_index=0,
        reference_audio_url=None,
        user_audio_url=None,
    )

    assert correct == 0
    assert verdicts[0]["error_type"] == "recognition_uncertain"
    assert "not a confirmed pronunciation error" in verdicts[0]["error_description"]
