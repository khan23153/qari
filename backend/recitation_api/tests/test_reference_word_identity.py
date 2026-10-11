"""Comparison keys preserve spoken Quran letters, excluding nonspeech marks."""
from types import SimpleNamespace

import pytest

from app.services import streaming_session as ss


@pytest.mark.parametrize('text,expected',[
    ('۞ أَتَأْمُرُونَ','اتامرون'),
    ('۞ ٱللَّهُ','الله'),
    ('إِبْرَٰهِـۧمَ','ابراهيم'),
    ('ٱلنَّبِيِّـۧنَ','النبيين'),
    ('رَبَّـٰنِيِّـۧنَ','ربانيين'),
    ('بِهِۦ','به'),
])
def test_normalization_preserves_base_small_high_ya_and_excludes_section_marker(text,expected):
    assert ss._normalize(text) == expected


def test_corpus_aliases_exclude_real_word_collisions_and_ambiguous_spellings(monkeypatch):
    words = [
        ('ابرهم','إِبْرَٰهِـۧمَ'),
        ('ابراهيم','إِبْرَاهِيمَ'),
        ('والمنفقت','وَٱلْمُنَـٰفِقَـٰتُ'),
        ('عليكم','عَلَيْكُمْ'),
        ('عليهم','عَلَيْهِمْ'),
        ('كتب','كِتَٰب'),
        ('كتب','كَتَبَ'),
        ('علم','عَالِم'),
        ('علم','عَلِيم'),
    ]
    store = SimpleNamespace(
        list_ayahs=lambda:[(1,1)],
        get=lambda *_:SimpleNamespace(words=[SimpleNamespace(word=word,text_with_tashkeel=text) for word,text in words]),
    )
    monkeypatch.setattr(ss,'_get_reference_store',lambda:store)
    aliases = ss._get_live_word_aliases()
    assert aliases == {'ابرهم':'ابراهيم','والمنفقت':'والمنافقات'}
    aliases['عليكم']='عليهم'
    assert 'عليكم' not in ss._get_live_word_aliases()


def test_reference_display_and_ayah_marker_survive_comparison_normalization(monkeypatch):
    text = '۞ أَتَأْمُرُونَ'
    word = SimpleNamespace(word='اتامرون',text_with_tashkeel=text)
    reference = SimpleNamespace(words=[word],reference_audio_url='')
    store = SimpleNamespace(has=lambda *_:True,get=lambda *_:reference)
    monkeypatch.setattr(ss,'_get_reference_store',lambda:store)
    display,normalized,_,entries = ss.resolve_reference_words(2,44)
    assert display == [text]
    assert normalized == ['اتامرون']
    assert entries[0]['text_with_tashkeel'] == text
