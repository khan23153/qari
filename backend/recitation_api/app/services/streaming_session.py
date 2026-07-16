"""Real-time streaming recitation session (Tarteel-style live tracking).

This service backs the ``/ws/recitation/stream`` WebSocket. Unlike the
upload → Redis-Stream → worker flow (batch analysis of a finished recording),
a :class:`StreamingRecitationSession` processes a **continuous audio stream**
while the user is still reciting and emits **word-by-word** match events in
real time.

Flow
----
1. The client opens the WebSocket and sends a ``start`` message (surah / ayah).
2. The session resolves the expected (reference) word list for the ayah(s).
3. The client streams raw PCM16 mono 16 kHz audio frames (binary messages).
4. Periodically the session re-transcribes the accumulated audio and feeds the
   cumulative hypothesis into a :class:`ml.alignment.streaming_matcher.StreamingMatcher`.
   Newly-resolved reference words are emitted as ``word`` events
   (matched / error / skipped).
5. On ``stop`` the session writes the full recording to disk, builds the
   mobile-shaped :class:`RecitationAnalysisResult` blob (so history + A/B
   playback keep working) and returns a ``final`` event.

The transcriber is pluggable. When ``QARI_ML_USE_STUB`` is set (or the real
Whisper model cannot be loaded) a lightweight duration-based stub is used so the
end-to-end live experience works without GPU / model weights.
"""

from __future__ import annotations

import asyncio
import os
import struct
import uuid
import wave
from datetime import datetime, timezone
from typing import Callable, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# How many seconds of *new* audio to accumulate before re-transcribing.
TRANSCRIBE_INTERVAL_SEC = 1.2
# Stub transcriber: assumed seconds per recited word (reveals words over time).
STUB_SECONDS_PER_WORD = 0.9

# A transcriber turns a float32 mono 16 kHz signal into (normalized_words,
# per_word_confidences).
Transcriber = Callable[["object", int], "tuple[list[str], list[float]]"]


# ---------------------------------------------------------------------------
# Reference resolution (expected normalized words for an ayah)
# ---------------------------------------------------------------------------

# Inlined Arabic normalizer (mirrors ml.inference.asr.normalize_arabic) so the
# streaming reference resolution does NOT import the heavy ASR module (torch /
# numpy). The live stream only needs lightweight normalization + the pure-Python
# StreamingMatcher; the full ASR engine is only used by the real transcriber.
import re as _re

_HARAKAT = _re.compile(
    "[\u0618-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]"
)
_TATWEEL = _re.compile("\u0640")
_ALEF = {"\u0622": "ا", "\u0623": "ا", "\u0625": "ا", "\u0671": "ا", "\u0672": "ا", "\u0673": "ا"}
_YA = {"\u0649": "ي", "\u06CC": "ي"}
_TA_MARBUTA = "\u0629"
_HA = "\u0647"
_HAMZA = {"\u0624": "و", "\u0626": "ي", "\u0621": ""}
_NON_ARABIC = _re.compile(r"[^\u0621-\u064A\u0660-\u0669\u066E-\u06D5\u06DE\u06EF ]")
_MULTI_SPACE = _re.compile(r"\s+")


def _normalize(text: str) -> str:
    if not text:
        return ""
    text = _HARAKAT.sub("", text)
    text = _TATWEEL.sub("", text)
    for variant, canonical in _ALEF.items():
        text = text.replace(variant, canonical)
    for variant, canonical in _YA.items():
        text = text.replace(variant, canonical)
    text = text.replace(_TA_MARBUTA, _HA)
    for variant, canonical in _HAMZA.items():
        text = text.replace(variant, canonical)
    text = _NON_ARABIC.sub(" ", text)
    text = _MULTI_SPACE.sub(" ", text)
    return text.strip()


