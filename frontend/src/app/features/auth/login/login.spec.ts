import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { Login } from './login';
import { AuthService } from '../../../core/services/auth.service';

describe('Login', () => {
  let component: Login;
  let fixture: ComponentFixture<Login>;
  let authServiceMock: {
    login: ReturnType<typeof vi.fn>;
  };
  let router: Router;

  beforeEach(async () => {
    authServiceMock = {
      login: vi.fn(() =>
        of({
          user: { id: 1, username: 'demo', email: 'demo@test.com' },
        }),
      ),
    };

    await TestBed.configureTestingModule({
      imports: [Login],
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

    fixture = TestBed.createComponent(Login);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show an error when email and password are empty', () => {
    component.email = '';
    component.password = '';

    component.onSubmit();

    expect(component.errorMessage()).toBe('Email and password are required.');
    expect(authServiceMock.login).not.toHaveBeenCalled();
  });

  it('should call AuthService.login with trimmed email and navigate to /upload by default', () => {
    const navigateByUrlSpy = vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);

    component.email = '  demo@test.com  ';
    component.password = 'secret123';

    component.onSubmit();

    expect(authServiceMock.login).toHaveBeenCalledWith({
      email: 'demo@test.com',
      password: 'secret123',
    });
    expect(navigateByUrlSpy).toHaveBeenCalledWith('/upload');
    expect(component.errorMessage()).toBe('');
    expect(component.isSubmitting()).toBe(false);
  });

  it('should navigate to returnUrl after successful login when provided', async () => {
    await TestBed.resetTestingModule();

    authServiceMock = {
      login: vi.fn(() =>
        of({
          user: { id: 1, username: 'demo', email: 'demo@test.com' },
        }),
      ),
    };

    await TestBed.configureTestingModule({
      imports: [Login],
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

    fixture = TestBed.createComponent(Login);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();

    const navigateByUrlSpy = vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);

    component.email = 'demo@test.com';
    component.password = 'secret123';

    component.onSubmit();

    expect(navigateByUrlSpy).toHaveBeenCalledWith('/results');
  });

  it('should show backend error message when login fails', () => {
    authServiceMock.login.mockReturnValue(
      throwError(() => ({
        error: { error: 'Invalid email or password' },
      })),
    );

    component.email = 'demo@test.com';
    component.password = 'wrongpass';

    component.onSubmit();

    expect(component.errorMessage()).toBe('Invalid email or password');
    expect(component.isSubmitting()).toBe(false);
  });
});
