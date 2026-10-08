## Session 2026-10-08 — Live recognition overlap confidence recovery

- Build 74 screenshots show matched words appearing live and the same words
  confirmed in review. Hifz still hides unconfirmed text intentionally; all
  numbered ayah medallions remain visible. These screenshots do not establish
  what the user actually recited or the deployed model's transcript.
- Reproduced a backend tracking defect using the production speech gates and
  matcher: an initial low-confidence Allah token stayed at 0.2 when the next
  overlapping independent decode reported it at 0.95. Stitching deduplicated
  the new token but discarded its clearer evidence; no live match was sent.
- `stitch_hypothesis` now replaces the overlap with the latest token/score
  pairs, preserving indices and non-overlapping history. Latest lower scores
  also replace older higher scores; do not pool maximum scores or loosen the
  confidence, silence, speech-budget or independent-witness guards.
- Three regression tests were observed failing before the fix. Validation:
  75 recitation API tests and 166 ML/legacy API tests pass locally. Model decode
  fixtures are controlled; this does not measure real model accuracy.
- Public aiquranic.com /health returns core API OK, not ASR readiness. No VPS
  connection or authenticated live-session logs are available in this runtime.
  The backend change still requires production deployment and real-mic checking;
  rebuilding an unchanged APK alone cannot apply this server-side correction.
