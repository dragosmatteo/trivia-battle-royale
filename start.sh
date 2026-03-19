#!/bin/bash
echo "============================================"
echo "   Trivia Battle Royale - Startup"
echo "============================================"

# Start backend
echo "[1/2] Starting Backend (FastAPI)..."
cd "$(dirname "$0")/backend"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

sleep 3

# Start frontend
echo "[2/2] Starting Frontend (Vite)..."
cd "$(dirname "$0")/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "============================================"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo "============================================"

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
