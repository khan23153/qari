# Larger frozen-encoder phoneme training

The user requests continued repair until pronunciation and tracking work. The
95-clip synthetic pilot overfits, with33.55% unseen-voice phoneme error. Public
word-trained alternatives did not separate labelled vowel errors reliably.
Kaggle login is now verified as telethonfool using its current2.2.4 CLI;30GPUhours
are available. Host CLI1.7.4.5 does not understand KAGGLE_API_TOKEN.

Extend the existing experimental audio-only CTC approach using the exact original
Whisper-base CTranslate2 encoder. Freeze all encoder weights. Train a small masked
temporal convolutional phoneme head on at most8192 actual altered-phone clips from
public IqraEval/Iqra_TTS revision97d27c2a575739e7aaffee2518d6817d203829c9.
Use at most1536 clips per training voice, and512 validation clips fromJessica.
Normalize only reference grouping (never phone targets), reserve15% of reference
groups by stable hash, and exclude those groups from every training voice.
Jessica never trains. Retain vowel case, lengths, geminates and actual phoneme_mis;
missing altered targets fail. Source audio, hashes and split provenance are recorded.
No user recording, human evaluation clip, target-text prompt or text decoder trains.

The head consumes actual20ms512-dimensional encoder frames, cachesfloat16 features,
and masks padding before every temporal convolution so batch padding cannot alter
real frames. CTC blank0, finite loss/gradients and repeated-phone frame feasibility
are checked. Vocabulary is built from training phones only; unknown validation
phones count as errors. Synthetic evaluation never qualifies pronunciation.

Kaggle-only execution: oneT4 GPU, at most7200seconds,40epochs with early stopping,
batch16; feature batches at most8. Reserve4GiB remote disk and2GiB GPU memory;
abort on nonfinite state or resource exhaustion. Input is a private allowlisted
copy of the original encoder's five model files plus hashes. No credentials or
user audio are uploaded. Frontend version1.0.3 matches the VPS; CUDA CTranslate2
runtime may differ and is explicitly fingerprinted. CPU inference on original
VPS models must be separately validated before any candidate promotion.

Write progress after feature batches and epochs; save the best head, vocabulary,
source/split manifests, versions, hashes, resources and decision. Monitor the
actual remote run to terminal status. Download only bounded head/reports to VPS,
whose512MiB disk reserve remains. Human acoustic release qualification and all
existing correctness/negative/latency guards are still mandatory. Production and
UI remain unchanged during training; no APK is released from this experiment.
