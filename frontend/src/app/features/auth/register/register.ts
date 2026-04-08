import { Component, inject, signal } from '@angular/core';
import { NgIf } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-register',
  imports: [FormsModule, RouterLink, NgIf],
  templateUrl: './register.html',
  styleUrl: './register.css',
  host: { class: 'tv-page-auth' },
})
export class Register {
  username = '';
  email = '';
  password = '';
  confirmPassword = '';

  readonly errorMessage = signal('');
  readonly isSubmitting = signal(false);

  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  onSubmit(): void {
    this.errorMessage.set('');

    if (
      !this.username.trim() ||
      !this.email.trim() ||
      !this.password.trim() ||
      !this.confirmPassword.trim()
    ) {
      this.errorMessage.set('All fields are required.');
      return;
    }

    if (this.password !== this.confirmPassword) {
      this.errorMessage.set('Passwords do not match.');
      return;
    }

    this.isSubmitting.set(true);

    this.authService.register({
      username: this.username.trim(),
      email: this.email.trim(),
      password: this.password,
      confirmPassword: this.confirmPassword,
    }).subscribe({
      next: () => {
        this.isSubmitting.set(false);

        const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl');
        this.router.navigateByUrl(returnUrl || '/upload');
      },
      error: (error) => {
        this.isSubmitting.set(false);
        this.errorMessage.set(
          error?.error?.error || 'Registration failed. Please try again.'
        );
      }
    });
  }
}
