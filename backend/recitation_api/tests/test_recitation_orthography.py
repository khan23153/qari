"""Native spelling/token boundaries must not reject words or merge identities."""
from types import SimpleNamespace

import pytest

from app.services import streaming_session as ss
from ml.alignment.streaming_matcher import StreamingMatcher, WordStatus
from ml.inference import fastconformer_transcriber as fc
from ml.inference.transcript import TimedTranscript


@pytest.fixture
def corpus(monkeypatch):
    # Independently published Uthmani words, including a real collision with
    # the old lossy Yahya key. Legacy keys deliberately retain that old bug.
    pairs = [
        ('نحي', 'نُحْىِ'), ('يحي', 'يُحْىِ'), ('يحيي', 'يَحْيَىٰ'),
        ('شيا', 'شَيْـًٔا'), ('عني', 'عَنِّى'),
        ('ياقوم', 'يَـٰقَوْمِ'), ('ياليت', 'يَـٰلَيْتَ'),
        ('ياحسره', 'يَـٰحَسْرَةً'), ('ياويلنا', 'يَـٰوَيْلَنَا'),
        ('يابني', 'يَـٰبَنِىٓ'), ('قوم', 'قَوْم'), ('ليت', 'لَيْت'),
        ('حسره', 'حَسْرَة'), ('ويلنا', 'وَيْلَنَا'), ('بني', 'بَنِى'),
        ('الله', 'ٱللَّهُ'), ('العظام', 'ٱلْعِظَـٰمَ'), ('من', 'مَن'),
    ]
    reference = SimpleNamespace(words=[SimpleNamespace(word=a, text_with_tashkeel=b) for a,b in pairs])
    store = SimpleNamespace(list_ayahs=lambda:[(1,1)], get=lambda *_:reference)
    monkeypatch.setattr(ss, '_get_reference_store', lambda:store)
    monkeypatch.setenv('QARI_LIVE_ASR_ENGINE', 'fastconformer_rnnt')


def recognize(monkeypatch, words, confidences=None, timings=None):
    native = TimedTranscript(words, confidences or [.95]*len(words),
                             timings or [(i*.3, i*.3+.1) for i in range(len(words))])
    monkeypatch.setattr(fc, 'get_transcriber', lambda:SimpleNamespace(transcribe=lambda audio,sr:native))
    return ss._independent_transcriber([.1]*1600,16000)


def matcher(display):
    return StreamingMatcher([ss._normalize(display)],
        known_error_words=ss._get_live_error_vocabulary(),word_aliases=ss._get_live_word_aliases())


@pytest.mark.parametrize('native,display', [
    ('نحيي','نُحْىِ'), ('يحيي','يُحْىِ'), ('شيئًا','شَيْـًٔا'),
])
def test_independently_published_spellings_confirm_without_changing_native_scores(corpus,monkeypatch,native,display):
    decoded=recognize(monkeypatch,[native],[.93])
    m=matcher(display)
    states=m.evaluate(decoded.words,decoded.confidences)
    assert len(states)==1 and states[0].status==WordStatus.MATCHED
    assert states[0].confidence==.93


@pytest.mark.parametrize('native,display', [('يحيى','يُحْىِ'),('يحيي','يَحْيَىٰ')])
def test_yahya_and_yuhyi_remain_distinct_real_quran_words(corpus,monkeypatch,native,display):
    decoded=recognize(monkeypatch,[native])
    assert not matcher(display)._is_match(decoded.words[0],ss._normalize(display))


@pytest.mark.parametrize('following,expected', [
    ('قوم','ياقوم'),('ليت','ياليت'),('حسرة','ياحسره'),('ويلنا','ياويلنا'),('بني','يابني'),
])
def test_timely_native_vocative_components_form_one_corpus_word(corpus,monkeypatch,following,expected):
    decoded=recognize(monkeypatch,['يا',following],[.82,.96],[(1.,1.1),(1.4,1.8)])
    assert decoded.words==[expected]
    assert decoded.confidences==[.82]
    assert decoded.timings==[(1.,1.8)]


