import { HttpClient, provideHttpClient, withXsrfConfiguration } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

describe('Django CSRF wiring', () => {
  let client: HttpClient;
  let http: HttpTestingController;

  beforeEach(() => {
    document.cookie = 'csrftoken=token-from-django';
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(
          withXsrfConfiguration({ cookieName: 'csrftoken', headerName: 'X-CSRFToken' }),
        ),
        provideHttpClientTesting(),
      ],
    });
    client = TestBed.inject(HttpClient);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('sends the django csrf header on writes', () => {
    client.post('/api/messages/', { text: 'hallo' }).subscribe();
    const req = http.expectOne('/api/messages/');
    expect(req.request.headers.get('X-CSRFToken')).toBe('token-from-django');
    req.flush({});
  });

  it('leaves safe methods alone', () => {
    client.get('/api/channels/').subscribe();
    const req = http.expectOne('/api/channels/');
    expect(req.request.headers.has('X-CSRFToken')).toBe(false);
    req.flush([]);
  });
});
