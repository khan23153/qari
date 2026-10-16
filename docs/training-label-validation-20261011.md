# Spoken labels before Qari ASR adaptation

TLOG clean indicates valid filenames and noncorrupt audio; its labels are inferred from the filename and are not further validated according to the [official dataset card](https://huggingface.co/datasets/tarteel-ai/tlog). Structural waveform, token and CTC-frame checks cannot establish that the label was spoken. Two unprompted recognizers corroborated different-ayah conflicts in the existing local training set; original data and detailed private evidence are retained.

`prepare_pilot_data` now quarantines filename-derived TLOG sources and their linked augmented descendants before training, records every quarantined row/source, and refuses unvalidated evaluation labels. It preserves original audio/manifests. A clean boolean is not transcript evidence. The bounded PCD adaptation additionally requires the curated RetaSy sources, known disjoint speaker IDs, exact source/PCM hashes, native vocabulary/frame-fit checks and phone/control holdout.

The repaired existing5143-row input yields4000 explicit quarantines and1143 RetaSy clean/augmented training rows with the unchanged37 clean evaluation clips. The active pretrained model has not been trained on this local dataset; this finding is not proof of the cause of its remaining microphone Huwa miss. No automatic ASR relabeling or candidate deployment is performed.

Candidate release still requires independent native confidences, actual saved microphone Fatiha/Ikhlas, supported substitutions, silence/wrong-speech/prefix and phase controls, CPU/export/public latency checks and running source/model verification. Actual posterior scores and current confidence/speech guards remain unchanged.
