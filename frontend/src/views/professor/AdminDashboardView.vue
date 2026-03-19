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

    <!-- Two columns: Upload + Recent Games -->
    <div class="grid-2" style="margin-bottom: 32px;">
      <!-- Upload Course -->
      <div class="card">
        <h3 style="font-weight: 700; margin-bottom: 16px;">Incarca un curs nou</h3>
        <form @submit.prevent="uploadCourse">
          <div class="form-group">
            <label>Titlul cursului</label>
            <input v-model="newCourse.title" class="form-input" placeholder="ex: Inteligenta Artificiala" required />
          </div>
          <div class="form-group">
            <label>Fisier PDF</label>
            <input type="file" accept=".pdf" @change="onFileChange" class="form-input" required ref="fileInput" />
          </div>
          <button type="submit" class="btn btn-primary" :disabled="uploading" style="width: 100%;">
            {{ uploading ? 'Se incarca...' : 'Incarca PDF' }}
          </button>
        </form>
        <div v-if="uploadMsg" style="margin-top: 12px; font-size: 13px; color: var(--success);">{{ uploadMsg }}</div>
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
      Nu ai incarcat niciun curs. Incarca un PDF pentru a incepe.
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
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
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
const uploading = ref(false)
const uploadMsg = ref('')
const fileInput = ref(null)
const newCourse = ref({ title: '', description: '' })
let selectedFile = null

function formatDate(dateStr) {
  if (!dateStr || dateStr === 'None') return '-'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString('ro-RO', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function onFileChange(e) {
  selectedFile = e.target.files[0]
}

async function uploadCourse() {
  if (!selectedFile || !newCourse.value.title) return
  uploading.value = true
  uploadMsg.value = ''
  try {
    const formData = new FormData()
    formData.append('title', newCourse.value.title)
    formData.append('description', newCourse.value.description || '')
    formData.append('pdf', selectedFile)
    const { data } = await api.post('/courses/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    courses.value.unshift(data)
    newCourse.value = { title: '', description: '' }
    selectedFile = null
    if (fileInput.value) fileInput.value.value = ''
    uploadMsg.value = `Cursul "${data.title}" a fost incarcat cu succes!`
    stats.value.total_courses += 1
  } catch (e) {
    uploadMsg.value = 'Eroare: ' + (e.response?.data?.detail || 'Nu s-a putut incarca')
  } finally {
    uploading.value = false
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
    // Fallback: still load courses if stats fail
    try {
      const { data } = await api.get('/courses/')
      courses.value = data
    } catch {}
  }
})
</script>
