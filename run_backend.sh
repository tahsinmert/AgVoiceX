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
uv pip install -e .

echo "⚙️ Setting up Environment Variables for Local Models..."
export HF_HOME="/Users/tahsinmert/Documents/Voice Agent Models/HuggingFace Hub"
export XDG_DATA_HOME="/Users/tahsinmert/Documents/Voice Agent Models"
export COQUI_TOS_AGREED=1

echo "🟢 Starting the Server..."
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
