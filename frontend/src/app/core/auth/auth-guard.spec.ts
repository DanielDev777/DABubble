import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  provideRouter,
  Router,
  RouterStateSnapshot,
  UrlTree,
} from '@angular/router';

import { authGuard } from './auth-guard';
import { AuthStore } from './auth-store';
import { guestGuard } from './guest-guard';

function configure(authenticated: boolean) {
  TestBed.configureTestingModule({
    providers: [
      provideRouter([]),
      { provide: AuthStore, useValue: { isAuthenticated: signal(authenticated) } },
    ],
  });
}

const route = {} as ActivatedRouteSnapshot;
const stateFor = (url: string) => ({ url }) as RouterStateSnapshot;

describe('authGuard', () => {
  it('lets a signed-in user through', () => {
    configure(true);
    const result = TestBed.runInInjectionContext(() =>
      authGuard(route, stateFor('/workspace')),
    );
    expect(result).toBe(true);
  });

  it('redirects a signed-out user to login', () => {
    configure(false);
    const result = TestBed.runInInjectionContext(() =>
      authGuard(route, stateFor('/workspace')),
    );
    expect(result).toBeInstanceOf(UrlTree);
    expect(TestBed.inject(Router).serializeUrl(result as UrlTree)).toBe(
      '/login?returnUrl=%2Fworkspace',
    );
  });

  it('remembers where the user was heading', () => {
    configure(false);
    const result = TestBed.runInInjectionContext(() =>
      authGuard(route, stateFor('/workspace/channel/7')),
    );
    expect(TestBed.inject(Router).serializeUrl(result as UrlTree)).toBe(
      '/login?returnUrl=%2Fworkspace%2Fchannel%2F7',
    );
  });
});

describe('guestGuard', () => {
  it('lets a signed-out visitor reach the login screen', () => {
    configure(false);
    const result = TestBed.runInInjectionContext(() => guestGuard(route, stateFor('/login')));
    expect(result).toBe(true);
  });

  it('sends a signed-in user to the workspace', () => {
    configure(true);
    const result = TestBed.runInInjectionContext(() => guestGuard(route, stateFor('/login')));
    expect(result).toBeInstanceOf(UrlTree);
    expect(TestBed.inject(Router).serializeUrl(result as UrlTree)).toBe('/workspace');
  });
});
