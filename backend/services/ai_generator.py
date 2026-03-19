import json
import random
from openai import AsyncOpenAI
from config import OPENAI_API_KEY
from services.pdf_processor import chunk_text

client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

SYSTEM_PROMPT = """Ești un expert în generarea de quiz-uri educaționale universitare. Primești un extras din materialul de curs și generezi întrebări cu răspunsuri multiple.

REGULI STRICTE:
1. Fiecare întrebare TREBUIE să fie responsabilă din textul furnizat.
2. Fiecare întrebare are exact 4 opțiuni de răspuns (A, B, C, D).
3. Exact UNA dintre opțiuni este corectă.
4. Explicația trebuie să facă referire la textul sursă.
5. Niveluri de dificultate: "easy" (reamintire factuală), "medium" (înțelegere), "hard" (analiză/aplicare).
6. TOATE întrebările și răspunsurile TREBUIE să fie în LIMBA ROMÂNĂ.
7. Opțiunile greșite trebuie să fie plauzibile dar clar incorecte.
8. Nu repeta întrebări similare.

Returnează DOAR JSON valid în acest format exact:
{
  "questions": [
    {
      "question_text": "Textul întrebării aici?",
      "options": ["Opțiunea A", "Opțiunea B", "Opțiunea C", "Opțiunea D"],
      "correct_index": 0,
      "explanation": "Explicația de ce acest răspuns este corect, bazat pe materialul de curs.",
      "difficulty": "medium"
    }
  ]
}"""


async def generate_questions_ai(
    course_text: str,
    num_questions: int = 5,
    difficulty: str | None = None,
    chapter_hint: str | None = None,
) -> list[dict]:
    """Generate questions using OpenAI API with RAG approach."""
    if not client:
        return _generate_fallback_questions(course_text, num_questions, difficulty)

    # RAG: select relevant chunks
    chunks = chunk_text(course_text)
    if chapter_hint and chunks:
        # Filter chunks that contain chapter-related keywords
        relevant = [c for c in chunks if chapter_hint.lower() in c.lower()]
        context_text = "\n\n".join(relevant[:3]) if relevant else "\n\n".join(chunks[:3])
    else:
        # Use a sample of chunks to stay within token limits
        selected = chunks[:5] if len(chunks) <= 5 else random.sample(chunks, 5)
        context_text = "\n\n".join(selected)

    difficulty_instruction = ""
    if difficulty:
        difficulty_instruction = f"\nGenerate ALL questions at '{difficulty}' difficulty level."

    user_prompt = f"""Based on the following course material, generate exactly {num_questions} multiple-choice questions.{difficulty_instruction}

COURSE MATERIAL:
\"\"\"
{context_text[:8000]}
\"\"\"

Generate {num_questions} questions. Return ONLY valid JSON."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=4000,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        questions = data.get("questions", [])

        # Validate structure
        validated = []
        for q in questions:
            if (
                isinstance(q.get("question_text"), str)
                and isinstance(q.get("options"), list)
                and len(q["options"]) == 4
                and isinstance(q.get("correct_index"), int)
                and 0 <= q["correct_index"] <= 3
            ):
                validated.append({
                    "question_text": q["question_text"],
                    "options": q["options"],
                    "correct_index": q["correct_index"],
                    "explanation": q.get("explanation", ""),
                    "difficulty": q.get("difficulty", difficulty or "medium"),
                })

        return validated[:num_questions]

    except Exception as e:
        print(f"AI generation error: {e}")
        return _generate_fallback_questions(course_text, num_questions, difficulty)


def _generate_fallback_questions(
    text: str, num_questions: int, difficulty: str | None
) -> list[dict]:
    """Generate better demo questions when no API key is available.
    Uses sentence-based extraction with randomized correct answer positions."""
    import re

    # Clean text and extract meaningful sentences
    clean = re.sub(r'\s+', ' ', text)
    raw_sentences = re.split(r'(?<=[.!?])\s+', clean)
    sentences = [s.strip() for s in raw_sentences if 40 < len(s.strip()) < 300 and any(c.isalpha() for c in s)]

    # Shuffle to get variety
    random.shuffle(sentences)

    difficulties = ["easy", "medium", "hard"]
    question_templates = [
        "Care dintre următoarele afirmații este corectă?",
        "Conform materialului de curs, care este varianta corectă?",
        "Care este afirmația adevărată din următoarele?",
        "Selectați varianta corectă conform cursului:",
        "Din perspectiva materialului studiat, care afirmație este validă?",
    ]

    wrong_templates = [
        "Această afirmație nu corespunde materialului de curs",
        "Informație incorectă - nu se regăsește în material",
        "Varianta nu este susținută de conținutul cursului",
        "Afirmație falsă conform documentației",
    ]

    questions = []
    used = set()

    for sentence in sentences:
        if len(questions) >= num_questions:
            break
        if sentence in used:
            continue
        used.add(sentence)

        # Truncate long sentences nicely
        display = sentence if len(sentence) <= 120 else sentence[:117] + "..."

        # Randomize correct answer position
        correct_idx = random.randint(0, 3)
        options = list(random.sample(wrong_templates, 3))
        options.insert(correct_idx, display)

        diff = difficulty or random.choice(difficulties)
        template = random.choice(question_templates)

        questions.append({
            "question_text": template,
            "options": options,
            "correct_index": correct_idx,
            "explanation": f"Răspunsul corect provine din materialul de curs.",
            "difficulty": diff,
        })

    # Pad with topic-based questions if needed
    topics = [
        ("Gamificarea în educație", "Gamificarea reprezintă aplicarea elementelor de design din jocuri în contexte educaționale",
         "Gamificarea se referă doar la jocuri video", "Gamificarea nu are efecte asupra motivației", "Gamificarea este interzisă în mediul academic"),
        ("Arhitectura Transformer", "Transformer-ul se bazează pe mecanismul de auto-atenție pentru procesarea secvențelor",
         "Transformer-ul procesează datele secvențial ca RNN", "Transformer-ul nu poate fi paralelizat", "Transformer-ul funcționează doar pentru imagini"),
        ("Battle Royale în evaluare", "Mecanismul Battle Royale introduce eliminarea progresivă a participanților",
         "Battle Royale înseamnă că toți jucătorii câștigă", "Nu există eliminare în formatul Battle Royale", "Battle Royale se aplică doar în jocuri video"),
        ("Procesarea Limbajului Natural", "NLP permite extragerea automată de informații din texte nestructurate",
         "NLP funcționează doar pentru limba engleză", "NLP nu poate genera întrebări automat", "NLP este identic cu OCR"),
        ("Retrieval Augmented Generation", "RAG combină căutarea în documente cu generarea de text prin modele de limbaj",
         "RAG nu folosește documente externe", "RAG generează text fără niciun context", "RAG este un protocol de rețea"),
    ]

    for topic_name, correct, w1, w2, w3 in topics:
        if len(questions) >= num_questions:
            break
        correct_idx = random.randint(0, 3)
        opts = [w1, w2, w3]
        opts.insert(correct_idx, correct)
        questions.append({
            "question_text": f"Ce afirmație este corectă despre {topic_name}?",
            "options": opts,
            "correct_index": correct_idx,
            "explanation": f"{correct}.",
            "difficulty": difficulty or random.choice(difficulties),
        })

    return questions[:num_questions]
