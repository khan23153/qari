"""Production batch observed-diacritic and strict word evidence contract."""
from types import SimpleNamespace
import numpy as np
import pytest

from app.workers.fast_inference_worker import BatchWordMatchingPipeline, _reference_only_verdicts
from ml.inference.asr import ASRResult, ASRToken
from ml.tajweed.reference_store import AyahReference, ReferenceStore, WordReference


def run_batch(expected, heard, confidences=None, *, asr=None):
    store = ReferenceStore()
    store.add(AyahReference(surah=1, ayah=7, text=' '.join(expected), normalized_text='',
                           words=[WordReference(word=w, text_with_tashkeel=w) for w in expected]))
    confidence = confidences or [.95]*len(heard)
    tokens=[ASRToken(text=w,normalized=w,start_time=i*.2,end_time=(i+1)*.2,confidence=c)
            for i,(w,c) in enumerate(zip(heard,confidence))]
    asr=asr or SimpleNamespace(transcribe=lambda *_: ASRResult(raw_text=' '.join(heard),normalized_text='',tokens=tokens))
    rows=BatchWordMatchingPipeline(store,asr).analyze(np.ones(16000,dtype='float32')*.1,16000,1,[7],'test').words
    return _reference_only_verdicts(rows,start_index=0,reference_audio_url=None,user_audio_url=None)[0]


def test_explicit_any_wrong_word_is_substitution_not_fuzzy_correct():
    row=run_batch(['الكافرون'],['القافرون'])[0]
    assert row['is_correct'] is False
    assert row['error_type']=='substituted'
    assert row['evidence_confirmed'] is True
    assert row['display_color']=='#EF4444'


def test_observed_damma_before_next_word_is_harakat_mistake_red():
    rows=run_batch(['أَنْعَمْتَ','عَلَيْهِمْ'],['أَنْعَمْتُ','عَلَيْهِمْ'])
    assert rows[0]['error_type']=='harakat_mistake'
    assert rows[0]['evidence_source']=='asr_diacritic'
    assert rows[0]['display_color']=='#EF4444'
    assert rows[0]['actual_text']=='أَنْعَمْتُ'
    assert rows[1]['is_correct'] is True


@pytest.mark.parametrize('spoken',['الْعَالَمِين','الْعَالَمِينْ'])
def test_waqf_final_vowel_not_a_false_accusation(spoken):
    row=run_batch(['الْعَالَمِينَ'],[spoken])[0]
    assert row['is_correct'] is True
    assert row['error_type'] is None


def test_partial_tashkeel_and_no_tashkeel_are_not_false_errors():
    for heard in ['أَنْعَمْت','انعمت']:
        row=run_batch(['أَنْعَمْتَ'],[heard])[0]
        assert row['is_correct'] is True
        assert row['error_type'] is None


def test_two_missing_words_between_confirmed_anchors_are_missed_red():
    rows=run_batch(['الحمد','لِلَّهِ','رَبِّ','العالمين'],['الحمد','العالمين'])
    assert [r['error_type'] for r in rows]==[None,'missed','missed',None]
    assert all(r['display_color']=='#EF4444' and r['evidence_confirmed'] for r in rows[1:3])


def test_unread_suffix_is_pending_not_red():
    rows=run_batch(['الحمد','لِلَّهِ','رَبِّ','العالمين'],['الحمد'])
    assert [r['error_type'] for r in rows[1:]]==['not_reached']*3
    assert all(not r['evidence_confirmed'] and r['display_color'] is None for r in rows[1:])


def test_low_confidence_diacritics_do_not_become_red_errors():
    row=run_batch(['أَنْعَمْتَ'],['أَنْعَمْتُ'],[.2])[0]
    assert row['error_type']=='recognition_uncertain'
    assert not row['evidence_confirmed']
    assert row['display_color'] is None


def test_invalid_confidence_cannot_prove_missing_prefix_words():
    rows=run_batch(['الحمد','الله','رب'],['رب'],[1.2])
    assert all(not row['evidence_confirmed'] for row in rows)
    assert all(row['display_color'] is None for row in rows)


