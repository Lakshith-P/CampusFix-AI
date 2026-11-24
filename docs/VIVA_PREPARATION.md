# CampusFix AI — Viva Preparation

## 1. What is CampusFix AI?
A multimodal campus maintenance complaint platform. Students submit text, images, audio or PDFs; AI helps extract and classify the issue; administrators review and assign it to suitable maintenance workers; workers update progress and submit evidence.

## 2. What problem does it solve?
Manual complaint triage is slow and students may not know technical categories. Multimodal intake allows users to show or describe the issue in the format they can provide.

## 3. Why multimodal?
Text alone may be insufficient. Images provide visible evidence, audio can capture spoken descriptions, and PDFs can contain supporting reports. Each modality requires a suitable preprocessing path.

## 4. Why three portals?
Students report and track issues, workers perform assigned tasks, and administrators manage complaints, users, AI configuration and oversight. Role-based access separates responsibilities.

## 5. What does the AI do?
It extracts evidence and recommends complaint category, priority, department and specialist. The backend validates output and business rules. AI does not authorize assignments or declare physical repairs complete.

## 6. Explain manual, automatic and comparison modes.
Manual executes the administrator-selected compatible model. Automatic chooses from configured compatible providers. Comparison runs two configured text providers and compares structured fields. In v2.6.0, comparison is text-only.

## 7. Which providers are integrated?
Groq, Gemini and OpenRouter text adapters are present where configured. Groq Whisper handles audio transcription, Gemini handles image understanding, and pypdf extracts text from text-based PDFs. Live calls depend on credentials, quota, model availability and network TLS configuration.

## 8. What is structured output?
The model response is constrained to a defined schema, represented using Pydantic. Required fields, types and allowed values are checked before downstream use.

## 9. Why use a second model?
An independent model can provide a second opinion. The application compares structured fields and can flag disagreement for human review. It is not a guarantee of truth.

## 10. What is prompt injection?
Untrusted complaint text or documents may contain instructions attempting to override system policy. The application treats this content as data and separates it from trusted instructions.

## 11. What are deterministic business rules?
Rules enforced by backend code rather than model suggestions: role permissions, worker specialization, availability, assignment duplication and valid status transitions.

## 12. How is cost controlled?
The project includes token estimation, truncation and a budget gate. Estimates are approximate and should not be described as exact billing measurements.

## 13. What happens if a provider fails?
The backend handles errors and can try configured free text providers in the automatic text path. If no configured provider succeeds, it returns a controlled failure. It does not use paid fallback.

## 14. What are the current limitations?
Scanned PDF OCR is not implemented; vision and audio each have one configured provider; multimodal comparison is not implemented; live provider/browser verification and Nimbus deployment remain pending.

## 15. What tests have been run?
The backend suite was run during packaging: 31 tests passed. This does not prove frontend build, live provider calls, all ten formal evidence demonstrations or deployment.

## 16. What is still required for CA4?
Faculty title approval, frontend and live provider verification, all ten evaluation evidence records, ByteXL Nimbus deployment, deployed end-to-end testing and final report evidence.

## 17. Why is Nimbus mandatory?
The assignment explicitly requires ByteXL Nimbus deployment and testing of frontend-to-backend-to-database-to-LLM connectivity. Local testing or deployment only to another platform does not satisfy that requirement.

## 18. What is your individual contribution?
Answer honestly with the modules you personally designed, coded, tested and debugged. Be ready to explain one API route, one database model, one provider adapter, one validation rule and one evaluation test from your own implementation.
