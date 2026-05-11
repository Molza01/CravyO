#!/bin/bash
cd "$(dirname "$0")/backend"
echo "🚀 Starting Zyndai Backend..."
pip install -r requirements.txt -q
uvicorn main:app --reload --port 8000
