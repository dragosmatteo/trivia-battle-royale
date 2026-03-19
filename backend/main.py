import asyncio
import os
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models.database import init_db
from routers import auth, courses, game, admin
from services.game_manager import game_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("Database initialized")
    yield


app = FastAPI(
    title="Trivia Battle Royale API",
    description="Educational quiz game with AI-generated questions and Battle Royale mechanics",
    version="1.0.0",
    lifespan=lifespan,
)

# --- Security: CORS ---
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# --- Security: Rate limiting (simple in-memory) ---
_rate_limit: dict[str, list[float]] = {}
RATE_LIMIT_MAX = 60  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    import time
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    if client_ip not in _rate_limit:
        _rate_limit[client_ip] = []

    # Clean old entries
    _rate_limit[client_ip] = [t for t in _rate_limit[client_ip] if now - t < RATE_LIMIT_WINDOW]

    if len(_rate_limit[client_ip]) >= RATE_LIMIT_MAX:
        return JSONResponse(status_code=429, content={"detail": "Prea multe cereri. Încercați din nou în curând."})

    _rate_limit[client_ip].append(now)
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response


# --- Security: Input sanitization ---
def sanitize_input(value: str) -> str:
    """Remove potentially dangerous characters from user input."""
    return re.sub(r'[<>"\';]', '', value.strip())


# Include routers
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(game.router)
app.include_router(admin.router)


# --- WebSocket Endpoints ---

@app.websocket("/ws/professor/{pin}")
async def professor_websocket(websocket: WebSocket, pin: str):
    # Validate PIN format
    if not re.match(r'^\d{6}$', pin):
        await websocket.close(code=4001)
        return

    await websocket.accept()

    room = game_manager.get_room(pin)
    if not room:
        await websocket.send_json({"type": "error", "message": "Sesiunea nu există"})
        await websocket.close()
        return

    await game_manager.connect_professor(pin, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action", "")

            if action == "start_game":
                asyncio.create_task(game_manager.start_game(pin))
            elif action == "next_question":
                room = game_manager.get_room(pin)
                if room:
                    asyncio.create_task(game_manager._next_question(room))
            elif action == "end_game":
                room = game_manager.get_room(pin)
                if room:
                    asyncio.create_task(game_manager._end_game(room))

    except WebSocketDisconnect:
        room = game_manager.get_room(pin)
        if room:
            room.professor_ws = None


@app.websocket("/ws/player/{pin}/{nickname}")
async def player_websocket(websocket: WebSocket, pin: str, nickname: str):
    # Validate inputs
    if not re.match(r'^\d{6}$', pin):
        await websocket.close(code=4001)
        return
    if len(nickname) < 2 or len(nickname) > 20:
        await websocket.close(code=4002)
        return
    # Sanitize nickname
    nickname = re.sub(r'[<>"\';]', '', nickname.strip())

    await websocket.accept()

    connected = await game_manager.connect_player(pin, nickname, websocket)
    if not connected:
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action", "")

            if action == "answer":
                selected = data.get("selected_option")
                if isinstance(selected, int) and 0 <= selected <= 3:
                    await game_manager.submit_answer(pin, nickname, selected)

    except WebSocketDisconnect:
        await game_manager.disconnect_player(pin, nickname)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Trivia Battle Royale API is running"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
