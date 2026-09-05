# Qari Resume

## 1. CURRENT STATUS

- V4.5 TRAINING = NO-GO
- No V4.5 training has happened
- Never resume V1/V4.1/V4.2/V4.3/V4.4 checkpoints

## 2. CURRENT EXACT TARGET

- Immediate unresolved target: `52:8`
- clip_id: `4767f47ae36fbb7649a5`
- Goal: resolve its actual spoken words and human ayah identity
- Allowed outcome: `CURRENT_CONFIRMED`, `CANDIDATE_CONFIRMED:<ayah>`, `AMBIGUOUS_OR_FRAGMENT`, or `UNRESOLVED`

## 3. CURRENT HUMAN STATE

- `26:48` / `7ccb317b8b94ffaaf99b`: `CURRENT_CONFIRMED`
- `35:30` / `dc9ff8a461787a2eed6b`: `AMBIGUOUS_OR_FRAGMENT`
- `52:8` / `4767f47ae36fbb7649a5`: `UNRESOLVED`

## 4. CURRENT EVIDENCE TASK

Prepare/maintain a compact `52:8` review packet containing:

- TARGET audio path + SHA256
- Whisper-small evidence transcript
- CURRENT `52:8` six refs + transcripts + SHA256 + duration
- CANDIDATE `52:9` six refs + transcripts + SHA256 + duration
- CANDIDATE `52:1` six refs + transcripts + SHA256 + duration
- apparent partial/cross-ayah continuation evidence

Model output is evidence only. Do NOT assign semantic truth automatically.

## 5. AFTER 52:8

- complete target adjudication
- human-review affected reference-bank rows
- exclude/resegment only from recorded human decisions
- preserve partial/cross-ayah metadata explicitly
- rebuild immutable human-reviewed reference bank/control
- compute deterministic SHA256
- rerun Stage2 with unchanged strong margin `0.05`
- even if Stage2 passes, run a larger fresh untouched negative-specificity control
- only then continue toward final manifest freeze and Base V4.5 harness

## 6. IMPORTANT DATA STATE

Current cleaned corpus:

- `/home/ubuntu/qari-tlog-clean-v3.1/train_manifest_clean_v3_1.jsonl`
- rows: `57544`
- SHA256: `e378f5bd402a18c0eb9c0d74d94d7f01af130943694a381a812b2347af289ace`

Do NOT overwrite Clean-V3.1.

FALSE3 bundle:

- `/home/ubuntu/qari-stage2-false3-audit.zip`
- SHA256: `75e68e31e2afeaebde0d4dec18d38d8a2add7c36ab75d70e2b3fb456a5f2eab5`

Kaggle FALSE3 dataset: `telethonfool/qari-false3-audit-v1`

Current transcription kernel: `telethonfool/qari-false3-transcribe-v1`

## 7. RESUME COMMANDS

Kaggle:

```bash
source ~/kaggle-cli/bin/activate
```

Audit venv:

```bash
source ~/qari-audit-venv/bin/activate
```

Prep venv:

```bash
source ~/qari-v42-prep/venv/bin/activate
```

Never install Torch in `qari-v42-prep`.

If Kaggle auth expires:

```bash
kaggle auth login --force --no-launch-browser
```

## 8. SAFETY / WORK RULES

- Do not train while status is NO-GO
- Do not relabel from model output alone
- Human review outranks model hypotheses
- Do not mutate Uthmani/Imla'i text silently
- Do not overwrite frozen artifacts
- Version every new control/report/manifest
- Record SHA256 + source hashes + row counts
- Do not use `exit 1` or `set -e` in interactive shell blocks
- Do not commit private audio or secrets

## 9. FIRST ACTION AFTER LOGIN

On every new session:

1. Read `QARI_RESUME.md`
2. Read `/home/ubuntu/qari-agent-state/QARI_RECOVERED_STATE.md`
3. Read `/home/ubuntu/qari-agent-state/QARI_NEXT_GATE_REPORT.md`
4. Verify current files/hashes before changes
5. Continue from CURRENT EXACT TARGET
6. Do not ask the user to restate project history if local evidence answers it

## 10. LAST UPDATED

- UTC: `2026-09-05T18:38:14Z`
- Git HEAD: `081dc92cee82f927b26d0b68d1bf78173902a0da`
