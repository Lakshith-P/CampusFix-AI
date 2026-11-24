# CampusFix AI — CA4 phase and evidence tracker (v2.6.0)

**Status convention:** “Implemented” means code exists; “verified” means a local test or inspection was actually run; “external evidence pending” means a faculty/platform action or live-provider run is still required. A phase is not called complete merely because a route, document, or test stub exists.

| Phase | What this release contains | Verification in this workspace | What remains before claiming complete |
|---|---|---|---|
| 1 — Project definition | Project proposal, problem, roles, input/output types, data entities and workflow drafts | Documents present | Obtain faculty title/proposal approval and retain approval evidence |
| 2 — Full-stack foundation | React/Vite UI, FastAPI API, SQLAlchemy persistence, authentication, role-scoped complaint CRUD and status rules | Backend suite: 31 tests passed; frontend production build not verified here | Run frontend build; fresh-install browser test for student, staff and admin; retain screenshots and DB evidence |
| 3 — LLM gateway | Backend-only Groq, Gemini and OpenRouter text adapters; Groq Whisper audio; Gemini image; local pypdf document extraction | Adapter code inspected; no live provider request performed in this workspace | Configure keys locally and capture successful/failed live requests for each enabled provider |
| 4 — Model selection | Capability allow-list; manual provider/model selection; automatic text routing tries configured free providers in order; modality-specific auto adapter; text comparison endpoint | Automatic candidate selection covered by unit test; backend suite passed | Live provider failover trace and representative model quality/latency comparison; vision/audio have one supported cloud adapter each, so cannot fail over to another model |
| 5 — Prompt engineering | Trusted system prompt, untrusted complaint boundary, JSON response contract, prompt catalogue and explicit `PROMPT_VERSION` | Prompt-boundary and prompt-version tests passed | Record a prompt experiment and a real injection demonstration with logs |
| 6 — Structured output | Pydantic output schema, parsing/validation and bounded provider retry/fallback | Valid/invalid/malformed schema tests passed | Capture provider response/retry evidence for report |
| 7 — Multi-stage orchestration | Attachment extraction → classification → independent verification → specialist suggestion → DB write → audit | Pipeline code inspected; unit/API tests passed | Live end-to-end evidence for text, image, audio and PDF; verify each resulting DB row and audit event |
| 8 — Multi-model verification | Independent second configured text provider; structured category/priority/department comparison; human-review flag on disagreement or unavailable verifier | Mocked disagreement and missing-verifier tests passed | Live two-provider agreement and disagreement evidence |
| 9 — Deterministic business logic | RBAC, duplicate detection, specialist/availability validation, status transitions, resolution note requirement and backend authorization | Existing API/business-rule tests passed | Capture admin/staff/student role and rejected-action screenshots/logs |
| 10 — Cost, token and context | Token estimate, bounded input, monthly budget gate, usage table and estimated-cost tracking | Long-context and budget-gate tests passed | Record actual provider usage and demonstrate budget block using configured local budget |
| 11 — Security and failure handling | Server-side credentials, signed tokens, salted password hashes, upload MIME/size checks, untrusted-input boundary, retry/fallback, no paid fallback | Auth, validation, injection and provider-exhaustion tests passed | Run live invalid-key, rate-limit, timeout, file-type and secret-scan checks; rotate any exposed keys |
| 12 — Database, audit and observability | Persistent complaints/attachments/users, AI usage, audit trail, admin metrics/usage/audit endpoints and complaint history | API tests passed; endpoints present | Browser verification and retained audit/usage screenshots after real executions |
| 13 — Mandatory evaluation | Automated checks cover all ten required behaviour categories; exact scenario catalogue in `EVALUATION_EVIDENCE_PACK.md` | 31 backend tests passed locally | Execute and record all ten scenarios in the running app, with expected/actual output, screenshots, API/log/DB evidence and final PASS/FAIL |
| 14 — ByteXL Nimbus | Docker files and Nimbus deployment guide | **Not deployed** | Deploy on ByteXL Nimbus; test deployed frontend→backend→database→LLM; submit public frontend URL and logs |
| 15 — Final report and viva | Report outline, architecture, phase map, prompt catalogue, evaluation pack and viva topics | Draft material present | Populate measured results, approval proof, screenshots, evaluation outcomes and Nimbus URL; rehearse viva against actual code |

## Mandatory ten evaluation categories

1. Incomplete input handling.
2. Contradictory information detection.
3. Hallucination detection and prevention.
4. Invalid structured output handling.
5. Prompt injection and instruction conflict handling.
6. Multi-model disagreement and verification.
7. LLM provider failure and fallback.
8. Token limit and long-context handling.
9. Cost and budget constraint handling.
10. Deterministic business rule and transaction validation.

See `EVALUATION_EVIDENCE_PACK.md` for the test matrix and evidence fields. The 31 passing automated tests are not a substitute for the brief's required live demonstrations and screenshots.

## Important deployment note

The CA4 brief explicitly requires ByteXL Nimbus. A local VS Code run, Render backend or Vercel frontend does not by itself satisfy Phase 14 unless the faculty explicitly approves an alternative in writing.
