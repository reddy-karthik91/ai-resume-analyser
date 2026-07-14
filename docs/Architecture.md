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

5. **`PromptBuilderService` ([prompt_builder_service.py](file:///Users/reddykarthik/Desktop/ai-resume-analyser/backend/app/services/prompt_builder_service.py))**
   - Loads and compiles external Markdown templates (`system_prompt.md`, `analysis_instructions.md`, `scoring_rules.md`, `recommendation_rules.md`, `output_schema.md`).
   - Caches templates in-memory during construction to prevent filesystem reads on subsequent requests.
   - Outputs provider-independent `PromptRequest` instances containing formatted user resume segments and execution metadata.

6. **`GeminiService` ([gemini_service.py](file:///Users/reddykarthik/Desktop/ai-resume-analyser/backend/app/services/gemini_service.py))** and **`GroqService` ([groq_service.py](file:///Users/reddykarthik/Desktop/ai-resume-analyser/backend/app/services/groq_service.py))**
   - Implements LLM generation clients. The active provider is resolved dynamically via the `LLM_PROVIDER` environment variable (defaulting to `"groq"`).
   - `GeminiService` communicates with Google Gemini API using the official unified `google-genai` SDK.
   - `GroqService` communicates with Groq Cloud using the official `groq` SDK (targeting `llama-3.3-70b-versatile`).
   - Converts standard `PromptRequest` variables into API calls, configuring JSON formatting structures to prefer structured JSON.
   - Generates trace correlation `request_id` parameters, implements transient retry backoffs, executes content output validation, maps token metadata, and yields provider-neutral `PromptResponse` DTOs.

7. **`AnalysisFormatterService` ([analysis_formatter_service.py](file:///Users/reddykarthik/Desktop/ai-resume-analyser/backend/app/services/analysis_formatter_service.py))**
   - Parses, decodes, and validates JSON completions from `PromptResponse`.
   - Executes Stage 1 Structural Validation (ensuring sections and typing structures match schema expectations) and Stage 2 Business Rules Validation (bounds checking, enums validation, lists constraints).
   - Generates nested dataclasses, maps metadata metrics from the provider response, and constructs the immutable aggregate root `ResumeAnalysisResult`.

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

## 🔒 Provider-Independent AI Boundary Rule

To maintain clean contracts, the client application (Angular) **never consumes raw vendor responses** from LLM APIs (e.g. Gemini, OpenAI, Claude). Instead, the backend defines a provider-agnostic completion pipeline where core domain models are completely isolated from vendor SDK definitions:

```text
ParsedDocument
      │
      ▼
PromptBuilderService (Compiles system/user prompts)
      │
      ▼
PromptRequest (DTO holding prompts and settings)
      │
      ▼
LLMService (Abstract contract interface)
      │
      ▼
PromptResponse (DTO holding raw content, finish reasons, token stats)
      │
      ▼
AnalysisFormatterService (Parses raw content to structured DTOs)
      │
      ▼
ResumeAnalysisResult (Aggregate Root holding final formatted scores)
      │
      ▼
Angular Frontend Client (via JSON response envelope)
```

This strict boundary guarantees:
1. **Vendor Independence**: Swapping LLM providers requires changing only the `LLMService` implementation. The rest of the pipeline remains unchanged.
2. **Execution Metadata Separation**: Auditing parameters (durations, prompt versions, token counts) are mapped to `AnalysisMetadata` and `TokenUsage`, keeping candidate evaluations clean.
3. **Domain Type Safety**: Uses domain enums (`ATSGrade`, `ProfessionalLevel`, `RecommendationCategory`) to ensure the client receives strongly typed structures rather than raw text.

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

### 6. Prompt Templates In-Memory Caching
- **Decision**: Read and cache prompt markdown templates (`system_prompt.md`, `analysis_instructions.md`, etc.) in-memory inside the `PromptBuilderService` constructor (`__init__`).
- **Rationale**: Avoids costly filesystem I/O operations (open/read/close) on every inbound resume analysis request, resulting in faster latency and lower host CPU/IO overhead.

### 7. Google GenAI SDK Selection
- **Decision**: Adopt Google's unified `google-genai` Python library over legacy `google-generativeai`.
- **Rationale**: Follows current Google recommendation for live API maintenance and ensures compatibility with Python 3.9+ environments.

### 8. Structured Response Validation and Tracing
- **Decision**: Execute strict candidate output checks (verifying existence of candidates, parts, and non-whitespace text) and generate unique correlation `request_id` parameters logged with every request.
- **Rationale**: Prevents mapping empty completions or safety blocks to standard response envelopes and simplifies remote logging audit debugging without exposing SDK details or PII.

### 9. Two-Stage Validation Flow
- **Decision**: Validate the schema inside `AnalysisFormatterService` using two isolated validation sweeps: `_validate_structure()` for syntax and type constraints, and `_validate_business_rules()` for domain range bounds and enums correctness.
- **Rationale**: Isolates structural checks from business metrics validations, yielding highly targetable error logging traces and clean code maintainability.

### 10. Fail-Fast MVP Constraint
- **Decision**: Stop execution immediately and raise a `ValidationException` when any structural or business rule check fails, with zero silent corrections, default values, or auto-clamping.
- **Rationale**: Maximizes prompt version tuning feedback cycles, ensuring that LLM inconsistencies are caught during development instead of masked.
