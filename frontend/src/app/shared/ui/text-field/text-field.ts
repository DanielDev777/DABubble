import {
  booleanAttribute,
  ChangeDetectionStrategy,
  Component,
  computed,
  forwardRef,
  input,
  signal,
} from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

let nextId = 0;

/**
 * The pill-shaped input from the auth screens: optional leading icon, label,
 * error text. Implements ControlValueAccessor so it drops into the reactive
 * forms that 9b builds.
 */
@Component({
  selector: 'app-text-field',
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [
    { provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => TextField), multi: true },
  ],
  host: { class: 'app-text-field' },
  template: `
    @if (label()) {
      <label [attr.for]="id">{{ label() }}</label>
    }

    <div class="control" [class.invalid]="!!error()">
      @if (icon()) {
        <img class="icon" [src]="icon()" alt="" />
      }
      <input
        [id]="id"
        [type]="type()"
        [value]="value()"
        [placeholder]="placeholder()"
        [disabled]="disabled()"
        [attr.autocomplete]="autocomplete()"
        [attr.aria-invalid]="!!error()"
        [attr.aria-describedby]="error() ? errorId : null"
        (input)="onInput($event)"
        (blur)="onTouched()"
      />
    </div>

    @if (error()) {
      <p class="error" [id]="errorId" role="alert">{{ error() }}</p>
    }
  `,
  styles: `
    :host { display: grid; gap: var(--space-2); }

    label {
      font-size: var(--text-sm);
      color: var(--color-text-muted);
    }

    .control {
      display: flex;
      align-items: center;
      gap: var(--space-3);
      background: var(--color-bg);
      border: 1px solid transparent;
      border-radius: var(--radius-pill);
      padding: var(--space-3) var(--space-5);
      transition: border-color var(--duration-fast) var(--easing);
    }

    .control:focus-within { border-color: var(--color-primary); }
    .control.invalid { border-color: var(--color-danger); }

    .icon { width: 1.25rem; height: 1.25rem; flex: none; }

    input {
      flex: 1;
      min-width: 0;
      border: none;
      background: none;
      outline: none;
    }

    input::placeholder { color: var(--color-text-placeholder); }

    .error {
      margin: 0;
      padding-left: var(--space-4);
      font-size: var(--text-sm);
      color: var(--color-danger);
    }
  `,
})
export class TextField implements ControlValueAccessor {
  readonly label = input('');
  readonly placeholder = input('');
  readonly type = input<'text' | 'email' | 'password'>('text');
  readonly icon = input<string | null>(null);
  readonly error = input<string | null>(null);
  readonly autocomplete = input<string | null>(null);
  readonly required = input(false, { transform: booleanAttribute });

  protected readonly id = `app-text-field-${nextId++}`;
  protected readonly errorId = `${this.id}-error`;

  protected readonly value = signal('');
  protected readonly disabled = signal(false);

  private onChange: (value: string) => void = () => undefined;
  protected onTouched: () => void = () => undefined;

  writeValue(value: string | null): void {
    this.value.set(value ?? '');
  }

  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled.set(isDisabled);
  }

  protected onInput(event: Event): void {
    const next = (event.target as HTMLInputElement).value;
    this.value.set(next);
    this.onChange(next);
  }
}
