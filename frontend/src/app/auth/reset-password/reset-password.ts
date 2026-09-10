import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import {
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { PasswordResetService } from '../../core/auth/password-reset';
import { Button } from '../../shared/ui/button/button';
import { TextField } from '../../shared/ui/text-field/text-field';
import { ToastService } from '../../shared/ui/toast/toast';
import { AuthLayout } from '../auth-layout';

/** The confirm field is frontend-only — the API takes a single password. */
const passwordsMatch: ValidatorFn = (group) => {
  const { password, confirm } = (group as FormGroup).getRawValue();
  return password && confirm && password !== confirm ? { mismatch: true } : null;
};

@Component({
  selector: 'app-reset-password',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [AuthLayout, Button, ReactiveFormsModule, RouterLink, TextField],
  templateUrl: './reset-password.html',
  styleUrl: './reset-password.scss',
})
export default class ResetPassword {
  private readonly route = inject(ActivatedRoute);
  private readonly reset = inject(PasswordResetService);
  private readonly router = inject(Router);
  private readonly toasts = inject(ToastService);

  private readonly uid = this.route.snapshot.queryParamMap.get('uid') ?? '';
  private readonly token = this.route.snapshot.queryParamMap.get('token') ?? '';

  protected readonly busy = signal(false);
  protected readonly formError = signal('');

  // A link with no uid/token is already dead: show the dead end without asking
  // the server about credentials we do not have.
  protected readonly linkError = signal(!this.uid || !this.token);

  protected readonly form = new FormGroup(
    {
      password: new FormControl('', {
        nonNullable: true,
        validators: [Validators.required, Validators.minLength(8)],
      }),
      confirm: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
    },
    { validators: passwordsMatch },
  );

  // Reactive-forms validity is not a signal, so bump a counter on every change
  // and read it inside each computed. Same trick as login.ts.
  private readonly status = signal(0);

  protected readonly passwordError = computed(() => {
    this.status();
    const control = this.form.controls.password;
    if (control.valid || control.pristine) return null;
    return control.hasError('required')
      ? 'Bitte geben Sie ein Passwort ein.'
      : 'Das Passwort muss mindestens 8 Zeichen lang sein.';
  });

  protected readonly confirmError = computed(() => {
    this.status();
    const control = this.form.controls.confirm;
    if (control.pristine) return null;
    if (control.hasError('required')) return 'Bitte bestätigen Sie Ihr Passwort.';
    return this.form.hasError('mismatch') ? 'Die Passwörter stimmen nicht überein.' : null;
  });

  constructor() {
    this.form.valueChanges.subscribe(() => this.status.update((value) => value + 1));
  }

  protected submit(): void {
    if (this.form.invalid || this.busy()) return;
    this.busy.set(true);
    this.formError.set('');

    this.reset.confirm(this.uid, this.token, this.form.getRawValue().password).subscribe({
      next: () => {
        this.toasts.show('Passwort geändert'); // 05B-Overlay
        void this.router.navigateByUrl('/login');
      },
      error: (error: HttpErrorResponse) => {
        this.busy.set(false);
        // Two distinct 400 shapes, by design: a top-level `detail` means the
        // link is bad or spent; a `password` array means the password itself
        // was rejected and the link is still good for another try.
        if (error.error?.detail) {
          this.linkError.set(true);
        } else {
          this.formError.set(this.translate(error.error?.password?.[0]));
        }
      },
    });
  }

  /** Django's validators answer in English; the UI is German. */
  private translate(message?: string): string {
    if (!message) return 'Passwort konnte nicht geändert werden.';
    if (message.includes('too short')) return 'Das Passwort muss mindestens 8 Zeichen lang sein.';
    if (message.includes('too common')) return 'Dieses Passwort ist zu häufig.';
    if (message.includes('entirely numeric')) {
      return 'Das Passwort darf nicht nur aus Zahlen bestehen.';
    }
    return 'Dieses Passwort ist nicht sicher genug.';
  }
}
