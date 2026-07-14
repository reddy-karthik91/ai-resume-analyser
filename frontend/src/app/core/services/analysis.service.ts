import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { API_CONFIG } from '../http/api.config';
import { ResumeAnalysisResult, AnalysisResponseEnvelope } from '../models/resume-analysis-result.model';

@Injectable({
  providedIn: 'root'
})
export class AnalysisService {
  constructor(private http: HttpClient) {}

  /**
   * Triggers the AI analysis workflow for a successfully uploaded resume.
   * 
   * @param documentId The document identifier (UUID string).
   * @returns An Observable emitting the ResumeAnalysisResult.
   */
  processResume(documentId: string): Observable<ResumeAnalysisResult> {
    const url = `${API_CONFIG.BASE_URL}/resumes/${documentId}/process`;
    return this.http.post<AnalysisResponseEnvelope>(url, {}).pipe(
      map(response => {
        if (response && response.success && response.data) {
          return response.data;
        }
        throw new Error(response?.message || 'Resume analysis failed.');
      }),
      catchError(error => {
        // Safe console logs for operational metadata (excluding raw content or PII)
        console.error('Analysis request error', {
          status: error.status,
          message: error.message || error
        });
        return throwError(() => error);
      })
    );
  }
}
