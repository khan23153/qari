# Qari — working context and VPS handoff

Last updated: **2026-10-19, 09:29 UTC**. Later progress and exact evidence are appended below. Paths refer to this VPS.
This file records verified runtime state, historical evidence and unfinished work
separately. It contains no passwords, API tokens, OAuth codes or signing secrets.

## Current outcome — read first

Backend repair **`0c7562b0ee35cee33f9e1884ac5f8e9a6974a37d`** is deployed.
It retains strict lexical correctness from afe3dc6 and adds atomic recovery of
2–3 adjacent unresolved words, proven by two native decodes at the same audio
occurrence between original confirmed anchors. No confidence/model/cursor change.
**900 backend tests passed; 1 optional skip.** Fourteen saved recording/control
replays passed: repeated Fatiha live23→27/29, Baqarah live148→150/final166→167
of230, full Ya-Sin724/725 unchanged. Some decodes remain incorrect/unconfirmed.
Public paced WSS **9/9 checks passed**, including normal Fatiha29/29, repeated
Fatiha27live/28final, Tilawat Ikhlas15/15, partial4words, and negative controls.
Owned savedPCM is byte-identical, everyayahmarker remains, allMATCHEDwords use
strict native identity/confidence. Running container healthy,0restarts/0OOM;
no transcribe/loop/final failure events since deployment. Prior193Fluttertests
apply to the unchanged UI source from PR34; no newAPK.

**Pronunciation/grammar grading is still unresolved.** ASR/normalization loses
short vowels and shadda; high word confidence cannot certify adaegi or tajweed.
Baqarah and repeated-phone recognition still have misses. Full repetition-warning
work remains in its separate unqualified worktree. Summary UI source distinguishes
matched/unconfirmed words and unavailable pronunciation, but **no new APK was
released**: existing signing certificates differ and a compatible release key is
not configured. Existing APKs use the deployed backend without reinstalling.
Baseline pronunciation preparation is isolated on `fix/acoustic-pronunciation-20261018`
in `/tmp/qari-lexical-precision-20261018`. Actual public labelled audio reproduces
false acceptance: all16 contributor-labelled vowel-error targets were matched,
and3of8 expert-labelled incorrect full-ayah recordings were fully word-matched.
The existing native phonetic model also misses errors; it is not qualified to grade.
A new frozen-encoder CTC pilot completed40epochs on95 synthetic training clips with
32 unseen-voice/text-group validation clips. Best synthetic phoneme error33.55%;
this is feasibility evidence only. Corrected-cache rerun also completed40epochs with the same best33.55% error,
510.35MiB memory peak and no OOM. Pilot-stage test suite: **960passed,1optional
skip**. All36 human inference diagnostics completed; phoneme errors remain and no
pronunciation candidate qualifies. **No experimental model is deployed.**