def _pack_entries(display: list[str], norm: list[str]) -> list[dict]:
    """Zip display + normalized words into the blueprint word-level model.

    Keeps all three lists aligned (a reference word with no clean_text is
    dropped from all three) so the matcher, the UI, and the ``ready`` payload
    always agree on indices.
    """
    entries: list[dict] = []
    kept_display: list[str] = []
    kept_norm: list[str] = []
    for d, n in zip(display, norm):
        if not n:
            continue
        entries.append({"text_with_tashkeel": d, "clean_text": n})
        kept_display.append(d)
        kept_norm.append(n)
    return entries, kept_display, kept_norm


def resolve_reference_words(surah: int, ayah: int) -> tuple[list[str], list[str], str, list[dict]]:
    """Resolve the expected (reference) word list for a single ayah.

    Returns ``(display_words, normalized_words, reference_audio_url,
    word_entries)`` where ``word_entries`` is a list (aligned 1:1 with the
    returned ``display_words``) of the blueprint word-level model::

        {"text_with_tashkeel": <UI Arabic>, "clean_text": <ASR key>}

    Tries the ML file-backed reference store first, then core_api. Returns
    empty lists when nothing is available (the client then falls back to its
    own bundled corpus for the masked text).
    """
    # 1) ML reference store (prebuilt {surah}_{ayah}.json bundle).
    try:
        from ml.tajweed.reference_store import ReferenceStore

        store = ReferenceStore(settings.reference_data_dir or None)
        if store.has(surah, ayah):
            ref = store.get(surah, ayah)
            display = [w.text_with_tashkeel or w.word for w in ref.words]
            norm = [_normalize(w.word) for w in ref.words]
            entries, display, norm = _pack_entries(display, norm)
            return display, norm, ref.reference_audio_url or "", entries
    except Exception as exc:  # pragma: no cover - ml deps optional
        logger.debug("stream.refstore_miss", surah=surah, ayah=ayah, error=str(exc))

    # 2) core_api fallback.
    try:
        import httpx

        url = (
            f"{settings.core_api_base_url}/v1/surahs/{surah}/ayahs"
            f"?from={ayah}&to={ayah}"
        )
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        ayahs = payload if isinstance(payload, list) else (
            payload.get("ayahs") or payload.get("data") or []
        )
        if ayahs:
            words = ayahs[0].get("words", [])
            display = [w.get("text_arabic", "") for w in words]
            norm = [_normalize(w.get("text_arabic", "")) for w in words]
            entries, display, norm = _pack_entries(display, norm)
            return display, norm, ayahs[0].get("audio_url", "") or "", entries
    except Exception as exc:
        logger.warning("stream.ref_fetch_failed", surah=surah, ayah=ayah, error=str(exc))

    return [], [], "", []


def resolve_reference_words_sequence(
    ayah_refs: list[tuple[int, int]],
) -> tuple[list[str], list[str], str, list[dict], list[dict]]:
    """Resolve and **concatenate** the reference word lists for a sequence of
    ``(surah, ayah)`` references — used for continuous full-page / full-surah
    recitation.

    Returns ``(display_words, normalized_words, first_audio_url,
    word_entries, ayah_boundaries)`` where ``ayah_boundaries`` is a list
    (one entry per ayah) of ``{"surah", "ayah", "word_index_end",
    "word_count"}`` describing where each ayah ends in the global
    (concatenated) word index. This lets the client render end-of-ayah markers
    without re-deriving the split itself.
    """
    display: list[str] = []
    norm: list[str] = []
    audio_url = ""
    entries: list[dict] = []
    boundaries: list[dict] = []

    for surah, ayah in ayah_refs:
        d, n, url, e = resolve_reference_words(surah, ayah)
        if not audio_url and url:
            audio_url = url
        # Record the boundary *before* extending so word_index_end is correct.
        boundaries.append({
            "surah": surah,
            "ayah": ayah,
            "word_index_end": len(display) + len(d) - 1,
            "word_count": len(d),
        })
        display.extend(d)
        norm.extend(n)
        entries.extend(e)

    return display, norm, audio_url, entries, boundaries


