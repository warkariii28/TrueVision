import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./features/home/home').then((m) => m.Home),
  },
  {
    path: 'login',
    loadComponent: () =>
      import('./features/auth/login/login').then((m) => m.Login),
  },
  {
    path: 'register',
    loadComponent: () =>
      import('./features/auth/register/register').then((m) => m.Register),
  },
  {
    path: 'upload',
    loadComponent: () =>
      import('./features/upload/upload').then((m) => m.Upload),
  },
  {
    path: 'results',
    loadComponent: () =>
      import('./features/results/results-list/results-list').then((m) => m.ResultsList),
    canActivate: [authGuard],
  },
  {
    path: 'results/:id',
    loadComponent: () =>
      import('./features/results/result-detail/result-detail').then((m) => m.ResultDetail),
    canActivate: [authGuard],
  },
  {
    path: 'result-preview',
    loadComponent: () =>
      import('./features/results/result-detail/result-detail').then((m) => m.ResultDetail),
  },
  {
    path: 'performance',
    loadComponent: () =>
      import('./features/performance/performance').then((m) => m.Performance),
  },
];
