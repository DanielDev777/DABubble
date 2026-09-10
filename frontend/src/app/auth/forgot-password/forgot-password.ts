import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { PasswordResetService } from '../../core/auth/password-reset';
import { Button } from '../../shared/ui/button/button';
import { TextField } from '../../shared/ui/text-field/text-field';
import { ToastService } from '../../shared/ui/toast/toast';
import { AuthLayout } from '../auth-layout';

/**
 * Note the formal "Sie" in the copy: the reset flow and the 8c reset email
 * speak Sie, the rest of the app speaks du. Kept consistent within the flow.
 */
@Component({
  selector: 'app-forgot-password',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [AuthLayout, Button, ReactiveFormsModule, RouterLink, TextField],
  templateUrl: './forgot-password.html',
  styleUrl: './forgot-password.scss',
})
export default class ForgotPassword {
  private readonly reset = inject(PasswordResetService);
  private readonly router = inject(Router);
  private readonly toasts = inject(ToastService);

  protected readonly busy = signal(false);
  protected readonly formError = signal('');

  protected readonly form = new FormGroup({
    email: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.email],
    }),
  });

  // Reactive-forms validity is not a signal, so bump a counter on every change
  // and read it inside the computed. Same trick as login.ts.
  private readonly status = signal(0);

  protected readonly emailError = computed(() => {
    this.status();
    const control = this.form.controls.email;
    if (control.valid || control.pristine) return null;
    return control.hasError('required')
      ? 'Bitte geben Sie Ihre E-Mail-Adresse ein.'
      : 'Diese E-Mail-Adresse ist leider ungültig.';
  });

  constructor() {
    this.form.valueChanges.subscribe(() => this.status.update((value) => value + 1));
  }

  protected submit(): void {
    if (this.form.invalid || this.busy()) return;
    this.busy.set(true);
    this.formError.set('');

    this.reset.request(this.form.getRawValue().email).subscribe({
      // A 200 says the mail was accepted, not that the account exists. Showing
      // the same confirmation either way is the point of the endpoint.
      next: () => {
        this.toasts.show('E-Mail gesendet'); // 04B-Overlay
        void this.router.navigateByUrl('/login');
      },
      error: (error: HttpErrorResponse) => {
        this.busy.set(false);
        this.formError.set(
          error.status === 429
            ? 'Zu viele Anfragen. Bitte versuchen Sie es später erneut.' // the 5/hour throttle
            : 'E-Mail konnte nicht gesendet werden.',
        );
      },
    });
  }
}
