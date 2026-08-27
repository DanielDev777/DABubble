import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { AuthStore } from './auth-store';
import { User } from './user';

const ADA: User = {
  id: 1,
  email: 'ada@example.com',
  full_name: 'Ada Lovelace',
  avatar: null,
  avatar_url: null,
  default_avatar: 'bob',
  is_guest: false,
  is_online: true,
};

describe('AuthStore', () => {
  let store: AuthStore;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    store = TestBed.inject(AuthStore);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('starts logged out', () => {
    expect(store.user()).toBeNull();
    expect(store.isAuthenticated()).toBe(false);
  });

  it('stores the user after login', () => {
    store.login('ada@example.com', 's3cret').subscribe();
    const req = http.expectOne('/api/auth/login/');
    expect(req.request.body).toEqual({ email: 'ada@example.com', password: 's3cret' });
    req.flush({ user: ADA });

    expect(store.user()).toEqual(ADA);
    expect(store.isAuthenticated()).toBe(true);
  });

  it('stores the user after signup', () => {
    store
      .signup({
        first_name: 'Ada',
        last_name: 'Lovelace',
        email: 'ada@example.com',
        password: 's3cret',
        consent: true,
      })
      .subscribe();
    http.expectOne('/api/auth/signup/').flush({ user: ADA });
    expect(store.user()).toEqual(ADA);
  });

  it('flags guest sessions', () => {
    store.loginAsGuest().subscribe();
    http.expectOne('/api/auth/guest/').flush({ user: { ...ADA, is_guest: true } });
    expect(store.isGuest()).toBe(true);
  });

  it('sends the google id token under the name the backend expects', () => {
    store.loginWithGoogle('id-token-123').subscribe();
    const req = http.expectOne('/api/auth/google/');
    expect(req.request.body).toEqual({ id_token: 'id-token-123' });
    req.flush({ user: ADA });
  });

  it('restores a session from the me endpoint', async () => {
    const restored = store.restore();
    http.expectOne('/api/auth/me/').flush(ADA);
    await restored;
    expect(store.user()).toEqual(ADA);
  });

  it('resolves restore as logged out on 401 instead of failing bootstrap', async () => {
    const restored = store.restore();
    http.expectOne('/api/auth/me/').flush(null, { status: 401, statusText: 'Unauthorized' });
    await restored;
    expect(store.user()).toBeNull();
  });

  it('clears the user on logout', () => {
    store.login('ada@example.com', 's3cret').subscribe();
    http.expectOne('/api/auth/login/').flush({ user: ADA });

    store.logout().subscribe();
    http.expectOne('/api/auth/logout/').flush(null);
    expect(store.user()).toBeNull();
  });

  it('clears the user even when logout fails on the server', () => {
    store.login('ada@example.com', 's3cret').subscribe();
    http.expectOne('/api/auth/login/').flush({ user: ADA });

    store.logout().subscribe();
    http.expectOne('/api/auth/logout/').flush(null, { status: 500, statusText: 'Server Error' });
    expect(store.user()).toBeNull();
  });
});
