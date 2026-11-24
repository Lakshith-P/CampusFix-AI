# Build verification record — consolidated local VS Code build

Verification date: 2026-11-23. Scope: source code and backend tests executed in the packaging environment. This is not a live provider or cloud deployment certification.

| Check | Result | Evidence / limitation |
|---|---|---|
| Python compileall | PASS | `python -m compileall -q app seed_synthetic_data.py tests` |
| Backend pytest suite | PASS | `PYTHONPATH=. python -m pytest -q` — 30 passed |
| Auth password hashing | PASS | PBKDF2-HMAC-SHA256 hash/verify tests |
| Auth token integrity | PASS | HMAC-signed JWT-compatible token tamper test |
| Complaint API role tests | PASS | Registration/login, protected endpoint, student access, create/list, incomplete input, duplicate rejection |
| AI evaluation tests | PASS | Schema validation, malformed JSON, long input, injection boundary, provider outage fallback, missing verifier, disagreement, location/date/time conflicts, HVAC skill matching, AC water-leak-to-HVAC routing and student multimodal complaint workflow |
| SQLite schema migration | Source check | Adds `specialization` and `available` columns to older SQLite databases at API startup; not tested against a user's existing production database |
| Frontend production build | NOT VERIFIED | `node_modules` absent; npm registry unavailable in this packaging environment (`ENOTCACHED`) |
| Browser/UI end-to-end | NOT VERIFIED | Requires local browser run after `npm install` |
| Live Groq/Gemini/OpenRouter | NOT VERIFIED | Requires user-owned API keys and network access |
| Student multimodal complaint workflow | PASS — MOCKED ADAPTER TEST | Student image submission is tested with a mocked vision extractor; actual Gemini request still requires live key/quota. |
| Worker multimodal evidence workflow | IMPLEMENTED — LIVE TEST PENDING | Assigned workers can upload image/audio/PDF evidence; extraction and audit are wired. Verify with a live worker session and provider key. |
| Image/audio/PDF provider workflow | NOT VERIFIED LIVE | PDF extraction is local for embedded text; image/audio require live provider keys |
| Multi-provider comparison | Code present; live behavior NOT VERIFIED | Requires two configured provider keys |
| Nimbus deployment | NOT DONE | Must be deployed and tested in the user's ByteXL Nimbus workspace; deployment instructions supplied |
| Title approval | NOT PROVIDED | Attach faculty approval evidence |

A passing backend test suite does not prove live provider availability, frontend build success, Nimbus deployment, or all ten evaluation demonstrations against external services. Do not mark Phase 14 complete until Nimbus evidence and public URL are recorded.
