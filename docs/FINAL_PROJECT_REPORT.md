# CampusFix AI — Final Project Report (Submission Draft)

**Project:** CampusFix AI: A Multimodal, Multi-Model Intelligent Campus Complaint Detection, Verification and Resolution System  
**Course:** Generative AI Foundations — CSB312  
**Assessment:** CA4 Final Project  
**Repository release reviewed:** v2.6.0

> **Accuracy statement:** This is an evidence-based report draft. It documents the v2.6.0 repository and the checks actually run. It does not claim all CA4 phases are complete. Faculty approval, frontend production build, live provider calls, the formal ten-task evidence pack and ByteXL Nimbus deployment remain outstanding.

## 1. Abstract

CampusFix AI is a campus maintenance complaint management application intended to help students report infrastructure issues and help administrators coordinate maintenance workers. It accepts text, image, audio and PDF inputs. Its backend preprocesses supported attachments, uses configured AI providers for supported tasks, produces complaint classifications, applies deterministic workflow rules and records application activity.

The application has three role-oriented experiences: Student, Maintenance Worker and Administrator. The administrator has an AI Studio for modality-aware execution and model controls. The project emphasizes backend-controlled provider credentials, capability validation, structured complaint data, worker-specialization checks, human review and auditability.

## 2. Problem statement

Universities receive maintenance complaints involving plumbing, electrical systems, air-conditioning, furniture, sanitation and campus IT. Students may not know the technical category of a problem and may provide incomplete descriptions. Manual triage can cause inconsistent categorization, delayed prioritization and unsuitable worker assignment. A text-only intake process also limits students who can explain an issue more effectively through a photograph, voice recording or supporting document.

CampusFix AI addresses this problem through multimodal complaint intake, AI-assisted extraction and classification, model routing, verification signals and deterministic backend workflow controls. AI outputs are recommendations; authorization and actual database actions remain backend responsibilities.

## 3. Objectives

- Provide a centralized complaint workflow for students, workers and administrators.
- Accept text, image, audio and PDF evidence.
- Extract relevant information and generate structured complaint recommendations.
- Provide modality-aware model selection in the administrator AI Studio.
- Support manual and automatic model execution, plus text-model comparison.
- Apply worker-specialization, authorization and status-transition rules.
- Record AI execution and workflow audit information.
- Demonstrate CA4 evaluation scenarios and document their evidence.

## 4. Users and roles

### Student
The student-facing workflow provides complaint submission with text and attachment options, including image, audio and PDF paths. Complaint records include location and issue information. Students can access complaint records and follow status workflows according to permissions.

### Maintenance worker
Workers are represented with specialization and availability information. Assignment and evidence workflows support maintenance work. Worker actions must be authorized and status changes must follow backend rules.

### Administrator
The administrator can access complaint and staff management functions, AI Studio, AI status/usage information and audit-related views. AI Studio exposes Text, Vision, Audio and Documents modes. Provider/model choices are validated by the backend capability catalogue.

## 5. System architecture

- **Frontend:** React, TypeScript and Vite.
- **Backend:** Python and FastAPI.
- **Data layer:** SQLAlchemy with the configured database.
- **Validation:** Pydantic schemas.
- **AI integrations:** Groq, Gemini and OpenRouter text routes where configured; Groq Whisper for audio transcription; Gemini image understanding; local pypdf extraction for text PDFs.
- **Testing:** pytest and HTTPX-based backend tests.

### End-to-end workflow

1. User submits complaint text and/or attachment with location details.
2. Backend validates request fields and attachment type/size.
3. The relevant modality extractor processes the attachment.
4. The classification workflow generates structured complaint information.
5. Configured verification logic compares important fields where a second provider is available.
6. Deterministic rules validate authorization, specialization, assignment and status transitions.
7. Records and audit events are persisted.
8. The frontend displays the resulting complaint/workflow state.

## 6. Multimodal processing

### Text
Text input is passed to the classification workflow, which produces complaint fields such as category, priority and department subject to schema validation and configured provider availability.

### Vision
The repository includes a Gemini image-understanding adapter. Live image interpretation depends on a valid Gemini key, supported model, network trust and quota. This release has one configured vision adapter; cross-provider vision failover and vision multi-model comparison are not implemented.

### Audio
The repository includes Groq Whisper transcription. Transcribed text is passed into the complaint-processing workflow. Live transcription depends on a valid Groq key, supported model, network trust and quota. Cross-provider audio failover and audio multi-model comparison are not implemented.

### Documents
Text-based PDF extraction is performed locally using pypdf. Scanned PDFs that contain page images require OCR, which is not implemented in this release. Document extraction is not equivalent to a separately selectable document LLM.

## 7. AI model selection and governance

The backend exposes a model capability catalogue. Manual execution validates that the selected provider/model supports the requested modality. Automatic execution uses configured free-provider candidates for supported paths. Text comparison submits work to two configured text providers and compares structured fields.

