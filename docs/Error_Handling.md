# Error Handling Strategy

This document details the application's error-handling strategy across both backend (Flask) and frontend (Angular) layers. The objective is to prevent server traceback exposures, enforce standard HTTP status codes, and guarantee user-friendly error alerts.

---

## 🐍 Backend Error-Handling Pipeline (Flask)

The Flask backend utilizes a centralized error-handling strategy via global error handlers registered using `@app.errorhandler`.

### 1. Centralized Error Handlers
* **Standard Exception Interception**: All unhandled python exceptions (`Exception`) are caught globally. The server logs the full traceback with its `requestId` for developers and returns a clean, sanitized standard envelope with a `500 Internal Server Error` status to the client.
* **Custom Custom API Exceptions**: The system maps custom classes extending `APIException` directly to their matching status codes:
  * `InvalidResumeException` $\rightarrow$ `400 Bad Request`
  * `UnsupportedFileException` $\rightarrow$ `415 Unsupported Media Type`
  * `AIServiceException` $\rightarrow$ `503 Service Unavailable`
  * `ValidationException` $\rightarrow$ `400 Bad Request`

### 2. Request Inputs Validation
* When JSON payloads fail validator checks (e.g., missing parameter variables), the request raises a `ValidationException`. The response includes a `400 Bad Request` code and lists the failed fields inside the `errors` array of the standard envelope.

### 3. File Upload Validations
* File upload handlers check boundaries prior to parsing:
  * Payload size exceeding boundaries $\rightarrow$ `413 Payload Too Large` (Limit: 5MB).
  * Wrong file extension or mime type $\rightarrow$ `415 Unsupported Media Type` (Limit: `.pdf`).
  * Empty file or corrupt header $\rightarrow$ `400 Bad Request`.

---

## 🅰️ Frontend Error-Handling Pipeline (Angular)

The Angular client intercepts and processes errors asynchronously using centralized handlers.

### 1. HTTP Error Interceptor
* A global `HttpInterceptor` catches outgoing requests and maps failed responses:
  * **Network Outages**: Returns a generic connection offline notification.
  * **`400` & `415` Validation Errors**: Extracts standard error items from the response `errors` array and displays them on the active form.
  * **`500` & `503` Server/AI Service Errors**: Renders generic help-desk prompts via toast widgets to protect users from technical details.

### 2. UX Presentation Strategy
* Critical exceptions are displayed through toast widgets (`ngx-toastr`) or alerts.
* Validation warnings are rendered directly beneath input fields on forms.
