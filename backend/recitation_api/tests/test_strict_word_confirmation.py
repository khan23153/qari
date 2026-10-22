"""Captured near words must not acquire a production correctness verdict."""
import pytest
from types import SimpleNamespace

from app.services import streaming_session as ss
from tests.test_production_matcher_policy import production_session, pcm


@pytest.mark.parametrize('expected,heard', [
    ('الكافرون', 'القافلون'), ('الكافرون', 'الطافلون'),
    ('الكافرون', 'القاتلون'), ('الكتاب', 'الختام'),
    ('المغضوب', 'المغدوم'), ('اهدنا', 'اهدينا'),
    ('انعمت', 'انعمك'), ('فليعبدوا', 'فليغدوا'),
    ('عابد', 'عابدا'), ('عبدتم', 'اعبدتم'),
    ('الصمد', 'السمد'), ('حاسد', 'هاسد'), ('غاسق', 'غاسك'),
])
def test_actual_production_matcher_rejects_captured_different_native_text(production_session, expected, heard):
    assert not production_session._matcher._delegate._is_match(heard, expected)


def test_lossy_legacy_reference_key_cannot_undo_production_hamza_identity(production_session,monkeypatch):
    word=SimpleNamespace(word='يسلكم',text_with_tashkeel='يَسْـَٔلُكُمْ')
    store=SimpleNamespace(list_ayahs=lambda:[(36,21)],get=lambda *_:SimpleNamespace(words=[word]))
    monkeypatch.setattr(ss,'_get_reference_store',lambda:store)
    production_session.load_reference()
    matcher=production_session._matcher._delegate
    assert ss._normalize('يَسْـَٔلُكُمْ')=='يسالكم'
    assert not matcher._is_match('يسلكم','يسالكم')
    assert matcher._is_match('يسالكم','يسالكم')


@pytest.mark.asyncio
async def test_close_unknown_word_stays_unrevealed_as_following_word_progresses(production_session, monkeypatch):
    decodes=iter([(['بسم','الله'],[.95]*2),
                  (['بسم','الله','الرحمين','الرحيم'],[.95]*4)])
    monkeypatch.setattr(ss,'_independent_transcriber',lambda audio,sr:next(decodes))
    production_session.add_audio(pcm(1.5))
    await production_session.maybe_transcribe()
    production_session.add_audio(pcm(1.5))
    events=await production_session.maybe_transcribe()
    assert all(e['word_index']!=2 for e in events)
    assert any(e['word_index']==3 and e['status']=='match' for e in events)
    assert production_session._matcher._cursor==4
