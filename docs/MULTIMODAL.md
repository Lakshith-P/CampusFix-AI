# Multimodal processing and model controls

## Admin AI Studio

The Admin AI Studio has four capability-specific tabs: Text, Vision, Audio and Documents. The selected modality/provider/model is submitted to `POST /ai/execute` as multipart form data. The backend enforces a capability allow-list and never returns API credentials.

- Text: Groq, Gemini or OpenRouter structured complaint classification.
- Vision: Gemini image analysis for PNG, JPEG and WebP.
- Audio: Groq Whisper transcription for MPEG, WAV, MP4 or WebM. The browser can record a voice note using `MediaRecorder` where microphone access is available.
- Documents: local pypdf embedded-text extraction from PDF files; scanned/image-only PDFs require OCR, which is not implemented in this baseline.

Manual routing uses the selected compatible provider/model. Automatic routing selects the first configured compatible free provider (text: Groq, Gemini, OpenRouter; vision: Gemini; audio: Groq; document: local pypdf). No paid fallback is performed. Two-model comparison is currently implemented for text classification only.

Extracted text is untrusted evidence. The AI Studio displays extraction output and flags media output for human review; it does not mark a physical repair complete or execute maintenance actions.

## API contract

`GET /ai/catalog` returns configured status and model modality capabilities. `POST /ai/execute` requires an admin bearer token and accepts `modality`, `provider`, `model`, optional `prompt`, and an optional uploaded `file`. Unsupported provider/modality combinations, model IDs, MIME types, oversized uploads and missing provider keys are rejected by the backend.


## Role-based multimodal flows (v2.4.0)

**Student:** choose Photo/Image, Audio, or PDF in the complaint form; optional text context is combined with extracted attachment content before classification. Location remains required.

**Maintenance worker:** only assigned work orders expose the evidence upload control. The worker can attach image/audio/PDF evidence; the backend extracts it, stores the file and writes an audit event. Evidence analysis never changes a complaint to completed.

**Image routing:** the vision prompt explicitly distinguishes an AC appliance dripping water (HVAC) from a visible plumbing-pipe leak. The complaint workflow applies an additional deterministic AC-water-leak routing rule and flags the result for human review.

**Admin:** the AI Studio provider/model selector reconciles its selected provider with the selected modality after the capability catalog loads, avoiding a blank selector when a user switches to Vision before the catalog response arrives.