def test_unrelated_confident_word_cannot_prove_skipped_words_or_suffix_progress():
    rows = run_batch(['الحمد', 'لله', 'رب', 'العالمين'], ['الحمد', 'شكرا'])
    assert rows[0]['is_correct']
    assert not any(row['error_type'] == 'missed' for row in rows)
    assert all(not row['evidence_confirmed'] and row['display_color'] is None
               for row in rows[2:])


def test_partial_repeated_reference_uses_first_occurrence_and_keeps_second_pending():
    rows = run_batch(['رَبِّ', 'الْعَالَمِينَ', 'رَبِّ', 'الْعَالَمِينَ'],
                     ['رَبِّ', 'الْعَالَمِينَ'])
    assert [row['is_correct'] for row in rows] == [True, True, False, False]
    assert [row['error_type'] for row in rows] == [None, None, 'not_reached', 'not_reached']
    assert all(not row['evidence_confirmed'] for row in rows[2:])


def test_equal_cost_internal_repetition_does_not_steal_first_occurrence():
    rows = run_batch(['رب', 'رب', 'العالمين'], ['رب', 'العالمين'])
    assert rows[0]['is_correct']
    assert rows[1]['error_type'] == 'missed'
    assert rows[2]['is_correct']


@pytest.mark.parametrize('invalid', [float('nan'), float('inf'), -.1, 1.2, None, 'invalid'])
def test_invalid_confidence_text_cannot_choose_the_later_occurrence(invalid):
    rows = run_batch(['رب', 'الأول', 'رب', 'الثاني', 'الرحيم'],
                     ['رب', 'الثاني', 'الرحيم'], [.95, invalid, invalid])
    assert [i for i, row in enumerate(rows) if row['is_correct']] == [0]
    assert all(not row['evidence_confirmed'] and row['display_color'] is None
               for row in rows[1:])


def adapter_for(raw_word, confidence=.93, starts=140, ends=860):
    from app.workers.fast_inference_worker import FasterWhisperASRAdapter

    adapter = FasterWhisperASRAdapter.__new__(FasterWhisperASRAdapter)
    adapter._transcriber = SimpleNamespace(
        verify_model_dir='/unused/independent',
        transcribe_independent_with_timings=lambda *_: ([raw_word], [confidence], [starts], [ends]),
    )
    return adapter


def test_adapter_splits_raw_phrase_once_without_fabricating_native_metadata():
    adapter = adapter_for('الْحَمْدُ لِلَّهِ')
    result = adapter.transcribe(np.ones(16000, dtype='float32'), 16000)
    assert [token.text for token in result.tokens] == ['الْحَمْدُ', 'لِلَّهِ']
    assert result.raw_text == 'الْحَمْدُ لِلَّهِ'
    assert result.normalized_words == ['الحمد', 'لله']
    assert [token.confidence for token in result.tokens] == [.93, .93]
    # Preserve the actual shared native span; never synthesize per-word timing.
    assert [(token.start_time, token.end_time) for token in result.tokens] == [(.14, .86)] * 2
    rows = run_batch(['الْحَمْدُ', 'لِلَّهِ'], [], asr=adapter)
    assert all(row['is_correct'] and row['error_type'] is None for row in rows)
    assert [row['observed_text'] for row in rows] == ['الْحَمْدُ', 'لِلَّهِ']


def test_ambiguous_raw_boundaries_retain_lexical_tokens_without_vowel_evidence():
    adapter = adapter_for('أَنْعَمْتُ،عَلَيْهِمْ')
    result = adapter.transcribe(np.ones(16000, dtype='float32'), 16000)
    assert result.normalized_words == ['انعمت', 'عليهم']
    assert result.raw_text == 'أَنْعَمْتُ،عَلَيْهِمْ'
    assert [token.text for token in result.tokens] == ['', '']
    rows = run_batch(['أَنْعَمْتَ', 'عَلَيْهِمْ'], [], asr=adapter)
    assert all(row['is_correct'] and row['error_type'] is None for row in rows)
    assert all(not row['harakat_conflicts'] for row in rows)


def test_canonical_printed_conflict_text_preserves_legacy_lexical_word_key():
    row = run_batch(['أَنْعَمْتَ'], ['أَنْعَمْتُ،'])[0]
    assert row['error_type'] == 'harakat_mistake'
    assert row['word'] == 'انعمت'
    assert row['expected_text'] == 'أَنْعَمْتَ'
    assert row['actual_text'] == 'أَنْعَمْتُ،'


