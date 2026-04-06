import { Component, inject } from '@angular/core';
import { NgIf } from '@angular/common';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-navbar',
  imports: [RouterLink, RouterLinkActive, NgIf],
  templateUrl: './navbar.html',
  styleUrl: './navbar.css'
})
export class Navbar {
  readonly authService = inject(AuthService);

  private readonly router = inject(Router);

  logout(): void {
  console.log('Logout clicked');

  this.authService.logout().subscribe({
    next: () => {
      console.log('Logout success');
      this.router.navigate(['/']);
    },
    error: (error) => {
      console.error('Logout failed:', error);
    }
  });
}
}
