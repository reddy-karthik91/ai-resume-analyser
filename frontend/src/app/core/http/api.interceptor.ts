import { HttpInterceptorFn } from '@angular/common/http';

export const apiInterceptor: HttpInterceptorFn = (req, next) => {
  // api.interceptor.ts
  // Centralized HTTP request and response interceptor.
  //
  // Future implementation details:
  // Intercept requests to inject bearer tokens, format endpoints path,
  // and globally catch response exceptions (e.g. auto-logouts on 401).
  return next(req);
};