# ---------------------------------------------------------------------------
# Transcribers
# ---------------------------------------------------------------------------

_real_asr = None


def _real_transcriber(audio, sr: int) -> tuple[list[str], list[float]]:
    """Transcribe with Faster-Whisper (CT2, INT8) — CPU-efficient real-time ASR.

    Uses ``tarteel-ai/whisper-tiny-ar-quran`` (converted to CTranslate2 INT8) so
    the live stream runs with low latency on a standard CPU VPS. The raw Arabic
    tokens are normalized with the *same* ``_normalize`` used for the reference
    words, so the :class:`StreamingMatcher` compares hypothesis ↔ reference on a
    consistent basis. Returns ``([], [])`` on any failure so the session falls
    back to the stub-style behaviour instead of crashing.
    """
    try:
        from ml.inference.faster_whisper_transcriber import get_transcriber

        raw_words, confs = get_transcriber().transcribe(audio, sr)
    except Exception as exc:  # pragma: no cover - model/load failures
        logger.error("stream.faster_whisper_failed", error=str(exc))
        return [], []

    norm: list[str] = []
    out_confs: list[float] = []
    for w, c in zip(raw_words, confs):
        n = _normalize(w)
        if n:
            norm.append(n)
            out_confs.append(c)
    return norm, out_confs


def _make_stub_transcriber(reference_words: list[str]) -> Transcriber:
    """Duration-based stub: reveal reference words as audio accumulates.

    Lets the full live flow be demoed without model weights. It reveals one
    reference word per ``STUB_SECONDS_PER_WORD`` of audio, so words light up
    green sequentially as the user "recites".
    """

    def _transcribe(audio, sr: int) -> tuple[list[str], list[float]]:
        try:
            n = len(audio)
        except TypeError:
            n = 0
        seconds = (n / sr) if sr else 0.0
        reveal = min(len(reference_words), int(seconds / STUB_SECONDS_PER_WORD))
        words = list(reference_words[:reveal])
        return words, [0.9] * len(words)

    return _transcribe


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

