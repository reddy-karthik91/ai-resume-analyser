# Logging Strategy

This document outlines the logging strategy and rotation guidelines for the AI Resume Analyzer server application.

---

## 📋 Log Classifications

To support audit tracking and debugging, server transactions are partitioned into distinct log classifications:

### 1. Request Logs
* **Purpose**: Records incoming HTTP requests, response latency, remote client IPs, HTTP methods, and status codes.
* **Format**: Standard JSON schema, containing a `requestId` value linking to the client transaction.

### 2. Error Logs
* **Purpose**: Captures warnings, validator errors, custom exceptions, and system-level tracebacks.
* **Level**: `WARNING`, `ERROR`, or `CRITICAL`. Includes request parameters (excluding private user data) and traceback dumps.

### 3. AI Transactions Logs
* **Purpose**: Audits prompt lengths, token budgets consumed, model versions utilized, and API response latencies for OpenAI calls.
* **Security Rules**: Raw resume text and personal identifier info are excluded from log logs to protect applicant privacy.

### 4. File Ingestion Logs
* **Purpose**: Logs file upload attempts, file name hashes, size metrics, and parsing status results from PyMuPDF.

### 5. Security Audit Logs
* **Purpose**: Tracks validation failures, access control attempts, CORS blocks, and rate limit exhaustion events.

---

## ⚙️ Log Rotation & Storage Strategy

* **Local Output Path**: Placed in `backend/logs/` (Git-ignored).
* **Handler Configuration**: Flask application logging uses a `RotatingFileHandler`.
* **Rotation Rules**:
  * **Size Trigger**: Files are rotated when they reach **10MB**.
  * **Retention Limit**: Retain a maximum of **5 backup logs** locally before deleting old records.
* **Format Standard**: All logs output as structured JSON objects containing:
  * Timestamp (UTC)
  * Log Level
  * Request UUID (`requestId`)
  * Execution Thread ID
  * Target Module / Source Class
  * Context Message
