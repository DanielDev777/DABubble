import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AuthStore } from '../core/auth/auth-store';
import { Button } from '../shared/ui/button/button';
import { TextField } from '../shared/ui/text-field/text-field';
import { ToastService } from '../shared/ui/toast/toast';
import { AuthLayout } from './auth-layout';

@Component({
  selector: 'app-login',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [AuthLayout, Button, ReactiveFormsModule, RouterLink, TextField],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export default class Login {
  private readonly auth = inject(AuthStore);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly toasts = inject(ToastService);

  protected readonly busy = signal(false);
  protected readonly formError = signal('');

  protected readonly form = new FormGroup({
    email: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.email] }),
    password: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
  });

  private readonly status = signal(0);

  protected emailError = computed(() => {
    this.status();
    const control = this.form.controls.email;
    if (control.valid || control.pristine) return null;
    return control.hasError('required')
      ? 'Bitte gib deine E-Mail-Adresse ein.'
      : 'Diese E-Mail-Adresse ist leider ungültig.';
  });

  protected passwordError = computed(() => {
    this.status();
    const control = this.form.controls.password;
    return control.valid || control.pristine ? null : 'Bitte gib dein Passwort ein.';
  });

  constructor() {
    this.form.valueChanges.subscribe(() => this.status.update((value) => value + 1));
  }

  protected submit(): void {
    if (this.form.invalid || this.busy()) return;

    this.busy.set(true);
    this.formError.set('');
    const { email, password } = this.form.getRawValue();

    this.auth.login(email, password).subscribe({
      next: () => void this.router.navigateByUrl(this.returnUrl()),
      error: (error: HttpErrorResponse) => {
        this.busy.set(false);
        this.formError.set(
          error.status === 400
            ? 'E-Mail-Adresse oder Passwort stimmen nicht überein.'
            : 'Anmeldung derzeit nicht möglich. Bitte versuche es später erneut.',
        );
      },
    });
  }

  protected asGuest(): void {
    this.busy.set(true);
    this.formError.set('');
    this.auth.loginAsGuest().subscribe({
      next: () => void this.router.navigateByUrl('/workspace'),
      error: () => {
        this.busy.set(false);
        this.formError.set('Gäste-Login derzeit nicht möglich.');
      },
    });
  }

  protected notImplemented(): void {
    this.toasts.show('Google-Anmeldung folgt in Kürze.');
  }

  private returnUrl(): string {
    return this.route.snapshot.queryParamMap.get('returnUrl') ?? '/workspace';
  }
}
