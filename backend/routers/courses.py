import os
import json
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from models.database import get_db
from models.schemas import CourseResponse, GenerateRequest, QuestionResponse, QuestionSchema
from routers.auth import get_current_user
from services.pdf_processor import extract_text_from_pdf
from services.ai_generator import generate_questions_ai
from config import UPLOAD_DIR

router = APIRouter(prefix="/api/courses", tags=["Courses"])


@router.post("/", response_model=CourseResponse)
async def create_course(
    title: str = Form(...),
    description: str = Form(""),
    pdf: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    if user["role"] != "professor":
        raise HTTPException(status_code=403, detail="Doar profesorii pot crea cursuri")

    # Save PDF
    filename = f"{user['id']}_{pdf.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    content = await pdf.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Extract text
    extracted = extract_text_from_pdf(filepath)
    if not extracted or len(extracted) < 50:
        raise HTTPException(status_code=400, detail="Nu s-a putut extrage text din PDF")

    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO courses (title, description, professor_id, pdf_filename, extracted_text) VALUES (?, ?, ?, ?, ?)",
        (title, description, user["id"], filename, extracted),
    )
    await db.commit()
    course_id = cursor.lastrowid

    cursor = await db.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
    course = dict(await cursor.fetchone())
    await db.close()

    return CourseResponse(
        id=course["id"], title=course["title"], description=course["description"],
        professor_id=course["professor_id"], pdf_filename=course["pdf_filename"],
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
    if not course["extracted_text"]:
        await db.close()
        raise HTTPException(status_code=400, detail="Cursul nu conține text extras")

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
    """Create a question manually (professor types it)."""
    if user["role"] != "professor":
        raise HTTPException(status_code=403, detail="Doar profesorii pot adăuga întrebări")

    db = await get_db()
    # Verify course belongs to professor
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
