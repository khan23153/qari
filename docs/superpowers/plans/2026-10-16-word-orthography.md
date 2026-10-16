# Recitation spelling repair implementation plan

**Goal:** Recover independently recognized Ya-Sin words while preserving lexical identities, confidence and bounded memory.

**Architecture:** Preserve final maqsura after ya so Yahya remains distinct from yuhyi. Add three spelling pairs verified against a separately published Imlai Quran edition, filtered against global canonical collisions. Join independently decoded vocatives using the entire Quran vocabulary and emission times, never selected-reference hints.

**Constraints:** Existing models, .55 confidence, .006 RMS, speech budget, 240-second single pass / 30-second long-review slices and 6 GiB production cap stay in place. Isolated tests and recording replays have 3500 MiB memory and no swap. UI stays unchanged.

1. Write failing production-boundary tests for all three spelling pairs, Yahya/yuhyi separation, joined vocatives, missing/weak particles, long pauses and wrong following words. Run and inspect failures.
2. Implement the minimal normalization, published spelling and timed vocative changes; run focused and complete recitation/ml/api suites.
3. Replay all 829.85 seconds privately using original models under 3500 MiB. Validate each targeted index, silence, wrong speech and existing short recordings. Measure peak memory. No unbounded decoder call is permitted.
4. Review the complete diff, commit and push. Deploy with existing compose configuration only after checks pass. Verify code hashes, memory cap, real public WebSocket results and restart/OOM status.

**Evidence:** published-quran-simple-clean.json SHA256 e9f87186120851fbf1e04813a423076850e1b6b9ad769a797117dca623aad4af; independently published quran-simple-clean edition, https://api.alquran.cloud/v1/quran/quran-simple-clean . Ya-Sin12 nحيي,78 يحيي and23/54/82 شيئا. No held-out audio is used as a training label.
