import { HttpClient } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { catchError, firstValueFrom, map, Observable, of, tap } from 'rxjs';

import { User } from './user';

export interface SignupPayload {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  consent: boolean;
}

export interface ProfilePatch {
  full_name?: string;
  default_avatar?: string;
}

interface UserEnvelope {
  user: User;
}

@Injectable({ providedIn: 'root' })
export class AuthStore {
  private readonly http = inject(HttpClient);
  private readonly currentUser = signal<User | null>(null);

  readonly user = this.currentUser.asReadonly();
  readonly isAuthenticated = computed(() => this.currentUser() !== null);
  readonly isGuest = computed(() => this.currentUser()?.is_guest ?? false);

  login(email: string, password: string): Observable<User> {
    return this.enveloped('/api/auth/login/', { email, password });
  }

  signup(payload: SignupPayload): Observable<User> {
    return this.enveloped('/api/auth/signup/', payload);
  }

  loginAsGuest(): Observable<User> {
    return this.enveloped('/api/auth/guest/', {});
  }

  loginWithGoogle(idToken: string): Observable<User> {
    return this.enveloped('/api/auth/google/', { id_token: idToken });
  }

  /** PATCH /api/auth/me/ returns the user object directly, not an envelope. */
  updateProfile(patch: ProfilePatch): Observable<User> {
    return this.http
      .patch<User>('/api/auth/me/', patch)
      .pipe(tap((user) => this.currentUser.set(user)));
  }

  uploadAvatar(file: File): Observable<User> {
    const body = new FormData();
    body.append('avatar', file);
    // No Content-Type header: the browser must set the multipart boundary itself.
    return this.http
      .patch<User>('/api/auth/me/', body)
      .pipe(tap((user) => this.currentUser.set(user)));
  }

  logout(): Observable<void> {
    return this.http.post<void>('/api/auth/logout/', {}).pipe(
      // The session is over locally whether or not the server confirmed it.
      catchError(() => of(undefined)),
      tap(() => this.clear()),
      map(() => undefined),
    );
  }

  /**
   * Ask the backend who we are. The JWT cookies are httpOnly, so a page reload
   * cannot read them — restoring a session means asking. Resolves rather than
   * rejects when logged out, so app bootstrap never fails for a visitor.
   */
  restore(): Promise<void> {
    return firstValueFrom(
      // Any failure here means "start logged out" — a 401 because there is no
      // session, anything else because a visitor should still get an app.
      this.http.get<User>('/api/auth/me/').pipe(catchError(() => of(null))),
    ).then((user) => this.currentUser.set(user));
  }

  clear(): void {
    this.currentUser.set(null);
  }

  private enveloped(url: string, body: unknown): Observable<User> {
    return this.http.post<UserEnvelope>(url, body).pipe(
      map((response) => response.user),
      tap((user) => this.currentUser.set(user)),
    );
  }
}
