import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { Register } from './register';
import { AuthService } from '../../../core/services/auth.service';

describe('Register', () => {
  let component: Register;
  let fixture: ComponentFixture<Register>;
  let authServiceMock: {
    register: ReturnType<typeof vi.fn>;
  };
  let router: Router;

  beforeEach(async () => {
    authServiceMock = {
      register: vi.fn(() =>
        of({
          user: { id: 1, username: 'demo', email: 'demo@test.com' },
        }),
      ),
    };

    await TestBed.configureTestingModule({
      imports: [Register],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              queryParamMap: convertToParamMap({}),
            },
          },
        },
        {
          provide: AuthService,
          useValue: authServiceMock,
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Register);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show an error when any field is empty', () => {
    component.username = '';
    component.email = 'demo@test.com';
    component.password = 'secret123';
    component.confirmPassword = 'secret123';

    component.onSubmit();

    expect(component.errorMessage()).toBe('All fields are required.');
    expect(authServiceMock.register).not.toHaveBeenCalled();
  });

  it('should show an error when passwords do not match', () => {
    component.username = 'demo';
    component.email = 'demo@test.com';
    component.password = 'secret123';
    component.confirmPassword = 'different123';

    component.onSubmit();

    expect(component.errorMessage()).toBe('Passwords do not match.');
    expect(authServiceMock.register).not.toHaveBeenCalled();
  });

  it('should call AuthService.register with trimmed values and navigate to /upload by default', () => {
    const navigateByUrlSpy = vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);

    component.username = '  demo  ';
    component.email = '  demo@test.com  ';
    component.password = 'secret123';
    component.confirmPassword = 'secret123';

    component.onSubmit();

    expect(authServiceMock.register).toHaveBeenCalledWith({
      username: 'demo',
      email: 'demo@test.com',
      password: 'secret123',
      confirmPassword: 'secret123',
    });
    expect(navigateByUrlSpy).toHaveBeenCalledWith('/upload');
    expect(component.errorMessage()).toBe('');
    expect(component.isSubmitting()).toBe(false);
  });

  it('should navigate to returnUrl after successful registration when provided', async () => {
    await TestBed.resetTestingModule();

    authServiceMock = {
      register: vi.fn(() =>
        of({
          user: { id: 1, username: 'demo', email: 'demo@test.com' },
        }),
      ),
    };

    await TestBed.configureTestingModule({
      imports: [Register],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              queryParamMap: convertToParamMap({ returnUrl: '/results' }),
            },
          },
        },
        {
          provide: AuthService,
          useValue: authServiceMock,
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Register);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();

    const navigateByUrlSpy = vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);

    component.username = 'demo';
    component.email = 'demo@test.com';
    component.password = 'secret123';
    component.confirmPassword = 'secret123';

    component.onSubmit();

    expect(navigateByUrlSpy).toHaveBeenCalledWith('/results');
  });

  it('should show backend error message when registration fails', () => {
    authServiceMock.register.mockReturnValue(
      throwError(() => ({
        error: { error: 'User already exists! Please use a different email or username.' },
      })),
    );

    component.username = 'demo';
    component.email = 'demo@test.com';
    component.password = 'secret123';
    component.confirmPassword = 'secret123';

    component.onSubmit();

    expect(component.errorMessage()).toBe(
      'User already exists! Please use a different email or username.',
    );
    expect(component.isSubmitting()).toBe(false);
  });
});
