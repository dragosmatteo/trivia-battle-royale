import json
import re
import time
from fastapi import APIRouter, HTTPException, Depends, Request
from models.database import get_db
from models.schemas import GameSessionCreate, GameSessionResponse
from routers.auth import get_current_user
from services.game_manager import game_manager

router = APIRouter(prefix="/api/game", tags=["Game"])


# --- Rate limiting for PIN checks (anti brute-force) ---
_pin_check_attempts: dict[str, list[float]] = {}
PIN_CHECK_MAX = 10  # max attempts per minute per IP
PIN_CHECK_WINDOW = 60  # seconds


def _rate_limit_pin_check(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    if client_ip not in _pin_check_attempts:
        _pin_check_attempts[client_ip] = []

    _pin_check_attempts[client_ip] = [
        t for t in _pin_check_attempts[client_ip] if now - t < PIN_CHECK_WINDOW
    ]

    if len(_pin_check_attempts[client_ip]) >= PIN_CHECK_MAX:
        raise HTTPException(
            status_code=429,
            detail="Prea multe incercari. Asteptati un minut.",
        )

    _pin_check_attempts[client_ip].append(now)


def _require_professor(user: dict):
    if user["role"] != "professor":
        raise HTTPException(status_code=403, detail="Doar profesorii pot crea sesiuni")


@router.post("/create-session", response_model=GameSessionResponse)
async def create_session(req: GameSessionCreate, user: dict = Depends(get_current_user)):
    _require_professor(user)

    db = await get_db()

    # Verify the course belongs to this professor
    cursor = await db.execute(
        "SELECT id FROM courses WHERE id = ? AND professor_id = ?",
        (req.course_id, user["id"]),
    )
    if not await cursor.fetchone():
        await db.close()
        raise HTTPException(status_code=404, detail="Cursul nu a fost gasit")

    # Get questions for the course
    cursor = await db.execute(
        "SELECT * FROM questions WHERE course_id = ? ORDER BY RANDOM() LIMIT ?",
        (req.course_id, req.num_questions),
    )
    rows = await cursor.fetchall()
    if len(rows) < 3:
        await db.close()
        raise HTTPException(status_code=400, detail="Cursul nu are suficiente intrebari (minim 3). Generati mai intai intrebari.")

    questions = [
        {
            "question_text": r["question_text"],
            "options": json.loads(r["options"]),
            "correct_index": r["correct_index"],
            "explanation": r["explanation"],
            "difficulty": r["difficulty"],
        }
        for r in rows
    ]

    room_pin = game_manager.create_room(
        course_id=req.course_id,
        professor_id=user["id"],
        questions=questions,
        time_per_question=req.time_per_question,
    )

    cursor = await db.execute(
        "INSERT INTO game_sessions (pin_code, course_id, professor_id, status, time_per_question) VALUES (?, ?, ?, 'waiting', ?)",
        (room_pin, req.course_id, user["id"], req.time_per_question),
    )
    await db.commit()
    session_id = cursor.lastrowid
    await db.close()

    return GameSessionResponse(
        id=session_id, pin_code=room_pin, course_id=req.course_id,
        status="waiting", time_per_question=req.time_per_question,
        created_at="",
    )


@router.get("/sessions", response_model=list[GameSessionResponse])
async def list_sessions(user: dict = Depends(get_current_user)):
    db = await get_db()
    if user["role"] == "professor":
        cursor = await db.execute(
            "SELECT * FROM game_sessions WHERE professor_id = ? ORDER BY created_at DESC LIMIT 20",
            (user["id"],),
        )
    else:
        cursor = await db.execute("SELECT * FROM game_sessions ORDER BY created_at DESC LIMIT 20")
    rows = await cursor.fetchall()
    await db.close()

    return [
        GameSessionResponse(
            id=r["id"], pin_code=r["pin_code"], course_id=r["course_id"],
            status=r["status"], time_per_question=r["time_per_question"],
            created_at=str(r["created_at"]),
        )
        for r in rows
    ]


@router.get("/check-pin/{pin_code}")
async def check_pin(pin_code: str, request: Request):
    # Rate limit PIN checks to prevent brute-force
    _rate_limit_pin_check(request)

    # Validate PIN format
    if not re.match(r'^\d{6}$', pin_code):
        raise HTTPException(status_code=400, detail="Format PIN invalid (trebuie 6 cifre)")

    room = game_manager.get_room(pin_code)
    if not room:
        raise HTTPException(status_code=404, detail="Sesiunea nu exista")
    if room.status != "waiting":
        raise HTTPException(status_code=400, detail="Sesiunea a inceput deja")
    return {"valid": True, "players_count": len(room.players)}
