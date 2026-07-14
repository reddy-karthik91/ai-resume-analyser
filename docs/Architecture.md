# Technical Architecture Design Guide

This document describes the design patterns, architectural principles, and communication flow for the AI Resume Analyzer application.

---

## 🏗️ Architectural Overview

The application is built on an **Enterprise-Grade Modular Service Architecture** that maintains strict separation of concerns between delivery frameworks (REST controllers) and business logic. 

```text
    [Presentation Layer]               Angular 19 Frontend Client
                                                   │
                                                   │ HTTP REST Requests
                                                   ▼
    [API Controller Layer]            Flask Blueprints & Controllers
                                                   │
                                                   ▼
   [Orchestration Pipeline]              ResumeAnalysisPipeline
                                                   │
                                   ┌───────────────┼───────────────┬────────────────┐
                                   │               │               │                │
    [Business Services Layer]      ▼               ▼               ▼                ▼
                             UploadService   PdfParser     PromptBuilder      OpenAIService
                                   │         (Planned)       (Planned)          (Planned)
                                   ▼
                          FileStorageService
```

---

## 🏃 Resume Analysis Pipeline

The heart of the business workflow is orchestrated by `ResumeAnalysisPipeline`. This class coordinates the validation, text extraction, analysis, and formatting flow without containing service-specific logic.

### Complete Orchestration Flow (Sprint 2 - 4)

```text
Angular Frontend
   │
   ▼
resumes_routes: POST /api/v1/resumes/upload
   │
   ▼
ResumeAnalysisPipeline
   │
   ├── 1. upload_resume() ──► UploadService ──► FileStorageService (Saves uuid_timestamp.pdf)
   │
   ├── 2. parse_resume() ──► [PLANNED] PdfParserService (Extracts PDF text via PyMuPDF)
   │
   ├── 3. build_prompt() ──► [PLANNED] PromptBuilderService (Constructs optimized prompts)
   │
   ├── 4. analyze_resume() ──► [PLANNED] OpenAIService (Interacts with OpenAI API)
   │
   └── 5. format_response() ──► [PLANNED] AnalysisFormatterService (Normalizes assessment report)
   │
   ▼
Standardized API Success/Error JSON Response
```

---

## 📂 Service Directory & Responsibilities

The `backend/app/services/` layer is split into individual, highly focused classes mapping to single responsibilities:

### Active Components

1. **`ResumeAnalysisPipeline` ([resume_analysis_pipeline.py](file:///Users/reddykarthik/Desktop/ai-resume-analyser/backend/app/services/resume_analysis_pipeline.py))**
   - Coordinates high-level business workflow steps.
   - Delegates operations to dedicated services.
   - Prevents code coupling between controllers and utility services.

2. **`UploadService` ([upload_service.py](file:///Users/reddykarthik/Desktop/ai-resume-analyser/backend/app/services/upload_service.py))**
   - Performs multi-layer file validation (checks PDF extension, verifies `application/pdf` MIME type).
   - Validates file size constraints (max 5 MB limit, zero-byte uploads prevention).

3. **`FileStorageService` ([file_storage_service.py](file:///Users/reddykarthik/Desktop/ai-resume-analyser/backend/app/services/file_storage_service.py))**
   - Creates destination directories on the filesystem automatically.
   - Generates safe unique names using `<uuid>_<timestamp>.pdf`.
   - Writes binary file payloads securely to disk.

### Planned Components (Future Architecture)

4. **`PdfParserService` (`pdf_parser_service.py` - Planned in Sprint 3)**
   - Responsible for reading text from PDF files using the PyMuPDF engine.
   - Validates document structure and reports empty/unreadable text.
   - Extends parser compatibility to support cover letters, job descriptions, and certifications.

5. **`PromptBuilderService` (`prompt_builder_service.py` - Planned in Sprint 4)**
   - Combines extracted text, target job descriptions, and structured grading rules.
   - Compiles optimized prompt templates dynamically.

6. **`OpenAIService` (`openai_service.py` - Planned in Sprint 4)**
   - Manages connection lifecycle with the OpenAI ChatCompletion API.
   - Implements back-off retries and rate limit tracking.

7. **`AnalysisFormatterService` (`analysis_formatter_service.py` - Planned in Sprint 4)**
   - Deserializes and maps raw LLM responses to the strict API envelope structure.
   - Provides default score values and fallbacks in case of analysis issues.
