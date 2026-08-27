import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { Button } from './button';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Button],
  template: `
    <button appButton [variant]="variant()" [disabled]="disabled()" (click)="clicks = clicks + 1">
      Senden
    </button>
  `,
})
class Host {
  readonly variant = signal<'primary' | 'secondary' | 'ghost'>('primary');
  readonly disabled = signal(false);
  clicks = 0;
}

describe('Button', () => {
  async function render() {
    const fixture = TestBed.createComponent(Host);
    await fixture.whenStable();
    return fixture;
  }

  it('marks the primary variant', async () => {
    const fixture = await render();
    const button = fixture.nativeElement.querySelector('button') as HTMLButtonElement;
    expect(button.classList).toContain('app-button');
    expect(button.classList).toContain('primary');
  });

  it('switches variant classes', async () => {
    const fixture = await render();
    fixture.componentInstance.variant.set('secondary');
    await fixture.whenStable();

    const button = fixture.nativeElement.querySelector('button') as HTMLButtonElement;
    expect(button.classList).toContain('secondary');
    expect(button.classList).not.toContain('primary');
  });

  it('keeps native disabled semantics', async () => {
    const fixture = await render();
    fixture.componentInstance.disabled.set(true);
    await fixture.whenStable();

    const button = fixture.nativeElement.querySelector('button') as HTMLButtonElement;
    expect(button.disabled).toBe(true);

    button.click();
    expect(fixture.componentInstance.clicks).toBe(0);
  });

  it('clicks through when enabled', async () => {
    const fixture = await render();
    (fixture.nativeElement.querySelector('button') as HTMLButtonElement).click();
    expect(fixture.componentInstance.clicks).toBe(1);
  });
});
