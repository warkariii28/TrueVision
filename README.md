# TrueVision

TrueVision is a deepfake image detection application with:

- an Angular frontend
- a Flask backend API
- PostgreSQL for persisted users, saved results, and model performance
- guest upload support with temporary preview results

## Features

- Upload a face image and run deepfake analysis
- View confidence score, explanation, recommendation, and Grad-CAM output
- Guest mode:
  guests can upload and view results without logging in
- Authenticated mode:
  logged-in users get saved history and feedback persistence
- Public model performance report

## Project Structure

```text
TrueVision - Angular/
├── backend/
│   ├── app.py
│   ├── routes.py
│   ├── models.py
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

## Backend Setup

### 1. Create and activate a virtual environment

From the `backend` folder:

```powershell
py -3.10 -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Create `.env`

Create this file:

`backend/.env`

Use:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost/deepfake_detection
```

You can copy from:

`backend/.env.example`

### 4. Run the backend

From `backend`:

```powershell
.\venv\Scripts\python.exe -m flask --app routes.py --debug run
```

Backend runs at:

`http://localhost:5000`

## Frontend Setup

From the `frontend` folder:

### 1. Install dependencies

```powershell
npm install
```

### 2. Run the Angular app

```powershell
npm start
```

Frontend runs at:

`http://localhost:4200`

## Session Persistence

Session persistence is already implemented.

### Backend

In `backend/app.py`:

- session lifetime is set to 7 days
- Flask session cookie is used for auth

In `backend/routes.py`:

- login sets `session.permanent = True`
- authenticated API calls use the same session cookie

### Frontend

In `frontend/src/app/app.ts`:

- the app calls `/api/auth/me` on startup
- this restores auth state after refresh if the session is still valid

In Angular services:

- API calls use `withCredentials: true`
- that ensures browser cookies are sent with requests

## Guest vs Logged-in Flow

### Guest users

- can open upload page
- can upload image
- can view result preview
- preview survives refresh using `sessionStorage`
- results are not saved to history

### Logged-in users

- can upload image
- result is saved in the database
- can view `/results`
- can revisit saved result pages
- can submit feedback

## Backend API Summary

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

### Performance

- `GET /api/performance`

## Git Upload Safety

Before pushing to GitHub:

- do not commit `backend/.env`
- do not commit virtual environments
- do not commit uploaded/generated images unless intentionally needed
- do not commit SQLite DB files, caches, or `__pycache__`

This repo now includes a root `.gitignore` to help with that.

## Suggested Git Commands

If this is a new repo:

```powershell
git init
git add .
git commit -m "Initial TrueVision Angular + Flask API migration"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

If Git warns that `.env` is already tracked, remove it from Git tracking first:

```powershell
git rm --cached backend/.env
git commit -m "Stop tracking backend env file"
```

## Legacy Flask Version


The older Flask-only version of the project is preserved in:

`legacy-flask-version/`

The root project is the current Angular frontend + Flask API version.

## Notes

- The backend serves generated result images from `backend/static/uploads` and `backend/static/gradcam`
- Angular uses its own favicon from `frontend/public/favicon.ico`
- PostgreSQL is recommended for full saved-history functionality
