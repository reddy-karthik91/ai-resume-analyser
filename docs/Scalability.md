# Scalability Strategy

This document describes the architectural roadmap and design choices that enable the AI Resume Analyzer application to scale from a single developer setup to a production-grade SaaS system.

---

## 🏗️ Architectural Separation

The system decouples the frontend client (Angular) from the API backend (Flask REST API), allowing both components to scale independently:
* **Frontend Delivery**: Built as static HTML/CSS/JS bundles and distributed via global Content Delivery Networks (CDNs) like Vercel, providing fast load times and minimal server load.
* **Backend Processing**: Run as an independent REST API layer on Render. This allows us to scale backend container instances vertically or horizontally based on request volume.

---

## ⚡ Caching Layer

Because text extraction and LLM calls are computationally heavy and expensive, the system plans to implement caching:
* **Checksum Caching**: Compute MD5 hashes of uploaded PDF resume files.
* **Result Cache Store**: Store successful analysis JSON reports in a Redis database using the file's MD5 checksum as the key.
* **Benefits**: If a user uploads the same resume multiple times, the server returns the cached analysis instantly, reducing OpenAI API costs and response times.

---

## ⏳ Background Job Processing

To keep the main HTTP request-response cycle fast, long-running processes will be processed asynchronously:
* **Asynchronous Queue**: Integrate a distributed task queue (e.g. Celery with Redis).
* **Task Offloading**: The upload route will accept the file, queue the analysis task, and immediately return a `202 Accepted` status with a task ID to the Angular client.
* **Client Polling / WebSockets**: The frontend client will poll a status endpoint or listen to a WebSocket channel to receive the results once the background task is complete.

---

## 📦 Containerization & Deployment

* **Containerization**: Use Docker to package both the Flask API and Redis cache into isolated containers.
* **Orchestration**: Manage local development dependencies (API, Redis, Celery) using a `docker-compose.yml` config.
* **Kubernetes (Planned)**: Scale API pods dynamically using Horizontal Pod Autoscalers (HPA) during high traffic.
