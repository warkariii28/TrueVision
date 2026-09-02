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
    return [...this.modelRows()].sort((left, right) => this.modelScore(right) - this.modelScore(left));
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

  get topModels(): PerformanceModel[] {
    return this.rankedModels.slice(0, 5);
  }

  get bestModelNameShort(): string {
    return this.bestModel()?.modelName.replace(/^Stage-\d\s+/, '') ?? '';
  }

  get totalTestCases(): number {
    const best = this.bestModel();

    if (!best) {
      return 0;
    }

    return best.tp + best.tn + best.fp + best.fn;
  }

  get correctDecisionRate(): number {
    const total = this.totalTestCases;

    if (!total) {
      return 0;
    }

    return this.correctDecisions / total;
  }

  get correctDecisions(): number {
    const best = this.bestModel();

    if (!best) {
      return 0;
    }

    return best.tp + best.tn;
  }

  get wrongDecisions(): number {
    const best = this.bestModel();

    if (!best) {
      return 0;
    }

    return best.fp + best.fn;
  }

  get falseAlertRate(): number {
    const best = this.bestModel();

    if (!best) {
      return 0;
    }

    const realImages = best.tn + best.fp;
    return realImages ? best.fp / realImages : 0;
  }

  get missedFakeRate(): number {
    const best = this.bestModel();

    if (!best) {
      return 0;
    }

    const fakeImages = best.tp + best.fn;
    return fakeImages ? best.fn / fakeImages : 0;
  }

  get riskTakeaway(): string {
    const best = this.bestModel();

    if (!best) {
      return 'Review the visual evidence before making a final decision.';
    }

    return best.fp > best.fn
      ? 'Most remaining mistakes are false alerts, so review fake labels carefully before rejecting an image.'
      : 'Most remaining mistakes are missed fakes, so review real labels carefully when the image is important.';
  }

  get riskSummary(): string {
    const details = this.bestModelDetails;

    if (!details) {
      return 'Risk details are unavailable until model rows load.';
    }

    if (details.fnr > details.fpr) {
      return 'This model is more likely to miss a fake than falsely accuse a real image.';
    }

    if (details.fpr > details.fnr) {
      return 'This model is more likely to flag a real image than miss a fake.';
    }

    return 'False alerts and missed fakes are balanced in this test set.';
  }

  modelScore(model: Pick<PerformanceModel, 'accuracy' | 'f1Score'>): number {
    return (model.accuracy * 0.65) + (model.f1Score * 0.35);
  }

  modelFamily(modelName: string): string {
    return modelName.replace(/^Stage-\d\s+/, '');
  }
  isBestModel(modelName: string): boolean {
    return this.bestModel()?.modelName === modelName;
  }

  rankFor(modelName: string): number {
    return this.rankedModels.findIndex((row) => row.modelName === modelName) + 1;
  }
}
