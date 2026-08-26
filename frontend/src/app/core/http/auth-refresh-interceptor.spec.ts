import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { AuthStore } from '../auth/auth-store';
import { authRefreshInterceptor } from './auth-refresh-interceptor';

const UNAUTHORIZED = { status: 401, statusText: 'Unauthorized' };

describe('authRefreshInterceptor', () => {
  let client: HttpClient;
  let http: HttpTestingController;
  let auth: AuthStore;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authRefreshInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    client = TestBed.inject(HttpClient);
    http = TestBed.inject(HttpTestingController);
    auth = TestBed.inject(AuthStore);
  });

  afterEach(() => http.verify());

  it('refreshes once and retries the original request', () => {
    let body: unknown;
    client.get('/api/channels/').subscribe((response) => (body = response));

    http.expectOne('/api/channels/').flush(null, UNAUTHORIZED);
    http.expectOne('/api/auth/refresh/').flush(null);
    http.expectOne('/api/channels/').flush([{ id: 1 }]);

    expect(body).toEqual([{ id: 1 }]);
  });

  it('refreshes only once for concurrent failures', () => {
    client.get('/api/channels/').subscribe();
    client.get('/api/messages/').subscribe();
    client.get('/api/notifications/').subscribe();

    http.expectOne('/api/channels/').flush(null, UNAUTHORIZED);
    http.expectOne('/api/messages/').flush(null, UNAUTHORIZED);
    http.expectOne('/api/notifications/').flush(null, UNAUTHORIZED);

    // One refresh for all three, or rotation invalidates the others.
    http.expectOne('/api/auth/refresh/').flush(null);

    http.expectOne('/api/channels/').flush([]);
    http.expectOne('/api/messages/').flush([]);
    http.expectOne('/api/notifications/').flush([]);
  });

  it('gives up and clears the session when refreshing fails', () => {
    let failed = false;
    client.get('/api/channels/').subscribe({ error: () => (failed = true) });

    http.expectOne('/api/channels/').flush(null, UNAUTHORIZED);
    http.expectOne('/api/auth/refresh/').flush(null, UNAUTHORIZED);

    expect(failed).toBe(true);
    expect(auth.user()).toBeNull();
  });

  it('does not refresh when login itself is rejected', () => {
    let failed = false;
    client.post('/api/auth/login/', {}).subscribe({ error: () => (failed = true) });

    http.expectOne('/api/auth/login/').flush(null, UNAUTHORIZED);

    http.expectNone('/api/auth/refresh/');
    expect(failed).toBe(true);
  });

  it('does not refresh on a non-401 failure', () => {
    client.get('/api/channels/').subscribe({ error: () => undefined });
    http.expectOne('/api/channels/').flush(null, { status: 403, statusText: 'Forbidden' });
    http.expectNone('/api/auth/refresh/');
  });
});
