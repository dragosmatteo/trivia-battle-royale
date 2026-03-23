<template>
  <div class="page container">
    <h1 class="page-title">Panou de Control</h1>
    <p class="page-subtitle">Gestioneaza cursurile, clasele si sesiunile de evaluare</p>

    <!-- Stats Cards -->
    <div class="stat-grid" style="margin-bottom: 32px;">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_courses }}</div>
        <div class="stat-label">Cursuri</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_questions }}</div>
        <div class="stat-label">Intrebari</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_games }}</div>
        <div class="stat-label">Jocuri finalizate</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_students }}</div>
        <div class="stat-label">Studenti</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_players }}</div>
        <div class="stat-label">Participanti unici</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.avg_score }}</div>
        <div class="stat-label">Scor mediu</div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="card" style="margin-bottom: 32px;">
      <h3 style="font-weight: 700; margin-bottom: 16px;">Actiuni rapide</h3>
      <div style="display: flex; gap: 12px; flex-wrap: wrap;">
        <button class="btn btn-primary btn-lg" @click="$router.push('/professor/courses')">
          + Curs nou
        </button>
        <button class="btn btn-success btn-lg" @click="$router.push('/professor/classes')">
          + Clasa noua
        </button>
        <button class="btn btn-outline btn-lg" @click="$router.push('/professor/history')">
          Istoric jocuri
        </button>
      </div>
    </div>

    <!-- Two columns: Chat Creator + Recent Games -->
    <div class="grid-2" style="margin-bottom: 32px;">
      <!-- Chat-style Course Creator -->
      <div class="card" style="display: flex; flex-direction: column; height: 420px; padding: 0; overflow: hidden;">
        <div style="padding: 16px 20px; border-bottom: 1px solid var(--border);">
          <h3 style="font-weight: 700; margin: 0;">Creeaza un curs</h3>
          <p style="font-size: 12px; color: var(--text-muted); margin: 4px 0 0 0;">Scrie titlul, adauga o descriere sau ataseaza PDF-uri</p>
        </div>

        <!-- Messages area -->
        <div ref="chatArea" style="flex: 1; overflow-y: auto; padding: 16px 20px; display: flex; flex-direction: column; gap: 12px;">
          <!-- System welcome -->
          <div class="chat-msg chat-system">
            <div class="chat-bubble system">
              Salut! Cum vrei sa se numeasca noul curs?
            </div>
          </div>

          <!-- Message history -->
          <div v-for="(msg, i) in chatMessages" :key="i" :class="['chat-msg', msg.from === 'user' ? 'chat-user' : 'chat-system']">
            <div :class="['chat-bubble', msg.from === 'user' ? 'user' : 'system']">
              <!-- File attachment display -->
              <div v-if="msg.file" style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                <span style="font-size: 18px;">&#128196;</span>
                <span style="font-size: 13px; font-weight: 600;">{{ msg.file }}</span>
              </div>
              <span v-html="msg.text"></span>
            </div>
          </div>

          <!-- Typing indicator -->
          <div v-if="systemTyping" class="chat-msg chat-system">
            <div class="chat-bubble system">
              <span class="typing-dots">
                <span></span><span></span><span></span>
              </span>
            </div>
          </div>
        </div>

        <!-- Input area -->
        <div style="padding: 12px 16px; border-top: 1px solid var(--border); display: flex; gap: 8px; align-items: center;">
          <label class="attach-btn" :class="{ disabled: creating }">
            <input type="file" accept=".pdf" multiple @change="onFilesSelected" style="display: none;" :disabled="creating" />
            <span style="font-size: 20px; cursor: pointer;" title="Ataseaza PDF">&#128206;</span>
          </label>
          <input
            ref="chatInput"
            v-model="userInput"
            class="form-input"
            style="flex: 1; margin: 0; font-size: 14px;"
            :placeholder="inputPlaceholder"
            @keydown.enter.prevent="sendMessage"
            :disabled="creating"
          />
          <button class="btn btn-primary" style="padding: 8px 16px; font-size: 14px;" @click="sendMessage" :disabled="!userInput.trim() && !pendingFiles.length || creating">
            &#10148;
          </button>
        </div>
      </div>

      <!-- Recent Games -->
      <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <h3 style="font-weight: 700;">Jocuri recente</h3>
          <button class="btn btn-outline" style="font-size: 12px; padding: 6px 12px;" @click="$router.push('/professor/history')">
            Vezi toate
          </button>
        </div>
        <div v-if="stats.recent_games && stats.recent_games.length > 0">
          <div
            v-for="g in stats.recent_games"
            :key="g.id"
            style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--border);"
          >
            <div>
              <div style="font-weight: 600; font-size: 14px;">{{ g.course_title }}</div>
              <div style="font-size: 12px; color: var(--text-muted);">{{ formatDate(g.created_at) }} &middot; {{ g.player_count }} jucatori</div>
            </div>
            <div style="text-align: right;">
              <div style="font-size: 13px; color: var(--gold); font-weight: 600;">{{ g.winner }}</div>
              <div style="font-size: 11px; color: var(--text-muted);">PIN: {{ g.pin_code }}</div>
            </div>
          </div>
        </div>
        <div v-else style="color: var(--text-muted); text-align: center; padding: 30px 0; font-size: 14px;">
          Niciun joc finalizat inca.
        </div>
      </div>
    </div>

    <!-- Courses List -->
    <h3 style="font-weight: 700; margin-bottom: 16px;">Cursurile tale</h3>
    <div v-if="courses.length === 0" style="color: var(--text-muted); padding: 40px; text-align: center;">
      Nu ai incarcat niciun curs. Foloseste chat-ul de mai sus pentru a crea unul.
    </div>
    <div class="grid-2">
      <div v-for="course in courses" :key="course.id" class="card" style="cursor: pointer;" @click="$router.push(`/professor/course/${course.id}`)">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
          <h4 style="font-weight: 700; font-size: 17px;">{{ course.title }}</h4>
          <span style="font-size: 12px; color: var(--text-muted);">ID: {{ course.id }}</span>
        </div>
        <p style="color: var(--text-secondary); font-size: 13px; margin-bottom: 16px;">
          {{ course.description || 'Fara descriere' }}
        </p>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-primary" style="font-size: 12px; padding: 6px 12px;" @click.stop="$router.push(`/professor/course/${course.id}`)">
            Vezi intrebari
          </button>
          <button class="btn btn-success" style="font-size: 12px; padding: 6px 12px;" @click.stop="createSession(course.id)">
            Porneste joc
          </button>
          <button class="btn btn-danger" style="font-size: 12px; padding: 6px 12px;" @click.stop="deleteCourse(course.id, course.title)">
            Sterge
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../services/api'

const router = useRouter()
const courses = ref([])
const stats = ref({
  total_games: 0,
  total_players: 0,
  total_questions: 0,
  total_courses: 0,
  total_students: 0,
  avg_score: 0,
  recent_games: [],
})

// Chat course creator state
const chatMessages = ref([])
const userInput = ref('')
const chatArea = ref(null)
const chatInput = ref(null)
const systemTyping = ref(false)
const creating = ref(false)
const pendingFiles = ref([])

// Chat flow state
const chatStep = ref('title') // title, description, files, confirm, done
const courseData = ref({ title: '', description: '', files: [] })

const inputPlaceholder = computed(() => {
  switch (chatStep.value) {
    case 'title': return 'Scrie titlul cursului...'
    case 'description': return 'Adauga o descriere sau scrie "skip"...'
    case 'files': return 'Ataseaza PDF sau scrie "gata"...'
    case 'confirm': return 'Scrie "da" pentru a crea cursul...'
    case 'done': return 'Cursul a fost creat!'
    default: return 'Scrie un mesaj...'
  }
})

function scrollToBottom() {
  nextTick(() => {
    if (chatArea.value) {
      chatArea.value.scrollTop = chatArea.value.scrollHeight
    }
  })
}

function addUserMessage(text, file = null) {
  chatMessages.value.push({ from: 'user', text, file })
  scrollToBottom()
}

async function addSystemMessage(text) {
  systemTyping.value = true
  scrollToBottom()
  await new Promise(r => setTimeout(r, 400 + Math.random() * 400))
  systemTyping.value = false
  chatMessages.value.push({ from: 'system', text })
  scrollToBottom()
}

