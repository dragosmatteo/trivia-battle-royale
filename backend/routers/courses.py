import os
import json
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional
from models.database import get_db
from models.schemas import CourseResponse, GenerateRequest, QuestionResponse, QuestionSchema, MaterialResponse
from routers.auth import get_current_user
from services.pdf_processor import extract_text_from_pdf
from services.ai_generator import generate_questions_ai
from config import UPLOAD_DIR

router = APIRouter(prefix="/api/courses", tags=["Courses"])


# ──────────────────── Course CRUD ────────────────────

@router.post("/", response_model=CourseResponse)
async def create_course(
    title: str = Form(...),
    description: str = Form(""),
    pdf: UploadFile = File(None),
    user: dict = Depends(get_current_user),
):
    if user["role"] != "professor":
        raise HTTPException(status_code=403, detail="Doar profesorii pot crea cursuri")

    extracted = ""
    filename = None

    # If PDF provided, save and extract
    if pdf and pdf.filename:
        filename = f"{user['id']}_{pdf.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        content = await pdf.read()
        with open(filepath, "wb") as f:
            f.write(content)

        extracted = extract_text_from_pdf(filepath)

        # Also save as first material
        db = await get_db()
        cursor = await db.execute(
            "INSERT INTO courses (title, description, professor_id, pdf_filename, extracted_text) VALUES (?, ?, ?, ?, ?)",
            (title, description, user["id"], filename, extracted),
        )
        await db.commit()
        course_id = cursor.lastrowid

        # Save as material
        char_count = len(extracted)
        status = "ready" if char_count > 50 else "error"
        error_msg = "" if char_count > 50 else "Nu s-a putut extrage suficient text din PDF"
        await db.execute(
            "INSERT INTO course_materials (course_id, filename, original_name, file_size, extracted_text, char_count, status, error_message) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (course_id, filename, pdf.filename, len(content), extracted, char_count, status, error_msg),
        )
        await db.commit()
    else:
        # Create course without PDF (materials can be added later)
        db = await get_db()
        cursor = await db.execute(
            "INSERT INTO courses (title, description, professor_id, extracted_text) VALUES (?, ?, ?, ?)",
            (title, description, user["id"], ""),
        )
        await db.commit()
        course_id = cursor.lastrowid

    cursor = await db.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
    course = dict(await cursor.fetchone())
    await db.close()

    return CourseResponse(
        id=course["id"], title=course["title"], description=course["description"],
        professor_id=course["professor_id"], pdf_filename=course.get("pdf_filename"),
        created_at=str(course["created_at"]),
    )


@router.get("/", response_model=list[CourseResponse])
async def list_courses(user: dict = Depends(get_current_user)):
    db = await get_db()
    if user["role"] == "professor":
        cursor = await db.execute("SELECT * FROM courses WHERE professor_id = ? ORDER BY created_at DESC", (user["id"],))
    else:
        cursor = await db.execute("SELECT * FROM courses ORDER BY created_at DESC")

    rows = await cursor.fetchall()
    await db.close()

    return [
        CourseResponse(
            id=r["id"], title=r["title"], description=r["description"],
            professor_id=r["professor_id"], pdf_filename=r["pdf_filename"],
            created_at=str(r["created_at"]),
        )
        for r in rows
    ]


