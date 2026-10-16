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
# The pinned RNNT decoder finishes well within this interval on the VPS.
# Keep the existing Whisper/stub cadence and all recognition guards unchanged.
RNNT_TRANSCRIBE_INTERVAL_SEC = .9
RNNT_STARTUP_INTERVAL_SEC = .6
# --- Early first pass (2026-09-26): cut the first-word latency ---------------
#
# Measured decomposition of the ~2.1 s first-word latency on this 4-vCPU VPS:
#   ~1.2 s waiting for TRANSCRIBE_INTERVAL_SEC of audio to accumulate, plus
#   ~1.0-1.1 s for the unprompted decode of the 6.0+1.5 s window.
# The steady-state interval and window are NOT changed (recorded regressions:
# a 5.0 s window stalled the end of the surah, VERIFY_EVERY_N_PASSES=2 produced
# 5-13 s apparent latency). Instead ONLY the very first pass of a session is
# allowed to fire early, on a shorter window:
#
#   * EARLY_FIRST_PASS_SEC       audio required before pass #1 (was 1.2 s)
#   * EARLY_FIRST_PASS_WINDOW_S  window length for pass #1 (was 7.5 s)
#
# A shorter window also decodes faster, so this attacks BOTH terms. It applies
# once per session; the normal interval/window resume immediately afterwards.
# SAFETY: a very short window is where Whisper hallucinates, so this is gated on
# the same SILENCE_RMS_THRESHOLD check as every other pass, and the output is
# still only accepted through the unchanged matcher corroboration path.
#
# *** DEFAULT IS OFF — MEASURED NEGATIVE RESULT, DO NOT SIMPLY RE-ENABLE ***
# Enabling it made first-word latency WORSE, not better:
#     OFF : 2094 / 2119 / 2131 / 2139 / 2185 ms   (p50 ~2131)
#     ON  : 3137 / 3139 / 3142 / 3145 ms          (p50 ~3142)  <- +1.0 s WORSE
# Cause: 0.5 s of audio is below what Whisper needs to emit a usable
# transcript, so the "early" pass spends a full ~1 s decode producing nothing,
# and the real first word is pushed out by exactly that wasted decode. The
# window reduction does not help either: decode cost is independent of window
# length (measured: 7.5 s and 2.5 s windows both decode in 0.977 s) because
# Whisper pads input to 30 s internally.
#
# The ~1 s decode is a hard per-pass floor on this CPU, so there is no window /
# interval tuning that gets to 400 ms. Reaching it needs the GPU migration or a
# VAD + forced-alignment path that never runs Whisper per pass.
#
# The code and the env knobs are kept (QARI_EARLY_FIRST_PASS=1 to re-enable, and
# QARI_EARLY_FIRST_PASS_SEC to retune) so the negative result is reproducible
# rather than folklore. The loop-cadence coupling fix below is kept because it
# is correct regardless of this flag.
EARLY_FIRST_PASS = os.environ.get("QARI_EARLY_FIRST_PASS", "0").lower() in (
    "1", "true", "yes",
)
EARLY_FIRST_PASS_SEC = float(os.environ.get("QARI_EARLY_FIRST_PASS_SEC", "0.5"))
EARLY_FIRST_PASS_WINDOW_S = float(
    os.environ.get("QARI_EARLY_FIRST_PASS_WINDOW_S", "2.5")
)
# Users-perceived latency TARGET for a match, to be re-measured after the GPU
# migration. One unprompted decode of even a short window costs ~0.4-1.1 s on
# this CPU, so 400 ms is NOT achievable here today — recorded so the gap is
# explicit and re-measurable, not silently claimed.
TARGET_FIRST_WORD_MS = int(os.environ.get("QARI_TARGET_FIRST_WORD_MS", "400"))

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
# The window (+ OVERLAP) controls both context and reveal latency. Tried a
# shorter 5.0s window: faster cadence but it lost the boundary-word context
# and stalled the end of the surah, so 6.0s stays. Latency is instead kept
# down by making each pass cheaper (unprompted verification runs on alternate
# passes — see _verify_every) and by the decode caps in the transcriber.
TRANSCRIBE_WINDOW_SEC = 6.0
# Run the unprompted verification decode only every N-th pass. Successive
# windows overlap heavily, so a verification set stays valid for the next
# pass; skipping the verification on alternate passes halves the average pass
# cost.
# NOTE: this MUST stay 1 in production. With N=2 the tier-2 evidence set is up
# to two passes (~4s) STALE, so a word the user has just spoken is not yet in
# it, tier-1 gets filtered as "uncorroborated" and the reveal waits for the
# next refresh — measured 5-13s apparent word latency over a full-surah
# recitation (the "words stop appearing" symptom). The concurrent tier-1 +
# tier-2 decode is ~2s, which the cadence absorbs, so fresh evidence every
# pass costs little and is what keeps the reveal tracking the voice.
VERIFY_EVERY_N_PASSES = 1
# Max already-resolved words used as the ORACLE prompt (see maybe_transcribe).
# Bounded because long prompts drift; 10 keeps the anchor local to the audio.
PROMPT_ANCHOR_WORDS = 10
# Left-overlap added to every sliding window. Without it a word straddling
# the window boundary is CUT IN HALF: the model sees only the word's tail in
# the next window and emits a broken fragment (e.g. 'ٰطَ' for 'صِرَٰطَ')
# that matches nothing — the matcher stalls and live events stop (observed
# at ayah boundaries in full-surah sessions). The overlap keeps the whole
# boundary word inside the window; stitch_hypothesis() already dedups the
# repeated tail (STITCH_MAX_OVERLAP_WORDS).
TRANSCRIBE_WINDOW_OVERLAP_SEC = 1.5
# How many not-yet-consumed hypothesis words to retain past the matcher's
# consumed prefix. Bounds repetition bursts without ever truncating the tail
# where freshly transcribed words are appended.
HYPO_TAIL_CAP = 40
# Max words of overlap to search when stitching a new window onto the cumulative
# hypothesis (drops words the previous window already contributed).
STITCH_MAX_OVERLAP_WORDS = 12
# Three80ms RNNT frames of right context protect against a word predicted from
# an unfinished suffix. In a real paced stream, 5.7s of عليكم was decoded as
# عليهم(.794); the complete6.0s window corrected it to عليكم(.841).
LIVE_RIGHT_CONTEXT_SEC = .24

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

# Verbose per-pass live diagnostics (tier-1/tier-2 words, matcher cursor, stall
# counter). Off by default — enable with QARI_STREAM_DEBUG=1 when diagnosing a
# live tracking problem, otherwise it floods the logs every ~2s per session.
STREAM_DEBUG = os.environ.get("QARI_STREAM_DEBUG", "").lower() in ("1", "true", "yes")

# Preserve the established review of short recordings. Full-surah RNNT
# attention otherwise grows without bound and can exhaust the API's memory.
FINAL_RECORDING_SINGLE_PASS_SEC = 240
FINAL_RECORDING_CHUNK_SEC = 30

# Live evidence policy — WHICH decode feeds the live word reveal.
#
#   "tier2" (default): the INDEPENDENT, unprompted base decode is the live
#       hypothesis. This is the only witness that reports what the reciter
#       actually said. Measured on this VPS: 29/29 words revealed live on a real
#       Al-Fatiha recitation (repeatedly), and only 7/29 on an unrelated clip
#       (Fatiha's repeated words, textually ambiguous).
#   "corroborated": the prompt-conditioned Qari model supplies the words, kept
#       only where the independent decode agrees. Cleaner segmentation, but the
#       Qari model is an ORACLE (see _independent_transcriber): its echo of the
#       expected text passes corroboration whenever the independent decode heard
#       *any* occurrence of the same word, so it over-reveals (measured 9/29 on
#       the same unrelated clip).
#
# Live tracking therefore runs on the independent witness; the prompt-conditioned
# Qari model still drives the FINAL review (timed full-audio pass + tajweed
# checks), where it is scoring against the recorded audio instead of steering a
# live reveal.
EVIDENCE_POLICY = os.environ.get("QARI_EVIDENCE_POLICY", "tier2").lower()

# A transcriber turns a float32 mono 16 kHz signal into (normalized_words,
# per_word_confidences).
Transcriber = Callable[["object", int], "tuple[list[str], list[float]]"]


class LiveTranscriberUnavailable(RuntimeError):
    """Raised when production live ASR cannot be loaded safely."""


# ---------------------------------------------------------------------------
# Reference resolution (expected normalized words for an ayah)
# ---------------------------------------------------------------------------

# Lightweight live normalizer; dagger alef retains its spoken long vowel. The
# streaming reference resolution does NOT import the heavy ASR module (torch /
# numpy). The live stream only needs lightweight normalization + the pure-Python
# StreamingMatcher; the full ASR engine is only used by the real transcriber.
import re as _re
import unicodedata as _unicodedata

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
    # Establish word boundaries and ya variants before preserving identities.
    text = "".join(" " if _unicodedata.category(c).startswith("P") else c
                   for c in text).replace("ی", "ي")
    # At word end, maqsura already carries the long vowel. Preserve internal
    # carrier keys used by existing corpus aliases and dagger expansion elsewhere.
    text = _re.sub(
        r"ى([ـً-ٟ]*)ٰ(?=[ؘ-ًؚ-ٟۖ-ۭ]*(?:\s|$))",
        r"ى\1", text,
    )
    # Protect only an ORIGINAL ya + final maqsura. Expanding small-high ya
    # later can also produce يى (يُحْـِۧىَ); that is yuhyi, not yahya.
    maqsura_tag = "\ue000"
    text = _re.sub(r"(ي[ـؘ-ًؚ-ٟ]*)ى(?=[ـؘ-ًؚ-ٟۖ-ۭ]*(?:\s|$))",
                   lambda match: match.group(1) + maqsura_tag, text)
    text = text.replace("ٰ", "ا").replace("ۧ", "ي").replace("۞", " ")
    text = _HARAKAT.sub("", text)
    text = _TATWEEL.sub("", text)
    for variant, canonical in _ALEF.items():
        text = text.replace(variant, canonical)
    for variant, canonical in _YA.items():
        text = text.replace(variant, canonical)
    text = text.replace(maqsura_tag, "ى")
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


_reference_store_cache = None


def _get_reference_store():
    """Return a process-wide, read-only :class:`ReferenceStore` (built once).

    ``ReferenceStore.__init__`` globs and parses EVERY ``{surah}_{ayah}.json``
    bundle in ``reference_data_dir`` (~0.6s of disk + JSON work on this VPS).
    Rebuilding it on every ``resolve_reference_words`` call made a full-surah
    session (7 ayahs) spend 4+ seconds in ``load_reference`` BEFORE the
    ``ready`` handshake — the "app is frozen when I tap start" cold-start
    freeze. The store is immutable after load (a plain ``(surah, ayah) ->
    AyahReference`` dict with instant lookups), so one shared instance is safe
    and makes repeat lookups free. Mirrors the cached-store pattern already used
    in ``app.workers.inference_worker``.
    """
    global _reference_store_cache
    if _reference_store_cache is None:
        from ml.tajweed.reference_store import ReferenceStore

        _reference_store_cache = ReferenceStore(settings.reference_data_dir or None)
    return _reference_store_cache


_live_error_vocab_cache: Optional[tuple[object, frozenset[str]]] = None


def _get_live_error_vocabulary() -> frozenset[str]:
    """Known words across the immutable corpus, used only to confirm errors.

    Garbled ASR strings are recognition gaps, not proof of a spoken mistake.
    This vocabulary never enters recognition or supplies words to the matcher.
    """
    global _live_error_vocab_cache
    try:
        store = _get_reference_store()
        if _live_error_vocab_cache is not None and _live_error_vocab_cache[0] is store:
            return _live_error_vocab_cache[1]
        vocabulary: set[str] = set()
        for key in store.list_ayahs():
            ref = store.get(*key)
            if ref is None:
                continue
            for word in ref.words:
                vocabulary.add(_normalize(word.word))
                text = word.text_with_tashkeel or ""
                vocabulary.add(_normalize(text))
        vocabulary.discard("")
        frozen = frozenset(vocabulary)
        _live_error_vocab_cache = (store, frozen)
        return frozen
    except Exception as exc:
        logger.debug("stream.error_vocab_unavailable", error=type(exc).__name__)
        return frozenset()


