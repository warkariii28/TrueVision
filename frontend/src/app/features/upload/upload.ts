import { Component, ElementRef, ViewChild, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { NgClass, NgIf } from '@angular/common';
import { ResultsService } from '../../core/services/results.service';

@Component({
  selector: 'app-upload',
  imports: [RouterLink, NgIf, NgClass],
  templateUrl: './upload.html',
  styleUrl: './upload.css',
})
export class Upload {
  @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;

  readonly previewUrl = signal('');
  readonly errorMessage = signal('');
  readonly showProgress = signal(false);
  readonly progress = signal(0);
  readonly progressClass = signal('');
  readonly isSubmitting = signal(false);
  readonly statusMessage = signal('');
  readonly selectedFileName = signal('');

  isDragging = false;
  selectedFile: File | null = null;

  private progressTimer: ReturnType<typeof setInterval> | null = null;

  private readonly resultsService = inject(ResultsService);
  private readonly router = inject(Router);

  openFilePicker(): void {
    if (this.isSubmitting()) {
      return;
    }

    this.fileInput.nativeElement.click();
  }

  onKeydown(event: KeyboardEvent): void {
    if (this.isSubmitting()) {
      return;
    }

    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      this.openFilePicker();
    }
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    if (file) {
      this.processFile(file);
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    if (!this.isSubmitting()) {
      this.isDragging = true;
    }
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = false;

    if (this.isSubmitting()) {
      return;
    }

    const file = event.dataTransfer?.files?.[0];
    if (file) {
      this.processFile(file);
    }
  }

  startFakeProgress(): void {
    this.stopFakeProgress();
    this.progress.set(12);
    this.progressClass.set('low');
    this.statusMessage.set('Uploading and analyzing image...');
    this.showProgress.set(true);

    this.progressTimer = setInterval(() => {
      const current = this.progress();

      if (current < 35) {
        this.progress.set(current + 8);
        this.progressClass.set('low');
      } else if (current < 70) {
        this.progress.set(current + 5);
        this.progressClass.set('mid');
      } else if (current < 90) {
        this.progress.set(current + 2);
        this.progressClass.set('high');
      }
    }, 400);
  }

  stopFakeProgress(): void {
    if (this.progressTimer) {
      clearInterval(this.progressTimer);
      this.progressTimer = null;
    }
  }

  processFile(file: File): void {
    this.errorMessage.set('');
    this.showProgress.set(false);
    this.progress.set(0);
    this.progressClass.set('');
    this.statusMessage.set('');

    if (!this.validateFile(file)) {
      this.previewUrl.set('');
      this.selectedFileName.set('');
      this.selectedFile = null;
      return;
    }

    this.selectedFile = file;
    this.selectedFileName.set(file.name);

    const reader = new FileReader();
    reader.onload = () => {
      this.previewUrl.set(reader.result as string);
    };
    reader.readAsDataURL(file);
  }

  validateFile(file: File): boolean {
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg'];

    if (!allowedTypes.includes(file.type)) {
      this.errorMessage.set('Only PNG, JPG, and JPEG images are allowed.');
      return false;
    }

    if (file.size > 5 * 1024 * 1024) {
      this.errorMessage.set('File size exceeds 5 MB. Please upload a smaller image.');
      return false;
    }

    this.errorMessage.set('');
    return true;
  }

  onSubmit(event: Event): void {
    event.preventDefault();

    if (!this.selectedFile || this.isSubmitting()) {
      if (!this.selectedFile) {
        this.errorMessage.set('Please choose an image before continuing.');
      }
      return;
    }

    this.errorMessage.set('');
    this.isSubmitting.set(true);
    this.startFakeProgress();
    sessionStorage.removeItem('guestPreviewResult');

    this.resultsService.uploadImage(this.selectedFile).subscribe({
      next: (response) => {
        this.stopFakeProgress();
        this.progress.set(100);
        this.progressClass.set('high');
        this.statusMessage.set('Analysis complete. Opening result...');
        this.isSubmitting.set(false);

        setTimeout(() => {
          if (response.result.id) {
            this.router.navigate(['/results', response.result.id]);
            return;
          }

          this.router.navigate(['/result-preview'], {
            state: { result: response.result },
          });
        }, 300);
      },
      error: (error) => {
        this.stopFakeProgress();
        this.isSubmitting.set(false);
        this.showProgress.set(false);
        this.progress.set(0);
        this.progressClass.set('');
        this.statusMessage.set('');
        this.errorMessage.set(
          error?.error?.error === 'Uploaded image did not meet quality standards.'
            ? 'This image could not be checked clearly. Try a brighter, sharper face image facing the camera.'
            : error?.error?.error || 'Upload failed. Please try again.',
        );
      },
    });
  }
}
