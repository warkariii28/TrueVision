import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { Performance } from './performance';
import { ResultsService } from '../../core/services/results.service';

describe('Performance', () => {
  let component: Performance;
  let fixture: ComponentFixture<Performance>;
  let resultsServiceMock: {
    getPerformance: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    resultsServiceMock = {
      getPerformance: vi.fn(() =>
        of({
          bestModel: {
            id: 1,
            modelName: 'Swin',
            accuracy: 95.6,
            precision: 94.1,
            recall: 93.8,
            f1Score: 93.9,
            aucRoc: 97.2,
            prAuc: 96.4,
            tp: 100,
            tn: 95,
            fp: 5,
            fn: 7,
          },
          models: [],
        }),
      ),
    };

    await TestBed.configureTestingModule({
      imports: [Performance],
      providers: [
        {
          provide: ResultsService,
          useValue: resultsServiceMock,
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Performance);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load performance data', () => {
    expect(resultsServiceMock.getPerformance).toHaveBeenCalled();
    expect(component.bestModel()?.modelName).toBe('Swin');
    expect(component.modelRows()).toEqual([]);
    expect(component.isLoading()).toBe(false);
  });

  it('should show friendly message when no performance data exists', async () => {
    resultsServiceMock.getPerformance.mockReturnValue(
      throwError(() => ({
        error: { error: 'No performance data available.' },
      })),
    );

    fixture = TestBed.createComponent(Performance);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();

    expect(component.errorMessage()).toBe('No model report data has been added yet.');
    expect(component.isLoading()).toBe(false);
  });
});
