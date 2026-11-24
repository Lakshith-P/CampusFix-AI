# Development backlog for the master CampusFix baseline

Work only from this ZIP's `campusfix-final` folder. Complete and verify one item before moving on.

## Priority 1 — make the current end-to-end flow reliable

- [ ] Install backend requirements on the user's Windows machine and run the full pytest suite.
- [ ] Install frontend dependencies and pass `npx.cmd tsc --noEmit` and `npm.cmd run build`.
- [ ] Verify all three seeded roles can log in, and verify the `admin@gmail.com` account.
- [ ] Verify the student can submit text, image, audio and PDF reports with a required block/building.
- [ ] Verify image/audio extraction errors are visible and do not create false AI-analysis claims.
- [ ] Verify worker assignment, specialization restrictions, status updates and resolution notes.
- [ ] Verify admin review, AI status, usage and audit views.

## Priority 2 — complete the CA4 ten evaluation tasks

- [ ] Incomplete input and clarification workflow.
- [ ] Contradictory information beyond simple block/room references (dates, details and locations).
- [ ] Hallucination prevention for unsupported campus facts.
- [ ] Invalid structured output and bounded retry evidence.
- [ ] Prompt-injection and document-injection tests.
- [ ] Two-provider agreement/disagreement using real provider responses.
- [ ] Provider timeout, rate-limit, invalid-key and outage tests.
- [ ] Long-context handling and trace evidence.
- [ ] Budget limit, usage tracking and cost-estimate validation.
- [ ] Authorization, invalid assignment, duplicate and transaction rejection tests.

## Priority 3 — advanced product features

- [ ] Complaint detail drawer with full timeline and attachments.
- [ ] Student notifications and feedback after resolution.
- [ ] Worker specialization stored as a dedicated database field, workload-aware routing and availability.
- [ ] Admin review queue for low-confidence and disagreement cases.
- [ ] SLA timers, overdue alerts, reopen/escalation policy and response-time analytics.
- [ ] Campus heatmap by block/floor, recurring-issue detection and maintenance forecasting.
- [ ] Image evidence before/after repair, with human confirmation.
- [ ] Admin user management and safe password reset flow.
- [ ] Exportable CSV/PDF reports and audit filters.
- [ ] Accessibility, responsive mobile layouts and automated frontend tests.

## Priority 4 — submission

- [ ] Obtain/attach title approval evidence.
- [ ] Prepare the final report and viva notes from measured implementation evidence.
- [ ] Deploy and verify on ByteXL Nimbus as required by the course brief.
- [ ] Record the final deployed frontend URL and screenshots.
