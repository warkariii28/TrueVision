import { Component, inject, signal } from '@angular/core';
import { CommonModule, NgFor } from '@angular/common';
import {
  PerformanceModel,
  PerformanceResponse,
  ResultsService,
} from '../../core/services/results.service';

@Component({
  selector: 'app-performance',
  imports: [NgFor, CommonModule],
  templateUrl: './performance.html',
  styleUrl: './performance.css',
  host: { class: 'tv-page-performance' },
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

  get rankedModels(): PerformanceModel[] {
    return [...this.modelRows()].sort((left, right) => right.accuracy - left.accuracy);
  }

  get runnerUpModel(): PerformanceModel | null {
    return this.rankedModels[1] ?? null;
  }

  get bestModelDetails(): PerformanceModel | null {
    const best = this.bestModel();

    if (!best) {
      return null;
    }

    return this.modelRows().find((row) => row.modelName === best.modelName) ?? null;
  }

  get accuracyLead(): number | null {
    const best = this.bestModel();
    const runnerUp = this.runnerUpModel;

    if (!best || !runnerUp) {
      return null;
    }

    return best.accuracy - runnerUp.accuracy;
  }

  get leadingModelCount(): number {
    return this.rankedModels.length;
  }

  isBestModel(modelName: string): boolean {
    return this.bestModel()?.modelName === modelName;
  }

  rankFor(modelName: string): number {
    return this.rankedModels.findIndex((row) => row.modelName === modelName) + 1;
  }
}
