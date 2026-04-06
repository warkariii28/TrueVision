import { Component, inject, signal } from '@angular/core';
import { NgFor, NgIf } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ResultItem, ResultsService } from '../../../core/services/results.service';
import { STATIC_BASE_URL } from '../../../core/config/api.config';


@Component({
  selector: 'app-results-list',
  imports: [NgFor, NgIf, RouterLink],
  templateUrl: './results-list.html',
  styleUrl: './results-list.css',
})
export class ResultsList {
  private readonly resultsService = inject(ResultsService);

  readonly results = signal<ResultItem[]>([]);
  readonly isLoading = signal(true);
  readonly errorMessage = signal('');
  private readonly backendBase = `${STATIC_BASE_URL}/`;
;

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

  imageUrl(path: string): string {
    return `${this.backendBase}${path}`;
  }

  gradcamUrl(path: string | null): string {
    return path ? `${this.backendBase}${path}` : '';
  }
}
