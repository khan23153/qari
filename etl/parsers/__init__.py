"""Parsers for Quranic Arabic Corpus, tajweed markup, and audio segments."""

from .corpus_parser import CorpusParser
from .tajweed_parser import TajweedParser
from .audio_segment_parser import AudioSegmentParser

__all__ = ["CorpusParser", "TajweedParser", "AudioSegmentParser"]
