import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { FormControl, ReactiveFormsModule } from '@angular/forms';

import { TextField } from './text-field';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TextField, ReactiveFormsModule],
  template: `
    <app-text-field
      [formControl]="control"
      label="E-Mail"
      placeholder="beispielname@email.com"
      type="email"
      [error]="error()"
    />
  `,
})
class Host {
  readonly control = new FormControl('');
  readonly error = signal<string | null>(null);
}

describe('TextField', () => {
  async function render() {
    const fixture = TestBed.createComponent(Host);
    await fixture.whenStable();
    return fixture;
  }

  function input(fixture: { nativeElement: HTMLElement }) {
    return fixture.nativeElement.querySelector('input') as HTMLInputElement;
  }

  it('renders label, placeholder and type', async () => {
    const fixture = await render();
    expect(fixture.nativeElement.querySelector('label')?.textContent).toContain('E-Mail');
    expect(input(fixture).placeholder).toBe('beispielname@email.com');
    expect(input(fixture).type).toBe('email');
  });

  it('associates the label with the input', async () => {
    const fixture = await render();
    const label = fixture.nativeElement.querySelector('label') as HTMLLabelElement;
    expect(label.getAttribute('for')).toBe(input(fixture).id);
  });

  it('writes typed values back to the form control', async () => {
    const fixture = await render();
    const field = input(fixture);
    field.value = 'ada@example.com';
    field.dispatchEvent(new Event('input'));

    expect(fixture.componentInstance.control.value).toBe('ada@example.com');
  });

  it('shows a value pushed in from the form control', async () => {
    const fixture = await render();
    fixture.componentInstance.control.setValue('grace@example.com');
    await fixture.whenStable();

    expect(input(fixture).value).toBe('grace@example.com');
  });

  it('reflects a disabled control', async () => {
    const fixture = await render();
    fixture.componentInstance.control.disable();
    await fixture.whenStable();

    expect(input(fixture).disabled).toBe(true);
  });

  it('announces errors and links them to the input', async () => {
    const fixture = await render();
    fixture.componentInstance.error.set('Diese E-Mail-Adresse ist ungültig.');
    await fixture.whenStable();

    const error = fixture.nativeElement.querySelector('.error') as HTMLElement;
    expect(error.textContent).toContain('ungültig');
    expect(error.getAttribute('role')).toBe('alert');
    expect(input(fixture).getAttribute('aria-invalid')).toBe('true');
    expect(input(fixture).getAttribute('aria-describedby')).toBe(error.id);
  });
});
