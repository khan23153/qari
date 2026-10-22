# Acoustic phoneme pilot

The requested outcome is continuous word tracking that detects changed vowels and pronunciation instead of accepting canonical ASR text. Keep the deployed word matcher, original models, confidence/activity/cursor guards, Hifz visibility and ayah markers. No user test recording is training data.

The production lexical decoder and existing Zipformer canonicalize all16 contributor-labelled Ikhlas error targets in a36-clip probe. The expert-labelled14-clip cross-check also shows both missed errors and incorrect phonetic transcriptions on correct speech. Neither text equality nor naive phonetic equality qualifies pronunciation.

Run an experimental, separate phoneme CTC head over the existing independent Whisper-base audio encoder. The encoder is frozen and its text decoder is never called. Train only from the public IqraEval/Iqra_TTS `phoneme_mis` targets of altered speech; never substitute canonical `phoneme_ref`. The pilot uses at most128 short synthetic clips, three training voices and one validation voice, with canonical sentence groups disjoint. This is feasibility testing; synthetic validation is not human qualification.

Use512-dimensional encoder frames at20ms, a small frame classifier, CTC blank0 and an explicit learned phoneme vocabulary preserving vowels, lengths and geminates. Validate PCM and target/frame lengths, source hashes, split identity and finite features. Preserve actual short-clip frame counts when encoding through the fixed30-second Whisper input. Memory limit3500MiB including swap, two CPUthreads at low priority, no GPU/quota dependency, disk reserve512MiB.

Report training/validation loss and independent greedy phoneme error rate; include unsupported validation phones. Keep all candidate weights outside git and outside production model paths. Human corrected-phoneme training/evaluation and release qualification remain mandatory before any rollout. The gated Iqra_Extra_IS26/IqraEval_Test_GT access is pending; existing unlabelled tester recordings cannot substitute for that truth. No pronunciation or tajweed accuracy claim follows from this pilot.

## Observed result and release decision

Both40-epoch runs completed without OOM. Corrected-cache v2 used95 training and32
voice/text-group-disjoint validation clips. Best synthetic phoneme error33.55% at
epoch16; later training overfits (epoch40 train loss.02037, validation loss2.0073).
All36 held-out human inference diagnostics completed, but phone deletion and
substitution errors remain even on correct-labelled recordings. Actual human
phone annotations are unavailable; no human PER or pronunciation accuracy is
claimed. The candidate is rejected for production grading.

Final full recitation API, ML and legacy API suite:960passed,1optional skip.
The pilot unit tests also pass without the optional inference installation.
Corrected human phoneme data and held-out acoustic qualification are the next
required steps. Production stays on0c7562b; this work adds no live grader.
