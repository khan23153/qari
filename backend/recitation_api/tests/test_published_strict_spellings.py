"""Strict confirmation accepts published spellings, not held-out ASR guesses."""
from types import SimpleNamespace
import pytest
from app.services import streaming_session as ss
from ml.alignment.streaming_matcher import StreamingMatcher, WordStatus

# quran-simple-clean edition, SHA256 e9f87186120851fbf1e04813a423076850e1b6b9ad769a797117dca623aad4af.
# Each Uthmani spelling is in the local immutable reference bundle.
PAIRS=[
    ('الصلاة','ٱلصَّلَوٰةَ'), ('إيلافهم','إِۦلَـٰفِهِمْ'),
    ('أأنذرتهم','ءَأَنذَرْتَهُمْ'), ('أأتخذ','ءَأَتَّخِذُ'),
    ('يستهزئون','يَسْتَهْزِءُونَ'), ('مستهزئون','مُسْتَهْزِءُونَ'),
    ('متكئون','مُتَّكِـُٔونَ'), ('أقصى','أَقْصَا'),
    ('الليل','ٱلَّيْلَ'), ('والليل','وَٱلَّيْلِ'),
    ('الزكاة','ٱلزَّكَوٰةَ'), ('الحياة','ٱلْحَيَوٰةَ'),
    ('أدراك','أَدْرَىٰكَ'), ('إسرائيل','إِسْرَٰٓءِيلَ'),
]


@pytest.mark.parametrize('imlai,uthmani',PAIRS)
def test_published_representation_difference_retains_original_confidence(monkeypatch,imlai,uthmani):
    word=SimpleNamespace(word=ss._normalize(uthmani),text_with_tashkeel=uthmani)
    store=SimpleNamespace(list_ayahs=lambda:[(1,1)],get=lambda *_:SimpleNamespace(words=[word]))
    monkeypatch.setattr(ss,'_get_reference_store',lambda:store)
    reference=ss._normalize(uthmani)
    heard=ss._normalize(imlai)
    m=StreamingMatcher([reference],known_error_words=ss._get_live_error_vocabulary(),
                       word_aliases=ss._get_live_word_aliases(),strict_word_identity=True)
    states=m.evaluate([heard],[.91])
    assert [(s.index,s.status,s.confidence)for s in states]==[(0,WordStatus.MATCHED,.91)]


def test_question_hamza_does_not_become_the_ordinary_past_tense(monkeypatch):
    words=[SimpleNamespace(word='اتخذ',text_with_tashkeel='ٱتَّخَذَ'),
           SimpleNamespace(word='اتخذ',text_with_tashkeel='ءَأَتَّخِذُ')]
    store=SimpleNamespace(list_ayahs=lambda:[(1,1)],get=lambda *_:SimpleNamespace(words=words))
    monkeypatch.setattr(ss,'_get_reference_store',lambda:store)
    past=ss._normalize('ٱتَّخَذَ')
    question=ss._normalize('ءَأَتَّخِذُ')
    assert past=='اتخذ' and question=='ااتخذ'
    m=StreamingMatcher([past],known_error_words=ss._get_live_error_vocabulary(),
                       word_aliases=ss._get_live_word_aliases(),strict_word_identity=True)
    assert not m._is_match(question,past)
    assert m._is_match(past,past)


@pytest.mark.parametrize('text,expected',[
    ('ءَأَنذَرْتَهُمْ','اانذرتهم'), ('ءَأَتَّخِذُ','ااتخذ'),
    ('ءَامَنُوا۟','امنوا'), ('لِإِيلَـٰفِ','لايلاف'),
])
def test_initial_interrogative_preserves_two_alefs_without_inventing_one_in_amanu(text,expected):
    assert ss._normalize(text)==expected


@pytest.mark.parametrize('printed,imlai_key,distinct_bare',[
    ('يَسْـَٔلُكُمْ','يسالكم','يسلكم'),
    ('أَءِنَّكَ','اانك','انك'),
])
def test_exact_published_print_retains_hamza_without_rewriting_another_bare_word(printed,imlai_key,distinct_bare):
    assert ss._normalize(printed)==imlai_key
    assert ss._normalize(distinct_bare)==distinct_bare
    assert ss._normalize(printed)!=ss._normalize(distinct_bare)
