import { Component, inject, signal } from '@angular/core';
import { CommonModule, NgFor, DecimalPipe } from '@angular/common';
import {
  PerformanceModel,
  PerformanceResponse,
  ResultsService,
} from '../../core/services/results.service';

@Component({
  selector: 'app-performance',
  imports: [NgFor, CommonModule, DecimalPipe],
  templateUrl: './performance.html',
  styleUrl: './performance.css',
})
export class Performance {
  private readonly resultsService = inject(ResultsService);

  readonly isLoading = signal(true);
  readonly errorMessage = signal('');
  readonly bestModel = signal<PerformanceResponse['bestModel'] | null>(null);
  readonly modelRows = signal<PerformanceModel[]>([]);

  constructor() {
    this.resultsService.getPerformance().subscribe({
      next: (response) => {
        this.bestModel.set(response.bestModel);
        this.modelRows.set(response.models);
        this.isLoading.set(false);
      },
      error: (error) => {
        this.errorMessage.set(
          error?.error?.error === 'No performance data available.'
            ? 'No model report data has been added yet.'
            : error?.error?.error || 'Failed to load performance data.',
        );
        this.isLoading.set(false);
      },
    });
  }
}
