import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthStore } from './auth-store';

/**
 * Gate for routes that need a session.
 *
 * Reads the auth signal synchronously, which is safe because the app
 * initializer has already awaited AuthStore.restore() before the first route
 * activates. Without that ordering, a hard reload would always bounce to login.
 */
export const authGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthStore);
  const router = inject(Router);

  return (
    auth.isAuthenticated() ||
    router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } })
  );
};
