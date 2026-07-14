import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { NavbarComponent } from '../../shared/components/navbar/navbar.component';
import { FooterComponent } from '../../shared/components/footer/footer.component';
import { HeroComponent } from './components/hero/hero.component';
import { UploadCardComponent } from './components/upload-card/upload-card.component';
import { ProcessingPlaceholderComponent } from './components/processing-placeholder/processing-placeholder.component';
import { ResultsPlaceholderComponent } from './components/results-placeholder/results-placeholder.component';
import { AnalysisService } from '../../core/services/analysis.service';
import { ResumeAnalysisResult } from '../../core/models/resume-analysis-result.model';

export type AnalysisStatus = 'idle' | 'uploading' | 'uploaded' | 'processing' | 'completed' | 'error';

export interface AnalysisState {
  status: AnalysisStatus;
  progress: number;
  errorMessage: string | null;
  fileName: string;
  result: ResumeAnalysisResult | null;
}

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    NavbarComponent,
    FooterComponent,
    HeroComponent,
    UploadCardComponent,
    ProcessingPlaceholderComponent,
    ResultsPlaceholderComponent
  ],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss'
})
export class HomeComponent {
  private analysisService = inject(AnalysisService);

  // Strongly typed state using Angular Signals
  state = signal<AnalysisState>({
    status: 'idle',
    progress: 0,
    errorMessage: null,
    fileName: '',
    result: null
  });

  onFileSelected(file: File): void {
    this.state.update(s => ({
      ...s,
      status: 'uploading',
      fileName: file.name,
      errorMessage: null
    }));
  }

  onUploadCompleted(metadata: any): void {
    // 1. Transition to processing status
    this.state.update(s => ({
      ...s,
      status: 'processing',
      progress: 50
    }));

    const documentId = metadata.uploadId;
    
    // 2. Trigger the synchronous analysis call
    this.analysisService.processResume(documentId).subscribe({
      next: (result: ResumeAnalysisResult) => {
        // Safe logging of status and timing (PII-free)
        console.log('Analysis completed successfully', {
          status: 'success',
          document_id: result.document_id,
          recommendation_count: result.recommendations.length,
          time_ms: result.analysis_metadata.analysis_duration_ms
        });
        
        this.state.update(s => ({
          ...s,
          status: 'completed',
          result: result,
          progress: 100
        }));
      },
      error: (err) => {
        let msg = 'Analysis failed due to a server or LLM processing error.';
        if (err.error) {
          msg = err.error.message || err.error.errors?.[0] || msg;
        } else if (err.message) {
          msg = err.message;
        }

        console.error('Analysis failed', {
          status: 'error',
          error_msg: msg
        });

        this.state.update(s => ({
          ...s,
          status: 'error',
          errorMessage: msg
        }));
      }
    });
  }

  onUploadFailed(errorMessage: string): void {
    this.state.update(s => ({
      ...s,
      status: 'error',
      errorMessage: errorMessage
    }));
  }

  onReset(): void {
    this.state.set({
      status: 'idle',
      progress: 0,
      errorMessage: null,
      fileName: '',
      result: null
    });
  }
}
