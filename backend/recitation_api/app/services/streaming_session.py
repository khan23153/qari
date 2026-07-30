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

The transcriber is pluggable. A lightweight duration-based stub is available
only when ``QARI_ML_USE_STUB`` is explicitly set (for tests and demos). A
missing real model must fail the session rather than awarding words merely as
time passes.
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

# --- Sliding-window transcription (fixes unbounded live lag) ----------------
# The OLD live loop re-transcribed the ENTIRE growing audio buffer on every
# pass, so per-pass cost grew with recitation length. On a CPU VPS each Whisper
# pass already takes ~2.5-4s (base) which is slower than the 1.2s cadence, so the
# reveal fell further and further behind real time (worse with the bigger model).
#
# Instead we transcribe only a bounded WINDOW of the most recent audio each pass
# and STITCH the new words onto a cumulative `_hypothesis` list (the
# StreamingMatcher requires a cumulative hypothesis — it resumes at `_hyp_cursor`
# and never re-scans resolved words). Per-pass cost is now ~constant (bounded by
# the window length), so the reveal keeps up regardless of recitation length.
#
# The window must comfortably exceed the ~1.2s new-audio interval so a word that
# straddles the boundary is re-read in the next window's OVERLAP and stitched
# (deduplicated) rather than lost. 6s is the sweet spot on the CPU VPS: large
# enough for reliable context/overlap, small enough that each Whisper pass is
# ~2.2s (tiny) so the live reveal keeps up with continuous speech.
TRANSCRIBE_WINDOW_SEC = 6.0
# Max words of overlap to search when stitching a new window onto the cumulative
# hypothesis (drops words the previous window already contributed).
STITCH_MAX_OVERLAP_WORDS = 12

# --- Silence gating (fixes "ayah auto-completes while the user is silent") -----
# When the user is quiet, the mic still streams low-level room noise and Whisper
# frequently HALLUCINATES Arabic-looking tokens on near-silent audio. Those
# phantom words flowed into the matcher and "completed" the ayah automatically
# even though the user said nothing. We measure the RMS energy of each
# transcribed window and, when it is below this floor, treat the segment as
# silence: skip transcription entirely and emit NO word events (so nothing
# resolves until the user actually recites). 16-bit PCM normalized to [-1, 1];
# a calm room is typically ~0.002–0.01, speech is >0.02. Set conservatively low
# so only near-total silence (the user not reciting at all) is gated — quiet
# recitation must still pass through to ASR.
SILENCE_RMS_THRESHOLD = 0.006

# A transcriber turns a float32 mono 16 kHz signal into (normalized_words,
# per_word_confidences).
Transcriber = Callable[["object", int], "tuple[list[str], list[float]]"]


class LiveTranscriberUnavailable(RuntimeError):
    """Raised when production live ASR cannot be loaded safely."""


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


def _words_similar(a: str, b: str, threshold: float = 0.80) -> bool:
    """Loose word match used when stitching overlapping ASR windows.

    The ASR re-transcribes the same audio every pass, and the model rarely emits
    byte-identical tokens across passes (segmentation / diacritic-stripping noise
    differ). An *exact* equality check therefore almost never finds the overlap,
    so every window got appended again and the cumulative hypothesis grew without
    bound — which made the matcher blow through the entire reference ayah long
    before the user had spoken those words. Comparing on the normalized form with
    a similarity floor recovers the overlap.
    """
    na, nb = _normalize(a), _normalize(b)
    # When normalization strips everything (e.g. non-Arabic / Latin test tokens,
    # numbers), fall back to a raw comparison so overlap detection still works.
    if not na or not nb:
        return a == b
    if na == nb:
        return True
    from ml.alignment.streaming_matcher import char_similarity

    return char_similarity(na, nb) >= threshold