async function sendMessage() {
  const text = userInput.value.trim()

  // If there are pending files and no text, just process the files
  if (!text && pendingFiles.value.length > 0) {
    await processFiles()
    return
  }

  if (!text) return
  userInput.value = ''

  switch (chatStep.value) {
    case 'title':
      addUserMessage(text)
      courseData.value.title = text
      chatStep.value = 'description'
      await addSystemMessage(`Titlu: <strong>${text}</strong>. Adauga o descriere pentru curs, sau scrie <strong>skip</strong> daca nu vrei.`)
      break

    case 'description':
      addUserMessage(text)
      if (text.toLowerCase() === 'skip' || text.toLowerCase() === '-') {
        courseData.value.description = ''
        chatStep.value = 'files'
        await addSystemMessage('OK, fara descriere. Acum poti atasa PDF-uri cu butonul &#128206; sau scrie <strong>gata</strong> pentru a crea cursul fara fisiere.')
      } else {
        courseData.value.description = text
        chatStep.value = 'files'
        await addSystemMessage(`Descriere salvata. Acum poti atasa PDF-uri cu butonul &#128206; sau scrie <strong>gata</strong> pentru a crea cursul.`)
      }
      break

    case 'files':
      if (text.toLowerCase() === 'gata' || text.toLowerCase() === 'done' || text.toLowerCase() === 'da') {
        await createCourse()
      } else {
        // Treat text input as additional description
        addUserMessage(text)
        courseData.value.description = courseData.value.description
          ? courseData.value.description + '\n' + text
          : text
        await addSystemMessage('Am adaugat informatia la curs. Ataseaza PDF-uri sau scrie <strong>gata</strong>.')
      }
      break

    case 'confirm':
      addUserMessage(text)
      if (text.toLowerCase().startsWith('da') || text.toLowerCase().startsWith('yes') || text.toLowerCase() === 'ok') {
        await createCourse()
      } else {
        chatStep.value = 'files'
        await addSystemMessage('OK, poti continua sa adaugi informatii. Scrie <strong>gata</strong> cand esti pregatit.')
      }
      break

    case 'done':
      // Reset for new course
      courseData.value = { title: '', description: '', files: [] }
      chatStep.value = 'title'
      chatMessages.value = []
      await addSystemMessage('Salut! Cum vrei sa se numeasca noul curs?')
      // Process any text as new title
      if (text) {
        userInput.value = text
        await sendMessage()
      }
      break
  }
}

async function onFilesSelected(e) {
  const files = Array.from(e.target.files)
  if (!files.length) return

  for (const file of files) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      await addSystemMessage(`<span style="color: var(--danger);">&#10060; ${file.name}</span> nu este un PDF. Doar fisiere PDF sunt acceptate.`)
      continue
    }
    if (file.size > 20 * 1024 * 1024) {
      await addSystemMessage(`<span style="color: var(--danger);">&#10060; ${file.name}</span> este prea mare (max 20 MB).`)
      continue
    }

    courseData.value.files.push(file)
    addUserMessage('', file.name)
    await addSystemMessage(`&#128196; <strong>${file.name}</strong> atasat (${(file.size / 1024).toFixed(0)} KB). Poti atasa mai multe sau scrie <strong>gata</strong>.`)
  }

  // If we were at title or description step, auto-advance
  if (chatStep.value === 'title' && !courseData.value.title) {
    await addSystemMessage('Am primit PDF-ul! Acum scrie titlul cursului.')
  } else if (chatStep.value === 'description') {
    chatStep.value = 'files'
  } else if (chatStep.value === 'title' && courseData.value.title) {
    chatStep.value = 'files'
  }

  // Reset the file input
  e.target.value = ''
}

async function processFiles() {
  pendingFiles.value = []
}

