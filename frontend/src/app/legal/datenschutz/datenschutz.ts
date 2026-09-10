import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthLayout } from '../../auth/auth-layout';

/**
 * The headings list what DABubble actually stores, which is the part that comes
 * from the code. The prose underneath is a legal statement about how it is
 * handled and has to be written by the operator, not generated.
 */
@Component({
  selector: 'app-datenschutz',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [AuthLayout, RouterLink],
  templateUrl: './datenschutz.html',
  styleUrl: './datenschutz.scss',
})
export default class Datenschutz {}
