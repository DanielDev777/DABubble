import { ChangeDetectionStrategy, Component } from '@angular/core';

interface Swatch {
  name: string;
  token: string;
}

/** Development-only page for eyeballing the design tokens against the Figma set. */
@Component({
  selector: 'app-token-preview',
  changeDetection: ChangeDetectionStrategy.OnPush,
  styleUrl: './token-preview.scss',
  templateUrl: './token-preview.html',
})
export default class TokenPreview {
  protected readonly swatches: Swatch[] = [
    { name: 'Primary', token: '--color-primary' },
    { name: 'Primary hover', token: '--color-primary-hover' },
    { name: 'Accent', token: '--color-accent' },
    { name: 'Navy', token: '--color-navy' },
    { name: 'Background', token: '--color-bg' },
    { name: 'Surface alt', token: '--color-surface-alt' },
    { name: 'Border', token: '--color-border' },
    { name: 'Text muted', token: '--color-text-muted' },
    { name: 'Placeholder', token: '--color-text-placeholder' },
    { name: 'Online', token: '--color-online' },
    { name: 'Bubble pink', token: '--color-bubble-pink' },
    { name: 'Bubble green', token: '--color-bubble-green' },
    { name: 'Bubble orange', token: '--color-bubble-orange' },
    { name: 'Bubble blue', token: '--color-bubble-blue' },
  ];
}