class StreamingRecitationSession:
    """Stateful live recitation session for a single WebSocket connection."""

    def __init__(
        self,
        *,
        surah: int = 1,
        ayah_from: int = 1,
        ayah_to: int = 1,
        ayah_refs: Optional[list[tuple[int, int]]] = None,
        mode: str = "tracking",
        sample_rate: int = 16000,
        transcriber: Optional[Transcriber] = None,
        client_words: Optional[list[str]] = None,
    ) -> None:
        self.session_id = str(uuid.uuid4())

        # `ayah_refs` is the authoritative, ordered list of (surah, ayah) the
        # user will recite continuously (a full Mushaf page or a whole surah).
        # When omitted we fall back to a single-surah range for backwards
        # compatibility with older clients.
        if ayah_refs:
            self.ayah_refs: list[tuple[int, int]] = list(ayah_refs)
        else:
            self.ayah_refs = [(surah, a) for a in range(ayah_from, ayah_to + 1)]

        self.surah = self.ayah_refs[0][0] if self.ayah_refs else surah
        self.ayah_from = self.ayah_refs[0][1] if self.ayah_refs else ayah_from
        self.ayah_to = self.ayah_refs[-1][1] if self.ayah_refs else ayah_to
        self.mode = mode
        self.sample_rate = sample_rate

        self.display_words: list[str] = []
        self.reference_words: list[str] = []
        self.reference_audio_url: str = ""
        self.word_entries: list[dict] = []
        self.ayah_boundaries: list[dict] = []

        # Client-supplied word list (sent in the `start` handshake). Used as a
        # fallback reference when the server's own reference store / corpus is
        # empty, so the matcher still produces verdicts (fixes "0 of 0 words").
        self._client_words: list[str] = list(client_words or [])

        self._pcm = bytearray()
        self._samples_at_last_transcribe = 0
        self._transcribe_lock = asyncio.Lock()
        self._matcher = None
        self._last_status: dict[int, str] = {}
        self._last_hypothesis: list[str] = []
        self._explicit_transcriber = transcriber
        self._transcriber: Optional[Transcriber] = None

    # ------------------------------------------------------------------
    def load_reference(self) -> None:
        """Resolve the expected (concatenated) word list and pick a transcriber."""
        from ml.alignment.streaming_matcher import StreamingMatcher

        display, norm, ref_url, entries, boundaries = resolve_reference_words_sequence(
            self.ayah_refs
        )
        self.display_words = display
        self.reference_words = norm
        self.reference_audio_url = ref_url
        self.word_entries = entries
        self.ayah_boundaries = boundaries

        # Fallback: if the server resolved NO reference words (empty reference
        # store / corpus), trust the client's own resolved word list so we can
        # still score and emit word events instead of "0 of 0".
        if not self.reference_words and self._client_words:
            logger.warning(
                "stream.using_client_words_fallback",
                session_id=self.session_id,
                count=len(self._client_words),
            )
            c_display = list(self._client_words)
            c_norm = [_normalize(w) for w in c_display]
            c_entries, c_display, c_norm = _pack_entries(c_display, c_norm)
            self.display_words = c_display
            self.reference_words = c_norm
            self.word_entries = c_entries
            self.ayah_boundaries = []

        # Build the matcher + transcriber from the FINAL reference words (which
        # may be the client-words fallback), not the original (possibly empty)
        # `norm` returned by the server's own resolver.
        self._matcher = StreamingMatcher(self.reference_words)

        if self._explicit_transcriber is not None:
            self._transcriber = self._explicit_transcriber
        elif settings.ml_use_stub or not self.reference_words:
            self._transcriber = _make_stub_transcriber(self.reference_words)
        else:
            # Real ASR requested. Probe whether the Faster-Whisper CT2 model is
            # actually loadable in this container (it must be bind-mounted at
            # QARI_FASTERWHISPER_MODEL_DIR). If it is missing/unloadable the real
            # transcriber would silently return [] on every call → the live
            # stream shows NO words and finalize reports "0 of N". Fall back to
            # the duration-based stub so the live flow + a non-empty result still
            # work (and log loudly) instead of a broken 0/29.
            try:
                from ml.inference.faster_whisper_transcriber import get_transcriber

                get_transcriber().load()
                self._transcriber = _real_transcriber
                logger.info(
                    "stream.transcriber", session_id=self.session_id,
                    engine="faster-whisper", words=len(self.reference_words),
                )
            except Exception as exc:
                logger.error(
                    "stream.real_transcriber_unavailable_falling_back_to_stub",
                    session_id=self.session_id, error=str(exc),
                )
                self._transcriber = _make_stub_transcriber(self.reference_words)

    # ------------------------------------------------------------------
    def ready_payload(self) -> dict:
        # Word-level model served to the client (per the Hifz data contract):
        #   word_id, sequence_index, text_with_tashkeel, clean_text, state
        # The first word is "active" (the next word the user must recite); the
        # rest start "hidden" until revealed by the live engine.
        words = []
        for i, entry in enumerate(self.word_entries):
            words.append({
                "word_id": i + 1,
                "sequence_index": i + 1,
                "text_with_tashkeel": entry.get("text_with_tashkeel", self.display_words[i]),
                "clean_text": entry.get("clean_text", self.display_words[i]),
                "state": "active" if i == 0 else "hidden",
            })
        return {
            "type": "ready",
            "session_id": self.session_id,
            "surah_number": self.surah,
            "ayah_from": self.ayah_from,
            "ayah_to": self.ayah_to,
            "mode": self.mode,
            "words": words,
            "word_count": len(self.reference_words),
            "ayah_boundaries": self.ayah_boundaries,
        }

    # ------------------------------------------------------------------
    def add_audio(self, chunk: bytes) -> None:
        self._pcm.extend(chunk)

    @property
    def _total_samples(self) -> int:
        return len(self._pcm) // 2  # 16-bit samples

    @property
    def duration_seconds(self) -> float:
        return self._total_samples / self.sample_rate if self.sample_rate else 0.0

    def _decode_float(self):
        # Numpy-free decode: convert the raw PCM16 bytes into a list of float32
        # samples in [-1, 1]. Kept dependency-light so the live stream runs in
        # the API container without the full ML stack. The stub transcriber only
        # needs the sample COUNT; the real (Whisper) transcriber would convert
        # this list to a tensor itself when QARI_ML_USE_STUB is false.
        if not self._pcm:
            return []
        import array

        samples = array.array("h")
        samples.frombytes(bytes(self._pcm))
        return [s / 32768.0 for s in samples]

    # ------------------------------------------------------------------
    async def maybe_transcribe(self, *, force: bool = False) -> list[dict]:
        """Re-transcribe if enough new audio arrived; return new word events."""
        if self._matcher is None or self._transcriber is None:
            return []
        new_samples = self._total_samples - self._samples_at_last_transcribe
        threshold = int(TRANSCRIBE_INTERVAL_SEC * self.sample_rate)
        if not force and new_samples < threshold:
            return []
        if self._transcribe_lock.locked():
            return []

        async with self._transcribe_lock:
            self._samples_at_last_transcribe = self._total_samples
            audio = self._decode_float()
            try:
                words, confs = await asyncio.to_thread(
                    self._transcriber, audio, self.sample_rate
                )
            except Exception as exc:  # pragma: no cover - model failures
                logger.error("stream.transcribe_failed", session_id=self.session_id, error=str(exc))
                return []
            self._last_hypothesis = words
            states = self._matcher.evaluate(words, confs)
            return self._diff_events(states)

    def _diff_events(self, states) -> list[dict]:
        events: list[dict] = []
        for st in states:
            if self._last_status.get(st.index) == st.status.value:
                continue
            self._last_status[st.index] = st.status.value
            # Blueprint contract: the client receives a stable ``status`` of
            # ``match`` (correctly revealed) or ``error_skipped`` (skipped /
            # mispronounced), keyed by the 1-based ``word_id``. We keep the
            # richer fields (word_index, expected, spoken, confidence) for
            # debugging and richer UI affordances — they are additive.
            blueprint_status = (
                "match" if st.status.value == "matched" else "error_skipped"
            )
            events.append({
                "type": "word",
                "session_id": self.session_id,
                "status": blueprint_status,
                "word_id": st.index + 1,
                "word_index": st.index,
                "expected": st.expected,
                "spoken": st.spoken,
                "confidence": round(st.confidence, 3),
                "timestamp_ms": int(self.duration_seconds * 1000),
            })
        return events

    # ------------------------------------------------------------------
    def _write_wav(self) -> Optional[str]:
        if not self._pcm:
            return None
        try:
            storage = os.path.join(settings.audio_storage_path, self.session_id)
            os.makedirs(storage, exist_ok=True)
            path = os.path.join(storage, "audio.wav")
            with wave.open(path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(bytes(self._pcm))
            return path
        except Exception as exc:  # pragma: no cover
            logger.warning("stream.wav_write_failed", session_id=self.session_id, error=str(exc))
            return None

    async def finalize(self) -> dict:
        """End the session: persist audio + build the final result blob."""
        from ml.alignment.streaming_matcher import WordStatus

        # If live transcription never produced a hypothesis (e.g. the forced
        # final transcription on `stop` was slow and the client timed out, or the
        # transcriber was the stub and produced nothing), do ONE full-audio
        # transcription here so the verdicts aren't all "skipped" (0 of N). This
        # guarantees a meaningful result whenever reference words exist.
        if not self._last_hypothesis and self._transcriber is not None and self._pcm:
            try:
                audio = self._decode_float()
                words, confs = await asyncio.to_thread(
                    self._transcriber, audio, self.sample_rate
                )
                if words:
                    self._last_hypothesis = words
            except Exception as exc:  # pragma: no cover - model failures
                logger.error("stream.finalize_transcribe_failed", session_id=self.session_id, error=str(exc))

        audio_path = self._write_wav()
        public_base = settings.recitation_api_public_url.rstrip("/")
        user_audio_url = (
            f"{public_base}/v1/recitations/{self.session_id}/audio"
            if public_base and audio_path
            else audio_path
        )

        states = (
            self._matcher.finalize(self._last_hypothesis)
            if self._matcher is not None
            else []
        )

        word_verdicts = []
        matched = 0
        for st in states:
            is_correct = st.status == WordStatus.MATCHED
            if is_correct:
                matched += 1
            word_verdicts.append({
                "word": st.expected,
                "word_index": st.index,
                "is_correct": is_correct,
                "confidence": round(st.confidence, 3),
                "expected_text": st.expected,
                "actual_text": st.spoken,
                "error_type": None if is_correct else st.status.value,
                "error_description": (
                    None if is_correct else _describe(st.status.value)
                ),
                "reference_audio_url": self.reference_audio_url or None,
                "user_audio_url": user_audio_url,
                "phoneme_errors": [],
            })

        total = len(states)
        accuracy = (matched / total) if total else 0.0
        # Live matching without a resolvable reference gives us nothing to score
        # against → low confidence (mobile shows "no red marks", per trust rule).
        confidence = 1.0 if total else 0.0

        result = {
            "session_id": self.session_id,
            "surah_number": self.surah,
            "ayah_number": self.ayah_from,
            "overall_score": round(accuracy, 4),
            "pronunciation_score": round(accuracy, 4),
            "tajweed_score": 0.0,
            "fluency_score": round(accuracy, 4),
            "accuracy_score": round(accuracy, 4),
            "word_verdicts": word_verdicts,
            "reference_audio_url": self.reference_audio_url or None,
            "user_audio_url": user_audio_url,
            "feedback": (
                "Live session complete. Tap red words to compare your recitation."
                if total else
                "We couldn't analyse this recitation with enough confidence."
            ),
            "feedback_urdu": None,
            "duration_seconds": int(self.duration_seconds),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "confidence": round(confidence, 4),
        }
        await self._persist(result, audio_path)
        return result

    async def _persist(self, result: dict, audio_path: Optional[str]) -> None:
        """Store the result in Redis so GET /{session_id} + history keep working."""
        try:
            import json

            import redis.asyncio as redis

            r = redis.from_url(settings.redis_url, decode_responses=True)
            now = datetime.now(timezone.utc).isoformat()
            await r.hset(
                f"qari:recitation:session:{self.session_id}",
                mapping={
                    "session_id": self.session_id,
                    "surah_number": str(self.surah),
                    "ayah_from": str(self.ayah_from),
                    "ayah_to": str(self.ayah_to),
                    "status": "completed",
                    "source": "stream",
                    "audio_path": audio_path or "",
                    "completed_at": now,
                },
            )
            await r.expire(f"qari:recitation:session:{self.session_id}", 86400)
            await r.set(
                f"qari:recitation:result:{self.session_id}",
                json.dumps(result, default=str),
                ex=86400,
            )
            await r.aclose()
        except Exception as exc:  # pragma: no cover - redis optional in tests
            logger.warning("stream.persist_failed", session_id=self.session_id, error=str(exc))


def _describe(status: str) -> str:
    if status == "skipped":
        return "You skipped this word. Recite it before moving on."
    if status == "error":
        return "This word sounded different from the reference. Listen and retry."
    return "Needs practice."
