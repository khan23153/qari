"""Tests for ETL parsers."""
import pytest
from etl.parsers.corpus_parser import CorpusParser
from etl.parsers.tajweed_parser import TajweedParser


class TestCorpusParser:
    def test_pos_group_mapping(self):
        parser = CorpusParser()
        assert parser.POS_GROUP_MAP["N"] == "ism"
        assert parser.POS_GROUP_MAP["V"] == "fil"
        assert parser.POS_GROUP_MAP["P"] == "harf"

    def test_transliterate_root(self):
        parser = CorpusParser()
        result = parser._transliterate_root("حمد")
        assert "H" in result
        assert "M" in result
        assert "D" in result


class TestTajweedParser:
    def test_parse_empty(self):
        parser = TajweedParser()
        result = parser.parse_ayah(1, 1, "", [])
        assert result == []