@router.delete("/{course_id}")
async def delete_course(course_id: int, user: dict = Depends(get_current_user)):
    """Delete a course and all its questions, materials, and game sessions."""
    if user["role"] != "professor":
        raise HTTPException(status_code=403, detail="Doar profesorii pot șterge cursuri")

    db = await get_db()

    # Verify course belongs to professor
    cursor = await db.execute("SELECT id FROM courses WHERE id = ? AND professor_id = ?", (course_id, user["id"]))
    if not await cursor.fetchone():
        await db.close()
        raise HTTPException(status_code=404, detail="Cursul nu a fost găsit")

    # Delete related data
    await db.execute("DELETE FROM questions WHERE course_id = ?", (course_id,))
    await db.execute("DELETE FROM course_materials WHERE course_id = ?", (course_id,))

    # Delete game results for sessions of this course
    cursor = await db.execute("SELECT id FROM game_sessions WHERE course_id = ?", (course_id,))
    session_ids = [r["id"] for r in await cursor.fetchall()]
    for sid in session_ids:
        await db.execute("DELETE FROM game_results WHERE session_id = ?", (sid,))
    await db.execute("DELETE FROM game_sessions WHERE course_id = ?", (course_id,))

    # Delete course itself
    await db.execute("DELETE FROM courses WHERE id = ?", (course_id,))

    # Delete uploaded files
    cursor = await db.execute("SELECT filename FROM course_materials WHERE course_id = ?", (course_id,))
    for r in await cursor.fetchall():
        filepath = os.path.join(UPLOAD_DIR, r["filename"])
        if os.path.exists(filepath):
            os.remove(filepath)

    await db.commit()
    await db.close()
    return {"message": "Cursul a fost șters complet"}


# ──────────────────── Materials (Knowledge Base) ────────────────────

@router.get("/{course_id}/materials", response_model=list[MaterialResponse])
async def list_materials(course_id: int, user: dict = Depends(get_current_user)):
    """List all uploaded materials for a course."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM course_materials WHERE course_id = ? ORDER BY created_at DESC",
        (course_id,),
    )
    rows = await cursor.fetchall()
    await db.close()

    return [
        MaterialResponse(
            id=r["id"], course_id=r["course_id"], original_name=r["original_name"],
            file_size=r["file_size"], char_count=r["char_count"],
            status=r["status"], error_message=r["error_message"] or "",
            created_at=str(r["created_at"]),
        )
        for r in rows
    ]


@router.post("/{course_id}/materials", response_model=MaterialResponse)
async def upload_material(
    course_id: int,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload a new material (PDF) to the course knowledge base."""
    if user["role"] != "professor":
        raise HTTPException(status_code=403, detail="Doar profesorii pot adăuga materiale")

    db = await get_db()

    # Verify course belongs to professor
    cursor = await db.execute("SELECT id FROM courses WHERE id = ? AND professor_id = ?", (course_id, user["id"]))
    if not await cursor.fetchone():
        await db.close()
        raise HTTPException(status_code=404, detail="Cursul nu a fost găsit")

    # Save file
    filename = f"{user['id']}_{course_id}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    file_size = len(content)
    with open(filepath, "wb") as f:
        f.write(content)

    # Extract text
    extracted = extract_text_from_pdf(filepath)
    char_count = len(extracted)

    if char_count < 50:
        status = "error"
        error_msg = "Nu s-a putut extrage suficient text. Verificați dacă PDF-ul conține text selectabil."
    else:
        status = "ready"
        error_msg = ""

    # Save material record
    cursor = await db.execute(
        "INSERT INTO course_materials (course_id, filename, original_name, file_size, extracted_text, char_count, status, error_message) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (course_id, filename, file.filename, file_size, extracted, char_count, status, error_msg),
    )
    await db.commit()
    mat_id = cursor.lastrowid

    # Update course's aggregated extracted_text
    await _rebuild_course_text(db, course_id)
    await db.commit()
    await db.close()

    return MaterialResponse(
        id=mat_id, course_id=course_id, original_name=file.filename,
        file_size=file_size, char_count=char_count,
        status=status, error_message=error_msg,
        created_at="",
    )


