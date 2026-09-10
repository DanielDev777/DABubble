import { Routes } from '@angular/router';

import { authGuard } from './core/auth/auth-guard';
import { guestGuard } from './core/auth/guest-guard';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () => import('./auth/intro/intro'),
  },
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () => import('./auth/login'),
  },
  {
    path: 'signup',
    canActivate: [guestGuard],
    loadComponent: () => import('./auth/signup/signup'),
  },
  {
    // Reached straight after signup, so the session already exists.
    path: 'avatar',
    canActivate: [authGuard],
    loadComponent: () => import('./auth/avatar-picker/avatar-picker'),
  },
  {
    path: 'passwort-vergessen',
    canActivate: [guestGuard],
    loadComponent: () => import('./auth/forgot-password/forgot-password'),
  },
  {
    // Baked into the emailed link by backend/accounts/tokens.py::make_reset_link.
    // Renaming this path without changing that function breaks every reset mail.
    path: 'reset-password',
    canActivate: [guestGuard],
    loadComponent: () => import('./auth/reset-password/reset-password'),
  },
  {
    path: 'impressum',
    loadComponent: () => import('./legal/impressum/impressum'),
  },
  {
    path: 'datenschutz',
    loadComponent: () => import('./legal/datenschutz/datenschutz'),
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
  { path: '**', loadComponent: () => import('./shared/not-found') },
];
