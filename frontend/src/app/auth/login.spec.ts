import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { User } from '../core/auth/user';
import Login from './login';

const GUEST: User = {
  id: 7,
  email: 'guest_x@guest.local',
  full_name: 'Guest',
  avatar: null,
  avatar_url: null,
  default_avatar: 'bob',
  is_guest: true,
  is_online: false,
};

describe('Login', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function render() {
    const fixture = TestBed.createComponent(Login);
    await fixture.whenStable();
    return fixture;
  }

  function el<T extends HTMLElement>(fixture: { nativeElement: HTMLElement }, testid: string) {
    return fixture.nativeElement.querySelector(`[data-testid="${testid}"]`) as T;
  }

  function type(fixture: { nativeElement: HTMLElement }, index: number, value: string) {
    const input = fixture.nativeElement.querySelectorAll('input')[index] as HTMLInputElement;
    input.value = value;
    input.dispatchEvent(new Event('input'));
  }

  it('renders the German copy from the design', async () => {
    const fixture = await render();
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Anmeldung');
    expect(text).toContain('Wir empfehlen dir');
    expect(text).toContain('Passwort vergessen?');
    expect(text).toContain('Anmelden mit Google');
    expect(text).toContain('Gäste-Login');
  });

  it('keeps submit disabled until the form is complete', async () => {
    const fixture = await render();
    const submit = el<HTMLButtonElement>(fixture, 'login');
    expect(submit.disabled).toBe(true);

    type(fixture, 0, 'ada@example.com');
    await fixture.whenStable();
    expect(submit.disabled).toBe(true);

    type(fixture, 1, 's3cret-pass');
    await fixture.whenStable();
    expect(submit.disabled).toBe(false);
  });

  it('rejects a malformed email', async () => {
    const fixture = await render();
    type(fixture, 0, 'not-an-email');
    type(fixture, 1, 's3cret-pass');
    await fixture.whenStable();

    expect(el<HTMLButtonElement>(fixture, 'login').disabled).toBe(true);
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('ungültig');
  });

  it('logs in and navigates to the workspace', async () => {
    const fixture = await render();
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);

    type(fixture, 0, 'ada@example.com');
    type(fixture, 1, 's3cret-pass');
    await fixture.whenStable();
    el<HTMLButtonElement>(fixture, 'login').click();

    const req = http.expectOne('/api/auth/login/');
    expect(req.request.body).toEqual({ email: 'ada@example.com', password: 's3cret-pass' });
    req.flush({ user: { ...GUEST, is_guest: false } });

    expect(navigate).toHaveBeenCalledWith('/workspace');
  });

  it('explains rejected credentials without blaming the network', async () => {
    const fixture = await render();
    type(fixture, 0, 'ada@example.com');
    type(fixture, 1, 'wrong-pass');
    await fixture.whenStable();
    el<HTMLButtonElement>(fixture, 'login').click();

    http.expectOne('/api/auth/login/').flush(null, { status: 400, statusText: 'Bad Request' });
    await fixture.whenStable();

    const alert = fixture.nativeElement.querySelector('[role="alert"]') as HTMLElement;
    expect(alert.textContent).toContain('stimmen nicht überein');
  });

  it('offers guest login without any form input', async () => {
    const fixture = await render();
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);

    el<HTMLButtonElement>(fixture, 'guest-login').click();
    http.expectOne('/api/auth/guest/').flush({ user: GUEST });

    expect(navigate).toHaveBeenCalledWith('/workspace');
  });
});
