import { Component, inject, signal } from '@angular/core';
import { NgClass, NgIf } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ResultItem, ResultsService } from '../../../core/services/results.service';

@Component({
  selector: 'app-result-detail',
  imports: [NgClass, NgIf, RouterLink],
  templateUrl: './result-detail.html',
  styleUrl: './result-detail.css',
  host: { class: 'tv-page-result' },
})
export class ResultDetail {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly resultsService = inject(ResultsService);

  readonly result = signal<ResultItem | null>(null);
  readonly errorMessage = signal('');
  readonly successMessage = signal('');
  readonly isLoading = signal(true);
  readonly isSubmittingFeedback = signal(false);

  constructor() {
    const navigation = this.router.getCurrentNavigation();
    const previewResult = navigation?.extras.state?.['result'] as ResultItem | undefined;
    const storedPreview = sessionStorage.getItem('guestPreviewResult');
    const storedResult = storedPreview ? (JSON.parse(storedPreview) as ResultItem) : null;
    const id = Number(this.route.snapshot.paramMap.get('id'));

    if (previewResult) {
      sessionStorage.setItem('guestPreviewResult', JSON.stringify(previewResult));
      this.result.set(previewResult);
      this.isLoading.set(false);
      return;
    }

    if (this.router.url === '/result-preview' && storedResult) {
      this.result.set(storedResult);
      this.isLoading.set(false);
      return;
    }

    if (!id) {
      this.errorMessage.set('No preview result found. Please upload an image again.');
      this.isLoading.set(false);
      return;
    }

    this.resultsService.getResultById(id).subscribe({
      next: (response) => {
        sessionStorage.removeItem('guestPreviewResult');
        this.result.set(response.result);
        this.isLoading.set(false);
      },
      error: (error) => {
        this.errorMessage.set(error?.error?.error || 'Failed to load result details.');
        this.isLoading.set(false);
      },
    });
  }

  get confidenceWidth(): string {
    return `${this.result()?.confidence ?? 0}%`;
  }

  get imageUrl(): string {
    const result = this.result();
    return result ? this.resultsService.resultImageUrl(result) : '';
  }

  get gradcamUrl(): string {
    const result = this.result();
    if (!result || (result.saved && !result.gradcamPath)) {
      return '';
    }
    return this.resultsService.resultGradcamUrl(result);
  }

  get isGuestPreview(): boolean {
    return !this.result()?.id;
  }

  async downloadReport(): Promise<void> {
    const currentResult = this.result();
    if (!currentResult?.id) {
      return;
    }

    const createdAt = currentResult.createdAt
      ? new Date(currentResult.createdAt).toLocaleString()
      : 'Not recorded';
    const verdictText = currentResult.prediction === 'Fake'
      ? 'Suspicious manipulation signals were detected.'
      : 'The image appears more likely authentic.';
    const [imageDataUrl, gradcamDataUrl] = await Promise.all([
      this.mediaUrlToDataUrl(this.imageUrl),
      this.gradcamUrl ? this.mediaUrlToDataUrl(this.gradcamUrl) : Promise.resolve(''),
    ]);
    const reportHtml = this.buildReportHtml(currentResult, createdAt, verdictText, imageDataUrl, gradcamDataUrl);
    const blob = new Blob([reportHtml], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');

    anchor.href = url;
    anchor.download = `truevision-result-${currentResult.id}.html`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  private async mediaUrlToDataUrl(mediaUrl: string): Promise<string> {
    if (!mediaUrl) {
      return '';
    }

    try {
      const response = await fetch(mediaUrl, { credentials: 'include' });
      if (!response.ok) {
        return '';
      }

      const blob = await response.blob();
      return await new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(typeof reader.result === 'string' ? reader.result : '');
        reader.onerror = () => resolve('');
        reader.readAsDataURL(blob);
      });
    } catch {
      return '';
    }
  }

