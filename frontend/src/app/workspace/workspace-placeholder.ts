import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router } from '@angular/router';

import { AuthStore } from '../core/auth/auth-store';

/** Placeholder. The real workspace shell arrives with Part 9c. */
@Component({
  selector: 'app-workspace-placeholder',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="card">
      <h1>Eingeloggt</h1>
      <p data-testid="current-user">{{ auth.user()?.full_name }}</p>
      <button type="button" data-testid="logout" (click)="logout()">Abmelden</button>
    </main>
  `,
  styles: `
    .card {
      max-width: 32rem;
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
  `,
})
export default class WorkspacePlaceholder {
  protected readonly auth = inject(AuthStore);
  private readonly router = inject(Router);

  protected logout(): void {
    this.auth.logout().subscribe(() => void this.router.navigateByUrl('/login'));
  }
}
