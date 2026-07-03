import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-results-placeholder',
  standalone: true,
  imports: [CommonModule, MatButtonModule],
  templateUrl: './results-placeholder.component.html',
  styleUrl: './results-placeholder.component.scss'
})
export class ResultsPlaceholderComponent {
  @Input() fileName: string = '';
  @Output() reset = new EventEmitter<void>();

  // Mock data representing standard parsed outcomes
  atsScore = 78;
  missingSkills = ['RxJS State Streams', 'Angular Material Layouts', 'REST API Architecture', 'Unit Testing (Jasmine)'];
  keywords = [
    { name: 'TypeScript', found: true },
    { name: 'Angular 19', found: true },
    { name: 'RxJS State Streams', found: false },
    { name: 'REST API Architecture', found: false },
    { name: 'SCSS / CSS Grid', found: true },
    { name: 'Flask REST API', found: true }
  ];
  strengths = [
    'Strong structural foundation in modern frontend web app development frameworks.',
    'Consistent adherence to standard PEP 8 naming conventions and guidelines.',
    'Clear encapsulation of database config logic from initialization modules.'
  ];
  weaknesses = [
    'Lacks quantitative metrics demonstrating feature optimizations.',
    'Missing RxJS state stream architectures for component communication.',
    'Absence of automated unit testing configs.'
  ];
}
