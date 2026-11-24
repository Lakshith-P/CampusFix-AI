# One-hour submission checklist

## 0–10 minutes: prove the local build
- [ ] Start backend and frontend from this exact source folder.
- [ ] Open `/health` and `/docs`.
- [ ] Run backend tests: `python -m pytest -q` (32 passed in packaging session).
- [ ] Run frontend `npm ci` then `npm run build` on the submission machine. This build has not been verified in this packaging session.

## 10–30 minutes: capture live demo evidence
- [ ] Student login and complaint submission.
- [ ] Vision upload and prediction.
- [ ] Audio upload, transcription and review.
- [ ] PDF upload, extracted text and classification.
- [ ] Student edit/approval.
- [ ] Admin assignment.
- [ ] Worker acceptance, status update and completion evidence.
- [ ] Admin resolution verification; student notification; audit history.

## 30–45 minutes: CA4 evidence
- [ ] Demonstrate incomplete input and location conflict.
- [ ] Demonstrate prompt injection is treated as untrusted complaint text.
- [ ] Demonstrate invalid structured output/retry or safe failure.
- [ ] Demonstrate provider outage and confirm no paid fallback.
- [ ] Demonstrate model disagreement / human review.
- [ ] Demonstrate long input truncation and budget gate.
- [ ] Demonstrate duplicate/unauthorized action rejection.
- [ ] Save exact input, expected result, actual result, screenshot/log and PASS/FAIL for each of the ten scenarios.

## 45–60 minutes: submission integrity
- [ ] If required, deploy to ByteXL Nimbus and verify public health/auth.
- [ ] Add deployment URL and screenshots to report.
- [ ] Remove `.env`, API keys, local database, uploads and personal data from submission ZIP.
- [ ] Confirm project title, team/member details and faculty approval page.
- [ ] Submit only claims supported by the attached evidence.

## Known limitations to disclose if still unresolved
- Current multimodal comparison is modality-specific extraction followed by independent text review, not two independent vision/audio models.
- Scanned-PDF OCR is not implemented.
- Frontend production build and Nimbus deployment require verification.
