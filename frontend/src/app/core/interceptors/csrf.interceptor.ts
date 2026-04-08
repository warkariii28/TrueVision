import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';

import { AuthService } from '../services/auth.service';

const MUTATING_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

export const csrfInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const csrfToken = authService.csrfToken();

  if (!MUTATING_METHODS.has(req.method) || !csrfToken) {
    return next(req);
  }

  return next(
    req.clone({
      setHeaders: {
        'X-CSRF-Token': csrfToken,
      },
    })
  );
};
