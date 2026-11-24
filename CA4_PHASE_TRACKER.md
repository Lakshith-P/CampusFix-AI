# CampusFix AI — CA4 implementation and evidence tracker

This tracker separates code delivered in the repository from external approvals, live-provider checks and deployment evidence. A feature is not marked PASS merely because a UI control exists.

| Phase | Requirement | Repository status | Evidence / remaining action |
|---|---|---|---|
| 1 | Project definition and faculty title approval | PARTIAL / EXTERNAL | Project definition is documented. Obtain faculty approval and retain signed/email evidence. |
| 2 | Full-stack foundation | IMPLEMENTED — LOCAL TEST | FastAPI, SQLAlchemy, React/Vite, role-aware API and local setup are present. Student report form exposes text/photo/audio/PDF choices and audio recording; assigned workers can upload evidence. Run frontend production build on the target workstation. |
| 3 | LLM gateway, at least three providers/models | IMPLEMENTED — CONFIG-DEPENDENT | Groq, Gemini and OpenRouter text adapters; Groq Whisper audio; Gemini image; local pypdf. Live provider calls require valid keys/quota. |
| 4 | Model selection, routing, fallback, comparison | PARTIAL — modality-aware manual/auto; text compare | Admin AI Studio has Text/Vision/Audio/Document tabs and backend capability allow-lists; manual and automatic compatible routing are wired. Provider/model selector race fixed when switching modality before catalog load. Student and assigned-worker portals now expose modality-specific evidence workflows. Two-model comparison is text-only. AC-associated water leakage is deterministically routed to HVAC and flagged for human review. Two-model comparison is text-only. Live provider execution still needs testing. |
| 5 | Prompt engineering, untrusted/trusted separation, versioning | PARTIAL | System prompt treats complaints/attachments as untrusted and limits action claims. Add formal prompt registry/version history before claiming full completion. |
| 6 | Structured output/schema validation/retries | IMPLEMENTED — TEXT PATH | Pydantic classification schema and provider retry/fallback logic. Modality extraction outputs remain extraction text and require human review. |
| 7 | Multi-stage orchestration | PARTIAL | Attachment extraction → classification → verification → deterministic specialist suggestion exists in complaint flow. Expand explicit stage trace and per-stage retry policy. |
| 8 | Independent second-model verification/disagreement | IMPLEMENTED — CONFIG-DEPENDENT | Second configured text provider compares category/priority/department; missing verifier or disagreement triggers review. Verify with two live providers. |
| 9 | Deterministic business logic/authorization/human approval | IMPLEMENTED — LOCAL TEST | Role checks, specialist matching, status/assignment controls, duplicate checks and human-review flags are backend controlled. |
| 10 | Token/cost/budget/context management | PARTIAL | Input truncation, token estimates and monthly budget gate exist. Estimates are approximate; confirm cost accounting against current provider pricing. |
| 11 | Security/failure handling/prompt injection | PARTIAL | Password hashing, signed tokens, role gates, untrusted-input boundary, upload size/type validation and controlled provider errors. Conduct a deployment security review, rate limiting and malware scanning before production. |
| 12 | Database/audit/observability | IMPLEMENTED — BASELINE | SQLAlchemy records, audit events, AI usage and health/status endpoints exist. Add retention policy and external monitoring for production. |
| 13 | Ten evaluation tasks and evidence | PARTIAL — 31 LOCAL TESTS; formal evidence pending | Automated evaluation tests (31 passing in this packaging environment) cover schema failures, injection boundary, location conflicts, long context, provider outage, disagreement, missing verifier, worker specialization and AC water-leak routing. The complete ten-scenario evidence pack still requires real demonstrations and screenshots. Run all ten formal scenarios and capture exact input, expected/actual, logs, screenshots and PASS/FAIL evidence in the report. |
| 14 | ByteXL Nimbus deployment (compulsory) | NOT DEPLOYED | Deploy the backend/frontend to the required Nimbus environment, configure secrets and verify public health/auth/workflows. Render/Vercel alone does not satisfy this requirement. |
| 15 | Report and viva | PARTIAL | Prepare the final report, architecture, model rationale, test evidence, deployment screenshots and viva answers after phases 13–14. |

## Ten formal evaluation scenarios

1. Incomplete input — reject/ask for missing required information; do not fabricate a location.
2. Contradiction detection — conflicting block/room/date/time details require clarification.
3. Hallucination prevention — the assistant must not claim unseen causes or completed repairs.
4. Invalid structured output — reject schema-invalid JSON and use bounded retry/fallback.
5. Prompt injection — complaint/file text cannot override system policy or request secrets/actions.
6. Multi-model disagreement — flag for human review.
7. Provider failure/fallback — show controlled failure or configured safe fallback; never route to a paid provider.
8. Long context/token limits — truncate within configured limits and expose the truncation.
9. Budget — stop AI execution when the configured monthly budget gate would be exceeded.
10. Deterministic business rule — duplicate and unauthorized actions are rejected by backend rules.

## Current implementation notes

- `/ai/catalog` lists providers and modality capabilities without exposing credentials.
- `/ai/execute` accepts multipart execution requests and validates modality/provider/model server-side. `provider=auto` chooses a configured free-capable provider for that modality.
- Text classification uses structured Pydantic output. Vision uses Gemini image understanding; audio uses Groq Whisper; PDF text extraction uses local pypdf. Student image/audio/PDF complaints enter extraction → classification → verification → specialist suggestion; assigned workers can attach and analyze evidence. AC water leaking from an air-conditioning unit is routed to HVAC, with human review required.
- AI Studio comparison currently supports text models only. Vision/audio/PDF output is treated as untrusted evidence and requires human review.
- Free-tier availability, quota and model names are controlled by vendors. A configured key does not guarantee a live request will succeed.


## v2.6.0 additions

- Student portal: explicit text, image, audio and PDF selection; browser audio recording; multimodal upload flows.
- Admin portal: API-backed account/role administration, AI monitoring, usage, worker list and audit pages; ten-scenario evaluation checklist.
- Backend tests rerun in this release: 31 passed. Frontend build not verified here because `npm ci` timed out/incomplete.
- OCR for scanned PDFs and multi-model vision/audio comparison are not implemented; do not mark them complete.

## 2026-11-24 focused completion update
- Added centralized prompt registry and authenticated `GET /ai/prompts` manifest. Active prompt versions are complaint triage 1.1.0, vision 1.0.0, audio 1.0.0, document extraction 1.1.0.
- Reworked `/ai/compare-multimodal` so both selected modality adapters receive the same original attachment bytes and return separate outputs; partial failures/disagreements require human review.
- Vision comparison requires configured Gemini and OpenRouter vision-capable model. Audio comparison supports Groq Whisper and Gemini audio. Document comparison requires an explicitly configured distinct Gemini PDF-capable secondary model (`GEMINI_DOCUMENT_SECONDARY_MODEL`).
- Scanned PDF OCR uses Gemini visual PDF input when embedded text is absent; pypdf and PyMuPDF handle text PDFs/parser fallback.
- Local verification: Python compileall passed; backend pytest suite 32 passed. Live provider, real scanned-PDF OCR, frontend compare wiring, and Nimbus deployment remain environment-dependent and are not claimed as verified.
