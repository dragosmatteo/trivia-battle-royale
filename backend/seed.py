"""
Seed script - creates test users and sample data for demo.
Run: python seed.py
"""
import asyncio
import json
import os
import sys
from hashlib import sha256

# Add parent to path
sys.path.insert(0, os.path.dirname(__file__))

from config import SECRET_KEY
from models.database import init_db, get_db


def hash_password(password: str) -> str:
    return sha256((password + SECRET_KEY).encode()).hexdigest()


USERS = [
    {
        "username": "admin",
        "email": "admin@trivia.ro",
        "password": "admin123",
        "full_name": "Administrator Sistem",
        "role": "professor",
        "group_name": "",
    },
    {
        "username": "prof.ionescu",
        "email": "ionescu@tuiasi.ro",
        "password": "profesor123",
        "full_name": "Prof. Ion Ionescu",
        "role": "professor",
        "group_name": "",
    },
    {
        "username": "prof.popescu",
        "email": "popescu@tuiasi.ro",
        "password": "profesor123",
        "full_name": "Prof. Maria Popescu",
        "role": "professor",
        "group_name": "",
    },
    {
        "username": "student1",
        "email": "student1@student.tuiasi.ro",
        "password": "student123",
        "full_name": "Alexandru Marin",
        "role": "student",
        "group_name": "1401A",
    },
    {
        "username": "student2",
        "email": "student2@student.tuiasi.ro",
        "password": "student123",
        "full_name": "Elena Dumitrescu",
        "role": "student",
        "group_name": "1401A",
    },
    {
        "username": "student3",
        "email": "student3@student.tuiasi.ro",
        "password": "student123",
        "full_name": "Mihai Georgescu",
        "role": "student",
        "group_name": "1401B",
    },
    {
        "username": "student4",
        "email": "student4@student.tuiasi.ro",
        "password": "student123",
        "full_name": "Ana Moldovan",
        "role": "student",
        "group_name": "1401B",
    },
    {
        "username": "student5",
        "email": "student5@student.tuiasi.ro",
        "password": "student123",
        "full_name": "Radu Stanescu",
        "role": "student",
        "group_name": "1402A",
    },
]

SAMPLE_QUESTIONS = [
    {
        "question_text": "Ce reprezinta gamificarea in context educational?",
        "options": [
            "Aplicarea elementelor de design din jocuri in contexte educationale",
            "Inlocuirea cursurilor cu jocuri video",
            "Utilizarea exclusiva a calculatorului in educatie",
            "Eliminarea evaluarilor traditionale",
        ],
        "correct_index": 0,
        "explanation": "Gamificarea este aplicarea mecanismelor si elementelor de design din jocuri (puncte, recompense, competitie) in contexte non-ludice, precum educatia.",
        "difficulty": "easy",
    },
    {
        "question_text": "Care este principalul avantaj al arhitecturii Transformer fata de RNN?",
        "options": [
            "Consuma mai putina memorie",
            "Permite procesarea paralela a secventelor prin mecanismul de auto-atentie",
            "Este mai simplu de implementat",
            "Functioneaza doar pe CPU",
        ],
        "correct_index": 1,
        "explanation": "Transformer-ul elimina procesarea secventiala a RNN-urilor, permitand procesarea paralela a intregii secvente prin mecanismul de self-attention.",
        "difficulty": "medium",
    },
    {
        "question_text": "Ce este RAG (Retrieval Augmented Generation)?",
        "options": [
            "Un protocol de retea pentru transfer de date",
            "Un limbaj de programare pentru AI",
            "O tehnica ce combina cautarea in documente cu generarea de text prin LLM-uri",
            "Un algoritm de compresie a datelor",
        ],
        "correct_index": 2,
        "explanation": "RAG combina retrieval (cautarea in baze de cunostinte/documente) cu generarea de text prin modele de limbaj, reducand halucinatiile AI.",
        "difficulty": "medium",
    },
    {
        "question_text": "In formatul Battle Royale educational, ce se intampla cand un student raspunde gresit in faza Sudden Death?",
        "options": [
            "Primeste o penalizare de puncte",
            "Poate incerca din nou",
            "Este eliminat instantaneu din joc",
            "Nimic, continua normal",
        ],
        "correct_index": 2,
        "explanation": "In Sudden Death, daca cel putin un jucator raspunde corect, toti cei care au gresit sunt eliminati instantaneu (Last Man Standing).",
        "difficulty": "easy",
    },
    {
        "question_text": "Ce protocol de comunicare este folosit pentru sincronizarea in timp real a jocului?",
        "options": [
            "HTTP standard",
            "FTP",
            "WebSocket",
            "SMTP",
        ],
        "correct_index": 2,
        "explanation": "WebSocket permite comunicare bidirectionala persistenta intre server si clienti, esentiala pentru latenta scazuta in jocurile real-time.",
        "difficulty": "easy",
    },
    {
        "question_text": "Ce rol are Pinia in aplicatia Vue.js?",
        "options": [
            "Gestionarea bazei de date",
            "Routing intre pagini",
            "Store global de stare reactiva (sursa unica de adevar)",
            "Procesarea fisierelor PDF",
        ],
        "correct_index": 2,
        "explanation": "Pinia este state management store-ul oficial pentru Vue.js 3, functionand ca 'sursa unica de adevar' pentru starea aplicatiei.",
        "difficulty": "medium",
    },
    {
        "question_text": "De ce a fost ales FastAPI in locul Flask sau Django?",
        "options": [
            "Este mai vechi si mai stabil",
            "Suport nativ ASGI pentru WebSocket si performanta asincrona superioara",
            "Are mai multe template-uri HTML",
            "Nu necesita Python",
        ],
        "correct_index": 1,
        "explanation": "FastAPI ofera suport nativ ASGI esential pentru gestionarea performanta a WebSocket-urilor, cu viteza de executie superioara framework-urilor traditionale.",
        "difficulty": "hard",
    },
    {
        "question_text": "Ce model de arhitectura server este folosit pentru a preveni frauda?",
        "options": [
            "Peer-to-Peer",
            "Client Autoritar",
            "Server Autoritar (Authoritative Server)",
            "Arhitectura descentralizata",
        ],
        "correct_index": 2,
        "explanation": "Serverul Autoritar valideaza toate actiunile pe server, prevenind modificarea codului client de catre studenti pentru a obtine avantaje.",
        "difficulty": "hard",
    },
    {
        "question_text": "Care este scopul principal al mecanismului de chunking in pipeline-ul RAG?",
        "options": [
            "Comprimarea fisierelor PDF",
            "Segmentarea textului in unitati semantice optimizate pentru fereastra de context a modelului AI",
            "Criptarea datelor",
            "Formatarea textului pentru afisare",
        ],
        "correct_index": 1,
        "explanation": "Chunking-ul imparte textul in fragmente de dimensiune optima pentru a se incadra in fereastra de context a LLM-ului, pastrind coerenta semantica.",
        "difficulty": "hard",
    },
    {
        "question_text": "Ce avantaj ofera formatul Battle Royale fata de testele clasice?",
        "options": [
            "Este mai usor de implementat",
            "Nu necesita intrebari",
            "Creeaza o miza psihologica imediata prin eliminare progresiva",
            "Elimina nevoia de corectare",
        ],
        "correct_index": 2,
        "explanation": "Formatul Battle Royale introduce 'high stakes' - supravietuirea depinde direct de cunostinte, crescind concentrarea si motivatia intrinseca.",
        "difficulty": "medium",
    },
]


