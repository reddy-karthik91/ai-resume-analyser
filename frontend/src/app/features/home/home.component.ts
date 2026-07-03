import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NavbarComponent } from '../../shared/components/navbar/navbar.component';
import { FooterComponent } from '../../shared/components/footer/footer.component';
import { HeroComponent } from './components/hero/hero.component';
import { UploadCardComponent } from './components/upload-card/upload-card.component';
import { ProcessingPlaceholderComponent } from './components/processing-placeholder/processing-placeholder.component';
import { ResultsPlaceholderComponent } from './components/results-placeholder/results-placeholder.component';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule,
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
  uiState = signal<'idle' | 'processing' | 'results'>('idle');
  fileName = signal<string>('');

  onFileSelected(file: File): void {
    this.fileName.set(file.name);
    this.uiState.set('processing');

    // Simulate backend parsing delay of 2.5 seconds
    setTimeout(() => {
      this.uiState.set('results');
    }, 2500);
  }

  onReset(): void {
    this.uiState.set('idle');
    this.fileName.set('');
  }
}
