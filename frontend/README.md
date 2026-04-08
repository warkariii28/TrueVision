# TrueVision Frontend

This is the Angular frontend for TrueVision.

## Tech Stack

- Angular 21
- TypeScript
- RxJS
- custom `bootstrap-lite.css` utility layer
- Bootstrap Icons

## What It Covers

- guest image upload
- logged-in upload with saved history
- temporary result preview and saved result detail views
- feedback submission for saved results
- public model performance page

## Backend Connectivity

Frontend API and static URLs are centralized in:

- `src/app/core/config/api.config.ts`

Behavior:

- local Angular development defaults to `http://localhost:5000`
- same-origin production deploys use the current origin automatically
- an alternate backend host can be injected through `window.__TRUEVISION_CONFIG__`

Example runtime override:

```html
<script>
  window.__TRUEVISION_CONFIG__ = {
    backendOrigin: 'https://api.example.com'
  };
</script>
```

## Install and Run

From the `frontend` folder:

```powershell
npm install
npm start
```

Then open `http://localhost:4200`.

## Route Summary

### Public routes

- `/`
- `/upload`
- `/result-preview`
- `/performance`
- `/login`
- `/register`

### Protected routes

- `/results`
- `/results/:id`

Protected routes use `src/app/core/guards/auth.guard.ts` and redirect guests to login with a `returnUrl`.

## Main Areas

### Core

- `src/app/app.ts`
- `src/app/app.routes.ts`
- `src/app/app.config.ts`

### Auth

- `src/app/core/services/auth.service.ts`
- `src/app/core/guards/auth.guard.ts`
- `src/app/features/auth/`

### Upload and results

- `src/app/core/services/results.service.ts`
- `src/app/features/upload/`
- `src/app/features/results/`

### Performance

- `src/app/features/performance/`

### Shared UI

- `src/app/shared/components/navbar/`
- `src/app/shared/components/footer/`

## Build and Test

```powershell
cmd /c npx ng test --watch=false
cmd /c npm run build
```

## Notes

- API calls use `withCredentials: true` so Flask session cookies are sent correctly
- auth state is restored on app startup through `/api/auth/me`
- the frontend is lazy-routed to keep the initial bundle smaller
