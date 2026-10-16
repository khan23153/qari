# Live encoder padding qualification

Short live audio was padded to 30 seconds by Faster-Whisper's feature extractor. On the two-core deployment, independent CPU INT8 recognition averaged about 2.5 seconds per pass. Live recognition now uses a separate model/extractor view and the supported `chunk_length` option, retaining a 15-second acoustic padding floor and the existing 30-second maximum. Concurrent generators cannot change the shared extractor used by other sessions or timestamped final review.

The 15-second floor is deliberate: an initial audio-length-plus-tail crop introduced two confirmed red events on the older presumed-correct Al-Fatihah recording. It was withheld. The 15-second version retains the baseline live matches and introduces no confirmed red events in the paired recordings and reference fixtures.

The existing models, Arabic decoding, unprompted recognition, beam size 1, temperature 0, 64-token cap, tier2 policy, confidence 0.55 and RMS 0.006 remain unchanged. No Flutter/UI code changes. Confirmed words remain the only Hifz reveals; unresolved gaps stay neutral and all ayah markers remain visible.

## Native model replay

| Recording | Baseline matches | 15-second padding matches | Baseline mean decode | New mean decode | Confirmed red events |
|---|---:|---:|---:|---:|---:|
| Older full phone Al-Fatihah, 36.92s | 5/29 | 5/29 | 2.531s | 1.390s | 0 |
| Latest partial phone capture, 28.12s | 4 of 29 selected words | 4 of 29 selected words | 2.575s | 1.510s | 0 |
| Reference Al-Fatihah | 29/29 | 29/29 | 2.457s | 1.447s | 0 |
| Reference Al-Ikhlas | 11/15 | 11/15 | 2.496s | 1.477s | 0 |
| Al-Ikhlas with Al-Fatihah selected | 1/29, cursor 2 | 1/29, cursor 2 | 2.462s | 1.484s | 0 |
| Digital silence | 0 events | 0 events | — | — | 0 |

The user clarified that the latest recording is partial; its count is coverage of the selected page, not a complete-recitation accuracy score. The older recording is the primary full-recitation comparison.

Additional real-ASR checks: seeded Gaussian noise at RMS 0.06 produces zero events; four seconds of reference speech followed by 20 seconds of silence or noise produces four matched words, no late reveals and no completion. These are offline replay measurements on the actual VPS CPU, not microphone-to-screen latency.

Fresh automated checks: ML plus API 183 passed; recitation API 76 passed (259 total). Seven encoder tests cover the padding floor, distinct concurrent chunk lengths, unchanged timestamped review and the 30-second maximum. The updated tests first failed on the earlier aggressive crop (5 failures, 2 passes), then passed on the qualified floor. Independent code review found no release blocker.

An initial recitation-suite invocation used a signing key different from its test fixture, causing 27 authentication/configuration failures. Rerunning with the fixture's documented test key passed all 76; no production authentication change was made. Existing dependency deprecation/optional SOCKS warnings remain.

## Recognition limitation

This change reduces decoding work; it does not recover the words missed by the independent ASR on the older phone recording. The controlled overlap-confidence bug is fixed, but acoustic transcripts remain incomplete/incorrect before matching. A completed private original Whisper Turbo GPU diagnostic matches 11/29 on the older phone recording and 29/29 on reference Al-Fatihah; a trained Conformer matches 12/29 on the older recording with one unverified confirmed red event. Neither candidate is deployed. Full-file decoded word counts do not establish accurate recognition or correct pronunciation.