@router.delete("/{course_id}/materials/{material_id}")
async def delete_material(course_id: int, material_id: int, user: dict = Depends(get_current_user)):
    """Remove a material from the course knowledge base."""
    if user["role"] != "professor":
        raise HTTPException(status_code=403, detail="Doar profesorii pot șterge materiale")

    db = await get_db()

    # Get filename to delete physical file
    cursor = await db.execute("SELECT filename FROM course_materials WHERE id = ? AND course_id = ?", (material_id, course_id))
    row = await cursor.fetchone()
    if row:
        filepath = os.path.join(UPLOAD_DIR, row["filename"])
        if os.path.exists(filepath):
            os.remove(filepath)

    await db.execute("DELETE FROM course_materials WHERE id = ? AND course_id = ?", (material_id, course_id))
    await db.commit()

    # Rebuild course text without this material
    await _rebuild_course_text(db, course_id)
    await db.commit()
    await db.close()

    return {"message": "Materialul a fost șters"}


@router.get("/{course_id}/knowledge-stats")
async def knowledge_stats(course_id: int, user: dict = Depends(get_current_user)):
    """Get stats about the course's knowledge base."""
    db = await get_db()
    cursor = await db.execute("SELECT extracted_text FROM courses WHERE id = ?", (course_id,))
    course = await cursor.fetchone()

    cursor = await db.execute(
        "SELECT COUNT(*) as total, SUM(char_count) as total_chars, SUM(file_size) as total_size FROM course_materials WHERE course_id = ? AND status = 'ready'",
        (course_id,),
    )
    stats = dict(await cursor.fetchone())

    cursor = await db.execute("SELECT COUNT(*) as cnt FROM questions WHERE course_id = ?", (course_id,))
    q_count = (await cursor.fetchone())["cnt"]

    await db.close()

    total_text = len(course["extracted_text"]) if course and course["extracted_text"] else 0

    return {
        "materials_count": stats["total"] or 0,
        "total_characters": total_text,
        "total_file_size": stats["total_size"] or 0,
        "questions_count": q_count,
        "estimated_pages": total_text // 2000 if total_text else 0,
    }


async def _rebuild_course_text(db, course_id: int):
    """Aggregate all materials' text into the course's extracted_text field."""
    cursor = await db.execute(
        "SELECT extracted_text FROM course_materials WHERE course_id = ? AND status = 'ready' ORDER BY created_at ASC",
        (course_id,),
    )
    rows = await cursor.fetchall()
    aggregated = "\n\n--- Material nou ---\n\n".join(
        r["extracted_text"] for r in rows if r["extracted_text"]
    )
    await db.execute(
        "UPDATE courses SET extracted_text = ? WHERE id = ?",
        (aggregated, course_id),
    )


# ──────────────────── Questions ────────────────────

@router.post("/generate-questions", response_model=list[QuestionResponse])
async def generate_questions(req: GenerateRequest, user: dict = Depends(get_current_user)):
    if user["role"] != "professor":
        raise HTTPException(status_code=403, detail="Doar profesorii pot genera întrebări")

    db = await get_db()
    cursor = await db.execute("SELECT * FROM courses WHERE id = ? AND professor_id = ?", (req.course_id, user["id"]))
    course = await cursor.fetchone()
    if not course:
        await db.close()
        raise HTTPException(status_code=404, detail="Cursul nu a fost găsit")

    course = dict(course)
    if not course["extracted_text"] or len(course["extracted_text"]) < 50:
        await db.close()
        raise HTTPException(status_code=400, detail="Cursul nu conține suficient text. Încarcă materiale (PDF-uri) mai întâi.")

    # Generate questions via AI
    questions = await generate_questions_ai(
        course_text=course["extracted_text"],
        num_questions=req.num_questions,
        difficulty=req.difficulty.value if req.difficulty else None,
        chapter_hint=req.chapter_hint,
    )

    # Save to database
    saved = []
    for q in questions:
        cursor = await db.execute(
            "INSERT INTO questions (course_id, question_text, options, correct_index, explanation, difficulty) VALUES (?, ?, ?, ?, ?, ?)",
            (req.course_id, q["question_text"], json.dumps(q["options"]), q["correct_index"], q["explanation"], q["difficulty"]),
        )
        q_id = cursor.lastrowid
        saved.append(QuestionResponse(
            id=q_id, course_id=req.course_id, question_text=q["question_text"],
            options=q["options"], correct_index=q["correct_index"],
            explanation=q["explanation"], difficulty=q["difficulty"],
        ))

    await db.commit()
    await db.close()
    return saved


