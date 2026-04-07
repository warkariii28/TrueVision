import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { Upload } from './upload';
import { ResultsService } from '../../core/services/results.service';

describe('Upload', () => {
  let component: Upload;
  let fixture: ComponentFixture<Upload>;
  let resultsServiceMock: {
    uploadImage: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    resultsServiceMock = {
      uploadImage: vi.fn(() =>
        of({
          message: 'Upload processed successfully',
          result: {
            id: 1,
            saved: true,
            prediction: 'Fake',
            confidence: 91.2,
            feedback: null,
            imagePath: 'uploads/demo.jpg',
            gradcamPath: 'gradcam/demo_gradcam.jpg',
            explanation: 'Test explanation',
            recommendation: 'Test recommendation',
            createdAt: '2026-04-07T10:00:00',
            inferenceTime: 1.1,
          },
        }),
      ),
    };

    await TestBed.configureTestingModule({
      imports: [Upload],
      providers: [
        provideRouter([]),
        {
          provide: ResultsService,
          useValue: resultsServiceMock,
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Upload);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should reject unsupported file types', () => {
    const file = new File(['test'], 'demo.gif', { type: 'image/gif' });

    const isValid = component.validateFile(file);

    expect(isValid).toBe(false);
    expect(component.errorMessage()).toBe('Only PNG, JPG, and JPEG images are allowed.');
  });

  it('should reject files larger than 5 MB', () => {
    const file = new File(['test'], 'large.jpg', { type: 'image/jpeg' });
    Object.defineProperty(file, 'size', { value: 6 * 1024 * 1024 });

    const isValid = component.validateFile(file);

    expect(isValid).toBe(false);
    expect(component.errorMessage()).toBe('File size exceeds 5 MB. Please upload a smaller image.');
  });

  it('should accept valid image files', () => {
    const file = new File(['test'], 'demo.jpg', { type: 'image/jpeg' });
    Object.defineProperty(file, 'size', { value: 1024 });

    const isValid = component.validateFile(file);

    expect(isValid).toBe(true);
    expect(component.errorMessage()).toBe('');
  });

  it('should show an error if submit is attempted without selecting a file', () => {
    const event = new Event('submit');

    component.onSubmit(event);

    expect(component.errorMessage()).toBe('Please choose an image before continuing.');
    expect(resultsServiceMock.uploadImage).not.toHaveBeenCalled();
  });
});
