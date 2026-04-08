import { Component, inject, signal } from '@angular/core';
import { NgFor, NgIf } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ResultItem, ResultsService } from '../../../core/services/results.service';
import { ResultDetail } from '../result-detail/result-detail';

@Component({
  selector: 'app-results-list',
  imports: [NgFor, NgIf, RouterLink],
  templateUrl: './results-list.html',
  styleUrl: './results-list.css',
  host: { class: 'tv-page-results' },
})
export class ResultsList {
  private readonly resultsService = inject(ResultsService);

  readonly results = signal<ResultItem[]>([]);
  readonly isLoading = signal(true);
  readonly errorMessage = signal('');

  constructor() {
    this.resultsService.getResults().subscribe({
      next: (response) => {
        this.results.set(response.results);
        this.isLoading.set(false);
      },
      error: (error) => {
        this.errorMessage.set(
          error?.error?.error || 'Failed to load saved results.'
        );
        this.isLoading.set(false);
      }
    });
  }

  imageUrl(result: ResultItem): string {
    return this.resultsService.resultImageUrl(result);
  }

  gradcamUrl(result: ResultItem): string {
    return this.resultsService.resultGradcamUrl(result);
  }

  get totalResults(): number {
    return this.results().length;
  }

  get fakeCount(): number {
    return this.results().filter((result) => result.prediction === 'Fake').length;
  }

  get realCount(): number {
    return this.results().filter((result) => result.prediction === 'Real').length;
  }

  get feedbackCount(): number {
    return this.results().filter((result) => !!result.feedback).length;
  }
}
