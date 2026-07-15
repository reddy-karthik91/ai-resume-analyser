export const API_CONFIG = {
  // api.config.ts
  // Centralized configurations mapping for backend API routing.
  //
  // Future implementation details:
  // Dynamically map base URLs and REST routes depending on environment level configs
  // (e.g. dev/prod endpoints).

  BASE_URL: 'https://ai-resume-analyser-bz2m.onrender.com/api/v1',
  // BASE_URL: 'http://localhost:5001/api/v1',
  ENDPOINTS: {
    HEALTH: '/health',
    RESUME: {
      UPLOAD: '/resumes/upload',
      ANALYZE: '/resumes/analyze',
      HISTORY: '/resumes/history'
    }
  }
};
