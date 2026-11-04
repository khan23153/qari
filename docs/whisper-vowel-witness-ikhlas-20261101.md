# Whisper vowel witness on labeled real recitations — 1 November 2026

Model: independent Whisper base CT2 INT8 `qari-ct2-base`, model.bin SHA256 `b47c0fc7cd202c24ad4c7816e29d06c7d37c3761c1dcc91690796227df01dfa0` (same hash as production), recovered from Kaggle dataset `telethonfool/qari-frozen-encoder-20261018`.

Decode: production `FasterWhisperTranscriber.transcribe_independent` (no prompt, `condition_on_previous_text=False`, beam 1, temperature 0). Check: base-letter alignment, then `compare_harakat` on aligned words with confidence >= 0.55 (as `ml/alignment/vowel_witness.py`).

Audio: 36 human recordings of Surah Al-Ikhlas with contributor labels, Kaggle `telethonfool/qari-native-probe-private-20261021` (source: MuazAhmad7/Surah_Ikhlas-Labeled_Dataset, CC-BY-4.0). Labels were not re-annotated by Qari.

## Result

| Recordings | Count | Turned red |
|---|---|---|
| Labeled correct | 20 | **0** (false alarms) |
| Labeled harakat error | 16 | **3** caught |

- No false red on any correct recording, including ones where Whisper misheard a word (those words do not align, so they lend nothing).
- Most vowel errors are missed: Whisper writes the canonical vowels anyway (all 5 قُلْ errors came back as `قُلْ`). The witness is safe but low recall; it cannot replace an acoustic vowel model.
- Decode time per short ayah in the sandbox (4 threads): 0.8–1.89 s.

## Per recording

| id | ayah | label | error word | Whisper raw | flagged |
|---|---|---|---|---|---|
| ID165V1F | 1 | error | قُلْ | قُلْ هُوَ اللَّهُ أَحَدٌ | — |
| ID252V1F | 1 | error | قُلْ | قُلْ هُوَ اللَّهُ أَحَدٌ | — |
| ID276V1F | 1 | error | قُلْ | قُلْ هُوَ اللَّهُ أَحَدٌ | — |
| ID277V1F | 1 | error | قُلْ | قُلْ يَوْمَ اللَّهُ أَحَدٌ | — |
| ID279V1F | 1 | error | قُلْ | قُلْ هُوَ اللَّهُ أَحَدٌ | — |
| ID3V1T | 1 | correct | — | قُلْ هُوَ اللَّهُ أَحَدٌ | — |
| ID4V1T | 1 | correct | — | قُلْ إِفْرَى اللَّهُ أَحَدٌ | — |
| ID5V1T | 1 | correct | — | قُلْ هُوَ اللَّهُ أَحَدٌ | — |
| ID6V1T | 1 | correct | — | قُلْ هُوَ اللَّهُ أَحَدٌ | — |
| ID7V1T | 1 | correct | — | قُلْ هُوَ اللَّهُ وَحَدٌ | — |
| ID146V2F | 2 | error | ٱلصَّمَدُ | اللَّهُ الصَّمَدُ | — |
| ID3V2T | 2 | correct | — | اللَّهُ الصَّمَدُ | — |
| ID4V2T | 2 | correct | — | اللَّهُ الصَّمَدُ | — |
| ID5V2T | 2 | correct | — | اللَّهُ الصَّمَدُ | — |
| ID6V2T | 2 | correct | — | اللَّهُ السَّمَدُ | — |
| ID7V2T | 2 | correct | — | اللَّهُ الصَّمَدُ | — |
| ID2V3T | 3 | correct | — | لَمْ يَلِدْ وَلَمْ يُوبِدْ | — |
| ID3V3T | 3 | correct | — | لَمْ يَلِدْ وَلَمْ يُولَدْ | — |
| ID4V3T | 3 | correct | — | لَمْ يَلِدْ وَلَمْ يُولَدْ | — |
| ID5V3T | 3 | correct | — | لَمْ يَلِدْ وَلَمْ يُولَدْ | — |
| ID6V3T | 3 | correct | — | لَمْ يَجِدْ وَلَمْ يُولَدْ | — |
| ID12V4F | 4 | error | كُفُوًا | وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ | — |
| ID14V4F | 4 | error | كُفُوًا | وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ | — |
| ID15V4F | 4 | error | كُفُوًا | وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ | — |
| ID26V4F | 4 | error | كُفُوًا | وَلَمْ يَكُنْ لَهُ كُفٌّ أَحَدٌ | — |
| ID38V4F | 4 | error | كُفُوًا | وَلَمْ يَكُنْ لَهُ كُفْوًا أَحَدٌ | كُفُوًا → كُفْوًا |
| ID52V4F | 4 | error | كُفُوًا | وَيَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ | — |
| ID69V4F | 4 | error | كُفُوًا | وَلَمْ يَكُنْ لَهُ كُفْوًا أَحَدٌ | كُفُوًا → كُفْوًا |
| ID90V4F | 4 | error | كُفُوًا | وَلَمْ يَكُنْ لَهُ كُفًُا أَحَدٌ | — |
| ID142V4F | 4 | error | كُفُوًا | وَلَمْ يَكُنْ لَهُ كُفْوًا أَحَدٌ | كُفُوًا → كُفْوًا |
| ID173V4F | 4 | error | كُفُوًا | وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ | — |
| ID3V4T | 4 | correct | — | وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ | — |
| ID4V4T | 4 | correct | — | وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ | — |
| ID5V4T | 4 | correct | — | وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ | — |
| ID8V4T | 4 | correct | — | وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ | — |
| ID11V4F | 4 | correct | — | وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ | — |
