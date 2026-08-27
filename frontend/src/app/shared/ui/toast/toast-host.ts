import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { ToastService } from './toast';

/** Renders the toast stack. Belongs once, at the app root. */
@Component({
  selector: 'app-toast-host',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { class: 'app-toast-host', role: 'status', 'aria-live': 'polite' },
  template: `
    @for (toast of toasts.toasts(); track toast.id) {
      <div class="toast" [class.error]="toast.tone === 'error'">
        <span>{{ toast.text }}</span>
        <button type="button" aria-label="Schließen" (click)="toasts.dismiss(toast.id)">×</button>
      </div>
    }
  `,
  styles: `
    :host {
      position: fixed;
      inset-block-end: var(--space-5);
      inset-inline: 0;
      z-index: 200;
      display: grid;
      gap: var(--space-2);
      justify-items: center;
      pointer-events: none;
    }

    .toast {
      pointer-events: auto;
      display: flex;
      align-items: center;
      gap: var(--space-4);
      background: var(--color-primary);
      color: #fff;
      border-radius: var(--radius-card);
      box-shadow: var(--shadow-overlay);
      padding: var(--space-3) var(--space-5);
      font-weight: var(--weight-semibold);
    }

    .toast.error { background: var(--color-danger); }

    button { color: inherit; font-size: var(--text-lg); line-height: 1; }
  `,
})
export class ToastHost {
  protected readonly toasts = inject(ToastService);
}
