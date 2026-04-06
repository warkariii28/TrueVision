import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ResultsList } from './results-list';

describe('ResultsList', () => {
  let component: ResultsList;
  let fixture: ComponentFixture<ResultsList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ResultsList],
    }).compileComponents();

    fixture = TestBed.createComponent(ResultsList);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
