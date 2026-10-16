# Known Quran word identity in live matching

An independent ASR decode of Ikhlas emitted Allah with confidence 0.725 while Fatihah was selected. Generic one-alef tolerance matched this to lillah and incorrectly revealed that selected word. It also merged qal/qul and alam/ilm. The existing overlap-confidence fix is already present; this is a separate matching bug.

Apply known-word identity before generic alef or fuzzy similarity. Preserve exact matches, corpus aliases, article handling and the established Rahman, Sirat and Bism spelling families. When production supplies an empty vocabulary after lookup failure, reject guesses after those verified identities; preserve the legacy unspecified-vocabulary behavior.

Regression tests reproduce all six semantic pair directions, the wrong-surah reveal, explicit aliases, spelling variants and the empty-vocabulary fallback. Complete verification: 304 ml/tests + api/tests and 164 backend/recitation_api/tests pass. Independent code review found and verified the empty-vocabulary correction.

Saved real-audio verification uses the existing unprompted PCD RNNT INT8 model, production streaming session and matcher, with sample rate, RMS, transcript, native confidences, cursor and emitted events recorded privately. Fatihah recognizes 29/29 and the new proper recorder Ikhlas recognizes 15/15. The older phone Ikhlas remains 14/15: Huwa is absent in the raw ASR output despite the user confirming it was recited. Do not infer or reveal it from the selected reference. Silence, noise, wrong-surah, omitted-word and supported-substitution controls must preserve their existing guards. Saved replay is not fresh phone capture or acoustic word-end latency proof.

No model, confidence/speech policy or Flutter UI changes. Live Hifz still reveals confirmed evidence only and keeps every ayah marker; mistakes and unreached words remain in summary. Unqualified training candidates are not deployed.
