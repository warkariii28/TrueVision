import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  QueryList,
  ViewChildren,
  signal,
} from '@angular/core';
import { NgClass } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-home',
  imports: [RouterLink, NgClass],
  templateUrl: './home.html',
  styleUrl: './home.css',
  host: { class: 'tv-page-home' },
})
export class Home implements AfterViewInit, OnDestroy {
  @ViewChildren('revealBlock') revealBlocks!: QueryList<ElementRef<HTMLElement>>;

  readonly rotatingWords = ['manipulated', 'synthetic', 'deepfake', 'AI-generated'];
  readonly currentWord = signal(this.rotatingWords[0]);
  readonly wordState = signal<'is-entering' | 'is-exiting' | 'is-settled'>('is-settled');

  private wordIndex = 0;
  private rotationTimer: ReturnType<typeof setInterval> | null = null;
  private phaseTimer: ReturnType<typeof setTimeout> | null = null;

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.revealBlocks.forEach((block, index) => {
        setTimeout(() => {
          block.nativeElement.classList.add('is-visible');
        }, index * 120);
      });
    }, 100);

    this.startWordRotation();
  }

  ngOnDestroy(): void {
    if (this.rotationTimer) {
      clearInterval(this.rotationTimer);
    }

    if (this.phaseTimer) {
      clearTimeout(this.phaseTimer);
    }
  }

  private startWordRotation(): void {
    this.rotationTimer = setInterval(() => {
      this.wordState.set('is-exiting');

      this.phaseTimer = setTimeout(() => {
        this.wordIndex = (this.wordIndex + 1) % this.rotatingWords.length;
        this.currentWord.set(this.rotatingWords[this.wordIndex]);
        this.wordState.set('is-entering');

        this.phaseTimer = setTimeout(() => {
          this.wordState.set('is-settled');
        }, 260);
      }, 380);
    }, 3200);
  }
}
