# CA4 completion update — Prompt registry, multimodal comparison, scanned PDF OCR

## Prompt registry
- Registry: `backend/app/prompt_registry.py`
- Active prompts: `complaint_triage@1.1.0`, `vision_inspection@1.0.0`, `audio_transcription@1.0.0`, `document_extraction@1.1.0`.
- Authenticated endpoint: `GET /ai/prompts`; provider catalogue also returns active prompt manifest.
- Prompt versions are immutable identifiers in source control. To change prompt text, add a new version rather than silently rewriting a historical version.
- Untrusted user complaint/media/document content remains separate from trusted prompt instructions.

## Independent multimodal comparison
- `POST /ai/compare-multimodal` now runs both selected modality-capable adapters against the same original uploaded bytes.
- Vision: Gemini and OpenRouter vision (OpenRouter requires `OPENROUTER_VISION_MODEL` to be explicitly configured to a free, image-capable model).
- Audio: Groq Whisper and Gemini audio.
- Documents: Gemini PDF extraction/OCR and a separately configured Gemini document model. Configure `GEMINI_DOCUMENT_SECONDARY_MODEL` only with a distinct PDF-capable model ID available to your account. The app does not invent a model ID or silently use a paid model.
- Both raw outputs are retained separately. Partial failures and disagreements require human review. The comparison does not claim semantic agreement merely because outputs match exactly.

## Scanned PDF OCR
- Text PDFs: pypdf extraction, with PyMuPDF fallback for parser failures.
- Scanned/image-only PDFs: original PDF bytes are sent to Gemini's PDF-capable `generateContent` adapter for visual OCR when Gemini is configured. OCR preserves page/text uncertainty and treats document contents as untrusted evidence.
- If Gemini is not configured or its selected model does not support PDF input, scanned PDF OCR fails explicitly. There is no false claim of local OCR; no Tesseract dependency is bundled.

## Required `.env` configuration
```env
GEMINI_API_KEY=...
GEMINI_MODEL=<your configured Gemini model>
OPENROUTER_API_KEY=...
OPENROUTER_VISION_MODEL=<verified free image-capable OpenRouter model ID>
GROQ_API_KEY=...
GROQ_AUDIO_MODEL=whisper-large-v3-turbo
GEMINI_DOCUMENT_SECONDARY_MODEL=<optional distinct PDF-capable Gemini model ID>
```

## Verification boundaries
- Backend test suite: 32 tests passed after changes.
- Python compile check passed.
- Live API calls, account free-tier availability, browser UI wiring to the revised comparison endpoint, scanned PDF OCR against a real scanned PDF, and Nimbus deployment must be tested with the submitter's credentials/environment. These are not marked verified by source tests.
