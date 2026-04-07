import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter, Router } from '@angular/router';
import { of } from 'rxjs';

import { ResultDetail } from './result-detail';
import { ResultsService } from '../../../core/services/results.service';

describe('ResultDetail', () => {
  let component: ResultDetail;
  let fixture: ComponentFixture<ResultDetail>;
  let resultsServiceMock: {
    getResultById: ReturnType<typeof vi.fn>;
    submitFeedback: ReturnType<typeof vi.fn>;
  };
  let router: Router;

  const mockResult = {
    id: 1,
    saved: true,
    prediction: 'Fake' as const,
    confidence: 92.3,
    feedback: null,
    imagePath: 'uploads/demo.jpg',
    gradcamPath: 'gradcam/demo_gradcam.jpg',
    explanation: 'Test explanation',
    recommendation: 'Test recommendation',
    createdAt: '2026-04-07T10:00:00',
    inferenceTime: 1.2,
  };

  beforeEach(async () => {
    sessionStorage.clear();

    resultsServiceMock = {
      getResultById: vi.fn(() => of({ result: mockResult })),
      submitFeedback: vi.fn(() =>
        of({
          message: 'Feedback saved successfully',
          result: { ...mockResult, feedback: 'Fake' },
        }),
      ),
    };

    await TestBed.configureTestingModule({
      imports: [ResultDetail],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: convertToParamMap({ id: '1' }),
            },
          },
        },
        {
          provide: ResultsService,
          useValue: resultsServiceMock,
        },
      ],
    }).compileComponents();

    router = TestBed.inject(Router);
  });

  afterEach(() => {
    sessionStorage.clear();
  });

  it('should create', () => {
    fixture = TestBed.createComponent(ResultDetail);
    component = fixture.componentInstance;
    fixture.detectChanges();

    expect(component).toBeTruthy();
  });

  it('should load a saved result by route id', () => {
    fixture = TestBed.createComponent(ResultDetail);
    component = fixture.componentInstance;
    fixture.detectChanges();

    expect(resultsServiceMock.getResultById).toHaveBeenCalledWith(1);
    expect(component.result()).toEqual(mockResult);
    expect(component.isLoading()).toBe(false);
  });

  it('should use session storage preview on /result-preview', () => {
    sessionStorage.setItem('guestPreviewResult', JSON.stringify({
      ...mockResult,
      id: null,
      saved: false,
    }));

    vi.spyOn(router, 'url', 'get').mockReturnValue('/result-preview');

    fixture = TestBed.createComponent(ResultDetail);
    component = fixture.componentInstance;
    fixture.detectChanges();

    expect(resultsServiceMock.getResultById).not.toHaveBeenCalled();
    expect(component.result()?.saved).toBe(false);
    expect(component.isGuestPreview).toBe(true);
    expect(component.isLoading()).toBe(false);
  });

  it('should submit feedback for a saved result', () => {
    fixture = TestBed.createComponent(ResultDetail);
    component = fixture.componentInstance;
    fixture.detectChanges();

    component.submitFeedback('Satisfied');

    expect(resultsServiceMock.submitFeedback).toHaveBeenCalledWith(1, 'Satisfied');
    expect(component.successMessage()).toBe('Feedback saved successfully');
    expect(component.isSubmittingFeedback()).toBe(false);
  });
});
