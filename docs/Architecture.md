# Technical Architecture Design Guide

This document describes the design patterns, architectural principles, and communication flow for the AI Resume Analyzer application.

---

## 🏗️ Architectural Overview

The application is built on an **Enterprise-Grade Modular Service Architecture** that maintains strict separation of concerns between delivery frameworks (REST controllers), business logic orchestration, and the persistence/repository layer.

```text
    [Presentation Layer]                 Angular 19 Frontend Client
                                                     │
                                                     │ HTTP REST Requests
                                                     ▼
    [API Controller Layer]              Flask Blueprints & Controllers
                                                     │
                                                     ▼
   [Orchestration Pipeline]                ResumeAnalysisPipeline
                                                     │
                                   ┌─────────────────┼─────────────────┐
                                   │                 │                 │
    [Business Services Layer]      ▼                 ▼                 ▼
                             UploadService     PdfParserService   PromptBuilder
                                   │           (Utilizes PyMuPDF)  (Planned)
                                   ▼
                           FileStorageService
                                   │
                                   ▼
    [Repository Layer]             │ ◄─────────────────────────────────┐
                           DocumentRepository (Abstraction)            │
                                   │                                   │
                                   ▼                                   │
                     FilesystemDocumentRepository (Concrete)           │
                                   │                                   │
                                   ▼                                   │
                            JSON Index File                            │
                                   │                                   │
                                   └───────────────────────────────────┘
```

---

## 🏃 Orchestrated Document Processing Flow

The heart of the business workflow is orchestrated by `ResumeAnalysisPipeline`. The pipeline binds decoupled components via Dependency Injection.

### Processing Sequence Flow

```text
Angular Frontend
   │
   ▼
resumes_routes: POST /api/v1/resumes/<uuid:document_id>/process
   │
   ▼
ResumeAnalysisPipeline.parse_resume(document_id)
   │
   ├── 1. Get metadata entry ──► DocumentRepository.get(document_id) 
   │                                 └─► FilesystemDocumentRepository (Reads index.json)
   │
   ├── 2. Resolve PDF path & DTO ──► Reconstructs DocumentFileInfo from entry
   │
   ├── 3. Parse PDF document ──► PdfParserService.parse(file_path, file_info)
   │                                 └─► PyMuPDF engine extracts and normalizes text
   │
   ▼
Standardized API Envelope JSON Success/Error Response
```

---

## 📂 Service Directory & Responsibilities

The backend layer is split into individual, highly focused classes mapping to single responsibilities:

### Active Components

