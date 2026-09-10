import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { ToastService } from '../../shared/ui/toast/toast';
import ForgotPassword from './forgot-password';

describe('ForgotPassword', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function render() {
    const fixture = TestBed.createComponent(ForgotPassword);
    await fixture.whenStable();
    return fixture;
  }

  function submitButton(fixture: ComponentFixture<ForgotPassword>) {
    return fixture.nativeElement.querySelector('[data-testid="send-reset"]') as HTMLButtonElement;
  }

  async function fill(fixture: ComponentFixture<ForgotPassword>, value: string) {
    const input = fixture.nativeElement.querySelector('input') as HTMLInputElement;
    input.value = value;
    input.dispatchEvent(new Event('input'));
    await fixture.whenStable();
  }

  it('keeps the button disabled until the address is valid', async () => {
    const fixture = await render();
    expect(submitButton(fixture).disabled).toBe(true);

    await fill(fixture, 'nope');
    expect(submitButton(fixture).disabled).toBe(true);
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('ungültig');

    await fill(fixture, 'ada@example.com');
    expect(submitButton(fixture).disabled).toBe(false);
  });

  it('confirms and returns to login', async () => {
    const fixture = await render();
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    const toasts = vi.spyOn(TestBed.inject(ToastService), 'show');

    await fill(fixture, 'ada@example.com');
    submitButton(fixture).click();

    const req = http.expectOne('/api/auth/password-reset/');
    expect(req.request.body).toEqual({ email: 'ada@example.com' });
    req.flush(null);
    await fixture.whenStable();

    expect(toasts).toHaveBeenCalledWith('E-Mail gesendet');
    expect(navigate).toHaveBeenCalledWith('/login');
  });

  it('says the same thing for an address with no account', async () => {
    const fixture = await render();
    vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    const toasts = vi.spyOn(TestBed.inject(ToastService), 'show');

    await fill(fixture, 'nobody@example.com');
    submitButton(fixture).click();
    http.expectOne('/api/auth/password-reset/').flush(null);
    await fixture.whenStable();

    // No account enumeration: an unknown address must look exactly like a known
    // one, so the confirmation is identical and nothing hints either way.
    expect(toasts).toHaveBeenCalledWith('E-Mail gesendet');
    expect((fixture.nativeElement as HTMLElement).querySelector('[role="alert"]')).toBeNull();
  });

  it('explains the throttle on 429', async () => {
    const fixture = await render();

    await fill(fixture, 'ada@example.com');
    submitButton(fixture).click();
    http
      .expectOne('/api/auth/password-reset/')
      .flush({ detail: 'Request was throttled.' }, { status: 429, statusText: 'Too Many Requests' });
    await fixture.whenStable();

    const alert = fixture.nativeElement.querySelector('[role="alert"]') as HTMLElement;
    expect(alert.textContent).toContain('Zu viele Anfragen');
    expect(submitButton(fixture).disabled).toBe(false);
  });
});
