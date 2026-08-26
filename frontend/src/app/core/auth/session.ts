import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { finalize, Observable, share } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class SessionService {
  private readonly http = inject(HttpClient);
  private inFlight: Observable<void> | null = null;

  /**
   * Rotate the access token. Concurrent callers share one request: the backend
   * rotates and blacklists on every refresh, so parallel calls would invalidate
   * each other and log the user out.
   */
  refresh(): Observable<void> {
    this.inFlight ??= this.http.post<void>('/api/auth/refresh/', {}).pipe(
      finalize(() => (this.inFlight = null)),
      share(),
    );
    return this.inFlight;
  }
}
