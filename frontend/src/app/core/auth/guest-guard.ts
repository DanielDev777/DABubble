import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthStore } from './auth-store';

/** Keeps a signed-in user out of the login and signup screens. */
export const guestGuard: CanActivateFn = () => {
  const auth = inject(AuthStore);
  const router = inject(Router);

  return !auth.isAuthenticated() || router.createUrlTree(['/workspace']);
};
