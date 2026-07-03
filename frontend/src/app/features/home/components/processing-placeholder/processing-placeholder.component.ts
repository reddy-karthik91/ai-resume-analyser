import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatProgressBarModule } from '@angular/material/progress-bar';

@Component({
  selector: 'app-processing-placeholder',
  standalone: true,
  imports: [CommonModule, MatProgressBarModule],
  templateUrl: './processing-placeholder.component.html',
  styleUrl: './processing-placeholder.component.scss'
})
export class ProcessingPlaceholderComponent {
  @Input() fileName: string = '';
}
