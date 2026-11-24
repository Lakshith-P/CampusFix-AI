# ByteXL Nimbus deployment — required CA4 phase 14

The course brief explicitly requires deployment on ByteXL Nimbus. The repository is developed locally in VS Code, then imported/pushed to the Nimbus project workspace. This guide is an operational checklist; it is **not proof of deployment**.

## Local build before Nimbus
1. Ensure backend `requirements.txt` installs successfully in the Nimbus Python environment.
2. Set `DATABASE_URL` to a persistent database supported by the Nimbus workspace. Do not use an ephemeral filesystem for the final database.
3. Set a strong `SECRET_KEY`, `CORS_ORIGINS` to the exact frontend origin, and provider keys as backend secrets.
4. Set `UPLOAD_DIR` to persistent storage or configure object storage; local container files may be ephemeral.
5. Build frontend with `npm ci` (or `npm install` if no lockfile is available) and `npm run build`.

## Nimbus deployment sequence
1. Create/import the project in ByteXL Nimbus using the course workspace instructions.
2. Configure backend service from `backend/` with start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Configure frontend build from `frontend/` with build command `npm install && npm run build`; serve `dist/` using the Nimbus-supported static hosting mechanism.
4. Set `VITE_API_URL` to the public backend URL at frontend build time.
5. Set backend `CORS_ORIGINS` to the public frontend URL.
6. Configure secrets only in Nimbus backend environment settings. Never commit `.env`.
7. Seed only demonstration accounts/data in a demo environment. Do not seed demo passwords into a production campus instance.
8. Verify `/health`, login for each role, complaint create/update, file upload, AI calls, database persistence, and audit records against the deployed URLs.
9. Save screenshots, logs, public frontend URL and deployment timestamp under `evidence/`.

## Required evidence to close Phase 14
- Public Nimbus frontend URL.
- Backend `/health` response.
- Browser screenshot of deployed student/admin portals.
- Successful deployed frontend → API → database request.
- At least one live provider response and one controlled provider-failure result.
- Confirmation that uploaded files and database records persist after service restart.

Do not claim Phase 14 passed until these checks are performed in Nimbus. Render/Vercel are alternative hosting providers and do not satisfy the explicit Nimbus requirement unless the instructor grants written approval.