1. **`ResumeAnalysisPipeline` ([resume_analysis_pipeline.py](file:///Users/reddykarthik/Desktop/ai-resume-analyser/backend/app/services/resume_analysis_pipeline.py))**
   - Coordinates high-level business workflow steps (upload, parse, prompt generation).
   - Injects repository, parser, and upload services through its constructor.
   - Decoupled from service implementation details.

2. **`PdfParserService` ([pdf_parser_service.py](file:///Users/reddykarthik/Desktop/ai-resume-analyser/backend/app/services/pdf_parser_service.py))**
   - Opens the saved PDF securely using PyMuPDF.
   - Extracts page-by-page text, cleans layout line breaks, and computes counts (words/characters).
   - Compiles and returns the immutable `ParsedDocument` DTO.

3. **`UploadService` ([upload_service.py](file:///Users/reddykarthik/Desktop/ai-resume-analyser/backend/app/services/upload_service.py))**
   - Performs multi-layer file validation (checks PDF extension, verifies `application/pdf` MIME type).
   - Validates file size constraints (max 5 MB limit, zero-byte uploads prevention).

4. **`FileStorageService` ([file_storage_service.py](file:///Users/reddykarthik/Desktop/ai-resume-analyser/backend/app/services/file_storage_service.py))**
   - Creates destination directories on the filesystem.
   - Generates unique stored filenames matching `<uuid>_<timestamp>.pdf`.
   - Saves binary file payloads to disk and registers entries via `DocumentRepository`.

### Planned Components (Future Architecture)

5. **`PromptBuilderService` (`prompt_builder_service.py` - Planned in Sprint 4)**
   - Combines extracted text, target job descriptions, and structured grading rules.
   - Compiles optimized prompt templates dynamically.

6. **`OpenAIService` (`openai_service.py` - Planned in Sprint 4)**
   - Manages connection lifecycle with the OpenAI ChatCompletion API.
   - Implements back-off retries and rate limit tracking.

7. **`AnalysisFormatterService` (`analysis_formatter_service.py` - Planned in Sprint 4)**
   - Deserializes and maps raw LLM responses to the strict API envelope structure.
   - Provides default score values and fallbacks in case of analysis issues.

---

## 🗄️ Repository Layer

To decouple storage engines from service layers, we introduce the repository pattern:

### Package Structure
```text
backend/app/repositories/
├── __init__.py
└── document/
    ├── __init__.py
    ├── document_repository.py (Abstract interface)
    └── filesystem_document_repository.py (Lightweight filesystem index store)
```

### Domain Data Models
- **`DocumentIndexEntry` ([document_index_entry.py](file:///Users/reddykarthik/Desktop/ai-resume-analyser/backend/app/schemas/document/document_index_entry.py))**: Immutable domain DTO representing document metadata records in the repository layer. Decouples repositories from upload schemas.
  - `document_id`: str (UUID)
  - `original_filename`: str
  - `stored_filename`: str
  - `file_size`: int
  - `uploaded_at`: datetime

---

## 📄 Parsed Document Domain Model

We utilize strict Domain-Driven Design (DDD) principles to build an immutable data transfer contract representing a parsed document.

### Domain Model Hierarchy

All components are implemented as **immutable (frozen) Python dataclasses** to guarantee state safety:

```text
ParsedDocument (Aggregate Root)
├── document_id: UUID
├── document_type: DocumentType (Enum: RESUME, JOB_DESCRIPTION, COVER_LETTER, etc.)
├── file: DocumentFileInfo
│     ├── original_filename: str
│     ├── stored_filename: str
│     └── file_size: int
├── metadata: DocumentMetadata
│     ├── page_count: int
│     ├── word_count: int
│     ├── character_count: int
│     ├── parsing_time_ms: int
│     ├── has_extractable_text: bool
│     └── language: Optional[str]
├── pages: List[PageContent]
│     ├── page_number: int
│     ├── text: str
│     ├── word_count: int
│     ├── character_count: int
│     └── has_text: bool
└── text: str (Full consolidated text)
```

---

## 🔒 Future AI Boundary Rule

To maintain clean contracts, the Angular client application **never consumes raw API outputs from OpenAI**. Instead, the backend encapsulates OpenAI response structures within an isolated domain boundary:

```text
OpenAI Service ──► AIAnalysisResult ──► AnalysisFormatterService ──► ResumeAnalysisResponse ──► Angular Frontend
```

---

## ⚙️ Engineering Decisions

### 1. Flask Extension Registry Pattern
- **Decision**: Register composed services inside `app.extensions["resume_pipeline"]`.
- **Rationale**: Follows Flask best practices and avoids polluting the Flask application namespace. Prevents global state coupling and simplifies dependency mocking during automated test setups.

### 2. Centralized Dependency Composition inside `create_app()`
- **Decision**: Perform all dependency compositions inside the `create_app()` factory method (Composition Root).
- **Rationale**: Implements clean Dependency Injection and Dependency Inversion. High-level orchestrators depend only on abstract contracts (like `DocumentRepository`).

### 3. Single Metadata Index for Repository
- **Decision**: Store all upload metadata records inside a centralized JSON index: `backend/storage/documents/index.json`.
- **Rationale**: Avoids directory clutter, resolves synchronization concerns, and prepares the schema layout for direct migration to SQLite/PostgreSQL.

### 4. PII-Safe Structured Logging
- **Decision**: Centralize system logs using standard logging with `extra={...}` variables. Exclude resume text and PII.
- **Rationale**: Promotes secure operational auditing and compliance with data privacy regulations (e.g. GDPR).

### 5. Repository Thread Safety
- **Decision**: Wrap index reads and writes in `FilesystemDocumentRepository` using `threading.Lock()`.
- **Rationale**: Prevents data race corruption of the index JSON during concurrent requests.
- **Limit/Caveat**: `threading.Lock` applies strictly within a single-process application server. Swapping this implementation for SQLite/PostgreSQL in production will naturally replace this in-memory locking model with transaction-level database locking.
