import json
from fastapi import APIRouter, HTTPException, Depends
from models.database import get_db
from models.schemas import GameSessionCreate, GameSessionResponse
from routers.auth import get_current_user
from services.game_manager import game_manager

router = APIRouter(prefix="/api/game", tags=["Game"])


@router.post("/create-session", response_model=GameSessionResponse)
async def create_session(req: GameSessionCreate, user: dict = Depends(get_current_user)):
    if user["role"] != "professor":
        raise HTTPException(status_code=403, detail="Doar profesorii pot crea sesiuni")

    db = await get_db()
    # Get questions for the course
    cursor = await db.execute(
        "SELECT * FROM questions WHERE course_id = ? ORDER BY RANDOM() LIMIT ?",
        (req.course_id, req.num_questions),
    )
    rows = await cursor.fetchall()
    if len(rows) < 3:
        await db.close()
        raise HTTPException(status_code=400, detail="Cursul nu are suficiente întrebări (minim 3). Generați mai întâi întrebări.")

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

    # Create game room in the GameManager singleton
    room_pin = game_manager.create_room(
        course_id=req.course_id,
        professor_id=user["id"],
        questions=questions,
        time_per_question=req.time_per_question,
    )

    # Save to database
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
async def check_pin(pin_code: str):
    room = game_manager.get_room(pin_code)
    if not room:
        raise HTTPException(status_code=404, detail="Sesiunea nu există")
    if room.status != "waiting":
        raise HTTPException(status_code=400, detail="Sesiunea a început deja")
    return {"valid": True, "players_count": len(room.players)}
