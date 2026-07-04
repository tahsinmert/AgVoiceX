#!/bin/bash
# run_backend.sh
# Script to run the backend natively on Apple Silicon with MLX and MPS acceleration

set -e

echo "🚀 Starting Voice Agent Backend natively on Apple Silicon..."

cd backend

echo "📦 Setting up Python virtual environment with 'uv' (Python 3.10 required for TTS)..."
if [ -d ".venv" ]; then
    echo "Removing existing virtual environment to ensure Python 3.10..."
    rm -rf .venv
fi
uv venv --python 3.10

echo "🔌 Activating virtual environment..."
source .venv/bin/activate

echo "⬇️ Installing dependencies (this may take a few minutes the first time)..."
uv pip install -e ".[voice]"

echo "⚙️ Setting up Environment Variables for Local Models..."
export HF_HOME="/Users/tahsinmert/Documents/Voice Agent Models/HuggingFace Hub"
export XDG_DATA_HOME="/Users/tahsinmert/Documents/Voice Agent Models"
export COQUI_TOS_AGREED=1

echo "🗄️ Configuring native backend service URLs..."
export POSTGRES_DB="${POSTGRES_DB:-voice_agent}"
export POSTGRES_USER="${POSTGRES_USER:-voice_agent}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-voice_agent}"
export POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
export BACKEND_PUBLIC_URL="${BACKEND_PUBLIC_URL:-http://localhost:8001}"
export BACKEND_CORS_ORIGINS="${BACKEND_CORS_ORIGINS:-http://localhost:3000,http://localhost:5678}"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"

if ! nc -z localhost "${POSTGRES_PORT}" >/dev/null 2>&1; then
    echo "❌ PostgreSQL is not reachable at localhost:${POSTGRES_PORT}."
    echo "   Start the infrastructure first:"
    echo "   docker compose up -d postgres redis qdrant"
    exit 1
fi

if ! nc -z localhost 6379 >/dev/null 2>&1; then
    echo "❌ Redis is not reachable at localhost:6379."
    echo "   Start the infrastructure first:"
    echo "   docker compose up -d postgres redis qdrant"
    exit 1
fi

if ! nc -z localhost 6333 >/dev/null 2>&1; then
    echo "❌ Qdrant is not reachable at localhost:6333."
    echo "   Start the infrastructure first:"
    echo "   docker compose up -d postgres redis qdrant"
    exit 1
fi

echo "🟢 Starting the Server..."
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
