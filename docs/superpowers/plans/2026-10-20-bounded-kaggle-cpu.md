# Bounded Kaggle CPU execution plan

Spec: docs/superpowers/specs/2026-10-20-bounded-kaggle-cpu.md
Execute inline, preserve isolated worktree/PR39 and root production.

## Review focus

Local CPU limits must remain64words/3epochs; remote scope cannot start on the
currentVPS or write outside/Kaggle working. Honest actual CPU device, unchanged
statistical/model/data protocol and fixed support floors, CPU memory/disk/deadline
checks and no CUDA API dependency. Do not pick a backend using held scores.

### Task 1: Explicit remote CPU bounds and resource checks

Files: ml/training/local_vowel_head.py,ml/training/kaggle_phoneme_job.py and tests.
Consumes explicit device='kaggle_cpu', guarded environment/output and existing
feature manifest. Produces same FP32 CPU head/report with scope metadata; normal
CPU64/3 and CUDA paths remain unchanged.

- [ ] RED guards/resource tests and actual75word/4epoch bounded fixture.
- [ ] Implement explicit context, separate actual/limits devices and CPU reserves.
- [ ] Focused/full suite, one fresh review; verified fixes if required; commit.

### Task 2: Observed free private CPU fallback when needed

Files: external private packet/observer; context.md and experiment report.
Consumes identical1393source cohort and frozen native features/head protocol.
Produces actual execution report/held breakdown/CPU portability if a head exists.

- [ ] CheckT4 before submission; if started, use it without a CPU duplicate.
- [ ] Otherwise source-verify privateCPU job; observe native readiness/progress.
- [ ] Follow spec's start-time decision, cancel only our superseded queued run;
never choose using held scores. Monitor to actual terminal state.
- [ ] Retrieve small results; preserve qualification false and all limitations.
