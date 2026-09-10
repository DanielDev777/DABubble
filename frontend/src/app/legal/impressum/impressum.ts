import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthLayout } from '../../auth/auth-layout';

/**
 * Deliberately unfinished. An Impressum is a legal document under § 5 DDG and
 * needs the operator's real name, address and contact details — plausible-looking
 * placeholder text would be worse than a visible TODO.
 */
@Component({
  selector: 'app-impressum',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [AuthLayout, RouterLink],
  templateUrl: './impressum.html',
  styleUrl: './impressum.scss',
})
export default class Impressum {}
