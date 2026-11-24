# CampusFix AI v2.5.0 — Reliability and workflow fixes

## Fixed
1. TLS certificate trust for all outbound model requests. Uses Windows/system trust via `truststore`, with optional PEM CA bundle. Certificate verification remains mandatory; no insecure `verify=False` workaround.
2. Compare execution mode now invokes the comparison workflow. Backend records each provider outcome and returns partial successes when only one model fails.
3. Admin assignment choices are limited to active/available staff and filtered by category specialization. Backend assignment validation remains authoritative and gives actionable errors.
4. PDF extraction distinguishes readable text PDFs, encrypted PDFs, and scanned/image-only PDFs requiring OCR.
5. Modality selector values resolve to a compatible provider/model while catalog data loads or tabs change.

## Run verification
```powershell
cd backend
python -m pip install -r requirements.txt
python -m pytest -q
```

## Windows TLS configuration
Normally the new `truststore` dependency uses Windows trusted roots. If a campus proxy intercepts TLS and its root is not trusted by Windows, ask campus IT for the approved PEM CA chain and set this in `backend/.env`:

```env
CAMPUSFIX_CA_BUNDLE=C:/certs/campus-approved-root-chain.pem
```

Restart Uvicorn after changing `.env`. Never disable TLS verification or paste private keys/certificates into source code.

## Known limits / verification not claimed
- Text PDF extraction only; scanned PDFs need OCR, and password-protected PDFs need an unlocked copy.
- Compare is currently for text models. Vision uses Gemini, audio uses Groq Whisper, and documents use local pypdf extraction.
- Frontend production build was not verified in the packaging environment because `npm ci` timed out.
- No live provider API test was possible here. API keys, quotas, selected model availability, and Windows certificate trust must be tested on the user's machine.
- ByteXL Nimbus deployment has not been performed.
