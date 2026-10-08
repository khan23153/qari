# Full Hifz checking APK — build 74

- APK: Qari-Full-v1.0.49-build74.apk (77,146,235 bytes)
- Version: 1.0.49+74; package com.qari.app; universal ARM64/ARMv7/x86_64.
- App source: 43fdb6dc039cb4870cfa3b22400b2cafdf03959d; build commit: 7f7611f28d223df953cae3740998e6ff3d53f5df.
- Production entry: lib/main.dart. API https://aiquranic.com/v1; live socket wss://aiquranic.com/ws/recitation/stream.
- APK SHA256: 66d8d2cc4e503283ab260d964aaec41c1f9c89068dece82a1df506db6aab9b88.
- Build/artifact: https://github.com/khan23153/qari/actions/runs/37739904499/artifacts/11533512175 .
- Fix PR: https://github.com/khan23153/qari/pull/17 .

Hifz reveals only confirmed words during setup, recording and finalizing. Pending, active and missed words are fully hidden; all ornate numbered ayah medallions stay visible in their printed positions. Review retains ghost unreached text and red mistakes. Tilawat, canonical RTL rows and spacing remain unchanged.

Validation: CI 37739727114 passes formatting, analysis (no errors; existing warnings/info), and all 169 Flutter tests. Regression CI 37739202730 reproduced pending-word ghost ink and hidden markers before the fix. Real KFGQPC-font light/night live and review captures verified on pages 1, 3 and 8. Complete release build repeats the 169 tests, verifies package version/signature, and archive/CRC/hash checks match the downloaded APK. APK bundles the unchanged KFGQPC font and all three native ABIs. Authenticated microphone/model inference still requires device testing.

This checking APK uses CI debug signing, SHA256 certificate d00878ff16dc3b7dd06e3869e96caab01c0130143e4a1b56ce4e8869b67d5e5b, different from build 73. If Android refuses an update, uninstalling the old test APK is required and clears its local data. No public release/OTA metadata was changed.
