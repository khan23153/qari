# Live native recognition repair

Goal: recover independently recognized live words from the complete held-out
Ya-Sin recording while preserving lexical identity, confidence, speech guards,
original occurrence and bounded memory.

1. Trace exact saved913live native windows. Identify frame-phase variation,
   duplicated consumed evidence and frozen/missing hypothesis slots.
2. Verify40/80ms crop perturbations with original-model recognition. Write RED
   frame-origin and consumed-frame tests, implement the minimal fixes.
3. Add captured native triple fixtures and RED positive/negative backfill tests.
   Implement two-view native evidence validation and budget-bound state repair.
4. Independent review: reproduce close-rereading/reused-source issue RED; reject
   ambiguous original anchors, owned frames and non-independent policies. GREEN
   fullsuite739tests. Keep original thresholds/model/audio windows bounded.
5. Run complete original-model recording under3500MiB/no swap; final-guard replay
   must consume exactly the same941native PCM windows and preserve725live/final
   matches. Test real omitted/wrong words and existing short recordings.
6. Deploy through existing compose only after validations. Verify actual module
   hashes, image revision,6GiB limit and public paced WebSocket behavior. Report
   remaining recognition failures; do not claim global model perfection.
