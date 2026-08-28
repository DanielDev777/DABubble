import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

/**
 * The frame every auth screen shares: brand mark top-left, optional
 * "Neu bei DABubble?" call to action top-right, centred card, legal footer.
 */
@Component({
  selector: 'app-auth-layout',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  template: `
    <div class="page">
      <header>
        <img class="logo" src="/brand/logo.png" alt="DABubble" />

        @if (showSignupLink()) {
          <div class="signup-cta">
            <span>Neu bei DABubble?</span>
            <a routerLink="/signup">Konto erstellen</a>
          </div>
        }
      </header>

      <main>
        <section class="card">
          <ng-content />
        </section>
      </main>

      <footer>
        <a routerLink="/impressum">Impressum</a>
        <a routerLink="/datenschutz">Datenschutz</a>
      </footer>
    </div>
  `,
  styles: `
    @use '../../styles/mixins' as *;

    .page {
      min-height: 100dvh;
      display: grid;
      grid-template-rows: auto 1fr auto;
      gap: var(--space-5);
      padding: var(--space-5) var(--space-6);
    }

    header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: var(--space-4);
    }

    .logo { height: 4.5rem; width: auto; }

    .signup-cta {
      display: grid;
      justify-items: end;
      gap: var(--space-2);
      font-size: var(--text-lg);
    }

    main { display: grid; place-items: center; }

    .card {
      width: min(39rem, 100%);
      background: var(--color-surface);
      border-radius: var(--radius-card);
      box-shadow: var(--shadow-card);
      padding: var(--space-7) var(--space-6);
    }

    footer {
      display: flex;
      justify-content: center;
      gap: var(--space-6);
    }

    @include mobile {
      .page { padding: var(--space-4) var(--space-3); }
      .logo { height: 3rem; }
      .signup-cta { font-size: var(--text-base); }
      .card { padding: var(--space-6) var(--space-4); }
    }
  `,
})
export class AuthLayout {
  readonly showSignupLink = input(false);
}
