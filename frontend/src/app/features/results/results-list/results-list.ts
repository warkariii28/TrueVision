import { Component, inject, signal } from '@angular/core';
import { DatePipe, NgFor, NgIf } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ResultItem, ResultsService } from '../../../core/services/results.service';

type ResultFilter = 'All' | 'Fake' | 'Real';
type ResultSort = 'newest' | 'confidence-desc' | 'confidence-asc';

@Component({
  selector: 'app-results-list',
  imports: [DatePipe, NgFor, NgIf, RouterLink],
  templateUrl: './results-list.html',
  styleUrl: './results-list.css',
  host: { class: 'tv-page-results' },
})
export class ResultsList {
  private readonly resultsService = inject(ResultsService);

  readonly results = signal<ResultItem[]>([]);
  readonly isLoading = signal(true);
  readonly errorMessage = signal('');
  readonly filterMode = signal<ResultFilter>('All');
  readonly sortMode = signal<ResultSort>('newest');

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

  updateFilter(value: string): void {
    this.filterMode.set((['All', 'Fake', 'Real'].includes(value) ? value : 'All') as ResultFilter);
  }

  updateSort(value: string): void {
    this.sortMode.set((['newest', 'confidence-desc', 'confidence-asc'].includes(value) ? value : 'newest') as ResultSort);
  }

  get visibleResults(): ResultItem[] {
    const filter = this.filterMode();
    const filtered = this.results().filter((result) => filter === 'All' || result.prediction === filter);

    return [...filtered].sort((left, right) => {
      if (this.sortMode() === 'confidence-desc') {
        return right.confidence - left.confidence;
      }

      if (this.sortMode() === 'confidence-asc') {
        return left.confidence - right.confidence;
      }

      return new Date(right.createdAt ?? 0).getTime() - new Date(left.createdAt ?? 0).getTime();
    });
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