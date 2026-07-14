import { UploadMetadata } from './upload-metadata.model';

export interface UploadState {
  status: 'idle' | 'uploading' | 'success' | 'error';
  progress: number;
  errorMessage: string | null;
  metadata: UploadMetadata | null;
}
