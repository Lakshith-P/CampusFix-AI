# CampusFix AI v2.9.0 — Analytics and multimodal comparison update

## Included in this update
- Administrator overview now includes a Power BI-inspired analytics board with KPI cards, 7-day report trend, status doughnut, category bars and priority chart. Charts use role-scoped complaint data returned by the API; no invented trend values are added.
- AI Studio compare mode is enabled for vision, audio and documents. It runs a modality-aware extraction stage, then an independently selected text model reviews the extracted evidence. The response explicitly states that the second model receives extracted text, not the original media. This is a staged comparison, not two independent vision/audio models.
- Gemini audio transcription and Gemini PDF visual reading are added as alternative modality adapters. Groq Whisper remains available for audio. OpenRouter vision is exposed only when `OPENROUTER_VISION_MODEL` is explicitly configured to a vision-capable free model.
- Scanned/image-only PDFs can be sent to Gemini as PDF evidence for visual text extraction when configured; ordinary text PDFs continue to use local pypdf extraction.
- Existing provider keys remain backend-only; no paid fallback is added.

## Verification
- Backend compileall passed.
- Backend pytest: 31 passed.
- Frontend production build attempted but could not complete because `npm ci` timed out and the local `node_modules` tree is incomplete (`vite/client` types unavailable). The frontend build is therefore **not verified**.

## Limitations
- Multimodal compare is staged extraction + independent text review. It is not a claim that every provider independently accepts every media type.
- OpenRouter image support requires configuring an actual image-capable free model identifier in `OPENROUTER_VISION_MODEL`; the generic `openrouter/free` route is not assumed to support images.
- PDF visual extraction requires a configured Gemini API key and a model/account that accepts PDF input.
- Student and worker submission forms do not yet expose the full provider/model picker inline; AI Studio remains the shared provider-selection workspace.