_live_word_alias_cache: Optional[tuple[object, dict[str, str]]] = None

# Independently published Imla'i / Uthmani spellings, not model predictions.
# Provenance and collision checks: docs/recitation-orthography.md.
_PUBLISHED_WORD_SPELLINGS = (
    ("نحيي", "نُحْىِ"),
    ("يحيي", "يُحْىِ"),
    ("شيئا", "شَيْـًٔا"),
)
# Independently attested vocatives only. Lossy normalized forms of يأمن or
# يأكل also start with يا, but are verbs and cannot authorize such a join.
_PUBLISHED_VOCATIVES = ("ياقوم", "ياليت", "ياحسرة", "ياويلنا", "يابني")


def _get_live_word_aliases() -> dict[str, str]:
    """Unambiguous legacy spellings and explicit published spelling families.

    These compare reference/recognition text only; they never enter ASR. A key
    that is itself a canonical Quran word (or has multiple targets) cannot
    acquire a legacy alias. Only the separately verified published families
    may unify canonical printed forms; عليكم cannot become عليهم here.
    """
    global _live_word_alias_cache
    try:
        store = _get_reference_store()
        if _live_word_alias_cache is not None and _live_word_alias_cache[0] is store:
            return dict(_live_word_alias_cache[1])
        canonical_words: set[str] = set()
        targets: dict[str, set[str]] = {}
        for key in store.list_ayahs():
            reference = store.get(*key)
            if reference is None:
                continue
            for word in reference.words:
                legacy = _normalize(word.word)
                canonical = _normalize(word.text_with_tashkeel or word.word)
                if canonical:
                    canonical_words.add(canonical)
                if legacy and canonical and legacy != canonical:
                    targets.setdefault(legacy, set()).add(canonical)
        published = {_normalize(uthmani): _normalize(imlai)
                     for imlai, uthmani in _PUBLISHED_WORD_SPELLINGS}
        reserved = set(published) | set(published.values())
        aliases = {
            legacy: next(iter(candidates))
            for legacy, candidates in targets.items()
            if legacy not in canonical_words and legacy not in reserved and len(candidates) == 1
        }
        # Published spellings reserve their own identity ahead of lossy legacy
        # keys: old يحيي on a Yahya bundle must not redirect actual yuhyi.
        # Both printed forms are verified identities, including canonical
        # يُحْـِۧىَ -> يحيي. Never redirect that key using an old Yahya bundle.
        aliases.update({key: target for key, target in published.items()
                        if key in canonical_words})
        _live_word_alias_cache = (store, aliases)
        return dict(aliases)
    except Exception as exc:
        logger.debug("stream.word_aliases_unavailable", error=type(exc).__name__)
        return {}


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
    # 1) ML reference store (prebuilt {surah}_{ayah}.json bundle) — cached.
    try:
        store = _get_reference_store()
        if store.has(surah, ayah):
            ref = store.get(surah, ayah)
            display = [w.text_with_tashkeel or w.word for w in ref.words]
            norm = [_normalize(text) for text in display]
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


def _real_transcriber(
    audio, sr: int, initial_prompt: str = ""
) -> tuple[list[str], list[float]]:
    """Transcribe with Faster-Whisper (CT2, INT8) — CPU-efficient real-time ASR.

    Runs the **Qari V50 trained model** (prompt-conditioned LoRA merged into
    whisper-base-ar-quran, converted to CTranslate2 INT8 from local files).
    ``initial_prompt`` = expected ayah text (tashkeel) — the ORACLE prompt the
    model was trained with (WER 0.0065 prompted vs 6.8 unprompted); it curbs
    the repetition loops the free-running decoder falls into. Raw Arabic
    tokens are normalized with the *same* ``_normalize`` used for the reference
    words, so the :class:`StreamingMatcher` compares hypothesis ↔ reference on a
    consistent basis. Returns ``([], [])`` on any failure so the session falls
    back to the stub-style behaviour instead of crashing.
    """
    try:
        from ml.inference.faster_whisper_transcriber import get_transcriber

        raw_words, confs = get_transcriber().transcribe(audio, sr, initial_prompt)
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


def _accepts_prompt(transcriber) -> bool:
    """Whether a transcriber callable takes an oracle prompt as 3rd argument.

    Transcriber callables come in two shapes: the production Faster-Whisper
    wrapper takes ``(audio, sample_rate, prompt)``, while the duration stub and
    the injected test fakes take ``(audio, sample_rate)``. Calling a 2-arg
    callable with 3 arguments raised TypeError, which the live loop swallowed
    (``stream.transcribe_failed``) — so NO word event ever fired on the stub
    path and the streaming WebSocket test hung waiting for them.
    """
    import inspect

    try:
        params = inspect.signature(transcriber).parameters
    except (TypeError, ValueError):  # builtins / C callables: assume flexible
        return True
    count = 0
    for param in params.values():
        if param.kind == param.VAR_POSITIONAL:
            return True
        if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
            count += 1
    return count >= 3


def _invoke_transcriber(transcriber, audio, sr: int, prompt: str):
    """Call ``transcriber`` with the prompt only when it accepts one."""
    if _accepts_prompt(transcriber):
        return transcriber(audio, sr, prompt)
    return transcriber(audio, sr)


def _independent_recording_transcriber(audio, sr: int) -> tuple[list[str], list[float]]:
    """Review long RNNT recordings without an unbounded encoder allocation.

    Each sample belongs to exactly one native decode. No overlap stitching,
    reference text, or synthetic confidence can become final speech evidence.
    Boundary words may remain uncertain; confirmed live evidence is retained
    separately by the final matcher. Whisper already manages its own chunks.
    """
    if _live_asr_engine() != "fastconformer_rnnt" or len(audio) <= FINAL_RECORDING_SINGLE_PASS_SEC * sr:
        return _independent_transcriber(audio, sr)
    if sr != 16000:
        raise ValueError("RNNT recording review requires 16000 Hz mono PCM")
    words, confidences = [], []
    chunk_samples = FINAL_RECORDING_CHUNK_SEC * sr
    logger.info("stream.recording_review_chunked", seconds=round(len(audio) / sr, 3),
                chunk_seconds=FINAL_RECORDING_CHUNK_SEC)
    for start in range(0, len(audio), chunk_samples):
        chunk = audio[start:start + chunk_samples]
        if _rms_energy(chunk) < SILENCE_RMS_THRESHOLD:
            continue
        native_words, native_confidences = _independent_transcriber(chunk, sr)
        words.extend(native_words)
        confidences.extend(native_confidences)
    return words, confidences


def _independent_transcriber(audio, sr: int) -> tuple[list[str], list[float]]:
    """UNPROMPTED decode with the independent base model — the honest witness.

    The Qari adapter is an ORACLE model (trained to reproduce the expected text
    given as the prompt), so it cannot validate a recitation: with Al-Fatiha as
    the prompt it emits Al-Fatiha even when the audio is a totally different
    recitation (verified on this VPS). Only a decode that never sees the
    expected text can tell what the reciter actually said, which is what the
    live matcher needs to flag real mistakes.
    """
    try:
        if _live_asr_engine() == "fastconformer_rnnt":
            from ml.inference.fastconformer_transcriber import get_transcriber
            decoded = get_transcriber().transcribe(audio, sr)
        else:
            from ml.inference.faster_whisper_transcriber import get_transcriber
            decoded = get_transcriber().transcribe_independent(audio, sr)
        raw_words, confs = decoded
    except Exception as exc:  # pragma: no cover - model/load failures
        logger.error("stream.independent_decode_failed", error=str(exc))
        return [], []

    norm: list[str] = []
    out_confs: list[float] = []
    timings = getattr(decoded, "timings", None)
    out_timings = []
    for index, (w, c) in enumerate(zip(raw_words, confs)):
        n = _normalize(w)
        if n:
            norm.append(n)
            out_confs.append(c)
            if timings is not None:
                out_timings.append(timings[index])
    if timings is not None:
        from ml.inference.transcript import TimedTranscript
        return _join_split_vocatives(TimedTranscript(norm, out_confs, out_timings))
    return norm, out_confs


def _join_split_vocatives(transcript):
    """Join native يا + word only when the global Quran corpus has that form.

    Neither recognition nor this conversion receives the selected passage.
    Keep the weaker component's native confidence and the complete time span.
    Untimed decoders cannot supply evidence for this conversion.
    """
    from ml.inference.transcript import TimedTranscript

    vocabulary = _get_live_error_vocabulary()
    vocatives = {_normalize(word) for word in _PUBLISHED_VOCATIVES}
    words, confidences, timings = [], [], []
    for word, confidence, timing in zip(transcript.words, transcript.confidences, transcript.timings):
        if (words and words[-1] == "يا" and "يا" + word in vocatives
                and "يا" + word in vocabulary
                and 0 <= timing[0] - timings[-1][1] <= .8 + 1e-6):
            words[-1] += word
            confidences[-1] = min(confidences[-1], confidence)
            timings[-1] = (timings[-1][0], timing[1])
        else:
            words.append(word)
            confidences.append(confidence)
            timings.append(timing)
    return TimedTranscript(words, confidences, timings)


def _live_asr_engine() -> str:
    engine = os.environ.get("QARI_LIVE_ASR_ENGINE", "faster_whisper")
    if engine not in {"faster_whisper", "fastconformer_rnnt"}:
        raise ValueError("Unsupported live ASR engine")
    return engine


def _make_stub_transcriber(reference_words: list[str]) -> Transcriber:
    """Duration-based stub: reveal reference words as audio accumulates.

    Lets the full live flow be demoed without model weights. It reveals one
    reference word per ``STUB_SECONDS_PER_WORD`` of audio, so words light up
    green sequentially as the user "recites".

    Silence gate: only reveal words when the audio actually contains speech
    (RMS above ``SILENCE_RMS_THRESHOLD``). Without this, room tone / breath
    alone would accumulate duration and auto-complete the ayah even though the
    user said nothing — matching the real-ASR path's behaviour.
    """

    def _transcribe(audio, sr: int) -> tuple[list[str], list[float]]:
        try:
            n = len(audio)
        except TypeError:
            n = 0
        # Silence gate: if the audio is essentially quiet (the user is not
        # reciting), reveal nothing — even the stub must not auto-complete the
        # ayah on room tone / breath alone.
        if _rms_energy(audio) < SILENCE_RMS_THRESHOLD:
            return [], []
        seconds = (n / sr) if sr else 0.0
        reveal = min(len(reference_words), int(seconds / STUB_SECONDS_PER_WORD))
        words = list(reference_words[:reveal])
        return words, [0.9] * len(words)

    return _transcribe


# Reviewed spelling identities for already-consumed native tokens only.
# Alif-lam and wasla-lam are not general proof of an article (e.g. اللهم/لهم,
# التقى/تقي, ألوانه/وأنه). Keep this table explicit; no tokens are synthesized.
_STITCH_ARTICLE_IDENTITIES = frozenset({
    frozenset(('اليتيم', 'يتيم')),
    frozenset(('السايل', 'سايل')),
})


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

    # These reviewed article variants still have to pass the same consumed
    # PCM/time conditions; a genuine later repetition remains a new word.
    if frozenset((na, nb)) in _STITCH_ARTICLE_IDENTITIES:
        return True

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
    replace that overlap with the latest tokens AND their confidences, then
    append the remainder. Keeping the first window's low score would cause the
    live matcher to skip a word even after a clearer decode confirms it. Taking
    the latest pair also avoids assigning an old token a different token's score
    or retaining stale high confidence when the new decode is less certain.
    The same spoken word is never counted twice, so hypothesis length tracks
    actual progress instead of exploding.

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
    keep = len(prefix) - best_k
    merged = list(prefix[:keep]) + list(window_words)
    merged_confs = list(prefix_confs[:keep]) + list(window_confs)
    return merged, merged_confs