async function createCourse() {
  creating.value = true
  addUserMessage('gata')
  await addSystemMessage('Se creeaza cursul...')

  try {
    const formData = new FormData()
    formData.append('title', courseData.value.title)
    formData.append('description', courseData.value.description || '')

    // Upload the first file as the main PDF
    if (courseData.value.files.length > 0) {
      formData.append('pdf', courseData.value.files[0])
    }

    const { data: newCourse } = await api.post('/courses/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    courses.value.unshift(newCourse)
    stats.value.total_courses += 1

    // Upload additional files as materials
    for (let i = 1; i < courseData.value.files.length; i++) {
      const matForm = new FormData()
      matForm.append('file', courseData.value.files[i])
      try {
        await api.post(`/courses/${newCourse.id}/materials`, matForm, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
      } catch (err) {
        await addSystemMessage(`<span style="color: var(--warning);">&#9888; ${courseData.value.files[i].name} nu a putut fi incarcat.</span>`)
      }
    }

    chatStep.value = 'done'
    const filesText = courseData.value.files.length > 0
      ? ` cu ${courseData.value.files.length} fisier${courseData.value.files.length > 1 ? 'e' : ''}`
      : ''
    await addSystemMessage(
      `&#10004; Cursul <strong>"${newCourse.title}"</strong> a fost creat${filesText}! ` +
      `<br><br><a href="#" onclick="return false" style="color: var(--accent); text-decoration: underline;" id="go-to-course-${newCourse.id}">Deschide cursul</a> pentru a genera intrebari.` +
      `<br><br><span style="color: var(--text-muted); font-size: 12px;">Scrie orice pentru a crea alt curs.</span>`
    )

    // Add click handler for the course link
    nextTick(() => {
      const link = document.getElementById(`go-to-course-${newCourse.id}`)
      if (link) {
        link.addEventListener('click', (e) => {
          e.preventDefault()
          router.push(`/professor/course/${newCourse.id}`)
        })
      }
    })
  } catch (e) {
    const detail = e.response?.data?.detail || 'Eroare la crearea cursului'
    await addSystemMessage(`<span style="color: var(--danger);">&#10060; ${detail}</span><br>Incearca din nou.`)
    chatStep.value = 'files'
  } finally {
    creating.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr || dateStr === 'None') return '-'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString('ro-RO', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function deleteCourse(courseId, title) {
  if (!confirm(`Sigur vrei sa stergi cursul "${title}"?\n\nAceasta actiune va sterge toate intrebarile, materialele si sesiunile asociate.`)) return
  try {
    await api.delete(`/courses/${courseId}`)
    courses.value = courses.value.filter(c => c.id !== courseId)
    stats.value.total_courses = Math.max(0, stats.value.total_courses - 1)
  } catch (e) {
    alert(e.response?.data?.detail || 'Eroare la stergerea cursului')
  }
}

async function createSession(courseId) {
  try {
    const { data } = await api.post('/game/create-session', {
      course_id: courseId,
      num_questions: 10,
      time_per_question: 30,
    })
    router.push(`/professor/game/${data.pin_code}`)
  } catch (e) {
    alert(e.response?.data?.detail || 'Nu s-a putut crea sesiunea. Generati mai intai intrebari.')
  }
}

onMounted(async () => {
  try {
    const [coursesRes, statsRes] = await Promise.all([
      api.get('/courses/'),
      api.get('/admin/stats'),
    ])
    courses.value = coursesRes.data
    stats.value = statsRes.data
  } catch (e) {
    console.error('Failed to load dashboard:', e)
    try {
      const { data } = await api.get('/courses/')
      courses.value = data
    } catch {}
  }
})
</script>

<style scoped>
.chat-msg {
  display: flex;
}
.chat-user {
  justify-content: flex-end;
}
.chat-system {
  justify-content: flex-start;
}
.chat-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}
.chat-bubble.user {
  background: var(--accent);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.chat-bubble.system {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-bottom-left-radius: 4px;
  border: 1px solid var(--border);
}
.attach-btn {
  display: flex;
  align-items: center;
  padding: 4px;
  border-radius: 8px;
  transition: background 0.2s;
}
.attach-btn:hover:not(.disabled) {
  background: var(--bg-secondary);
}
.attach-btn.disabled {
  opacity: 0.4;
  pointer-events: none;
}
.typing-dots {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  height: 20px;
}
.typing-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: typingBounce 1.2s ease-in-out infinite;
}
.typing-dots span:nth-child(2) { animation-delay: 0.15s; }
.typing-dots span:nth-child(3) { animation-delay: 0.3s; }
@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}
</style>
