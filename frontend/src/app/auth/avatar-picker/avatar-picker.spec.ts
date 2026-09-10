import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { AuthStore } from '../../core/auth/auth-store';
import { User } from '../../core/auth/user';
import { ToastService } from '../../shared/ui/toast/toast';
import AvatarPicker from './avatar-picker';

const ADA: User = {
  id: 12,
  email: 'ada@example.com',
  full_name: 'Ada Lovelace',
  avatar: null,
  avatar_url: null,
  default_avatar: null,
  is_guest: false,
  is_online: false,
};

describe('AvatarPicker', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function render() {
    // Signup left a session behind, so the store already knows who this is.
    TestBed.inject(AuthStore).restore();
    http.expectOne('/api/auth/me/').flush(ADA);

    const fixture = TestBed.createComponent(AvatarPicker);
    await fixture.whenStable();
    return fixture;
  }

  function el<T extends HTMLElement>(fixture: ComponentFixture<AvatarPicker>, testid: string) {
    return fixture.nativeElement.querySelector(`[data-testid="${testid}"]`) as T;
  }

  it('shows the new account name and offers the six default avatars', async () => {
    const fixture = await render();
    const host = fixture.nativeElement as HTMLElement;

    expect(host.textContent).toContain('Ada Lovelace');
    expect(host.querySelectorAll('.choices button')).toHaveLength(6);
  });

  it('keeps Weiter disabled until an avatar is picked', async () => {
    const fixture = await render();
    const submit = el<HTMLButtonElement>(fixture, 'avatar-continue');
    expect(submit.disabled).toBe(true);

    el<HTMLButtonElement>(fixture, 'avatar-bob').click();
    await fixture.whenStable();

    expect(submit.disabled).toBe(false);
  });

  it('previews the selected avatar', async () => {
    const fixture = await render();
    const preview = fixture.nativeElement.querySelector('.preview') as HTMLImageElement;
    expect(preview.getAttribute('src')).toBe('/avatars/placeholder.svg');

    el<HTMLButtonElement>(fixture, 'avatar-quiff').click();
    await fixture.whenStable();

    expect(preview.getAttribute('src')).toBe('/avatars/quiff.png');
  });

  it('patches the profile and lands in the workspace', async () => {
    const fixture = await render();
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    const toasts = vi.spyOn(TestBed.inject(ToastService), 'show');

    el<HTMLButtonElement>(fixture, 'avatar-bald-beard').click();
    await fixture.whenStable();
    el<HTMLButtonElement>(fixture, 'avatar-continue').click();

    const req = http.expectOne('/api/auth/me/');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ default_avatar: 'bald-beard' });
    req.flush({ ...ADA, default_avatar: 'bald-beard' });
    await fixture.whenStable();

    expect(toasts).toHaveBeenCalledWith('Konto erfolgreich erstellt!');
    expect(navigate).toHaveBeenCalledWith('/workspace');
  });

  it('stays put and complains when the patch fails', async () => {
    const fixture = await render();
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    const toasts = vi.spyOn(TestBed.inject(ToastService), 'error');

    el<HTMLButtonElement>(fixture, 'avatar-bob').click();
    await fixture.whenStable();
    const submit = el<HTMLButtonElement>(fixture, 'avatar-continue');
    submit.click();

    http
      .expectOne('/api/auth/me/')
      .flush({ detail: 'CSRF Failed' }, { status: 403, statusText: 'Forbidden' });
    await fixture.whenStable();

    expect(toasts).toHaveBeenCalledWith('Avatar konnte nicht gespeichert werden.');
    expect(navigate).not.toHaveBeenCalled();
    expect(submit.disabled).toBe(false);
  });
});
