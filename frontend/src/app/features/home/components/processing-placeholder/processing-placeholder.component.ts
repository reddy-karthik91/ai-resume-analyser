import { Component, Input, OnInit, OnDestroy, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatProgressBarModule } from '@angular/material/progress-bar';

@Component({
  selector: 'app-processing-placeholder',
  standalone: true,
  imports: [CommonModule, MatProgressBarModule],
  templateUrl: './processing-placeholder.component.html',
  styleUrl: './processing-placeholder.component.scss'
})
export class ProcessingPlaceholderComponent implements OnInit, OnDestroy {
  @Input() fileName: string = '';

  activeStep = signal<number>(0);
  private intervalId: any;

  ngOnInit(): void {
    this.intervalId = setInterval(() => {
      this.activeStep.update(current => {
        if (current < 2) {
          return current + 1;
        }
        return current;
      });
    }, 2500);
  }

  ngOnDestroy(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
    }
  }
}
