# Repository Guidelines

## Project Structure & Module Organization
- `backend/` FastAPI app: `app/` (api, services, data_processing, schemas), `tests/` for pytest cases.
- `frontend/` Vite + React: `src/` (api/, types/, assets/, App.tsx), `public/` static assets.
- `models/` holds pretrained weights; `scripts/` has training/eval entrypoints; `data/` contains raw covers (`aiphoto/`) and labels (`annotations/`).
- `infra/` carries container configs; `docs/` stores design and implementation notes.
- `start_local.sh|.bat` boot backend + frontend with deps; `stop_local.*` stops them.

## Build, Test, and Development Commands
- Create venv then install: `python -m venv .venv` and activate, `pip install -r backend/requirements.txt`.
- Backend dev: `cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.
- Frontend dev: `cd frontend && npm install && npm run dev` (default API base `http://localhost:8000`).
- Backend tests: `pytest backend/tests`.
- Frontend checks: `cd frontend && npm run lint && npm run build`.
- One-click: `./start_local.sh` (mac/linux) or `./start_local.bat` (Windows) to install deps and start both services.

## Coding Style & Naming Conventions
- Python: 4-space indent, typing everywhere; snake_case for modules/functions/vars, PascalCase for Pydantic models. Keep config in `app/core`, API routes in `app/api/v1`, shared logic in `app/services`, request/response models in `app/schemas`. Prefer structured logging over prints.
- TypeScript/React: functional components with hooks, camelCase for props/state, PascalCase for components/files. ESLint config in `frontend/eslint.config.js`; follow existing two-space indent. Keep API helpers in `src/api` and shared contracts in `src/types`.

## Testing Guidelines
- pytest under `backend/tests` with `test_*.py`; use FastAPI `TestClient` and mocks for OCR-heavy paths. Add fixtures in `data/` when expanding pipeline behaviors.
- Frontend lacks unit tests; always run `npm run lint` and `npm run build` before pushing. Add lightweight UI tests when shipping new flows.

## Commit & Pull Request Guidelines
- Git history uses short, lower-case subjects (e.g., "bugfix"); prefer concise imperative lines like `fix upload mime validation`.
- Squash noisy WIP commits before review.
- PRs: include what changed, test commands executed, and screenshots/GIFs for UI changes. Link related issues/docs and call out model/data downloads or migrations.

## Security & Configuration Tips
- Backend settings use env vars with prefix `COVEROCR_` (see `app/core/config.py`). Do not commit secrets or `.env`; use `frontend/.env.example` as a template for local overrides.
- Models under `models/` are large; avoid committing new weights¡ªdocument download steps instead.
- Validate uploads (MIME/size) before pipeline use and avoid logging sensitive payloads.
