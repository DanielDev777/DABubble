import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter, Router } from '@angular/router';

import { ToastService } from '../../shared/ui/toast/toast';
import ResetPassword from './reset-password';

function withQueryParams(params: Record<string, string>) {
  return {
    provide: ActivatedRoute,
    useValue: { snapshot: { queryParamMap: convertToParamMap(params) } },
  };
}

const GOOD_LINK = { uid: 'MTI', token: 'abc-123' };

describe('ResetPassword', () => {
  let http: HttpTestingController;

  function configure(params: Record<string, string>) {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        withQueryParams(params),
      ],
    });
    http = TestBed.inject(HttpTestingController);
  }

  afterEach(() => http.verify());

  async function render(params: Record<string, string> = GOOD_LINK) {
    configure(params);
    const fixture = TestBed.createComponent(ResetPassword);
    await fixture.whenStable();
    return fixture;
  }

  function el<T extends HTMLElement>(fixture: ComponentFixture<ResetPassword>, testid: string) {
    return fixture.nativeElement.querySelector(`[data-testid="${testid}"]`) as T | null;
  }

  async function fill(fixture: ComponentFixture<ResetPassword>, password: string, confirm = password) {
    const inputs = fixture.nativeElement.querySelectorAll('input') as NodeListOf<HTMLInputElement>;
    inputs[0].value = password;
    inputs[0].dispatchEvent(new Event('input'));
    inputs[1].value = confirm;
    inputs[1].dispatchEvent(new Event('input'));
    await fixture.whenStable();
  }

  it('shows the dead end without a request when the link has no uid or token', async () => {
    const fixture = await render({});

    expect(el(fixture, 'link-error')).not.toBeNull();
    expect(el(fixture, 'reset-submit')).toBeNull();
    // The important half: nothing was sent. http.verify() in afterEach proves it.
  });

  it('refuses to submit when the two passwords differ', async () => {
    const fixture = await render();

    await fill(fixture, 'new-pass-4711', 'new-pass-0815');
    expect(el<HTMLButtonElement>(fixture, 'reset-submit')!.disabled).toBe(true);
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('stimmen nicht überein');

    await fill(fixture, 'new-pass-4711');
    expect(el<HTMLButtonElement>(fixture, 'reset-submit')!.disabled).toBe(false);
  });

  it('confirms the reset and sends the visitor to login', async () => {
    const fixture = await render();
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    const toasts = vi.spyOn(TestBed.inject(ToastService), 'show');

    await fill(fixture, 'new-pass-4711');
    el<HTMLButtonElement>(fixture, 'reset-submit')!.click();

    const req = http.expectOne('/api/auth/password-reset/confirm/');
    expect(req.request.body).toEqual({ ...GOOD_LINK, password: 'new-pass-4711' });
    req.flush(null);
    await fixture.whenStable();

    expect(toasts).toHaveBeenCalledWith('Passwort geändert');
    expect(navigate).toHaveBeenCalledWith('/login');
  });

  it('translates a rejected password and keeps the form usable', async () => {
    const fixture = await render();
    vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);

    await fill(fixture, 'password1234');
    el<HTMLButtonElement>(fixture, 'reset-submit')!.click();
    http.expectOne('/api/auth/password-reset/confirm/').flush(
      { password: ['This password is too common.'] },
      { status: 400, statusText: 'Bad Request' },
    );
    await fixture.whenStable();

    // A rejected password must not burn the link — the form stays, not the
    // dead end, so a second attempt with a stronger password can succeed.
    expect(el(fixture, 'link-error')).toBeNull();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('zu häufig');

    await fill(fixture, 'k0rrekt-pferd-batterie');
    el<HTMLButtonElement>(fixture, 'reset-submit')!.click();
    http.expectOne('/api/auth/password-reset/confirm/').flush(null);
    await fixture.whenStable();
  });

  it('shows the dead end when the server says the link is spent', async () => {
    const fixture = await render();

    await fill(fixture, 'new-pass-4711');
    el<HTMLButtonElement>(fixture, 'reset-submit')!.click();
    http.expectOne('/api/auth/password-reset/confirm/').flush(
      { detail: 'Invalid or expired link.' },
      { status: 400, statusText: 'Bad Request' },
    );
    await fixture.whenStable();

    expect(el(fixture, 'link-error')).not.toBeNull();
    expect(el(fixture, 'retry-reset')).not.toBeNull();
  });
});
