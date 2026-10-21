# Zero full-sequence collisions still miss a local pronunciation contrast

The complete published CROTTC-IF bundle ran successfully, but the observed
configuration is not qualified for live Qari pronunciation grading. Neither
native decoder produced an identical full-ayah sequence across the public
correct/error labels. Inspection at the labelled word nevertheless found a
counterexample: an incorrect Qul clip and two correct clips all begin with the
same native acoustic phones `q U l h`. Extra and repeated output elsewhere can
make whole recordings look distinct while their local pronunciation contrast is
still missing. Do not interpret the zero-collision count as detection accuracy.

No backend, frontend, deployed model, threshold or APK changed.

## Frozen native experiment

Private Kaggle `telethonfool/qari-crottc-if-screen-20261021` v1 completed 39 cases:
the fixed 36 public contributor-labelled Ikhlas recordings and three synthetic
non-speech controls. Comparing the first wrapper result with the unmodified
native file helper required one additional pass, giving 40 encoder/search passes.
No training, reference prompt, external language model or threshold selection was
performed. Extra was not used as an independent test because this model already
trained on that corpus.

The selected [complete author bundle](https://huggingface.co/Haopeng/iqra_CROTTC_IF_k3/tree/8ec7ac50c3ded8bda412073a893657556c2aba8d)
includes its native inference code, Conformer/Transformer, WavLM configuration,
labels and explicit Apache-2.0 model license. Its small files match the pinned
Hugging Face Git blobs; nine nonweight files additionally match the author's
SHA256 manifest. Large weights were downloaded only on the remote worker:

- `model.ckpt`: 87,135,139 bytes, SHA256
  `5ac6c370a7c9b755817e567fcbe2ca46c4d240a574c7b87cf17b02634ed5c426`.
- `perceived_ssl.ckpt`: 1,262,009,603 bytes, SHA256
  `fac17437e057b8f5d798e39a3f444b993da3b69f0f3f0c7681ded848146eb6a0`.

The unmodified native `IqraIF` implementation loaded 323,286,990 inference
parameters with its strict component and projection-alias checks. All saved state
values, including retained training heads, were checked finite before loading.
Weights-only loading, mmap, file checksums and an offline constructor were used.

Both native outputs were retained: acoustic greedy and joint beam decoding with
acoustic weight 0.9, decoder weight 0.1, beam 10, temperature 1.1 and maximum
decode ratio 0.3. Native filtering removes only blank0/EOS1/BOS69. Unmapped class70
remains visible. Native waveform normalization uses `F.layer_norm`; no output
normalization, word repair or generic repetition collapse was introduced.

## Measured results

| Measurement | Result |
| --- | --- |
| Native helper token parity | Pass, both acoustic and joint IDs |
| Full-ayah cross-label collisions | 0 acoustic; 0 joint |
| Empty / unmapped Quran decodes | 0 / 0 for both decoders |
| Silence raw phone counts | Acoustic 8; joint 28 |
| Noise raw phone counts | Acoustic 3; joint 28 |
| Tone raw phone counts | Acoustic 2; joint 28 |
| Runtime | 146.48 seconds, including bootstrap/downloads |
| Remote peak RSS | 4,216,400 KiB, approximately 4.021 GiB |

The acoustic counterexample is contributor-labelled incorrect `ID279V1F`, versus
correct `ID3V1T` and `ID6V1T`. All begin `q U l h`. Mean native emission
probabilities for q/U/l are:

| Clip | q | U | l |
| --- | --- | --- | --- |
| ID279V1F, labelled error | .9423 | .9090 | .9076 |
| ID3V1T, labelled correct | .7538 | .6164 | .9155 |
| ID6V1T, labelled correct | .8181 | .9169 | .8749 |

Thus retaining correct lower-confidence phones while raising a single confidence
threshold cannot resolve this example. This does not prove identical posteriors
or establish a calibrated false-accept rate. The contributor labels have not been
independently re-annotated by Qari; the result is a local diagnostic, not expert
proof of every spoken phone.

Joint outputs contain extensive repeated phones, and both decoders emit sounds
on non-speech. These controls have no connection to live WebSockets/cursors and
are not live negative-control tests. Existing lexical confidence, speech, cursor
and UI guards must remain in place.

The separate standard-library verifier recomputed source PCM identity, labels,
ID-to-phone mappings, emission ranges/confidences, collision counts, control
counts and frozen settings from retained outputs. It passed. The wrapper matched
the untouched native helper, so the local failure was not invented by reporting.

## Reference-library check

Private `telethonfool/qari-crottc-ref-libraries-20261021` v2 completed the fixed
four diagnostic clips on remote CPU with Torch/TorchAudio 2.6.0+cpu, matching
TorchVision 0.21.0+cpu, SpeechBrain 1.0.3 and Transformers 4.57.0. Both acoustic
and joint phone IDs match the original GPU output for **all four clips**. The
incorrect/correct Qul prefix `q U l h` persists. Acoustic emission frame spans
also agree; the largest change in a mean phone probability is below 0.00010.
Changing these libraries did not repair the observed local contrast.

Version 1 failed before inference because the isolated Torch 2.6 target imported
Kaggle's incompatible ambient TorchVision (`operator torchvision::nms does not
exist`). The corrected launcher uses the [official matching package versions](https://pytorch.org/get-started/previous-versions/),
checks all four package paths, and resolves the lazy WavLM import before weight
downloads. No native model code, audio, weights or decoding settings changed.
The failed source/logs were preserved rather than counted as recognition results.

The successful run took 125.23 seconds including bootstrap/downloads, with peak
remote RSS 3,764,564 KiB (approximately 3.590 GiB). An independent standard-library
verifier checks the four IDs, protocol/prior-output hashes, runtime versions,
sequence comparisons and resource limits. It passed. This is diagnostic parity,
not fresh accuracy qualification or a VPS/live latency measurement. Python 3.13
still differs from the author's Python 3.10; device and main versions changed
together. No remote run remains active from this experiment.

## Runtime and data limitations

The actual initial runtime was Torch/TorchAudio 2.11.0+cu128, SpeechBrain 1.0.3,
Transformers 4.57.6 and NumPy 2.2.6 on Tesla T4. The author specifies Torch 2.6.0
and Transformers 4.57.0. A separate four-clip main-library diagnostic completed
as described below.
Do not claim that this screen reproduces the author's historical F1, or that it
rules out other training/runtime configurations. A source inspection ruled out a
suspected RoPE handling mismatch: inherited SpeechBrain 1.0.3 `encode`/`decode`
already implement the relevant handling. No patch was made for that hypothesis.

TorchAudio 2.11 removed its legacy backend enumeration. A recorded compatibility
shim returns an empty enumeration for SpeechBrain's old warning check. It does
not advertise a working backend or process audio: original source audio is read
and verified with SoundFile as mono 16k, so no resampling is performed.

The frozen cohort has been reused during research, with no verified third-party
training/speaker independence. Model selection requires fresh qualification.
The public bundle's archived results explicitly do not identify the exact settings
of a reproduced fresh full test. No VPS/streaming latency was measured here.

A conservative new Extra label audit found 74 training and 4 validation recordings
with exactly one internal short-vowel-quality substitution; its existing test role
contains zero positives under that exact filter. Allophone-only changes and final
vowel deletions were excluded, and `@` was not interpreted as a label. This subset
cannot establish independent vowel detection performance. A broader audit that
retains one-to-one vowel substitutions forced on every optimal edit path gives
the same 74/4/0 positive counts; this is not merely an exact-Hamming-filter gap.
There are no canonical word boundaries or independently checked audio labels.
No classifier was trained
on it, and no held split was silently rearranged to make an experiment pass.

The separate expert `IqraEval_Test_GT/labels_test.csv` remained authenticated HTTP403
at 2026-10-21 10:22 UTC. Approved Extra access does not grant that separate access.
The user must review its conditions personally; no new token was requested and no
conditions were accepted on their behalf.

Durable evidence:
`/home/innocent/qari-training-artifacts/crottc-if-screen-20261021/` contains the
frozen protocol, code, provider privacy/source proof, logs, verified predictions
and `word-level-rejection.json`. The earlier source audit is under
`published-phone-screen-20261021/`. Reference v1 failure and v2 verified output,
source/privacy proof and emission comparison are in `crottc-if-reference-20261021/`.
Keep the production pronunciation availability
flag false; the user goal is not complete.