async def seed():
    await init_db()
    db = await get_db()

    print("=== Seeding Database ===\n")

    # Create users
    print("Creating users:")
    for u in USERS:
        try:
            await db.execute(
                "INSERT INTO users (username, email, hashed_password, full_name, role, group_name) VALUES (?, ?, ?, ?, ?, ?)",
                (u["username"], u["email"], hash_password(u["password"]), u["full_name"], u["role"], u["group_name"]),
            )
            print(f"  + {u['role']:10s} | {u['username']:15s} | parola: {u['password']}")
        except Exception as e:
            print(f"  ~ {u['username']} already exists")

    # Create sample course
    print("\nCreating sample course:")
    try:
        await db.execute(
            "INSERT INTO courses (title, description, professor_id, extracted_text) VALUES (?, ?, ?, ?)",
            (
                "Inteligenta Artificiala - Demo",
                "Curs demonstrativ cu intrebari pre-generate",
                1,
                "Acest curs acopera teme precum gamificarea in educatie, arhitectura Transformer, NLP, RAG si mecanismul Battle Royale.",
            ),
        )
        print("  + Course: Inteligenta Artificiala - Demo (ID: 1)")
    except Exception:
        print("  ~ Course already exists")

    # Create sample questions
    print(f"\nCreating {len(SAMPLE_QUESTIONS)} sample questions:")
    for q in SAMPLE_QUESTIONS:
        try:
            await db.execute(
                "INSERT INTO questions (course_id, question_text, options, correct_index, explanation, difficulty) VALUES (?, ?, ?, ?, ?, ?)",
                (1, q["question_text"], json.dumps(q["options"]), q["correct_index"], q["explanation"], q["difficulty"]),
            )
            print(f"  + [{q['difficulty']:6s}] {q['question_text'][:60]}...")
        except Exception:
            pass

    await db.commit()
    await db.close()

    print("\n=== Seed Complete ===")
    print("\n--- Credentiale de test ---")
    print(f"{'Rol':<12} {'Username':<18} {'Parola':<15} {'Nume'}")
    print("-" * 70)
    for u in USERS:
        print(f"{u['role']:<12} {u['username']:<18} {u['password']:<15} {u['full_name']}")
    print()
    print("Frontend: http://localhost:5173")
    print("Backend:  http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(seed())
