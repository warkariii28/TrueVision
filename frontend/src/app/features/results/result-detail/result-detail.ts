import { Component, inject, signal } from '@angular/core';
import { NgClass, NgIf } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ResultItem, ResultsService } from '../../../core/services/results.service';
import { STATIC_BASE_URL } from '../../../core/config/api.config';

@Component({
  selector: 'app-result-detail',
  imports: [NgClass, NgIf, RouterLink],
  templateUrl: './result-detail.html',
  styleUrl: './result-detail.css',
})
export class ResultDetail {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly resultsService = inject(ResultsService);
  private readonly backendBase = `${STATIC_BASE_URL}/`;

  readonly result = signal<ResultItem | null>(null);
  readonly errorMessage = signal('');
  readonly successMessage = signal('');
  readonly isLoading = signal(true);
  readonly isSubmittingFeedback = signal(false);

  constructor() {
    const navigation = this.router.getCurrentNavigation();
    const previewResult = navigation?.extras.state?.['result'] as ResultItem | undefined;
    const storedPreview = sessionStorage.getItem('guestPreviewResult');
    const storedResult = storedPreview ? (JSON.parse(storedPreview) as ResultItem) : null;
    const id = Number(this.route.snapshot.paramMap.get('id'));

    if (previewResult) {
      sessionStorage.setItem('guestPreviewResult', JSON.stringify(previewResult));
      this.result.set(previewResult);
      this.isLoading.set(false);
      return;
    }

    if (this.router.url === '/result-preview' && storedResult) {
      this.result.set(storedResult);
      this.isLoading.set(false);
      return;
    }

    if (!id) {
      this.errorMessage.set('No preview result found. Please upload an image again.');
      this.isLoading.set(false);
      return;
    }

    this.resultsService.getResultById(id).subscribe({
      next: (response) => {
        sessionStorage.removeItem('guestPreviewResult');
        this.result.set(response.result);
        this.isLoading.set(false);
      },
      error: (error) => {
        this.errorMessage.set(error?.error?.error || 'Failed to load result details.');
        this.isLoading.set(false);
      },
    });
  }

  get confidenceWidth(): string {
    return `${this.result()?.confidence ?? 0}%`;
  }

  get imageUrl(): string {
    const imagePath = this.result()?.imagePath;
    return imagePath ? `${this.backendBase}${imagePath}` : '';
  }

  get gradcamUrl(): string {
    const gradcamPath = this.result()?.gradcamPath;
    return gradcamPath ? `${this.backendBase}${gradcamPath}` : '';
  }

  get isGuestPreview(): boolean {
    return !this.result()?.id;
  }

  submitFeedback(feedback: 'Satisfied' | 'Unsatisfied'): void {
    const currentResult = this.result();

    if (!currentResult || !currentResult.id) {
      return;
    }

    this.errorMessage.set('');
    this.successMessage.set('');
    this.isSubmittingFeedback.set(true);

    this.resultsService.submitFeedback(currentResult.id, feedback).subscribe({
      next: (response) => {
        this.result.set(response.result);
        this.successMessage.set(response.message);
        this.isSubmittingFeedback.set(false);
      },
      error: (error) => {
        this.errorMessage.set(error?.error?.error || 'Failed to save feedback.');
        this.isSubmittingFeedback.set(false);
      },
    });
  }
}
