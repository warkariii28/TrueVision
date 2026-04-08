# TrueVision Backend

This is the Flask backend API for TrueVision.

It provides:

- authentication APIs
- image upload and deepfake prediction
- saved result history for logged-in users
- feedback APIs
- performance report APIs
- protected media delivery for saved and guest-preview results

## Tech Stack

- Flask
- Flask-Login
- Flask-SQLAlchemy
- Flask-Migrate
- PostgreSQL
- PyTorch
- Transformers
- OpenCV
- MediaPipe

## Environment Setup

Create this file:

- `.env`

Use:

```env
APP_ENV=development
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=false
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost/deepfake_detection
CORS_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=Lax
PRELOAD_MODEL=false
RATELIMIT_STORAGE_URI=memory://
LOGIN_RATE_LIMIT_COUNT=10
LOGIN_RATE_LIMIT_WINDOW=300
REGISTER_RATE_LIMIT_COUNT=5
REGISTER_RATE_LIMIT_WINDOW=600
UPLOAD_RATE_LIMIT_COUNT=8
UPLOAD_RATE_LIMIT_WINDOW=600
```

You can copy the structure from:

- `.env.example`

## Install

From the `backend` folder:

```powershell
py -3.10 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

Use the virtual environment Python directly:

```powershell
.\venv\Scripts\python.exe -m flask --app routes.py run
```

Backend runs at:

`http://localhost:5000`

## API Overview

### Auth

- `GET /api/auth/me`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`

### Upload and results

- `POST /api/upload`
- `GET /api/results`
- `GET /api/results/<id>`
- `POST /api/results/<id>/feedback`
- `GET /api/media/result/<id>/image`
- `GET /api/media/result/<id>/gradcam`
- `GET /api/media/guest/image`
- `GET /api/media/guest/gradcam`

### Performance

- `GET /api/performance`

## Guest vs Logged-in Behavior

### Guest upload

- upload is allowed
- result is returned immediately
- media stays available only through the current browser session
- result is not saved to the database

### Logged-in upload

- upload is allowed
- result is saved in the `result` table
- result becomes visible in history

## Main Files

- `app.py`:
  app setup, env loading, DB/auth/cors config
- `routes.py`:
  API routes
- `models.py`:
  database models
- `inference.py`:
  model loading, prediction, and Grad-CAM generation
- `filter_utils.py`:
  image quality checks before prediction

## Media Storage

These folders are still needed:

- `static/uploads`
- `static/gradcam`

They are used to store:

- uploaded source images
- generated Grad-CAM images

Saved-result media is no longer linked directly from `/static/...` in the frontend.
Protected API endpoints now serve saved-result media only to the owning authenticated user.
Guest-preview media is served through session-scoped guest media endpoints.

## Important Notes

- The backend is now API-first; old Flask HTML page routes/templates are no longer part of the main app flow
- Unauthorized access returns JSON `401` responses
- `SECRET_KEY` is required in all environments
- If `DATABASE_URL` is missing, the backend falls back to SQLite for local safety, but PostgreSQL is recommended for real saved-history use
- Cookie-authenticated write routes use CSRF protection via `X-CSRF-Token`
- Auth and upload endpoints use Flask-Limiter
- In production, use HTTPS with `SESSION_COOKIE_SECURE=true`

## Production Notes

Recommended production values:

```env
APP_ENV=production
SECRET_KEY=<long-random-secret>
FLASK_DEBUG=false
DATABASE_URL=<production-database-url>
CORS_ORIGINS=https://your-frontend-domain.com
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=Lax
PRELOAD_MODEL=true
RATELIMIT_STORAGE_URI=redis://localhost:6379/0
LOGIN_RATE_LIMIT_COUNT=10
LOGIN_RATE_LIMIT_WINDOW=300
REGISTER_RATE_LIMIT_COUNT=5
REGISTER_RATE_LIMIT_WINDOW=600
UPLOAD_RATE_LIMIT_COUNT=8
UPLOAD_RATE_LIMIT_WINDOW=600
```

The inference stack is now lazy-loaded during upload processing, which avoids loading the model for auth/results/performance-only requests.
If you set `PRELOAD_MODEL=true`, the backend will warm the model during startup so the first upload request is faster.
Set `RATELIMIT_STORAGE_URI` to a Redis URI in production so all app instances share the same counters.

## Common Checks

### Confirm DB URL being used

```powershell
.\venv\Scripts\python.exe -c "from app import create_app; app=create_app(); print(app.config['SQLALCHEMY_DATABASE_URI'])"
```

### Run migrations if needed

Use your existing migration flow/tools in this project before running against a fresh database.

### Security verification

```powershell
.\venv\Scripts\python.exe -m pytest test_app_config.py test_auth_api.py test_upload_api.py test_results_api.py
```
