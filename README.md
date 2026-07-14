# AI Resume Analyzer

AI Resume Analyzer is an intelligent, automated candidate resume analysis and evaluation platform built with an enterprise-grade modular architecture. It leverages artificial intelligence and natural language processing to extract skills, evaluate job role compatibility, quantify resume match scores, and provide actionable feedback for job seekers and recruiters.

---

## 🏗️ High-Level Architecture

```text
Angular Frontend
        │
        │ HTTP / REST API
        ▼
Flask Backend (POST /api/v1/resumes/upload)
        │
        ▼
ResumeAnalysisPipeline (Orchestration Layer)
        ├─► UploadService / FileStorageService (Validate & write file to disk)
        ├─► PdfParserService (Planned: Extract text using PyMuPDF)
        ├─► PromptBuilderService (Planned: Build prompt layout)
        ├─► OpenAIService (Planned: Connect to ChatCompletion API)
        └─► AnalysisFormatterService (Planned: Normalize analysis response)
        │
        ▼
Standardized JSON Response
        │
        ▼
Angular Dashboard (Planned)
```


---

## 🛠️ Technology Stack

| Component | Technologies & Tools | Status / Notes |
| :--- | :--- | :--- |
| **Frontend** | Angular 19, TypeScript, RxJS, Angular Material, SCSS | Implementation planned |
| **Backend** | Python, Flask, Flask REST API, PyMuPDF, Flask-CORS, python-dotenv | Active, health endpoint verified |
| **AI Engine** | OpenAI API, Prompt Engineering | Integration planned |
| **Version Control** | Git, GitHub | Repository initialized |
| **Deployment** | Frontend $\rightarrow$ Vercel, Backend $\rightarrow$ Render | Planned |

---

## 📂 Project Folder Structure

```text
ai-resume-analyzer/
├── frontend/                 # Angular 19 client application
│   ├── src/                  # Application source code
│   │   ├── app/              # Main application module
│   │   │   ├── core/         # Core utilities & singleton configs
│   │   │   │   ├── http/     # HTTP api service, interceptor, and endpoints mapping
│   │   │   │   ├── services/
│   │   │   │   ├── interceptors/
│   │   │   │   ├── guards/
│   │   │   │   ├── constants/
│   │   │   │   ├── utils/
│   │   │   │   └── models/
│   │   │   ├── shared/       # Shared UI presentation files
│   │   │   │   ├── components/
│   │   │   │   ├── directives/
│   │   │   │   ├── pipes/
│   │   │   │   └── interfaces/
│   │   │   ├── features/     # Feature-scoped modules (with README checklists)
│   │   │   │   ├── home/
│   │   │   │   ├── upload/
│   │   │   │   ├── analysis/
│   │   │   │   ├── history/
│   │   │   │   └── settings/
│   │   │   └── layouts/      # Main and Auth layout structures
│   │   │       ├── main-layout/
│   │   │       └── auth-layout/
│   │   └── assets/           # Static images, styles, and custom typography assets
│   ├── angular.json          # Angular CLI configuration
│   ├── package.json          # Frontend dependency manifest
│   └── ...
│
├── backend/                  # Flask REST API server
│   ├── app/                  # Core application package (Factory pattern)
│   │   ├── api/              # API blueprint controllers and route handlers
│   │   ├── services/         # Business logic services
│   │   ├── utils/            # Shared helper functions and utilities
│   │   ├── middleware/       # Custom request interceptors and CORS configs
│   │   ├── prompts/          # OpenAI prompts templates
│   │   ├── models/           # Data models/schema schemas
│   │   ├── exceptions/       # Custom Exceptions (InvalidResume, UnsupportedFile, etc.)
│   │   ├── schemas/          # Centralized Pydantic validation schemas placeholders
│   │   ├── extensions/       # Flask integrations loaders (CORS, logging, db initializations)
│   │   ├── constants/        # Centralized app constants (limits, prefixes)
│   │   └── __init__.py       # Application factory initialization
│   │
│   ├── uploads/              # Local storage folder for uploaded resumes (Git-ignored)
│   ├── logs/                 # Application log directory (Git-ignored)
│   ├── tests/                # Unit and integration tests
│   ├── .venv/                # Python 3.9.6 virtual environment (Git-ignored)
│   ├── .env                  # Active environment variables configuration
│   ├── .env.example          # Environment variables template file
│   ├── requirements.txt      # Python dependencies manifest
│   └── run.py                # Server entry point
│
├── docs/                     # API and system documentation
├── README.md                 # Project overview and onboarding instructions
├── Implementation.md         # Active verification log and architecture plan
└── .gitignore                # Version control exclusion rules
```

---

## 🚀 Setup Instructions

### Prerequisites
* **Python**: 3.9 or newer (installed version: `3.9.6`)
* **Node.js**: LTS version (v22.x recommended, installed version: `v22.14.0`)
* **npm**: 10.x or newer (installed version: `10.9.2`)
* **Angular CLI**: 19.x or newer (installed version: `19.1.6`)
* **Git**: Any modern version (installed version: `2.43.0`)

### 1. Repository Setup
```bash
git clone <repository-url>
cd ai-resume-analyser
```

### 2. Backend Setup
```bash
cd backend
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment variables file
cp .env.example .env
```

### 3. Frontend Setup
```bash
cd ../frontend
# Install Node dependencies
npm install
```

---

## 🏃 Running the Application

To run the application locally, open two separate terminal windows or tabs:

### Tab A: Start the Flask Backend
```bash
cd backend
source .venv/bin/activate
python run.py
```
*The backend REST API will run at `http://localhost:5001`.*

### Tab B: Start the Angular Frontend
```bash
cd frontend
npm start
```
*The Angular app will compile and serve at `http://localhost:4200`.*


---

## 📜 License

This project is licensed under the MIT License.

---

## 📖 Technical Reference Guides

For detailed specifications and architectural blueprints, refer to the following design guides:
* **[API Response Format](file:///Users/reddykarthik/Desktop/ai-resume-analyser/docs/API_Response_Format.md)**: Standard JSON envelopes contract.
* **[Error Handling Strategy](file:///Users/reddykarthik/Desktop/ai-resume-analyser/docs/Error_Handling.md)**: Global exception logging and UX alerts strategy.
* **[Coding Guidelines & Standards](file:///Users/reddykarthik/Desktop/ai-resume-analyser/docs/Coding_Guidelines.md)**: Project styles, Conventional Commits, and naming guidelines.
* **[Logging Strategy](file:///Users/reddykarthik/Desktop/ai-resume-analyser/docs/Logging_Strategy.md)**: Request tracing and Rotating File handler rules.
* **[Security Baseline](file:///Users/reddykarthik/Desktop/ai-resume-analyser/docs/Security.md)**: CORS limitations, payload sizes checks, and upload safety configurations.
* **[Scalability Strategy](file:///Users/reddykarthik/Desktop/ai-resume-analyser/docs/Scalability.md)**: Redis caching models, Celery async task queue setups, and cloud deployments.

