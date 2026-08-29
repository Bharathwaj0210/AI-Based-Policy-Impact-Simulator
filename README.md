# AI POLICY (NEW)

An AI-powered policy advisory and impact simulator.

## Project Structure
- `backend/`: Django REST API
- `frontend/`: React Dashboard
- `streamlit/`: Interactive Demo Layer

## Getting Started
### Backend
1. `cd backend`
2. `pip install -r requirements.txt`
3. `python manage.py runserver`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm start`

## System requirements

- OS: Windows 10/11, macOS, or a recent Linux distribution
- Python: 3.10 - 3.12
- pip: latest
- Node.js: 16.x or newer (LTS recommended)
- npm or yarn: npm 8+ recommended
- Git: for cloning and version control
- Database: SQLite (default) or PostgreSQL (optional for production)

## Environment & API keys

This project loads environment variables from a `.env` file (see `backend/backend/settings.py`). At minimum you should set:

- `SECRET_KEY` — Django secret key
- `DEBUG` — `True` or `False`
- `ALLOWED_HOSTS` — comma-separated hosts for production
- `GOOGLE_API_KEY` — API key for any Google services used by the project

Example `.env` (place in `backend/`):

SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE

### How to get a Google API key

1. Open Google Cloud Console: https://console.cloud.google.com/
2. Create a new project (or select an existing one).
3. In the left menu go to `APIs & Services` → `Dashboard` and click `Enable APIs and Services`.
4. Search for and enable the specific API(s) you need (for example: Maps JavaScript API, Geocoding API, or other Google Cloud APIs).
5. Go to `APIs & Services` → `Credentials` and click `Create Credentials` → `API key`.
6. Copy the generated API key and **store it in your `backend/.env` file** as `GOOGLE_API_KEY`.
7. (Recommended) Under the created key's restrictions, set Application restrictions (HTTP referrers or IPs) and API restrictions to limit usage.

## Run the system (development)

Backend (Windows PowerShell example):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # optional
python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
npm start
```

Notes:
- If you use PostgreSQL in production, set `DATABASE_URL` in env and ensure `psycopg2` is installed.
- For production deployment use a WSGI server (Gunicorn/uvicorn) and set `DEBUG=False` and proper `ALLOWED_HOSTS`.

If you want, I can also add a sample `.env.example` file and a short script to start both backend and frontend concurrently.
