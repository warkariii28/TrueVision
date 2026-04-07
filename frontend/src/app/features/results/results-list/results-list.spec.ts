import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

import { ResultsList } from './results-list';
import { ResultsService } from '../../../core/services/results.service';

describe('ResultsList', () => {
  let component: ResultsList;
  let fixture: ComponentFixture<ResultsList>;
  let resultsServiceMock: {
    getResults: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    resultsServiceMock = {
      getResults: vi.fn(() =>
        of({
          results: [],
        }),
      ),
    };

    await TestBed.configureTestingModule({
      imports: [ResultsList],
      providers: [
        provideRouter([]),
        {
          provide: ResultsService,
          useValue: resultsServiceMock,
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ResultsList);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load saved results', () => {
    expect(resultsServiceMock.getResults).toHaveBeenCalled();
    expect(component.results()).toEqual([]);
    expect(component.isLoading()).toBe(false);
  });

  it('should show an error message if loading results fails', async () => {
    resultsServiceMock.getResults.mockReturnValue(
      throwError(() => ({
        error: { error: 'Failed to load saved results.' },
      })),
    );

    fixture = TestBed.createComponent(ResultsList);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();

    expect(component.errorMessage()).toBe('Failed to load saved results.');
    expect(component.isLoading()).toBe(false);
  });
});