def test_weak_particle_cannot_borrow_following_word_confidence(corpus,monkeypatch):
    decoded=recognize(monkeypatch,['يا','قوم'],[.2,.99])
    states=matcher('يَـٰقَوْمِ').evaluate(decoded.words,decoded.confidences)
    assert not any(s.status==WordStatus.MATCHED for s in states)
    assert decoded.confidences==[.2]


def test_long_pause_does_not_join_separate_evidence(corpus,monkeypatch):
    decoded=recognize(monkeypatch,['يا','قوم'],timings=[(0.,.1),(1.,1.2)])
    assert decoded.words==['يا','قوم']


def test_unrecognized_vocative_does_not_invent_a_quran_word(corpus,monkeypatch):
    decoded=recognize(monkeypatch,['يا','غريب'])
    assert decoded.words==['يا','غريب']


def test_missing_particle_does_not_reveal_vocative(corpus,monkeypatch):
    decoded=recognize(monkeypatch,['قوم'])
    assert not any(s.status==WordStatus.MATCHED for s in matcher('يَـٰقَوْمِ').evaluate(*decoded))


def test_spoken_wrong_vocative_cannot_match_selected_word(corpus,monkeypatch):
    decoded=recognize(monkeypatch,['يا','قوم'])
    assert not matcher('يَـٰوَيْلَنَا')._is_match(decoded.words[0],'ياويلنا')


def test_finalizer_keeps_shayan_attached_to_its_own_native_slot(corpus,monkeypatch):
    decoded=recognize(monkeypatch,['عني','شيئا','ولا'])
    m=StreamingMatcher(['عني','شيا','ولا'],known_error_words=ss._get_live_error_vocabulary(),
                       word_aliases=ss._get_live_word_aliases())
    states=m.finalize(*decoded)
    assert [(s.index,s.status)for s in states]==[(0,WordStatus.MATCHED),(1,WordStatus.MATCHED),(2,WordStatus.MATCHED)]
    assert states[1].spoken==decoded.words[1]


@pytest.mark.parametrize('native', ['يحيى،','يحيى.','يَحْيَىٰ،','یحیى'])
def test_punctuation_and_persian_ya_cannot_turn_yahya_into_yuhyi(corpus,monkeypatch,native):
    decoded=recognize(monkeypatch,[native])
    assert decoded.words==['يحيى']
    assert not matcher('يُحْىِ')._is_match(decoded.words[0],ss._normalize('يُحْىِ'))


@pytest.mark.parametrize('text,expected', [
    ('يُحْـِۧىَ','يحيي'),('لِّنُحْـِۧىَ','لنحيي'),('وَلِـِّۧىَ','وليي'),
])
def test_small_high_ya_expansion_does_not_protect_a_synthetic_maqsura_ending(text,expected):
    assert ss._normalize(text)==expected


def test_canonical_yuhyi_spelling_stays_distinct_from_yahya(monkeypatch):
    words=[SimpleNamespace(word='يحيي',text_with_tashkeel='يُحْـِۧىَ'),
           SimpleNamespace(word='يحيي',text_with_tashkeel='يَحْيَىٰ')]
    store=SimpleNamespace(list_ayahs=lambda:[(1,1)],get=lambda *_:SimpleNamespace(words=words))
    monkeypatch.setattr(ss,'_get_reference_store',lambda:store)
    m=matcher('يُحْـِۧىَ')
    assert m._is_match(ss._normalize('يحيي'),ss._normalize('يُحْـِۧىَ'))
    assert not m._is_match(ss._normalize('يحيى'),ss._normalize('يُحْـِۧىَ'))


@pytest.mark.parametrize('word,display', [('من','يَأْمَنُ'),('كل','يَأْكُلُ'),('مر','يَأْمُرُ')])
def test_vocative_grouping_cannot_create_an_unspoken_verb(corpus,monkeypatch,word,display):
    ref=SimpleNamespace(words=[SimpleNamespace(word=ss._normalize(display),text_with_tashkeel=display)])
    store=SimpleNamespace(list_ayahs=lambda:[(1,1)],get=lambda *_:ref)
    monkeypatch.setattr(ss,'_get_reference_store',lambda:store)
    decoded=recognize(monkeypatch,['يا',word])
    assert decoded.words==['يا',word]
