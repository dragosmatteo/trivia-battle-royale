# Trivia Battle Royale - Date de Logare

## Profesori

| Username | Parola | Nume | Email |
|----------|--------|------|-------|
| `admin` | `admin123` | Administrator Sistem | admin@trivia.ro |
| `prof.ionescu` | `profesor123` | Prof. Ion Ionescu | ionescu@tuiasi.ro |
| `prof.popescu` | `profesor123` | Prof. Maria Popescu | popescu@tuiasi.ro |

**Acces:** http://localhost:5173/login
**Dupa login:** redirectare catre `/professor` (Admin Dashboard)

---

## Studenti

| Username | Parola | Nume | Grupa |
|----------|--------|------|-------|
| `student1` | `student123` | Alexandru Marin | 1401A |
| `student2` | `student123` | Elena Dumitrescu | 1401A |
| `student3` | `student123` | Mihai Georgescu | 1401B |
| `student4` | `student123` | Ana Moldovan | 1401B |
| `student5` | `student123` | Radu Stanescu | 1402A |

**Acces:** http://localhost:5173/login
**Dupa login:** redirectare catre `/student` (Dashboard Student)

---

## Intrare in joc (fara cont)

Studentii pot intra intr-un joc **fara autentificare**:

**Acces:** http://localhost:5173/join
**Necesita:** PIN (6 cifre de la profesor) + Nickname (2-20 caractere)

---

## Swagger API (fara cont)

**Acces:** http://localhost:8000/docs
**Foloseste:** Butonul "Authorize" cu un JWT token obtinut din `/api/auth/login`