**Current active work:** direct human word-error classifier, isolated branch
`fix/human-word-error-20261019`, worktree `/tmp/qari-pronunciation-gpu-20261018`,
draft [PR38](https://github.com/khan23153/qari/pull/38). This is an offline Ikhlas
research experiment, **not deployed** and not full-Quran pronunciation grading.
Code `4973de4` passed 1,025 tests / 1 skip and both GitHub CI runs. Actual private
T4 version1 stopped before training because identical PCM crossed participant
IDs `187` (test) and `193` (train). This prevented leakage; no epoch ran. A full
pretraining audio audit now quarantines all clips of every duplicated participant;
bounded ordered four-source prefetch reduces measured download waits. Three new
regressions are GREEN; full suite 1,027 passed / 1 skip. Version2 is submitted and
queued; no epoch yet.

Original CPU reserved features are ready for 35 human clips, using the same new
44.1k-stereo→16k-float resampling recipe; one conflicting annotation quarantined.
The experimental classifier is trained on complete ayah clips, not qualified for
live partial words, app delay, or any other surah. Keep all production guards.

**Earlier completed work:** larger private GPU phoneme experiment in
`/tmp/qari-pronunciation-gpu-20261018`, branch`fix/pronunciation-gpu-training-20261018`,
draftPR37 https://github.com/khan23153/qari/pull/37. Code`adadd63` (FP32fix).
Fullsuite996passed/1skip; earlierstandaloneML/API510passed/1skip; latestGitHubCIbothpassed.
Kaggle`telethonfool/qari-audio-only-phoneme-ctc-20261018` version2endedERROR atfirstgradientstep after8192train/512held features. Version3
COMPLETE provedAMPoverflow andFP32stability onidenticalPCM. Version4fullFP32run
COMPLETE:18epochs,best10,syntheticPER14.21%; human36+expert14diagnostics
remainunqualified. Experimentalheadwasrejectedforproductiongrading. OriginalCPU held-out human features36/36ready.
Kaggle2.2.4 CLIcontainer authenticated;30GPUhours were available at22:07.


VPS Hugging Face authentication now works as **Shaikhaffan**, verified using the
previously authorized credential through a hidden terminal prompt. Token file is
`~/.cache/huggingface/token`, mode0600; never print or copy its value. Both corrected
human-label datasets still return403: this account is not on their authorized list.
The user needs to request/accept access in that same HF account at:
https://huggingface.co/datasets/IqraEval/Iqra_Extra_IS26 and
https://huggingface.co/datasets/IqraEval/IqraEval_Test_GT .
**No new token or login is required.** Public synthetic data cannot replace human
pronunciation qualification. See
section11 and the final progress entry for exact state and next work.

## 1. What the user wants

- Qari is a Flutter Quran app with a Python backend, live at `https://aiquranic.com`.
- User selects a surah/page, recites continuously, and expects accurate word tracking
  with low delay, including recognition of repetitions and deliberate mistakes.
- Both Hifz and Tilawat are being tested by multiple people using the shared APK.
- Hifz must reveal **confirmed words only**. Every ayah marker remains visible.
  Mistakes and unreached text belong in the review/summary; do not reveal an
  unconfirmed word just because the cursor passed it.
- Incorrect or repeated speech must not complete a page. Silence/wrong surah must
  not invent progress. Keep the current confidence and speech-activity guards.
- App is free and must have **no ads**. The earlier “paid later” wording was
  ambiguous; do not infer approval for a paid feature or change model licensing.
- Avoid memory crashes. Do not replace models or launch large training/downloads
  simply because a test failed. Do not train on the user's held-out test recordings.
- User prefers autonomous investigation and concrete results over repeated approval
  questions. They cannot remember the exact older repetition session or the exact
  word/time from the latest deliberate pronunciation tests. Do not repeatedly ask.

## 2. Latest report and what the logs actually establish

On October 18 the user reported that testers intentionally changed grammar or
pronunciation/adaegi, but Qari still marked the word correct. They tested both
Hifz and Tilawat. The exact changed word/surah/time is **unknown**.

Audit directory: `/home/innocent/qari-training-artifacts/tester-audit-20261018/`.

| Evidence | Observation |
| --- | --- |
| Available recitation log window | Oct 16 11:23 through Oct 17 16:47 UTC |
| All session starts in that window | 71; includes 5 known automated public checks |
| Sessions with app capture diagnostics | 66: **39 memorization/Hifz, 27 tracking/Tilawat** |
| App version/build in those diagnostics | `1.0.49`, build `77` |
| Surah starts represented | 1, 2, 96, 103, 106, 109, 112; pages may include further surahs |
| Retained session results and audio | **51**, copied before metadata expires |
| Results claiming pronunciation/tajweed assessment | **0**; availability flags are false |
| Results containing word-error verdicts | 17; these are decoder/matcher verdicts, not teacher labels |
| Results with no evaluated words | 12; stopping early/no recognition is not automatically a mistake |
| ASR failure events in the audited window | No `stream.transcribe_failed`, `stream.loop_transcribe_failed` or final transcription failures found |
| Other connection event | One `ws.stream.disconnected` |

Important files in the audit directory:

- `recitation-log-redacted.json`: allowlisted per-pass text, cursors and events.
- `log-overview.json`, `audit-findings.json`: session/mode/event counts.
- `retained-session-results.json`: retained metadata and full result payloads;
  ownership identifiers were excluded from metadata.
- `session-audit-summary.json`: per-session counts, times, modes and reported errors.
- `audio/<session-uuid>.wav`: **actual saved phone recordings**, not synthesized fixtures.
- `pronunciation-policy-proof.json`: running-code normalization counterexamples.
- `accepted-text-variant-audit.json`:35 distinct expected/accepted-text pairs;
  includes valid orthographic variants and suspicious lexical acceptances.
- `running-source-proof.json`, `host-inventory-redacted.json`:
  running source hashes and deployment/resource inventory.
- `cli-access-checks.json`, `verified-health-checks.json`:
  current authenticated-read/health checks.
- `artifact-directory-index.json`: complete top-level historical artifact directory index.

**Actual confirmed limitation:** live acceptance is primarily lexical ASR matching,
not a qualified acoustic pronunciation assessment. The production normalizer strips
harakat, including short-vowel distinctions. Directly executing the running code
shows `أنعمتَ` and `أنعمتُ` both become `انعمت`; `إيّاكَ` and `إيّاكِ` both become
`اياك`. These are text-only demonstrations of information loss, not proof of what
a particular tester said. The audited pre-afe3dc6 matcher also had broad spelling/article/alef/phonetic
tolerances; production now uses strict correctness with exact published spelling aliases. ASR can output the expected written word despite a spoken error.
High decoder confidence is not calibrated proof of correct pronunciation.

Therefore **a green word currently means accepted recognized text**, not verified
makhraj, harakat, shadda, madd, tajweed or grammar. The backend already returns
`pronunciation_available=false` and `tajweed_available=false`; do not invent scores.
The specific reported acoustic false acceptance remains unverified without a
known altered-word label or qualified review of the saved audio.

**Separate concrete matcher issue found in saved results:** some mismatched native
texts were nevertheless marked `is_correct=true`. Examples include `الكافرون` →
`القافلون` (4 results), `الكافرون` → `الطافلون` (1), `الكتاب` → `الختام` (1),
`اهدنا` → `اهدينا` (2), and `المغضوب` → `المغدوم` (2). Do not classify all35
pairs as errors: `الرحمان`/`الرحمن` and Quran spelling variants are expected.
These saved verdicts establish overpermissive **text acceptance** as a concrete
debugging target; they do not establish whether each mismatch originated in the
speaker or the decoder. Preserve the linked actual recordings and create separate
negative regression cases for distinct words versus valid spelling aliases.

Examples useful for follow-up, all on October 17 UTC:

- `58f2b8a7-1313-4f41-9274-1c46cd8fddd7`, 13:47, Fatiha/Hifz:
  29/29 lexical matches, 29.013s; pronunciation not assessed.
- `62736b18-0881-4f3a-811a-7753f8386b0a`, 16:46, Fatiha/Hifz:
  21 accepted words, 27.632s; the remaining eight were unconfirmed, not a full pass.
- `7ab7e04b-27f2-4f79-abdb-b9aa32c34be5`, 12:10, Baqarah/tracking,
  selected page 127 words: 125 matches, one reported `يكذبون` → `يكسبون`,
  one unconfirmed. This demonstrates a surfaced lexical mismatch, not verified
  acoustic correctness of all other words.
- Some Fatiha sessions switched speech to Ikhlas or repeated earlier phrases;
  inspect raw native text before treating their red verdicts as speaker mistakes.

## 3. Exactly what is deployed

Repository: `khan23153/qari`.

| Item | Verified value |
| --- | --- |
| Live checkout | `/home/innocent/qari` |
| Local live branch | `deploy/aiquranic-domain` |
| Backend source/image revision | **`0c7562b0ee35cee33f9e1884ac5f8e9a6974a37d`** |
| Running recitation container | `infra-recitation-api-1` |
| Image ID | `sha256:1c93eb3220a3dd980d3d7269e9eb6fcc9fa9731c0bb260dc0b54c420c7e58d57` |
| Qualified image tag | `infra-recitation-api:native-context-recovery-20261018` |
| Running since | Oct 18 15:24:02 UTC |
| Health/restarts/OOM | healthy; 0 restarts; not OOM-killed |
| Memory/swap ceiling | 6 GiB / 6 GiB total; host has no swap |
| Live source bind mount | host `ml/` → `/app/ml:ro` |
| Reference bind mount | `backend/recitation_api/reference_data` → `/app/reference_data:ro` |
| Model bind mount | host `models/` → `/app/models:ro` |
| Saved audio volume | `/var/lib/docker/volumes/infra_qari_audio/_data` → `/tmp/qari_audio` |
| Private recitation port | `127.0.0.1:8001` |

Running SHA256 values, independently rechecked October 18:

- `app.services.streaming_session`: `aa682fa2920d767527de0b9fe8e015668080738b79284e84426972fd205046dd`
- `ml.alignment.streaming_matcher`: `b8fe3b38057d76134e888e371125562b5f421fe6fb8eaaf0161320ffe8364f5b`
- `ml.alignment.native_evidence`: `334fe66dc830c2deed13f510c162885a1c86662fee0eaf84aaf8f894d42977e5`
- `app.main`: `0eb588d9e597805c4eec3603bc790a7acb12ac8d9e2e7fa6dedde30905072636`
- Exact raw spelling manifest: `703c5c9b3c03e1d2ac2b548a2cb1abd56966cd0f080432d912d5727d7d726ac0`
- `_remember_native_repetitions` is **absent** from the running container.

PR [18](https://github.com/khan23153/qari/pull/18) is merged and its original
overlap-confidence fix commit `9cfd52355fae472db702d6e9225b80915acb8c4b`
is an ancestor of the live checkout. PR
[33](https://github.com/khan23153/qari/pull/33), containing the final native
evidence and completed-phrase guard fixes, is also **merged**. GitHub `main`
was observed at `8ef92bdf1aacd474bbf26544f4a5854dc9af2265` on October 18.
Do not assume the deployed branch equals remote main. The local live branch
has diverged from its same-named remote; do not force-push or reset it blindly.

Repair PR34: https://github.com/khan23153/qari/pull/34 (strict lexical/UI source). Follow-up PR35: https://github.com/khan23153/qari/pull/35 (adjacent native-gap repair; based on PR34). Models unchanged; deployed source0c7562b. Public9case follow-up qualification complete and passing. Compare image revision and mountedML hashes for backend identity.

## 4. Backend topology, models and recognition policy

Deployment configuration: `infra/docker-compose.yml`, private values in
`infra/.env`, edge routing in `infra/Caddyfile.edge`.
Public HTTPS reaches the manually configured Cloudflare tunnel (`qari-tunnel`)
and Caddy (`qari-edge`). Core API, recitation API, Redis and PostgreSQL are Docker
services. `infra-inference-worker-1` is the separate batch worker; its code/image
is not interchangeable with the live WebSocket service.

- Core API: `infra-core-api-1`, local port `127.0.0.1:8010`.
- Recitation API: `infra-recitation-api-1`, local port `127.0.0.1:8001`.
- Redis: `infra-redis-1`; recitation metadata/results in Redis DB **1**.
- Database: `infra-postgres-1`, not publicly published.
- Current core, recitation, Redis and PostgreSQL services were healthy; tunnel
  and edge were running. Only recitation-api was recreated at12:18UTC for the tested repair; tunnel/edge/core were not restarted.
- An idle legacy Kaggle CLI container exists: `qari-conformer-kaggle-cli`.
  Old diagnostic containers include failures/exit137 and are not production
  services or evidence that training is running. Do not delete their evidence.

Current production models, unchanged during the October 18 audit:

| Host path | Role |
| --- | --- |
| `models/qari-fastconformer-pcd-rnnt-int8` | **Active**, original independent RNNT recognizer; encoder/decoder/joiner ONNX + tokens |
| `models/qari-ct2-base` | Independent Whisper/base fallback/diagnostic; model.bin SHA256 `b47c0fc7cd202c24ad4c7816e29d06c7d37c3761c1dcc91690796227df01dfa0` |
| `models/qari-v50-ct2` | Historical prompt-conditioned oracle; must **not** establish live speech correctness |

All three are mounted below `/app/models`. Current policy:

- `QARI_ML_USE_STUB=false`, `QARI_LIVE_ASR_ENGINE=fastconformer_rnnt`.
- `QARI_EVIDENCE_POLICY=tier2`: independent unprompted recognition.
- Word confidence threshold **0.55**, silence RMS **0.006**.
- Native right context **0.24s**; RNNT interval **0.9s**, startup **0.6s**.
- Measured-active-speech progress cap **2.4 words/sec**.
- Bounded live search: normal 3 words, widened 8 words, existing ayah guards.
- Independent final review uses sequential, nonoverlapping **30s** RNNT chunks
  for recordings longer than **240s**, avoiding an oversized encoder allocation.
- Model loading is offline (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`).
- **`QARI_STREAM_DEBUG=0`** restored at the idle rollout via
  `/home/innocent/qari-training-artifacts/lexical-precision-20261018/production-compose.yml`.
  The old Oct16 debug override is historical, not active.
- Production uses strict_word_identity=true, legacy word aliases disabled. Exact printed-token spelling lookup has660forms. Approximate placement keeps original DPweights but cannot award MATCHED. Final exact rereading recovery skips native insertions only with confirmed prior source and two strict following words.

`GET https://aiquranic.com/health` checks **core API only**. It does not prove the
recognition model or WebSocket works. On October 18, core public/local health and
local recitation health returned 200 with an explicit health-check User-Agent.
Default Python User-Agent public requests initially received403; the subsequent
explicit User-Agent check succeeded. New public paced recognition checks passed8cases after the12:18rollout; see appended progress and lexicalprecision/public-final-summary.json. Publichealth remains core-only; actual WSS was tested separately.

## 5. Main files and data flow

Paths below are relative to `/home/innocent/qari` unless absolute:

| File | Purpose |
| --- | --- |
| `backend/recitation_api/app/api/routes/websocket.py` | Start message, capture diagnostics, binary PCM reception, outgoing word/final events |
| `backend/recitation_api/app/services/streaming_session.py` | PCM buffers, energy/cadence/windowing, ASR, confidence/timing stitching, native evidence and final verdicts |
| `backend/recitation_api/app/main.py` | Conservative production matcher, measured-speech/silence guards, independent final merge, warmup |
| `ml/inference/fastconformer_transcriber.py` | Original RNNT native decoder |
| `ml/inference/transcript.py` | `TimedTranscript`, retaining native word confidence and emission bounds |
| `ml/alignment/streaming_matcher.py` | Live bounded alignment/cursor and final substitutions/skips |
| `ml/alignment/native_evidence.py` | Strict two-view original-occurrence proof for word repair |
| `ml/alignment/phonetic.py` | Text-derived phonetic similarity; **not an acoustic pronunciation scorer** |
| `ml/inference/asr.py` | General ASR/Arabic normalization; comparison is diacritic-insensitive |
| `backend/recitation_api/app/schemas/recitation.py` | Mobile-shaped final result/word verdict contract |
| `mobile/lib/data/services/streaming_recitation_service.dart` | Phone capture/resampling, WebSocket start/audio/stop; mode mapping |
| `mobile/lib/features/recitation/presentation/pages/live_recitation_page.dart` | Live reveal, final summary, recording/history actions |
| `mobile/lib/features/recitation/presentation/recitation_review.dart` | Final-vs-live verdict merge, reached/unreached handling |
| `mobile/lib/data/models/recitation_model.dart` | Availability flags, word verdict/error descriptions |
| `mobile/lib/core/constants/app_constants.dart` | Domain/base URL configuration |

Trace: received audio bytes → mono PCM16 at16kHz → RMS/activity → independent native
ASR words, confidence and source times → timed stitching → bounded matcher cursor
and native corroboration → confirmed WebSocket word events → independent final
recording review → final WordVerdicts → mobile summary. Debug `tier2` text is
truncated; stitched `hyp` can contain duplicates from timing revisions. Neither
duplicated stitched text nor a decoder's disagreement alone proves a user mistake.

App diagnostics commonly show capture44.1kHz, software gain3, MIC input, software
resampling to16kHz and dropped_frames0. Verify each session; do not assume every
tester used the same hardware or that zero dropped frames proves clean audio.

## 6. Fixes already applied and their limits

| Fix/evidence | Current status |
| --- | --- |
| Overlapping words retained stale first confidence, e.g .2 despite later .95 | Fixed by original `9cfd523...`/PR18, present in production |
| Quran orthographic aliases, known-word identity, native timing/gap/error repair, bounded live search | Multiple earlier qualified fixes are in current history; inspect tests/docs rather than removing guards |
| Final weak word lost stronger original native witnesses | `352156b...`, deployed and in PR33. Strict final-only unique-anchor/source-time proof, no extra live ASR |
| Shifted initial `الرحمن الرحيم` timing caused false jump past unheard Alhamd phrase | `d84454a...`, deployed. Completed phrase cannot identify an ambiguous forward jump |
| Long final recording could exhaust memory | Existing bounded sequential30s review and6GiB live service limit; retain these |
| Repeated speech warning | **Not deployed / not finished**; see next section |
| Grammar/short vowel/makhraj/tajweed errors marked correct | **Unresolved**; lexical recognition is not qualified pronunciation grading |
| Different unknown ASR words accepted through broad fuzzy/phonetic tolerance | **Fixed in afe3dc6**: strict correctness separate from approximate placement; printed spelling conversion660exactforms |
| Adjacent2–3word gaps stayed hidden despite later correct native recognition | **Fixed in0c7562b**: atomic two-view same-occurrence native proof; no cursor advance or reference-forced text |
| Exact repeated4word phrase shifted final review to wrong later words | **Fixed in afe3dc6** with bounded confirmed rereading insertion; warning events remain separate/unfinished |
| Incomplete recognized subset could show100% / ambiguous pronunciation claim | UI source fixed and tested in PR34; **APK not released** because compatible signing key is unavailable |

Current0c7562b: **900backend tests pass,1optional skip; UI unchanged from prior193Fluttertests**. All14recording/controlcases qualified. FullYaSin724/725 unchanged; old725thwas falsegreen ننكسه←نركزه. Baqarah150live167final/230; repeatedphone27live28final/29. Missingلا7/8, wrongspokencontrol6/8, silence/noise/wrongsurah0matches0verdicts. ExactfloatPCM cached native recognition replays with pinned assets/unchanged normalizer; firstcandidate had8fresh missing windows, finalformat-only requalification reused those nativecalls. Privatepeak1678.24MiB,0OOM. Public9case qualification passed with byte-identical owneraudio and noASRfailures. Pronunciation grading and repetition warning remain unfinished.

Historical evidence for **d844 before this repair**, not the current strict policy or unfinished repetition branch:

- Complete recitation API + `ml/tests` + `api/tests`: **804 passed, 1 skipped**
  (optional NeMo runtime), 2 dependency/deprecation warnings.
- Full Ya-Sin recording: cached replay verified every actual PCM window/end point,
  **941 original native calls, 725/725 live and final**. This is a matching replay,
  not a new phone capture or fresh inference benchmark.
- Fresh original-model Baqarah1–20: **163 live, 181 final matches /230**;
  **20 ASR mismatch verdicts, 29 uncertain/missing words** remain. These are not
  certified speaker mistakes. Peak private RSS approximately2.26GiB; no OOM.
- Public paced old phone16.82s recording: only4 opening words, no false later
  Rahman/Rahim reveal. Public full33.32s Fatiha:29/29.
- Public silence and Fatiha spoken while selecting Ya-Sin:0 matches and0 errors.
- These checks do **not** validate intentional pronunciation-error detection.

Evidence roots:
`qari-training-artifacts/phone-fatihah-repeat-20261016/`,
`qari-training-artifacts/baqarah-native-repair-20261016/`,
`qari-training-artifacts/live-gap-repair-20261016/`.

## 7. Unfinished repetition work — preserve it, do not claim shipped

Existing isolated worktree: **`/tmp/qari-live-gap-repair-20261016`**.
Branch: **`fix/recitation-repetition-20261016`**, based on deployed `d84454a`.
Changes are **uncommitted** and preserved. Root live ML files were not modified.

New/changed worktree files:

- `ml/alignment/streaming_matcher.py`: final-only insertion handling for an extra
  exact1–4-word copy, with original matched phrase and following context.
- `ml/alignment/native_repetition.py`: two consecutive confident mature native
  views must prove distinct original occurrences of a uniquely identifiable phrase.
- `backend/recitation_api/app/services/streaming_session.py`: retain proofs,
  independent final corroboration, existing `error_type='repetition'` review
  verdicts; keep live reveal unchanged. Preserve absolute times across long chunks.
- `backend/recitation_api/tests/test_native_repetition.py`,
  `tests/test_bounded_recording_review.py`,
  `tests/fixtures/fatihah_native_repetition.json`.
- `ml/tests/test_final_repetition_alignment.py`.
- `mobile/test/repetition_review_test.dart`: existing APK contract compatibility;
  **no mobile product-code change** was needed for that contract.

Actual repeat recordings on October16:

- `61eb2bf0-2e59-4a56-9742-2e30ced8a635`, 11:29:24.16s, first10/29 accepted;
 19 unreached. Native ASR contains the repeated Alhamd phrase.
- `e15f9469-7f5e-4e96-b541-c39b0691eb51`, 11:30:38.96s, actual app27/29.
 Repeated `الحمد لله رب العالمين`. Independent full decode recognizes correct
 `اياك` (.930) and `نعبد` (.996), but final alignment assigns them earlier
 `الرحيم`/`مالك`. This final matcher bug was reproduced.
- `0786e2cd-af82-4c2e-8b80-eee02baf397d`, 11:31:38.68s, actual app29/29.

Preserved audio: `phone-fatihah-repeat-20261016/phone-<UUID>.wav`.
Actual server results: `fresh-phone-sessions-1129-1132.json`.
Private .3s-feed replay differs in cadence: repeated case26/29, normal29/29.
Do not overwrite actual app counts with these diagnostic replay counts.

Candidate branch evidence and **blocking issues**:

- Captured case TDD first failed, then passed; subsequent complete candidate
  suite: `repetition-reviewed-full-suite.log`, **830 passed, 1 skipped**.
- Flutter focused review/Hifz checks:21 passed in the observed run.
- Candidate phone replay reported the repeated four words in review and fixed
  Iyyaka/Nabud alignment; normal/partial controls had no repetition warning.
- Candidate Baqarah replay identifies native double `مرضا` at reference85;
  counts become180 matches plus a repetition verdict. No human pronunciation
  judgment of this phrase has been established.
- **Full Ya-Sin candidate regression failed** its725 final-match assertion:
  `repetition-yasin-guard-replay.log`. The harness asserted before persisting
  detailed output. Re-run with results saved before assertions; identify whether
  changed verdicts are genuine repeats, ASR artifacts or matcher regression.
- **Important review issue still unfixed:** chunk-local timestamps are offset
  without first validating finite, ordered, nonnegative times within that original
  chunk's audio duration. A malformed negative time from a later chunk can become
  globally plausible earlier audio evidence. Add RED regressions for negative,
  beyond-chunk, nonfinite and unordered local times, then disable timed
  corroboration/fail closed for malformed chunks.
- Also test repeated speech ending exactly at Stop, without following context;
  it must not paint unheard following reference words red.
- Three earlier review findings were fixed/tested: complete live evidence must
  not skip required repeat corroboration; long review must retain native source
  timings; three copies must not suppress all repetition detection.
- **Do not deploy** this worktree until the remaining review issue and full
  Ya-Sin regression are resolved, all required tests pass, and real controls pass.

## 8. APKs and deployment identity

- Mobile source version: `1.0.49+77`; tester capture logs confirm build77.
- Pilot APK package: `com.qari.app.micpilot`; displayed app name can still be Qari.
- Local files: `releases/qari-mic-test-v77.apk`, `releases/qari-mic-test-v77.json`.
- Pilot download: `https://aiquranic.com/qari-mic-test-v77.apk`.
- Pilot APK SHA256:
  `b4d7f2d9c0e68f4ede0337a6b1d30cfefb1cd71d61adce4d62fb5f5cfa8709fb`.
- Pilot source commit: `92ba8b05fed9aee759fedc0bfbfd5bd22c30f832`.
- Successful build: https://github.com/khan23153/qari/actions/runs/38114216297 .
- `releases/app_release.json` still advertises **code75** at
  `https://aiquranic.com/v1/app/download`; distinguish it from pilot77.
- Other files: `releases/app-release.apk`, `app-mic-pilot.apk`, `qari-mic-test-v76.apk`.
- Backend code changes do not prove a new APK/model was trained or downloaded.
- Oct18 summary UI fixes are committed/tested in PR34 but not released. Existing APK publicsigners differ: see lexicalprecision/existing-apk-public-signers.json. No compatible release signingkey was found in VPSconfig or repo secrets. Do not replace stable75 or pilot77 with an incompatible debug-signed APK.

## 9. Historical model/training/recovery work

Read these host journals for detailed provenance instead of restarting old jobs:

| Path | Purpose |
| --- | --- |
| `/home/innocent/qari-active-repair-20261010.md` | Main chronological repair journal through Oct16; some early statements are superseded |
| `/home/innocent/qari-kaggle-model-recovery.md` | Kaggle/HF/Drive recovery, failed training attempts, verified training terminal status and rejected releases |
| `/home/innocent/qari-conformer-pilot-20261010.md` | Completed1590-step/3-epoch Conformer pilot; recognition gates failed, not deployed |
| `/home/innocent/qari-gpu-audio-diagnostic-20261010.md` | Completed GPU recognition diagnostics; not a trained release |
| `/home/innocent/qari-soup-compatibility-20261009.md` | User's Soup repository compatibility investigation |
| `/home/innocent/qari-word-tracking-deployment-20261010.md` | Earlier original RNNT deployment/provenance |
| `/home/innocent/qari-mic-pilot-release-20261010.md` | APK/capture fixes and pilot release evidence |
| `/tmp/qari-training-submit-20261008/` | Private audited data/manifests, Whisper training submission, smoke/export checks and terminal logs |
| `/tmp/qari-conformer-training-20261009/` | Conformer package, native exports, completed pilot artifacts and PCD adaptation diagnostics |
| `/tmp/qari-drive-recovery-20261009/` | Downloaded old Drive archives, training scripts, July tiny/checkpoint99 and rejected live gates |
| `/home/innocent/qari-training-artifacts/` |29 top-level experiment/evaluation directories; see audit's directory index |

Important conclusions already established:

- Historical V50/V13 prompt=target models can echo expected Quran text. Their
  advertised low training/eval errors do not prove independent phone recognition.
- A recovered Whisper phone pilot completed on Kaggle but regressed held-out
  WER (about.8301→.8431), failed live gates and was not deployed.
- July tiny/earlier checkpoint recovery also failed phone/independent gates.
- Soup repo: `https://github.com/MakazhanAlpamys/Soup`; old compatibility assessment
  pinned `a95bd38...`/v0.75.0. Old recovered scripts borrowed Soup ideas but do
  not establish that a current Soup-trained candidate is deployed.
- Current original PCD RNNT remains deployed. Multiple adapted/RTA/Whisper
  candidates were rejected after false matches, missing words, latency or OOM.
- Oct16 auxiliary context experiment cost116 extra ASR calls/80.476CPU seconds
  without additional matched words; rejected, prototype archived separately.
- Forcing30s chunking on the195s Baqarah fixture reduced final recall; rejected.
  Retain the current240s single-pass cutoff.
- New Maddogg Whisper-small candidate did not fix old Fa-aawaa and regressed
  another Duha clip; rejected, not deployed.
- Some phonetic/CTC diagnostics exist outside production. Native phone-alignment
  match counts/PER are not word-level correctness or calibrated pronunciation
  scores. Any new deployment needs independent negatives, license/provenance,
  speaker-independent evaluation and bounded VPS memory/latency checks.

Known held-out recordings and prepared WAV locations:

| Audio | Prepared artifacts |
| --- | --- |
| Fatiha recorder OGG `79b5ae64-37eb-45ff-8573-981154d35a3c` | `recording-comparison-20261010/`, `recorder-comparison-20261010/` |
| New Ikhlas M4A `dc1cff93-3831-41ed-9f41-4b81d64e5098` | `ikhlas-recorder-comparison-20261012/`; prefer this over uncertain old missing-huwa recording |
| Baqarah1–7 OGG `134ab738-159d-4b56-b51e-d6a48ee7d36b` | `baqarah-recorder-20261013/provided-baqarah-16k.wav` |
| Old Duha OGG `7f2cedbc-269c-47d7-8213-3e3f62e43dd5` | `duha-recorder-20261014/`; old Fa-aawaa mismatch remains |
| Ya-Sin1–10 M4A `3e7de9c6-a89e-4586-b878-554d345f8674` | Historical multisurah/Ya-Sin artifacts |
| Baqarah1–20 M4A `12905dfc-a4db-40df-8be6-168afbb1bf5d` | `baqarah-1-20-recorder-20261014/provided-baqarah-16k.wav` |
| New-speaker Duha OPUS `02cb7f8a-b042-44e9-974d-2009ca0fbf87` | `duha-new-speaker-20261015/` |
| Full Ya-Sin OPUS `d53c2b6a-aea5-45cc-b37f-ce3163259bf5` | `yasin-full-recorder-20261015/provided-yasin-full-16k.wav` |

Most table paths are under `/home/innocent/qari-training-artifacts/`. Original
`/tmp/<UUID>.<ext>` uploads can disappear; prepared WAVs/manifests are authoritative
preserved inputs. Full Ya-Sin ends at ayah83, followed by Sadaqallahul Azim;
that closing phrase must not become Quran match evidence. User previously allowed
trimming an opening A'udhu invocation for a specific Fatiha comparison; do not
silently trim or fabricate arbitrary later test audio.

### October18 pronunciation pilot assets

- Source worktree: `/tmp/qari-lexical-precision-20261018`, branch
  `fix/acoustic-pronunciation-20261018`; the new files are
  `ml/training/phoneme_ctc_pilot.py`, `ml/evaluation/pronunciation.py`, their tests,
  and `ml/evaluation/evaluate_phone_live.py` qualification integration.
- Evidence directory: `/home/innocent/qari-training-artifacts/pronunciation-qualification-20261018/`.
  `labelled-cases.json` and `labelled-native-results.json` contain the36 contributor
  clips; `expert-cases.json` and `expert-native-results.json` contain14 full-ayah
  expert-labelled clips. `pronunciation-baseline-rejected.json` records baseline
  false acceptance. Public source labels have their stated limitations.
- Experimental weights: `ctc-pilot-v2/experimental-head.pt`; report
  `ctc-pilot-v2/pilot-report.json`, `pilot-decision.json`, logs
  `ctc-pilot-v2.log`, resource samples `ctc-pilot-v2-memory.json`, exit marker
  `ctc-pilot-v2-exit.json`. V1 is preserved only for audit.
- Pilot source: public `IqraEval/Iqra_TTS` at
  `97d27c2a575739e7aaffee2518d6817d203829c9`.128clips downloaded,95train/32validation
  after one shared reference group was excluded. Validation uses Jessica voice;
  training uses Amer, Callum and Nabil. No user recording trains.
- Candidate uses only frozen audio encoding from `models/qari-ct2-base` and a small
  newly trained CTC head. Original encoder files are read-only; no text decoder is
  called. It is **unqualified**, and all candidate weights remain outside live models.
- `qualified-code-full-suite.log`: final960passed/1skip suite. `optional-dependency-green.log`:
  24pilot tests pass with faster-whisper unavailable, matching CI dependency scope.
  `runtime-recheck.json`: local recitation200, public core200 with application UA,
  healthy original0c7562b and no bounded-log ASR failures. Default Python urllib
  user agent gets403; application/browser user agents get200. This observation
  does not establish a tunnel outage, and no tunnel restart was needed.

## 10. VPS resources, tools and authenticated access

Observed October18: **aarch64, 2 logical CPUs, about11.65GiB RAM**, approximately
7GiB available at the snapshot, **no swap**. Disk about48.3GiB total with only
**1.17GiB free** before further work. Check again before exports/downloads.
Prefer a single low-priority bounded diagnostic. Do not parallelize large ASR jobs.
No `nvidia-smi`/local GPU was found. Historical training used remote Kaggle T4;
that is not proof of an active GPU session or current quota.

| Capability | Current access/status |
| --- | --- |
| GitHub CLI | `/home/innocent/.local/bin/gh`; API read authenticated as **khan23153** on Oct18 |
| GitHub config | `/home/innocent/.config/gh/hosts.yml`; private credentials, never print content |
| Google Drive CLI | `/home/innocent/.local/bin/rclone`; remote **`qari-training:`**; authenticated `rclone about` succeeded Oct18 |
| Drive config | `/home/innocent/.config/rclone/rclone.conf`; private OAuth data; historical user-owned account verified Oct9 with readonly scope after old account disconnected |
| Drive data | Historical folders `QariVPS-Backup` and `qari_ml`; recovered archives are in `/tmp/qari-drive-recovery-20261009/` |
| Kaggle CLI | **Authenticated as telethonfool** via existing qari-conformer-kaggle-cli container, Kaggle2.2.4/Python3.12.15. Host1.7.4.5 cannot use new access tokens; use container CLI |
| Kaggle historical account/job | **telethonfool**, e.g. `telethonfool/qari-conformer-quran-fp32-20261009`; old terminal logs exist |
| Kaggle helper | P4/kaggle_login_private.py uses hidden input, verifies telethonfool and caches token0600 at ~/.kaggle/access_token and CLI container private home. No credentials in job/input packets |
| Hugging Face | Authenticated as **Shaikhaffan** on Oct18 at19:43 using hidden input; private `~/.cache/huggingface/token` mode0600. Both needed gated datasets return403 until that account receives access |
| HF private helper | `/home/innocent/qari-training-artifacts/pronunciation-qualification-20261018/hf_login.py` uses hidden input, verifies identity and access, stores token0600; login complete, gated dataset access pending |
| Cloudflare | Existing tokenized tunnel container is running; dashboard/CLI account login has not been independently verified here. Do not print container args/env |
| Docker/FFmpeg | `/usr/bin/docker`, `/usr/bin/ffmpeg` |
| Flutter SDK | `/home/innocent/flutter/bin/flutter` |
| Deployment credentials | `/home/innocent/qari/infra/.env`; JWT, database and deployment values stay private |

User supplied HF/Kaggle tokens and OAuth callbacks earlier in chat. They are not
repeated here and must not be copied into git, reports, process arguments or logs.
Only credential locations, scopes/status and public account handles are recorded.
Do not replace the connected Drive account or log out again unless requested.

## 11. Next work, in priority order

1. HF login is complete. Await account access approval for the two gated human-label datasets.
   Do not repeat requests for unknown tester word/time, reuse exposed chat tokens,
   or train on the51 held-out tester WAVs. Existing36 contributor-labelled and14
   expert-labelled public probes reproduce false acceptance but are insufficient
   for a reliable word-level pronunciation release.
2. The corrected-cache synthetic pilot and36 human diagnostics are complete;
   keep their rejection decision and avoid rerunning them without a new hypothesis.
   Train/qualify a distinct acoustic detector using corrected human labels.
   Measure missed errors, false accusation, abstention and speaker/surah coverage;
   the new `ml/evaluation/pronunciation.py` gate is separate from word recall.
   Short vowels/consonants/shadda are a bounded phonemic scope; full tajweed
   needs its own labels and qualification. No expected-reference text may stand
   in for actual spoken phonemes or acoustic ground truth.
3. Improve actual recognition/context selection on Baqarah, repeated phone Fatiha
   and old Duha. Keep confidence/speech/word/ayah/source-time guards. Do not restore
   fuzzy correctness to increase match counts, or train on held-out recordings.
4. Finish the separate repetition-warning worktree: fix chunk-local provenance
   validation, review final-at-Stop controls and resolve its fullYaSin regression
   before deploying. The Oct18 exact rereading placement repair emits no warning.
5. Publish the tested summary UI only after compatible signing is resolved. Repo
   secrets are empty, VPS release key.properties is absent, and75/76/77 public
   APK signer certificates differ. Preserve installed app data and package identity;
   do not silently replace the stable APK with a newly debug-signed build. The only
   found local keystore is Flutter's unrelated engine test fixture.
6. Preserve PR34/PR35 and completed qualification evidence. Current backend is deployed;
   retain current pilot artifacts and avoid repeating completed corpus lookups,
   tests or old Drive OAuth login.
   For future deployment verify both image revision and mountedML hashes; rollback
   must restore/pin oldML as well as image. Never forcepush/reset the diverged live
   branch. Current models, API/tunnel credentials and release APKs are unchanged.

## 12. Useful commands and operational cautions

Read-only checks:

```bash
cd /home/innocent/qari
git status --short --branch
docker ps
curl -A Qari-deployment-health/1.0 http://127.0.0.1:8001/health
curl -A Qari-deployment-health/1.0 https://aiquranic.com/health
docker logs --since 10m infra-recitation-api-1
docker logs --tail 30 qari-tunnel
```

Logs may contain user speech; export allowlisted/redacted data instead of dumping
environment variables, JWTs, tunnel arguments or complete credential files.
Audio and results require owner authentication over the API; diagnostic harnesses
must use their own short-lived test identity and clean only their own sessions.

Complete offline suite, run from the isolated worktree when needed:

```bash
docker run --rm --network none --memory 1500m --memory-swap 1500m --cpus 1 \
  --no-healthcheck --entrypoint python --workdir /repo \
  -e PYTHONPATH=/repo:/repo/backend/recitation_api \
  -v /tmp/qari-lexical-precision-20261018:/repo:ro \
  infra-recitation-api:native-context-recovery-20261018 \
  -m pytest backend/recitation_api/tests ml/tests api/tests -q -p no:cacheprovider
```

The current live root has bind-mounted ML code. **Do not edit product ML files
there while preparing an untested change.** Work in the existing isolated tree.
For rollback, restore/pin the old mounted ML files as well as the previous image;
image-only rollback is incomplete. Existing overrides and deployment scripts are
under `/home/innocent/qari-training-artifacts/native-context-recovery-20261018/`; current rollback-compose.yml pins both oldmatcher AND oldnative_evidence and the oldimage tag is infra-recitation-api:rollback-native-context-20261018. Read and update pinned revisions and
acceptance checks before reuse. Never copy private environment values into docs.

Session metadata/results use a24h Redis TTL; the audio volume can retain files
longer. The Oct18 audit copied51 available recordings without changing Redis.
Earlier completed monitors/jobs are not running simply because an old session
ID is listed in a journal. The Oct16 live monitor ended at11:45 UTC. Check terminal
logs/current Docker/process state before restarting any job. Overall recognition,
pronunciation grading and repetition handling are **not all solved**.


## Progress — 2026-10-18T11:06:13.257179+00:00

User authorized fixing the Oct18 false acceptance and ongoing context updates. Created isolated worktree `/tmp/qari-lexical-precision-20261018`, branch `fix/lexical-precision-20261018`, from deployed d84454a. Existing dirty repetition worktree is preserved and will not be bundled into this first repair. Scope: separate strict production word confirmation from legacy approximate matching; preserve independently verified Quran orthographic aliases, exact-confidence/speech guards, and neutral handling of unknown ASR text. First reproduce saved accepted wrong-text pairs with TDD; then measure correct-speaker recall and false acceptance on actual saved PCM before any deployment. Live root/model files unchanged. New evidence directory: `/home/innocent/qari-training-artifacts/lexical-precision-20261018/`. Acoustic pronunciation/harakat grading remains a separate unqualified capability.


## Progress — 2026-10-18T11:16:11.045695+00:00

Strict lexical candidate:23new tests observed RED→GREEN; complete827pass1skip before8publishedspelling tests, then31focused tests pass. Captured wrongtextpairsare rejected and cleanlatestFatiha stays29/29. However first strict recording candidate is NOT qualified: Baqarahrecall117live142final/230 versusdeployed163/181; strong evidence incomplete Quran spelling coverage affectsalignment, so doNOTdeploy. Independentreview found401unmatchedpublished tokens/233distinctpairs among24857equal-length-ayah words; common الليل/اليل,الزكاة/الزكواه,الحياة/الحيواه etc. Reviewalsofoundnew8pairalias اتخذ→ااتخذ would merge interrogativewithordinaryverb; fix initial standalone interrogativehamza normalization before aliasing, with explicit collisionregression. Replacingadhoc8expansionwithindependentlysource-derivedcollision-checkedfull-corpus spellingmanifest; this is representationdata, not expected speech or ASR training. Runtime/source/modelrootunchanged. Singlebounded3500MiBprivatefirstregressionjob stillrunningfullYaSin; finishandpreserveasrejected-stage evidence.


## Progress — 2026-10-18T11:25:17.909261+00:00

Strictwordconfirmation RED→GREEN plus normalizer/collision coverage79focusedPASS. Firstincompletespellingcandidate rejected: fullYaSin721/725, Baqarah142/230; results archived rejected-incomplete-spellings-* (no deploy). ImplementedindependentlypinnedexactrawUthmani→Imlai representationlookup:660rawvariants from76327alignedtokens; neverredirectarbitrarybareASRtext. Compilercheckedin scripts/build_published_word_spellings.py; immutableJSON app/data/published_word_spellings.json. SourceQuran editions alignedperayah, onlycompilation groupsprintedvocativeboundaries, runtime1token→1token. Globalnewnormalizedredirectsdisabled(0) toavoidcollisions;existingfullcorpuslegacyaliasbuilderrunsaftercanonicalization. InitialUthmani ءأ retainsbothhamzas; actualpastاتخذcannotmatchquestionأأتخذ. Combininghamzaexampleيَسْـَٔلُكُمْ retainsaskidentitywhilebareيسلكمunchanged. IMPORTANT anyOLD nativecachecontainsnormalizedwordsfromoldnormalizer; cannotqualifynewnormalizerusingcachedtranscripts evenifPCMidentical. StartingALL-FRESH originalmodel replays bounded3500MiB/1CPU/noSwap; no models/threshold/productionroot changes.


## Progress — 2026-10-18T11:36:06.219740+00:00

Final backend candidate full suite: **849 passed, 1 skipped, 2 dependency warnings** in57.16s (backend/recitation_api/tests + ml/tests + api/tests). Independent review found no remaining important code findings after full6236-ayah check. Production strict matcher now disables legacy alias redirects entirely; exact published raw-token lookup handles660 attested variants, generated reproducibly from76327 compared units. Prior11:25 note about legacy alias builder is superseded: production aliases=0; retaining old clean aliases was a real identity bypass and has a regression test. All-fresh original-model qualification is running in private3500MiB/2CPU container; silence, seeded noise and Fatiha wrongly selectingYaSin all passed with0live matches/0verdicts. Await fullBaqarah/YaSin and detailed per-recording assessment before deployment. Source/model live root unchanged. UI summary wording refinement planned: report word matches and explicitly disclose pronunciation unavailable; no adaegi grading is implemented by lexical strictness.


## Progress — 2026-10-18T11:42:19.604350+00:00

Full-fresh strict candidate remains NOT qualified: Baqarah117live/142final versus deployed163/181, with38final errors versus20. Detailed comparison found both desirable removals (e.g. تفسدون previously accepted for تفسدوا) AND lost genuinely recognized later words. Strict identity was used for sequence placement as well as verdicts, disrupting alignment; increased error recovery also changed53of224 ASR audio windows. Preserved this candidate and all fresh results under rejected-strict-placement-* and stopped its unfinished YaSin replay to avoid wasting inference. Next isolate approximate sequence placement from strict correctness: similarity may locate a token, but only independently recognized lexical identity may receive MATCHED. Preserve word/ayah/provenance/confidence/speech bounds, and prove with regression tests plus fresh recordings. No deployment yet. Flutter summary focused29tests pass; full Flutter suite is running; existing page analyzer findings unchanged, new widget/test analyzer clean.


## Progress — 2026-10-18 11:45 UTC

Separated approximate sequence placement from strict correctness in isolated candidate. An actual Baqarah native transcript reproduces losing the final correctly decoded phrase (new test RED); placement/correctness separation makes that regression GREEN. A page of only similar-but-different tokens cannot start the live cursor or earn any final matches. 25 focused tests passed before additional guard test; full backend suite rerunning because matcher source changed. Original-model fresh qualification restarted with Baqarah first; candidate source hashes frozen. Full Flutter suite **192 tests passed**; changed summary widget and tests have clean targeted analysis. Page-level analysis reports six pre-existing unrelated findings; no claim of whole-project analyzer cleanliness. No production changes yet.


## Progress — 2026-10-18 11:47 UTC

Placement/verdict separation passed independent review. Full backend suite: **851 passed,1 skipped,2 warnings** in58.27s; added trailing native-slot regression also passes (12strict matcher tests total). Full Flutter suite: **192passed**. Fresh ASR candidate is still undergoing qualification, so any PR remains draft and no production rollout is authorized by these test counts alone. Private inference remains3500MiB/noadditionalSwap; no model/training change. UI source now labels matched words and discloses unavailable pronunciation assessment. Existing APK signing is not configured in VPS key.properties and earlier pilot was separate-package to avoid update-signature mismatch; do not blindly promote a new CI debug-signed APK over tester installations. Existing APKs can use a backend-only repair without reinstall.


## Progress — 2026-10-18T11:54:09.811431+00:00

Committed/pushed first reviewed implementation13c9925 to fix/lexical-precision-20261018; draft PR https://github.com/khan23153/qari/pull/34. Candidate image built but NOT deployed. Full fresh equal-placement candidate rejected on repeated Fatiha23live24final with5errors; Baqarah improved148live166final,21errors (15lost final greens include14different/unknown ASR text pairs and one genuine واذا). Preserved rejected-equal-placement-*; stopped unfinished YaSin. New TDD fixes: exact DP pairs score2, near placement0 (no positive correctness evidence), original mismatch-2. Strict-only final rereading insertion recognizes2–8 exact already-confirmed native words plus2distinct confident exact following words, skips only native insertion, no widened reference search or manufactured speech. Both specific regressions RED→GREEN,29focusedtestsPASS. This improves repeated-phrase alignment but does not implement repetition-warning events (separate old worktree remains unqualified). Running fresh qualification again; no live-source/model changes.


## Progress — 2026-10-18T11:57:29.329760+00:00

Priority/repetition candidate: full existing backend suite **854pass1skip1warning**; twelve additional negative rereading guards pass (26strict matcher tests total). Independent review found no concrete guard/falsegreen bypass; requested negative gates now covered. Fresh repeated phone Fatiha final restored28/29 with1ASR substitution (منهم vs عليهم); live23/29 remains versus prior strict27, so tracking is not perfect. Exact cached-window diagnostic (not new recognition) shows model actually decoding `هيا كنابد ... نستيم اهدينا` where اياك نعبد نستعين اهدنا are expected; strict correctness appropriately withholds these outputs. Window selection changes with unresolved states and affects later ASR; this needs continued model/context qualification rather than fuzzy approval. Final-only repeated-phrase skip now prevents repeated الحمد لله رب العالمين shifting subsequent review positions. No deployment yet; ongoing original-model Baqarah and fullYaSin qualification.


## Progress — 2026-10-18T12:04:43.672946+00:00

All866current backend tests pass (1optional skip,2dependency warnings), including12negative rereading gates. Scoring zero/0.5/1.0 for approximate placement is rejected on Baqarah115live161final. Exact-PCM cache probes verified unchanged model/normalizer/source-WAV identity and reused224/224actual Baqarah native decodes,46/46repeated Fatiha decodes; no fabricated transcript or cached-normalizer mismatch. These are explicitly prequalification probes, not fresh recognition or latency tests. FullYaSin replay was stopped once short-case regression became known. OriginalDP placement weights are likely preferable: preserve existing sequence positions, apply strict identity only to correctness/anchors, keep final exact rereading recovery. New manufactured preference for a later exact occurrence over an earlier near occurrence is being reassessed against native occurrence ownership; not a user requirement. Source/model live root remains d84454a and unchanged.


## Progress — 2026-10-18T12:08:57.963445+00:00

Final design retains original DP placement weights2/-2; scoring alternatives0,.5,1,1.5 rejected (last147live165final) and are not release candidates. Stronger preference for a later exact token can borrow a later reading to overwrite an earlier gap; that invented test expectation was replaced by native-occurrence guard, observedREDwithnewscoring→GREENwithoriginalweights. Existing strict match and bounded final rereading helper remain. Current complete suite866pass1skip2warnings; Flutter192pass. Qualification now replays exact cached native decodes only when sourceWAV/PCM slice bytes, model and normalizer/raw-spelling hashes are unchanged, with original-model fresh fallback; fullYaSin has no complete matching cache and is fresh. Reports final-recognition-qualification.* explicitly record cache/fresh counts; do not call allcases fresh. Two private harness-only conversion/scoping errors were corrected before qualification; invalid-list-harness-* logs are not production ASR failures. Fail-fast harness guards now prevent swallowed callback errors qualifying a recording. Runtime remains oldd84454a until final gates pass.


## Progress — 2026-10-18T12:16:41.233136+00:00

Final recognition qualification COMPLETE:14cases, no transcribe/loop/final failures. FullYaSin **724live/724final of725**,941fresh unprompted native calls; missing index578 ننكسه had previously been wrongly accepted with actualASR نركزه (priorreviewJSON proves it). No genuinely identical decoded word lost there. Baqarah148live166final/230,21model-reported substitutions,43unconfirmed; original181included14different-text falsegreens and1genuine واذا not recovered. Clean phone Fatiha29/29final (latest28live,old29live), partial4only, Ikhlas15/15, newDuha40/40, oldDuha39/40, repeatphone23live28final/29. Silence/noise/wrong-surah0matches0verdicts; omittedلاnotconfirmed and wrongspokencontrolnotcompleted. First13cases used exact cached actual-model windows with inputPCMbytes and unchangedSS/rawmanifest/model checks; YaSinall941callsfresh. Privatepeakabout2GiB,0OOM, limit3500MiB/noextraSwap. AllcasescurrentSS/matcher/rawdatahashes frozen. Report qualification-summary.json and final-recognition-qualification.json underlexicalprecisionartifactdirectory.

Additional UI bug reproducedRED→GREEN: a reached unconfirmedword couldleave100% scoreoveronlyevaluatedwords; summarynowshowsmatched/reachedfractionplusN unconfirmed instead. Pendingunreachedsuffixexcluded. All3summarywidgettestsandtargetedanalysispass; newfullFlutterreruninprogress. PublicAPKcertinspectionproves75,76,77use3different publicsignercertificates. GitHubsecretlistempty; VPSreleasekeyconfigabsent (onlyunrelatedFlutterenginefixturekeystorefound). DoNOTpromoteanewdebugsignedAPKoverexistinginstallsoraskuserstouninstall/losetheirdata. SummarysourceisreadybutAPKreleasependingcompatiblekey; backendrepaircanbenefitexistingAPK. Productionstillolduntiltestedrollout.


## Progress — 2026-10-18T12:18:45.892077+00:00

Final pre-rollout gates PASS: **866backend tests+1optional skip,193Flutter tests**, new summary targeted analyzerclean;14realrecording/negativecontrolqualificationcomplete, fullYaSin941freshcalls724/725. Candidate imagebuilt with revisionafe3dc6 and3sourcehashes matchqualification; models/thresholds/wordayahguardsunchanged. Recitation-only idle rollout now planned with pinned oldmatcher rollback because MLisbindmounted. Turn off temporary verboseQARI_STREAM_DEBUG at rollout. PublicWSS modes/audiointegrity/negativecontrolsstillpending; no claimproductioncompleteuntilthosefinish.


## Progress — 2026-10-18T12:25:42.161969+00:00

DEPLOYED AND VERIFIED bounded lexical repair: **afe3dc63abcfca5eaaba789b9df8195085cca59e**, imagesha256:e2fd5f3959afd20b4f76d1a96815b469abe642ad56e491312c1e963bc88eb80e, containerinfra-recitation-api-1 started12:18:48UTC. Actualimage label and packagedSS/bindmountedmatcher/rawmanifest hashes match14casequalification. ExistingDockerCompose recitation-only rollout,6GiB memory/6GiB total memory+swap, originalmodels/.55confidence/.006RMS/activity/ayah/provenance/30schunkguards retained; debug0. Rollbackoldimage tag infra-recitation-api:rollback-lexical-precision-20261018 plus rollback-compose.yml pins oldmatcher. Otherservices/tunnel/edge not restarted.

Complete validation **866backendpass1optionalSkip2warnings;193Flutterpass;newwidget/testanalyzerclean**. PublicpacedWSS8casesPASS: HifzFatiha29/29, TilawatIkhlas15/15, partialFatiha4only, silence/noise/wrongsurah0matches0verdicts, missingلا7/8 (لاnotinvented), wrongspokencontrol6/8 withlaterprogress. Allreadyayahmarkerspresent, everywire/finalMATCHEDstrictidentity, nativeconfidencepreserved, all8owner-audioGETPCMbyteidentical. Phonefirstwordevent~1.28s fromfixtureplaybackstart; this is saved-PCM replay, not newdevice latency or acousticaccuracy qualification. Initialsilence-only assertion requiredexplicitfalse optionalflags; actualclientdefaultsabsentflagstofalse. Preserved initialreport, correctedharnesscontract and fresh6ssilenceretestPASS; no backend sourcechange. Corepublic/localrecitationhealth200, Dockerhealthy0restarts0OOM; no stream.transcribe_failed/loop_transcribe_failed/finalfailures in deployedlogs. Publicsampledpeak~1.18GiB vs6GiBceiling.

Artifacts: deployment.json, qualification-summary.json, final-recognition-qualification.json, public-final-summary.json, public-qualification.json, public-silence-recheck.json, deployed-log-redacted.json, final-qualified-memory.json, public-qualified-memory.json under /home/innocent/qari-training-artifacts/lexical-precision-20261018/. All credentials redacted. No newAPK or trainingjob started; sourceUIreleasependingkey. Remaining: unqualifiedadaegi/grammar/tajweed, actualASRmisses onBaqarah/repeatphone/oldDuha, separate repetition-warningcandidate. Overallrecognition/pronunciationgoal is NOT claimedcomplete.


## Continuing repair — 2026-10-18T15:07:47.747899+00:00

User asked to fix remaining issues. Starting new isolated native-context investigation; productionafe3dc6 stays unchanged. Focus first on remaining live recognition/latency, then acoustic error-detector feasibility using existing assets. Do not repeat rejected matcher-score tuning or assume textconfidence provesadaegi. Compare identical phonePCM windows under7.5s and20s context, and inspect feedback from unknown/error states into laterASRwindow selection. New evidence directory native-context-recovery-20261018; exact changed-word label from testers stillunknown.


## Progress — 2026-10-18 15:20 UTC

Corrected earlier incomplete remaining-Fatiha diagnosis: actual same-PCM20s native decodes at25.2/26.1s correctly recognize اياك نعبد and نستعين اهدنا with native confidence above.55. Existing one-word anchored repair cannot repair two adjacent unresolved states. Isolated candidate adds atomic2–3word backfill using two mature same-occurrence native decodes and original matched outside anchors; no cursor/window/model/threshold changes. Focused50tests passed; first actual repeated-phone replay emitted four bounded span repairs at endpoints403200/417600. Full14case exact-float-PCM cached native replay with fresh missing-window fallback running in3500MiB/noextraSwap privatecontainer. Normalizer/PCM/windowselection AST verified unchanged outside the repair methods; pinned original RNNTassets loaded/validated. Independentcode review requested. Productionstillafe3dc6. No adaegi grading claim and noAPK/trainingchange.


## Qualified candidate — 2026-10-18 15:24 UTC

Native adjacent-gap repair final source frozen and reviewed, **900 backend/ML/API tests passed,1optional skip,1dependency warning**. All14real-audio/control replays complete: repeatedphone27live28final/29 (was23/28); Baqarah150live167final/230 (was148/166); latestcleanphone28live29final, oldclean29/29, partial4, Ikhlas15/15, newDuha40/40, oldDuha39/40, fullYaSin724/724of725 unchanged. Missingلا7/8 and wrongspokencontrol6/8 unchanged; silence/noise/wrongsurah0matches0verdicts. Firstcandidate needed8freshnativewindows for repeatedphone; finalreadability-onlyrequalification reused exactfloatPCM native hashes including thosefreshcalls. This is cachedactualrecognition validation, not newphonecapture or latency proof. Native model assets validated, normalizer/PCM/windowselection AST unchanged, sources frozen. Private3500MiB/noadditionalSwap limit, measuredpeak1678.24MiB,0OOMevents. Independent reviewer found no blockingissues after third-word negative coverage. Artifactdirectory native-context-recovery-20261018 includes qualification-summary.json, recognition-qualification.json/log/done, span-red/green logs, full-suite.log, private-memory.json and code-review.txt.

Deployment next: recitation-only existingCompose, originalmodels/policy/guards, debug0; image must include changedmain.py and session.py plus bothMLfiles. Rollback must pin oldmatcher AND native_evidence because MLisbindmounted. PublicpacedHifz/Tilawat/repeatedFatiha and silence/noise/wrongsurah/omittedword controls must pass before calling rollout verified. Productioncurrentlyafe3dc6. Adaegi/grammar/tajweed calibration remains unqualified and compatibleAPKsigningkey stillunavailable.


## Deployed follow-up — 2026-10-18 15:27 UTC

Native adjacent-gap repair0c7562b deployed15:24:02UTC, image sha256:1c93eb3220a3dd980d3d7269e9eb6fcc9fa9731c0bb260dc0b54c420c7e58d57. Runtimeapp/main,session,bothMLfiles,manifest,transcriber hashes all match qualified source; tier2/fastconformer/stubfalse/debugfalse,6GiB/noextraSwap retained. Otherservices untouched. PR35 draft basedonPR34. PublicpacedWSS normalFatiha29/29, repeatedFatiha27live28final andIkhlas15/15 PASS; remainingcontrols running. Do notcall entirepublicsuitecompleteyet. Earlier15:24entry describes predeploymentstate. Artifactsdeployment.json andproduction/rollback-compose.yml are authoritative.


## Verified follow-up deployment — 2026-10-18T15:29:21.887869+00:00

**Backend0c7562b0ee35cee33f9e1884ac5f8e9a6974a37d verified live**. PublicpacedWSS9/9PASS: normalFatiha29/29, repeatedFatiha27live28final/29 (four previously lostwords nowconfirmed), TilawatIkhlas15/15, partialFatiha4only, silence/noise/wrongsurah0matches0verdicts, missingلا7/8 and wrongspokencontrol6/8. Allword/marker/confidence/strictidentity/audioPCM/pong checks pass. Publicpeakmemory1074.05MiB,0OOM; Dockerhealthy0restarts; localrecitationandpubliccorehealth200;0stream.transcribe_failed/stream.loop_transcribe_failed/finalfailures since15:24:02UTC. Fourstream.native_span_word_repaired events observed in deployedlogs. No newAPK, modeltraining, downloadedmodel or credentialchange. Othercontainers preserved.

Privatequalification:900backend/ML/APIpass1skip1warning;14cachedactualnativePCMreplays complete, with8freshmissingwindows in firstcandidate; same normalization/pinnedassets and sourcehashchecks; independentcode review found no blockingissues. Publictests are fresh original-model paced saved-audio WSS, not newmicrophone capture. Artifactroot /home/innocent/qari-training-artifacts/native-context-recovery-20261018/: deployment.json, qualification-summary.json, recognition-qualification.json/log/done, full-suite.log, private-memory.json, public-qualification.json/log/done, public-summary.json, public-memory.json, deployed-log-redacted.json, code-review.txt, deploy_qualified.py, production-compose.yml, rollback-compose.yml, rollback-streaming_matcher.py androllback-native_evidence.py. Rollbackoldimage is infra-recitation-api:rollback-native-context-20261018; pinboth oldMLfiles aswellas image.

**Remaining, do notclaimallerrorsfixed**: (1) Adaegi/grammar/shortvowel/shadda/tajweed falseacceptance lacks teacherlabelled heldout qualification; textualASRconfidence cannotcertifyit. Existingphone-level Zipformerdiagnostics are unqualified and makeerrors oncleanwords. (2) RepeatedFatiha still27live/28finalof29; finalactualASRمنهم forعليهم isamodel mismatch, not certifiedspeakermistake. Four recoveredwordscanappear late: privateconfirmation26.1s fornativeemissions around17.4–23.1s; do notclaimdelayeliminated. (3) Baqarahstill150live/167finalof230, oldDuha39/40 andYaSin724/725; donotforcepass orlowerguards. (4) Separate repetitionwarning remainsunqualified. (5) PR34UIwordingtestedbutAPKreleaseblockedbycompatible signingkey; stableAPKunchanged.

PR35 https://github.com/khan23153/qari/pull/35 is the follow-up basedonPR34; bothCIjobs(coreAPIandrecitation/ML)passed oncodecommit. Documentation-only successor may becheckoutHEAD whileimage/source revision stays0c7562b. Userrequested continuedcontextupdates; lateststateisthisentry andthetopsections, historicalprogressisnotcurrentruntime.


## Pronunciation investigation resumed — 2026-10-18T18:45:33.887932+00:00

User explicitly requested full resolution, so priority is now acoustic adaegi/harakat falseacceptance. Production0c7562b remains unchanged. New isolated branchfix/acoustic-pronunciation-20261018 in /tmp/qari-lexical-precision-20261018; evidence /home/innocent/qari-training-artifacts/pronunciation-qualification-20261018. Existing Zipformer251-token model and corpus pinned to upstream2f261746, no newmodeldownload. Public upstream docsconfirm short-vowel probability comparison is distinct from ASR text and thresholdheuristics are not calibrated correctness probabilities. Its actederror recordings areprivate; notavailable. IqraEval/QuranMB.v2 accessible butfirstrowsonlyID/audio, no truephonemelabels; cannotservegroundtruthlocally. Found CC-BY-4.0 MuazAhmad7/Surah_Ikhlas-Labeled_Dataset revision973b5ef1d1532bcbe7e9a5a5b0dce125cc4d0dac with1506metadata rows/1500audiofiles and errorword/explanation inclharakat; contributorlabels, not independentlyteacherverifiedhere. Boundeddownload/16kresampling for vowelerrors andcorrectcontrols underway withsourcePCMhashes, speakerdev/heldsplit, no trainingoruseraudioaugmentation. RetaSygoldenexpertfilter timedout; noexpertlabelsubset claimed. Need demonstrate actualbaselinefalseaccept then compare independentnativephones. No productcode/deploy/thresholdchange yet.


## Acoustic falseacceptance evidence and bounded pilot — 2026-10-18T19:20:47.188230+00:00

P3=/home/innocent/qari-training-artifacts/pronunciation-qualification-20261018.36contributor-labelled Ikhlasclips(16error/20correct) actuallyran originalnativeASR+existingpinnedZipformer, all36uniquePCM.16/16labellederrorwordswerelexicallymatched; naivephonetic-equality alsofalseacceptedall16, including12/12inheldspeakerpartition. Noexperimentalphoneticmodelqualified. Sourceannotationsnotindependentlyrelabelledandupstreamtrainingoverlapunknown. P3/labelled-native-results.json, pronunciation-baseline-rejected.json, evaluation-labels.json preservefulloutputs. LowcontextsyllableCTCreset experimentunstableoncorrectclips, rejected; local-phones-results.json/log. Privatepeak836.89MiB/noOOM.

Independent RetaSyexpertgoldenmetadata:24pages/2400rowsyield22goldens;14fullayahfixtures(6correct/8incorrect) acrossseveralsurahs ranbothnativeengines.3/8incorrectutterancesgotallwordslexicallymatched; naivephonetic-equality alsoacceptsoneexpertincorrectclipanddisagreeswith4/6expertcorrectclips. Labelsareutterancelevel, so donotclaimlocalisedwordaccuracy. P3/expert-cases.json, expert-native-results.json, expert-summary.json. PartialAyatalKursiclipswereexcludedwithreason.

Newrepositorycodecurrentlyonlyisolatedbranchfix/acoustic-pronunciation-20261018. Addedhumanlabelledpronunciationqualificationseparatefromwordrecall; defaultengineeringgates100bad100good,5speakers3surahs,20bad20goodpervowel/gemination/consonantclass, recall.90/precision.98/FPR.02/coverage.95 perclassandaggregate, knownspeaker/PCMholdoutinventories andtestedbundleSHA. UnknownupstreamtrainingmustremainNone, neverpretendemptyknowninventory. Addedforce-passmaxcursorcapturebeforefinalize topreventtransientcompletionbeinghidden. Initialfull925testspassed; laterreviewfixeshave38focusedpass; newpilot17focusedpass, freshfullsuitepending. AllreviewfindingsbeingfixedbyRED/GREENregressions; nograde/modelclaimfrompytestcounts.

HFVPSloginmissing; IqraEval/Iqra_Extra_IS26andIqraEval_Test_GTarecurrentlygated. SecureownterminalhelperP3/hf_login.py useshiddenreadtokenand0600cache, neverpastecredentialsintoChat/git; userquestionpending. KaggleAPIauthalsofailsinsideexistingCLIcontainer. PublicIqra_TTSandIqra_trainmetadataavailable; syntheticactualphoneme_misexists, humanmispronunciationlabelaccessstillpending.

Boundedresearchpilotprepared: bypassexistingWhisperbase textdecoder; frozen512D/20msaudioencoder withnewsmallCTCphonehead usingonlyexplicitphoneme_mis frompublicsyntheticIqra_TTS. Max128shortclips,3trainingvoices+Jessica validationvoice, canonicalreferencegroupsdisjoint; noheldoutuserrecordings train. Nativeencodeofknown4sclipverifiedshape1x1500x512, actual203framesretained; Whisperrequires3000melinputframes, paddedencoderframesareexcluded. Spec/planin docs/superpowers/{specs,plans}/2026-10-18-acoustic-phoneme-pilot.md. CurrentTTSfixturepreparationrunning; traininghasNOTstarted. P3/run_ctc_pilot.py willrun3500MiB/noextraSwap,2CPU/nice19, noGPU, withlivelog+memorymonitor. Candidateisexperimental, neverautopromoted; finalhumanphonemelabelqualificationrequired. Productionremains0c7562bunchanged; noAPK/sourceUI/model/tunnelchanges.


## Frozen-encoder pilot started — 2026-10-18T19:23:57.149905+00:00

128publicsyntheticIqra_TTSclips prepared(32eachAmer/Callum/Jessica/Nabil), immutabledataset97d27c2a575739e7aaffee2518d6817d203829c9; phoneme_misusedasalteredphones, canonicalphoneme_refneverfallback. DataoutsidegitP3/tts-pilot-cases.json andtts-pilot-16k; nosourceuseraudio.56focusedtestsPASS(gate38+pilot18), inclrealPyTorchCTC oneepochfakeencodersmokeprovesencoderonly/no transcribecalls andnoqualificationclaim. Fullbackend/ML/APIruninprogress(P3/final-full-suite.log). Independentwholebranchreviewrequested. ActualboundedCPUtrainingstarted withP3/run_ctc_pilot.py, containerqari-phoneme-head-pilot-20261018, logfileP3/ctc-pilot.log, metricsP3/ctc-pilot/pilot-report.json, resourceP3/ctc-pilot-memory.json. Featureextractionfirst(Whisperbaseencoderonly,notV50), then40epochs smallframeCTChead.3500MiB/noextraSwap,2CPUs/nice19; noGPUneededforpilot. No modelpromotion, humanqualificationpendingHFuseraccess. Needcontinuewatchinglogs/resourcesuntilexit; donotabandonjoborcallittraineduntilactualepochoutputandexit0.


## Acoustic pilot first result and review corrections — 2026-10-18 19:30 UTC

First bounded pilot finished40epochs, exit0:95trainingclips/32Jessica validationclips after1reference-overlap removal. Greedy syntheticPER156.42% beforetraining tobest33.55%, final33.78%; finaltrainloss.02037. No unknownvalidationphones; peak609.90MiB, noOOM. This is syntheticfeasibility only, not qualifiedhumanpronunciation; no productionpromotion. Review found frontendcache omitted actualpreprocessor_config.json and releaseevaluator finalizecouldpersistfixtureaudio/Redisrecords. Bothreproducedin8REDtests thenfixed: completefrontendfile/effectiveparameter cacheidentity withfixed16k/160hop/80melvalidation; evaluationsessionssuppressaudio/recordpersistencewhilekeepingactualfinalverdicts. Also boundWAVframesbeforeallocation andreportvalidationCTCloss, absentifunknownphonepreventsfullscoring.60focusedtestsPASS. Pilotv1usesoldcacheidentity, preservedforaudit; rerunv2willusecorrectedidentityandfreshfeatures, not relabelv1results. Fullsuitebeforefix954pass1skip; freshpostfixsuitepending. Production0c7562bunchanged.


## Reviewed code verification — 2026-10-18 19:31 UTC

Both important independent review findings fixed and all8regressions nowGREEN. Focused tests60pass; fresh entire backend/recitation_api/tests + ml/tests + api/tests: **960passed,1optional skip,2dependency warnings in55.43s**, exit0. Full log P3/reviewed-full-suite.log; red/green evidence P3/review-fixes-{red,green}.log; review record P3/code-review-final.txt. Corrected-cache pilotv2 currentlyextracting127features; originalpilotfinishedwith0OOM. Productioncontainerrechecked19:30healthy,0restart/OOM, original0c7562b. HFtokenfileabsent; no useraccessreplyyet. Usertestrecordings nottrained or uploaded.


## Pronunciation pilot decision — 2026-10-18 19:37 UTC

Corrected-cache v2 finished all40epochs with exit0.95training clips and32 held
Jessica clips; one reference-group overlap was removed before training. Best
synthetic greedy phoneme error was **33.55% at epoch16**, validation CTC loss1.4374.
At epoch40 training loss fell to.02037 while validation loss rose to2.0073 and
error remained33.78%: more epochs on this small sample did not solve validation.
The best checkpoint is retained, not the last checkpoint. Native encoder, config,
preprocessor config, frontend source and effective timing are fingerprinted in
`ctc-pilot-v2/pilot-report.json`; v2 resource peak510.35MiB, no OOM.

Fresh human diagnostic then ran all36 previously held-out labelled clips with
**no training or expected-phone prompt**, exit0, peak445.94MiB and no OOM.
`pilot-human-diagnostic.json/log/done` and `pilot-human-f-contexts.json` preserve
outputs. Concrete limitations: error-labelled ID14V4F still emits `k u f u w a`,
while correct-labelled ID4V4T/ID5V4T emit `k u f w a n`, dropping the target vowel.
Some clips lose `f` entirely. These are model transcriptions, not assertions about
what a speaker actually pronounced; no per-phone human truth is available here.
A missing or incorrect model phone must not become a confident user accusation.
Candidate is therefore **REJECTED for production grading**, not force-passed.
Full decision: `pilot-decision.json`. No live model/threshold/UI changes.

Code's final complete suite after optional-dependency portability correction:
**960passed,1optional skip,2dependency warnings in55.87s**, exit0, log
`qualified-code-full-suite.log`. Without faster-whisper installed, all24 pilot
unit tests also pass; genuine RED6failures are preserved in
`optional-dependency-red.log`, then GREEN in `optional-dependency-green.log`.
Both earlier important independent review findings are fixed; feature identity
uses the actual extractor class source while keeping pure unit tests independent
of inference installation. This preserves v2's numeric frontend and cache key,
verified by human inference loading its exact feature bundle successfully.

Core public health200 with application/browser UA; default Python urllib UA403.
Local recitation health200, Docker healthy,0restart/OOM; original deployed backend
revision0c7562b remains. Last10000 log lines since deploy contain zero
stream.transcribe_failed/loop_transcribe_failed/finalize_failed events.
`runtime-recheck.json` records this bounded observation; no claim of logs beyond
that bound. Tunnel/edge are running and were not restarted.

Actual next dependency is corrected human spoken-phone data. HF login is still
absent and access to gated IqraEval/Iqra_Extra_IS26 + IqraEval_Test_GT is pending
user's account action. Secure helper path and access pages are above; no token is
in git/context. Do not repeat the unknown tester word/time question, train on
held-out user audio, lower existing confidence guards, or promote this pilot.
The full pronunciation/recognition goal is **NOT COMPLETE**. Tested qualification
code and the bounded pilot are being committed on the isolated branch for review.


## Review branch and CI follow-up — 2026-10-18 19:41 UTC

Committed/pushed research code476ee43603397039755151b9dce97c428632c5da on
`fix/acoustic-pronunciation-20261018`. Draft PR **https://github.com/khan23153/qari/pull/36**,
based onPR35 (`fix/native-context-selection-20261018`). It is draft because the
pronunciation outcome is unfinished; do not merge/promote a model from test counts.

GitHub CI caught a new test-environment issue: ML tests run in their own process,
without the recitation conftest adding `backend/recitation_api` to sys.path.
The async evaluator regression failed importing `app`; the combined local suite
had already loaded it. Fixed the regression to explicitly add its actual backend
path through monkeypatch, restoring the path at test teardown. Actual failing CI
log: `P3/github-ci-failure.log`. Fresh standalone CI-shaped `ml/tests api/tests`
now **475passed,1optional skip**, log `ci-standalone-green.log`; final combined suite
passed960tests,1optional skip,2warnings in54.27s with exit0 before pushing
this small test-only correction. Log: `final-ci-corrected-full-suite.log`. This is a test import
failure, not a production ASR crash. Source model/training results are unchanged.
Original overlap confidence fix9cfd523 is already an ancestor of current code;
no duplicate cherry-pick was required. Runtime source hashes were rechecked and
still match the qualified original0c7562b deployment.


The bounded pilot plan is complete, including independent review and documented
rejection. This does **not** complete the user’s pronunciation goal. Follow-up work
needs corrected human phoneme access, training and held-out acoustic accuracy;
all original recording/control, memory and latency gates must be retained.
PR36 stays draft. The test-path correction and handoff are being pushed; GitHub
CI for that code must be checked before claiming remote verification succeeds.


## HF authentication and remote verification corrected — 2026-10-18 19:45 UTC

Important update superseding earlier login-unavailable notes: existing user-provided
HF authorization was verified via getpass/hidden stdin, with no token in process
arguments, output, git or this file. Account is **Shaikhaffan**; token is saved at
`/home/innocent/.cache/huggingface/token` with permissions0600. A new token is not
needed. Both authenticated `/api/datasets/.../auth-check` calls return **403**,
explicitly saying the account is not in the authorized list and must visit each
repository to request access. Both repositories have automatic gating. The needed
user action is access request/terms acceptance in their own HF account, not another
CLI login. Public URLs are in Current outcome above. Redacted status is
`P3/hf-access-status.json`; it records account/HTTP status only, no token.

Latest tested code commit **e2beca9fd34d34b5172f24084c1c8dbb3cab5b0d** is pushed toPR36.
Both GitHub Backend CI runs **39159999711** and **39159996866** passed all jobs:
core API and recitation/ML. This supersedes the initial standalone import failure.
Final local suite960pass/1skip, standaloneML+API475pass/1skip and optional-inference
pilot24pass. All40-epoch runs and36human diagnostics completed with exit0/noOOM.
`P3/run-summary.json` and `experimental-bundle.json` index exact code/model/evidence
identity. Complete pronunciation goal remains unfinished, candidate unqualified,
production0c7562b unchanged. No APK or live model was released from this pilot.


## Continued without waiting for gated data — 2026-10-18 21:54 UTC

User explicitly requested continued work until full resolution. Authenticated HF
access rechecked21:47; both corrected-label repositories remain403. Investigating
public alternatives instead of repeating that blocker. New evidence directory:
/home/innocent/qari-training-artifacts/pronunciation-human-data-20261018.

Public QDAT-Bench (obadx/qdat_bench) revision53d7221da573b2b9e92d9542507564ae1b88fd30
has159human recordings, one per reciter, one shared ayah (Ma'idah5:109), with
phonetic transcript and observed madd/noon/qalqalah annotations. Metadata fetched,
audio not downloaded yet. This is a limited-scope alternative, not a replacement
for multi-surah word-level ground truth. Source:
https://huggingface.co/datasets/obadx/qdat_bench .

Other public Iqra mirrors contain canonical phonetizer targets and cannot
substitute for actual erroneous spoken phones. MON3EMPASHA Arabic mispronunciation
word dataset has binary labels but no realized phones/clear annotation provenance;
not accepted as human-phone truth. Official Iqra trained checkpoints are615MB
and require additional upstream dependencies; current disk free903MiB with512MiB
reserve. Existing Muaalem FP32 graph remains but its external data weights are
absent, so do not claim it is currently runnable. Android INT8 candidate876MB
would violate reserve and is not downloaded. No cache/container/model data deleted.

A small public candidate fryad-yaseen/quran-phoneme-ctc-tiny-v2 was downloaded
for private diagnostic only (32914622bytes, immutable75c2dae862b8703feb75f0c9984273a343677e8d,
sha256e00e996f9e8c2760cdb6d42e5a5b9163f0a951919d312645701e0d3421959f1d).
Architecture inspected with weights_only=True before use; license/training
provenance are not yet sufficient for deployment. It could test whether a
pretrained phoneme head improves the synthetic-only pilot's human errors without
new encoder training. Original production models and backend0c7562b unchanged.


## Public phonetic candidate running — 2026-10-18 22:00 UTC

Tiny33MBcandidate rejected before decoding because no published ID-to-phone map
exists in its repo; never guess vocabulary order. Its newly downloaded weights
were removed afterSHAverification, preserving metadata/rejection record to avoid
filling VPS disk. Public TBOGamer22/wav2vec2-quran-phonetics downloaded instead:
revision65c3ab93446f2f1041a18082433a911e5e154a9d, standard Wav2Vec2ForCTC with
complete40-ID vocabulary, nativeblank37, Apache2.0. All weight tensors loaded
strictly into existing runtime, no missing/random parameters. Source model trained
on isolated Quran words, so comparing whole short ayahs against original-native
word crops; no expected transcript enters phonetic inference.

P4=/home/innocent/qari-training-artifacts/pronunciation-human-data-20261018.
Actual probe P4/run_word_phone.py / probe_word_phone.py, container
qari-word-phone-probe-20261018, networknone/2500MiBtotalmemory/1CPU/nice19,
logs word-phone.log, output word-phone-results.json, resources word-phone-memory.json.
First whole-ayah outputs are poor as expected for word-trained model; crop output
still pending. No human correctness decisions or productionchanges made.
Model377635736bytes; disk530MiBfree above512MiBreserve. Do not download another
model or corpus while this candidate occupies that reserve. Dataset source labels
and all user recordings remain excluded from training. Needfinish/assess probe.


## Kaggle access restored; larger training preparation — 2026-10-18 22:12 UTC

The earlier Kaggle login failure was partly a tooling diagnosis error: host
CLI1.7.4.5 lacks KAGGLE_API_TOKEN support and fails locally before contacting Kaggle.
Existing qari-conformer-kaggle-cli container has Python3.12.15/Kaggle2.2.4/SDK0.1.37;
the same previously authorized token authenticates correctly there as **telethonfool**.
Legacy kernel default session isCOMPLETE (explicitversion1 returned404, not authfailure).
Credential is now cached0600 at /home/innocent/.kaggle/access_token and inside the
existing CLI container's private home. No token is in code, arguments, output or
this file. Private helper P4/kaggle_login_private.py uses getpass/hiddenstdin and
verifies the expected training account; existing differing credentials are backed
up privately before replacement. Current authoritative CLI is the container.

Actual quota query: **GPU0used/30hours remaining; TPU0used/20remaining**, refresh
2026-10-24. No current training job is claimed started yet. Plan now scales audio-
only frozen-original-encoder training to8192actual altered public TTS clips plus
512heldJessica clips, with15% reference-group holdout and1536pervoice trainingcap.
New isolated worktree /tmp/qari-pronunciation-gpu-20261018, branch
fix/pronunciation-gpu-training-20261018, basedPR36. Written spec/plan under
docs/superpowers/{specs,plans}/2026-10-18-gpu-phoneme-training.md. Core split and
padding-safe temporal head tests written first; RED run inprogress. Only frozen
original model files will be uploaded privately; no user audio or credentials.

Public word-phonetic candidate probe finished36cases, exit0, peak823.40MiB/noOOM.
Both wholeayah and original-native word crops failed to separate annotated vowel
errors reliably (wrong andcorrect clips oftenbothdecodedkufuu). Rejected, allraw
outputs/modelidentity retained P4/word-phone-results.json andword-phone-decision.json.
Its newly downloaded377635736-byte weights were removed after exactSHA verification
to reclaimdisk; metadata retained. Current originalproductionmodels untouched.


## Larger training core verified — 2026-10-18 22:17 UTC

Isolated GPUtraining branch coreTDD:17 meaningful failures to17pass. New head
masks padding before every temporal convolution; tests prove real-frame logits
are invariant to unrelated batch peers and poisoned padded tails, with finiteCTC
gradients. Reference grouping unifies presentation/diacritics for leakage checks
only; actual phoneme_mis targets retain vowels/geminates. Entire current backend
+ML+API suite **977passed,1optional skip,2warnings in54.64s**, exit0.
Task2runner tests writtenfirst andRED inprogress. Kaggletraining stillNOTstarted;
preparing/testingaudio-only extraction/finitecheckpointreportingbefore submission.

## 2026-10-18 22:34 UTC — bounded GPU experiment submission preparation

- Kaggle login is working in `qari-conformer-kaggle-cli` (Kaggle2.2.4/Python3.12); account `telethonfool`, verified30GPUhours remaining. HostCLI1.7.4.5 did not support the new token format; that was a tooling failure, not proof of bad credentials. Private cached authentication locations are documented above; no secrets are copied here.
- Isolated branch `fix/pronunciation-gpu-training-20261018`, worktree `/tmp/qari-pronunciation-gpu-20261018`, basedPR36`efba180`. Core commit `02bb80b`; original live model and backend unchanged.
- First full runner suite988passed/1skipped. Reviewer found one Important issue: dependency installation was outside the whole-job timeout and defaultSIGALRM bypassed failure metadata. One fix pass adds a standard-library deadline covering bootstrap and processing, bounded dependency subprocess, inherited deadline, terminal failure metadata; three real timeout/success tests pass. Focused suite31passed. Fresh reviewed whole suite991passed/1skipped,2warnings in55.11s.
- Private frozen encoder dataset `telethonfool/qari-frozen-encoder-20261018` ready, datasetId12691275; downloaded provider metadata confirmsisPrivate=true; only five original model assets plus hash manifest are included. No learner audio or credentials. Model SHA unchanged`b47c0fc7cd202c24ad4c7816e29d06c7d37c3761c1dcc91690796227df01dfa0`.
- Planned private kernel `telethonfool/qari-phoneme-ctc-20261018` is NOT yet submitted/training. Packet `/tmp/qari-conformer-training-20261009/phoneme-ctc-20261018`; build/decisions/tests under `/home/innocent/qari-training-artifacts/pronunciation-human-data-20261018`.
- Research only: independently split actual synthetic altered-phone targets, frozen audio encoder, temporal CTC head; Jessica and normalized reference groups held out. Min4096train/512validation, caps8192/512/1536pervoice; no expected text decoder. Deadline7100s and provider7200s cap. No qualification or deployment claim until human-labeled errors, correct speech, original CPU encoder and guards pass.

###22:37UTC — private GPU version1 running

Runner commit`05f4b42` pushed; draftPR37 https://github.com/khan23153/qari/pull/37 (basedPR36). Actual provider slug differs from requested metadata id because title normalized it: **`telethonfool/qari-audio-only-phoneme-ctc-20261018`**, kernelId139498044, version1. Do not resubmit using the old requested slug. Provider source pull confirmsis_private=true, NvidiaTeslaT4, exact launcher-byte match. ActualstatusRUNNING andQARI_GPU_BOOTSTRAP_START observed22:34:50UTC; gradient training has not yet been observed. Live monitor `/tmp/qari-conformer-training-20261009/phoneme-ctc-20261018/monitor.py` and runtime-v1.log/monitor-v1.jsonl/status artifacts; submissionrecordalsoinP4. OriginalCPU encoder held-out human features are being prepared independently; model/correctness qualification remainspending.

###22:40UTC — actual GPU bootstrap failure and repair

Version1 endedERROR before model setup/gradients. ProviderPython3.13.15 cannot install the originally pinnedNumPy1.26.4/oldPyAV dependencies. Bounded wrapper correctly savedfailure.json; retrievedoutput-v1. This is a bootstrap compatibility failure, not an acoustic training result. Runtime repair pinsNumPy2.2.6/faster-whisper1.2.1/CT24.6.0 and requests binary wheels only. The original faster-whisper1.0.3 feature_extractor.py is preserved byte-for-byte as research module`ml/training/frozen_whisper_frontend.py`, SHA`5509a21380cc933327bcb01f1d3d2d5ee2e242a7664e672006796ed4f4491b55`, with upstreamMITlicense. Four tests RED→GREEN verify source identity and exact original mel features for silence/voice-band/impulse audio. OriginalCPU human features completed36/36 at~397MiB under1.2GBlimit; no model text decoder or GPU cache reused. Actual publicTTS source WAV checked16kmono2.61225s, so sample-rate selection is applicable. Fresh whole suite and version2submissionpending.

###22:44UTC — GPU version2 feature extraction verified

Runtime repair commit`06dca92`, test-only successor`06c6a4d`, draftPR37. Full suite995passed/1skipped54.17s; final standaloneML/API510passed/1skipped5.61s, frontend tests also work around legacy optional-ASR stubs. Version2source pull confirms privateT4 and exact launcher-byte match. ActualGPU_SETUP22:42UTC verified frozenmodelSHA and originalfrontendSHA, CUDA0/int8_float32, Torch2.11.0+cu128, NumPy2.2.6, CT24.6.0, faster-whisper1.2.1, datasets3.6.0, soundfile0.13.1. Feature bundle`cc9601b43926b4b9b46049d13ccb543d2e29f0b125b5256248e8ae69776fa0a9`; originalCPU runtime is intentionally distinct and must be evaluated separately. Public source streaming and actual batch feature extraction observed (256trainclips29.9s), no decoder. No gradient/accuracy claim yet. Monitor now uses default current session because explicitversion_label='2' returned404 despite current sessionRUNNING; old observer stopped and one current monitor retained. Generic Kaggle preinstalled package conflicts were pip warnings; setup and features succeeded.

## 2026-10-19 05:55 UTC — resumed actual terminal result and precision investigation

Version2 endedERROR at2026-10-18 23:00:24UTC, after preparing8192train/512heldJessica clips across6trainingvoices. No successful epoch/checkpoint was produced. Failure.json andsource-manifest/feature-identity retrieved under `/tmp/qari-conformer-training-20261009/phoneme-ctc-20261018/output-v2`. Strictfinite-gradient clipping rejected nonfinite gradients at first training step; loss-scaling/FP16overflow is the hypothesis, not yet proven. Guard remains enabled.

Local regression: caller autocast contaminated CTC training (initial RED: inference cached tensor error; forward-only disable still changed validation loss); whole forward/backward/optimizer FP32 wrapper passes12focusedtests. No arbitrary error suppression, zero_infinity remainsfalse. Fullsuitepending. Version3 is a private900sT4 diagnostic (not full training), comparing originalAMP vsFP32 on the same16 shuffled first-step publiccaseIDs and44-token vocabulary. It verifies each clip's actual floatPCM SHA against version2 before encoding. DiagnosticlauncherSHA`79e7e7dbc3c8b0fce4cbc395107f893ec1b1fa3dfcd0c342c1e967943ef1ebf3`; script/monitor/artifacts underP4 andprivatepacket.

Public canonical phone-reference columns were read without audio download using bounded HTTP range reads:3554unique references,3669885networkbytes from firstpinnedIqra_TTSshard; foundIkhlas112:3reference. This is expected-reference text only, not human spoken-phone truth. OriginalCPUhumanfeatures36ready. No experimental model deployed; original backend unchanged.

### 2026-10-19 05:58 UTC — FP32 regression verification

Commit`adadd63` pushed toPR37. Full996passed/1skipped54.80s. Version3actualGPUbootstrap succeeded; all16first-batch publicPCM hashes verified exactly againstversion2metadata. AMP/FP32 numerical comparison nowinprogress. Both publiccorehealth andlocalrecitationhealth200, originalproductionimageunchanged, recitationhealthy/0restarts/0OOM.

### 2026-10-19 06:04 UTC — numerical root cause verified, full FP32 run active

Version3COMPLETE. Same16publicPCM recordings verified against version2: AMPFP16 loss14.0669918060 finite, initialscale65536, exactly9nonfinitegradientvalues, clipping rejected update; FP32 loss14.0673179626 finite,0nonfinitegradientvalues, norm14.10006237, optimizerstepcompleted. Saved`output-v3/precision-diagnostic.json`. Thus training-start failure was actualFP16gradientoverflow under initialloss scaling; it is separate from the original pronunciation false acceptance. No finite/confidence/speech guard was disabled. LatestGitHubCI39207109634 and39207104753 passed foradadd63.

Version4privateT4 fullFP32 run submitted, actualGPU_SETUP and feature extraction observed, pulledprovider sourcebyte-identical andprivate. Featurebundle`11b823a007f037a6f61fa6081758b0a1937b4d2bd20266689042787c352a7a32`. Monitor_v4.py/runtime-v4.log active. No training epoch/qualification result yet.

HFauth-check rechecked2026-10-19: correctedhuman datasetsIqra_Extra_IS26 andIqraEval_Test_GT still403. No newcredentialrequested. A separate publicmodel candidate`MostafaMaroof/wav2vec2-arabic-phoneme-asr` revision`0a32c641aaaeec6957e41a794add52e024e46b50` (315Mparameters/1262135432-byte safetensors, SHA`582149e3e913a0fc7f29c116530e0b1b6ae7a7ab23eef4efc3fc2acc760e2b75`) is being tested privately without alteringoriginalmodels. Weightdownload goes to ephemeralRAMtmpfs,4GiBhardmemory/3.5GiBsoftstop,0.75CPU,1200stimecap, exacthash/nativevocab/blank/processor/strictmetadeviceload. Sourcecardclaim14.4%syntheticphoneerror is not Qari qualification. Metadata/helpers/logs underP4arabic-phone-*; no output verdict invented.

### 2026-10-19, 06:10 UTC — held-out evaluation preparation

OriginalCPU feature caches now include36contributor-labelledIkhlas clips and14expert-labelledmulti-surah utterances (`human-cpu-feature-manifest.json`, `expert-cpu-feature-manifest.json`), allheldout/no training. Expertlabelsareutterancelevelonly, no inventedword-errorlocations. Public315MArabicphonememodel weights/native80-token vocabulary/blank77/strictmetadeviceload verified; actualRAM~1.5GiBunder4GiB, no diskweightcopy. Its early free-phone transcripts disagree with labelledcorrect clips too; do not assume mismatches are speaker errors. Bounded36clipcomparison stillrunning. Canonicalreference-only Iqra columnscan reached11,008,302networkbytes across3shards, foundIkhlasayah2–4;180sdiagnostictimeoutstoppedfurtherreads, no rawaudio downloaded. Canonicalphone strings containpausing/phoneticconventionissues and are NOT human realized-phone groundtruth. MON3EMPASHAmetadata shows100commonArabicwords/children-speaker folders and_Nsuffixlabels; sourceappearsASMDD/MSAdialogue, not Quranwordphone annotations. Do not use it to claim Quranqualification.

### 2026-10-19 06:14 UTC — larger public phoneme recognizer rejected after complete bounded diagnostic

MostafaMaroof315M candidate completed36/36held-outcontributor-labelledclips plusnativewordcrops, exit0, noOOM/no3.5GiBsoftstop. ProcesspeakRSS1819604KiB; sampledcgrouppeak1688.58MiB under4GiBcap. Five labellederror clips produceexactlythesamefree-phone text ascorrectclips(sameayah);4correctclips participateincollisions. This demonstratesphone-text-only matchingcannotseparatethese observedclasses; it doesNOT measure a calibratedposterior/GOPclassifier orprovewhatthereciteractuallysaid. Medianwhole-clipRTF2.2469 at0.75CPUcap. No humanrealized-phonegroundtruth wasinvented. Decisionnopromotion, qualifiedfalse. ExactpinnedweightswereRAM-onlyanddisappearedoncontainerexit; originalmodelsuntouched. P4`arabic-phone-results.json`, `arabic-phone-readiness.json`, `arabic-phone-decision.json`, logs/memory/exit andsourcepinsretained.

Version4stillRUNNINGwithfeatures>5500train; no successfultrainingepochyet. OriginalCPUhuman36+expert14featuresreadyforitshead.

## 2026-10-19, 06:42 UTC — completed GPU experiment; pronunciation goal still open

**No experimental model was deployed.** Version4terminalCOMPLETE at06:30:23UTC. It trained18epochs (earlystopafter8unimproved), bestepoch10, 8192TTSalteredclips/512Jessicaheldclips,6trainingvoices. BestsyntheticPER0.14205191594561187; trainingphase477.53s. Native44-token vocabularyincludingblank0, no unknownheldphones. FP32retainsfinitegradientguard; no textdecoder/oracle. HeadSHA`e419a176420196d0ee5004ed781f8fc99ecf214f6517ee574c4c30cafb6f2115`,1.1MiB. Privateoutputfolder `/tmp/qari-conformer-training-20261009/phoneme-ctc-20261018/output-v4` holdshead,report,512bestpredictions,source-manifestandfeatureidentity(~9MiBtotal). This is a researchcheckpoint, not a releasemodel.

Completed originalCPU/INT8 evaluation:36contributor-labelledhumanclips +14expert-labelledutterances. Outputs oncorrect-labeledspeechare not reliableenough to serve as phonemic grading. No humanphonemePER, pronunciationaccuracy, or successfulworderrorgradingwasinvented; all50statusesremainunassessed. Zero exactgreedyclasscollisions innewhead doesNOT meanzeroerrors (noisyuniquetranscriptscanavoidcollisions). Recordednative20msframeposteriorswithfilehashes underP4`gpu-human-posteriors` and`gpu-expert-posteriors`; observation/decisionJSONsretainheadandfrontendidentity. Medianheadforward+posteriorcalculation57.43ms at0.5CPUcap, excludingencoderandfileIO; liveappdelaynotmeasuredbythisofflinefigure.

Matchedbackendcomparison:32identicalpublicheldTTSwaveforms/1256actualsyntheticphones. CPU14.2516%PER vsGPU14.1720%PER (difference0.0796percentagepoints);23/32decodedsequencesidentical. OriginalCPUfeaturePCM/sha/nativeframessourcevalidatedagainstfinalv4manifest. ThuslargeCPU/GPUportregressionwasnotobservedonthislimitedsubset; likelysynthetic-to-natural domaingapisaseparate concern, not a provenhumanphonemeerrorrate. SeeP4`portability-report.json`, `portability-cpu-feature-manifest.json`, `portability-cases.json`.

Three model-only controls (2ssilence,belowenergy sine,white-noise) returnedblankphones. ThisdoesNOT exerciseappmatchercursor/WS; unchangedproduction'searlier9publicWSchecksremainseparateevidence. Currentproductionhealthrechecked06:40UTC:corepublic200/localrecitation200,recitationhealthy0restarts0OOM,imageunchanged`sha256:1c93eb3220a3dd980d3d7269e9eb6fcc9fa9731c0bb260dc0b54c420c7e58d57`. Main/streaming_sessionactualsourcehashesstillmatchdeployed0c7562. BoundedDockerlogwindowafter00:00UTCcontained0lines, thereforeitdoesnotverifynewliverecitationaccuracy.

Finalengineeringtests996passed/1skip; bothGitHubCI39207109634/39207104753passedoncode`adadd63`. PR37staysdraft; rootproductioncode/UI/originalmodelsunchanged. Rootcontext.mdandtrainingworktreecopyupdated; preserveallworktrees/privateartifacts. Currentusergoal **fully fixing pronunciation is NOT complete**.

**Next dependency:** correctedhumanrealized-phone/errorlabels. HFauthworksbutIqra_Extra_IS26andIqraEval_Test_GTstill403at06:41UTC; userwasaskedviaasyncrequesttorequest/acceptaccessinthesameShaikhaffanaccount. No newtokenneeded. PublicIqra_train revision`02f9863194faa8aab2de7896c936a6f1f1a55138` wasaudited:71,391train/2588dev,phoneme_ref/phoneme_aug,mostlycanonicalweaklabelsfromMSA/Quran. Sourcepaperexplicitlyassumesvowelizationmatchesaudioandacknowledgesnativevowel deviations. Do NOTrelabeltheseautomaticreferencephonesasactuallearnererrorannotationsortrainincorrectspeechwithcanonicaltargetstoforcepasses. Furtherdatarecipesmustdeclareweaksupervision; theycannotreplacehumanqualification.

Afterlegitimateaccess:pinandinspectschemas,keeptestGT/userrecordingsheldout,trainwithactualspokenphonesfrompropertrainpart,validateword-errorfalseaccepts/falsealarmsacrossrequiredvoices/surahs/kinds. Onlyahumanqualifiedmodelmayintegratewithoriginalspeech/confidence/cursorguards; re-runactualrecitationcontrolsanddeployusingexistingconfigafterthat. No promisesofallpronunciationerrorsbeingfixedfromsyntheticPER. Fullresearchdecision:P4`final-experiment-decision.json`.


## 2026-10-19 — follow-up investigation and actual human-label path

The wider pronunciation goal is still open. Fresh runtime check08:40UTC: public
core/localrecitation health200; recitation/tunnel/edge running0restarts/0OOM,
original image unchanged; bounded recitation logs since06:40 have0lines. This is
health evidence, not a new live accuracy claim. Both corrected Iqra datasets still
403 at08:38, login credential unchanged. No new token needed.

A small alignment-marginalized CTC prefix diagnostic on stored posteriors avoids
forcing the remaining expected sentence. Six independent checks include exhaustive
CTC path enumeration, repeat/blank handling and underflow. On5error+5correct held
Ikhlas opening clips: canonical prefix preferred on3error labels, inserted short
vowel preferred on1correct label; diagnostic rankAUC.72. This is only a hypothesis
for l-sukoon vs inserted vowels, not actual erroneous-phone ground truth or a full
GOP-SF implementation. No threshold fitted/model trained/live changed. Artifacts
P4/ctc_prefix_probe.py, test_ctc_prefix_probe.py, prefix-contrast-results.json.

**Correction to earlier next-dependency wording:** actual realized-phone labels
are necessary to supervise phone diagnosis, but a *binary word-error* classifier
can be researched with existing human word-correctness labels. Gated Iqra access
is not the only possible next step. Audited all1506 pinned public Ikhlas records:
384participantIDs,851error/655correct utterances, only one surah. Conservative
parser quarantines12records (2filename/explicitlabel conflicts,9unmapped/ambiguous
locations,1correctlabel carrying error annotations). Unlisted words in error clips
are UNKNOWN, never negative training targets. Bare lam inayah3 is ambiguous.
All24previously probed speakers are reserved. Deterministic remaining split before
audio:1129train/290speakers/964error+1742correct knownwordtargets;129validation/
34speakers/95error+242correct;142test/36speakers/106error+240correct;94reserved/
24speakers. P4/human-word-experiment/label-manifest.json. No training audio fetched
yet and no GPU job submitted for this experiment.

Existing isolated worktree reused on new branchfix/human-word-error-20261019,
parentPR37 docs69f2805; design24d78ec, strictdata contract5321149. Specs/plans under
docs/superpowers/{specs,plans}/2026-10-19-human-word-error.md. Intent: frozen original
encoder, small15-position word-query acoustic binary head; train actual human
labels, not canonical phone targets. Text-only prior baseline required. FP32 and
finite guards/bounded private T4; test/reserved scores cannot select checkpoint or
threshold.12contracttestsRED→GREEN; padding-safe classifier/training tests inprogress.
This research remains Ikhlas-only, qualified=false, no live integration/model/UI
changes. Multi-surah/actual vowel/consonant/gemination qualification still required.


### Human-label experiment reviewed/submitted — 2026-10-19 09:04 UTC

Code4973de4 onfix/human-word-error-20261019, draftPR38
https://github.com/khan23153/qari/pull/38, baseddraftPR37. Entire recitationAPI+
ml/tests+api/tests1025passed1skip2knownwarnings108.98s; focused29tests independently
passed byfreshreviewer. NoCritical/Importantfindings. Minor splitrecipe omitted
first8hex32bitSHA truncation; prose corrected, actualcohortsunchanged. Full SHA
recipe wasneverused; auditedmanifestpreserveseveryrole. New head alwaysunqualified.

PrivateKaggleT4 jobtelethonfool/qari-human-word-errors-20261019 version1 submitted.
Provider source pulledbyte-identical; is_private=true, machine_shapeNvidiaTeslaT4.
LauncherSHA992d3d9e5808da01fe3267c1bc7f379c7caff5a9b0b63711d02c925988fda214.
Packet /tmp/qari-conformer-training-20261009/human-word-20261019, submission-record-v1.json;
monitor.py/monitor-v1.jsonl watchesactualstatusandlogs. ProviderstatusRUNNING,
butlogendpointreturnedHTTP500 at09:03; no actualtrainingepochclaimyet. Do notblindly
resubmit. CLIobserverfallbackbeingchecked; periodicmonitorcontinues.

OriginalCPUcomparisonfeaturehelper initiallyfailed fromFW1.0.3 conveniencewrapper
adding anextra batchdimension to alreadybatchedmel. Privatehelper only: raw CT2
StorageView encode call fixes dimensionownership; rerunprogressesactualrecordings.
SourcehumanWAV44.1kstereo -> fixedscipypolyphase16kmono floatPCM; cannotreuse old
ffmpegPCM16features silently. Existing36probeclips reduce to35eligible because
ID11V4F has conflictingfilename/correctlabel andwasquarantined. All24sourceparticipant
IDs reserved, noneusedforoptimization. Newfeatures/logmanifest under
P4/human-word-experiment/cpu-reserved-*;600stimecap/1200MiBhard/.5CPU; originalmodels
unchanged. No experimentalmodeldeployed, no newAPK.


### Actual data collision and repair — 2026-10-19

Version1 terminalERROR09:11:45UTC, actualfatal line09:11:02: Duplicate actual PCM:
ID187V1T and ID193V1T. Audited metadata roles aretest/train, respectively; eachID
hasfourayahclips. Sourcefailure/partialmanifest/featureidentity/log retained at
`/tmp/qari-conformer-training-20261009/human-word-20261019/output-v1`. No training
epoch or checkpoint existed. This is a dataset integrity failure caught by the
guard, separate from pronunciation model accuracy and from core/API health.

Repair rationale: dropping only the later copy can leak one participant's other
ayahs if the duplicate indicates ambiguous identity. New two-stage pipeline first
downloads/decodes/hashes all public sources, then quarantines every participant
involved in any duplicate group (including their other unique clips), preserving
all original split assignments. Only then encode/train; final training validator
still stops on any unresolved duplicate. Sourceaudit records all excluded cases
and exact hashgroups; no case is silently relabelled. At most4ordered requests,
shared byte reservations, counted partial failed reads, total1GB content-readcap.
Three meaningful RED regressions→GREEN; new full suite pending before resubmission.

Source category coverage (parallel type/location lists, not actual heard phones):
train143vowel/8vowel+tajweed/811tajweed error targets; validation11/2/82;test13/0/91;
reserved23/2/42. Two rows have ambiguous parallel category lists; do not invent
word-level kinds there. Only3pure-vowel-only utterances remain in training and16
are reserved; mixed-error utterances contribute most othervoweltargets. This
explains why aggregate tajweed scores must never be presented as vowel accuracy.
`P4/human-word-experiment/source-category-coverage.json` retains counts.

Additional source review (no models/code copied):
- https://huggingface.co/Quran-Lab/zipformer_p-arabic-v3#honest-limitations openly
  reports canonical-label bias on human error audio (81/94 plain-noon clips decoded
  as fullikhfa). Its low overallPER is not proof of mispronunciation rejection.
  New weights not downloaded; same architecture issue as our observed false accepts.
- https://github.com/harounRhim/sanad calibrates duration/nasality on one reciter,
  not learner phonemic errors; cannot substitute for our missing broad errorlabels.
- https://github.com/kaylaque/quranic-pipeline skips acoustic scoring when ASR text
  fullymatches, and acknowledges ASR diacritic limits; that approach would retain
  the canonicalized-error blind spot. No borrowed code or changed licensing.

Primary live decoder uses sherpa_onnx.OfflineRecognizer.from_transducer in
`ml/inference/fastconformer_transcriber.py`, returning words/confidences/times, not
public hiddenfeatures. Any future shared acoustic head needs a proven feature
hook or a verified decoder refactor; do not claim zeroextraencodingcost or lower
app delay from this offline Whisper-head experiment. Core lexical backend/model
and UI remain unchanged.


### 2026-10-19 — version2 queued; original raw diacritics audit

Repaircode50e083a pushedPR38. Full1027passed1skip2knownwarnings108.69s; bothGitHub
CI39229252334/39229258728 pass recitation+ML andcoreAPI. Version2submittedprivateT4;
provider sourcebyte-identical, machine_shapeNvidiaTeslaT4, launcherSHA
`a9959fb7420aca93711a91df8caf7fbfbd2763fd84739b413d05a549a3dffdaa`.
`submission-record-v2.json`, monitor_v2.py/monitor-v2.jsonl/runtime-v2.log trackactual
state. At09:28UTC QUEUED, no bootstrap/epochyet. RecentotherQari kernelschecked:
phonemeCTCcomplete,PCDcorrectedcomplete,Qwencomplete,turbocomplete,oldPCDcleanERROR;
no recentolderRUNNINGjobwasfoundblockingit. Do not infermodelaccuracyfromqueue.

Raw native inspection completed36/36publicheldclips withoriginalhashedPCD RNNT,
not `_independent_transcriber`'s already-normalized output. It emitteddiacritics
on81rawwords; tokeninventoryhas137markedtokensof1025lines. Backendnormalizesraw
words atstreaming_session.py:639 andonlythenreturnsnativewordevidence. Thus
prior553normalizedwordobservationswithzeromarksare NOTproofthatrawPCDneveremits
marks. P4/probe_raw_pcd.py/raw-pcd-probe.log/raw-pcd-observations.jsonretainrawtext,
tokens/nativeys_log_probs/confidences/sourcePCMhashes. Same frozenmodels, no training
or productionedits; offline600s/1200MiB/.5CPUguard, exit0.

However10/10contributor-labelledkufuwanvowelerrorsstillhaveexpectedfa-damma`فُ`
inrawASRoutput, oftenhighconfidence. Missing/variablemarksaffectotherclips. Hence
keepingmarksalonewouldnotrepairtheseknownfalseaccepts, andanabsenceofmarksisnot
proofofwrongrecitation. P4/raw-pcd-decision.json. Do notturnoffnormalizationor
flagallmissingcase-endingsaserrors; legitimatewaqf/partialASRrequireseparatehandling.
NVIDIA'supstreammaintaineralsodescribesmixedfully/partially/non-diacritizedtraining
withnocontroloverdiacriticpresence:
https://github.com/NVIDIA-NeMo/Speech/issues/15452
(theissuepage/maintainerMarch3commentisthesource; donotassumeacommunityreportthat
allPCDweightsarewrongappliestothisverifiedexport).

CurrentTarteelcomparisonmustusethelatestofficialsupport,not2022marketing:
https://support.tarteel.ai/en/articles/16559266-a-mistake-was-flagged-that-i-didn-t-make
saysoptionalTashkeelmistakedetectionexists,acknowledgesmissedmistakes/falseflags,
andstatesgeneralTajweedrulesarenotchecked. Thesearedistinctcapabilities; neither
Qari'swordmatchingnorcompetitorfeatureclaimsprovephonemicgradingisqualified.


### REA installed — 2026-10-19T12:07:29.563676+00:00

User requested https://github.com/morluto/rea installation. Installed official
npm package rea-agents@6.7.0 globally with --ignore-scripts (Node22.23.3).
Executable: /home/innocent/.nvm/versions/node/v22.23.3/bin/rea.
Reviewed dry-run then applied `rea setup --client codex --yes --json`.
Codex MCP entry added to /home/innocent/.codex/config.toml; backup at
/home/innocent/.codex/config.toml.rea.backup. Semantic comparison confirms all
unrelated configuration preserved. Matching bundled workflow installed at
/home/innocent/.agents/skills/reverse-engineer-anything (skill42,207tools).
`rea doctor --client codex --skill --json`: healthy=true, all scoped checks pass.
Actual stdio MCP initialize + tools/list smoke check: server6.7.0,207tools.
Restart/reconnect Codex to discover MCP tools in the agent; this smoke test does
not establish that the current agent has connected. No optional native engines
(Hopper/Ghidra/IDA/JADX) installed; engine-dependent analysis needs its provider.
No Qari production/model/UI changes. npm disposable cache cleared after install;
filesystem free space ~1.1GiB. Setup/doctor reports under /tmp/qari-rea-*-20261019.json.

Qari human-word-errors-20261019 version2 still QUEUED at this timestamp via
Kaggle CLI. Existing monitor_v2.py process remains running (PID3961676 at check),
monitor-v2.jsonl continues status polling; no epoch or training result yet.
Pronunciation false-acceptance issue remains unresolved; REA is an analysis tool,
not a new speech model or a demonstrated fix for that issue.


### Storage cleanup — 2026-10-19T12:40:51.381608+00:00

User needed room for an APK upload. Removed only unused Python dependency
environment /tmp/qari-asr-repair-20261009/nemo-venv (~1.9GiB). Verified no active
host process or running container mount used it. Saved all dependency versions
and Python metadata first under /home/innocent/qari-training-artifacts/
storage-cleanup-20261019/: removed-nemo-venv.json, nemo-venv-requirements.txt,
cleanup-result.json. Old stopped diagnostics need this environment recreated.
Production models, all source worktrees/local changes, recordings, research
outputs and running services preserved. Space went from ~906MiB to ~2.7GiB free;
current free bytes: 2823249920.

Drive qari-training: remains read-only and cannot upload. Prepared a separate
drive.file backup OAuth login. User then said choro apk upload hogaya: cancelled
backup per that instruction, stopped pending OAuth, removed unauthenticated
backup-only configuration. Original Drive login unchanged. NO FILES UPLOADED TO
DRIVE; no important files deleted awaiting backup. User confirmed APK uploaded.


### Tarteel asset analysis and Flutter Madani layouts — 2026-10-19T13:09:01.420647+00:00

User supplied /home/innocent/com.mmmoussa.iqra-5-81-9-android70.xapk
(Tarteel5.81.9/code420, SHA c89d130535495788c82b99778ec00abcc098dd89416e2725f634ee099ffd35df).
Used connected REA tools for archive inventory, then bounded local ZIP/SQLite
inspection and Hermes96 disassembly (P1sec/hermes-dec revision
2e796663e1fedb93dca51060797ebf3327b3fedb). No APK execution or Tarteel service calls.
Verified 1405=QPC_V1/qpc_v1_layout/dk_v1/DigitalKhatt Old Madina
(DigitalKhattQuranic.otf);1421=QPC_V2/qpc_v2_layout/dk_v2/DigitalKhatt New Madina
(DigitalKhattV2.otf). Classic1405 also has optional QCF_P001..604 glyph-font path.
Each layout604pages/9046lines/83668tokens including6236ayahmarkers;4662rowdifferences.
Font-only switching is insufficient. Exact function IDs/offsets and font hashes
are recorded in docs/tarteel_mushaf_asset_analysis.md and artifact findings.json.
Implementation isolated in /tmp/qari-mushaf-layouts-20261019, branch
feat/mushaf-layout-switcher-20261019. New files: mobile/lib/data/models/madani_page.dart,
data/repositories/madani_page_repository.dart, features/recitation/presentation/
mushaf/{mushaf_layout_switcher,madani_mushaf_reader}.dart, and
mobile/lib/main_mushaf_layout_preview.dart. Controlled Flutter selector and paired
reader use existing MushafTheme. Repository caches4decodedpages and2fontfamilies,
rejects mismatched data, hides stale content and supports retry. This is a READING
component/standalone preview; NOT enabled in existing released APK or live Hifz.
Existing Hifz, confirmations, markers, mistakes, ASR models and backend unchanged.
Global imported IDs include markers; future live integration must map word refs,
never feed these IDs directly to ASR. No claim of exact Tarteel Skia elongation.
scripts/import_madani_assets.py imports only needed paired page data/fonts
from local APK/XAPK. Generated assets ignored by git; tracked README placeholders
keep clean checkouts valid. Actual25MiB assets under mobile/assets/madani in worktree.
Reader requires import before preview/release packaging. Re-imports stage and
validate the complete result before publication, with rollback and sibling backup
on publication error. Peer review caught partial-overwrite failure; added a real
failing-then-passing re-import preservation test and successful retry.
Verification: full Flutter suite199passed/10opt-in skipped(exit0); additional
fresh focused run18passed (8unit/widget+10actual-font cases across pages1,3,76,77,604);
4Python importer tests passed. New Dart files: No issues found. Initial full-project
analyzer reported252existing warnings/info, no errors. Screenshots and full logs
under /tmp/qari-tarteel-assets-20261019/. Captures use a local Latin UI font override
only because Flutter widget tests replace platform fonts; Quran fonts remain
actual imported edition fonts. Original XAPK preserved; removed only recoverable
170MB extracted base-APK duplicate after analysis. Current disk free ~2.2GiB.
Production recitation container remains healthy/0restarts/noOOM. Kaggle human
word-error experiment remains QUEUED at last check; no pronunciation fix deployed.
No Drive upload or APK build performed for this component task.

Local component commit: d2829b1e54b73c66bbb0cf6547507e7433d9404f on
feat/mushaf-layout-switcher-20261019 (not pushed). Worktree clean; imported
external assets remain ignored. No credentials or external binaries staged.


### Tarteel mistake-detection client trace — 2026-10-19T19:21:30.724744+00:00

User asked to inspect mistake detection in the same supplied Tarteel5.81.9 XAPK.
Static Hermes/native-bridge inspection only; no Tarteel login/service requests,
recording uploads, runtime accuracy/latency test, or Qari production changes.
Artifact SHA c89d130535495788c82b99778ec00abcc098dd89416e2725f634ee099ffd35df.
Detailed report: /tmp/qari-mushaf-layouts-20261019/docs/
tarteel_mistake_detection_analysis.md. Retained focused disassembly, hashes,
function references and findings.json: /tmp/qari-tarteel-assets-20261019/
mistake-detection/. Report function IDs/offsets verified against saved disassembly.

Observed StreamingClient path initializes native MicStream with a production
voice-v2.tarteel.io WebSocket and selected recitation range/mode. Declared audio
configuration is 16kHz/16bit/mono/bufferSize512; native buffer unit and actual wire
cadence are unknown. Separate PARTIAL_TRANSCRIPT and STATES_UPDATE callbacks.
Mistake types: INCORRECT_WORDS, MISSED_WORDS, EXTRA_WORDS, INCORRECT_TASHKEEL,
plus PEEKED_WORDS (memorization annotation). Tashkeel has separate detail/highlight
and isDiacritized session toggle. isDualModel/remote dual-model flag is present,
but this does NOT reveal architecture, weights, accuracy or active user setting.
Server updates include newStates/stateIndexOffset and mistakeUpdates. Reducer
replaces a state suffix, merges mistake IDs and retracts falsey mistake updates;
latest POSITION drives surah/ayah/word cursor. Client can revise earlier results.
The APK contains multiple engine paths; static trace does not establish rollout.

No remote detector/model/training data/decision thresholds recovered. Absence of
common standalone model suffixes in base APK inventory is only a bounded negative
search, not proof that no embedded/downloaded/offline model exists. Qari still
reports pronunciation_available=false and tajweed_available=false. Its ASR can
canonicalize incorrect vowels; client flags/colors or lower confidence cannot
qualify pronunciation grading. Next research work: held-out human acoustic error
qualification, typed pronunciation evidence separate from lexical progress, and
explicit revisions while retaining confidence/speech guards and confirmed-only
Hifz. This analysis is not a pronunciation fix or deployment. Existing detailed
Kaggle queue status above is historical, not refreshed by this documentation task.


### Human-word training v2 failure and bounded loader repair — 2026-10-19T20:04:16.964736+00:00

Resumed actual pronunciation investigation after Tarteel static trace. Fresh
Kaggle status is ERROR (v2), not still queued: provider started15:42UTC, failed
15:43UTC before encoder extraction/optimization. Retained failure.json and logs:
/tmp/qari-conformer-training-20261009/human-word-20261019/output-v2/ and runtime-v2.log.
Actual cause: pinned data/ID247V1T.wav is3,310,754bytes, above3MB per-file cap;
generic fetch exception aborted whole audit instead of excluding invalid source.
Pinned tree audit1506entries,713,449,399bytes, onlythatoneoversizedfile, so this
was not total1GBexhaustion. Tree evidence source-size-audit-v2.json in packet.

Repair isolated in /tmp/qari-pronunciation-gpu-20261018 branch
fix/human-word-error-20261019: typed per-file exception, ordered-prefetch exclusion
callback, filename/reason/consumed-byte accounting and null full-source hash for
partialread. Total1GBguard, network/identity failures, original3MBcap, duplicate
participant quarantine, speaker roles and held24participants unchanged. New real
fetch/audit regression failed on original byte-limit exception then passed; total
budget exhaustion remains fatal. Focused12passed. Complete recitation/ML/API suite
1029passed1skipped2knownwarnings in56.86s, log:
/home/innocent/qari-training-artifacts/pronunciation-human-data-20261018/
human-oversized-full-suite.log. Research spec clarified exclusion; no live model,
backend or UI changes. Private v3 submission is being prepared; do not call it
running/complete until provider verification. Pronunciation issue still unresolved.


### Human-word v3 running / source identity verified — 2026-10-19T20:07:52.523815+00:00

Private Kaggle version3 started20:04UTC onTeslaT4 (notqueued). Provider source
pulled and verified byte-identical to tested packet; private settings and input
originalencoder verified. Commitb7c230ae81c3287232bb8d9b6f5fe0c05d3aef19 pushed to
existingdraftPR38; allfour coreAPI/recitation-ML CI checks passed. LauncherSHA
 d04f4fa76120d7d7be580e4e1008466f0b7719eebfdaa2f8b440b028f5082ccd.
Provider7200s/wholejob7100s budget unchanged. Observer monitor_v3.py, logs
monitor-v3.jsonl/runtime-v3.log/latest-status-v3.json in existingpacket, never
resubmits. Submission-record-v3.json stores exact private/source/runidentity.
Actual oversizedsourceexcluded andaudit768clips by20:07:26UTC; no accuracy result
or trained head yet. OriginalCPUhelper mislabeled mixedbinarywordlabels asvowel;
backedup then corrected kind tobinary_word_error_unclassified, preserving default
qualification gates and documenting unknown class coverage. Broader gated HF
Iqra_Extra_IS26/IqraEval_Test_GT still403 on authenticatedauthcheck20:06UTC.
Originalbackendhealthy/0restarts/noOOM, revision0c7562b remainsdeployed.


### Human-word GPU v3 COMPLETE; harakat qualification FAILED — 2026-10-19T20:15:55.273241+00:00

Actual providerstatusCOMPLETE, training10epochs/best4/threshold0.7857852578163147.
Private frozen-encoder run finished successfully, no failureartifact. Source/head
identities verified. HeadSHA f396e657f637eb0c886e58c4ab2c2307455211ad5b02ecb7f6192f8f9ce7fd9a.
Fullaudit1393cleanclips:1055train/122validation/127test/89reserved;13duplicatePCMgroups,
19participantIDs/all81theirclipsquarantined,19speech-guardexclusions,1oversized,
plus12preexistingmetadataexclusions. Limits/splits/unknownmasks preserved.

Actualheldtest:75/96errorsdetected,21missed;13falsealarms/216correctwords
(6.02%FPR,85.23%precision,78.125%recall).14of21misses onayah3 y alid/yulad
(7each),8of13falsealarms alsoayah3. Reservedall:34/61detected,27missed,
5falsealarms/148correctwords. Threshold/checkpoint werevalidation-only; no
heldtest/reserved tuning. Text-positionpriorbaseline detected0errors withits
validation-selectedconservative threshold; notanASR/livecomparison.

CrucialoriginalCPUreservedsubset:34of35clipsvalid (ID165V1F excluded fromcleanGPU
cohort);15contributor-labelledharakaterrorwords,1detected/14missed,0falsealarms
on70correctwords. All34resampledPCMidentical,0CPU/GPUdecisiondisagreements.
Thus CPU conversion doesnotexplain the misses. Head-onlyCPUmedian5.51ms excludes
encoder/buffering/network; no live latencyclaim. Sourceannotationcategories of
those15errors separatelyverifiedasحركات; diagnosticglobalkindremainsunclassified
binaryworderror ratherthaninventedphoneclasscoverage. Only2pure-harakattraining
errorutterances, mosttrainingerrors tajweed/mixed; co-occurrence/generalization
warning, notprovensolecause. Fullayahattention word-locality also unverified.

Candidate isNOTqualified andNOTdeployed. Original livebackend/model/UIunchanged;
pronunciation_available=false/tajweed_available=false remain truthful. Report:
/tmp/qari-pronunciation-gpu-20261018/docs/human_word_error_result_20261019.md,
durablecopyunder /home/innocent/qari-training-artifacts/pronunciation-human-data-20261018/
human-word-experiment/human-word-error-result-20261019.md. GPUaudit/head/reports/
predictions inpacketoutput-v3. CPUresultsandlog inhuman-word-experiment.

Nextresearchrequires separatevowel supervision, enoughpureerror/correcthuman
examples, qualifiedword-local acoustic evidence and independent speakers/surahs.
DoNOTlowerguards, labellexicalASRcorrectaspronunciationcorrect, retuneonheldscores
orclaimfullyfixed. BroadIqragateddatastill403. ExistingresearchdraftPR38contains
boundedtrainingloaderfixb7c230a; full1029passed1skip2knownwarnings andallCIpass.
