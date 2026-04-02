import json
import random
from openai import AsyncOpenAI
from config import OPENAI_API_KEY
from services.pdf_processor import chunk_text

client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

SYSTEM_PROMPT = """Ești un expert în generarea de quiz-uri educaționale universitare cu nivel academic ridicat. Primești un extras din materialul de curs și generezi întrebări cu răspunsuri multiple riguroase și tehnice.

REGULI STRICTE:
1. Fiecare întrebare TREBUIE să fie derivată direct din textul furnizat, referind concepte, teoreme sau principii specifice prezente în material.
2. Fiecare întrebare are exact 4 opțiuni de răspuns (A, B, C, D).
3. Exact UNA dintre opțiuni este corectă.
4. Explicația TREBUIE să aibă cel puțin 2-3 propoziții: prima propoziție explică de ce răspunsul corect este corect, a doua propoziție conectează răspunsul la conceptul mai larg din material, iar a treia (opțional) menționează secțiunea, pagina sau contextul din sursă dacă este identificabil.
5. Niveluri de dificultate:
   - "easy": reamintire factuală, definiții, identificare de termeni sau concepte de bază
   - "medium": înțelegerea relațiilor dintre concepte, compararea abordărilor, aplicarea cunoștințelor în situații date
   - "hard": analiză critică, sinteză, evaluare, raționament în mai mulți pași, integrarea mai multor concepte
6. TOATE întrebările și răspunsurile TREBUIE să fie în LIMBA ROMÂNĂ.
7. Opțiunile greșite (distractori) TREBUIE să fie plauzibile academic: bazate pe concepții greșite frecvente, pe confuzii între termeni similari, sau pe aplicări incorecte ale unor principii reale. NU folosi variante evident false sau generice.
8. Nu repeta întrebări similare. Variază tipul de întrebare folosind formule diferite:
   - "Care din următoarele..." (identificare)
   - "Ce reprezintă..." (definiție)
   - "De ce..." (cauzalitate, motivație)
   - "Care este diferența dintre... și...?" (comparație)
   - "În ce context se aplică...?" (aplicare)
   - "Care este rolul... în...?" (funcție, scop)
   - "Cum influențează... asupra...?" (relație de cauzalitate)
   - "Care dintre afirmațiile de mai jos este incorectă?" (negație, tip tricky)
9. Întrebările trebuie să testeze înțelegerea profundă, nu memorarea superficială. Fă referire la concepte, algoritmi, mecanisme sau principii numite explicit în text.

Returnează DOAR JSON valid în acest format exact:
{
  "questions": [
    {
      "question_text": "Textul întrebării aici?",
      "options": ["Opțiunea A", "Opțiunea B", "Opțiunea C", "Opțiunea D"],
      "correct_index": 0,
      "explanation": "Explicația detaliată (min. 2-3 propoziții) de ce acest răspuns este corect, cu referire la conceptul din materialul de curs și, dacă este posibil, la secțiunea sau contextul relevant.",
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
        diff_descriptions = {
            "easy": "easy (factual recall, definitions, basic identification of terms and concepts)",
            "medium": "medium (understanding relationships between concepts, comparing approaches, applying knowledge to given situations)",
            "hard": "hard (critical analysis, synthesis, evaluation, multi-step reasoning integrating multiple concepts)",
        }
        diff_label = diff_descriptions.get(difficulty, f"'{difficulty}'")
        difficulty_instruction = f"\nGenerate ALL {num_questions} questions at difficulty level: {diff_label}."

    user_prompt = f"""Based on the following course material, generate exactly {num_questions} multiple-choice questions in Romanian.{difficulty_instruction}

IMPORTANT INSTRUCTIONS:
- Use diverse question types: "Care din următoarele...", "Ce reprezintă...", "De ce...", "Care este diferența dintre...", "În ce context...", "Care este rolul...", "Cum influențează...", "Care afirmație este incorectă?"
- Reference specific concepts, algorithms, principles, or mechanisms named in the text.
- Wrong options must be academically plausible distractors based on common misconceptions or similar-sounding concepts — not obviously false statements.
- Explanations must be at least 2-3 sentences: explain why the correct answer is right, connect it to the broader concept, and reference the relevant section or context from the source if identifiable.
- Do NOT generate superficial questions. Test deep understanding, not surface memorization.

COURSE MATERIAL:
\"\"\"
{context_text[:8000]}
\"\"\"