@router.get("/{course_id}/questions", response_model=list[QuestionResponse])
async def get_questions(course_id: int, difficulty: str | None = None, user: dict = Depends(get_current_user)):
    db = await get_db()

    if difficulty:
        cursor = await db.execute(
            "SELECT * FROM questions WHERE course_id = ? AND difficulty = ? ORDER BY created_at DESC",
            (course_id, difficulty),
        )
    else:
        cursor = await db.execute(
            "SELECT * FROM questions WHERE course_id = ? ORDER BY created_at DESC",
            (course_id,),
        )

    rows = await cursor.fetchall()
    await db.close()

    return [
        QuestionResponse(
            id=r["id"], course_id=r["course_id"], question_text=r["question_text"],
            options=json.loads(r["options"]), correct_index=r["correct_index"],
            explanation=r["explanation"], difficulty=r["difficulty"],
        )
        for r in rows
    ]


@router.post("/{course_id}/questions", response_model=QuestionResponse)
async def create_question_manual(course_id: int, q: QuestionSchema, user: dict = Depends(get_current_user)):
    """Create a question manually."""
    if user["role"] != "professor":
        raise HTTPException(status_code=403, detail="Doar profesorii pot adăuga întrebări")

    db = await get_db()
    cursor = await db.execute("SELECT id FROM courses WHERE id = ? AND professor_id = ?", (course_id, user["id"]))
    if not await cursor.fetchone():
        await db.close()
        raise HTTPException(status_code=404, detail="Cursul nu a fost găsit")

    cursor = await db.execute(
        "INSERT INTO questions (course_id, question_text, options, correct_index, explanation, difficulty) VALUES (?, ?, ?, ?, ?, ?)",
        (course_id, q.question_text, json.dumps(q.options), q.correct_index, q.explanation, q.difficulty.value),
    )
    await db.commit()
    q_id = cursor.lastrowid
    await db.close()

    return QuestionResponse(
        id=q_id, course_id=course_id, question_text=q.question_text,
        options=q.options, correct_index=q.correct_index,
        explanation=q.explanation, difficulty=q.difficulty.value,
    )


@router.put("/{course_id}/questions/{question_id}", response_model=QuestionResponse)
async def update_question(course_id: int, question_id: int, q: QuestionSchema, user: dict = Depends(get_current_user)):
    """Edit an existing question."""
    if user["role"] != "professor":
        raise HTTPException(status_code=403, detail="Doar profesorii pot edita întrebări")

    db = await get_db()
    cursor = await db.execute("SELECT id FROM questions WHERE id = ? AND course_id = ?", (question_id, course_id))
    if not await cursor.fetchone():
        await db.close()
        raise HTTPException(status_code=404, detail="Întrebarea nu a fost găsită")

    await db.execute(
        "UPDATE questions SET question_text = ?, options = ?, correct_index = ?, explanation = ?, difficulty = ? WHERE id = ?",
        (q.question_text, json.dumps(q.options), q.correct_index, q.explanation, q.difficulty.value, question_id),
    )
    await db.commit()
    await db.close()

    return QuestionResponse(
        id=question_id, course_id=course_id, question_text=q.question_text,
        options=q.options, correct_index=q.correct_index,
        explanation=q.explanation, difficulty=q.difficulty.value,
    )


@router.delete("/{course_id}/questions/{question_id}")
async def delete_question(course_id: int, question_id: int, user: dict = Depends(get_current_user)):
    if user["role"] != "professor":
        raise HTTPException(status_code=403, detail="Doar profesorii pot șterge întrebări")

    db = await get_db()
    await db.execute("DELETE FROM questions WHERE id = ? AND course_id = ?", (question_id, course_id))
    await db.commit()
    await db.close()
    return {"message": "Întrebarea a fost ștearsă"}
