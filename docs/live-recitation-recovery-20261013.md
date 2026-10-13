# Native streaming recovery and final-review audit

The selected surah remains matcher scope. The RNNT decoder receives audio only, with the original pinned model and native confidence/timestamp validation. The UI and speech/confidence limits are unchanged.

## Causes and behavior

- Arabic standalone waw emissions can split a connected word into two matcher tokens. Join only actual adjacent Arabic components within the bounded emission gap; preserve their union span and minimum confidence.
- A moving short audio crop changes recognition context and the frontend frame origin. Keep the ordinary 7.5-second window. Recent unresolved native evidence and the stop pass may use 20 to less than 21 seconds on an absolute one-second PCM grid. Early startup and legacy/injected transcribers retain their existing windows.
- A consumed unresolved gap can hide a word that subsequent independent decodes recognize. Repair only an existing unowned placeholder between immediately neighboring mapped, confirmed words. Both native views must identify the same occurrence, agree within one emission frame, satisfy frozen and fresh span order, and remain within the measured speech budget. No new hypothesis slot or reference progress is created.
- One confidently misdecoded word can create a transient red event. For timed RNNT evidence, require two distinct native PCM views of the same wrong word and occurrence before confirming a live mistake. Correct words and later cursor progress remain immediate.
- Re-decoding an entire long recording at stop repeats already independent recognition. Skip that pass only when every resolved prefix state has strong matching native provenance and the latest independently decoded suffix covers the current PCM endpoint, contains a complete strong reference suffix, and has no pending correction. Uncertain cases retain the independent full-recording fallback. Never pass stitched text as fresh final evidence.

## Qualification

The held-out Al-Baqarah recorder file contains verses 2:1–7 through ghishawah: 56 spoken words out of 59 displayed reference words. The last three words must stay unread. User recordings remain evaluation-only.

Initial deployed result: 51 live / 54 final words, with approximately 9.66 seconds from stop to final. The bounded context and placeholder prototype independently recognizes 56 live / 56 final words using the original model. The source-verified combined candidate passes a paced staging replay with all 56 live/final words, no false-red events, all seven ayah markers and the last three words hidden. Stored PCM is byte-identical to the input. Stop-to-final takes 1.252 seconds versus the deployed baseline of approximately 9.66 seconds. Complete native safety controls and a public replay remain release gates.

Automated candidate verification: 577 recitation API plus ML/API tests pass. Actual native and paced qualification results are recorded separately; they are not inferred from unit tests. The older Ikhlas recording is excluded from current acceptance at the user's request and remains a negative historical sentinel.
