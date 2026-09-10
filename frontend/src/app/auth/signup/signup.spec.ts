import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { User } from '../../core/auth/user';
import Signup from './signup';

const CREATED: User = {
  id: 12,
  email: 'ada@example.com',
  full_name: 'Ada Lovelace',
  avatar: null,
  avatar_url: null,
  default_avatar: 'bob',
  is_guest: false,
  is_online: false,
};

describe('Signup', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function render() {
    const fixture = TestBed.createComponent(Signup);
    await fixture.whenStable();
    return fixture;
  }

  function el<T extends HTMLElement>(fixture: ComponentFixture<Signup>, testid: string) {
    return fixture.nativeElement.querySelector(`[data-testid="${testid}"]`) as T;
  }

  function type(fixture: ComponentFixture<Signup>, index: number, value: string) {
    const input = fixture.nativeElement.querySelectorAll('input')[index] as HTMLInputElement;
    input.value = value;
    input.dispatchEvent(new Event('input'));
  }

  function tickConsent(fixture: ComponentFixture<Signup>) {
    (fixture.nativeElement.querySelector('input[type="checkbox"]') as HTMLInputElement).click();
  }

  async function fillValid(fixture: ComponentFixture<Signup>, name = 'Ada Lovelace') {
    type(fixture, 0, name);
    type(fixture, 1, 'ada@example.com');
    type(fixture, 2, 's3cret-pass');
    tickConsent(fixture);
    await fixture.whenStable();
  }

  it('requires a first and last name', async () => {
    const fixture = await render();
    const submit = el<HTMLButtonElement>(fixture, 'signup');

    await fillValid(fixture, 'Ada');
    expect(submit.disabled).toBe(true);
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Vor- und Nachnamen');

    type(fixture, 0, 'Ada Lovelace');
    await fixture.whenStable();
    expect(submit.disabled).toBe(false);
  });

  it('keeps Weiter disabled until consent is ticked', async () => {
    const fixture = await render();
    const submit = el<HTMLButtonElement>(fixture, 'signup');

    type(fixture, 0, 'Ada Lovelace');
    type(fixture, 1, 'ada@example.com');
    type(fixture, 2, 's3cret-pass');
    await fixture.whenStable();
    expect(submit.disabled).toBe(true);

    tickConsent(fixture);
    await fixture.whenStable();
    expect(submit.disabled).toBe(false);
  });

  it('splits the name on the last space', async () => {
    const fixture = await render();
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);

    await fillValid(fixture, 'Anna Maria Weber');
    el<HTMLButtonElement>(fixture, 'signup').click();

    const req = http.expectOne('/api/auth/signup/');
    expect(req.request.body).toEqual({
      first_name: 'Anna Maria',
      last_name: 'Weber',
      email: 'ada@example.com',
      password: 's3cret-pass',
      consent: true,
    });
    req.flush({ user: CREATED });

    expect(navigate).toHaveBeenCalledWith('/avatar');
  });

  it('reports a duplicate email in German', async () => {
    const fixture = await render();

    await fillValid(fixture);
    el<HTMLButtonElement>(fixture, 'signup').click();

    http
      .expectOne('/api/auth/signup/')
      .flush(
        { email: ['A user with this email already exists.'] },
        { status: 400, statusText: 'Bad Request' },
      );
    await fixture.whenStable();

    const alert = fixture.nativeElement.querySelector('[role="alert"]') as HTMLElement;
    expect(alert.textContent).toContain('bereits verwendet');
  });
});
