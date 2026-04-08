# TrueVision

TrueVision is a deepfake image detection application built with an Angular frontend, a Flask backend API, PostgreSQL-backed persistence, and a PyTorch/Transformers inference pipeline.

## What It Does

- Upload a face image and run deepfake analysis
- Show prediction confidence, explanation, recommendation, and Grad-CAM output
- Support guest uploads with temporary preview results
- Support logged-in users with saved result history and feedback
- Expose a public model performance report

## Project Structure

```text
TrueVision - Angular/
├── backend/
│   ├── app.py
│   ├── routes.py
│   ├── models.py
│   ├── inference.py
│   ├── requirements.txt
│   ├── .env.example
│   └── static/
│       ├── uploads/
│       └── gradcam/
├── frontend/
│   ├── package.json
│   ├── angular.json
│   ├── public/
│   └── src/
└── README.md
```

## Local Setup

### Backend

From `backend`:

```powershell
py -3.10 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `backend/.env` using `backend/.env.example`.

Example local values:

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

Run the backend:

```powershell
.\venv\Scripts\python.exe -m flask --app routes.py run
```

Backend runs at `http://localhost:5000`.

### Frontend

From `frontend`:

```powershell
npm install
npm start
```

Frontend runs at `http://localhost:4200`.

## Production Notes

Recommended backend values:

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

- `SECRET_KEY` is required in all environments
- `SESSION_COOKIE_SECURE=true` should be used behind HTTPS
- `PRELOAD_MODEL=true` warms the AI model during startup so the first upload is faster
- write routes use CSRF protection through the `X-CSRF-Token` header
- auth and upload endpoints are rate-limited through Flask-Limiter
- use Redis for `RATELIMIT_STORAGE_URI` in multi-instance production so rate limits stay shared

The frontend now derives backend URLs from the browser origin by default.

- Angular dev server defaults to `http://localhost:5000`
- same-origin production deploys use the current site origin automatically

If you need a separate API host, inject runtime config before the Angular bundle loads:

```html
<script>
  window.__TRUEVISION_CONFIG__ = {
    backendOrigin: 'https://api.example.com'
  };
</script>
```

## Main Flows

### Guest users

- can open the upload page
- can upload an image
- can view a temporary result preview
- preview survives refresh using `sessionStorage`
- results are not saved to history

### Logged-in users

- can log in or register
- can upload an image and save the result
- can view `/results`
- can revisit saved result pages
- can submit feedback

## API Summary

### Auth

- `GET /api/auth/me`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`

### Results

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

## Testing

### Frontend

From `frontend`:

```powershell
cmd /c npx ng test --watch=false
cmd /c npm run build
```

### Backend

From `backend`:

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

## Notes

- The backend stores generated files in `backend/static/uploads` and `backend/static/gradcam`
- Saved-result media is delivered through protected API endpoints instead of direct static URLs
- The inference model is lazy-loaded, so non-upload routes do not boot the full ML stack
- PostgreSQL is the recommended database for real saved-history usage
- Do not commit `backend/.env`

## Legacy Version

The older Flask-only version is preserved in `legacy-flask-version/`.
