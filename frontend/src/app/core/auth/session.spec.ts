import { HttpClient } from '@angular/common/http';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { SessionService } from './session';

describe('SessionService', () => {
  let session: SessionService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    session = TestBed.inject(SessionService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('posts to the refresh endpoint', () => {
    session.refresh().subscribe();
    const req = http.expectOne('/api/auth/refresh/');
    expect(req.request.method).toBe('POST');
    req.flush(null);
  });

  it('shares one request between concurrent callers', () => {
    let completed = 0;
    session.refresh().subscribe(() => completed++);
    session.refresh().subscribe(() => completed++);
    session.refresh().subscribe(() => completed++);

    // One HTTP call, three satisfied callers. Without this, token rotation
    // blacklists each token out from under the next request.
    http.expectOne('/api/auth/refresh/').flush(null);
    expect(completed).toBe(3);
  });

  it('starts a fresh request once the previous one finished', () => {
    session.refresh().subscribe();
    http.expectOne('/api/auth/refresh/').flush(null);

    session.refresh().subscribe();
    http.expectOne('/api/auth/refresh/').flush(null);
  });

  it('releases the in-flight request when refreshing fails', () => {
    session.refresh().subscribe({ error: () => undefined });
    http.expectOne('/api/auth/refresh/').flush(null, { status: 401, statusText: 'Unauthorized' });

    session.refresh().subscribe({ error: () => undefined });
    http.expectOne('/api/auth/refresh/').flush(null, { status: 401, statusText: 'Unauthorized' });
  });
});
