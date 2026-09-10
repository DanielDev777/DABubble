import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { AuthStore } from '../../core/auth/auth-store';
import { FALLBACK_AVATAR } from '../../core/auth/user';
import { Button } from '../../shared/ui/button/button';
import { ToastService } from '../../shared/ui/toast/toast';
import { AuthLayout } from '../auth-layout';

/**
 * The last step of onboarding, and the app's first authenticated write — so it
 * is also where the X-CSRFToken wiring meets a CSRF-enforcing Django endpoint
 * for the first time. A 403 here points at app.config.ts, not at this file.
 */
@Component({
  selector: 'app-avatar-picker',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [AuthLayout, Button, RouterLink],
  templateUrl: './avatar-picker.html',
  styleUrl: './avatar-picker.scss',
})
export default class AvatarPicker {
  protected readonly auth = inject(AuthStore);
  private readonly router = inject(Router);
  private readonly toasts = inject(ToastService);

  // These strings are the backend's stored slugs; each one must have a matching
  // public/avatars/<slug>.png.
  protected readonly slugs = ['long-hair', 'quiff', 'wavy-hair', 'bald-beard', 'bob', 'dark-hair'];
  protected readonly selected = signal<string | null>(null);
  protected readonly busy = signal(false);

  protected readonly preview = computed(() => {
    const slug = this.selected();
    return slug ? `/avatars/${slug}.png` : FALLBACK_AVATAR;
  });

  protected save(): void {
    const slug = this.selected();
    if (!slug || this.busy()) return;
    this.busy.set(true);

    this.auth.updateProfile({ default_avatar: slug }).subscribe({
      next: () => {
        this.toasts.show('Konto erfolgreich erstellt!'); // 03B-Overlay One
        void this.router.navigateByUrl('/workspace');
      },
      error: () => {
        this.busy.set(false);
        this.toasts.error('Avatar konnte nicht gespeichert werden.');
      },
    });
  }
}
