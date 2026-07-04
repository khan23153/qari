"""ML pipeline orchestrator — runs the full recitation analysis.

Steps:
1. ASR pass (Whisper-Quran) → hypothesis tokens
2. Word-level alignment (Levenshtein) → omission/insertion/mispronunciation
3. Forced alignment (Wav2Vec2-CTC) → per-word timestamps + confirmation
4. Tajweed checks (Phase 2) → rule-specific pass/fail
5. Scoring + result formatting
"""
import numpy as np
from typing import Optional
import structlog

from ml.inference.asr import QuranASR
from ml.alignment.word_alignment import align_words
from ml.alignment.forced_alignment import ForcedAligner
from ml.tajweed.checks import check_tajweed_rule
from ml.evaluation.scoring import compute_scores

log = structlog.get_logger()


class RecitationPipeline:
    """Orchestrates the full ML recitation analysis pipeline."""

    def __init__(self):
        self.asr = QuranASR()
        self.aligner = ForcedAligner()

    def analyze(
        self,
        audio: np.ndarray,
        expected_words: list[dict],
        tajweed_annotations: list[dict] | None = None,
        sample_rate: int = 16000,
    ) -> dict:
        """Run full analysis on a recitation audio clip.

        Args:
            audio: mono 16kHz audio
            expected_words: list of {"word_position", "text_uthmani", "text_normalized"}
            tajweed_annotations: optional tajweed spans for Phase 2 checks

        Returns:
            Full result dict with word verdicts, scores, timestamps
        """
        # Step 1: ASR
        asr_result = self.asr.transcribe(audio, sample_rate)
        log.info("ASR complete", tokens=len(asr_result["tokens"]))

        # Step 2: Word-level alignment
        expected_tokens = [w["text_normalized"] for w in expected_words]
        alignment = align_words(
            expected_tokens,
            asr_result["tokens"],
            asr_confidence=asr_result["confidence"],
        )
        log.info("Word alignment complete", verdicts=len(alignment))

        # Step 3: Forced alignment for timestamps
        expected_text = " ".join(expected_tokens)
        fa_result = self.aligner.align(audio, expected_text, sample_rate)

        # Step 4: Tajweed checks (Phase 2)
        tajweed_results = None
        if tajweed_annotations:
            tajweed_results = []
            for ann in tajweed_annotations:
                # Extract audio segment for this annotation
                word_ts = fa_result["word_timestamps"]
                if ann["word_position"] - 1 < len(word_ts):
                    ts = word_ts[ann["word_position"] - 1]
                    start_sample = int(ts["start_ms"] / 1000 * sample_rate)
                    end_sample = int(ts["end_ms"] / 1000 * sample_rate)
                    segment = audio[start_sample:end_sample]

                    result = check_tajweed_rule(
                        ann["rule"],
                        segment,
                        sample_rate=sample_rate,
                    )
                    if result:
                        tajweed_results.append(result)

        # Step 5: Format word verdicts
        word_verdicts = []
        for align_entry in alignment:
            verdict = {
                "verdict": align_entry["verdict"],
            }
            if "expected_idx" in align_entry and align_entry["expected_idx"] is not None:
                idx = align_entry["expected_idx"]
                verdict["key"] = f"{expected_words[idx].get('surah', '0')}:{expected_words[idx].get('ayah', '0')}:{expected_words[idx]['word_position']}"
                # Attach timestamps from forced alignment
                if idx < len(fa_result["word_timestamps"]):
                    ts = fa_result["word_timestamps"][idx]
                    verdict["user_clip"] = {
                        "start_ms": ts["start_ms"],
                        "end_ms": ts["end_ms"],
                    }
            word_verdicts.append(verdict)

        # Step 6: Score
        scores = compute_scores(word_verdicts, tajweed_results)

        return {
            **scores,
            "words": word_verdicts,
            "tajweed_results": tajweed_results,
        }
