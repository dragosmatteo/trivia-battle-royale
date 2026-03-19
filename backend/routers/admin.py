"""
Admin router – Game history, statistics, and class/group management.
All endpoints require professor role.
"""

import json
import secrets
import string
from datetime import datetime, timezone
from hashlib import sha256

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional

from models.database import get_db
from routers.auth import get_current_user
from config import SECRET_KEY

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_professor(user: dict):
    if user["role"] != "professor":
        raise HTTPException(status_code=403, detail="Acces permis doar pentru profesori")


def _hash_password(password: str) -> str:
    return sha256((password + SECRET_KEY).encode()).hexdigest()


def _generate_password(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# ---------------------------------------------------------------------------
# Pydantic request / response models
# ---------------------------------------------------------------------------

class ClassCreate(BaseModel):
    group_name: str = Field(..., min_length=1, max_length=50)


class StudentCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str


class InviteLinkRequest(BaseModel):
    group_name: str


# ===========================================================================
# GAME HISTORY
# ===========================================================================

@router.get("/game-history")
async def list_game_history(
    course_id: Optional[int] = Query(None),
    user: dict = Depends(get_current_user),
):
    """List all finished game sessions for this professor."""
    _require_professor(user)

    db = await get_db()

    query = """
        SELECT gs.id, gs.pin_code, gs.course_id, gs.status, gs.time_per_question,
               gs.created_at, c.title as course_title,
               (SELECT COUNT(*) FROM game_results gr WHERE gr.session_id = gs.id) as player_count,
               (SELECT gr2.player_name FROM game_results gr2
                WHERE gr2.session_id = gs.id ORDER BY gr2.is_alive DESC, gr2.score DESC LIMIT 1) as winner
        FROM game_sessions gs
        LEFT JOIN courses c ON c.id = gs.course_id
        WHERE gs.professor_id = ? AND gs.status = 'finished'
    """
    params = [user["id"]]

    if course_id is not None:
        query += " AND gs.course_id = ?"
        params.append(course_id)

    query += " ORDER BY gs.created_at DESC"

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    await db.close()

    return [
        {
            "id": r["id"],
            "pin_code": r["pin_code"],
            "course_id": r["course_id"],
            "course_title": r["course_title"] or "Curs necunoscut",
            "status": r["status"],
            "time_per_question": r["time_per_question"],
            "created_at": str(r["created_at"]),
            "player_count": r["player_count"],
            "winner": r["winner"] or "-",
        }
        for r in rows
    ]


@router.get("/game-history/{session_id}")
async def get_game_detail(session_id: int, user: dict = Depends(get_current_user)):
    """Detailed view of a single game session."""
    _require_professor(user)

    db = await get_db()

    # Session info
    cursor = await db.execute(
        """SELECT gs.*, c.title as course_title
           FROM game_sessions gs
           LEFT JOIN courses c ON c.id = gs.course_id
           WHERE gs.id = ? AND gs.professor_id = ?""",
        (session_id, user["id"]),
    )
    session = await cursor.fetchone()
    if not session:
        await db.close()
        raise HTTPException(status_code=404, detail="Sesiunea nu a fost gasita")

    # Player results
    cursor = await db.execute(
        """SELECT * FROM game_results
           WHERE session_id = ?
           ORDER BY is_alive DESC, score DESC""",
        (session_id,),
    )
    results = await cursor.fetchall()
    await db.close()

    players = [
        {
            "id": r["id"],
            "player_name": r["player_name"],
            "user_id": r["user_id"],
            "score": r["score"],
            "is_alive": bool(r["is_alive"]),
            "eliminated_at_round": r["eliminated_at_round"],
            "finished_at": str(r["finished_at"]) if r["finished_at"] else None,
        }
        for r in results
    ]

    return {
        "id": session["id"],
        "pin_code": session["pin_code"],
        "course_id": session["course_id"],
        "course_title": session["course_title"] or "Curs necunoscut",
        "status": session["status"],
        "time_per_question": session["time_per_question"],
        "created_at": str(session["created_at"]),
        "player_count": len(players),
        "winner": players[0]["player_name"] if players else "-",
        "players": players,
    }


# ===========================================================================
# STATISTICS
# ===========================================================================

@router.get("/stats")
async def get_stats(user: dict = Depends(get_current_user)):
    """Overall statistics for the professor's dashboard."""
    _require_professor(user)

    db = await get_db()

    # Total games played
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM game_sessions WHERE professor_id = ? AND status = 'finished'",
        (user["id"],),
    )
    total_games = (await cursor.fetchone())["cnt"]

    # Total unique players
    cursor = await db.execute(
        """SELECT COUNT(DISTINCT gr.player_name) as cnt
           FROM game_results gr
           JOIN game_sessions gs ON gs.id = gr.session_id
           WHERE gs.professor_id = ?""",
        (user["id"],),
    )
    total_players = (await cursor.fetchone())["cnt"]

    # Average score
    cursor = await db.execute(
        """SELECT AVG(gr.score) as avg_score
           FROM game_results gr
           JOIN game_sessions gs ON gs.id = gr.session_id
           WHERE gs.professor_id = ?""",
        (user["id"],),
    )
    row = await cursor.fetchone()
    avg_score = round(row["avg_score"], 1) if row["avg_score"] else 0

    # Total questions generated
    cursor = await db.execute(
        """SELECT COUNT(*) as cnt FROM questions q
           JOIN courses c ON c.id = q.course_id
           WHERE c.professor_id = ?""",
        (user["id"],),
    )
    total_questions = (await cursor.fetchone())["cnt"]

    # Total courses
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM courses WHERE professor_id = ?",
        (user["id"],),
    )
    total_courses = (await cursor.fetchone())["cnt"]

    # Total students (in classes managed by this professor — or just all students)
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM users WHERE role = 'student'"
    )
    total_students = (await cursor.fetchone())["cnt"]

    # Recent 5 games
    cursor = await db.execute(
        """SELECT gs.id, gs.pin_code, gs.course_id, gs.created_at,
                  c.title as course_title,
                  (SELECT COUNT(*) FROM game_results gr WHERE gr.session_id = gs.id) as player_count,
                  (SELECT gr2.player_name FROM game_results gr2
                   WHERE gr2.session_id = gs.id ORDER BY gr2.is_alive DESC, gr2.score DESC LIMIT 1) as winner
           FROM game_sessions gs
           LEFT JOIN courses c ON c.id = gs.course_id
           WHERE gs.professor_id = ? AND gs.status = 'finished'
           ORDER BY gs.created_at DESC LIMIT 5""",
        (user["id"],),
    )
    recent_rows = await cursor.fetchall()

    recent_games = [
        {
            "id": r["id"],
            "pin_code": r["pin_code"],
            "course_id": r["course_id"],
            "course_title": r["course_title"] or "Curs necunoscut",
            "created_at": str(r["created_at"]),
            "player_count": r["player_count"],
            "winner": r["winner"] or "-",
        }
        for r in recent_rows
    ]

    await db.close()

    return {
        "total_games": total_games,
        "total_players": total_players,
        "total_questions": total_questions,
        "total_courses": total_courses,
        "total_students": total_students,
        "avg_score": avg_score,
        "recent_games": recent_games,
    }


