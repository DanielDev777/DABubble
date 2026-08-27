import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { Overlay } from './overlay';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Overlay],
  template: `
    @if (open()) {
      <app-overlay label="Kanal erstellen" (closed)="open.set(false)">
        <button type="button" data-testid="first">Erste</button>
        <button type="button" data-testid="last">Letzte</button>
      </app-overlay>
    }
  `,
})
class Host {
  readonly open = signal(true);
}

describe('Overlay', () => {
  async function render() {
    const fixture = TestBed.createComponent(Host);
    await fixture.whenStable();
    return fixture;
  }

  function overlay(fixture: { nativeElement: HTMLElement }) {
    return fixture.nativeElement.querySelector('app-overlay') as HTMLElement;
  }

  it('exposes a labelled modal dialog', async () => {
    const fixture = await render();
    const dialog = fixture.nativeElement.querySelector('[role="dialog"]') as HTMLElement;
    expect(dialog.getAttribute('aria-modal')).toBe('true');
    expect(dialog.getAttribute('aria-label')).toBe('Kanal erstellen');
  });

  it('locks background scrolling while open', async () => {
    const fixture = await render();
    expect(document.body.style.overflow).toBe('hidden');

    fixture.componentInstance.open.set(false);
    await fixture.whenStable();
    expect(document.body.style.overflow).not.toBe('hidden');
  });

  it('closes on escape', async () => {
    const fixture = await render();
    overlay(fixture).dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    await fixture.whenStable();

    expect(fixture.componentInstance.open()).toBe(false);
  });

  it('closes on a backdrop click but not on a panel click', async () => {
    const fixture = await render();
    const panel = fixture.nativeElement.querySelector('.panel') as HTMLElement;

    panel.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    await fixture.whenStable();
    expect(fixture.componentInstance.open()).toBe(true);

    overlay(fixture).dispatchEvent(new MouseEvent('click', { bubbles: true }));
    await fixture.whenStable();
    expect(fixture.componentInstance.open()).toBe(false);
  });

  it('moves focus into the dialog', async () => {
    const fixture = await render();
    const first = fixture.nativeElement.querySelector('[data-testid="first"]') as HTMLElement;
    expect(document.activeElement).toBe(first);
  });

  it('wraps tab from the last control back to the first', async () => {
    const fixture = await render();
    const first = fixture.nativeElement.querySelector('[data-testid="first"]') as HTMLElement;
    const last = fixture.nativeElement.querySelector('[data-testid="last"]') as HTMLElement;

    last.focus();
    overlay(fixture).dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true }));
    expect(document.activeElement).toBe(first);
  });

  it('wraps shift+tab from the first control to the last', async () => {
    const fixture = await render();
    const first = fixture.nativeElement.querySelector('[data-testid="first"]') as HTMLElement;
    const last = fixture.nativeElement.querySelector('[data-testid="last"]') as HTMLElement;

    first.focus();
    overlay(fixture).dispatchEvent(
      new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true }),
    );
    expect(document.activeElement).toBe(last);
  });
});
