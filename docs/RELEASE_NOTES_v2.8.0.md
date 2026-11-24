# CampusFix AI v2.8.0 — UI and role-access update

## Included in this working release
- Refreshed dashboard styling with warmer layered surfaces, improved spacing, clearer metric cards, complaint rows, responsive navigation and AI workspace presentation.
- AI Studio navigation is now available to authenticated Student, Maintenance Worker and Administrator accounts.
- `/ai/catalog`, `/ai/execute` and `/ai/compare` now require authentication rather than administrator-only access. Provider secrets remain server-side.
- Student-owned complaints can edit title, description and location while status is `submitted` or `assigned`; edits are rejected after work starts. Existing ownership checks remain in place.
- Vision prompt now asks for fixture-level identification (tap/faucet, sink mixer, pipe, valve, etc.). A tap/faucet leak detected in the multimodal evidence is refined to `Plumbing - Tap/Faucet`, with cause uncertainty and human review retained.

## Verification
- Backend compileall: passed.
- Backend pytest: 31 passed.
- Frontend dependency installation timed out in this build environment; TypeScript/Vite production build is therefore **not verified**.

## Still incomplete / known limitations
- Compare mode is text-only. Vision/audio/PDF multi-model comparison is not implemented.
- Vision is Gemini-only; audio transcription is Groq Whisper-only; PDF extraction is local pypdf. These are not multi-provider per modality.
- The student/worker AI Studio is shared and authenticated, but the complaint submission and worker evidence forms do not yet expose full manual/automatic/compare provider selection controls.
- Scanned-PDF OCR is not implemented.
- Live API calls, browser end-to-end flows, and Nimbus deployment have not been verified.
- Admin provider credential configuration is via backend `.env`; no UI-based secret editor was added.

Do not represent this release as a complete implementation of all requested multi-provider/multi-model features.
