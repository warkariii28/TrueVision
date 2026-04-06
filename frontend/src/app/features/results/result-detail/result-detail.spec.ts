import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ResultDetail } from './result-detail';

describe('ResultDetail', () => {
  let component: ResultDetail;
  let fixture: ComponentFixture<ResultDetail>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ResultDetail],
    }).compileComponents();

    fixture = TestBed.createComponent(ResultDetail);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
