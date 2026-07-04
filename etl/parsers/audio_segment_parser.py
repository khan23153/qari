"""
Audio segment parser for Quran.com ayah audio.

Quran.com's audio API returns per-ayah audio files with an optional
``segments`` array.  Each segment is a triple (or longer tuple) of:

    [start_ms, end_ms, word_position]

where ``word_position`` is the 1-indexed word number within the ayah
(0 or -1 typically indicates a pause/silence segment).

The parser converts these into structured per-word timing dicts suitable
for database insertion and CDN synchronisation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class AudioSegmentParser:
    """Parse Quran.com audio segment timestamps into per-word timing data.

    Usage::

        parser = AudioSegmentParser()
        word_timings = parser.parse_segments(raw_segments)
    """

    def parse_segments(
        self,
        raw_segments: Optional[List[Any]],
    ) -> List[Dict[str, Any]]:
        """Parse raw segment data into structured word-timing dicts.

        Parameters
        ----------
        raw_segments:
            List of segment tuples/lists from the API, e.g.::

                [[0, 4200, 0], [4200, 5100, 1], [5100, 6800, 2], ...]

            Each inner list is ``[start_ms, end_ms, word_position]``.
            Some reciters include a 4th element (``[start, end, word, verse]``).

        Returns
        -------
        list of dicts with keys::

            word_position (1-indexed, or 0 for silence/pause),
            start_ms, end_ms, duration_ms,
            is_silence (bool — True when word_position <= 0),
            verse_segment (optional int from 4-element segments),
        """
        if not raw_segments:
            return []

        timings: List[Dict[str, Any]] = []

        for seg in raw_segments:
            if not seg or len(seg) < 3:
                logger.warning("malformed_segment", segment=seg)
                continue

            try:
                start_ms = int(seg[0])
                end_ms = int(seg[1])
                word_position = int(seg[2])
            except (ValueError, TypeError, IndexError) as exc:
                logger.warning("segment_parse_error", segment=seg, error=str(exc))
                continue

            duration_ms = end_ms - start_ms
            is_silence = word_position <= 0

            timing: Dict[str, Any] = {
                "word_position": word_position,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "duration_ms": duration_ms,
                "is_silence": is_silence,
            }

            # Some segments include a verse number as the 4th element
            if len(seg) >= 4:
                try:
                    timing["verse_segment"] = int(seg[3])
                except (ValueError, TypeError):
                    pass

            timings.append(timing)

        logger.debug("parsed_segments", count=len(timings))
        return timings

    # ------------------------------------------------------------------
    # Batch helper
    # ------------------------------------------------------------------

    def parse_ayah_audio(
        self,
        surah_number: int,
        ayah_number: int,
        audio_file: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse a complete audio file dict (from Quran.com) into structured data.

        Parameters
        ----------
        surah_number, ayah_number:
            Location identifiers.
        audio_file:
            Dict from the API with keys like ``audio_url``, ``duration``,
            ``segments``, ``verse_number``.

        Returns
        -------
        dict with keys::

            surah, ayah, audio_url, duration_sec, segments (parsed list),
        """
        raw_segments = audio_file.get("segments") or audio_file.get("timing_segments")
        parsed = self.parse_segments(raw_segments)

        return {
            "surah": surah_number,
            "ayah": ayah_number,
            "audio_url": audio_file.get("audio_url", ""),
            "duration_sec": audio_file.get("duration", 0),
            "segments": parsed,
        }

    def parse_surah_audio(
        self,
        surah_number: int,
        audio_files: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Parse all audio files for a surah into structured timing data.

        Parameters
        ----------
        surah_number:
            Surah number.
        audio_files:
            List of audio file dicts from ``QuranComClient.get_audio_segments()``.
        """
        results: List[Dict[str, Any]] = []

        for af in audio_files:
            ayah_num = af.get("verse_number", 0)
            parsed = self.parse_ayah_audio(surah_number, ayah_num, af)
            results.append(parsed)

        logger.info(
            "parsed_surah_audio",
            surah=surah_number,
            ayahs=len(results),
            total_segments=sum(len(r["segments"]) for r in results),
        )
        return results
