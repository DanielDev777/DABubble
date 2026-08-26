import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-not-found',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  template: `
    <main class="card">
      <h1>404</h1>
      <p>Diese Seite gibt es nicht.</p>
      <a routerLink="/">Zurück zur Startseite</a>
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
  `,
})
export default class NotFound {}
