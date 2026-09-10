import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { AuthLayout } from '../auth-layout';
import { Button } from '../../shared/ui/button/button';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { TextField } from '../../shared/ui/text-field/text-field';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthStore } from '../../core/auth/auth-store';

@Component({
  imports: [AuthLayout, Button, ReactiveFormsModule, RouterLink, TextField],
  changeDetection: ChangeDetectionStrategy.OnPush,
  selector: 'app-signup',
  styleUrl: './signup.scss',
  templateUrl: './signup.html',
})
export default class Signup {
  private readonly auth = inject(AuthStore);
  private readonly router = inject(Router);

  protected readonly busy = signal(false);
  protected readonly formError = signal('');

  protected readonly form = new FormGroup({
    name: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.pattern(/^\S+(\s+\S+)+$/)],
    }),
    email: new FormControl('', {
      nonNullable: true, validators: [Validators.required, Validators.email],
    }),
    password: new FormControl('', {
      nonNullable: true, validators: [Validators.required, Validators.minLength(8)],
    }),
    consent: new FormControl(false, {
      nonNullable: true, validators: [Validators.requiredTrue],
    }),
  });

  private readonly status = signal(0);

  protected readonly nameError = computed(() => {
    this.status();
    const control = this.form.controls.name;
    if (control.valid || control.pristine) return null;
    return control.hasError('required')
      ? 'Bitte gib deinen Namen ein.'
      : 'Bitte gib Vor- und Nachnamen ein.';
  });

  protected readonly emailError = computed(() => {
    this.status();
    const control = this.form.controls.email;
    if (control.valid || control.pristine) return null;
    return control.hasError('required')
      ? 'Bitte gib deine E-Mail-Adresse ein.'
      : 'Diese E-Mail-Adresse ist leider ungültig.';
  });

  protected readonly passwordError = computed(() => {
    this.status();
    const control = this.form.controls.password;
    if (control.valid || control.pristine) return null;
    return control.hasError('required')
      ? 'Bitte gib ein Passwort ein.'
      : 'Das Passwort muss mindestens 8 Zeichen lang sein.';
  });

  constructor() {
    this.form.valueChanges.subscribe(() => this.status.update((value) => value + 1));
  }

  protected submit(): void {
    if (this.form.invalid || this.busy()) return;
    this.busy.set(true);
    this.formError.set('');

    const { name, email, password } = this.form.getRawValue();
    const cut = name.trim().lastIndexOf(' ');

    this.auth.signup({
      first_name: name.trim().slice(0, cut),
      last_name: name.trim().slice(cut + 1),
      email,
      password,
      consent: true,
    }).subscribe({
      // Signup auto-logs-in (201 + cookies), so the avatar step is authenticated.
      next: () => void this.router.navigateByUrl('/avatar'),
      error: (error: HttpErrorResponse) => {
        this.busy.set(false);
        this.formError.set(this.describe(error));
      },
    });
  }

  private describe(error: HttpErrorResponse): string {
    const email = error.error?.email?.[0] as string | undefined;
    if (email?.includes('already exists')) {
      return 'Diese E-Mail-Adresse wird bereits verwendet.';
    }
    const password = error.error?.password?.[0] as string | undefined;
    if (password) return 'Dieses Passwort ist zu schwach.';
    return 'Konto konnte nicht erstellt werden. Bitte versuche es später erneut.';
  }
}
