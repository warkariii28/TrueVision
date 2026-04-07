# TrueVision Backend

This is the Flask backend API for TrueVision.

It provides:

- authentication APIs
- image upload and deepfake prediction
- saved result history for logged-in users
- feedback APIs
- performance report APIs
- static serving for uploaded images and Grad-CAM outputs

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
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost/deepfake_detection
CORS_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=Lax
PRELOAD_MODEL=false
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
.\venv\Scripts\python.exe -m flask --app routes.py --debug run
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

### Performance

- `GET /api/performance`

## Guest vs Logged-in Behavior

### Guest upload

- upload is allowed
- result is returned immediately
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
  database models and prediction logic
- `filter_utils.py`:
  image quality checks before prediction

## Static Files Still Used

These folders are still needed:

- `static/uploads`
- `static/gradcam`

They are used to serve:

- uploaded source images
- generated Grad-CAM images

## Important Notes

- The backend is now API-first; old Flask HTML page routes/templates are no longer part of the main app flow
- Unauthorized access returns JSON `401` responses
- If `.env` is missing, the backend falls back to SQLite for local safety, but PostgreSQL is recommended for real saved-history use
- In production, `APP_ENV=production` requires `SECRET_KEY` to be set and should use HTTPS with `SESSION_COOKIE_SECURE=true`

## Production Notes

Recommended production values:

```env
APP_ENV=production
SECRET_KEY=<long-random-secret>
DATABASE_URL=<production-database-url>
CORS_ORIGINS=https://your-frontend-domain.com
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=Lax
PRELOAD_MODEL=true
```

The inference stack is now lazy-loaded during upload processing, which avoids loading the model for auth/results/performance-only requests.
If you set `PRELOAD_MODEL=true`, the backend will warm the model during startup so the first upload request is faster.

## Common Checks

### Confirm DB URL being used

```powershell
.\venv\Scripts\python.exe -c "from app import create_app; app=create_app(); print(app.config['SQLALCHEMY_DATABASE_URI'])"
```

### Run migrations if needed

Use your existing migration flow/tools in this project before running against a fresh database.
