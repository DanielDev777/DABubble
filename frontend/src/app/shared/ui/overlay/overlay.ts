import { DOCUMENT } from '@angular/common';
import {
  afterNextRender,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  inject,
  input,
  OnDestroy,
  output,
} from '@angular/core';

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

/**
 * Modal shell behind every "*B-Overlay *" screen in the Figma set: backdrop,
 * focus trap, Escape to close, scroll lock. Built once here because 9d brings a
 * dozen dialogs that all need the same behaviour.
 */
@Component({
  selector: 'app-overlay',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    class: 'app-overlay',
    '(keydown.escape)': 'close()',
    // Angular's keydown.tab matches Tab with no modifiers, so shift+tab
    // needs its own binding or focus escapes the dialog backwards.
    '(keydown.tab)': 'trapFocus($event)',
    '(keydown.shift.tab)': 'trapFocus($event)',
    '(click)': 'onBackdropClick($event)',
  },
  template: `
    <div
      class="panel"
      role="dialog"
      aria-modal="true"
      [attr.aria-label]="label()"
      (click)="$event.stopPropagation()"
    >
      <ng-content />
    </div>
  `,
  styles: `
    :host {
      position: fixed;
      inset: 0;
      z-index: 100;
      display: grid;
      place-items: center;
      padding: var(--space-4);
      background: rgba(27, 20, 100, 0.35);
    }

    .panel {
      background: var(--color-surface);
      border-radius: var(--radius-card);
      box-shadow: var(--shadow-overlay);
      padding: var(--space-6);
      max-width: min(32rem, 100%);
      max-height: 100%;
      overflow: auto;
    }
  `,
})
export class Overlay implements OnDestroy {
  readonly label = input.required<string>();
  readonly closed = output<void>();

  private readonly host = inject(ElementRef<HTMLElement>);
  private readonly document = inject(DOCUMENT);
  private readonly previousOverflow = this.document.body.style.overflow;
  private readonly previouslyFocused = this.document.activeElement as HTMLElement | null;

  constructor() {
    this.document.body.style.overflow = 'hidden';
    afterNextRender(() => this.focusables()[0]?.focus());
  }

  ngOnDestroy(): void {
    this.document.body.style.overflow = this.previousOverflow;
    this.previouslyFocused?.focus();
  }

  protected close(): void {
    this.closed.emit();
  }

  protected onBackdropClick(event: MouseEvent): void {
    if (event.target === this.host.nativeElement) {
      this.close();
    }
  }

  /** Keeps Tab inside the dialog, wrapping at both ends. */
  protected trapFocus(rawEvent: Event): void {
    const event = rawEvent as KeyboardEvent;
    const focusables = this.focusables();
    if (focusables.length === 0) {
      event.preventDefault();
      return;
    }

    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    const active = this.document.activeElement;

    if (event.shiftKey && (active === first || !this.host.nativeElement.contains(active))) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && active === last) {
      event.preventDefault();
      first.focus();
    }
  }

  private focusables(): HTMLElement[] {
    return Array.from(
      (this.host.nativeElement as HTMLElement).querySelectorAll<HTMLElement>(FOCUSABLE),
    );
  }
}