# ===========================================================================
# CLASS / GROUP MANAGEMENT
# ===========================================================================

@router.get("/classes")
async def list_classes(user: dict = Depends(get_current_user)):
    """List all distinct classes/groups with student counts."""
    _require_professor(user)

    db = await get_db()
    cursor = await db.execute(
        """SELECT group_name, COUNT(*) as student_count
           FROM users
           WHERE role = 'student' AND group_name != ''
           GROUP BY group_name
           ORDER BY group_name"""
    )
    rows = await cursor.fetchall()
    await db.close()

    return [
        {"group_name": r["group_name"], "student_count": r["student_count"]}
        for r in rows
    ]


@router.post("/classes")
async def create_class(data: ClassCreate, user: dict = Depends(get_current_user)):
    """Create a new class (just records the group_name — students will be added later)."""
    _require_professor(user)

    db = await get_db()
    # Check if group already has students
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM users WHERE group_name = ? AND role = 'student'",
        (data.group_name,),
    )
    existing = (await cursor.fetchone())["cnt"]
    await db.close()

    # The group is implicitly created when students are assigned to it.
    # Return success regardless — idempotent.
    return {
        "group_name": data.group_name,
        "student_count": existing,
        "message": "Clasa a fost creata cu succes" if existing == 0 else "Clasa exista deja",
    }


@router.get("/classes/{group_name}/students")
async def list_students_in_class(group_name: str, user: dict = Depends(get_current_user)):
    """List students in a specific class, with per-student game stats."""
    _require_professor(user)

    db = await get_db()
    cursor = await db.execute(
        """SELECT id, username, email, full_name, group_name, created_at
           FROM users
           WHERE role = 'student' AND group_name = ?
           ORDER BY full_name""",
        (group_name,),
    )
    students = await cursor.fetchall()

    result = []
    for s in students:
        # Per-student stats from game_results (matching by player_name = username or full_name)
        cursor2 = await db.execute(
            """SELECT COUNT(*) as games_played,
                      COALESCE(AVG(score), 0) as avg_score,
                      COALESCE(SUM(is_alive), 0) as wins
               FROM game_results
               WHERE player_name = ? OR user_id = ?""",
            (s["username"], s["id"]),
        )
        stats = await cursor2.fetchone()

        result.append({
            "id": s["id"],
            "username": s["username"],
            "email": s["email"],
            "full_name": s["full_name"],
            "group_name": s["group_name"],
            "created_at": str(s["created_at"]),
            "games_played": stats["games_played"],
            "avg_score": round(stats["avg_score"], 1),
            "wins": stats["wins"],
        })

    await db.close()
    return result


