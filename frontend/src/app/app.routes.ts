import { Routes } from '@angular/router';
import { Home } from './features/home/home';
import { Login } from './features/auth/login/login';
import { Register } from './features/auth/register/register';
import { Upload } from './features/upload/upload';
import { ResultsList } from './features/results/results-list/results-list';
import { ResultDetail } from './features/results/result-detail/result-detail';
import { Performance } from './features/performance/performance';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', component: Home },
  { path: 'login', component: Login },
  { path: 'register', component: Register },
  { path: 'upload', component: Upload },
  { path: 'results', component: ResultsList, canActivate: [authGuard] },
  { path: 'results/:id', component: ResultDetail, canActivate: [authGuard] },
  { path: 'result-preview', component: ResultDetail },
  { path: 'performance', component: Performance }
];
