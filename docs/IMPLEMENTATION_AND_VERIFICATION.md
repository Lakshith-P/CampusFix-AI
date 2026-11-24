# Implementation and verification record — v2.6.0

## Source changes in this release

- Updated release/API version to 2.6.0.
- Added `auto_provider_candidates()` as the single capability-aware free-provider ordering function.
- Automatic text execution now attempts configured Groq → Gemini → OpenRouter adapters in order. Failed attempts are audited. If every configured free provider fails, the request returns a controlled 502; no paid provider is attempted.
- Automatic vision/audio/document selection remains constrained to the one supported adapter for each modality (Gemini, Groq Whisper and local pypdf respectively).
- Added explicit prompt version identifier `complaint-triage-v1.0.0` to AI catalog metadata.
- Updated AI Studio explanatory text so it no longer claims that automatic mode is UI-only.
- Added browser-recording `audio/webm` to supported audio MIME handling.
- Added unit tests for automatic provider ordering, budget rejection and prompt versioning.
- Replaced phase tracker with evidence-based completion statuses and added a ten-scenario evaluation evidence pack.

## Verification actually run during packaging

Command:

```text
python -m compileall -q backend/app backend/tests
python -m pytest -q
```

Result:

```text
31 passed in 2.41s
```

Frontend dependency installation (`npm ci`) did not finish before the packaging environment timeout. Therefore the frontend production build is **not verified** in this record. No live Groq, Gemini or OpenRouter API call was made. No ByteXL Nimbus deployment was performed.

## Known limitations / open work

- Faculty approval is external and must be attached by the student.
- Live model availability, API-key validity and provider quota require local testing.
- Gemini is the only configured vision provider; Groq Whisper is the only configured audio provider. There is no cross-provider failover for those modalities.
- PDF support extracts embedded text; scanned PDFs need OCR.
- Text comparison is supported; multimodal multi-model comparison is not implemented in this release.
- The 28 automated tests do not constitute the final ten-scenario evidence pack; screenshots, live API logs and database evidence are still required.
- Nimbus deployment and deployed end-to-end test remain mandatory and outstanding.
- The frontend build must be run locally and its result recorded.
