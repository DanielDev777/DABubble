import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

import { AuthStore } from '../core/auth/auth-store';

/** Placeholder. The real login screen arrives with Part 9b. */
@Component({
  selector: 'app-login-placeholder',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="card">
      <h1>DABubble</h1>
      <p>Anmeldung folgt in Teil 9b.</p>
      <button type="button" data-testid="guest-login" [disabled]="busy()" (click)="asGuest()">
        Gastzugang
      </button>
      @if (error()) {
        <p role="alert" class="error">{{ error() }}</p>
      }
    </main>
  `,
  styles: `
    .card {
      max-width: 24rem;
      margin: 10vh auto;
      padding: var(--space-6);
      display: grid;
      gap: var(--space-4);
      justify-items: center;
      background: var(--color-surface);
      border-radius: var(--radius-card);
      box-shadow: var(--shadow-card);
    }

    button {
      background: var(--color-primary);
      color: #fff;
      border-radius: var(--radius-pill);
      padding: var(--space-3) var(--space-5);
      font-weight: var(--weight-semibold);
    }

    button:disabled { background: var(--color-text-muted); cursor: default; }
    .error { color: var(--color-danger); }
  `,
})
export default class LoginPlaceholder {
  private readonly auth = inject(AuthStore);
  private readonly router = inject(Router);

  protected readonly busy = signal(false);
  protected readonly error = signal('');

  protected asGuest(): void {
    this.busy.set(true);
    this.error.set('');
    this.auth.loginAsGuest().subscribe({
      next: () => void this.router.navigateByUrl('/workspace'),
      error: () => {
        this.busy.set(false);
        this.error.set('Gastzugang fehlgeschlagen.');
      },
    });
  }
}
