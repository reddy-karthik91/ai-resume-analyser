import { UploadMetadata } from './upload-metadata.model';

export interface UploadResponse {
  success: boolean;
  message: string;
  data: UploadMetadata | null;
  errors: string[] | null;
  timestamp: string;
}
