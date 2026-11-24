# CampusFix AI — CA4 working release v2.6.0

Multimodal campus maintenance reporting and resolution system with Student, Maintenance Worker and Admin roles. The release contains a React/Vite frontend, FastAPI backend, SQLAlchemy persistence, backend-controlled AI adapters, schema validation, independent verification, deterministic assignment/status rules, cost controls and audit endpoints.

## Included AI capabilities

| Modality | Provider / adapter | Behaviour |
|---|---|---|
| Text | Groq, Gemini, OpenRouter | Structured complaint classification; manual selection or automatic free-provider routing with ordered text failover |
| Vision | Gemini | Image evidence description; content remains untrusted and requires human review |
| Audio | Groq Whisper | Audio transcription; content remains untrusted and requires human review |
| Documents | Local pypdf | Extracts embedded PDF text; scanned PDFs require OCR and are not supported by this adapter |

No paid fallback is enabled. Provider model IDs, free quotas and account access may change. Keys are backend-only. Do not add keys to frontend `.env`, source control, screenshots or reports.

## 1. Backend setup — PowerShell terminal 1

Open the extracted `campusfix-final` folder in VS Code. Then run each command from the backend directory:

```powershell
cd backend
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Paste your own provider keys into `backend/.env` using the exact variable names already shown there. Save the file. Do not paste keys into this chat. If `.env` already exists, do not overwrite it with `Copy-Item`; open it with `notepad .env` instead. The settings loader reads `.env` relative to the backend working directory, so start the API from `backend/`.

Seed fictional demo users and complaints:

```powershell
python seed_synthetic_data.py
```

Run the API:

```powershell
python -m uvicorn app.main:app --reload
```

Backend health: http://127.0.0.1:8000/health  
API docs: http://127.0.0.1:8000/docs

## 2. Frontend setup — PowerShell terminal 2

Open a second terminal at the extracted project root:

```powershell
cd frontend
Copy-Item .env.example .env
npm.cmd ci
npm.cmd run dev
```

If `frontend/.env` already exists, do not overwrite it; confirm it contains `VITE_API_URL=http://127.0.0.1:8000`. Open http://localhost:5173.

If Rollup's native module is blocked by Windows Application Control, retain the WASM Rollup override in `package.json` and run `npm.cmd install` rather than trying to bypass the device security policy.

## 3. Admin AI Studio

Sign in with an Admin account and open **AI Studio**. Select Text, Vision, Audio or Documents. Manual mode uses the selected compatible provider/model. Automatic text mode tries configured free providers in order and logs failed attempts; vision and audio have one configured provider adapter each. Text model comparison is available when two text providers are configured. PDF processing uses local pypdf, not a cloud model. Upload the correct file type for the selected modality.

The provider readiness panel shows whether backend environment variables were detected; it does not prove that a key is valid, that a model is available, or that free quota remains. A live request is required to verify those things.

## 4. Tests and build verification

From `backend/`:

```powershell
python -m compileall -q app tests
python -m pytest -q
```

Expected for this source release: **28 backend tests pass**. Record the actual result when you run it.

From `frontend/`:

```powershell
npm.cmd run build
```

The frontend production build was not verified in the packaging environment; run it locally and save the terminal output. Live provider calls also require your configured keys and have not been verified by this package build.

## 5. Demo accounts

Run `python seed_synthetic_data.py` first. The seed script creates fictional demo users. Check `backend/seed_synthetic_data.py` for the current credentials; change demo passwords before any public deployment.

## 6. CA4 phase and evaluation status

Read:
- `docs/CA4_PHASE_MAPPING.md` — honest phase-by-phase implementation and remaining evidence.
- `docs/EVALUATION_EVIDENCE_PACK.md` — all ten required evaluation scenarios and evidence fields.
- `docs/REPORT_OUTLINE.md` — report structure.
- `docs/PROMPT_CATALOGUE.md` — prompt strategy.
- `docs/DEPLOYMENT_NIMBUS.md` — Nimbus deployment steps.
- `docs/FINAL_HANDOFF_CHECKLIST.md` — submission checklist.

This release does **not** claim that all phases are complete. Faculty approval (Phase 1), live integration/evaluation evidence (especially Phase 13), and final measured report/viva evidence (Phase 15) still require your actions. **Phase 14 must be deployed and verified on ByteXL Nimbus** as required by the official brief; Vercel/Render alone is not a substitute unless faculty approves it in writing.

## 7. Security and packaging

The distributable ZIP intentionally excludes `.env`, databases, uploads, `.venv`, `node_modules`, `.git` and caches. Create your local `.env` from `.env.example`. Rotate any keys that were previously placed in an archive or committed to Git. The bundled campus dataset is synthetic and must be identified as synthetic in your report.


