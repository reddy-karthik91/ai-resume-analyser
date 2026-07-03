# Security Baseline

This document specifies the security constraints, validation criteria, and deployment configurations protecting the AI Resume Analyzer monorepo.

---

## 🔒 Data Protection & Secret Keys

* **Secrets Isolation**: Keys (e.g., `OPENAI_API_KEY`, Flask `SECRET_KEY`) are managed exclusively using environment files (`.env`) loaded by `python-dotenv`.
* **Exclusion Constraints**: The root `.gitignore` excludes environment scripts (`*.env`, `.env`, `.env.local`) to prevent accidental pushes to public repositories.

---

## 📂 File Ingestion Safety Rules

To prevent server exploitation, the upload endpoint implements strict security controls:
1. **Size Verification**: The server enforces a maximum content limit of **5MB** (`MAX_CONTENT_LENGTH_BYTES = 5 * 1024 * 1024`). Requests exceeding this boundary are blocked before files are written to disk.
2. **MIME Verification**: File verification is based on actual MIME types (verifying `application/pdf`) rather than relying on user-provided file names.
3. **Extension Whitelisting**: Only files ending with `.pdf` are allowed.
4. **Sanitized File Names**: User-provided file names are processed using security sanitization helpers (e.g. `werkzeug.utils.secure_filename`) before storage to prevent path traversal attacks.

---

## 🌐 Network & Access Security

* **CORS Scope Restrictions**: Cross-Origin Resource Sharing (CORS) limits requests to trusted Angular client origins (configured via `Flask-CORS`). All other requests are denied.
* **Input Sanitization**: Resume text extracted by PyMuPDF is sanitized to strip out control characters and prompt injections before building the OpenAI prompt.
* **Stateless API Routes**: Session values are not saved on the backend, minimizing the memory footprint and reducing the risk of session hijacking.
* **Planned Token Authorization**: Future iterations will secure user dashboard actions using JWT (JSON Web Tokens) with short expiration windows.
* **HTTPS Protocol Enforcement**: Web communication must use the HTTPS protocol to protect data in transit.
