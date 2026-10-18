"""A dagger alef on an existing alef maqsura must not add a second letter."""
from types import SimpleNamespace
import pytest
from app.services import streaming_session as ss
from ml.alignment.streaming_matcher import StreamingMatcher


@pytest.mark.parametrize('uthmani,plain,key',[
    ('عَلَىٰ','على','علي'),
    ('وَعَلَىٰٓ','وعلى','وعلي'),
    ('إِلَىٰ','إلى','الي'),
    ('أُولَىٰ','أولى','اولي'),
    ('مُوسَىٰ','موسى','موسي'),
    ('هُدَىٰ','هدى','هدي'),
])
def test_maqsura_dagger_and_plain_spelling_share_one_key(uthmani,plain,key):
    assert ss._normalize(uthmani)==ss._normalize(plain)==key


def test_real_reference_preposition_matches_without_merging_different_word(monkeypatch):
    text='عَلَىٰ'
    reference=SimpleNamespace(words=[
        SimpleNamespace(word='علي',text_with_tashkeel=text),
        SimpleNamespace(word='عليا',text_with_tashkeel='عَلِيًّا'),
    ],reference_audio_url='')
    store=SimpleNamespace(has=lambda *_:True,get=lambda *_:reference,list_ayahs=lambda:[(2,7)])
    monkeypatch.setattr(ss,'_get_reference_store',lambda:store)
    display,normalized,_,entries=ss.resolve_reference_words(2,7)
    matcher=StreamingMatcher(normalized,known_error_words=ss._get_live_error_vocabulary(),word_aliases=ss._get_live_word_aliases())
    assert matcher._is_match(ss._normalize('على'),normalized[0])
    assert not matcher._is_match(ss._normalize('على'),normalized[1])
    assert display==[text,'عَلِيًّا']
    assert entries[0]['text_with_tashkeel']==text

@pytest.mark.parametrize('text,published_key',[
    ('أَدْرَىٰكُم','ادراكم'),
    ('تَخْشَىٰهُ','تخشاه'),
])
def test_internal_carrier_uses_its_independently_published_word_identity(text,published_key):
    assert ss._normalize(text)==published_key

@pytest.mark.parametrize('text',['عَلَىَٰ','عَلَىـٰٓ ۖ'])
def test_terminal_carrier_accepts_intervening_combining_marks(text):
    assert ss._normalize(text)=='علي'
