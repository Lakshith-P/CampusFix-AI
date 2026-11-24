# Final CA4 Submission Checklist

## Before submission
- [ ] Faculty approval for project title attached.
- [ ] Run backend tests and save terminal output.
- [ ] Run frontend `npm ci` and `npm run build`; save actual output.
- [ ] Test Student text complaint.
- [ ] Test Student image complaint with live Gemini credentials.
- [ ] Test Student audio recording/upload with live Groq Whisper.
- [ ] Test text-based PDF extraction.
- [ ] Test admin manual model execution.
- [ ] Test admin automatic text routing.
- [ ] Test text comparison with two configured providers.
- [ ] Test worker assignment with correct specialization and availability.
- [ ] Test worker accept/reject, progress and evidence upload.
- [ ] Execute all ten evaluation scenarios.
- [ ] Save exact input, expected/actual result, screenshot, API/log and database evidence for each scenario.
- [ ] Update `CA4_PHASE_TRACKER.md` using evidence only.
- [ ] Complete report student/faculty details and limitations.
- [ ] Rehearse viva questions.
- [ ] Deploy on ByteXL Nimbus.
- [ ] Verify deployed frontend-to-backend-to-database-to-LLM connectivity.
- [ ] Add deployed frontend URL and deployment screenshots.

## Do not claim complete until
- [ ] Frontend production build passes.
- [ ] Live model calls work with the configured keys.
- [ ] All role workflows are browser-tested.
- [ ] All ten evaluation tasks have recorded evidence.
- [ ] Nimbus deployment is live and tested.
