# TrueVision Frontend

This is the Angular frontend for TrueVision.

It provides:

- guest image upload
- logged-in upload with saved history
- result preview and result detail pages
- feedback submission for saved results
- public model performance page

## Tech Stack

- Angular 21
- Bootstrap 5
- Bootstrap Icons
- RxJS

## Runs Against

The frontend expects the Flask backend API to be running at:

- API base: `http://localhost:5000/api`
- static assets: `http://localhost:5000/static`

These values are centralized in:

- `src/app/core/config/api.config.ts`

## Install

From the `frontend` folder:

```powershell
npm install
```

## Run

```powershell
npm start
```

Then open:

`http://localhost:4200`

## Main User Flows

### Guest users

- can open the upload page
- can upload an image
- can view a temporary result preview
- preview survives refresh using `sessionStorage`
- results are not saved to history

### Logged-in users

- can log in and register through the Angular UI
- uploads are saved to backend history
- can view `My Results`
- can open saved result details
- can submit feedback

## Important App Areas

### Core config

- `src/app/core/config/api.config.ts`

### Auth

- `src/app/core/services/auth.service.ts`
- `src/app/core/guards/auth.guard.ts`

### Results and upload

- `src/app/core/services/results.service.ts`
- `src/app/features/upload/`
- `src/app/features/results/`

### Performance

- `src/app/features/performance/`

## Protected Routes

These routes require login:

- `/results`
- `/results/:id`

These routes are public:

- `/`
- `/upload`
- `/result-preview`
- `/performance`
- `/login`
- `/register`

## Build

```powershell
npm run build
```

## Test

```powershell
npm test
```

## Notes

- The favicon is served by Angular from `public/favicon.ico`
- API calls use `withCredentials: true` so Flask session cookies are sent correctly
- Auth state is restored on app startup via `/api/auth/me`
