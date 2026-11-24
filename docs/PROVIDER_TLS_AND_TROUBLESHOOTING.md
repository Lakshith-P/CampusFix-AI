# Provider TLS, comparison, assignment and PDF troubleshooting

## SSL CERTIFICATE_VERIFY_FAILED on Windows
CampusFix 2.5.0 uses Python's OS certificate trust store through `truststore` for outbound HTTPX calls. This supports approved organization proxy roots installed in Windows. TLS verification remains enabled.

If your organization uses TLS inspection and its root certificate is not in the Windows Trusted Root Certification Authorities store, obtain the approved PEM root/intermediate chain from campus IT. Set `CAMPUSFIX_CA_BUNDLE` in `backend/.env` to that PEM file path, then restart the API. Do not set `verify=False`, disable TLS verification, or download random certificates.

## Model comparison
Select Execution mode = Compare two text models, enter the complaint, then click Compare two models. The API reports each provider independently; a single provider failure no longer hides the successful model result. Both providers must have valid keys, supported model IDs, quota and network access.

## Assignment
The admin worker list now only returns active, available staff. The backend still checks category/specialization compatibility. If a worker is not shown, update their specialization/availability in the admin user records and refresh.

## PDF extraction
Text-based PDFs are extracted with pypdf. Scanned/image-only PDFs need OCR; this release reports that explicitly instead of pretending text was extracted. Password-protected PDFs require an unlocked copy.

## Verification boundaries
Local tests do not prove live Groq/Gemini credentials, network certificate trust, model quotas, browser interaction or Nimbus deployment. Test those in the target Windows environment.
