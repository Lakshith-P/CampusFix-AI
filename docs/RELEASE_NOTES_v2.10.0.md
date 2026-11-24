# CampusFix AI v2.10.0 — Inline AI controls for student and worker workflows

## Included
- Student complaint submission now includes Manual, Automatic and Compare execution modes.
- The student form loads the backend capability catalogue and offers provider/model choices compatible with the selected input type (text, image, audio or PDF). Unconfigured providers are shown as unavailable and cannot be selected.
- Manual multimodal submission sends the selected modality provider/model to the backend. Its text-triage stage uses the separately selected text provider/model.
- Automatic mode uses the backend's free-only compatible routing and local PDF text extraction with configured Gemini visual OCR fallback for scanned PDFs.
- Compare mode for multimodal submissions runs the modality extraction with the selected compatible extractor, then compares automatic text triage with an independently selected text model. Disagreement is flagged for human review. The second model is explicitly a text reviewer; it is not represented as having received the original image/audio/PDF.
- Text-only student submissions pass the selected provider/model to the backend; Compare executes two distinct selected text models.
- Worker evidence forms now expose evidence modality, Manual/Automatic/Compare mode, compatible provider/model selectors and a second text reviewer selector. The chosen configuration is sent with the evidence upload.
- Worker compare output displays the independent review result alongside extracted evidence.
- Backend validates selected provider/model pairs against its free-tier capability allow-list. API keys remain server-side. No paid fallback is introduced.

## Verification
- `python -m compileall -q backend/app` passed.
- `python -m pytest -q`: **31 passed**.
- Frontend production build remains **unverified**. `npm ci` timed out; an offline retry confirmed a required package was not cached. Do not interpret backend tests as frontend build or browser end-to-end verification.
- Live Groq/Gemini/OpenRouter calls were not run because provider credentials and live quotas are environment-specific.

## Operational notes
- Student and worker users need valid credentials and must be authenticated for `/ai/catalog` and protected workflows.
- Manual selections fail closed if a provider key is missing, the selected model is not allow-listed, or the provider does not support the selected modality.
- For compare mode, configure at least two usable text providers/models where the selected comparison requires them.
