import { Component, ElementRef, AfterViewInit, ViewChild } from '@angular/core';
import { animate } from 'motion/mini';

@Component({
  selector: 'app-infinite-path-loader',
  templateUrl: './infinite-path-loader.html',
  styleUrl: './infinite-path-loader.css',
})
export class InfinitePathLoader implements AfterViewInit {
  @ViewChild('loaderPath') private readonly path?: ElementRef<SVGPathElement>;
  @ViewChild('glowPath') private readonly glowPath?: ElementRef<SVGPathElement>;

  ngAfterViewInit(): void {
    const pathEl = this.path?.nativeElement;
    const glowEl = this.glowPath?.nativeElement;
    if (!pathEl || !glowEl) return;

    const length = pathEl.getTotalLength();
    const segmentLength = length * 0.3; // 30% of the path is a line

    // Setup both paths for "flowing segment" effect
    [pathEl, glowEl].forEach(el => {
      el.style.strokeDasharray = `${segmentLength} ${length - segmentLength}`;
      el.style.strokeDashoffset = `${length}`;
    });

    animate(
      pathEl,
      {
        strokeDashoffset: [length, 0],
      },
      {
        duration: 2,
        ease: 'linear',
        repeat: Infinity,
        onUpdate: (latest) => {
          // Sync the glow path with the main path's current offset
          if (glowEl) {
            glowEl.style.strokeDashoffset = `${latest.strokeDashoffset}px`;
          }
        },
      }
    );
  }
}