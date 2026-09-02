import { DOCUMENT } from '@angular/common';
import { Injectable, inject, signal } from '@angular/core';

export type ThemeMode = 'dark' | 'light';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  private readonly storageKey = 'truevision-theme';
  readonly mode = signal<ThemeMode>(this.readInitialMode());

  constructor() {
    this.applyMode(this.mode());
  }

  isDark(): boolean {
    return this.mode() === 'dark';
  }

  toggleMode(): void {
    this.setMode(this.isDark() ? 'light' : 'dark');
  }

  setMode(mode: ThemeMode): void {
    this.mode.set(mode);
    this.applyMode(mode);

    if (typeof localStorage === 'undefined') {
      return;
    }

    try {
      localStorage.setItem(this.storageKey, mode);
    } catch {
      // Storage can be unavailable in private or restricted browser contexts.
    }
  }

  private readInitialMode(): ThemeMode {
    if (typeof localStorage === 'undefined') {
      return 'dark';
    }

    try {
      const savedMode = localStorage.getItem(this.storageKey);
      return savedMode === 'light' || savedMode === 'dark' ? savedMode : 'dark';
    } catch {
      return 'dark';
    }
  }

  private applyMode(mode: ThemeMode): void {
    const body = this.document.body;
    body.classList.toggle('tv-theme-dark', mode === 'dark');
    body.classList.toggle('tv-theme-light', mode === 'light');
    body.setAttribute('data-theme', mode);
  }
}