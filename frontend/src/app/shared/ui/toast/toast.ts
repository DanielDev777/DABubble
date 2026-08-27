import { computed, Injectable, signal } from '@angular/core';

export type ToastTone = 'info' | 'error';

export interface Toast {
  id: number;
  text: string;
  tone: ToastTone;
}

/** Transient confirmations — "E-Mail gesendet", "Konto erstellt". */
@Injectable({ providedIn: 'root' })
export class ToastService {
  private static readonly DEFAULT_DURATION = 4000;
  private nextId = 0;
  private readonly items = signal<Toast[]>([]);
  private readonly timers = new Map<number, ReturnType<typeof setTimeout>>();

  readonly toasts = this.items.asReadonly();
  readonly hasToasts = computed(() => this.items().length > 0);

  show(text: string, tone: ToastTone = 'info', duration = ToastService.DEFAULT_DURATION): number {
    const id = this.nextId++;
    this.items.update((toasts) => [...toasts, { id, text, tone }]);

    if (duration > 0) {
      this.timers.set(
        id,
        setTimeout(() => this.dismiss(id), duration),
      );
    }
    return id;
  }

  error(text: string, duration?: number): number {
    return this.show(text, 'error', duration);
  }

  dismiss(id: number): void {
    const timer = this.timers.get(id);
    if (timer !== undefined) {
      clearTimeout(timer);
      this.timers.delete(id);
    }
    this.items.update((toasts) => toasts.filter((toast) => toast.id !== id));
  }
}