Limitations to state during demonstration:
- Automatic text routing can try configured Groq, Gemini and OpenRouter text adapters in order.
- Vision currently uses the Gemini adapter.
- Audio currently uses the Groq Whisper adapter.
- PDF extraction is local pypdf extraction.
- Multi-model comparison is text-only.
- A configured API key does not guarantee a live request; quota, model availability, TLS certificates and network policy also matter.
- No paid fallback is intended.

## 8. Structured output, verification and business rules

Complaint classification uses a Pydantic model and controlled provider retry/fallback logic. Complaint and attachment content is treated as untrusted input. Important classification fields can be compared with a second configured text provider. Missing verifier availability or disagreement should lead to human review rather than unsupported certainty.

Backend rules cover role checks, worker specialization, assignment/status controls and duplicate checks. AI recommendations do not independently authorize assignment or mark maintenance as completed.

## 9. Security and reliability

The repository includes password hashing, signed-token authentication, role checks, upload type/size validation, trusted/untrusted prompt separation, controlled provider errors and TLS certificate verification support. Production deployment still requires a security review covering rate limits, upload malware scanning, secret management, database backups, retention policy and monitoring.

## 10. Testing and verification

The following backend checks were executed during final preparation:

```powershell
python -m compileall -q backend/app backend/tests
python -m pytest -q
```

**Observed result:** 31 backend tests passed.

This result is limited to the automated backend test suite. It does not prove frontend production build success, live provider API success, complete browser workflows or deployment success.

Not verified in this packaging environment:
- Frontend `npm ci` and production build.
- Live Groq, Gemini and OpenRouter requests.
- End-to-end browser workflows for all three roles.
- All ten formal CA4 evaluation demonstrations with screenshots/log/database evidence.
- ByteXL Nimbus deployment.

## 11. CA4 phase mapping

| Phase | Evidence-based status |
|---|---|
| 1 Project definition | Project definition documented; faculty approval evidence pending |
| 2 Full-stack foundation | Local implementation and backend tests present; frontend build/browser verification pending |
| 3 LLM gateway | Provider adapters present; live provider tests pending |
| 4 Model selection | Manual/automatic capability-aware paths and text comparison present; multimodal comparison absent |
| 5 Prompt engineering | Prompt safety and version identifier present; formal prompt registry/history incomplete |
| 6 Structured output | Text classification schema validation present; modality extraction outputs require human review |
| 7 Orchestration | Attachment extraction, classification and verification stages present; explicit stage tracing can be expanded |
| 8 Verification | Second text provider comparison present when configured; live evidence pending |
| 9 Business logic | Role, specialization, assignment and status rules present; full browser workflow verification pending |
| 10 Cost/context | Token estimates, truncation and budget gate present; accounting is approximate |
| 11 Security | Core controls present; production security review pending |
| 12 Audit/observability | Database records, audit events and AI usage/status endpoints present; production monitoring/retention work pending |
| 13 Evaluation | Automated suite present; formal ten-scenario evidence pack incomplete |
| 14 Nimbus | Not deployed; compulsory external phase |
| 15 Report/viva | This report is a draft; complete evidence and viva rehearsal pending |

## 12. Ten mandatory evaluation tasks

The project documentation includes an evidence template for: (1) incomplete input, (2) contradictory information, (3) hallucination prevention, (4) invalid structured output, (5) prompt injection, (6) multi-model disagreement, (7) provider failure/fallback, (8) long-context/token handling, (9) budget constraints and (10) deterministic business rules/transaction validation.

For each scenario, enter the exact test input, expected result, actual result, screenshot filename, API/backend evidence, database/audit evidence, timestamp and PASS/FAIL. Do not mark a scenario PASS until it has been run in the application.

## 13. Limitations

- OCR for scanned PDFs is not included.
- Vision and audio each use one configured provider in this release.
- Multi-model comparison is text-only.
- Frontend production build and browser workflows remain to be verified locally.
- Live provider calls depend on API credentials, provider availability, quota and network certificate configuration.
- Nimbus deployment is not included in this local release.
- Faculty approval is external.

## 14. Conclusion

CampusFix AI establishes a full-stack foundation for multimodal campus complaint handling with role-based workflows, backend AI integrations, model capability controls, structured classification, verification signals and deterministic assignment safeguards. The current repository is a tested development baseline, not yet a fully evidenced CA4 submission. Final readiness depends on local frontend and live-provider verification, completion of the ten evaluation evidence records, faculty approval, final report updates and ByteXL Nimbus deployment.

## 15. Submission details to complete

- Student name / ID: [Enter]
- Faculty guide: [Enter]
- Approved project title evidence: [Attach]
- Frontend build result: [Enter]
- Live provider test results: [Enter]
- Ten evaluation evidence folder: [Attach]
- Nimbus frontend URL: [Enter after deployment]
- Deployment screenshots: [Attach]
