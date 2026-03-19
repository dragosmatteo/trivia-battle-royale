# Trivia Battle Royale - Tutorial Complet

## Credentiale de Test

| Rol | Username | Parola | Nume |
|-----|----------|--------|------|
| Profesor | `admin` | `admin123` | Administrator Sistem |
| Profesor | `prof.ionescu` | `profesor123` | Prof. Ion Ionescu |
| Profesor | `prof.popescu` | `profesor123` | Prof. Maria Popescu |
| Student | `student1` | `student123` | Alexandru Marin (1401A) |
| Student | `student2` | `student123` | Elena Dumitrescu (1401A) |
| Student | `student3` | `student123` | Mihai Georgescu (1401B) |
| Student | `student4` | `student123` | Ana Moldovan (1401B) |
| Student | `student5` | `student123` | Radu Stanescu (1402A) |

## Rulare Locala

### Cerinte
- Python 3.11+
- Node.js 18+

### Pornire
```bash
# 1. Backend (terminal 1)
cd backend
pip install -r requirements.txt
python seed.py          # Creeaza conturi de test
python -m uvicorn main:app --port 8000 --reload

# 2. Frontend (terminal 2)
cd frontend
npm install
npm run dev
```

Sau dublu-click pe `start.bat` (Windows).

Deschide: http://localhost:5173

## Flux de Utilizare

### 1. Profesor - Pregatirea cursului
1. Mergi la http://localhost:5173/login
2. Logheaza-te cu `prof.ionescu` / `profesor123`
3. Pe Dashboard, completeaza "Titlul cursului" si alege un PDF
4. Click "Incarca PDF" -> textul se extrage automat
5. Click "Vezi intrebari" pe card-ul cursului
6. Configureaza: numar intrebari, dificultate, capitol (optional)
7. Click "Genereaza" -> AI-ul creeaza intrebari automat
8. Revizuieste, editeaza sau sterge intrebarile nedorite

### 2. Profesor - Pornirea jocului
1. De pe Dashboard, click "Porneste joc" pe cursul dorit
2. Se afiseaza Camera de Asteptare cu un cod PIN de 6 cifre
3. Distribui PIN-ul studentilor (verbal, pe ecran, prin chat)
4. Asteapta ca studentii sa se conecteze (ii vezi in lista)
5. Cand sunt suficienti, click "Porneste Jocul"

### 3. Student - Intrarea in joc
1. Mergi la http://localhost:5173/join
2. Introdu codul PIN primit de la profesor
3. Alege un Nickname (pseudonim)
4. Click "Intra in joc"
5. Asteapta in Camera de Asteptare pana profesorul porneste jocul

### 4. Desfasurarea Battle Royale
1. **Intrebari cu timer** - Fiecare intrebare are un cronometru (30s default)
2. **Raspuns** - Click pe varianta corecta, raspunsul se blocheaza
3. **Rezultat** - Dupa expirarea timpului sau cand toti raspund:
   - Corect: primesti puncte (100 baza + bonus viteza)
   - Serie 3+: bonus suplimentar de 50 puncte
4. **Eliminare** - Daca nu raspunzi la timp -> eliminat
5. **Sudden Death** (ultimele 5 intrebari): raspuns gresit = eliminat instant
6. **Spectator** - Dupa eliminare, poti urmari jocul
7. **Castigator** - Ultimul jucator ramas "in viata"

## Deploy Online (pentru testare multi-player)

### Varianta 1: Render.com (Recomandat - suporta WebSocket)

1. Creeaza cont gratuit pe https://render.com
2. Conecteaza repository-ul GitHub
3. "New Web Service" -> selecteaza repository-ul
4. Configureaza:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Adauga Environment Variables:
   - `SECRET_KEY` = (genereaza una random)
   - `OPENAI_API_KEY` = (optional, pentru intrebari AI reale)
   - `ALLOWED_ORIGINS` = `https://trivia-battle-royale.vercel.app`
6. Click Deploy -> primesti URL-ul backend-ului (ex: `https://trivia-xyz.onrender.com`)

7. Pentru frontend, pe Vercel:
   - Import repository-ul
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - Adauga Environment Variables:
     - `VITE_API_URL` = `https://trivia-xyz.onrender.com/api`
     - `VITE_WS_URL` = `wss://trivia-xyz.onrender.com`

### Varianta 2: Railway.app (Alternativa simpla)

1. Mergi la https://railway.app
2. "New Project" -> "Deploy from GitHub"
3. Selecteaza repository-ul, root: `backend`
4. Railway detecteaza automat Python
5. Adauga env vars (SECRET_KEY, OPENAI_API_KEY)
6. Deploy -> primesti URL public

### Varianta 3: VPS (Digital Ocean / AWS EC2)

```bash
# Pe server
git clone <repo-url>
cd backend && pip install -r requirements.txt
python seed.py
uvicorn main:app --host 0.0.0.0 --port 8000 &

cd ../frontend && npm install && npm run build
# Serveste dist/ cu nginx
```

## Arhitectura Tehnica

```
Frontend (Vue.js 3)          Backend (FastAPI)
+------------------+         +------------------+
|  Login/Register  |  REST   |  Auth (JWT)      |
|  Dashboard Prof  |-------->|  Courses API     |
|  Dashboard Stud  |  HTTP   |  Questions API   |
|  Course Detail   |         |  Game Sessions   |
+------------------+         +------------------+
        |                            |
        |     WebSocket              |
        +--------------------------->|
        |  - join/leave              |  Game Manager
        |  - questions               |  (Singleton)
        |  - answers                 |  - Rooms
        |  - round results           |  - Players
        |  - elimination             |  - Timer
        |  - game over               |  - Elimination
        +<---------------------------+  - Leaderboard
```

## Structura Fisiere

```
backend/
  main.py              # FastAPI app + WebSocket endpoints
  config.py            # Configuratie (secret key, paths)
  seed.py              # Creeaza date de test
  models/
    database.py        # SQLite schema + conexiune
    schemas.py         # Pydantic validation models
  routers/
    auth.py            # Register, Login, JWT
    courses.py         # Upload PDF, Generate Questions
    game.py            # Create/Join Sessions
  services/
    pdf_processor.py   # Extract text din PDF
    ai_generator.py    # RAG pipeline + OpenAI
    game_manager.py    # WebSocket game engine (Singleton)

frontend/
  src/
    App.vue            # Layout + Navbar
    router/index.js    # Route definitions
    stores/
      auth.js          # Pinia - user state
      game.js          # Pinia - game state (isAlive, timer, etc)
    services/
      api.js           # Axios HTTP client
      websocket.js     # WebSocket client
    views/
      LoginView.vue       # Pagina de login
      RegisterView.vue    # Pagina de inregistrare
      professor/
        DashboardView.vue    # Panou profesor
        CourseDetailView.vue # Intrebari curs
        GameControlView.vue  # Control joc (PIN, start, leaderboard)
      student/
        DashboardView.vue    # Panou student
        JoinGameView.vue     # Intro PIN + nickname
        GamePlayView.vue     # Jocul propriu-zis
```

## Securitate Implementata

- **Autentificare JWT** cu expirare (8 ore)
- **Rate limiting** (60 req/min per IP)
- **Security headers** (X-Frame-Options, X-XSS-Protection, etc.)
- **Input sanitization** pe nickname si parametri WebSocket
- **Validare PIN** (format strict 6 cifre)
- **Server Autoritar** - toata logica de joc ruleaza pe server
- **Parametrized SQL queries** - protectie SQL injection
- **CORS configurable** per environment
- **Answer validation** - raspunsurile se valideaza server-side (0-3)