  private buildReportHtml(
    result: ResultItem,
    createdAt: string,
    verdictText: string,
    imageUrl: string,
    gradcamUrl: string,
  ): string {
    const escapeHtml = (value: string | number | null | undefined): string => String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
    const isFake = result.prediction === 'Fake';
    const verdictClass = isFake ? 'fake' : 'real';
    const verdictLabel = isFake ? 'Needs Review' : 'Likely Authentic';
    const confidence = result.confidence.toFixed(2);
    const inferenceTime = result.inferenceTime === null || result.inferenceTime === undefined
      ? 'Not recorded'
      : `${result.inferenceTime.toFixed(2)} seconds`;

    return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TrueVision Result ${escapeHtml(result.id)}</title>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Arial, sans-serif; color: #eaf2ff; background: #07111f; }
    main { max-width: 1080px; margin: 0 auto; padding: 32px; }
    .hero, .panel { border: 1px solid #1e4960; border-radius: 20px; background: #0d1b2e; padding: 24px; margin-bottom: 18px; }
    .hero { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 24px; align-items: center; background: linear-gradient(135deg, #0d1b2e, #082337 58%, #1b1230); }
    .brand { margin: 0 0 8px; color: #67e8f9; font-size: 13px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
    h1 { margin: 0 0 10px; font-size: 38px; line-height: 1.05; }
    h2 { margin: 0 0 14px; font-size: 20px; color: #67e8f9; }
    p { line-height: 1.6; }
    .muted { color: #a9bad1; }
    .verdict { min-width: 210px; padding: 20px; border-radius: 18px; text-align: center; }
    .verdict.real { border: 1px solid #34d399; background: linear-gradient(135deg, rgba(52, 211, 153, .24), rgba(20, 184, 166, .12)); }
    .verdict.fake { border: 1px solid #fb7185; background: linear-gradient(135deg, rgba(251, 113, 133, .24), rgba(245, 158, 11, .12)); }
    .verdict span { display: inline-block; margin-bottom: 8px; padding: 7px 12px; border-radius: 999px; color: #06111f; font-weight: 800; }
    .verdict.real span { background: #6ee7b7; }
    .verdict.fake span { background: #fb7185; }
    .verdict strong { display: block; font-size: 42px; line-height: 1; }
    .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    .metric { border-radius: 16px; background: #081323; padding: 16px; border: 1px solid #17334a; }
    .metric span { display: block; color: #91a7c2; font-size: 12px; text-transform: uppercase; letter-spacing: .08em; }
    .metric strong { display: block; margin-top: 7px; font-size: 20px; color: #f8fbff; }
    .details { display: grid; gap: 14px; }
    .detail { padding: 16px; border-radius: 14px; background: #081323; border: 1px solid #17334a; }
    .detail strong { display: block; margin-bottom: 6px; color: #67e8f9; }
    .images { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    figure { margin: 0; border-radius: 16px; background: #06101d; padding: 14px; border: 1px solid #17334a; }
    figcaption { margin-bottom: 10px; color: #67e8f9; font-weight: 800; text-transform: uppercase; font-size: 12px; letter-spacing: .08em; }
    img { width: 100%; max-height: 460px; object-fit: contain; border-radius: 12px; background: white; }
    .missing { display: grid; place-items: center; min-height: 280px; border: 1px dashed #35516c; border-radius: 12px; color: #a9bad1; background: #07111f; text-align: center; padding: 18px; }
    .footer-note { color: #91a7c2; font-size: 13px; }
    @media (max-width: 760px) { main { padding: 18px; } .hero, .images, .metrics { grid-template-columns: 1fr; } .verdict { min-width: 0; } h1 { font-size: 30px; } }
    @media print { body { background: white; color: #111827; } .hero, .panel, .metric, .detail, figure { border-color: #d1d5db; background: white; } .muted, .footer-note { color: #4b5563; } .verdict strong, .metric strong { color: #111827; } }
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div>
        <p class="brand">TRUEVISION Deepfake Image Intelligence</p>
        <h1>Image Check Report</h1>
        <p class="muted">${escapeHtml(verdictText)}</p>
      </div>
      <div class="verdict ${verdictClass}">
        <span>${escapeHtml(verdictLabel)}</span>
        <strong>${escapeHtml(confidence)}%</strong>
        <small>Model confidence</small>
      </div>
    </section>

    <section class="panel metrics">
      <div class="metric"><span>Result ID</span><strong>#${escapeHtml(result.id)}</strong></div>
      <div class="metric"><span>Prediction</span><strong>${escapeHtml(result.prediction)}</strong></div>
      <div class="metric"><span>Checked</span><strong>${escapeHtml(createdAt)}</strong></div>
      <div class="metric"><span>Inference Time</span><strong>${escapeHtml(inferenceTime)}</strong></div>
    </section>

    <section class="panel details">
      <h2>Review Summary</h2>
      <div class="detail"><strong>Explanation</strong>${escapeHtml(result.explanation || 'No explanation available.')}</div>
      <div class="detail"><strong>Recommended action</strong>${escapeHtml(result.recommendation || 'No recommendation available.')}</div>
      <div class="detail"><strong>Feedback</strong>${escapeHtml(result.feedback || 'Not provided')}</div>
    </section>

    <section class="panel images">
      <figure>
        <figcaption>Uploaded Image</figcaption>
        ${imageUrl ? `<img src="${imageUrl}" alt="Uploaded image">` : `<div class="missing">Uploaded image could not be embedded.</div>`}
      </figure>
      <figure>
        <figcaption>Highlighted Focus Areas</figcaption>
        ${gradcamUrl ? `<img src="${gradcamUrl}" alt="Highlighted model focus areas">` : `<div class="missing">Highlighted image could not be embedded.</div>`}
      </figure>
    </section>

    <p class="footer-note">Generated by TrueVision. Use this report as a decision-support record, not as the only basis for high-stakes verification.</p>
  </main>
</body>
</html>`;
  }
  submitFeedback(feedback: 'Satisfied' | 'Unsatisfied'): void {
    const currentResult = this.result();

    if (!currentResult || !currentResult.id) {
      return;
    }

    this.errorMessage.set('');
    this.successMessage.set('');
    this.isSubmittingFeedback.set(true);

    this.resultsService.submitFeedback(currentResult.id, feedback).subscribe({
      next: (response) => {
        this.result.set(response.result);
        this.successMessage.set(response.message);
        this.isSubmittingFeedback.set(false);
      },
      error: (error) => {
        this.errorMessage.set(error?.error?.error || 'Failed to save feedback.');
        this.isSubmittingFeedback.set(false);
      },
    });
  }
}
