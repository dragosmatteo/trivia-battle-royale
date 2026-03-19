<template>
  <div class="page container">
    <h1 class="page-title">Panou Profesor</h1>
    <p class="page-subtitle">Gestionează cursurile și sesiunile de evaluare</p>

    <!-- Stats -->
    <div class="stat-grid" style="margin-bottom: 32px;">
      <div class="stat-card">
        <div class="stat-value">{{ courses.length }}</div>
        <div class="stat-label">Cursuri</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ totalQuestions }}</div>
        <div class="stat-label">Întrebări</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ sessions.length }}</div>
        <div class="stat-label">Sesiuni</div>
      </div>
    </div>

    <!-- Upload Course -->
    <div class="card" style="margin-bottom: 32px;">
      <h3 style="font-weight: 700; margin-bottom: 16px;">Încarcă un curs nou</h3>
      <form @submit.prevent="uploadCourse" style="display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end;">
        <div class="form-group" style="flex: 1; min-width: 200px; margin-bottom: 0;">
          <label>Titlul cursului</label>
          <input v-model="newCourse.title" class="form-input" placeholder="ex: Inteligență Artificială" required />
        </div>
        <div class="form-group" style="flex: 1; min-width: 200px; margin-bottom: 0;">
          <label>Fișier PDF</label>
          <input type="file" accept=".pdf" @change="onFileChange" class="form-input" required ref="fileInput" />
        </div>
        <button type="submit" class="btn btn-primary" :disabled="uploading">
          {{ uploading ? 'Se încarcă...' : 'Încarcă PDF' }}
        </button>
      </form>
      <div v-if="uploadMsg" style="margin-top: 12px; font-size: 13px; color: var(--success);">{{ uploadMsg }}</div>
    </div>

    <!-- Courses List -->
    <h3 style="font-weight: 700; margin-bottom: 16px;">Cursurile tale</h3>
    <div v-if="courses.length === 0" style="color: var(--text-muted); padding: 40px; text-align: center;">
      Nu ai încărcat niciun curs. Încarcă un PDF pentru a începe.
    </div>
    <div class="grid-2">
      <div v-for="course in courses" :key="course.id" class="card" style="cursor: pointer;" @click="$router.push(`/professor/course/${course.id}`)">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
          <h4 style="font-weight: 700; font-size: 17px;">{{ course.title }}</h4>
          <span style="font-size: 12px; color: var(--text-muted);">ID: {{ course.id }}</span>
        </div>
        <p style="color: var(--text-secondary); font-size: 13px; margin-bottom: 16px;">
          {{ course.description || 'Fără descriere' }}
        </p>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-primary" style="font-size: 12px; padding: 6px 12px;" @click.stop="$router.push(`/professor/course/${course.id}`)">
            Vezi întrebări
          </button>
          <button class="btn btn-success" style="font-size: 12px; padding: 6px 12px;" @click.stop="createSession(course.id)">
            Pornește joc
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../services/api'

const router = useRouter()
const courses = ref([])
const sessions = ref([])
const totalQuestions = ref(0)
const uploading = ref(false)
const uploadMsg = ref('')
const fileInput = ref(null)

const newCourse = ref({ title: '', description: '' })
let selectedFile = null

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
    uploadMsg.value = `Cursul "${data.title}" a fost încărcat cu succes!`
  } catch (e) {
    uploadMsg.value = 'Eroare: ' + (e.response?.data?.detail || 'Nu s-a putut încărca')
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
    alert(e.response?.data?.detail || 'Nu s-a putut crea sesiunea. Generați mai întâi întrebări.')
  }
}

onMounted(async () => {
  try {
    const [coursesRes, sessionsRes] = await Promise.all([
      api.get('/courses/'),
      api.get('/game/sessions'),
    ])
    courses.value = coursesRes.data
    sessions.value = sessionsRes.data

    // Count total questions
    let count = 0
    for (const c of courses.value) {
      try {
        const { data } = await api.get(`/courses/${c.id}/questions`)
        count += data.length
      } catch {}
    }
    totalQuestions.value = count
  } catch (e) {
    console.error('Failed to load dashboard:', e)
  }
})
</script>
