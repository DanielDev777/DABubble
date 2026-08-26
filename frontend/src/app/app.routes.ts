import { Routes } from '@angular/router';

import { authGuard } from './core/auth/auth-guard';
import { guestGuard } from './core/auth/guest-guard';

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () => import('./auth/login-placeholder'),
  },
  {
    path: 'workspace',
    canActivate: [authGuard],
    loadComponent: () => import('./workspace/workspace-placeholder'),
  },
  {
    // Development-only: the design-token preview from step 4.
    path: 'tokens',
    loadComponent: () => import('./dev/token-preview'),
  },
  { path: '', pathMatch: 'full', redirectTo: 'workspace' },
  { path: '**', loadComponent: () => import('./shared/not-found') },
];
