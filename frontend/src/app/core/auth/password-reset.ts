import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

/**
 * The two ends of the emailed reset link. Deliberately not on AuthStore: these
 * calls run for a signed-out visitor and never touch the current user.
 */
@Injectable({ providedIn: 'root' })
export class PasswordResetService {
  private readonly http = inject(HttpClient);

  /**
   * Always answers 200 for a well-formed address, existing account or not —
   * the backend refuses to leak which emails are registered. Never tell the
   * caller whether the account exists.
   */
  request(email: string): Observable<void> {
    return this.http.post<void>('/api/auth/password-reset/', { email });
  }

  confirm(uid: string, token: string, password: string): Observable<void> {
    return this.http.post<void>('/api/auth/password-reset/confirm/', { uid, token, password });
  }
}
