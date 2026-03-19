import aiosqlite
import json
import os
from hashlib import sha256
from config import DB_PATH, SECRET_KEY


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


def _hash_password(password: str) -> str:
    return sha256((password + SECRET_KEY).encode()).hexdigest()


async def init_db():
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('professor', 'student')),
            group_name TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            professor_id INTEGER NOT NULL,
            pdf_filename TEXT,
            extracted_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (professor_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            options TEXT NOT NULL,
            correct_index INTEGER NOT NULL,
            explanation TEXT DEFAULT '',
            difficulty TEXT DEFAULT 'medium' CHECK(difficulty IN ('easy', 'medium', 'hard')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(id)
        );

        CREATE TABLE IF NOT EXISTS game_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pin_code TEXT UNIQUE NOT NULL,
            course_id INTEGER NOT NULL,
            professor_id INTEGER NOT NULL,
            status TEXT DEFAULT 'waiting' CHECK(status IN ('waiting', 'playing', 'finished')),
            max_players INTEGER DEFAULT 50,
            time_per_question INTEGER DEFAULT 30,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(id),
            FOREIGN KEY (professor_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS game_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            player_name TEXT NOT NULL,
            user_id INTEGER,
            score INTEGER DEFAULT 0,
            is_alive INTEGER DEFAULT 1,
            eliminated_at_round INTEGER,
            finished_at TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES game_sessions(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    await db.commit()

    # Auto-seed if database is empty
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
    row = await cursor.fetchone()
    if row["cnt"] == 0:
        print("Empty database detected — seeding test data...")
        await _seed_data(db)

    await db.close()


async def _seed_data(db):
    """Insert default test users, a demo course, and sample questions."""
    users = [
        ("admin", "admin@trivia.ro", _hash_password("admin123"), "Administrator Sistem", "professor", ""),
        ("prof.ionescu", "ionescu@tuiasi.ro", _hash_password("profesor123"), "Prof. Ion Ionescu", "professor", ""),
        ("prof.popescu", "popescu@tuiasi.ro", _hash_password("profesor123"), "Prof. Maria Popescu", "professor", ""),
        ("student1", "student1@student.tuiasi.ro", _hash_password("student123"), "Alexandru Marin", "student", "1401A"),
        ("student2", "student2@student.tuiasi.ro", _hash_password("student123"), "Elena Dumitrescu", "student", "1401A"),
        ("student3", "student3@student.tuiasi.ro", _hash_password("student123"), "Mihai Georgescu", "student", "1401B"),
        ("student4", "student4@student.tuiasi.ro", _hash_password("student123"), "Ana Moldovan", "student", "1401B"),
        ("student5", "student5@student.tuiasi.ro", _hash_password("student123"), "Radu Stanescu", "student", "1402A"),
    ]
    for u in users:
        await db.execute(
            "INSERT OR IGNORE INTO users (username, email, hashed_password, full_name, role, group_name) VALUES (?, ?, ?, ?, ?, ?)",
            u,
        )

    # Demo course
    await db.execute(
        "INSERT OR IGNORE INTO courses (id, title, description, professor_id, extracted_text) VALUES (?, ?, ?, ?, ?)",
        (1, "Inteligenta Artificiala - Demo", "Curs demonstrativ cu intrebari pre-generate despre AI, NLP, Transformer si gamificare.",
         1, "Gamificarea reprezinta aplicarea elementelor de design din jocuri in contexte educationale. Arhitectura Transformer se bazeaza pe mecanismul de auto-atentie. RAG combina cautarea in documente cu generarea de text prin modele de limbaj. Mecanismul Battle Royale introduce eliminarea progresiva a participantilor. NLP permite extragerea automata de informatii din texte nestructurate. FastAPI ofera suport nativ ASGI esential pentru WebSocket. Serverul Autoritar valideaza toate actiunile pe server prevenind frauda. Pinia este state management store-ul oficial pentru Vue.js 3."),
    )

    # Sample questions
    questions = [
        ("Ce reprezinta gamificarea in context educational?",
         json.dumps(["Aplicarea elementelor de design din jocuri in contexte educationale", "Inlocuirea cursurilor cu jocuri video", "Utilizarea exclusiva a calculatorului in educatie", "Eliminarea evaluarilor traditionale"]),
         0, "Gamificarea este aplicarea mecanismelor si elementelor de design din jocuri (puncte, recompense, competitie) in contexte non-ludice.", "easy"),
        ("Care este principalul avantaj al arhitecturii Transformer fata de RNN?",
         json.dumps(["Consuma mai putina memorie", "Permite procesarea paralela a secventelor prin mecanismul de auto-atentie", "Este mai simplu de implementat", "Functioneaza doar pe CPU"]),
         1, "Transformer-ul elimina procesarea secventiala a RNN-urilor, permitand procesarea paralela a intregii secvente.", "medium"),
        ("Ce este RAG (Retrieval Augmented Generation)?",
         json.dumps(["Un protocol de retea pentru transfer de date", "Un limbaj de programare pentru AI", "O tehnica ce combina cautarea in documente cu generarea de text prin LLM-uri", "Un algoritm de compresie a datelor"]),
         2, "RAG combina retrieval (cautarea in baze de cunostinte) cu generarea de text prin modele de limbaj, reducand halucinatiile AI.", "medium"),
        ("In formatul Battle Royale educational, ce se intampla cand un student raspunde gresit in Sudden Death?",
         json.dumps(["Primeste o penalizare de puncte", "Poate incerca din nou", "Este eliminat instantaneu din joc", "Nimic, continua normal"]),
         2, "In Sudden Death, daca cel putin un jucator raspunde corect, toti cei care au gresit sunt eliminati instantaneu.", "easy"),
        ("Ce protocol de comunicare este folosit pentru sincronizarea in timp real a jocului?",
         json.dumps(["HTTP standard", "FTP", "WebSocket", "SMTP"]),
         2, "WebSocket permite comunicare bidirectionala persistenta intre server si clienti, esentiala pentru latenta scazuta.", "easy"),
        ("Ce rol are Pinia in aplicatia Vue.js?",
         json.dumps(["Gestionarea bazei de date", "Routing intre pagini", "Store global de stare reactiva (sursa unica de adevar)", "Procesarea fisierelor PDF"]),
         2, "Pinia este state management store-ul oficial pentru Vue.js 3, functionand ca sursa unica de adevar.", "medium"),
        ("De ce a fost ales FastAPI in locul Flask sau Django?",
         json.dumps(["Este mai vechi si mai stabil", "Suport nativ ASGI pentru WebSocket si performanta asincrona superioara", "Are mai multe template-uri HTML", "Nu necesita Python"]),
         1, "FastAPI ofera suport nativ ASGI esential pentru gestionarea performanta a WebSocket-urilor.", "hard"),
        ("Ce model de arhitectura server este folosit pentru a preveni frauda?",
         json.dumps(["Peer-to-Peer", "Client Autoritar", "Server Autoritar (Authoritative Server)", "Arhitectura descentralizata"]),
         2, "Serverul Autoritar valideaza toate actiunile pe server, prevenind modificarea codului client.", "hard"),
        ("Care este scopul principal al mecanismului de chunking in pipeline-ul RAG?",
         json.dumps(["Comprimarea fisierelor PDF", "Segmentarea textului in unitati semantice optimizate pentru fereastra de context AI", "Criptarea datelor", "Formatarea textului pentru afisare"]),
         1, "Chunking-ul imparte textul in fragmente de dimensiune optima pentru fereastra de context a LLM-ului.", "hard"),
        ("Ce avantaj ofera formatul Battle Royale fata de testele clasice?",
         json.dumps(["Este mai usor de implementat", "Nu necesita intrebari", "Creeaza o miza psihologica imediata prin eliminare progresiva", "Elimina nevoia de corectare"]),
         2, "Formatul Battle Royale introduce high stakes - supravietuirea depinde direct de cunostinte.", "medium"),
    ]
    for qt, opts, ci, expl, diff in questions:
        await db.execute(
            "INSERT INTO questions (course_id, question_text, options, correct_index, explanation, difficulty) VALUES (1, ?, ?, ?, ?, ?)",
            (qt, opts, ci, expl, diff),
        )

    await db.commit()
    print("Seeded: 8 users, 1 course, 10 questions")