@router.post("/classes/{group_name}/students")
async def add_student_to_class(
    group_name: str,
    data: StudentCreate,
    user: dict = Depends(get_current_user),
):
    """Create a new student account and assign to the class."""
    _require_professor(user)

    db = await get_db()

    # Check for duplicate username or email
    cursor = await db.execute(
        "SELECT id FROM users WHERE username = ? OR email = ?",
        (data.username, data.email),
    )
    if await cursor.fetchone():
        await db.close()
        raise HTTPException(status_code=400, detail="Username sau email deja existent")

    generated_password = _generate_password()
    hashed = _hash_password(generated_password)

    cursor = await db.execute(
        """INSERT INTO users (username, email, hashed_password, full_name, role, group_name)
           VALUES (?, ?, ?, ?, 'student', ?)""",
        (data.username, data.email, hashed, data.full_name, group_name),
    )
    await db.commit()
    student_id = cursor.lastrowid
    await db.close()

    return {
        "id": student_id,
        "username": data.username,
        "email": data.email,
        "full_name": data.full_name,
        "group_name": group_name,
        "generated_password": generated_password,
        "message": "Studentul a fost creat cu succes",
    }


class MoveStudentRequest(BaseModel):
    new_group: str = Field(..., min_length=1, max_length=50)


@router.put("/classes/{group_name}/students/{user_id}/move")
async def move_student_to_class(
    group_name: str,
    user_id: int,
    data: MoveStudentRequest,
    user: dict = Depends(get_current_user),
):
    """Move a student from one class to another."""
    _require_professor(user)

    db = await get_db()
    cursor = await db.execute(
        "SELECT id, group_name FROM users WHERE id = ? AND role = 'student'",
        (user_id,),
    )
    student = await cursor.fetchone()
    if not student:
        await db.close()
        raise HTTPException(status_code=404, detail="Studentul nu a fost găsit")

    if student["group_name"] != group_name:
        await db.close()
        raise HTTPException(status_code=400, detail="Studentul nu aparține acestei clase")

    await db.execute(
        "UPDATE users SET group_name = ? WHERE id = ?",
        (data.new_group, user_id),
    )
    await db.commit()
    await db.close()

    return {"message": f"Studentul a fost mutat în clasa {data.new_group}"}


@router.delete("/classes/{group_name}/students/{user_id}")
async def remove_student_from_class(
    group_name: str,
    user_id: int,
    user: dict = Depends(get_current_user),
):
    """Remove a student from a class (sets group_name to empty)."""
    _require_professor(user)

    db = await get_db()

    cursor = await db.execute(
        "SELECT id, group_name FROM users WHERE id = ? AND role = 'student'",
        (user_id,),
    )
    student = await cursor.fetchone()
    if not student:
        await db.close()
        raise HTTPException(status_code=404, detail="Studentul nu a fost gasit")

    if student["group_name"] != group_name:
        await db.close()
        raise HTTPException(status_code=400, detail="Studentul nu apartine acestei clase")

    await db.execute(
        "UPDATE users SET group_name = '' WHERE id = ?", (user_id,)
    )
    await db.commit()
    await db.close()

    return {"message": "Studentul a fost eliminat din clasa"}


@router.post("/invite-link")
async def generate_invite_link(
    data: InviteLinkRequest,
    user: dict = Depends(get_current_user),
):
    """Generate an invite code / link for a class."""
    _require_professor(user)

    # Simple invite code based on group_name — deterministic so it's stable
    code = secrets.token_urlsafe(8)
    # In a production system you'd store this in a table; for this demo
    # we derive a stable code from the group_name so it's reproducible.
    import hashlib
    stable_code = hashlib.md5(
        (data.group_name + SECRET_KEY).encode()
    ).hexdigest()[:10].upper()

    return {
        "group_name": data.group_name,
        "invite_code": stable_code,
        "invite_link": f"/register?class={stable_code}&group={data.group_name}",
        "message": f"Link-ul de invitatie pentru clasa {data.group_name}",
    }
