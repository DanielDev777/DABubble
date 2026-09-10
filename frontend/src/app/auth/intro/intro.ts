import { ChangeDetectionStrategy, Component, inject, OnDestroy, signal } from '@angular/core';
import { Router } from '@angular/router';

const SEEN_KEY = 'dabubble.intro';
const DURATION = 1600;

/**
 * The logo travelling from screen centre to its resting place in the login
 * header (Figma 00-Intro). Plays once per session, then hands over to /login.
 */
@Component({
  selector: 'app-intro',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './intro.html',
  styleUrl: './intro.scss',
})
export default class Intro implements OnDestroy {
  private readonly router = inject(Router);

  protected readonly done = signal(false);
  private timer: ReturnType<typeof setTimeout> | undefined;

  constructor() {
    if (this.alreadySeen()) {
      this.done.set(true);
      void this.router.navigateByUrl('/login');
      return;
    }

    this.remember();
    this.timer = setTimeout(() => void this.router.navigateByUrl('/login'), DURATION);
  }

  ngOnDestroy(): void {
    clearTimeout(this.timer);
  }

  // sessionStorage throws outright in some private-mode browsers, and a splash
  // screen is not worth failing the bootstrap over — treat any failure as
  // "not seen" and let the animation play.
  private alreadySeen(): boolean {
    try {
      return sessionStorage.getItem(SEEN_KEY) === '1';
    } catch {
      return false;
    }
  }

  private remember(): void {
    try {
      sessionStorage.setItem(SEEN_KEY, '1');
    } catch {
      // Ignored: the splash replays next visit, which is harmless.
    }
  }
}
