import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs/operators';

import { API_BASE_URL } from '../config/api.config';


export type AuthUser = {
  id: number;
  username: string;
  email: string;
};

export type AuthMeResponse = {
  authenticated: boolean;
  user: AuthUser | null;
  csrfToken: string | null;
};

export type AuthActionResponse = {
  message?: string;
  user?: AuthUser | null;
  csrfToken?: string | null;
  error?: string;
};

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private readonly apiBase = `${API_BASE_URL}/auth`;

  readonly user = signal<AuthUser | null>(null);
  readonly isAuthenticated = signal(false);
  readonly csrfToken = signal<string | null>(null);

  constructor(private http: HttpClient) {}

  me() {
    return this.http
      .get<AuthMeResponse>(`${this.apiBase}/me`, {
        withCredentials: true,
      })
      .pipe(
        tap((response) => {
          this.user.set(response.user);
          this.isAuthenticated.set(response.authenticated);
          this.csrfToken.set(response.csrfToken);
        })
      );
  }

  login(payload: { email: string; password: string }) {
    return this.http
      .post<AuthActionResponse>(`${this.apiBase}/login`, payload, {
        withCredentials: true,
      })
      .pipe(
        tap((response) => {
          this.user.set(response.user ?? null);
          this.isAuthenticated.set(!!response.user);
          this.csrfToken.set(response.csrfToken ?? null);
        })
      );
  }

  register(payload: {
    username: string;
    email: string;
    password: string;
    confirmPassword: string;
  }) {
    return this.http
      .post<AuthActionResponse>(`${this.apiBase}/register`, payload, {
        withCredentials: true,
      })
      .pipe(
        tap((response) => {
          this.user.set(response.user ?? null);
          this.isAuthenticated.set(!!response.user);
          this.csrfToken.set(response.csrfToken ?? null);
        })
      );
  }

  logout() {
    return this.http
      .post<AuthActionResponse>(
        `${this.apiBase}/logout`,
        {},
        {
          withCredentials: true,
        }
      )
      .pipe(
        tap(() => {
          this.user.set(null);
          this.isAuthenticated.set(false);
          this.csrfToken.set(null);
        })
      );
  }
}
