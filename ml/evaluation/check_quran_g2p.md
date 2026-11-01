# How `ml/alignment/quran_g2p.py` was checked

Against IqraEval's own reference phonemes (data from Hugging Face, not stored here):

| Set | Text used | Exact utterances | Phoneme error |
|---|---|---|---|
| Iqra_train (20,000 sentences, `style="sentence"`) | `tashkeel_sentence` | 88% | 0.64% |
| QuranMB.v2 test (1,642 recordings, `style="quran"`), each reference matched to its ayah | `ayah_text_simple` | 58% | 3.2% |

Most QuranMB differences come from that set's own spelling quirks (for example it
sometimes keeps the lam before a sun letter, or drops a shadda), not from wrong
pronunciation in our output. Using the Mushaf (Uthmani) spelling instead of the
plain spelling scores worse (5.7%), so the lexicon is built from the plain text.
