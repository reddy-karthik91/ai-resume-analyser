import { Component, Output, EventEmitter, signal, inject, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { HttpEventType, HttpEvent } from '@angular/common/http';
import { Subscription } from 'rxjs';
import { UploadService } from '../../../../core/services/upload.service';
import { UploadState } from '../../../../core/models/upload-state.model';
import { UploadResponse } from '../../../../core/models/upload-response.model';

@Component({
  selector: 'app-upload-card',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatProgressBarModule],
  templateUrl: './upload-card.component.html',
  styleUrl: './upload-card.component.scss'
})
export class UploadCardComponent implements OnDestroy {
  @Output() fileSelected = new EventEmitter<File>();
  
  private uploadService = inject(UploadService);
  private uploadSubscription?: Subscription;

  // Signals
  isDragOver = signal<boolean>(false);
  
  // Single, strongly typed state signal for managing upload flow
  uploadState = signal<UploadState>({
    status: 'idle',
    progress: 0,
    errorMessage: null,
    metadata: null
  });

  // Constants matching the backend validation rules
  private readonly MAX_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB
  private readonly ALLOWED_EXTENSION = '.pdf';
  private readonly ALLOWED_MIME_TYPE = 'application/pdf';

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    if (this.uploadState().status === 'idle') {
      this.isDragOver.set(true);
    }
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver.set(false);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver.set(false);

    if (this.uploadState().status !== 'idle') {
      return;
    }

    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      const file = event.dataTransfer.files[0];
      this.processFileSelection(file);
    }
  }

  onFileChange(event: Event): void {
    if (this.uploadState().status !== 'idle') {
      return;
    }

    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.processFileSelection(input.files[0]);
    }
  }

  /**
   * Run client-side validations and initiate upload if valid.
   */
  private processFileSelection(file: File): void {
    // Layer 1: Validate file presence and non-zero size
    if (!file || file.size === 0) {
      this.setErrorState('Request validation failed. The uploaded file is empty (0 bytes).');
      return;
    }

    // Layer 2: Validate extension (case-insensitive)
    const fileNameLower = file.name.toLowerCase();
    if (!fileNameLower.endsWith(this.ALLOWED_EXTENSION)) {
      this.setErrorState('The uploaded file format is unsupported. Only PDF files are allowed.');
      return;
    }

    // Layer 3: Validate MIME type
    if (file.type !== this.ALLOWED_MIME_TYPE) {
      this.setErrorState('The uploaded file format is unsupported. Only PDF files are allowed.');
      return;
    }

    // Size limit check (5 MB)
    if (file.size > this.MAX_SIZE_BYTES) {
      this.setErrorState('File size exceeds the maximum limit of 5 MB.');
      return;
    }

    // Emits fileSelected output for parent hook integrations if needed
    this.fileSelected.emit(file);

    // Validations passed, initiate upload
    this.startUpload(file);
  }

  private startUpload(file: File): void {
    // Reset state to uploading
    this.uploadState.set({
      status: 'uploading',
      progress: 0,
      errorMessage: null,
      metadata: null
    });

    // Cancel any ongoing upload
    this.cancelUploadSubscription();

    // Trigger API request
    this.uploadSubscription = this.uploadService.uploadResume(file).subscribe({
      next: (event: HttpEvent<UploadResponse>) => {
        if (event.type === HttpEventType.UploadProgress && event.total) {
          const pct = Math.round((100 * event.loaded) / event.total);
          this.uploadState.set({
            status: 'uploading',
            progress: pct,
            errorMessage: null,
            metadata: null
          });
        } else if (event.type === HttpEventType.Response) {
          const response = event.body;
          if (response && response.success && response.data) {
            this.uploadState.set({
              status: 'success',
              progress: 100,
              errorMessage: null,
              metadata: response.data
            });
          } else {
            const errMsg = response?.message || response?.errors?.[0] || 'Upload failed.';
            this.setErrorState(errMsg);
          }
        }
      },
      error: (err) => {
        let msg = 'An unexpected server error occurred.';
        if (err.error) {
          msg = err.error.message || err.error.errors?.[0] || msg;
        } else if (err.message) {
          msg = err.message;
        }
        this.setErrorState(msg);
      }
    });
  }

  private setErrorState(message: string): void {
    this.uploadState.set({
      status: 'error',
      progress: 0,
      errorMessage: message,
      metadata: null
    });
  }

  /**
   * Cancels the active upload request.
   */
  cancelUpload(): void {
    if (this.uploadSubscription) {
      this.cancelUploadSubscription();
      this.uploadState.set({
        status: 'idle',
        progress: 0,
        errorMessage: 'Upload was cancelled.',
        metadata: null
      });
    } else {
      this.resetCard();
    }
  }

  /**
   * Resets the upload card to ready state.
   */
  resetCard(): void {
    this.cancelUploadSubscription();
    this.uploadState.set({
      status: 'idle',
      progress: 0,
      errorMessage: null,
      metadata: null
    });
  }

  private cancelUploadSubscription(): void {
    if (this.uploadSubscription) {
      this.uploadSubscription.unsubscribe();
      this.uploadSubscription = undefined;
    }
  }

  ngOnDestroy(): void {
    this.cancelUploadSubscription();
  }
}
