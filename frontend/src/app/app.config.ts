import {
  provideHttpClient,
  withFetch,
  withInterceptors,
  withXsrfConfiguration,
} from '@angular/common/http';
import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideRouter } from '@angular/router';

import { AuthStore } from './core/auth/auth-store';
import { authRefreshInterceptor } from './core/http/auth-refresh-interceptor';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(
      withFetch(),
      // Django's names, not Angular's defaults (XSRF-TOKEN / X-XSRF-TOKEN).
      // Get these wrong and reads work while every write returns 403.
      withXsrfConfiguration({
        cookieName: 'csrftoken',
        headerName: 'X-CSRFToken',
      }),
      withInterceptors([authRefreshInterceptor]),
    ),
    // Guards read the auth signal synchronously, so the session has to be
    // resolved before the first route activates.
    provideAppInitializer(() => inject(AuthStore).restore()),
  ],
};
