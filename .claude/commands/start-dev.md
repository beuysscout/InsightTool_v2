Start the InsightTool_v2 development servers (backend and frontend).

## Backend
1. `cd backend` and ensure dependencies are installed: `pip install -e ".[dev]" --ignore-installed cryptography 2>/dev/null || true`
2. Ensure `STORE_BACKEND=memory` is set in `backend/.env` (fallback for environments where Supabase is unreachable).
3. Start the FastAPI backend: `cd /home/user/InsightTool_v2/backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
4. Run in the background so we can proceed to the frontend.

## Frontend
1. `cd frontend` and ensure dependencies are installed: `npm install`
2. Start the Vite dev server: `cd /home/user/InsightTool_v2/frontend && npx vite --host 0.0.0.0 --port 5173`
3. Run in the background.

After both are running, confirm the status of each server and report the URLs:
- Backend API: http://localhost:8000
- Frontend UI: http://localhost:5173

$ARGUMENTS
