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
  templateUrl: './auth-layout.html',
  styleUrl: './auth-layout.scss',
})
export class AuthLayout {
  readonly showSignupLink = input(false);

  /** Prose pages (Impressum, Datenschutz) need a wider card than a form does. */
  readonly wide = input(false);
}
