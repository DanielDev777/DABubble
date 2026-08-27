import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';

import { AuthStore } from '../auth/auth-store';
import { SessionService } from '../auth/session';

/**
 * Endpoints that establish or end a session. A 401 from any of them is a real
 * answer, not an expired access token — retrying would loop forever.
 */
const PUBLIC_ENDPOINTS = [
  '/api/auth/login/',
  '/api/auth/signup/',
  '/api/auth/guest/',
  '/api/auth/google/',
  '/api/auth/refresh/',
  '/api/auth/logout/',
  '/api/auth/password-reset/',
];

export const authRefreshInterceptor: HttpInterceptorFn = (req, next) => {
  const session = inject(SessionService);
  const auth = inject(AuthStore);

  return next(req).pipe(
    catchError((error: unknown) => {
      const expired =
        error instanceof HttpErrorResponse &&
        error.status === 401 &&
        !PUBLIC_ENDPOINTS.some((endpoint) => req.url.startsWith(endpoint));

      if (!expired) {
        return throwError(() => error);
      }

      return session.refresh().pipe(
        switchMap(() => next(req)),
        catchError((refreshError: unknown) => {
          auth.clear();
          return throwError(() => refreshError);
        }),
      );
    }),
  );
};
