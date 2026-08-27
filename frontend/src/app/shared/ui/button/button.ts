import { booleanAttribute, ChangeDetectionStrategy, Component, input } from '@angular/core';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost';

/**
 * Styles a native <button>: `<button appButton variant="secondary">`.
 *
 * Deliberately an attribute selector rather than a wrapper element. A real
 * <button> submits forms, handles Enter and Space, exposes disabled state to
 * assistive tech and takes focus — none of which a div with role="button" gets
 * for free, and all of which the auth forms in 9b need.
 */
@Component({
  selector: 'button[appButton]',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    class: 'app-button',
    '[class.primary]': 'variant() === "primary"',
    '[class.secondary]': 'variant() === "secondary"',
    '[class.ghost]': 'variant() === "ghost"',
    '[class.full-width]': 'fullWidth()',
  },
  template: '<ng-content />',
  styles: `
    :host {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: var(--space-2);
      padding: var(--space-3) var(--space-5);
      border-radius: var(--radius-pill);
      font-weight: var(--weight-semibold);
      font-size: var(--text-base);
      line-height: 1.2;
      transition: background var(--duration-fast) var(--easing),
        color var(--duration-fast) var(--easing);
    }

    :host(.full-width) { width: 100%; }

    :host(.primary) {
      background: var(--color-primary);
      color: #fff;
    }

    :host(.primary:hover:not(:disabled)) { background: var(--color-primary-hover); }

    :host(.secondary) {
      background: var(--color-surface);
      color: var(--color-primary);
      border: 1px solid var(--color-primary);
    }

    :host(.secondary:hover:not(:disabled)) {
      background: var(--color-surface-alt);
      color: var(--color-primary-hover);
    }

    :host(.ghost) {
      background: transparent;
      color: var(--color-text);
      padding: var(--space-2) var(--space-3);
    }

    :host(.ghost:hover:not(:disabled)) { background: var(--color-surface-alt); }

    :host(:disabled) {
      background: var(--color-text-muted);
      border-color: var(--color-text-muted);
      color: #fff;
      cursor: default;
    }

    :host(.ghost:disabled) {
      background: transparent;
      color: var(--color-text-muted);
    }
  `,
})
export class Button {
  readonly variant = input<ButtonVariant>('primary');
  readonly fullWidth = input(false, { transform: booleanAttribute });
}
