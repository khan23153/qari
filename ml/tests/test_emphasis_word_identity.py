"""Unknown native emphasis spellings cannot become another known Quran word."""
import pytest
from ml.alignment.streaming_matcher import StreamingMatcher

def test_native_samad_spelling_does_not_match_hamd():
 m=StreamingMatcher(['الحمد'],known_error_words={'الحمد','الصمد'})
 assert not m._is_match('السمد','الحمد')

def test_native_samad_spelling_preserves_its_own_known_identity():
 m=StreamingMatcher(['الصمد'],known_error_words={'الحمد','الصمد'})
 assert m._is_match('السمد','الصمد')

def test_captured_wrong_surah_cannot_reveal_hamd_after_shared_bismillah():
 ref=['بسم','الله','الرحمن','الرحيم','الحمد','لله','رب','العالمين']
 m=StreamingMatcher(ref,known_error_words=set(ref)|{'الصمد','قل','هو','احد'})
 for words in [ref[:4],ref[:4]+['السمد','لم','يلد']]:states=m.evaluate(words,[.95]*len(words))
 assert all(x.index<4 for x in states if x.status.value=='matched')

def test_known_identity_is_not_rewritten_through_an_emphasis_neighbor():
 m=StreamingMatcher(['صد'],known_error_words={'سد','صد'})
 assert not m._is_match('سد','صد')

@pytest.mark.parametrize('heard,legacy,canonical',[
 ('المطنفسون','المتنفسون','المتنافسون'),
 ('تقطلونهم','تقتلونهم','تقاتلونهم'),
 ('بالسلحين','بالصلحين','بالصالحين'),
 ('فالمغيرط','فالمغيرت','فالمغيرات'),
])
def test_emphasis_neighbor_keeps_previously_supported_quran_spelling_alias(heard,legacy,canonical):
 m=StreamingMatcher([canonical],known_error_words={legacy,canonical},word_aliases={legacy:canonical})
 assert m._is_match(heard,canonical)

@pytest.mark.parametrize('heard',['صوط','سوت'])
def test_ambiguous_canonical_word_neighbors_cannot_choose_selected_reference(heard):
 for reference in ['صوت','سوط']:
  m=StreamingMatcher([reference],known_error_words={'صوت','سوط'})
  assert not m._is_match(heard,reference)
