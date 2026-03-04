<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/dfa0bf13-d790-4576-9532-9be692b3b0e3

## Run Locally

**Prerequisites:**  Node.js and Python 3.13 (backend virtual environment)

1. Install frontend dependencies:
   ```bash
   npm install
   ```
2. Set required variables in `.env.local` / `.env` (Gemini, Supabase etc.).
3. Start the backend server (from repo root):
   ```bash
   cd backend
   .\venv\Scripts\activate        # Windows
   python -m uvicorn backend.main:app --reload --port 3000
   ```

4. Optionally seed sample jobs into the local SQLite database:
   ```bash
   python -m backend.scripts.seed_jobs
   ```
   The script inserts a handful of realistic postings; you can also POST to `/api/jobs`.

5. Run the frontend:
   ```bash
   cd ..
   npm run dev
   ```

### Backend features

* Resumes are parsed with expanded skill patterns, education/experience detection, and stored locally.
* The router returns matches from either Supabase or the embedded SQLite; the local store is always fast.
* A `/debug/supabase` endpoint reports remote connectivity status.
* Local jobs are served instantaneously; remote sync happens in the background.

`README` updated to document these new capabilities.
