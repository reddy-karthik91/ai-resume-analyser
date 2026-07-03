# AI Resume Analyzer

AI Resume Analyzer is an intelligent, automated candidate resume analysis and evaluation platform built with enterprise-grade modular architecture. It leverages artificial intelligence and natural language processing to extract skills, evaluate job role compatibility, quantify resume match scores, and provide actionable feedback for job seekers and recruiters.

---

## 🏗️ High-Level Architecture

```
+-------------------------------------------------------+
|                    Client Layer                       |
|         Angular Frontend (Single Page App)             |
+---------------------------+---------------------------+
                            | HTTP / REST API
                            v
+-------------------------------------------------------+
|                    API Layer                          |
|             Flask Backend (Python 3.12)               |
+---------------------------+---------------------------+
                            |
            +---------------+---------------+
            |                               |
            v                               v
+-----------------------+       +-----------------------+
|   Parsing & NLP       |       |    AI Inference Engine|
|  Resume Extractor     |       |  Google Gemini API    |
+-----------------------+       +-----------------------+
```

---

## 🛠️ Technology Stack

* **Frontend**: Angular CLI 16+, TypeScript, HTML5, SCSS/CSS
* **Backend**: Python 3.12, Flask, Virtualenv (`.venv`)
* **AI / Parsing Engine**: Google Gemini AI API, PyPDF2 / pdfplumber (Planned)
* **DevOps & Tooling**: Git, Docker Desktop (Optional), Google Cloud CLI (Optional)

---

## 📂 Project Folder Structure

```
ai-resume-analyzer/
│
├── frontend/             # Angular client application
├── backend/              # Flask REST API server and AI engine
│   ├── .venv/            # Python 3.12 virtual environment (git-ignored)
│   └── requirements.txt  # Backend Python dependencies
├── docs/                 # Project architecture & API documentation
├── .gitignore            # Version control exclusion rules
└── README.md             # Project overview and instructions
```

---

## 🚀 Setup Instructions

### Prerequisites
* **Python**: 3.12 or newer
* **Node.js**: LTS version (v20.x or v22.x recommended)
* **npm**: 10.x or newer
* **Angular CLI**: 16.x or newer
* **Git**: 2.40+

### 1. Repository Setup
```bash
git clone <repository-url>
cd "ai resume analyser"
```

### 2. Backend Setup
```bash
cd backend
# Create virtual environment (if not already created)
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Upgrade pip and install dependencies
pip install --upgrade pip
# pip install -r requirements.txt (Placeholder for application code phase)
```

### 3. Frontend Setup
```bash
cd ../frontend
# Angular project initialization placeholder
# npm install
# ng serve
```

---

## 📜 License

This project is licensed under the MIT License.
