<template>
  <div class="page container">
    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 8px;">
      <button class="btn btn-outline" @click="$router.push('/professor')" style="padding: 6px 12px;">&#8592; Înapoi</button>
      <h1 class="page-title" style="margin-bottom: 0;">{{ course?.title || 'Curs' }}</h1>
    </div>
    <p class="page-subtitle">Gestionează întrebările generate de AI</p>

    <!-- Generate Questions -->
    <div class="card" style="margin-bottom: 32px;">
      <h3 style="font-weight: 700; margin-bottom: 16px;">Generează întrebări cu AI</h3>
      <form @submit.prevent="generateQuestions" style="display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end;">
        <div class="form-group" style="margin-bottom: 0; min-width: 120px;">
          <label>Număr</label>
          <input v-model.number="genConfig.num_questions" type="number" min="1" max="20" class="form-input" />
        </div>
        <div class="form-group" style="margin-bottom: 0; min-width: 140px;">
          <label>Dificultate</label>
          <select v-model="genConfig.difficulty" class="form-select">
            <option value="">Mixtă</option>
            <option value="easy">Ușoară</option>
            <option value="medium">Medie</option>
            <option value="hard">Avansată</option>
          </select>
        </div>
        <div class="form-group" style="margin-bottom: 0; flex: 1; min-width: 200px;">
          <label>Capitol (opțional)</label>
          <input v-model="genConfig.chapter_hint" class="form-input" placeholder="ex: Rețele neuronale" />
        </div>
        <button type="submit" class="btn btn-primary" :disabled="generating">
          {{ generating ? 'Se generează...' : 'Generează' }}
        </button>
      </form>
      <div v-if="generating" style="margin-top: 16px; text-align: center; color: var(--text-secondary);">
        <div style="font-size: 24px; animation: pulse 1s infinite;">&#9889;</div>
        <p>AI-ul procesează materialul de curs...</p>
      </div>
    </div>

    <!-- Filter -->
    <div style="display: flex; gap: 8px; margin-bottom: 20px;">
      <button v-for="f in ['all', 'easy', 'medium', 'hard']" :key="f"
        :class="['btn', filter === f ? 'btn-primary' : 'btn-outline']"
        style="padding: 6px 14px; font-size: 12px;"
        @click="filter = f; loadQuestions()">
        {{ f === 'all' ? 'Toate' : f === 'easy' ? 'Ușoară' : f === 'medium' ? 'Medie' : 'Avansată' }}
      </button>
      <span style="margin-left: auto; color: var(--text-muted); font-size: 14px; align-self: center;">
        {{ questions.length }} întrebări
      </span>
    </div>

    <!-- Questions List -->
    <div v-if="questions.length === 0" style="color: var(--text-muted); padding: 40px; text-align: center;">
      Nu există întrebări. Generează din materialul de curs.
    </div>
    <div v-for="(q, idx) in questions" :key="q.id" class="card fade-in" style="margin-bottom: 16px;">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-weight: 800; color: var(--text-muted); font-size: 14px;">#{{ idx + 1 }}</span>
          <span :class="['badge', `badge-${q.difficulty}`]">{{ q.difficulty }}</span>
        </div>
        <button class="btn btn-danger" style="padding: 4px 10px; font-size: 11px;" @click="deleteQuestion(q.id)">
          Șterge
        </button>
      </div>
      <p style="font-weight: 600; font-size: 15px; margin-bottom: 12px;">{{ q.question_text }}</p>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px;">
        <div v-for="(opt, i) in q.options" :key="i"
          :style="{ padding: '8px 12px', borderRadius: '8px', fontSize: '13px', background: i === q.correct_index ? 'rgba(0,206,201,0.15)' : 'var(--bg-secondary)', border: i === q.correct_index ? '1px solid var(--success)' : '1px solid var(--border)' }">
          <strong>{{ ['A', 'B', 'C', 'D'][i] }}.</strong> {{ opt }}
        </div>
      </div>
      <div v-if="q.explanation" style="font-size: 13px; color: var(--text-secondary); padding: 10px; background: var(--bg-secondary); border-radius: 8px;">
        <strong>Explicație:</strong> {{ q.explanation }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../services/api'

const route = useRoute()
const courseId = parseInt(route.params.id)

const course = ref(null)
const questions = ref([])
const filter = ref('all')
const generating = ref(false)
const genConfig = ref({
  num_questions: 5,
  difficulty: '',
  chapter_hint: '',
})

async function loadQuestions() {
  try {
    const params = filter.value !== 'all' ? `?difficulty=${filter.value}` : ''
    const { data } = await api.get(`/courses/${courseId}/questions${params}`)
    questions.value = data
  } catch (e) {
    console.error('Failed to load questions:', e)
  }
}

async function generateQuestions() {
  generating.value = true
  try {
    const payload = {
      course_id: courseId,
      num_questions: genConfig.value.num_questions,
    }
    if (genConfig.value.difficulty) payload.difficulty = genConfig.value.difficulty
    if (genConfig.value.chapter_hint) payload.chapter_hint = genConfig.value.chapter_hint

    await api.post('/courses/generate-questions', payload)
    await loadQuestions()
  } catch (e) {
    alert(e.response?.data?.detail || 'Eroare la generarea întrebărilor')
  } finally {
    generating.value = false
  }
}

async function deleteQuestion(qId) {
  if (!confirm('Sigur vrei să ștergi această întrebare?')) return
  try {
    await api.delete(`/courses/${courseId}/questions/${qId}`)
    questions.value = questions.value.filter(q => q.id !== qId)
  } catch (e) {
    alert('Eroare la ștergere')
  }
}

onMounted(async () => {
  try {
    const { data: courses } = await api.get('/courses/')
    course.value = courses.find(c => c.id === courseId)
  } catch {}
  await loadQuestions()
})
</script>