Generate exactly {num_questions} questions covering different aspects of the material above. Return ONLY valid JSON."""

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


def _mutate_sentence(sentence: str) -> str:
    """Create a plausible but incorrect distractor by making a targeted substitution in the sentence."""
    import re

    negations = [
        (r'\beste\b', 'nu este'),
        (r'\bsunt\b', 'nu sunt'),
        (r'\bpermite\b', 'nu permite'),
        (r'\bpoate\b', 'nu poate'),
        (r'\breprezintă\b', 'nu reprezintă'),
        (r'\binclude\b', 'exclude'),
        (r'\bcrește\b', 'scade'),
        (r'\bmaximizează\b', 'minimizează'),
        (r'\bactivă\b', 'pasivă'),
        (r'\bdirectă\b', 'indirectă'),
        (r'\bprimară\b', 'secundară'),
        (r'\bsincrona?\b', 'asincronă'),
        (r'\basincronă\b', 'sincronă'),
        (r'\bstatica?\b', 'dinamică'),
        (r'\bdinamica?\b', 'statică'),
        (r'\blinear[ăa]?\b', 'neliniară'),
        (r'\bautomată?\b', 'manuală'),
        (r'\bmanual[ăa]?\b', 'automată'),
        (r'\bexplicit[ăa]?\b', 'implicită'),
        (r'\bimplicit[ăa]?\b', 'explicită'),
    ]

    replacements = [
        (r'\bîntotdeauna\b', 'uneori'),
        (r'\btoți\b', 'unii'),
        (r'\btoate\b', 'unele'),
        (r'\bniciodată\b', 'uneori'),
        (r'\bobligatoriu\b', 'opțional'),
        (r'\bopțional\b', 'obligatoriu'),
        (r'\bînainte\b', 'după'),
        (r'\bdupă\b', 'înainte'),
        (r'\bintern\b', 'extern'),
        (r'\bextern\b', 'intern'),
        (r'\blocal\b', 'global'),
        (r'\bglobal\b', 'local'),
    ]

    all_patterns = negations + replacements
    random.shuffle(all_patterns)

    for pattern, replacement in all_patterns:
        new_sentence, count = re.subn(pattern, replacement, sentence, count=1, flags=re.IGNORECASE)
        if count > 0 and new_sentence != sentence:
            return new_sentence

    # Fallback: append a qualifying clause that makes it subtly wrong
    qualifiers = [
        " — această proprietate nu se aplică în toate cazurile.",
        " — afirmație valabilă doar în condiții ideale, nu în practică.",
        " — condiție necesară, dar nu și suficientă.",
        " — aplicabil exclusiv în faza de inițializare, nu pe parcurs.",
    ]
    return sentence.rstrip('.') + random.choice(qualifiers)


def _generate_fallback_questions(
    text: str, num_questions: int, difficulty: str | None
) -> list[dict]:
    """Generate demo questions when no API key is available.
    Produces plausible distractors by mutating the correct sentence rather
    than using generic placeholder strings."""
    import re

    # Clean text and extract meaningful sentences
    clean = re.sub(r'\s+', ' ', text)
    raw_sentences = re.split(r'(?<=[.!?])\s+', clean)
    sentences = [s.strip() for s in raw_sentences if 50 < len(s.strip()) < 300 and any(c.isalpha() for c in s)]

    # Shuffle to get variety
    random.shuffle(sentences)

    difficulties = ["easy", "medium", "hard"]
    question_templates = [
        "Care dintre următoarele afirmații descrie corect conceptul menționat în curs?",
        "Conform materialului de curs, care variantă este corectă?",
        "Care este afirmația corectă referitoare la subiectul discutat?",
        "Care dintre următoarele opțiuni reflectă fidel conținutul materialului?",
        "Care afirmație este susținută de textul cursului?",
        "Identificați varianta corectă dintre cele de mai jos:",
        "Care dintre afirmațiile de mai jos este incorectă?",
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
        display = sentence if len(sentence) <= 140 else sentence[:137] + "..."

        # Generate 3 plausible distractors by mutating the correct sentence
        distractors = set()
        attempts = 0
        while len(distractors) < 3 and attempts < 12:
            mutated = _mutate_sentence(display)
            if mutated != display:
                distractors.add(mutated if len(mutated) <= 140 else mutated[:137] + "...")
            attempts += 1

        # Fallback distractors if mutations failed to produce 3 distinct variants
        generic_fallbacks = [
            f"{display.rstrip('.')} — afirmație parțial corectă, dar incompletă.",
            f"{display.rstrip('.')} — valabil doar în condiții restrictive.",
            f"Contrariul este adevărat: {display[:60].lower()}...",
        ]
        fallback_iter = iter(generic_fallbacks)
        while len(distractors) < 3:
            distractors.add(next(fallback_iter))

        # Randomize correct answer position
        correct_idx = random.randint(0, 3)
        options = list(distractors)[:3]
        options.insert(correct_idx, display)

        diff = difficulty or random.choice(difficulties)
        template = random.choice(question_templates)

        questions.append({
            "question_text": template,
            "options": options,
            "correct_index": correct_idx,
            "explanation": (
                f"Afirmația corectă provine direct din materialul de curs. "
                f"Celelalte variante conțin modificări subtile care le fac incorecte din punct de vedere al conținutului predat. "
                f"Răspunsul ales reflectă fidel conceptul sau principiul enunțat în text."
            ),
            "difficulty": diff,
        })

    # Pad with topic-based questions if needed
    topics = [
        (
            "Gamificarea în educație",
            "Gamificarea reprezintă aplicarea sistematică a elementelor de design din jocuri (puncte, insigne, clasamente) în contexte educaționale non-ludice.",
            "Gamificarea presupune transformarea întregului curriculum într-un joc video interactiv.",
            "Gamificarea nu influențează motivația intrinsecă, ci doar pe cea extrinsecă a elevilor.",
            "Gamificarea este echivalentă cu învățarea bazată pe joc (game-based learning) și nu prezintă diferențe conceptuale.",
        ),
        (
            "Arhitectura Transformer",
            "Transformer-ul se bazează pe mecanismul de auto-atenție (self-attention) care permite procesarea paralelă a întregii secvențe de intrare.",
            "Transformer-ul procesează secvențele token cu token, în mod secvențial, similar rețelelor recurente (RNN).",
            "Mecanismul de atenție din Transformer este identic cu cel din rețelele convoluționale (CNN).",
            "Transformer-ul nu poate fi antrenat pe secvențe de lungimi variabile fără modificări arhitecturale suplimentare.",
        ),
        (
            "Retrieval Augmented Generation (RAG)",
            "RAG combină căutarea semantică în documente externe cu generarea de text a unui model de limbaj, reducând halucinațiile.",
            "RAG generează răspunsuri exclusiv pe baza cunoștințelor parametrice ale modelului, fără a accesa documente externe.",
            "RAG este o tehnică de fine-tuning care ajustează parametrii modelului pe documente specifice domeniului.",
            "RAG și fine-tuning-ul sunt tehnici echivalente din perspectiva mecanismului de incorporare a cunoștințelor externe.",
        ),
        (
            "Procesarea Limbajului Natural (NLP)",
            "NLP permite extragerea automată de informații, clasificarea textelor și generarea de răspunsuri din documente nestructurate.",
            "NLP funcționează exclusiv pe texte în limba engleză, celelalte limbi necesitând arhitecturi specializate complet diferite.",
            "NLP și OCR sunt tehnici identice, ambele având ca scop recunoașterea și interpretarea textului din imagini.",
            "Modelele NLP moderne nu pot fi utilizate pentru generarea de întrebări din texte academice.",
        ),
        (
            "Mecanismul Battle Royale în evaluare",
            "Mecanismul Battle Royale în evaluare introduce eliminarea progresivă a participanților pe baza performanței, menținând presiunea competitivă.",
            "În formatul Battle Royale, toți participanții primesc același scor final, indiferent de momentul eliminării.",
            "Battle Royale elimină studenții aleatoriu, fără a ține cont de răspunsurile corecte sau de timpul de răspuns.",
            "Formatul Battle Royale nu poate fi aplicat în sesiuni sincrone cu mai mult de 10 participanți simultani.",
        ),
    ]

    for topic_name, correct, w1, w2, w3 in topics:
        if len(questions) >= num_questions:
            break
        correct_idx = random.randint(0, 3)
        opts = [w1, w2, w3]
        opts.insert(correct_idx, correct)
        questions.append({
            "question_text": f"Care afirmație descrie corect conceptul de {topic_name}?",
            "options": opts,
            "correct_index": correct_idx,
            "explanation": (
                f"{correct} "
                f"Celelalte variante reprezintă concepții greșite frecvente: confundarea cu tehnici similare, "
                f"suprageneralizarea sau negarea unor proprietăți esențiale ale conceptului."
            ),
            "difficulty": difficulty or random.choice(difficulties),
        })

    return questions[:num_questions]
