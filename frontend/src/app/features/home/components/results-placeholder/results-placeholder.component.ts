import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { ResumeAnalysisResult } from '../../../../core/models/resume-analysis-result.model';

@Component({
  selector: 'app-results-placeholder',
  standalone: true,
  imports: [CommonModule, MatButtonModule],
  templateUrl: './results-placeholder.component.html',
  styleUrl: './results-placeholder.component.scss'
})
export class ResultsPlaceholderComponent {
  @Input() fileName: string = '';
  @Input() result!: ResumeAnalysisResult;
  @Output() reset = new EventEmitter<void>();

  /**
   * Builds keyword match matrix by combining matches and gaps.
   */
  get keywordMatrix(): { name: string, found: boolean }[] {
    const list: { name: string, found: boolean }[] = [];
    if (!this.result?.skill_analysis) {
      return list;
    }
    
    for (const kw of this.result.skill_analysis.keyword_matches || []) {
      list.push({ name: kw, found: true });
    }
    for (const kw of this.result.skill_analysis.keyword_gaps || []) {
      list.push({ name: kw, found: false });
    }
    return list;
  }

  /**
   * Computes the SVG dash offset based on the ATS Score.
   */
  get dashOffset(): number {
    const score = this.result?.ats_score?.score ?? 0;
    const circumference = 326.7;
    return circumference - (circumference * score / 100);
  }
}