## v2.4.0 multimodal role and image-routing fixes

- Student complaint submission now exposes explicit text, photo, audio and PDF input choices, including browser voice recording. Text description can be combined with the selected attachment.
- Assigned maintenance workers can upload photo/audio/PDF evidence from their work-order row. The backend extracts evidence, stores the attachment and records an audit event; it does not automatically mark work complete.
- Image extraction now receives the student's optional context and asks the vision adapter to distinguish water dripping from an AC unit (HVAC) from a visible plumbing-pipe leak.
- AC-associated water leakage is protected by a deterministic HVAC routing rule and always remains flagged for human review.
- AI Studio repairs the provider/model selection race when the user switches modalities before the provider catalog has loaded.
- `audio/webm` is accepted by the student and worker evidence endpoints.

Provider-backed image/audio execution still requires valid provider keys in `backend/.env`, a model ID enabled for that account, and available provider quota. The automated tests do not replace a live Gemini/Groq request.

## v2.5.0 reliability fixes

- Outbound Groq/Gemini/OpenRouter HTTPX calls now use the operating-system certificate trust store through `truststore` where available. TLS verification stays enabled. For an approved campus proxy CA not present in the OS store, set `CAMPUSFIX_CA_BUNDLE` in `backend/.env` to the PEM certificate-chain path.
- Compare mode is now triggered by the execution-mode selector and reports per-provider success/failure so one failed model does not hide the other model's result.
- Admin worker choices are limited to active, available workers and filtered by complaint specialization in the UI; the backend remains authoritative and rejects incompatible assignments.
- PDF extraction now reports encrypted PDFs and scanned/image-only PDFs explicitly. Scanned PDFs require OCR and are not falsely reported as extracted.
- Provider/model selectors use a compatible fallback selection to avoid blank controlled dropdown values during modality changes/catalog loading.

Run `python -m pytest -q` from `backend`. Live provider calls, browser build, certificate trust in your Windows network, and Nimbus deployment must still be verified in the target environment.


## v2.6.0 role-workspace expansion

- Student reporting now exposes Text, Vision, Audio and Documents directly in the student portal. Text-only reports use the text classification endpoint; image/audio/PDF reports use the multimodal extraction workflow. Audio mode includes browser recording and uploads the resulting audio blob to the backend.
- Admin navigation now includes functional API-backed Accounts & Access, AI Monitoring, AI Usage & Budget, Worker Management and Audit Logs pages, plus a CA4 Evaluation Centre checklist. Role changes call the protected administrator endpoint.
- The optional custom CA bundle is read from backend `.env` settings as well as the process environment. TLS certificate verification remains enabled.
- Backend verification in the packaging environment: `python -m pytest -q` — 31 passed. The frontend production build could not be verified in this packaging environment because the dependency installation did not complete; run `npm.cmd ci` and `npm.cmd run build` on the Windows development machine.

## Important implementation boundaries

- Provider readiness only means a key is present. Live provider/model availability, quotas, organization TLS trust and actual image/audio interpretation must be tested using your own keys and network.
- PDF extraction supports text-based PDFs. Scanned/image-only PDFs are explicitly reported as requiring OCR; OCR is not claimed as implemented in this release.
- Text model comparison is supported. Vision and audio currently use their compatible single-provider adapters; they do not claim multi-model comparison.
- The Evaluation Centre lists all ten CA4 scenarios, while actual evidence must be generated by running each scenario and recording screenshots/logs.
- Phase 1 faculty approval, complete Phase 13 evidence, Phase 14 Nimbus deployment and Phase 15 final report/viva remain external or evidence-dependent.


## Final submission documents

- `docs/FINAL_PROJECT_REPORT.md` — evidence-based CA4 report draft.
- `docs/VIVA_PREPARATION.md` — viva questions and answers.
- `docs/FINAL_SUBMISSION_CHECKLIST.md` — remaining verification and submission checklist.

These documents distinguish implemented code from unverified live-provider, frontend-build, evaluation-evidence and Nimbus deployment work.

## v2.8.0 UI and role access update
See `docs/RELEASE_NOTES_v2.8.0.md` for included changes, verification, and remaining limitations. In particular, text comparison is currently supported, while vision/audio/document multi-provider comparison and per-submission provider controls remain unfinished.


## v2.9.0 update
See `docs/RELEASE_NOTES_v2.9.0.md` for the Power BI-inspired admin analytics board, multimodal staged comparison, Gemini audio/PDF extraction and explicit verification status.

## v2.10.0 inline AI selection update
Student complaint submission and worker evidence forms now expose Manual, Automatic and Compare AI controls. See `docs/RELEASE_NOTES_v2.10.0.md` for exact routing behavior, provider requirements and verification limits.
