<template>
  <div class="page container">
    <h1 class="page-title">Panou Student</h1>
    <p class="page-subtitle">Bun venit, {{ authStore.user?.full_name }}!</p>

    <!-- Stats Overview -->
    <div class="stat-grid" style="margin-bottom: 32px;">
      <div class="stat-card">
        <div class="stat-value">{{ myStats.total_games }}</div>
        <div class="stat-label">Jocuri jucate</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: var(--success);">{{ myStats.avg_score }}</div>
        <div class="stat-label">Scor mediu</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: var(--gold);">{{ myStats.best_score }}</div>
        <div class="stat-label">Cel mai bun scor</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: var(--accent);">{{ myStats.win_rate }}%</div>
        <div class="stat-label">Rata victorie</div>
      </div>
    </div>

    <!-- Quick Join -->
    <div class="card" style="margin-bottom: 32px;">
      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <span style="font-size: 24px;">&#127918;</span>
        <h3 style="font-weight: 700; margin: 0;">Intra intr-un joc</h3>
      </div>
      <form @submit.prevent="joinGame" style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
        <input v-model="pinCode" class="form-input" placeholder="Cod PIN (6 cifre)"
          style="width: 200px; text-align: center; font-size: 20px; font-weight: 700; letter-spacing: 4px;" maxlength="6" />
        <input v-model="nickname" class="form-input" placeholder="Nickname" style="width: 180px;" maxlength="20" />
        <button type="submit" class="btn btn-success btn-lg" :disabled="!pinCode || !nickname">
          Intra in joc
        </button>
      </form>
      <div v-if="joinError" style="margin-top: 12px; color: var(--danger); font-size: 13px;">{{ joinError }}</div>
    </div>

    <div class="grid-2" style="margin-bottom: 32px;">
      <!-- Game History -->
      <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; gap: 12px; flex-wrap: wrap;">
          <h3 style="font-weight: 700; margin: 0;">Istoricul jocurilor</h3>
          <select v-if="uniqueCourses.length > 1" v-model="selectedCourse" class="form-select"
            style="width: auto; min-width: 160px; font-size: 13px; color: var(--text-muted);">
            <option value="">Toate materiile</option>
            <option v-for="course in uniqueCourses" :key="course" :value="course">{{ course }}</option>
          </select>
        </div>
        <div v-if="filteredHistory.length === 0" style="color: var(--text-muted); text-align: center; padding: 30px 0; font-size: 14px;">
          Nu ai participat la niciun joc inca.
        </div>
        <div v-for="game in filteredHistory" :key="game.id"
          style="padding: 12px 0; border-bottom: 1px solid var(--border);">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
              <div style="font-weight: 600; font-size: 14px;">{{ game.course_title }}</div>
              <div style="font-size: 12px; color: var(--text-muted);">{{ formatDate(game.created_at) }}</div>
            </div>
            <div style="text-align: right;">
              <div style="font-size: 18px; font-weight: 800; color: var(--accent);">{{ game.score }} pts</div>
              <div v-if="game.league === 'champions'" style="font-size: 11px; color: var(--gold);">&#11088; Liga Campionilor</div>
              <div v-else-if="game.league === 'challengers'" style="font-size: 11px; color: var(--accent);">&#128170; Liga Provocarii</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Performance by Subject -->
      <div class="card">
        <h3 style="font-weight: 700; margin-bottom: 16px;">Performanta pe materii</h3>
        <div v-if="subjectStats.length === 0" style="color: var(--text-muted); text-align: center; padding: 30px 0; font-size: 14px;">
          Joaca pentru a vedea statisticile.
        </div>
        <div v-for="subject in subjectStats" :key="subject.course_title"
          style="padding: 10px 0; border-bottom: 1px solid var(--border);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-weight: 600; font-size: 14px;">{{ subject.course_title }}</span>
            <span style="font-size: 13px; color: var(--text-muted);">{{ subject.games_played }} jocuri</span>
          </div>
          <div style="display: flex; gap: 16px; font-size: 12px; color: var(--text-secondary);">
            <span>Scor mediu: <strong style="color: var(--accent);">{{ subject.avg_score }}</strong></span>
            <span>Best: <strong style="color: var(--gold);">{{ subject.best_score }}</strong></span>
          </div>
          <!-- Progress bar -->
          <div style="margin-top: 6px; height: 4px; background: var(--bg-secondary); border-radius: 2px; overflow: hidden;">
            <div :style="{ width: Math.min(subject.avg_score / 3, 100) + '%', background: progressColor(subject.avg_score), height: '100%', borderRadius: '2px', transition: 'width 0.5s ease' }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Available Courses -->
    <h3 style="font-weight: 700; margin-bottom: 16px;">Cursuri disponibile</h3>
    <div v-if="courses.length === 0" style="color: var(--text-muted); padding: 40px; text-align: center;">
      Nu sunt cursuri disponibile momentan.
    </div>
    <div class="grid-2">
      <div v-for="course in courses" :key="course.id" class="card">
        <h4 style="font-weight: 700; margin-bottom: 8px;">{{ course.title }}</h4>
        <p style="color: var(--text-secondary); font-size: 13px;">{{ course.description || 'Fara descriere' }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import api from '../../services/api'

const router = useRouter()
const authStore = useAuthStore()

const courses = ref([])
const history = ref([])
const myStats = ref({ total_games: 0, avg_score: 0, best_score: 0, win_rate: 0 })
const pinCode = ref('')
const nickname = ref(authStore.user?.username || '')
const joinError = ref('')
const selectedCourse = ref('')

const uniqueCourses = computed(() => {
  const titles = new Set(history.value.map(g => g.course_title).filter(Boolean))
  return [...titles].sort()
})

const filteredHistory = computed(() => {
  if (!selectedCourse.value) return history.value
  return history.value.filter(g => g.course_title === selectedCourse.value)
})

const subjectStats = computed(() => {
  const map = {}
  for (const game of history.value) {
    const title = game.course_title || 'Necunoscut'
    if (!map[title]) {
      map[title] = { course_title: title, scores: [], games_played: 0 }
    }
    map[title].scores.push(game.score)
    map[title].games_played++
  }
  return Object.values(map).map(s => ({
    ...s,
    avg_score: Math.round(s.scores.reduce((a, b) => a + b, 0) / s.scores.length),
    best_score: Math.max(...s.scores),
  }))
})

function progressColor(score) {
  if (score >= 200) return 'var(--gold)'
  if (score >= 100) return 'var(--success)'
  return 'var(--warning)'
}

function formatDate(dateStr) {
  if (!dateStr || dateStr === 'None') return '-'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString('ro-RO', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function joinGame() {
  joinError.value = ''
  try {
    await api.get(`/game/check-pin/${pinCode.value}`)
    router.push(`/play/${pinCode.value}?nickname=${encodeURIComponent(nickname.value)}`)
  } catch (e) {
    joinError.value = e.response?.data?.detail || 'PIN invalid sau sesiunea nu este disponibila'
  }
}

onMounted(async () => {
  const requests = [
    api.get('/courses/').catch(() => ({ data: [] })),
    api.get('/game/my-history').catch(() => ({ data: [] })),
    api.get('/game/my-stats').catch(() => ({ data: { total_games: 0, avg_score: 0, best_score: 0, win_rate: 0 } })),
  ]
  const [coursesRes, historyRes, statsRes] = await Promise.all(requests)
  courses.value = coursesRes.data
  history.value = historyRes.data
  myStats.value = statsRes.data
})
</script>
