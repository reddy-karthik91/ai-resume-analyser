import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent, HttpRequest } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_CONFIG } from '../http/api.config';
import { UploadResponse } from '../models/upload-response.model';

@Injectable({
  providedIn: 'root'
})
export class UploadService {
  private uploadUrl = `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.RESUME.UPLOAD}`;

  constructor(private http: HttpClient) {}

  /**
   * Uploads a resume PDF file to the backend, enabling progress tracking.
   * 
   * @param file The File object selected by the user.
   * @returns An Observable emitting HttpEvents containing progress ticks and final UploadResponse.
   */
  uploadResume(file: File): Observable<HttpEvent<UploadResponse>> {
    const formData = new FormData();
    formData.append('file', file);

    const req = new HttpRequest('POST', this.uploadUrl, formData, {
      reportProgress: true,
      responseType: 'json'
    });

    return this.http.request<UploadResponse>(req);
  }
}
