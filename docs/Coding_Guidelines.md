# Coding Guidelines & Standards

This document establishes the code naming, formatting, and organization conventions for the AI Resume Analyzer repository. Adhering to these standards ensures code readability, clean reviews, and long-term project maintainability.

---

## 🅰️ Angular Coding Standards

* **Folder Organization**:
  * Adopt a modular, feature-oriented structure inside `src/app/features/`.
  * House core configs and route guards inside `core/`.
  * Place reusable presentational UI elements inside `shared/components/`.
* **TypeScript Conventions**:
  * Class names: **PascalCase** (e.g. `UploadResumeComponent`).
  * File names: **kebab-case** with element descriptors (e.g., `upload-resume.component.ts`).
  * Methods and variables: **camelCase** (e.g., `parseFile()`).
  * Interfaces: Named with clear descriptors without `I` prefixes (e.g. `ResumeAnalysis`).
* **RxJS Streams Management**:
  * Always suffix observable variables with a `$` character (e.g., `analysisResult$`).
  * Use operators like `takeUntil()` or async pipes inside templates to clean up subscriptions and prevent memory leaks.

---

## 🐍 Python Coding Standards

* **Style Constraints**: Conform strictly to **PEP 8** style guidelines.
* **Naming Conventions**:
  * Classes: **PascalCase** (e.g., `ResumeParserService`).
  * Variables, functions, and routes: **snake_case** (e.g., `extract_text()`).
  * Constants: **UPPERCASE_SNAKE_CASE** (e.g., `MAX_FILE_SIZE_BYTES`).
* **Imports Hierarchy**:
  1. Standard library imports (e.g., `os`, `sys`).
  2. Third-party packages (e.g., `flask`, `pydantic`).
  3. Local application imports (e.g., `from app.services import ...`).
* **Docstrings**: Document every class, public function, and route endpoint using descriptive Docstrings.

---

## 🌐 API Endpoint Conventions

* Route paths must follow RESTful standards using kebab-case plural resources (e.g., `/api/v1/resumes/upload`).
* Always represent API version prefixing clearly: `/api/v1/`.

---

## 🐙 Version Control Rules

* **Branch Naming Standard**:
  * Features: `feature/short-desc`
  * Bugfixes: `bugfix/short-desc`
  * Hotfixes: `hotfix/short-desc`
* **Commit Message Format**: Follow **Conventional Commits**:
  * `feat: add PDF text extraction logic`
  * `fix: correct token budget overrun error`
  * `docs: update setup documentation guide`
  * `chore: upgrade npm dependencies`
* **Formatting Tools**: Run project linters and formatters before submitting Pull Requests.
