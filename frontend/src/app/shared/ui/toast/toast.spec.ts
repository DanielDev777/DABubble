import { TestBed } from '@angular/core/testing';

import { ToastHost } from './toast-host';
import { ToastService } from './toast';

describe('ToastService', () => {
  let toasts: ToastService;

  beforeEach(() => {
    vi.useFakeTimers();
    TestBed.configureTestingModule({});
    toasts = TestBed.inject(ToastService);
  });

  afterEach(() => vi.useRealTimers());

  it('starts empty', () => {
    expect(toasts.toasts()).toEqual([]);
    expect(toasts.hasToasts()).toBe(false);
  });

  it('queues messages in order', () => {
    toasts.show('E-Mail gesendet');
    toasts.error('Etwas ist schiefgelaufen');

    expect(toasts.toasts().map((toast) => toast.text)).toEqual([
      'E-Mail gesendet',
      'Etwas ist schiefgelaufen',
    ]);
    expect(toasts.toasts()[1].tone).toBe('error');
  });

  it('dismisses itself after the timeout', () => {
    toasts.show('E-Mail gesendet', 'info', 1000);
    expect(toasts.hasToasts()).toBe(true);

    vi.advanceTimersByTime(1000);
    expect(toasts.hasToasts()).toBe(false);
  });

  it('keeps a toast with no timeout until dismissed', () => {
    const id = toasts.show('Bleibt', 'info', 0);
    vi.advanceTimersByTime(60_000);
    expect(toasts.hasToasts()).toBe(true);

    toasts.dismiss(id);
    expect(toasts.hasToasts()).toBe(false);
  });

  it('dismisses only the requested toast', () => {
    const first = toasts.show('Erste');
    toasts.show('Zweite');

    toasts.dismiss(first);
    expect(toasts.toasts().map((toast) => toast.text)).toEqual(['Zweite']);
  });
});

describe('ToastHost', () => {
  it('renders queued toasts politely and dismisses on click', async () => {
    TestBed.configureTestingModule({});
    const toasts = TestBed.inject(ToastService);
    toasts.show('E-Mail gesendet', 'info', 0);

    const fixture = TestBed.createComponent(ToastHost);
    await fixture.whenStable();

    const host = fixture.nativeElement as HTMLElement;
    expect(host.getAttribute('aria-live')).toBe('polite');
    expect(host.textContent).toContain('E-Mail gesendet');

    (host.querySelector('button') as HTMLButtonElement).click();
    await fixture.whenStable();
    expect(toasts.hasToasts()).toBe(false);
  });
});