def stitch_hypothesis(
    prefix: list[str],
    prefix_confs: list[float],
    window_words: list[str],
    window_confs: list[float],
    *,
    max_overlap: int = STITCH_MAX_OVERLAP_WORDS,
) -> tuple[list[str], list[float]]:
    """Append a re-transcribed audio WINDOW onto the cumulative hypothesis.

    Consecutive windows overlap in time, so ``window_words`` re-contains the tail
    of what ``prefix`` already holds. We find the largest ``k`` such that the last
    ``k`` words of ``prefix`` are *similar* to the first ``k`` words of
    ``window_words`` (fuzzy, not exact — see :func:`_words_similar`) and only
    append the remainder — so the same spoken word is never counted twice and the
    hypothesis length tracks the user's actual progress instead of exploding.

    Falls back to appending the whole window when no overlap is found (e.g. the
    user recited fast enough that the window is entirely new). Pure function (no
    timestamps needed) so it is trivially unit-testable.
    """
    if not window_words:
        return list(prefix), list(prefix_confs)
    if not prefix:
        return list(window_words), list(window_confs)

    max_k = min(max_overlap, len(prefix), len(window_words))
    best_k = 0
    for k in range(max_k, 0, -1):
        if all(
            _words_similar(prefix[-(k - m)], window_words[m])
            for m in range(k)
        ):
            best_k = k
            break
    merged = list(prefix) + list(window_words[best_k:])
    merged_confs = list(prefix_confs) + list(window_confs[best_k:])
    return merged, merged_confs


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
        self._transcribe_stop = False
        self._matcher = None
        self._last_status: dict[int, str] = {}
        # Cumulative hypothesis (stitched from per-window transcriptions) + its
        # per-word confidences. `_last_hypothesis` is kept as an alias to the
        # cumulative words so `finalize()` and existing callers keep working.
        self._hypothesis: list[str] = []
        self._hypothesis_confs: list[float] = []
        self._last_hypothesis: list[str] = []
        self._explicit_transcriber = transcriber
        self._transcriber: Optional[Transcriber] = None
        # Whether the active transcriber is the duration-based stub (which needs
        # the FULL buffer sample count to reveal words over time) vs a real ASR
        # (which uses the bounded sliding window). Set in load_reference.
        self._is_stub = True

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
            # An explicit transcriber (tests / real ASR injection) is treated as
            # real so it uses the bounded sliding window.
            self._is_stub = False
        elif settings.ml_use_stub or not self.reference_words:
            self._transcriber = _make_stub_transcriber(self.reference_words)
            self._is_stub = True
        else:
            # Real ASR requested. Probe whether the Faster-Whisper CT2 model is
            # actually loadable in this container (it must be bind-mounted at
            # QARI_FASTERWHISPER_MODEL_DIR). If it is missing/unloadable the real
            # transcriber would silently return [] on every call. Critically,
            # never fall back to the duration-based demo stub here: that stub
            # reveals one word every 0.9 seconds without inspecting speech and
            # therefore auto-completes an ayah when the user says nothing.
            try:
                from ml.inference.faster_whisper_transcriber import get_transcriber

                get_transcriber().load()
                self._transcriber = _real_transcriber
                self._is_stub = False
                logger.info(
                    "stream.transcriber", session_id=self.session_id,
                    engine="faster-whisper", words=len(self.reference_words),
                )
            except Exception as exc:
                logger.error(
                    "stream.real_transcriber_unavailable",
                    session_id=self.session_id, error=str(exc),
                )
                raise LiveTranscriberUnavailable(
                    "Live speech recognition is temporarily unavailable. "
                    "The recitation model could not be loaded."
                ) from exc

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

    # Background transcription loop (driven by the WebSocket handler so the
    # receive loop never blocks on the slow Whisper call). Re-transcribes the
    # accumulated audio on a fixed cadence and emits `word` events as words
    # resolve. A single in-flight transcription is guarded by `_transcribe_lock`
    # so concurrent ticks never stack.
    def stop_transcription(self) -> "asyncio.Future":
        self._transcribe_stop = True
        return asyncio.sleep(0)  # no-op awaitable for callers

    async def transcription_loop(self, websocket) -> None:
        self._transcribe_stop = False
        try:
            while not self._transcribe_stop:
                try:
                    t0 = asyncio.get_event_loop().time()
                    for event in await self.maybe_transcribe():
                        await websocket.send_json(event)
                except Exception as exc:  # pragma: no cover - model failures
                    logger.error("stream.loop_transcribe_failed", session_id=self.session_id, error=str(exc))
                # Sleep only the *remaining* interval after a (possibly slow)
                # transcription pass so the cadence stays ~constant regardless of
                # how long Whisper took. This keeps the live reveal smooth
                # instead of a fixed 1.2s gap stacked on top of each pass.
                elapsed = asyncio.get_event_loop().time() - t0
                remaining = TRANSCRIBE_INTERVAL_SEC - elapsed
                if remaining > 0:
                    await asyncio.sleep(remaining)
        except asyncio.CancelledError:
            return

    @property
    def _total_samples(self) -> int:
        return len(self._pcm) // 2  # 16-bit samples

    @property
    def duration_seconds(self) -> float:
        return self._total_samples / self.sample_rate if self.sample_rate else 0.0

    def _rms_energy(self, samples: list[float]) -> float:
        """Root-mean-square energy of a float32 signal in [0, 1].

        Used to detect silence: near-silent mic audio (room tone / the user not
        reciting) has a very low RMS, while actual recitation is markedly higher.
        """
        if not samples:
            return 0.0
        return (sum(s * s for s in samples) / len(samples)) ** 0.5

    def _decode_float(self, start_sample: int = 0, end_sample: Optional[int] = None):
        # Numpy-free decode: convert the raw PCM16 bytes into a list of float32
        # samples in [-1, 1]. Kept dependency-light so the live stream runs in
        # the API container without the full ML stack. Optionally decode only the
        # sample range [start_sample, end_sample) — the sliding window transcribes
        # a bounded recent span instead of the whole growing buffer.
        if not self._pcm:
            return []
        import array

        start_byte = max(0, start_sample) * 2
        end_byte = (
            len(self._pcm)
            if end_sample is None
            else min(len(self._pcm), end_sample * 2)
        )
        # PCM length may be odd (partial final frame); align to an even byte
        # boundary so `array.frombytes` never sees a half-sample. Without this
        # the real-ASR sliding-window path raised ValueError on every pass ->
        # no word events fired during streaming (the reveal only "dumped" on the
        # forced final transcribe), which is exactly the "buffering" feel.
        end_byte -= end_byte % 2
        if end_byte <= start_byte:
            return []
        samples = array.array("h")
        samples.frombytes(bytes(self._pcm[start_byte:end_byte]))
        return [s / 32768.0 for s in samples]

    # ------------------------------------------------------------------
    async def maybe_transcribe(self, *, force: bool = False) -> list[dict]:
        """Re-transcribe if enough new audio arrived; return new word events.

        For the real ASR we transcribe only a bounded SLIDING WINDOW of the most
        recent audio (``TRANSCRIBE_WINDOW_SEC``) and stitch the new words onto the
        cumulative hypothesis — so per-pass cost stays ~constant and the live
        reveal keeps up regardless of recitation length. The duration-based STUB
        still needs the full buffer (it reveals words from the total sample
        count), so it runs on the whole buffer (which is cheap for the stub).
        """
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
            total = self._total_samples

            if self._is_stub:
                # Stub reveals words from the TOTAL duration → needs full buffer.
                audio = self._decode_float()
                try:
                    words, confs = await asyncio.to_thread(
                        self._transcriber, audio, self.sample_rate
                    )
                except Exception as exc:  # pragma: no cover - model failures
                    logger.error(
                        "stream.transcribe_failed",
                        session_id=self.session_id, error=str(exc),
                    )
                    return []
                self._hypothesis = list(words)
                self._hypothesis_confs = list(confs)
            else:
                # Real ASR: transcribe only the last TRANSCRIBE_WINDOW_SEC of
                # audio and stitch the new words onto the cumulative hypothesis.
                window_samples = int(TRANSCRIBE_WINDOW_SEC * self.sample_rate)
                start = max(0, total - window_samples)
                audio = self._decode_float(start_sample=start)
                # Silence gate: if this window is essentially quiet (the user is
                # not reciting), Whisper would still hallucinate phantom Arabic
                # words that "complete" the ayah on their own. Skip transcription
                # and emit NO events so nothing resolves until there is real
                # speech. Do NOT advance `_samples_at_last_transcribe` so the next
                # pass that does contain speech still re-scans this quiet span.
                if self._rms_energy(audio) < SILENCE_RMS_THRESHOLD:
                    return []
                try:
                    win_words, win_confs = await asyncio.to_thread(
                        self._transcriber, audio, self.sample_rate
                    )
                except Exception as exc:  # pragma: no cover - model failures
                    logger.error(
                        "stream.transcribe_failed",
                        session_id=self.session_id, error=str(exc),
                    )
                    return []
                stitched, stitched_confs = stitch_hypothesis(
                    self._hypothesis,
                    self._hypothesis_confs,
                    win_words,
                    win_confs,
                )
                # Clamp the cumulative hypothesis so ASR hallucinations /
                # repeated-token explosions can't drive the matcher far past the
                # reference. The matcher only ever resolves up to len(reference),
                # so anything beyond a small margin is pure noise that would make
                # it skip ahead of the user. Keep at most ref_len + LOOKAHEAD words.
                cap = len(self.reference_words) + getattr(
                    self._matcher, "lookahead", 3
                )
                if len(stitched) > cap:
                    stitched = stitched[:cap]
                    stitched_confs = stitched_confs[:cap]
                self._hypothesis = stitched
                self._hypothesis_confs = stitched_confs

            self._last_hypothesis = self._hypothesis
            states = self._matcher.evaluate(
                self._hypothesis, self._hypothesis_confs
            )
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

    def _run_tajweed_checks(
        self, audio
    ) -> Optional[tuple[float, list[dict]]]:
        """Timed full-audio transcription → acoustic tajweed checks.

        Runs synchronously (call via ``asyncio.to_thread``). Returns
        ``(score_0_to_1, surfaced_issue_dicts)`` or ``None`` when nothing
        could be evaluated. Uses the CT2 word timestamps instead of the
        torch forced aligner so it works inside the live API container.
        """
        from ml.inference.asr import normalize_arabic
        from ml.inference.faster_whisper_transcriber import get_transcriber
        from ml.tajweed.checks import TajweedChecker

        words, _confs, starts, ends = get_transcriber().transcribe_with_timings(
            audio, self.sample_rate
        )
        if not words:
            return None
        norm = [normalize_arabic(w) for w in words]
        summary = TajweedChecker(sample_rate=self.sample_rate).check_all(
            audio, norm, starts, ends
        )
        if summary.total_checks == 0:
            return None
        issues = [
            {
                "rule": r.check_type.value,
                "word_index": r.word_index,
                "word": norm[r.word_index]
                if r.word_index is not None and r.word_index < len(norm)
                else None,
                "letter": r.letter,
                "detail": r.detail,
                "start_ms": r.start_ms,
                "end_ms": r.end_ms,
            }
            for r in summary.results
            if r.should_surface
        ]
        return summary.tajweed_score / 100.0, issues

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

        # Best-effort tajweed pass (Tarteel-style post-session "mistake
        # review"): one timed full-audio transcription feeds the acoustic
        # tajweed checks (ghunnah/qalqalah/madd — numpy only, no torch).
        # Never blocks the result on failure; stub sessions and very long
        # sessions skip it.
        tajweed_score = 0.0
        tajweed_issues: list[dict] = []
        if (
            not self._is_stub
            and total
            and self._pcm
            and self.duration_seconds <= 300
        ):
            try:
                audio = self._decode_float()
                tj = await asyncio.to_thread(self._run_tajweed_checks, audio)
                if tj is not None:
                    tajweed_score, tajweed_issues = tj
            except Exception as exc:  # pragma: no cover - analysis best-effort
                logger.warning(
                    "stream.tajweed_failed",
                    session_id=self.session_id,
                    error=str(exc),
                )

        result = {
            "session_id": self.session_id,
            "surah_number": self.surah,
            "ayah_number": self.ayah_from,
            "overall_score": round(accuracy, 4),
            "pronunciation_score": round(accuracy, 4),
            "tajweed_score": round(tajweed_score, 4),
            "tajweed_issues": tajweed_issues,
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
