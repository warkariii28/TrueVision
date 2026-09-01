# TrueVision

TrueVision is a full-stack facial deepfake image detection app. It uses an Angular frontend, a Flask API backend, PostgreSQL persistence, and a PyTorch/Transformers inference pipeline with Grad-CAM visual evidence.

## Features

- Upload a face image for deepfake detection
- Guest result preview without saving history
- Login/register flow with saved result history
- Prediction, confidence score, plain-language explanation, recommendation, and Grad-CAM heatmap
- Feedback on saved results
- Model performance report seeded from project metrics
- Responsive premium Angular UI with dark deepfake-analysis theme

## Tech Stack

### Frontend

- Angular 21
- TypeScript
- RxJS
- Angular Router
- Bootstrap Icons
- Custom CSS theme split into reusable token, component, page, and theme layers

### Backend

- Python 3.10
- Flask 2.0
- Flask-SQLAlchemy
- Flask-Migrate / Alembic
- Flask-Login
- Flask-Bcrypt
- Flask-CORS
- Flask-Limiter
- PostgreSQL 17 recommended for local development
- PyTorch
- Transformers
- OpenCV
- MediaPipe

## Project Structure

```text
.
|-- backend/
|   |-- app.py
|   |-- routes.py
|   |-- models.py
|   |-- inference.py
|   |-- filter_utils.py
|   |-- gradcam_explainer.py
|   |-- requirements.txt
|   |-- .env.example
|   |-- migrations/
|   |-- scripts/
|   |   `-- seed_performance_from_pdf.py
|   `-- static/
|       |-- uploads/
|       `-- gradcam/
|-- frontend/
|   |-- angular.json
|   |-- package.json
|   |-- src/
|   |   |-- app/
|   |   `-- styles/
|   `-- public/
|-- .gitignore
`-- README.md
```

## Prerequisites

Install these on a fresh Windows device:

```powershell
winget install --id Git.Git -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id Python.Python.3.10 -e
winget install --id PostgreSQL.PostgreSQL.17 -e
```

Optional but useful:

```powershell
winget install --id Microsoft.VisualStudioCode -e
```

PostgreSQL notes:

- PostgreSQL 17 works with this project.
- Add PostgreSQL bin to PATH if `psql` is not recognized:

```text
C:\Program Files\PostgreSQL\17\bin
```

- If the postgres password was not set or was forgotten, reset it from `psql` as a privileged local user:

```sql
ALTER USER postgres WITH PASSWORD 'your-password';
```

## Backend Setup

From the repository root:

```powershell
cd backend
py -3.10 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create `backend/.env` from `backend/.env.example`:

```env
APP_ENV=development
SECRET_KEY=replace-with-a-long-random-secret
FLASK_DEBUG=false
DATABASE_URL=postgresql://postgres:your-password@localhost/deepfake_detection
CORS_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=Lax
PRELOAD_MODEL=false
RATELIMIT_STORAGE_URI=memory://
HF_LOCAL_FILES_ONLY=false
```

`SECRET_KEY` is required. Do not commit `.env`.

## PostgreSQL Setup

Open `psql`:

```powershell
psql -U postgres
```

Create the database if it does not exist:

```sql
CREATE DATABASE deepfake_detection;
```

Connect to it in `psql`:

```sql
\c deepfake_detection
```

List tables:

```sql
\dt
```

In pgAdmin Query Tool, do not use `\c`. Instead, right-click the `deepfake_detection` database and open Query Tool from that database. Then use normal SQL:

```sql
SELECT COUNT(*) FROM performance;
SELECT * FROM performance ORDER BY accuracy DESC;
```

## Seed Performance Data

The Performance page reads from the `performance` table. Seed it from the backend folder:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python scripts\seed_performance_from_pdf.py
```

Expected result:

```text
Seeded 12 performance rows.
Best model: Stage-2 Swin (... accuracy)
```

Important metric note:

