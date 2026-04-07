import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { API_BASE_URL } from '../config/api.config';

export type ResultItem = {
  id: number;
  saved: boolean;
  prediction: 'Fake' | 'Real';
  confidence: number;
  feedback: string | null;
  imagePath: string;
  gradcamPath: string | null;
  explanation: string;
  recommendation: string;
  createdAt: string | null;
  inferenceTime: number | null;
};

export type UploadResponse = {
  message: string;
  result: ResultItem;
};

export type ResultsResponse = {
  results: ResultItem[];
};

export type ResultDetailResponse = {
  result: ResultItem;
};

export type FeedbackResponse = {
  message: string;
  result: ResultItem;
};

export type PerformanceModel = {
  id: number;
  modelName: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  fpr: number;
  fnr: number;
  tnr: number;
  tp: number;
  tn: number;
  fp: number;
  fn: number;
  aucRoc: number;
  prAuc: number;
  confusionMatrix: string | null;
};

export type PerformanceResponse = {
  bestModel: {
    id: number;
    modelName: string;
    accuracy: number;
    precision: number;
    recall: number;
    f1Score: number;
    aucRoc: number;
    prAuc: number;
    tp: number;
    tn: number;
    fp: number;
    fn: number;
  };
  models: PerformanceModel[];
};

@Injectable({
  providedIn: 'root',
})
export class ResultsService {
  private readonly apiBase = API_BASE_URL;

  constructor(private http: HttpClient) {}

  uploadImage(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<UploadResponse>(`${this.apiBase}/upload`, formData, {
      withCredentials: true,
    });
  }

  getResults() {
    return this.http.get<ResultsResponse>(`${this.apiBase}/results`, {
      withCredentials: true,
    });
  }

  getResultById(id: number) {
    return this.http.get<ResultDetailResponse>(`${this.apiBase}/results/${id}`, {
      withCredentials: true,
    });
  }

  submitFeedback(id: number, feedback: 'Satisfied' | 'Unsatisfied') {
    return this.http.post<FeedbackResponse>(
      `${this.apiBase}/results/${id}/feedback`,
      { feedback },
      {
        withCredentials: true,
      }
    );
  }

  getPerformance() {
    return this.http.get<PerformanceResponse>(`${this.apiBase}/performance`, {
      withCredentials: true,
    });
  }
}
