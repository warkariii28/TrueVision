import { Component, inject, signal } from '@angular/core';
import { NgIf } from '@angular/common';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-navbar',
  imports: [RouterLink, RouterLinkActive, NgIf],
  templateUrl: './navbar.html',
  styleUrl: './navbar.css',
})
export class Navbar {
  readonly authService = inject(AuthService);
  readonly isMenuOpen = signal(false);

  private readonly router = inject(Router);

  toggleMenu(): void {
    this.isMenuOpen.update((isOpen) => !isOpen);
  }

  closeMenu(): void {
    this.isMenuOpen.set(false);
  }

  logout(): void {
    this.authService.logout().subscribe({
      next: () => {
        this.closeMenu();
        this.router.navigate(['/']);
      },
      error: (error) => {
        console.error('Logout failed:', error);
      }
    });
  }
}