def _rms_energy(samples: list[float]) -> float:
    """Root-mean-square energy of a float32 signal in [0, 1].

    Used to detect silence: near-silent mic audio (room tone / the user not
    reciting) has a very low RMS, while actual recitation is markedly higher.
    """
    if len(samples) == 0:
        return 0.0
    return (sum(s * s for s in samples) / len(samples)) ** 0.5


def _stitch_timed_hypothesis(
    prefix, prefix_confs, prefix_times, window_words, window_confs,
    window_times, *, consumed, consumed_end, window_start, window_seconds,
    confidence_threshold, right_context_seconds=0.0,
):
    """Retain consumed evidence and replace the remaining overlapping audio.

    RNNT bounds describe token emissions, with an 80ms frame. A distinct
    adjacent word may share that frame; an already consumed word may not be
    counted again. A confident identical word beginning on the same past
    emission frame anchors an end-time revision even with one consumed word.
    Two confident past tokens also anchor revisions whose first emission moved.
    """
    import math
    if not len(window_words) == len(window_confs) == len(window_times):
        raise ValueError("Timed transcript evidence must align")
    absolute = []
    previous = -1.0
    for confidence, (begin, end) in zip(window_confs, window_times):
        if not all(math.isfinite(v) for v in (begin, end, confidence)):
            raise ValueError("Nonfinite timed evidence")
        if not (0 <= begin <= end <= window_seconds + .08
                and begin >= previous and 0 <= confidence <= 1):
            raise ValueError("Timed evidence is outside its PCM window")
        previous = begin
        absolute.append((begin + window_start, end + window_start))
    keep = min(max(0, int(consumed)), len(prefix))
    if keep > len(prefix_confs) or keep > len(prefix_times):
        raise ValueError("Consumed timed evidence is incomplete")
    overlap_end = 0
    if keep and prefix_confs[keep - 1] >= confidence_threshold:
        previous_begin = prefix_times[keep - 1][0]
        for index, (begin, _) in enumerate(absolute):
            if (begin <= consumed_end + .08 + 1e-6
                    # A growing past span may start one encoder frame earlier.
                    # Allow float32 rounding, but never eat a later repetition.
                    and previous_begin - .08 - 1e-5 <= begin <= previous_begin + 1e-5
                    and window_confs[index] >= confidence_threshold
                    and _normalize(window_words[index]) == _normalize(prefix[keep - 1])):
                overlap_end = index + 1
                break
    if (keep >= 2 and prefix_confs[keep - 2] >= confidence_threshold
            and prefix_confs[keep - 1] >= confidence_threshold
            and prefix[keep - 2] != prefix[keep - 1]):
        for index in range(len(window_words) - 1):
            if (absolute[index][1] <= consumed_end + .08
                    and absolute[index + 1][1] <= consumed_end + .5
                    and window_confs[index] >= confidence_threshold
                    and window_confs[index + 1] >= confidence_threshold
                    and _words_similar(window_words[index], prefix[keep - 2])
                    and _words_similar(window_words[index + 1], prefix[keep - 1])):
                overlap_end = max(overlap_end, index + 2)
                break
    # A weak token between two strong past words must not make the last word
    # a fresh occurrence when its emission end grows in the next decode.
    # Require two unique native start-frame witnesses and a nontrivial old
    # final span; a zero-frame word could genuinely repeat one frame later.
    if (keep >= 3 and prefix_confs[keep - 3] >= confidence_threshold
            and prefix_confs[keep - 2] < confidence_threshold
            and prefix_confs[keep - 1] >= confidence_threshold):
        old = prefix_times[keep - 3:keep]
        def same_identity(a, b):
            a, b = _normalize(a), _normalize(b)
            return bool(a and b) and (a == b or frozenset((a, b)) in _STITCH_ARTICLE_IDENTITIES)
        if (all(math.isfinite(v) for span in old for v in span)
                and all(a <= b for a, b in old)
                and window_start <= old[0][0]
                and old[0][0] + .16 <= old[2][0] + 1e-6
                and old[2][1] - old[2][0] >= .16 - 1e-6
                and old[0][1] <= old[1][0] + .08
                and old[1][1] <= old[2][0] + .08
                and not same_identity(prefix[keep - 3], prefix[keep - 1])):
            hits = []
            for i in range(2, len(window_words)):
                spans = absolute[i - 2:i + 1]
                if (any(window_confs[j] < confidence_threshold for j in (i - 2, i))
                        or not all(same_identity(window_words[j], prefix[k])
                                   for j, k in ((i - 2, keep - 3), (i, keep - 1)))
                        or any(abs(spans[k][0] - old[k][0]) > .08 + 1e-6 for k in (0, 2))
                        or spans[0][0] + .16 > spans[2][0] + 1e-6
                        or any(max(spans[k][0], old[k][0]) > min(spans[k][1] + .08, old[k][1] + .08) for k in (0, 2))
                        or spans[0][1] > spans[1][0] + .08
                        or spans[1][1] > spans[2][0] + .08
                        or spans[2][1] + .08 > window_start + window_seconds - right_context_seconds):
                    continue
                if any(j not in (i - 2, i) and window_confs[j] >= confidence_threshold
                       and any(abs(bounds[0] - spans[k][0]) <= .08 + 1e-6 for k in (0, 2))
                       for j, bounds in enumerate(absolute)):
                    continue
                hits.append(i)
            if len(hits) == 1:
                overlap_end = max(overlap_end, hits[0] + 1)
    fresh = [
        index for index, (_, end) in enumerate(absolute)
        if index >= overlap_end and end > consumed_end - .08
        and (right_context_seconds <= 0.0
             # RNNT timestamps are emission-frame starts. Count that 80 ms
             # frame before requiring complete future context from PCM.
             or end + .08 <= window_start + window_seconds - right_context_seconds)
        and not (keep and end <= consumed_end + .08
                 and _words_similar(window_words[index], prefix[keep - 1]))
    ]
    return (
        list(prefix[:keep]) + [window_words[i] for i in fresh],
        list(prefix_confs[:keep]) + [window_confs[i] for i in fresh],
        list(prefix_times[:keep]) + [absolute[i] for i in fresh],
    )


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
        self._audio_ready = asyncio.Event()
        self._transcribe_stop = False
        self._matcher = None
        self._last_status: dict[int, str] = {}
        # Cumulative hypothesis (stitched from per-window transcriptions) + its
        # per-word confidences. `_last_hypothesis` is kept as an alias to the
        # cumulative words so `finalize()` and existing callers keep working.
        self._hypothesis: list[str] = []
        self._hypothesis_confs: list[float] = []
        self._hypothesis_timings: list[tuple[float, float]] = []
        self._consumed_audio_end = float("-inf")
        self._timed_evidence_seen = False
        self._pending_error_revisions: dict[int, tuple[str, int, int]] = {}
        self._pending_gap_revisions: dict[int, tuple[int, float, int, int, tuple]] = {}
        self._last_native_view = None
        self._previous_native_view = None
        self._native_word_repairs: dict[int, dict] = {}
        self._pending_native_reanchor = None
        self._pending_error_events: dict[int, tuple[str, int, int]] = {}
        self._confirmed_native_errors: set[int] = set()
        self._last_hypothesis: list[str] = []
        # Alternate-pass verification state: number of live transcription
        # passes so far and the (word, conf) list from the last unprompted
        # verification decode (reused on passes that skip it).
        self._pass_count = 0
        self._verified_words: list[tuple[str, float]] = []
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
        # Per-word tashkeel text used to build the ORACLE decode prompt for the
        # prompt-conditioned V50 ASR model. Falls back to normalized words when
        # tashkeel entries are unavailable (e.g. client-words fallback).
        self.reference_text_with_tashkeel_words: list[str] = [
            (e.get("text_with_tashkeel") or "") for e in entries
        ]
        if not self.reference_text_with_tashkeel_words or any(
            not w for w in self.reference_text_with_tashkeel_words
        ):
            self.reference_text_with_tashkeel_words = list(display or norm)

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
            self.reference_text_with_tashkeel_words = list(c_display)

        # Build the matcher + transcriber from the FINAL reference words (which
        # may be the client-words fallback), not the original (possibly empty)
        # `norm` returned by the server's own resolver.
        #
        # The ayah boundaries are handed to the matcher so its live search can be
        # clamped to the active ayah (+1). Without them the aligner could anchor
        # on a word several ayahs ahead and cascade SKIPPED marks over everything
        # in between (the "red wall" symptom).
        self._matcher = StreamingMatcher(
            self.reference_words,
            ayah_boundaries=self.ayah_boundaries,
            known_error_words=_get_live_error_vocabulary(),
            word_aliases=_get_live_word_aliases(),
        )

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
                engine = _live_asr_engine()
                if engine == "fastconformer_rnnt":
                    from ml.inference.fastconformer_transcriber import get_transcriber
                else:
                    from ml.inference.faster_whisper_transcriber import get_transcriber
                get_transcriber().load()
                self._transcriber = _real_transcriber
                self._is_stub = False
                logger.info(
                    "stream.transcriber", session_id=self.session_id,
                    engine=engine, words=len(self.reference_words),
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
        if not self._is_stub and _live_asr_engine() == "fastconformer_rnnt":
            threshold = self._next_interval_samples()
            if self._total_samples - self._samples_at_last_transcribe >= threshold:
                self._audio_ready.set()

    # Background transcription loop (driven by the WebSocket handler so the
    # receive loop never blocks on the slow Whisper call). Re-transcribes the
    # accumulated audio on a fixed cadence and emits `word` events as words
    # resolve. A single in-flight transcription is guarded by `_transcribe_lock`
    # so concurrent ticks never stack.
    def stop_transcription(self) -> "asyncio.Future":
        self._transcribe_stop = True
        self._audio_ready.set()
        return asyncio.sleep(0)  # no-op awaitable for callers

    def _is_first_pass(self) -> bool:
        """True only for the very first live pass of a session.

        Single source of truth for "is this still the early pass?", used by BOTH
        the audio threshold (maybe_transcribe) and the loop cadence. They must
        not drift: the first version lowered the threshold but left the loop
        sleeping the full 1.2 s, so the early pass never actually fired early
        and first-word latency stayed at ~2.1 s (measured). Keeping both call
        sites on this predicate is what makes the optimisation real.
        """
        return self._pass_count == 0 and not self._hypothesis

    def _next_interval_sec(self) -> float:
        """Seconds of *new* audio to accumulate before the next pass."""
        if EARLY_FIRST_PASS and self._is_first_pass():
            return EARLY_FIRST_PASS_SEC
        if not self._is_stub and _live_asr_engine() == "fastconformer_rnnt":
            if not self._matcher or getattr(self._matcher, "_cursor", 0) == 0:
                return RNNT_STARTUP_INTERVAL_SEC
            if self.sample_rate <= 0:
                return RNNT_TRANSCRIBE_INTERVAL_SEC
            # Preserve the regular audio phase after the early selected-word
            # decode. A permanent .6s cadence changed later context and produced
            # a false Yaqul error on a correctly recited Yakun.
            grid = max(1, round(RNNT_TRANSCRIBE_INTERVAL_SEC * self.sample_rate))
            used = self._samples_at_last_transcribe
            return ((used // grid + 1) * grid - used) / self.sample_rate
        return TRANSCRIBE_INTERVAL_SEC

    def _next_interval_samples(self) -> int:
        """Use one PCM threshold for waking, speech gating and decoding."""
        samples = self._next_interval_sec() * self.sample_rate
        if not self._is_stub and _live_asr_engine() == "fastconformer_rnnt":
            return max(1, round(samples))
        return int(samples)

    async def transcription_loop(self, websocket) -> None:
        if not self._is_stub and _live_asr_engine() == "fastconformer_rnnt":
            await self._audio_driven_transcription_loop(websocket)
            return
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
                #
                # The interval is EARLY-AWARE: on the first pass it is
                # EARLY_FIRST_PASS_SEC (0.5 s) instead of 1.2 s. Without this the
                # loop simply never ticked again until 1.2 s had elapsed, so
                # lowering the threshold in maybe_transcribe alone changed
                # nothing (measured: first word stayed ~2.1 s).
                elapsed = asyncio.get_event_loop().time() - t0
                remaining = self._next_interval_sec() - elapsed
                if remaining > 0:
                    await asyncio.sleep(remaining)
        except asyncio.CancelledError:
            return

    async def _audio_driven_transcription_loop(self, websocket) -> None:
        """Wake on eligible fresh PCM without adding a polling delay."""
        try:
            while not self._transcribe_stop:
                threshold = self._next_interval_samples()
                if self._total_samples - self._samples_at_last_transcribe >= threshold:
                    self._audio_ready.set()
                await self._audio_ready.wait()
                self._audio_ready.clear()
                if self._transcribe_stop:
                    break
                # Another caller may be draining a forced decode. Wait for it
                # instead of repeatedly waking on the same unconsumed samples.
                if self._transcribe_lock.locked():
                    async with self._transcribe_lock:
                        pass
                    if self._transcribe_stop:
                        break
                previous_samples = self._samples_at_last_transcribe
                try:
                    for event in await self.maybe_transcribe():
                        await websocket.send_json(event)
                except Exception as exc:  # pragma: no cover - model failures
                    logger.error("stream.loop_transcribe_failed", session_id=self.session_id, error=str(exc))
                if (self._samples_at_last_transcribe == previous_samples
                        and self._total_samples - previous_samples >= threshold):
                    # Unexpected failures before consuming PCM retain the old
                    # bounded retry cadence rather than spinning on that PCM.
                    await asyncio.sleep(max(RNNT_TRANSCRIBE_INTERVAL_SEC, self._next_interval_sec()))
        except asyncio.CancelledError:
            return

    @property
    def _total_samples(self) -> int:
        return len(self._pcm) // 2  # 16-bit samples

    @property
    def duration_seconds(self) -> float:
        return self._total_samples / self.sample_rate if self.sample_rate else 0.0

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
        # Early first pass: only pass #1 of the session, only when nothing has
        # been revealed yet, and only if the feature is enabled. After it, the
        # normal TRANSCRIBE_INTERVAL_SEC cadence resumes untouched.
        is_first_pass = self._is_first_pass()
        early = EARLY_FIRST_PASS and is_first_pass and not force
        threshold = self._next_interval_samples()
        if not force and new_samples < threshold:
            return []
        # A forced (stop-time) pass must NOT be dropped just because the
        # background loop is mid-transcription: dropping it silently discards
        # the final window's words (observed live: the last ayah never
        # resolved before `final`). Forced callers wait for the lock instead;
        # cadence callers skip to keep the reveal smooth.
        if self._transcribe_lock.locked() and not force:
            return []

        async with self._transcribe_lock:
            self._samples_at_last_transcribe = self._total_samples
            total = self._total_samples

            if self._is_stub:
                # Stub reveals words from the TOTAL duration → needs full buffer.
                audio = self._decode_float()
                try:
                    words, confs = await asyncio.to_thread(
                        _invoke_transcriber, self._transcriber, audio,
                        self.sample_rate,
                        " ".join(self.reference_text_with_tashkeel_words),
                    )
                except Exception as exc:  # pragma: no cover - model failures
                    self._pending_error_revisions.clear()
                    self._pending_gap_revisions.clear()
                    self._last_native_view = None
                    self._previous_native_view = None
                    self._pending_native_reanchor = None
                    self._pending_error_events.clear()
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
                # On the early first pass a SHORTER window is used so the decode
                # itself is cheaper; it applies to that one pass only.
                window_sec = (
                    EARLY_FIRST_PASS_WINDOW_S if early else TRANSCRIBE_WINDOW_SEC
                )
                overlap_sec = 0.0 if early else TRANSCRIBE_WINDOW_OVERLAP_SEC
                window_samples = int(
                    (window_sec + overlap_sec) * self.sample_rate
                )
                start = self._select_audio_window_start(
                    total, max(0, total - window_samples), early=early, force=force,
                )
                audio = self._decode_float(start_sample=start)
                # Silence gate: if this window is essentially quiet (the user is
                # not reciting), Whisper would still hallucinate phantom Arabic
                # words that "complete" the ayah on their own. Skip transcription
                # and emit NO events so nothing resolves until there is real
                # speech. Do NOT advance `_samples_at_last_transcribe` so the next
                # pass that does contain speech still re-scans this quiet span.
                # NOTE: _rms_energy is a MODULE-LEVEL function (not a method).
                # A previous `self._rms_energy(audio)` typo raised
                # AttributeError on EVERY live pass — the transcription loop
                # swallowed it and no `word` event ever reached the client
                # (the summary-only symptom).
                if _rms_energy(audio) < SILENCE_RMS_THRESHOLD:
                    return []
                # ORACLE prompt — must stay in the model's TRAINING condition:
                # V50 was trained on PER-AYAH prompts (prompt = text of the SAME
                # ayah as the speech). Cross-ayah or past-word prompts make the
                # model echo the prompt instead of transcribing (verified), and
                # full-page prompts break its alignment. So: prompt = the
                # remaining words of the ayah that contains the matcher cursor.
                # Echo risk exists only when the user recites something OTHER
                # than the on-screen reference — the trust-first matcher gate
                # bounds that, and the final review re-scores honestly.
                cursor = getattr(self._matcher, "_cursor", 0) or 0
                ayah_start, ayah_end = 0, len(self.reference_text_with_tashkeel_words) - 1
                for b in getattr(self, "ayah_boundaries", None) or []:
                    end = int(b.get("word_index_end", -1))
                    if end >= cursor:
                        ayah_start = max(0, end + 1 - int(b.get("word_count", 0)))
                        ayah_end = end
                        break
                # ANCHORED prompt: only words BEFORE the matcher cursor, capped to
                # a short span, and framed inside the current ayah. A prompt that
                # included the *upcoming* words made the model ECHO them instead
                # of transcribing: every echoed word was already resolved, so
                # stitching deduped it, the hypothesis stopped growing and the
                # live reveal FROZE for the rest of the ayah (verified: cursor
                # pinned at the ayah-6 -> 7 boundary for ~22s until the final
                # window cleared it). With no future text in the prompt the model
                # can only report what it actually hears, so the reveal tracks the
                # recitation (verified honest across the anchor matrix).
                # NOTE: tried anchoring the prompt on already-resolved words only
                # (no future text) to remove echo risk entirely — measured 3/29
                # live words vs 20/29 with the per-ayah prompt, so the model
                # really does need the current ayah's text (its training
                # condition) and the remaining-words prompt stays. Echo risk is
                # instead bounded by the corroboration filter + watchdog below.
                remaining = self.reference_text_with_tashkeel_words[
                    max(cursor, ayah_start):ayah_end + 1
                ]
                prompt = " ".join(remaining[:PROMPT_ANCHOR_WORDS])
                # --- Two-tier decode (V51-kernel style) ---------------------
                # Tier 1 (PROMPTED) is the model's training condition and
                # accurate when the audio matches the expectation, but an
                # oracle prompt is not an independent witness: on mismatched
                # audio the model ECHOES the prompt and would highlight words
                # the user has not recited yet (verified: ayah-5 words fired
                # while only ayah-3 audio had been streamed).
                # Tier 2 (UNPROMPTED) is echo-immune evidence of the actual
                # speech; a tier-1 word is accepted only when corroborated.
                # Decodes run CONCURRENTLY (2 threads each, see
                # QARI_FASTERWHISPER_THREADS) — wall time is ~max(tier1, tier2)
                # instead of the sum (measured 1.9s vs 4.2s). The unprompted
                # verification decode additionally runs only every
                # VERIFY_EVERY_N_PASSES passes: windows overlap heavily so its
                # token set stays valid, and skipping it on alternate passes
                # cuts the average pass cost further (lower reveal latency).
                stall = int(getattr(self._matcher, "_stall_passes", 0) or 0) >= 1
                self._pass_count += 1
                refresh_verify = (
                    not self._verified_words
                    or VERIFY_EVERY_N_PASSES <= 1
                    or self._pass_count % VERIFY_EVERY_N_PASSES == 0
                    or stall
                )
                window_timings = None
                try:
                    if EVIDENCE_POLICY == "tier2":
                        # The independent witness IS the live hypothesis (see
                        # EVIDENCE_POLICY), so the prompted decode is not needed
                        # at all: one decode instead of two halves CPU use and
                        # drops the pass wall time (~1.1s vs ~1.9s measured on
                        # this VPS), which is the live reveal latency.
                        decoded = await asyncio.to_thread(
                            _independent_transcriber, audio, self.sample_rate
                        )
                        win_words, win_confs = decoded
                        window_timings = getattr(decoded, "timings", None)
                        raw_words, raw_confs = list(win_words), list(win_confs)
                        self._verified_words = [
                            (w, c) for w, c in zip(raw_words, raw_confs) if w
                        ]
                    elif refresh_verify:
                        # tier-2 = INDEPENDENT model, unprompted (honest witness).
                        # NOT the V50 oracle with an empty prompt: that model
                        # only reproduces text it was prompted with and is
                        # useless as evidence.
                        (win_words, win_confs), (raw_words, raw_confs) = await asyncio.gather(
                            asyncio.to_thread(
                                _invoke_transcriber, self._transcriber, audio,
                                self.sample_rate, prompt,
                            ),
                            asyncio.to_thread(
                                _independent_transcriber, audio, self.sample_rate
                            ),
                        )
                        self._verified_words = [
                            (w, c) for w, c in zip(raw_words, raw_confs) if w
                        ]
                    else:
                        win_words, win_confs = await asyncio.to_thread(
                            _invoke_transcriber, self._transcriber, audio,
                            self.sample_rate, prompt,
                        )
                        raw_words = [w for w, _ in self._verified_words]
                        raw_confs = [c for _, c in self._verified_words]
                except Exception as exc:  # pragma: no cover - model failures
                    self._pending_error_revisions.clear()
                    self._pending_gap_revisions.clear()
                    self._last_native_view = None
                    self._previous_native_view = None
                    self._pending_native_reanchor = None
                    self._pending_error_events.clear()
                    logger.error(
                        "stream.transcribe_failed",
                        session_id=self.session_id, error=str(exc),
                    )
                    return []

                raw_norm_list = [_normalize(w) for w in raw_words if w]
                raw_norm_set = set(raw_norm_list)
                if STREAM_DEBUG:
                    logger.info(
                        "stream.pass_debug",
                        session_id=self.session_id,
                        force=force,
                        dur=round(self.duration_seconds, 1),
                        cursor_before=int(getattr(self._matcher, "_cursor", 0) or 0),
                        stall=stall,
                        tier1=" ".join(w for w in win_words if w)[:120],
                        tier2=" ".join(w for w in raw_words if w)[:120],
                        hyp=" ".join(self._hypothesis[-20:]),
                        dp=getattr(self._matcher, "_last_dp_debug", None),
                    )
                ref_norm_set = set(self.reference_words)
                # NOTE (removed): a "watchdog" used to disable this filter after
                # a few stalled passes, on the theory that tier-2 had gone
                # garbage while tier-1 was correct. With the ORACLE (V50) model
                # that bypass was the exact bug users see — it accepts text the
                # model ECHOED from the prompt, so a recitation is reported
                # correct no matter what was actually said. tier-2 is now the
                # independent base model (see _independent_transcriber), so the
                # corroboration requirement is kept unconditionally: no evidence
                # heard by the independent decode -> no match.
                def _corroborated(token: str) -> bool:
                    n = _normalize(token)
                    if not n:
                        return False
                    if n in raw_norm_set:
                        return True
                    # Different tokenization of the same word (article split /
                    # merged): a >=4-char word embedded in a longer raw token.
                    if len(n) >= 4 and any(n in r for r in raw_norm_list):
                        return True
                    # Tier-2 sometimes mangles a single word of an otherwise
                    # correct span — accept near-identical tokens.
                    import difflib

                    return any(
                        difflib.SequenceMatcher(None, n, r).ratio() >= 0.6
                        for r in raw_norm_list
                    )

                verified = [
                    (w, c) for w, c in zip(win_words, win_confs)
                    if _corroborated(w)
                ]
                if EVIDENCE_POLICY == "tier2":
                    win_words = list(raw_words)
                    win_confs = list(raw_confs)
                elif verified:
                    win_words = [w for w, _ in verified]
                    win_confs = [c for _, c in verified]
                elif raw_words:
                    # The prompted decode produced nothing OR was filtered out
                    # (a prompt ECHO). Either way the INDEPENDENT decode is the
                    # evidence of what was actually spoken, so use it. This case
                    # MUST cover the empty-tier-1 window: previously the fallback
                    # required a non-empty tier-1, so on windows where the oracle
                    # emitted no words the independent words were thrown away,
                    # the cumulative hypothesis stopped growing and the reveal
                    # FROZE for the rest of the surah (observed live from ayah 4
                    # onward, ~20 of 29 words).
                    logger.debug(
                        "stream.independent_fallback",
                        session_id=self.session_id,
                        tier1=len(win_words),
                        tier2=len(raw_words),
                    )
                    win_words = list(raw_words)
                    win_confs = list(raw_confs)
                else:
                    # Nothing independent was heard on this window: emit NO
                    # words rather than the oracle's echo (the honesty fix).
                    logger.debug(
                        "stream.echo_uncorroborated",
                        session_id=self.session_id,
                        tier1=len(win_words),
                    )
                    win_words = []
                    win_confs = []
                if window_timings is not None:
                    self._timed_evidence_seen = True
                if self._timed_evidence_seen:
                    if not win_words:
                        # Model failure/empty recognition supplies no revision.
                        # Preserve the last good word/time pairs for recovery.
                        self._pending_error_revisions.clear()
                        self._pending_gap_revisions.clear()
                        self._last_native_view = None
                        self._previous_native_view = None
                        self._pending_native_reanchor = None
                        self._pending_error_events.clear()
                        return []
                    if window_timings is None:
                        self._pending_error_revisions.clear()
                        self._pending_gap_revisions.clear()
                        self._last_native_view = None
                        self._previous_native_view = None
                        self._pending_native_reanchor = None
                        self._pending_error_events.clear()
                        logger.error("stream.transcribe_failed", session_id=self.session_id,
                                     error="Timed recognition lost emission metadata")
                        return []
                # STALL UNION: when the reference cursor did not advance during
                # the previous pass, the prompted decode is ECHOING the oracle
                # prompt. Every echoed word was already resolved earlier, so
                # stitching them adds nothing and the reveal FREEZES forever
                # (verified live: cursor pinned at the ayah-6 -> 7 boundary
                # while the user kept reciting). The unprompted decode is
                # echo-immune, so on stalled passes union its tokens into the
                # window output — the matcher then sees the words actually
                # spoken and walks forward again. Only used while stalled, so
                # normal passes keep the accurate prompted-only alignment.
                if stall and raw_words and EVIDENCE_POLICY != "tier2":
                    win_words = list(win_words) + list(raw_words)
                    win_confs = list(win_confs) + list(raw_confs)
                # STALL TAIL RESET: the matcher consumed the stalled tokens as
                # noise, so the tail past its cursor is spent. Worse, if those
                # tokens were prompt-echo they now sit in the hypothesis and
                # stitch_hypothesis() DEDUPS the genuinely-spoken words when the
                # user actually reaches them (seen live: the real ayah-7 words
                # were dropped as "already contributed" and the reveal never
                # moved again). Dropping the spent tail loses nothing and lets
                # fresh evidence append cleanly.
                if stall and self._hypothesis:
                    keep = max(
                        0, int(getattr(self._matcher, "_hyp_cursor", 0) or 0)
                    )
                    self._hypothesis = self._hypothesis[:keep]
                    self._hypothesis_confs = self._hypothesis_confs[:keep]
                    self._hypothesis_timings = self._hypothesis_timings[:keep]
                if window_timings is not None:
                    try:
                        stitched, stitched_confs, stitched_times = _stitch_timed_hypothesis(
                            self._hypothesis, self._hypothesis_confs,
                            self._hypothesis_timings, win_words, win_confs,
                            window_timings,
                            consumed=getattr(self._matcher, "_hyp_cursor", 0),
                            consumed_end=self._consumed_audio_end,
                            window_start=start / self.sample_rate,
                            window_seconds=len(audio) / self.sample_rate,
                            confidence_threshold=getattr(self._matcher, "live_confidence_threshold", .55),
                            right_context_seconds=0.0 if force else LIVE_RIGHT_CONTEXT_SEC,
                        )
                        self._revise_supported_timed_gaps(
                            win_words, win_confs, window_timings,
                            window_start=start / self.sample_rate,
                            window_seconds=len(audio) / self.sample_rate,
                            right_context_seconds=0.0 if force else LIVE_RIGHT_CONTEXT_SEC,
                            endpoint_samples=start + len(audio),
                        )
                        self._revise_supported_timed_errors(
                            win_words, win_confs, window_timings,
                            window_start=start / self.sample_rate,
                            window_seconds=len(audio) / self.sample_rate,
                            right_context_seconds=0.0 if force else LIVE_RIGHT_CONTEXT_SEC,
                            endpoint_samples=start + len(audio),
                        )
                        native_view = (
                            start, start + len(audio), tuple(win_words),
                            tuple(win_confs), tuple(window_timings),
                        )
                        self._repair_anchored_native_words(native_view)
                        self._previous_native_view = self._last_native_view
                        self._last_native_view = native_view
                        # Stitching validated the complete native window first.
                        # Copy only proven corrections into its retained prefix;
                        # fresh tokens, cursors and the consumed boundary stay put.
                        retained = min(getattr(self._matcher, "_hyp_cursor", 0), len(self._hypothesis))
                        stitched[:retained] = self._hypothesis[:retained]
                        stitched_confs[:retained] = self._hypothesis_confs[:retained]
                        stitched_times[:retained] = self._hypothesis_timings[:retained]
                    except (ValueError, TypeError) as exc:
                        self._pending_error_revisions.clear()
                        self._pending_gap_revisions.clear()
                        self._last_native_view = None
                        self._previous_native_view = None
                        self._pending_native_reanchor = None
                        self._pending_error_events.clear()
                        logger.error("stream.transcribe_failed", session_id=self.session_id, error=str(exc))
                        return []
                else:
                    stitched, stitched_confs = stitch_hypothesis(
                        self._hypothesis, self._hypothesis_confs, win_words, win_confs,
                    )
                    stitched_times = []
                # Clamp the cumulative hypothesis so ASR hallucinations /
                # repeated-token explosions can't grow it without bound. The
                # cap must be measured from the matcher's CONSUMED prefix
                # (`_hyp_cursor`), not from the reference length: an absolute
                # cap truncated the TAIL — exactly where the newly transcribed
                # words land — so once a repetition/echo burst filled the
                # budget, every later pass had its real words cut off and the
                # matcher pinned at the cap forever (verified live: cursor
                # frozen while the hypothesis sat at ref_len + lookahead).
                # Keeping `pref + HYPO_TAIL_CAP` words preserves index
                # alignment for the consumed region and lets the matcher walk
                # forward through new tokens as they arrive.
                pref = max(0, int(getattr(self._matcher, "_hyp_cursor", 0) or 0))
                cap = min(
                    len(stitched),
                    pref + HYPO_TAIL_CAP,
                )
                if len(stitched) > cap:
                    stitched = stitched[:cap]
                    stitched_confs = stitched_confs[:cap]
                self._hypothesis = stitched
                self._hypothesis_confs = stitched_confs
                self._hypothesis_timings = stitched_times[:cap]

            self._last_hypothesis = self._hypothesis
            _cursor_before = int(getattr(self._matcher, "_cursor", 0) or 0)
            states = self._matcher.evaluate(
                self._hypothesis, self._hypothesis_confs
            )
            if int(getattr(self._matcher, '_cursor', 0)) == _cursor_before:
                if self._recover_supported_native_anchor(force=force):
                    states = list(self._matcher._states)
            else:
                self._pending_native_reanchor = None
            consumed = int(getattr(self._matcher, "_hyp_cursor", 0))
            if 0 < consumed <= len(self._hypothesis_timings):
                self._consumed_audio_end = max(
                    self._consumed_audio_end, self._hypothesis_timings[consumed - 1][1],
                )
            if STREAM_DEBUG:
                logger.info(
                    "stream.pass",
                    session_id=self.session_id,
                    cursor_before=_cursor_before,
                    cursor_after=int(getattr(self._matcher, "_cursor", 0) or 0),
                    stall=int(getattr(self._matcher, "_stall_passes", 0) or 0),
                    hyp=len(self._hypothesis),
                )
            if self._last_native_view is not None:
                self._confirm_timed_error_events(right_context_seconds=0.0 if force else LIVE_RIGHT_CONTEXT_SEC)
            return self._diff_events(states)

    def _recover_supported_native_anchor(self, *, force=False):
        """Two fresh, unique timed word pairs may recover inside bounded reach."""
        from ml.alignment.streaming_matcher import LIVE_SEARCH_REACH_WIDE, LIVE_LOW_CONF_STREAK
        view = self._last_native_view
        recover = getattr(self._matcher, 'recover_native_anchor', None)
        d = getattr(self._matcher, '_delegate', None)
        if (view is None or recover is None or d is None
                or _live_asr_engine() != 'fastconformer_rnnt'
                or d._cursor <= 0 or d._stall_passes < LIVE_LOW_CONF_STREAK):
            self._pending_native_reanchor = None
            return False
        start, endpoint, words, scores, times = view
        threshold, tolerance = d.live_confidence_threshold, .08 + 1e-6
        identity = lambda word: d._word_aliases.get(word, word)
        ceiling = min(len(d.reference), int(self._matcher.max_live_words),
            d._cursor + LIVE_SEARCH_REACH_WIDE, d._ayah_ceiling(d._cursor, len(d.reference)))
        absolute = [(a + start / self.sample_rate, b + start / self.sample_rate) for a,b in times]
        candidates = []
        for i in range(len(words) - 1):
            a,b = absolute[i]; c,e = absolute[i + 1]
            pair = tuple(identity(w) for w in words[i:i+2])
            if (min(scores[i:i+2]) < threshold or pair[0] == pair[1]
                    or a <= self._consumed_audio_end + tolerance or c - a < .16 - 1e-6
                    or b > c + tolerance
                    or e + .08 > endpoint / self.sample_rate - (0. if force else LIVE_RIGHT_CONTEXT_SEC)
                    or any(j not in (i,i+1) and scores[j] >= threshold
                           and (abs(span[0]-a) <= tolerance or abs(span[0]-c) <= tolerance)
                           for j,span in enumerate(absolute))):
                continue
            # A growing last-word span must not recycle consumed speech as a
            # new anchor. Apply the existing native revision drift exclusion to
            # either same-identity consumed occurrence, including zero spans.
            if any(identity(self._hypothesis[j]) == pair[k]
                   and max(self._hypothesis_timings[j][0], absolute[i+k][0])
                       <= min(self._hypothesis_timings[j][1] + .24 + 1e-6,
                              absolute[i+k][1] + .24 + 1e-6)
                   for j in range(min(d._hyp_cursor,len(self._hypothesis_timings)))
                   for k in (0,1)):
                continue
            # Include the current position when establishing uniqueness, even
            # though only a later pair can recover a recognition gap.
            for index in range(d._cursor, ceiling - 1):
                if pair != tuple(identity(w) for w in d.reference[index:index+2]):
                    continue
                for slot in range(d._hyp_cursor, min(len(self._hypothesis),len(self._hypothesis_timings)) - 1):
                    if (tuple(identity(w) for w in self._hypothesis[slot:slot+2]) == pair
                            and min(self._hypothesis_confs[slot:slot+2]) >= threshold
                            and abs(self._hypothesis_timings[slot][0]-a) <= tolerance
                            and abs(self._hypothesis_timings[slot+1][0]-c) <= tolerance):
                        candidates.append((index,slot,pair,a,c))
        if len(candidates) != 1 or candidates[0][0] == d._cursor:
            self._pending_native_reanchor = None
            return False
        index,slot,pair,a,c = candidates[0]
        previous = getattr(self, '_pending_native_reanchor', None)
        count = 1
        if (previous and previous[:3] == (d._cursor,index,pair)
                and abs(a-previous[3]) <= tolerance and abs(c-previous[4]) <= tolerance):
            if endpoint <= previous[5]:
                return False
            count = previous[6] + 1
        self._pending_native_reanchor = (d._cursor,index,pair,a,c,endpoint,count)
        if count >= 2 and recover(index,slot,self._hypothesis,self._hypothesis_confs):
            self._pending_native_reanchor = None
            return True
        return False

    def _select_audio_window_start(self, total, default_start, *, early, force):
        """Recover recent native uncertainty with at most 21 seconds of context."""
        import math
        if early or settings.ml_use_stub or self._explicit_transcriber is not None or _live_asr_engine() != "fastconformer_rnnt":
            return default_start
        # RNNT emissions advance by 80ms. A one-second recovery grid flips
        # the encoder origin by half a frame on alternate seconds, changing
        # decoded endings and making same-audio timing witnesses disagree.
        # Use the recording's original encoder phase for ordinary views too.
        grid = max(1, round(.08 * self.sample_rate))
        default_start = (default_start // grid) * grid
        remembered = getattr(self, '_recent_native_uncertainty_begin', None)
        recover = force or (
            remembered is not None
            and max(0., total / self.sample_rate - 20.) <= remembered <= total / self.sample_rate
        )
        delegate = getattr(self._matcher, "_delegate", self._matcher)
        slots = getattr(delegate, "_live_hyp_indices", {})
        for state in getattr(delegate, "_resolved_states", []):
            if state.status.value not in {"error", "skipped"}:
                continue
            slot = slots.get(state.index, slots.get(state.index - 1))
            if slot is not None and 0 <= slot < len(self._hypothesis_timings):
                begin = self._hypothesis_timings[slot][0]
                if math.isfinite(begin) and max(0., total / self.sample_rate - 20.) <= begin <= total / self.sample_rate:
                    recover = True
                    # A supported substitution may have a corrected prefix;
                    # retain that context across its revision. Missing-token
                    # gaps use ordinary windows again after they are repaired.
                    if state.status.value == 'error':
                        self._recent_native_uncertainty_begin = begin
        if not recover:
            return default_start
        # A stable absolute PCM grid avoids moving the recognizer's frontend
        # frame origin with every irregular packet. No reference text is used.
        nominal = max(0, total - 20 * self.sample_rate)
        return (nominal // grid) * grid

    def _confirm_timed_error_events(self, *, right_context_seconds=LIVE_RIGHT_CONTEXT_SEC):
        """Require two native audio views before surfacing a supported error."""
        import math
        from ml.alignment.streaming_matcher import WordStatus
        view = self._last_native_view
        if view is None:
            self._pending_error_events.clear()
            return
        start, endpoint, words, scores, times = view
        delegate = getattr(self._matcher, "_delegate", self._matcher)
        slots = getattr(delegate, "_live_hyp_indices", {})
        threshold = getattr(delegate, "live_confidence_threshold", .55)
        tolerance = .08 + 1e-6
        eligible = set()
        for state in getattr(delegate, "_resolved_states", []):
            slot = slots.get(state.index)
            if (state.status != WordStatus.ERROR or not state.spoken or slot is None
                    or not 0 <= slot < len(self._hypothesis_timings)
                    or not math.isfinite(state.confidence) or state.confidence < threshold):
                continue
            old_begin, old_end = self._hypothesis_timings[slot]
            candidates=[]
            for i,(word,score,(begin,end)) in enumerate(zip(words,scores,times)):
                begin += start/self.sample_rate
                end += start/self.sample_rate
                if (word == state.spoken and math.isfinite(score) and threshold <= score <= 1
                        and abs(begin-old_begin) <= tolerance
                        and max(begin,old_begin) <= min(end+.08,old_end+.08)
                        and end + .08 <= endpoint/self.sample_rate-right_context_seconds+1e-6
                        and not any(j!=i and scores[j]>=threshold and abs(times[j][0]+start/self.sample_rate-begin)<=tolerance for j in range(len(words)))):
                    candidates.append(i)
            if len(candidates)!=1:
                continue
            eligible.add(state.index)
            previous=self._pending_error_events.get(state.index)
            if previous and endpoint<=previous[1]:
                continue
            count=previous[2]+1 if previous and previous[0]==state.spoken else 1
            self._pending_error_events[state.index]=(state.spoken,endpoint,count)
            if count>=2:
                self._confirmed_native_errors.add(state.index)
        for index in set(self._pending_error_events)-eligible:
            self._pending_error_events.pop(index,None)

    def _repair_anchored_native_words(self, current) -> None:
        """Confirm mature native evidence between two already tracked neighbors."""
        from ml.alignment.native_evidence import prove_native_word_repair
        from ml.alignment.streaming_matcher import WordStatus
        import math

        delegate = getattr(self._matcher, '_delegate', self._matcher)
        repair = getattr(self._matcher, 'repair_native_word', None)
        if (repair is None or self._last_native_view is None or self._is_stub
                or EVIDENCE_POLICY != 'tier2' or _live_asr_engine() != 'fastconformer_rnnt'):
            return
        states = {state.index: state for state in getattr(delegate, '_resolved_states', [])}
        slots = getattr(delegate, '_live_hyp_indices', {})
        threshold = getattr(delegate, 'live_confidence_threshold', .55)
        identity = lambda word: delegate._word_aliases.get(word, word)
        for index, state in states.items():
            before, after = states.get(index - 1), states.get(index + 1)
            left, right = slots.get(index - 1), slots.get(index + 1)
            if (state.status not in (WordStatus.SKIPPED, WordStatus.ERROR)
                    or before is None or after is None
                    or before.status != WordStatus.MATCHED or after.status != WordStatus.MATCHED
                    or any(not anchor.spoken or not math.isfinite(anchor.confidence)
                           or not threshold <= anchor.confidence <= 1 for anchor in (before, after))
                    or left is None or right is None or not 0 <= left < right
                    or right >= getattr(self._matcher, '_hyp_cursor', 0)
                    or right >= min(len(self._hypothesis), len(self._hypothesis_timings))
                    or self._hypothesis[left] != before.spoken or self._hypothesis[right] != after.spoken):
                continue
            evidence = prove_native_word_repair(
                self._last_native_view, current,
                expected=(before.expected, state.expected, after.expected),
                before_span=self._hypothesis_timings[left], after_span=self._hypothesis_timings[right],
                identity=identity, threshold=threshold, sample_rate=self.sample_rate,
                total_samples=self._total_samples, right_context_seconds=LIVE_RIGHT_CONTEXT_SEC,
            )
            if evidence:
                begin, end = evidence['spans'][1]
                # Native audio already assigned to another confirmed word is
                # unavailable, including earlier repairs without an old slot.
                used = []
                for other_index, other in states.items():
                    if other_index in (index - 1, index, index + 1) or other.status != WordStatus.MATCHED:
                        continue
                    other_slot = slots.get(other_index)
                    if other_slot is not None and 0 <= other_slot < len(self._hypothesis_timings):
                        used.append(self._hypothesis_timings[other_slot])
                    prior = self._native_word_repairs.get(other_index)
                    if prior:
                        used.append(prior['spans'][1])
                if any(max(begin, a) <= min(end + .08, b + .08) + 1e-5 for a, b in used):
                    continue
            if evidence and repair(index, evidence['word'], evidence['confidence']):
                self._native_word_repairs[index] = evidence
                logger.info('stream.native_word_repaired', word_index=index,
                            confidence=round(evidence['confidence'], 3), endpoints=evidence['endpoints'])

    def _revise_supported_timed_errors(
        self, window_words, window_confs, window_times, *, window_start,
        window_seconds, right_context_seconds, endpoint_samples,
    ) -> None:
        """Two native views may correct a supported error in the same PCM span."""
        import math
        from ml.alignment.streaming_matcher import WordStatus

        delegate = getattr(self._matcher, "_delegate", self._matcher)
        slots = getattr(delegate, "_live_hyp_indices", {})
        states = {s.index: s for s in getattr(delegate, "_resolved_states", [])}
        threshold = getattr(delegate, "live_confidence_threshold", .55)
        consumed = getattr(self._matcher, "_hyp_cursor", 0)
        tolerance = .08 + 1e-6
        try:
            if (self.sample_rate <= 0 or not 0 < endpoint_samples <= self._total_samples
                    or not all(math.isfinite(v) for v in (window_start, window_seconds))
                    or window_start < 0 or window_seconds <= 0
                    or abs(window_start + window_seconds - endpoint_samples / self.sample_rate) > 1e-6
                    or not len(window_words) == len(window_confs) == len(window_times)):
                raise ValueError("Incomplete native revision view")
            absolute = []
            previous = -1.0
            for word, score, (begin, end) in zip(window_words, window_confs, window_times):
                if (not isinstance(word, str) or not word
                        or not all(math.isfinite(v) for v in (score, begin, end))
                        or not 0 <= score <= 1
                        or not 0 <= begin <= end <= window_seconds + .08
                        or begin < previous):
                    raise ValueError("Invalid native revision view")
                previous = begin
                absolute.append((begin + window_start, end + window_start))
        except (ValueError, TypeError):
            self._pending_error_revisions.clear()
            self._pending_gap_revisions.clear()
            self._last_native_view = None
            self._previous_native_view = None
            self._pending_native_reanchor = None
            self._pending_error_events.clear()
            return

        def bounded_prefix_span(index, i, slot, old_begin, old_end, anchor_begin):
            # A one-token error may omit a prefix: its sole emission then lies
            # INSIDE the corrected multi-token word, not at its first frame.
            # Identify that same occurrence using BOTH already matched neighbors.
            # Retain the .08s frame tolerance; compensate only the common frame
            # origin measured from the left neighbor, never an arbitrary drift.
            left = states.get(index - 1)
            left_slot = slots.get(index - 1)
            if (i < 1 or abs(old_end - old_begin) > 1e-6
                    or left is None or left.status != WordStatus.MATCHED
                    or not left.spoken or not math.isfinite(left.confidence)
                    or left.confidence < threshold or left_slot != slot - 1
                    or not 0 <= left_slot < len(self._hypothesis_timings)
                    or self._hypothesis[left_slot] != left.spoken
                    or window_confs[i - 1] < threshold
                    or _normalize(window_words[i - 1]) != _normalize(left.spoken)
                    or _normalize(window_words[i + 1]) != _normalize(states[index + 1].spoken)
                    or len({_normalize(window_words[j]) for j in (i - 1, i, i + 1)}) != 3):
                return False
            left_begin, left_end = self._hypothesis_timings[left_slot]
            new_left_begin, new_left_end = absolute[i - 1]
            begin, end = absolute[i]
            next_begin, _ = absolute[i + 1]
            shift = new_left_begin - left_begin
            if (not all(math.isfinite(v) for v in (left_begin, left_end))
                    or not window_start <= left_begin <= left_end
                    or left_end + .08 > old_begin + 1e-6
                    or abs(shift) > tolerance
                    # Subtracting two float32 emission bounds accumulates a few
                    # microseconds of rounding at long recording offsets.
                    or abs(new_left_end - shift - left_end) > .08 + 1e-5
                    or abs(next_begin - shift - anchor_begin) > tolerance
                    or end - begin < .16 - 1e-6
                    or not begin - shift <= old_begin <= end - shift
                    or new_left_end + .08 > begin + 1e-6
                    or end + .08 > next_begin + 1e-6):
                return False
            return not any(
                j not in (i - 1, i, i + 1) and window_confs[j] >= threshold
                and any(abs(bounds[0] - absolute[k][0]) <= tolerance
                        for k in (i - 1, i, i + 1))
                for j, bounds in enumerate(absolute)
            )

        eligible = set()
        for index, state in states.items():
            anchor = states.get(index + 1)
            slot, following = slots.get(index), slots.get(index + 1)
            if (state.status != WordStatus.ERROR or not state.spoken
                    or not math.isfinite(state.confidence) or not threshold <= state.confidence <= 1
                    or anchor is None or anchor.status != WordStatus.MATCHED
                    or not anchor.spoken or anchor.confidence < threshold
                    or slot is None or following != slot + 1
                    or not 0 <= slot < following < consumed
                    or following >= min(len(self._hypothesis), len(self._hypothesis_confs), len(self._hypothesis_timings))):
                continue
            old_begin, old_end = self._hypothesis_timings[slot]
            anchor_begin, anchor_end = self._hypothesis_timings[following]
            if (not all(math.isfinite(v) for v in (old_begin, old_end, anchor_begin, anchor_end))
                    or not window_start <= old_begin <= old_end <= self._consumed_audio_end + tolerance
                    or not old_begin + .08 <= anchor_begin + 1e-6
                    or self._hypothesis[slot] != state.spoken
                    or self._hypothesis[following] != anchor.spoken):
                continue
            candidates = []
            for i in range(len(window_words) - 1):
                begin, end = absolute[i]
                next_begin, next_end = absolute[i + 1]
                if (window_confs[i] < threshold or window_confs[i + 1] < threshold
                        or not delegate._is_match(window_words[i], state.expected)
                        or not delegate._is_match(window_words[i + 1], anchor.expected)
                        or begin + .08 > next_begin + 1e-6
                        or end > next_begin + tolerance
                        or (right_context_seconds > 0
                            and max(end, next_end) + .08 > window_start + window_seconds - right_context_seconds)):
                    continue
                same_first_frame = (
                    abs(begin - old_begin) <= tolerance
                    and abs(next_begin - anchor_begin) <= tolerance
                    and max(begin, old_begin) <= min(end + .08, old_end + .08)
                )
                if not same_first_frame and not bounded_prefix_span(
                        index, i, slot, old_begin, old_end, anchor_begin):
                    continue
                # A second strong word on either identifying emission frame
                # makes the audio occurrence ambiguous, even if its text agrees.
                if any(j not in (i, i + 1) and window_confs[j] >= threshold
                       and (abs(bounds[0] - begin) <= tolerance
                            or abs(bounds[0] - next_begin) <= tolerance)
                       for j, bounds in enumerate(absolute)):
                    continue
                candidates.append(i)
            if len(candidates) != 1:
                continue
            i = candidates[0]
            eligible.add(index)
            word = window_words[i]
            previous = self._pending_error_revisions.get(index)
            count = 1
            if previous and previous[0] == word:
                if endpoint_samples <= previous[1]:
                    continue
                count = previous[2] + 1
            self._pending_error_revisions[index] = (word, endpoint_samples, count)
            if count >= 2 and self._matcher.revise_live_error(index, word, window_confs[i]):
                self._hypothesis[slot] = word
                self._hypothesis_confs[slot] = window_confs[i]
                self._hypothesis_timings[slot] = absolute[i]
                self._pending_error_revisions.pop(index, None)
        for index in set(self._pending_error_revisions) - eligible:
            self._pending_error_revisions.pop(index, None)

    def _revise_supported_timed_gaps(
        self, window_words, window_confs, window_times, *, window_start,
        window_seconds, right_context_seconds, endpoint_samples,
    ) -> None:
        """Repair one existing native-token gap using two independently decoded views."""
        import math
        from ml.alignment.streaming_matcher import WordStatus
        delegate = getattr(self._matcher, "_delegate", self._matcher)
        slots = getattr(delegate, "_live_hyp_indices", {})
        states = {x.index: x for x in getattr(delegate, "_resolved_states", [])}
        threshold = getattr(delegate, "live_confidence_threshold", .55)
        tolerance = .08 + 1e-6
        drift = .24 + 1e-6
        try:
            if (self.sample_rate <= 0 or not 0 < endpoint_samples <= self._total_samples
                    or not all(math.isfinite(v) for v in (window_start, window_seconds))
                    or window_start < 0 or window_seconds <= 0
                    or abs(window_start + window_seconds - endpoint_samples / self.sample_rate) > 1e-6
                    or not len(window_words) == len(window_confs) == len(window_times)):
                raise ValueError("Incomplete native gap view")
            absolute = []
            previous = -1.
            for word, score, (begin, end) in zip(window_words, window_confs, window_times):
                if (not isinstance(word, str) or not word
                        or not all(math.isfinite(v) for v in (score, begin, end))
                        or not 0 <= score <= 1 or not 0 <= begin <= end <= window_seconds + .08
                        or begin < previous):
                    raise ValueError("Invalid native gap view")
                previous = begin
                absolute.append((begin + window_start, end + window_start))
        except (ValueError, TypeError):
            self._pending_gap_revisions.clear()
            self._last_native_view = None
            self._previous_native_view = None
            self._pending_native_reanchor = None
            self._pending_error_events.clear()
            return
        eligible = set()
        for index, state in states.items():
            before, after = states.get(index - 1), states.get(index + 1)
            left, right = slots.get(index - 1), slots.get(index + 1)
            if (state.status != WordStatus.SKIPPED or state.spoken or state.confidence != 0
                    or index in slots or before is None or after is None
                    or before.status != WordStatus.MATCHED or after.status != WordStatus.MATCHED
                    or any(not x.spoken or not math.isfinite(x.confidence) or not threshold <= x.confidence <= 1 for x in (before, after))
                    or left is None or right != left + 2
                    or not 0 <= left < right < getattr(self._matcher, "_hyp_cursor", 0)
                    or right >= min(len(self._hypothesis), len(self._hypothesis_confs), len(self._hypothesis_timings))):
                continue
            slot = left + 1
            if slot in slots.values() or not self._hypothesis[slot]:
                continue
            old = self._hypothesis_timings[left:right + 1]
            if (not all(math.isfinite(v) for span in old for v in span)
                    or any(a > b for a,b in old)
                    or not window_start <= old[0][0] + .08 <= old[1][0] <= old[2][0] - .08 + 1e-6
                    or old[0][1] > old[1][0] + tolerance or old[1][1] > old[2][0] + tolerance
                    or old[2][1] > self._consumed_audio_end + tolerance
                    or self._hypothesis[left] != before.spoken or self._hypothesis[right] != after.spoken):
                continue
            if any(j not in (left,slot,right) and confidence >= threshold
                   and any(abs(span[0]-old[k][0]) <= tolerance for k in (0,1,2))
                   for j,(span,confidence) in enumerate(zip(self._hypothesis_timings,self._hypothesis_confs))):
                continue
            candidates=[]
            for i in range(1, len(window_words) - 1):
                spans=absolute[i-1:i+2]
                if (any(window_confs[j] < threshold for j in (i-1,i,i+1))
                        or not all(delegate._is_match(window_words[j], expected) for j,expected in ((i-1,before.expected),(i,state.expected),(i+1,after.expected)))
                        or abs(spans[1][0] - old[1][0]) > drift
                        or spans[1][0] < old[0][1] - tolerance
                        or spans[1][1] > old[2][0] + tolerance
                        or any(abs(spans[j][0]-old[j][0]) > drift for j in (0,2))
                        or max(spans[1][0],old[1][0]) > min(spans[1][1]+.08,old[1][1]+.08)
                        or not spans[0][0]+.08 <= spans[1][0] <= spans[2][0]-.08+1e-6
                        or spans[0][1] > spans[1][0]+tolerance or spans[1][1] > spans[2][0]+tolerance
                        or max(b for a,b in spans)+.08 > window_start+window_seconds-right_context_seconds):
                    continue
                if any(j not in (i-1,i,i+1) and window_confs[j]>=threshold
                       and any(abs(bounds[0]-span[0])<=tolerance for span in spans)
                       for j,bounds in enumerate(absolute)):
                    continue
                candidates.append(i)
            if len(candidates)!=1:
                continue
            eligible.add(index);i=candidates[0]
            previous=self._pending_gap_revisions.get(index)
            if previous and previous[:2] == (slot, old[1][0]) and endpoint_samples<=previous[2]:
                continue
            spans=tuple(absolute[i-1:i+2])
            agrees=(previous is not None and previous[:2] == (slot,old[1][0])
                    and all(abs(a[0]-b[0]) <= tolerance for a,b in zip(previous[4],spans))
                    and max(previous[4][1][0],spans[1][0]) <= min(previous[4][1][1]+.08,spans[1][1]+.08))
            count=previous[3]+1 if agrees else 1
            self._pending_gap_revisions[index]=(slot,old[1][0],endpoint_samples,count,spans)
            if count>=2 and self._matcher.revise_live_gap(index,slot,window_words[i],window_confs[i]):
                self._hypothesis[slot]=window_words[i]
                self._hypothesis_confs[slot]=window_confs[i]
                self._hypothesis_timings[slot]=absolute[i]
                self._pending_gap_revisions.pop(index,None)
        for index in set(self._pending_gap_revisions)-eligible:
            self._pending_gap_revisions.pop(index,None)

    def _diff_events(self, states) -> list[dict]:
        events: list[dict] = []
        for st in states:
            if (_live_asr_engine() == "fastconformer_rnnt" and self._timed_evidence_seen and st.status.value == "error"
                    and st.index not in self._confirmed_native_errors):
                continue
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
            evidence_confirmed = blueprint_status == "match" or (
                st.status.value == "error" and bool(st.spoken) and
                st.confidence >= getattr(self._matcher, "live_confidence_threshold", 0.55)
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
                "evidence_confirmed": evidence_confirmed,
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
            audio, self.sample_rate,
            " ".join(self.reference_text_with_tashkeel_words),
        )
        if not words:
            return None
        norm = [normalize_arabic(w) for w in words]
        # _decode_float() yields a plain list; the acoustic tajweed helpers are
        # numpy-based (segment.astype(...)) — convert before checking, otherwise
        # every finalize raises "'list' object has no attribute 'astype'".
        import numpy as np
        summary = TajweedChecker(sample_rate=self.sample_rate).check_all(
            np.asarray(audio, dtype=np.float32), norm, starts, ends
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

    def _native_final_evidence_complete(self) -> bool:
        """Audit native live witnesses and a fresh complete suffix, never stitched text."""
        import math
        from ml.alignment.streaming_matcher import WordStatus
        if (self._is_stub or _live_asr_engine() != "fastconformer_rnnt"
                or EVIDENCE_POLICY != "tier2" or self._last_native_view is None
                or self._pending_error_revisions or self._pending_gap_revisions):
            return False
        delegate = getattr(self._matcher, "_delegate", self._matcher)
        cursor = getattr(delegate, "_cursor", 0)
        budget = getattr(self._matcher, "max_live_words", 0)
        states = {x.index:x for x in getattr(delegate, "_resolved_states", [])}
        slots = getattr(delegate, "_live_hyp_indices", {})
        threshold = getattr(delegate, "live_confidence_threshold", .55)
        if (not 0 < cursor <= min(len(self.reference_words),budget)
                or set(states) != set(range(cursor))
                or set(slots) != set(range(cursor))):
            return False
        previous_slot = -1
        previous_time = -1.
        for index in range(cursor):
            state,slot = states[index],slots[index]
            if (state.status != WordStatus.MATCHED or not state.spoken
                    or not math.isfinite(state.confidence) or not threshold <= state.confidence <= 1
                    or not previous_slot < slot < min(len(self._hypothesis),len(self._hypothesis_confs),len(self._hypothesis_timings))
                    or self._hypothesis[slot] != state.spoken
                    or self._hypothesis_confs[slot] != state.confidence
                    or not delegate._is_match(state.spoken,self.reference_words[index])):
                return False
            begin,end = self._hypothesis_timings[slot]
            if (not all(math.isfinite(v)for v in (begin,end))
                    or not previous_time <= begin <= end <= self.duration_seconds+.08):
                return False
            previous_slot,previous_time = slot,begin
        start,endpoint,words,scores,times = self._last_native_view
        if (endpoint != self._total_samples or not 0 <= start < endpoint
                or not 0 < len(words) == len(scores) == len(times) <= cursor
                or (endpoint-start)/self.sample_rate > 21.
                or not getattr(self,"_timed_evidence_seen",False)):
            return False
        suffix_start = cursor-len(words)
        previous_time = -1.
        for index,(word,score,(begin,end)) in enumerate(zip(words,scores,times)):
            if (not word or not all(math.isfinite(v)for v in (score,begin,end))
                    or not threshold <= score <= 1
                    or not previous_time <= begin <= end <= (endpoint-start)/self.sample_rate+.08
                    or not delegate._is_match(word,self.reference_words[suffix_start+index])):
                return False
            # RNNT emission timestamps move by up to three encoder frames
            # between bounded contexts; they are not acoustic word boundaries.
            # Still require overlapping spans at the same mapped occurrence.
            slot=slots[suffix_start+index]
            old_begin,old_end=self._hypothesis_timings[slot]
            absolute_begin=begin+start/self.sample_rate
            absolute_end=end+start/self.sample_rate
            drift=.24+1e-6
            if (old_begin < start/self.sample_rate-drift
                    or abs(absolute_begin-old_begin)>drift
                    or max(absolute_begin,old_begin)>min(absolute_end+drift,old_end+drift)):
                return False
            previous_time=begin
        # Native suffix must account for every word through the current cursor;
        # a hallucinated/foreign extra token or an unknown trailing word fails
        # this audit rather than becoming independent final evidence.
        return True

    def _repair_final_native_words(self, states, native):
        """Keep two stronger original views of an uncertain final token.

        Only the SAME weak, correctly decoded token between globally unique
        final anchors qualifies. No new recognition, cursor progress, word
        substitution, or unsupported omission can become evidence here.
        """
        import math
        from collections import Counter
        from ml.alignment.native_evidence import prove_native_word_repair
        from ml.alignment.streaming_matcher import WordState, WordStatus

        previous, current = self._previous_native_view, self._last_native_view
        if (self._is_stub or self._explicit_transcriber is not None
                or EVIDENCE_POLICY != 'tier2' or _live_asr_engine() != 'fastconformer_rnnt'
                or previous is None or current is None or native is None
                or current[1] != self._total_samples or not hasattr(native, 'timings')):
            return states
        delegate = getattr(self._matcher, '_delegate', self._matcher)
        identity = lambda word: delegate._word_aliases.get(word, word)
        threshold = getattr(self._matcher, 'live_confidence_threshold', .55)
        words, scores, times = native.words, native.confidences, native.timings
        try:
            if not len(words) == len(scores) == len(times):
                return states
            last_begin = -1.
            for word, score, (begin, end) in zip(words, scores, times):
                if (not isinstance(word, str) or not word
                        or not all(math.isfinite(v) for v in (score, begin, end))
                        or not 0 <= score <= 1 or not 0 <= begin <= end <= self.duration_seconds + .08
                        or begin < last_begin):
                    return states
                last_begin = begin
            reference = [identity(word) for word in self.reference_words]
            keys = [identity(word) for word in words]
            ref_counts, native_counts = Counter(reference), Counter(keys)
            by_index = {state.index: state for state in states}
            limit = min(len(reference), int(self._matcher.max_live_words))
            for index in range(1, limit - 1):
                if index in by_index:
                    continue  # Never erase a supported error or prior match.
                triple = reference[index - 1:index + 2]
                if (len(set(triple)) != 3
                        or any(ref_counts[word] != 1 or native_counts[word] != 1 for word in triple)):
                    continue
                anchors = [by_index.get(index - 1), by_index.get(index + 1)]
                if any(anchor is None or anchor.status != WordStatus.MATCHED
                       or not math.isfinite(anchor.confidence) or not threshold <= anchor.confidence <= 1
                       or identity(anchor.spoken) != reference[anchor.index] for anchor in anchors):
                    continue
                left = keys.index(triple[0])
                if (keys[left:left + 3] != triple or scores[left] < threshold
                        or scores[left + 2] < threshold or scores[left + 1] >= threshold
                        or any(identity(state.spoken) == triple[1] for state in states if state.spoken)):
                    continue
                proof = prove_native_word_repair(
                    previous, current, expected=triple,
                    before_span=times[left], after_span=times[left + 2],
                    identity=identity, threshold=threshold, sample_rate=self.sample_rate,
                    total_samples=self._total_samples, right_context_seconds=LIVE_RIGHT_CONTEXT_SEC,
                )
                if proof is None:
                    continue
                old, new = times[left + 1], proof['spans'][1]
                if (abs(old[0] - new[0]) > .4 + 1e-5
                        or max(old[0], new[0]) > min(old[1] + .08, new[1] + .08) + 1e-5):
                    continue
                # A different recognized word can already own these frames.
                # Preserve live ownership even if final alignment changed its
                # text; prior native repairs may have no hypothesis slot.
                owners = {state.index: state for state in getattr(delegate, '_resolved_states', [])}
                owners.update(by_index)
                slots = getattr(delegate, '_live_hyp_indices', {})
                used = []
                for other_index, other in owners.items():
                    if (other_index in (index - 1, index, index + 1)
                            or other.status not in (WordStatus.MATCHED, WordStatus.ERROR)):
                        continue
                    slot = slots.get(other_index)
                    if slot is not None and 0 <= slot < len(self._hypothesis_timings):
                        used.append(self._hypothesis_timings[slot])
                    prior = self._native_word_repairs.get(other_index)
                    if prior:
                        used.append(prior['spans'][1])
                if (any(not all(math.isfinite(v) for v in bounds) for bounds in used)
                        or any(max(new[0], a) <= min(new[1] + .08, b + .08) + 1e-5 for a, b in used)):
                    continue
                by_index[index] = WordState(index, self.reference_words[index], WordStatus.MATCHED,
                                            proof['word'], proof['confidence'])
                logger.info('stream.final_native_repair', session_id=self.session_id,
                            word_index=index, confidence=proof['confidence'], endpoints=proof['endpoints'])
            return [by_index[index] for index in sorted(by_index)] if len(by_index) > len(states) else states
        except (ValueError, TypeError, IndexError, OverflowError):
            return states

    async def finalize(self) -> dict:
        """End the session: persist audio + build the final result blob."""
        from ml.alignment.streaming_matcher import WordStatus

        independent_finalizer = getattr(self._matcher, 'finalize_independent', None)
        use_recording_evidence = not self._is_stub and independent_finalizer is not None
        final_words: list[str] = []
        final_confs: list[float] = []
        final_native = None

        # A fresh native suffix may audit already independent live witnesses.
        # Otherwise retain the independent full-recording review. Stitched text
        # is never submitted as if it were new recognition evidence.
        native_complete = use_recording_evidence and self._native_final_evidence_complete()
        if use_recording_evidence and self._pcm and not native_complete:
            try:
                audio = self._decode_float()
                if _rms_energy(audio) >= SILENCE_RMS_THRESHOLD:
                    final_native = await asyncio.to_thread(
                        _independent_recording_transcriber, audio, self.sample_rate
                    )
                    words, confs = final_native
                    final_words, final_confs = list(words), list(confs)
            except Exception as exc:  # pragma: no cover - model failures
                logger.error("stream.finalize_transcribe_failed", session_id=self.session_id, error=str(exc))

        # A missing legacy/stub hypothesis permits one decode of audible speech.
        # Production evidence must remain independent of the prompted model;
        # failed recognition and silence cannot be promoted into a verdict.
        if not use_recording_evidence and not self._last_hypothesis and self._transcriber is not None and self._pcm:
            try:
                audio = self._decode_float()
                if _rms_energy(audio) >= SILENCE_RMS_THRESHOLD:
                    transcriber = (
                        self._transcriber if self._is_stub
                        else _independent_transcriber
                    )
                    words, confs = await asyncio.to_thread(
                        transcriber, audio, self.sample_rate
                    )
                    self._hypothesis = list(words)
                    self._hypothesis_confs = list(confs)
                    self._last_hypothesis = self._hypothesis
            except Exception as exc:  # pragma: no cover - model failures
                logger.error("stream.finalize_transcribe_failed", session_id=self.session_id, error=str(exc))

        audio_path = self._write_wav()
        public_base = settings.recitation_api_public_url.rstrip("/")
        user_audio_url = (
            f"{public_base}/v1/recitations/{self.session_id}/audio"
            if public_base and audio_path
            else audio_path
        )

        if use_recording_evidence:
            states = independent_finalizer(final_words, final_confs)
            states = self._repair_final_native_words(states, final_native)
        else:
            states = (
                self._matcher.finalize(self._last_hypothesis, self._hypothesis_confs)
                if self._matcher is not None
                else []
            )

        word_verdicts = []
        matched = 0
        evidence_confidences = []
        for st in states:
            supported = (
                st.status in (WordStatus.MATCHED, WordStatus.ERROR)
                and bool(st.spoken)
                and st.confidence >= getattr(self._matcher, 'live_confidence_threshold', 0.55)
            )
            if supported:
                evidence_confidences.append(st.confidence)
            elif not self._is_stub:
                # The mobile review falls back to live pending status when an
                # unconfirmed index is absent. Keep global indices unchanged.
                continue
            is_correct = st.status == WordStatus.MATCHED
            if is_correct:
                matched += 1
            word_verdicts.append({
                "word": st.expected,
                "word_index": st.index,
                "is_correct": is_correct,
                "confidence": round(st.confidence, 3),
                "evidence_confirmed": supported,
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

        total = len(word_verdicts)
        accuracy = (matched / total) if total else 0.0
        confidence = (
            sum(evidence_confidences) / len(evidence_confidences)
            if evidence_confidences else 0.0
        )

        # Best-effort tajweed pass (Tarteel-style post-session "mistake
        # review"): one timed full-audio transcription feeds the acoustic
        # tajweed checks (ghunnah/qalqalah/madd — numpy only, no torch).
        # Never blocks the result on failure; stub sessions and very long
        # sessions skip it. Independent production word review also skips this
        # prompted model pass: token emission times are not validated phoneme
        # boundaries and do not support acoustic grading.
        tajweed_score = 0.0
        tajweed_issues: list[dict] = []
        if (
            not self._is_stub
            and not use_recording_evidence
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
            "pronunciation_score": 0.0 if use_recording_evidence else round(accuracy, 4),
            "pronunciation_available": False,
            "tajweed_score": round(tajweed_score, 4),
            "tajweed_available": False,
            "tajweed_issues": tajweed_issues,
            "fluency_score": 0.0 if use_recording_evidence else round(accuracy, 4),
            "fluency_available": False,
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