- Accuracy, precision, recall, F1, AUC-ROC, and PR-AUC are stored from the project metrics.
- TP/TN/FP/FN counts are derived approximations using the documented test size and class split.
- Do not treat the derived counts as the source of the stored PDF accuracy.

## Model Files

The trained local weight file is expected at:

```text
backend/best_Swin_stage2.pth
```

This file is intentionally ignored by Git because it is large. Place your original project weight file there before using upload inference.

The base Swin processor/model comes from Hugging Face:

```text
microsoft/swin-base-patch4-window7-224
```

By default, the backend can download/cache the Hugging Face files on first use:

```env
HF_LOCAL_FILES_ONLY=false
```

Use this only when the model files are already cached locally:

```env
HF_LOCAL_FILES_ONLY=true
```

To test model loading:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -c "from inference import preload_model; raise SystemExit(0 if preload_model() else 1)"
```

## Run Backend

This project uses Flask 2.0, so use `FLASK_APP` instead of `flask --app`:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
$env:FLASK_APP="routes.py"
python -m flask run
```

Backend URL:

```text
http://127.0.0.1:5000
```

## Frontend Setup

In a second terminal:

```powershell
cd frontend
npm install
npm start
```

Frontend URL:

```text
http://localhost:4200
```

## API Summary

### Auth

- `GET /api/auth/me`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`

### Upload and Results

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

## Main User Flows

### Guest

- Open upload page
- Upload an image
- View temporary result preview
- Result is not saved to history

### Logged-in User

- Register or log in
- Upload an image
- View saved result history
- Reopen result detail pages
- Submit feedback

## Verification

Frontend:

```powershell
cd frontend
npm run build
npm test -- --watch=false
npm audit
```

Backend:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m pytest
```

## Troubleshooting

### `psql` is not recognized

Add PostgreSQL to PATH:

```text
C:\Program Files\PostgreSQL\17\bin
```

Open a new terminal and retry:

```powershell
psql -U postgres
```

### pgAdmin does not accept `\c deepfake_detection`

`\c` is a `psql` terminal command, not SQL. In pgAdmin, select the database in the left sidebar and open Query Tool from that database.

### `/api/performance` says relation `performance` does not exist

Check that Flask is connected to the same database you inspected:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -c "from app import create_app; app=create_app(); print(app.config['SQLALCHEMY_DATABASE_URI'])"
```

Then seed the table:

```powershell
python scripts\seed_performance_from_pdf.py
```

### Upload fails with Hugging Face image processor error

Make sure internet is available for the first run, or pre-cache the base model. Keep this in `.env` for new devices:

```env
HF_LOCAL_FILES_ONLY=false
```

Then run:

```powershell
python -c "from inference import preload_model; raise SystemExit(0 if preload_model() else 1)"
```

### VS Code shows stale Angular errors

If `npm run build` passes but VS Code still shows template errors:

1. Run `TypeScript: Restart TS Server`
2. Run `Developer: Reload Window`
3. Restart `npm start`

## Git Notes

Ignored local/generated files include:

- `backend/.env`
- `backend/venv/`
- `frontend/node_modules/`
- `frontend/dist/`
- `backend/static/uploads/*`
- `backend/static/gradcam/*`
- `backend/best_Swin_stage2.pth`
- `TrueVision.pdf`

Generated upload images and local model weights should not be committed.

## Production Notes

Recommended production settings:

```env
APP_ENV=production
SECRET_KEY=<long-random-secret>
FLASK_DEBUG=false
DATABASE_URL=<production-postgresql-url>
CORS_ORIGINS=https://your-frontend-domain.com
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=Lax
PRELOAD_MODEL=true
RATELIMIT_STORAGE_URI=redis://localhost:6379/0
HF_LOCAL_FILES_ONLY=true
```

Use HTTPS in production. Use Redis-backed rate limiting when running more than one backend instance.

## License

Add a license file before public distribution if this repository is intended to be open source.
