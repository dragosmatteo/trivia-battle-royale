# Trivia Battle Royale - Tutorial Complet

## Cuprins
1. [Credentiale de Test](#credentiale-de-test)
2. [Instalare si Rulare](#instalare-si-rulare)
3. [Ghid Profesor](#ghid-profesor)
4. [Ghid Student](#ghid-student)
5. [Desfasurarea Battle Royale](#desfasurarea-battle-royale)
6. [API Endpoints](#api-endpoints)
7. [Arhitectura Tehnica](#arhitectura-tehnica)
8. [Structura Fisiere](#structura-fisiere)
9. [Baza de Date](#baza-de-date)
10. [Securitate](#securitate)
11. [Deploy Online](#deploy-online)
12. [Troubleshooting](#troubleshooting)

---

## Credentiale de Test

### Profesori

| Username | Parola | Nume | Email |
|----------|--------|------|-------|
| `admin` | `admin123` | Administrator Sistem | admin@trivia.ro |
| `prof.ionescu` | `profesor123` | Prof. Ion Ionescu | ionescu@tuiasi.ro |
| `prof.popescu` | `profesor123` | Prof. Maria Popescu | popescu@tuiasi.ro |

### Studenti

| Username | Parola | Nume | Grupa | Email |
|----------|--------|------|-------|-------|
| `student1` | `student123` | Alexandru Marin | 1401A | student1@student.tuiasi.ro |
| `student2` | `student123` | Elena Dumitrescu | 1401A | student2@student.tuiasi.ro |
| `student3` | `student123` | Mihai Georgescu | 1401B | student3@student.tuiasi.ro |
| `student4` | `student123` | Ana Moldovan | 1401B | student4@student.tuiasi.ro |
| `student5` | `student123` | Radu Stanescu | 1402A | student5@student.tuiasi.ro |

> **Nota:** Datele de test se creeaza automat la prima pornire a backend-ului (auto-seed). Daca baza de date este goala, se insereaza automat utilizatorii de mai sus, un curs demo si 10 intrebari de test.

---

## Instalare si Rulare

### Cerinte sistem
- **Python** 3.11+
- **Node.js** 18+
- **pip** (Python package manager)
- **npm** (Node.js package manager)

### Pasul 1: Instalare dependente

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### Pasul 2: Seed baza de date (optional)

Baza de date se populeaza automat la prima pornire. Daca vrei sa resetezi:

```bash
cd backend
del trivia.db        # Windows
# rm trivia.db       # Linux/Mac
python seed.py       # Recreeaza baza de date cu date de test
```

### Pasul 3: Pornire

**Varianta rapida (Windows):** dublu-click pe `start.bat`

**Varianta manuala:**
```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### URL-uri importante

| Serviciu | URL |
|----------|-----|
| Frontend (aplicatia) | http://localhost:5173 |
| Backend (API) | http://localhost:8000 |
| Swagger API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/api/health |

---

## Ghid Profesor

### 1. Autentificare
1. Deschide http://localhost:5173/login
2. Introdu username-ul si parola (ex: `prof.ionescu` / `profesor123`)
3. Esti redirectat catre **Admin Dashboard** (`/professor`)

### 2. Admin Dashboard (`/professor`)
Pagina principala a profesorului cu:
- **Statistici generale**: numar total de jocuri, studenti, cursuri, intrebari, scor mediu
- **Jocuri recente**: ultimele 5 sesiuni cu castigatorul si numarul de participanti
- **Navigare rapida** catre: Cursuri, Istoric jocuri, Management clase

### 3. Management Cursuri (`/professor/courses`)
1. **Creeaza un curs nou**: completeaza titlul si optional incarca un PDF
2. PDF-ul este procesat automat - textul se extrage pentru generarea de intrebari
3. Pe card-ul cursului, ai optiunile:
   - **Vezi intrebari** - deschide pagina de detalii curs
   - **Porneste joc** - creeaza o sesiune de joc
   - **Sterge curs** - elimina cursul si intrebarile asociate

### 4. Detalii Curs / Knowledge Base (`/professor/course/:id`)
- **Knowledge Base multi-material**: poti incarca mai multe PDF-uri per curs
  - Fiecare material arata: nume fisier, dimensiune, numar caractere, status
  - Status-uri: `processing` (se proceseaza), `ready` (gata), `error` (eroare)
- **Generare intrebari AI**:
  1. Configureaza: numar intrebari (1-20), dificultate (easy/medium/hard/mixed), capitol optional
  2. Click "Genereaza" - AI-ul creeaza intrebari din textul extras
  3. Necesita `OPENAI_API_KEY` in `.env` pentru generare reala
- **Editare intrebari**: modifica textul, optiunile, raspunsul corect, explicatia, dificultatea
- **Stergere intrebari**: elimina intrebarile nedorite

### 5. Pornirea unui joc
1. De pe pagina Cursuri, click **"Porneste joc"** pe cursul dorit
2. Se genereaza un **PIN de 6 cifre** (ex: `482917`)
3. Se deschide **Camera de Asteptare** (`/professor/game/:pin`)
4. Distribuie PIN-ul studentilor
5. Urmareste lista de jucatori conectati in timp real
6. Cand sunt suficienti jucatori, click **"Porneste Jocul"**
7. In timpul jocului, profesorul poate:
   - Trece la urmatoarea intrebare
   - Vedea leaderboard-ul live
   - Vedea cine este eliminat
   - Opri jocul prematur

### 6. Istoric Jocuri (`/professor/history`)
- Lista tuturor sesiunilor de joc finalizate
- Filtreaza dupa curs
- Click pe o sesiune pentru detalii:
  - Clasament final cu scoruri
  - Cine a supravietuit / cine a fost eliminat si in ce runda
  - Statistici pe runde

### 7. Management Clase (`/professor/classes`)
- **Vizualizeaza clasele** existente cu numarul de studenti
- **Creeaza clasa noua** (ex: "1401A", "1402B")
- **Adauga studenti** intr-o clasa:
  - Completeaza: username, nume complet, email
  - Parola se genereaza automat (8 caractere alfanumerice)
  - Parola generata se afiseaza o singura data - noteaz-o!
- **Muta studenti** intre clase
- **Elimina studenti** dintr-o clasa
- **Genereaza link de invitatie** pentru o clasa
- **Statistici per student**: numar jocuri, scor mediu, victorii

---

## Ghid Student

### 1. Inregistrare / Autentificare
- **Login**: http://localhost:5173/login cu credentialele primite
- **Register**: http://localhost:5173/register - creeaza cont nou

### 2. Dashboard Student (`/student`)
- Vizualizarea cursurilor disponibile
- Acces rapid la "Intra in joc"

### 3. Intrarea intr-un joc
1. Mergi la http://localhost:5173/join (sau click "Intra in joc")
2. Introdu **codul PIN** (6 cifre) primit de la profesor
3. Alege un **Nickname** (2-20 caractere)
4. Click **"Intra in joc"**
5. Asteapta in Camera de Asteptare pana profesorul porneste jocul

### 4. Jocul propriu-zis (`/play/:pin`)
- Intrebarile apar automat, cu timer vizibil
- Click pe una din cele 4 variante de raspuns
- Dupa raspuns, butonul se blocheaza (nu poti schimba)
- Primesti feedback: corect/gresit, scor curent, pozitie in clasament
- Daca esti eliminat, treci in modul **Spectator**

---

## Desfasurarea Battle Royale

### Fazele jocului

```
1. CAMERA DE ASTEPTARE
   - Jucatorii se conecteaza cu PIN + Nickname
   - Profesorul vede lista si porneste jocul

2. RUNDE CALIFICATIVE (primele 3 runde)
   - Intrebari cu timer (default 30 secunde)
   - Raspuns corect: 100 puncte baza + bonus viteza (max 50)
   - Serie de 3+ raspunsuri corecte: +50 puncte bonus
   - Nu raspunzi la timp: ELIMINAT
   - Dupa 3 runde, jucatorii se impart in tier-uri de dificultate

3. DIFFICULTY TIERS (dupa runda 3)
   - "Advanced" tier: jucatori cu rata de corectitudine > 66%
   - "Standard" tier: restul jucatorilor
   - Tier-ul afecteaza dificultatea intrebarilor primite

4. SUDDEN DEATH (ultimele 5 intrebari)
   - Raspuns GRESIT = ELIMINAT INSTANT
   - Conditie: cel putin un jucator trebuie sa raspunda corect
   - Tensiune maxima - supravietuirea depinde de cunostinte

5. FINAL
   - Ultimul jucator ramas = CASTIGATORUL
   - Clasament final cu scoruri
   - Rezultatele se salveaza in baza de date
```

### Sistem de punctaj

| Actiune | Puncte |
|---------|--------|
| Raspuns corect | 100 |
| Bonus viteza (raspuns rapid) | pana la +50 |
| Bonus serie (3+ corecte consecutiv) | +50 |
| Raspuns gresit | 0 |
| Nu raspunzi la timp | ELIMINAT |
| Gresit in Sudden Death | ELIMINAT |

### Grace Period
Raspunsurile primite in **2.5 secunde** dupa expirarea timer-ului sunt inca acceptate (compenseaza latenta retelei).

---

## API Endpoints

### Autentificare (`/api/auth`)

| Metoda | Endpoint | Descriere |
|--------|----------|-----------|
| POST | `/api/auth/register` | Inregistrare cont nou |
| POST | `/api/auth/login` | Autentificare (returneaza JWT token) |
| GET | `/api/auth/me` | Profilul utilizatorului curent |

### Cursuri (`/api/courses`)

| Metoda | Endpoint | Descriere |
|--------|----------|-----------|
| GET | `/api/courses/` | Lista cursurile profesorului |
| POST | `/api/courses/` | Creeaza curs (+ optional PDF) |
| DELETE | `/api/courses/{id}` | Sterge un curs |
| GET | `/api/courses/{id}/questions` | Lista intrebarile cursului |
| POST | `/api/courses/{id}/generate` | Genereaza intrebari AI |
| PUT | `/api/courses/questions/{id}` | Editeaza o intrebare |
| DELETE | `/api/courses/questions/{id}` | Sterge o intrebare |
| GET | `/api/courses/{id}/materials` | Lista materialele cursului |
| POST | `/api/courses/{id}/materials` | Incarca material PDF |
| DELETE | `/api/courses/materials/{id}` | Sterge un material |

### Joc (`/api/game`)

| Metoda | Endpoint | Descriere |
|--------|----------|-----------|
| POST | `/api/game/create` | Creeaza sesiune de joc (returneaza PIN) |
| GET | `/api/game/{pin}/status` | Status sesiune |
| GET | `/api/game/active` | Sesiunile active ale profesorului |

### Admin (`/api/admin`)

| Metoda | Endpoint | Descriere |
|--------|----------|-----------|
| GET | `/api/admin/stats` | Statistici generale |
| GET | `/api/admin/game-history` | Istoric jocuri (filtreaza cu ?course_id=) |
| GET | `/api/admin/game-history/{id}` | Detalii sesiune de joc |
| GET | `/api/admin/classes` | Lista clase cu numar studenti |
| POST | `/api/admin/classes` | Creeaza clasa noua |
| GET | `/api/admin/classes/{group}/students` | Studenti dintr-o clasa + statistici |
| POST | `/api/admin/classes/{group}/students` | Adauga student (parola auto-generata) |
| PUT | `/api/admin/classes/{group}/students/{id}/move` | Muta student in alta clasa |
| DELETE | `/api/admin/classes/{group}/students/{id}` | Elimina student din clasa |
| POST | `/api/admin/invite-link` | Genereaza link de invitatie pentru clasa |

### WebSocket Endpoints

| Endpoint | Descriere |
|----------|-----------|
| `ws://localhost:8000/ws/professor/{pin}` | Conexiune profesor (control joc) |
| `ws://localhost:8000/ws/player/{pin}/{nickname}` | Conexiune jucator |

#### Actiuni WebSocket Profesor
- `{"action": "start_game"}` - Porneste jocul
- `{"action": "next_question"}` - Urmatoarea intrebare
- `{"action": "end_game"}` - Termina jocul

#### Actiuni WebSocket Jucator
- `{"action": "answer", "selected_option": 0-3}` - Trimite raspunsul

### Utilitare

| Metoda | Endpoint | Descriere |
|--------|----------|-----------|
| GET | `/api/health` | Health check |

> **Documentatia interactiva completa**: http://localhost:8000/docs (Swagger UI)

---

## Arhitectura Tehnica

```
Frontend (Vue.js 3 + Vite)          Backend (FastAPI + Python)
+-------------------------+         +-------------------------+
|  LoginView              |  REST   |  Auth Router (JWT)      |
|  RegisterView           |-------->|  Courses Router         |
|  Professor/             |  HTTP   |  Game Router            |
|    AdminDashboardView   |         |  Admin Router           |
|    DashboardView        |         +-------------------------+
|    CourseDetailView     |                    |
|    GameControlView      |                    |
|    GameHistoryView      |         +-------------------------+
|    ClassManagementView  |         |  Services               |
|  Student/               |         |    ai_generator.py      |
|    DashboardView        |         |    pdf_processor.py     |
|    JoinGameView         |         |    game_manager.py      |
|    GamePlayView         |         +-------------------------+
+-------------------------+                    |
        |                           +-------------------------+
        |     WebSocket             |  SQLite Database        |
        +-------------------------->|    trivia.db            |
        |  - join/leave             +-------------------------+
        |  - questions (shuffled)
        |  - answers
        |  - round results + stats
        |  - elimination
        |  - difficulty tiers
        |  - game over + leaderboard
        +<--------------------------+  GameManager (Singleton)
                                    |    - Rooms
                                    |    - Players
                                    |    - Timer
                                    |    - Elimination Logic
                                    |    - Adaptive Difficulty
                                    |    - Round Statistics
```

### Tehnologii folosite

| Componenta | Tehnologie | Versiune |
|------------|-----------|----------|
| Frontend Framework | Vue.js | 3.5+ |
| Frontend Build | Vite | 5.4+ |
| State Management | Pinia | 2.2+ |
| HTTP Client | Axios | 1.7+ |
| Routing (frontend) | Vue Router | 4.4+ |
| Backend Framework | FastAPI | latest |
| Server ASGI | Uvicorn | latest |
| Baza de date | SQLite (aiosqlite) | - |
| AI Generator | OpenAI API | - |
| PDF Processing | PyPDF2 | - |
| Autentificare | JWT (python-jose) | - |

---

## Structura Fisiere

```
PROIECT_LICENTA/
|-- start.bat                    # Pornire rapida Windows
|-- start.sh                     # Pornire rapida Linux/Mac
|-- TUTORIAL.md                  # Acest document
|
|-- backend/
|   |-- main.py                  # FastAPI app + WebSocket + middleware
|   |-- config.py                # Configurare (SECRET_KEY, paths, OPENAI_API_KEY)
|   |-- seed.py                  # Script populare date de test
|   |-- requirements.txt         # Dependente Python
|   |-- trivia.db                # Baza de date SQLite (auto-generata)
|   |-- render.yaml              # Config deploy Render.com
|   |-- Procfile                 # Config deploy Heroku/Railway
|   |-- uploads/                 # PDF-uri incarcate
|   |-- models/
|   |   |-- database.py          # Schema DB + init + auto-seed
|   |   |-- schemas.py           # Pydantic validation models
|   |-- routers/
|   |   |-- auth.py              # Register, Login, JWT, /me
|   |   |-- courses.py           # CRUD cursuri, materials, intrebari, generare AI
|   |   |-- game.py              # Create/Join sesiuni de joc
|   |   |-- admin.py             # Statistici, istoric, management clase
|   |-- services/
|       |-- pdf_processor.py     # Extragere text din PDF
|       |-- ai_generator.py      # RAG pipeline + OpenAI integration
|       |-- game_manager.py      # WebSocket game engine (Singleton)
|
|-- frontend/
    |-- package.json             # Dependente Node.js
    |-- vite.config.js           # Configurare Vite
    |-- src/
        |-- App.vue              # Layout principal + Navbar
        |-- main.js              # Entry point Vue
        |-- router/
        |   |-- index.js         # Route definitions + auth guards
        |-- stores/
        |   |-- auth.js          # Pinia - user state + JWT
        |   |-- game.js          # Pinia - game state (score, alive, timer)
        |-- services/
        |   |-- api.js           # Axios HTTP client cu interceptors
        |   |-- websocket.js     # WebSocket client wrapper
        |-- views/
            |-- LoginView.vue
            |-- RegisterView.vue
            |-- professor/
            |   |-- AdminDashboardView.vue   # Dashboard principal profesor
            |   |-- DashboardView.vue        # Management cursuri
            |   |-- CourseDetailView.vue      # Knowledge base + intrebari
            |   |-- GameControlView.vue      # Control joc live
            |   |-- GameHistoryView.vue      # Istoric sesiuni
            |   |-- ClassManagementView.vue  # Clase + studenti
            |-- student/
                |-- DashboardView.vue        # Dashboard student
                |-- JoinGameView.vue         # Ecran PIN + nickname
                |-- GamePlayView.vue         # Jocul propriu-zis
```

---

## Baza de Date

### Schema (SQLite)

#### `users`
| Coloana | Tip | Descriere |
|---------|-----|-----------|
| id | INTEGER PK | ID auto-increment |
| username | TEXT UNIQUE | Nume utilizator |
| email | TEXT UNIQUE | Adresa email |
| hashed_password | TEXT | Parola hash-uita (SHA256 + salt) |
| full_name | TEXT | Nume complet |
| role | TEXT | `professor` sau `student` |
| group_name | TEXT | Grupa studentului (ex: "1401A") |
| created_at | TIMESTAMP | Data creare cont |

#### `courses`
| Coloana | Tip | Descriere |
|---------|-----|-----------|
| id | INTEGER PK | ID auto-increment |
| title | TEXT | Titlul cursului |
| description | TEXT | Descrierea cursului |
| professor_id | INTEGER FK | ID-ul profesorului creator |
| pdf_filename | TEXT | Numele fisierului PDF |
| extracted_text | TEXT | Textul extras din PDF |
| created_at | TIMESTAMP | Data creare |

#### `course_materials`
| Coloana | Tip | Descriere |
|---------|-----|-----------|
| id | INTEGER PK | ID auto-increment |
| course_id | INTEGER FK | ID-ul cursului |
| filename | TEXT | Numele fisierului pe disk |
| original_name | TEXT | Numele original al fisierului |
| file_size | INTEGER | Dimensiunea in bytes |
| extracted_text | TEXT | Textul extras |
| char_count | INTEGER | Numar caractere extrase |
| status | TEXT | `processing`, `ready`, `error` |
| error_message | TEXT | Mesaj eroare (daca exista) |
| created_at | TIMESTAMP | Data incarcare |

#### `questions`
| Coloana | Tip | Descriere |
|---------|-----|-----------|
| id | INTEGER PK | ID auto-increment |
| course_id | INTEGER FK | ID-ul cursului |
| question_text | TEXT | Textul intrebarii |
| options | TEXT (JSON) | Array cu 4 variante de raspuns |
| correct_index | INTEGER | Indexul raspunsului corect (0-3) |
| explanation | TEXT | Explicatia raspunsului corect |
| difficulty | TEXT | `easy`, `medium`, `hard` |
| created_at | TIMESTAMP | Data creare |

#### `game_sessions`
| Coloana | Tip | Descriere |
|---------|-----|-----------|
| id | INTEGER PK | ID auto-increment |
| pin_code | TEXT UNIQUE | Codul PIN de 6 cifre |
| course_id | INTEGER FK | ID-ul cursului folosit |
| professor_id | INTEGER FK | ID-ul profesorului |
| status | TEXT | `waiting`, `playing`, `finished` |
| max_players | INTEGER | Numar maxim jucatori (default 50) |
| time_per_question | INTEGER | Secunde per intrebare (default 30) |
| created_at | TIMESTAMP | Data creare sesiune |

#### `game_results`
| Coloana | Tip | Descriere |
|---------|-----|-----------|
| id | INTEGER PK | ID auto-increment |
| session_id | INTEGER FK | ID-ul sesiunii de joc |
| player_name | TEXT | Nickname-ul jucatorului |
| user_id | INTEGER FK | ID-ul contului (optional) |
| score | INTEGER | Scorul final |
| is_alive | INTEGER | 1 = supravietuit, 0 = eliminat |
| eliminated_at_round | INTEGER | Runda in care a fost eliminat |
| finished_at | TIMESTAMP | Data finalizare |

---

## Securitate

| Masura | Detalii |
|--------|---------|
| Autentificare JWT | Token cu expirare 8 ore, HS256 |
| Rate Limiting | 60 cereri/minut per IP |
| Security Headers | X-Frame-Options: DENY, X-XSS-Protection, X-Content-Type-Options: nosniff, Referrer-Policy |
| Input Sanitization | Stergere caractere `< > " ' ;` din input-uri |
| Validare PIN | Format strict: exact 6 cifre |
| Validare Nickname | 2-20 caractere, sanitizat |
| Server Autoritar | Toata logica de joc ruleaza pe server (anti-cheat) |
| SQL Injection Protection | Parametrized queries (prepared statements) |
| CORS | Configurable per environment (`ALLOWED_ORIGINS`) |
| Answer Validation | Raspunsuri validate server-side (index 0-3) |
| Password Hashing | SHA256 + secret key salt |

---

## Deploy Online

### Varianta 1: Render.com (Recomandat - suporta WebSocket)

1. Creeaza cont pe https://render.com
2. Conecteaza repository-ul GitHub
3. **Backend** - "New Web Service":
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Environment Variables:
     - `SECRET_KEY` = (genereaza o cheie random)
     - `OPENAI_API_KEY` = (cheia ta OpenAI, optional)
     - `ALLOWED_ORIGINS` = `https://trivia-battle-royale.vercel.app`

4. **Frontend** - pe Vercel sau Netlify:
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Environment Variables:
     - `VITE_API_URL` = `https://trivia-xyz.onrender.com/api`
     - `VITE_WS_URL` = `wss://trivia-xyz.onrender.com`

### Varianta 2: Railway.app

1. Mergi la https://railway.app
2. "New Project" -> "Deploy from GitHub"
3. Selecteaza repository-ul, root: `backend`
4. Adauga env vars (SECRET_KEY, OPENAI_API_KEY)
5. Deploy -> primesti URL public

### Varianta 3: VPS (DigitalOcean / AWS EC2)

```bash
git clone <repo-url>
cd backend && pip install -r requirements.txt
python seed.py
uvicorn main:app --host 0.0.0.0 --port 8000 &

cd ../frontend && npm install && npm run build
# Serveste dist/ cu nginx
```

---

## Troubleshooting

### Backend nu porneste
```
Error: ModuleNotFoundError
```
**Solutie:** Instaleaza dependentele: `cd backend && pip install -r requirements.txt`

### Frontend nu porneste
```
Error: Cannot find module
```
**Solutie:** Instaleaza dependentele: `cd frontend && npm install`

### Port-ul 8000 este ocupat
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Linux
lsof -i :8000
kill -9 <pid>
```

### Intrebarile AI nu se genereaza
- Verifica ca ai setat `OPENAI_API_KEY` in `backend/.env`
- Formatul: `OPENAI_API_KEY=sk-...`
- Cursul trebuie sa aiba text extras (din PDF) pentru a genera intrebari

### WebSocket nu se conecteaza
- Verifica ca backend-ul ruleaza pe portul 8000
- Verifica consola browser-ului pentru erori
- PIN-ul trebuie sa fie exact 6 cifre
- Nickname-ul trebuie sa aiba 2-20 caractere

### Baza de date corupta / probleme
```bash
cd backend
del trivia.db      # Sterge baza de date
python seed.py     # Recreeaza cu date de test
# SAU reporneste backend-ul (auto-seed la prima pornire)
```

### Token expirat (401 Unauthorized)
- Token-ul JWT expira dupa 8 ore
- Fa logout si login din nou
- Token-ul se salveaza in `localStorage`

### CORS errors in browser
- Verifica `ALLOWED_ORIGINS` in configuratia backend-ului
- Pentru dezvoltare locala, default-ul este `*` (permite toate originile)
- Pentru productie, seteaza explicit URL-ul frontend-ului
