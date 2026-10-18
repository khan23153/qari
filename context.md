# Qari — working context and VPS handoff

Last verified: **2026-10-18, 12:25 UTC**; later progress is appended below. Paths refer to this VPS.
This file records verified runtime state, historical evidence and unfinished work
separately. It contains no passwords, API tokens, OAuth codes or signing secrets.

## Current outcome — read first

The strict lexical repair is deployed at **afe3dc63abcfca5eaaba789b9df8195085cca59e**.
It prevents similar-but-different ASR text from earning a correctness verdict;
sequence placement and native occurrence/confidence guards remain separate.
**866 backend tests,193 Flutter tests and8 public paced WSS cases pass.**
Full Ya-Sin yielded724/725; the removed old green had expected ننكسه but native
text نركزه. This was an incorrect textual acceptance, not a verified speaker error.

**Pronunciation/grammar grading is still unresolved.** ASR/normalization loses
short vowels and shadda; high word confidence cannot certify adaegi or tajweed.
Baqarah and repeated-phone recognition still have misses. Full repetition-warning
work remains in its separate unqualified worktree. Summary UI source distinguishes
matched/unconfirmed words and unavailable pronunciation, but **no new APK was
released**: existing signing certificates differ and a compatible release key is
not configured. Existing APKs use the deployed backend without reinstalling.
See sections3,6,8,11 and the final progress entry for exact state and next work.

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
a particular tester said. The matcher also has spelling/article/alef/phonetic
tolerances. ASR can output the expected written word despite a spoken error.
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
| Backend source/image revision | **`afe3dc63abcfca5eaaba789b9df8195085cca59e`** |
| Running recitation container | `infra-recitation-api-1` |
| Image ID | `sha256:e2fd5f3959afd20b4f76d1a96815b469abe642ad56e491312c1e963bc88eb80e` |
| Qualified image tag | `infra-recitation-api:lexical-precision-20261018` |
| Running since | Oct 18 12:18:48 UTC |
| Health/restarts/OOM | healthy; 0 restarts; not OOM-killed |
| Memory/swap ceiling | 6 GiB / 6 GiB total; host has no swap |
| Live source bind mount | host `ml/` → `/app/ml:ro` |
| Reference bind mount | `backend/recitation_api/reference_data` → `/app/reference_data:ro` |
| Model bind mount | host `models/` → `/app/models:ro` |
| Saved audio volume | `/var/lib/docker/volumes/infra_qari_audio/_data` → `/tmp/qari_audio` |
| Private recitation port | `127.0.0.1:8001` |

Running SHA256 values, independently rechecked October 18:

- `app.services.streaming_session`: `27b778f91fcad4f4fe54dac1399cd390fcba03b0601eb4032f9138e995e42721`
- `ml.alignment.streaming_matcher`: `850be9d1ea298e4a023c8cbdfb5757ef00da68470bb8c57636bdb3a3cab6d1bb`
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

Current repair PR: https://github.com/khan23153/qari/pull/34. Public qualification passed8cases. Models are unchanged; deployed source is afe3dc6. The checkout may have a later documentation-only commit; compare image revision and source hashes for backend identity.

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
| Exact repeated4word phrase shifted final review to wrong later words | **Fixed in afe3dc6** with bounded confirmed rereading insertion; warning events remain separate/unfinished |
| Incomplete recognized subset could show100% / ambiguous pronunciation claim | UI source fixed and tested in PR34; **APK not released** because compatible signing key is unavailable |

Current afe3dc6: **866backend tests pass,1optional skip;193Flutter tests pass**. All14recording/controlcases qualified; fullYaSin724/725 with941freshnativecalls, old725thwas falsegreen ننكسه←نركزه. Other13cases reused exact PCM-matched native decodes with unchanged model/normalizer fingerprints. Baqarah148live166final/230; repeatphone23live28final/29 remain recognition limitations. Public paced WSS qualification passed8cases, including bothmodes, byte-identical savedPCM, allayahmarkers, missing/wrongword, silence/noise/wrongsurah.

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
| Kaggle CLI | `/home/innocent/kaggle-cli/bin/kaggle`; not on default PATH. Current host authenticated `kernels list --mine` **failed**, so do not claim an active login |
| Kaggle historical account/job | **telethonfool**, e.g. `telethonfool/qari-conformer-quran-fp32-20261009`; old terminal logs exist |
| Kaggle helper | `/tmp/qari-conformer-training-20261009/kaggle_version_status.py` reads token via hidden prompt; never place token in a shell argument or context file |
| Hugging Face | No default `hf`/`huggingface-cli` or persistent `~/.cache/huggingface/token` was found; historical token use is not current authenticated access |
| HF private helper | `/tmp/qari-training-submit-20261008/hf_own_models.py` uses hidden input; do not run a blocking login flow without current need |
| Cloudflare | Existing tokenized tunnel container is running; dashboard/CLI account login has not been independently verified here. Do not print container args/env |
| Docker/FFmpeg | `/usr/bin/docker`, `/usr/bin/ffmpeg` |
| Flutter SDK | `/home/innocent/flutter/bin/flutter` |
| Deployment credentials | `/home/innocent/qari/infra/.env`; JWT, database and deployment values stay private |

User supplied HF/Kaggle tokens and OAuth callbacks earlier in chat. They are not
repeated here and must not be copied into git, reports, process arguments or logs.
Only credential locations, scopes/status and public account handles are recorded.
Do not replace the connected Drive account or log out again unless requested.

## 11. Next work, in priority order

1. Obtain independently reviewed correct/incorrect pronunciation labels from the
   preserved51 tester WAV/results. The user cannot identify exact changed words;
   do not ask the same question again or blame a speaker for ASR disagreement.
2. Qualify a distinct acoustic detector for vowels, shadda, makhraj and tajweed.
   Text equality and expected-reference alignment alone cannot establish these.
   Measure false acceptance and false accusation separately across speakers.
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
6. Preserve PR34 and completed qualification evidence. Current backend is deployed;
   no need to repeat training, corpus lookup, completed tests or old OAuth login.
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
  -v /tmp/qari-live-gap-repair-20261016:/repo:ro \
  infra-recitation-api:completed-phrase-guard-20261016 \
  -m pytest backend/recitation_api/tests ml/tests api/tests -q -p no:cacheprovider
```

The current live root has bind-mounted ML code. **Do not edit product ML files
there while preparing an untested change.** Work in the existing isolated tree.
For rollback, restore/pin the old mounted ML files as well as the previous image;
image-only rollback is incomplete. Existing overrides and deployment scripts are
under `phone-fatihah-repeat-20261016/`; read and update their pinned revisions and
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
