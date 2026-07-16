# NextRound Backend

Production-ready FastAPI backend skeleton for NextRound.

## Prerequisites

* Python >= 3.11
* [uv](https://github.com/astral-sh/uv) (Fast Python package installer and resolver)

## Setup and Installation

1. Sync dependencies and create virtual environment:
   ```bash
   uv sync
   ```

2. Copy environment defaults:
   ```bash
   cp .env.example .env
   ```

3. Run lint checks:
   ```bash
   uv run ruff check
   ```

4. Start the FastAPI development server:
   ```bash
   uv run uvicorn app.main:app --reload --port 8000
   ```

The health check endpoint will be available at `http://localhost:8000/health`.