def test_production_independent_decoder_explicitly_disables_prompts():
    from ml.inference.faster_whisper_transcriber import FasterWhisperTranscriber
    captured={}
    class Model:
        def transcribe(self,_audio,**kwargs):
            captured.update(kwargs)
            return [SimpleNamespace(words=[SimpleNamespace(word='قُلْ',probability=.9,start=0,end=.2)])],None
    t=FasterWhisperTranscriber('/unused/prompted')
    t._model_verify=Model()
    words,*_=t.transcribe_independent_with_timings(np.ones(16000,dtype='float32')*.1)
    assert words==['قُلْ']
    assert captured['initial_prompt'] is None
    assert captured['condition_on_previous_text'] is False


def test_zero_duration_tail_cannot_bridge_to_unread_substitutions():
    # Real upload failure: a zero-duration hallucination followed by another
    # confident token borrowed two unread reference slots after a correct ayah.
    heard = ['قل', 'هو', 'الله', 'أحد', 'ما', 'يغفى']
    tokens = [ASRToken(text=w, normalized=w, start_time=i*.15,
                       end_time=(i+1)*.15, confidence=.95)
              for i, w in enumerate(heard)]
    tokens[4].start_time = tokens[4].end_time = .6
    tokens[5].start_time, tokens[5].end_time = .6, .7
    asr = SimpleNamespace(transcribe=lambda *_: ASRResult(
        raw_text=' '.join(heard), normalized_text='', tokens=tokens))
    rows = run_batch(['قل', 'هو', 'الله', 'أحد', 'الله', 'الصمد'], [], asr=asr)
    assert all(row['is_correct'] for row in rows[:4])
    assert all(not row['evidence_confirmed'] and row['display_color'] is None
               for row in rows[4:])
    assert not any(row['error_type'] in {'missed', 'substituted', 'harakat_mistake'}
                   for row in rows[4:])


@pytest.mark.parametrize('start,end', [
    (0., 0.), (-.1, .2), (.3, .2), (0., 1.1),
    (float('nan'), .2), (0., float('inf')),
])
def test_invalid_native_span_cannot_confirm_an_error_or_omission(start, end):
    token = ASRToken(text='شكرا', normalized='شكرا', start_time=start,
                     end_time=end, confidence=.99)
    asr = SimpleNamespace(transcribe=lambda *_: ASRResult(
        raw_text='شكرا', normalized_text='', tokens=[token]))
    rows = run_batch(['الحمد', 'لله'], [], asr=asr)
    assert all(not row['evidence_confirmed'] and row['display_color'] is None
               for row in rows)


@pytest.mark.parametrize('next_confidence,conflict', [(.1, False), (.95, True)])
def test_wasl_context_requires_a_supported_following_native_word(next_confidence, conflict):
    rows = run_batch(['أَنْعَمْتَ', 'عَلَيْهِمْ'],
                     ['أَنْعَمْتْ', 'عَلَيْهِمْ'], [.95, next_confidence])
    assert (rows[0]['error_type'] == 'harakat_mistake') is conflict


@pytest.mark.parametrize('confidence,end', [(.95, .2), (.1, .4)])
def test_unresolved_native_word_makes_the_whole_bracketed_gap_uncertain(confidence, end):
    tokens = [
        ASRToken(text='الحمد', normalized='الحمد', start_time=0., end_time=.2, confidence=.95),
        ASRToken(text='رب', normalized='رب', start_time=.2, end_time=end, confidence=confidence),
        ASRToken(text='العالمين', normalized='العالمين', start_time=.4, end_time=.6, confidence=.95),
    ]
    asr = SimpleNamespace(transcribe=lambda *_: ASRResult(
        raw_text='الحمد رب العالمين', normalized_text='', tokens=tokens))
    rows = run_batch(['الحمد', 'لله', 'رب', 'العالمين'], [], asr=asr)
    assert rows[0]['is_correct'] and rows[3]['is_correct']
    assert all(row['error_type'] == 'recognition_uncertain' for row in rows[1:3])
    assert all(not row['evidence_confirmed'] and row['display_color'] is None
               for row in rows[1:3])
