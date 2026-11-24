# CampusFix AI — consolidated build status (16 Nov 2026)

## Changes in this consolidated source
- Admin AI Studio for backend-allow-listed provider/model execution and two-provider comparison.
- Backend selected model override is passed to provider calls and checked against configured allow-lists.
- Specialist assignment uses an explicit `specialization` and `available` field rather than guessing skill from display names; SQLite startup migration adds these columns to older databases.
- HVAC/air-conditioning maps to HVAC specialization.
- Complaint status transitions are constrained; only admins can assign workers; completing work requires a resolution note.
- Contradictory block, room, date and time references are flagged for clarification.
- Replaced `python-jose` and `passlib` runtime dependencies with stdlib HMAC-SHA256 signed JWT-compatible tokens and PBKDF2-HMAC-SHA256 password hashing, so local authentication tests can run in a dependency-constrained environment.
- Updated default monthly AI budget to USD 1.00; configurable in backend `.env`.
- Updated Nimbus deployment and CA4 evidence documentation.

## Verified here
- `python -m compileall -q app seed_synthetic_data.py tests` — passed.
- `PYTHONPATH=. pytest -q` — **25 passed**.
- ZIP integrity check — run when packaging.

## Not verified here
- Frontend production build/browser tests: npm dependencies absent and registry unreachable from packaging environment.
- Live Groq/Gemini/OpenRouter calls, multimodal image/audio provider calls and real two-provider comparison: require user credentials and network access.
- ByteXL Nimbus deployment: requires user's Nimbus workspace and must be performed there.
- Faculty project-title approval and actual screenshots/evidence from the user's environment.

This is a stronger local development build, not a claim that all 15 phases have passed. In particular, Phase 14 is open until Nimbus deployment is proven. Synthetic data is fictional and must be labeled as such.
