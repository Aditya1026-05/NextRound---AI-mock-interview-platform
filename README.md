# NextRound — AI-Powered Mock Interview Platform

NextRound is a production-grade mock interview simulator designed to help engineers prepare for coding, behavioral, system design, and machine learning rounds. It features adaptive AI interviewers, resume-aware questioning, real-time code sandboxes, and long-term learning roadmaps.

---

## 📂 Project Architecture & Directories

* **`artifacts/interviewos/`**: React, Vite, Tailwind CSS v4, and Zustand state-managed frontend.
* **`backend/`**: FastAPI, SQLAlchemy 2.0 (Async), PostgreSQL, Redis, LiteLLM, and LangGraph-backed agent workspace.

---

## 🛠 Prerequisites

Ensure you have the following installed on your system:
* **Node.js** (v18.x or v20.x recommended) & **pnpm**
* **Python** (>= 3.11) & **[uv](https://github.com/astral-sh/uv)** (Python package installer)
* **Docker & Docker Compose** (for localized databases and third-party integrations)

---

## 🚀 Getting Started

### 1. Backend Setup & Run

Navigate to the backend directory:
```bash
cd backend
```

1. **Synchronize Virtual Environment & Dependencies**:
   ```bash
   uv sync --all-extras
   ```

2. **Copy Environment Defaults**:
   ```bash
   cp .env.example .env
   ```

3. **Verify Code Quality (Linting)**:
   ```bash
   uv run ruff check
   ```

4. **Start the FastAPI Development Server**:
   ```bash
   uv run uvicorn app.main:app --reload --port 8000
   ```
   * The backend health check endpoint will run at: [http://localhost:8000/health](http://localhost:8000/health)

---

### 2. Frontend Setup & Run

Navigate to the frontend directory:
```bash
cd artifacts/interviewos
```

1. **Install Frontend Dependencies**:
   ```bash
   pnpm install
   ```

2. **Start the Vite Development Server**:
   ```bash
   pnpm run dev
   ```
   * The React Web App will be available at: [http://localhost:5173](http://localhost:5173)

---

### 3. Alternate Setup: Running the entire stack via Docker

If you prefer to run Postgres, Redis, and the web backend in isolated containers:

Navigate to the backend directory:
```bash
cd backend
```

1. **Launch Containers**:
   ```bash
   docker-compose up --build
   ```
   * This binds Postgres to port `5432`, Redis to `6379`, and the FastAPI app to `8000`.
