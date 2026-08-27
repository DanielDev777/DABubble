import {
  booleanAttribute,
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
} from '@angular/core';

import { avatarSrc, User } from '../../../core/auth/user';

export type AvatarSize = 'sm' | 'md' | 'lg';

/** A user's picture, with the presence dot the design puts on every avatar. */
@Component({
  selector: 'app-avatar',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    class: 'app-avatar',
    '[class.sm]': 'size() === "sm"',
    '[class.md]': 'size() === "md"',
    '[class.lg]': 'size() === "lg"',
  },
  template: `
    <img [src]="src()" [alt]="alt()" />
    @if (showPresence() && user()?.is_online) {
      <span class="presence" data-testid="presence" [attr.aria-label]="'Aktiv'"></span>
    }
  `,
  styles: `
    :host {
      position: relative;
      display: inline-block;
      flex: none;
      --avatar-size: 2.5rem;
    }

    :host(.sm) { --avatar-size: 1.75rem; }
    :host(.md) { --avatar-size: 2.5rem; }
    :host(.lg) { --avatar-size: 4rem; }

    img {
      width: var(--avatar-size);
      height: var(--avatar-size);
      border-radius: 50%;
      object-fit: cover;
      background: var(--color-surface-alt);
    }

    .presence {
      position: absolute;
      right: 0;
      bottom: 0;
      width: calc(var(--avatar-size) / 4);
      height: calc(var(--avatar-size) / 4);
      border-radius: 50%;
      background: var(--color-online);
      border: 2px solid var(--color-surface);
    }
  `,
})
export class Avatar {
  readonly user = input<User | null>(null);
  readonly size = input<AvatarSize>('md');
  readonly showPresence = input(true, { transform: booleanAttribute });

  protected readonly src = computed(() => avatarSrc(this.user()));
  protected readonly alt = computed(() => {
    const name = this.user()?.full_name;
    return name ? `Profilbild von ${name}` : 'Profilbild';
  });
}
