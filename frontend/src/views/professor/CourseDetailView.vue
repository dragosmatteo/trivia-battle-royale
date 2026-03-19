<template>
  <div class="page container">
    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 8px;">
      <button class="btn btn-outline" @click="$router.push('/professor')" style="padding: 6px 12px;">&#8592; Înapoi</button>
      <h1 class="page-title" style="margin-bottom: 0;">{{ course?.title || 'Curs' }}</h1>
    </div>
    <p class="page-subtitle">Gestionează întrebările generate de AI</p>

    <!-- Generate Questions -->
    <div class="card" style="margin-bottom: 24px;">
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
          {{ generating ? 'Se generează...' : 'Generează cu AI' }}
        </button>
      </form>
      <div v-if="generating" style="margin-top: 16px; text-align: center; color: var(--text-secondary);">
        <div style="font-size: 24px; animation: pulse 1s infinite;">&#9889;</div>
        <p>AI-ul procesează materialul de curs...</p>
      </div>
    </div>

    <!-- Add Manual Question -->
    <div class="card" style="margin-bottom: 24px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <h3 style="font-weight: 700; margin: 0;">Adaugă întrebare manual</h3>
        <button class="btn btn-outline" style="padding: 6px 14px; font-size: 13px;" @click="toggleManualForm">
          {{ showManualForm ? 'Anulează' : '+ Adaugă' }}
        </button>
      </div>
      <form v-if="showManualForm" @submit.prevent="saveManualQuestion">
        <div class="form-group">
          <label>Textul întrebării</label>
          <input v-model="manualQuestion.question_text" class="form-input" placeholder="Scrie întrebarea aici..." required />
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div v-for="(_, i) in 4" :key="i" class="form-group">
            <label>
              Opțiunea {{ ['A', 'B', 'C', 'D'][i] }}
              <span v-if="manualQuestion.correct_index === i" style="color: var(--success); font-weight: 700;"> ✓ Corect</span>
            </label>
            <div style="display: flex; gap: 8px;">
              <input v-model="manualQuestion.options[i]" class="form-input" style="flex: 1;" :placeholder="'Răspuns ' + ['A','B','C','D'][i]" required />
              <button type="button" class="btn" :class="manualQuestion.correct_index === i ? 'btn-success' : 'btn-outline'"
                style="padding: 6px 12px; font-size: 12px; white-space: nowrap;"
                @click="manualQuestion.correct_index = i">
                {{ manualQuestion.correct_index === i ? '✓' : 'Corect' }}
              </button>
            </div>
          </div>
        </div>
        <div style="display: flex; gap: 12px; flex-wrap: wrap;">
          <div class="form-group" style="min-width: 140px;">
            <label>Dificultate</label>
            <select v-model="manualQuestion.difficulty" class="form-select">
              <option value="easy">Ușoară</option>
              <option value="medium">Medie</option>
              <option value="hard">Avansată</option>
            </select>
          </div>
          <div class="form-group" style="flex: 1;">
            <label>Explicație (opțional)</label>
            <input v-model="manualQuestion.explanation" class="form-input" placeholder="De ce este corect acest răspuns?" />
          </div>
        </div>
        <button type="submit" class="btn btn-success" style="margin-top: 8px;">Salvează întrebarea</button>
      </form>
    </div>

    <!-- Filter -->
    <div style="display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap;">
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
      Nu există întrebări. Generează din materialul de curs sau adaugă manual.
    </div>
    <div v-for="(q, idx) in questions" :key="q.id" class="card fade-in" style="margin-bottom: 16px;">
      <!-- View Mode -->
      <div v-if="editingId !== q.id">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-weight: 800; color: var(--text-muted); font-size: 14px;">#{{ idx + 1 }}</span>
            <span :class="['badge', `badge-${q.difficulty}`]">{{ q.difficulty }}</span>
          </div>
          <div style="display: flex; gap: 6px;">
            <button class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" @click="startEdit(q)">
              &#9998; Editează
            </button>
            <button class="btn btn-danger" style="padding: 4px 10px; font-size: 11px;" @click="deleteQuestion(q.id)">
              &#128465; Șterge
            </button>
          </div>
        </div>
        <p style="font-weight: 600; font-size: 15px; margin-bottom: 12px;">{{ q.question_text }}</p>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px;">
          <div v-for="(opt, i) in q.options" :key="i"
            :style="{ padding: '8px 12px', borderRadius: '8px', fontSize: '13px', background: i === q.correct_index ? 'rgba(0,206,201,0.15)' : 'var(--bg-secondary)', border: i === q.correct_index ? '1px solid var(--success)' : '1px solid var(--border)' }">
            <strong>{{ ['A', 'B', 'C', 'D'][i] }}.</strong> {{ opt }}
            <span v-if="i === q.correct_index" style="color: var(--success); font-weight: 700;"> ✓</span>
          </div>
        </div>
        <div v-if="q.explanation" style="font-size: 13px; color: var(--text-secondary); padding: 10px; background: var(--bg-secondary); border-radius: 8px;">
          <strong>Explicație:</strong> {{ q.explanation }}
        </div>
      </div>

      <!-- Edit Mode -->
      <div v-else>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <h4 style="font-weight: 700; color: var(--accent);">Editare întrebare #{{ idx + 1 }}</h4>
          <div style="display: flex; gap: 6px;">
            <button class="btn btn-success" style="padding: 4px 14px; font-size: 12px;" @click="saveEdit(q.id)">
              &#10003; Salvează
            </button>
            <button class="btn btn-outline" style="padding: 4px 14px; font-size: 12px;" @click="cancelEdit()">
              &#10005; Anulează
            </button>
          </div>
        </div>
        <div class="form-group">
          <label>Textul întrebării</label>
          <input v-model="editForm.question_text" class="form-input" />
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div v-for="(_, i) in 4" :key="i" class="form-group">
            <label>
              Opțiunea {{ ['A', 'B', 'C', 'D'][i] }}
              <span v-if="editForm.correct_index === i" style="color: var(--success);"> ✓ Corect</span>
            </label>
            <div style="display: flex; gap: 8px;">
              <input v-model="editForm.options[i]" class="form-input" style="flex: 1;" />
              <button type="button" class="btn" :class="editForm.correct_index === i ? 'btn-success' : 'btn-outline'"
                style="padding: 6px 10px; font-size: 11px;"
                @click="editForm.correct_index = i">
                {{ editForm.correct_index === i ? '✓' : 'Corect' }}
              </button>
            </div>
          </div>
        </div>
        <div style="display: flex; gap: 12px; flex-wrap: wrap;">
          <div class="form-group" style="min-width: 140px;">
            <label>Dificultate</label>
            <select v-model="editForm.difficulty" class="form-select">
              <option value="easy">Ușoară</option>
              <option value="medium">Medie</option>
              <option value="hard">Avansată</option>
            </select>
          </div>
          <div class="form-group" style="flex: 1;">
            <label>Explicație</label>
            <input v-model="editForm.explanation" class="form-input" />
          </div>
        </div>
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

// --- Manual question form ---
const showManualForm = ref(false)
const manualQuestion = ref({
  question_text: '',
  options: ['', '', '', ''],
  correct_index: 0,
  explanation: '',
  difficulty: 'medium',
})

function toggleManualForm() {
  showManualForm.value = !showManualForm.value
  if (showManualForm.value) {
    manualQuestion.value = {
      question_text: '',
      options: ['', '', '', ''],
      correct_index: 0,
      explanation: '',
      difficulty: 'medium',
    }
  }
}

async function saveManualQuestion() {
  try {
    await api.post(`/courses/${courseId}/questions`, manualQuestion.value)
    showManualForm.value = false
    await loadQuestions()
  } catch (e) {
    alert(e.response?.data?.detail || 'Eroare la salvarea întrebării')
  }
}

// --- Edit question ---
const editingId = ref(null)
const editForm = ref({
  question_text: '',
  options: ['', '', '', ''],
  correct_index: 0,
  explanation: '',
  difficulty: 'medium',
})

function startEdit(q) {
  editingId.value = q.id
  editForm.value = {
    question_text: q.question_text,
    options: [...q.options],
    correct_index: q.correct_index,
    explanation: q.explanation || '',
    difficulty: q.difficulty,
  }
}

function cancelEdit() {
  editingId.value = null
}

async function saveEdit(questionId) {
  try {
    await api.put(`/courses/${courseId}/questions/${questionId}`, editForm.value)
    editingId.value = null
    await loadQuestions()
  } catch (e) {
    alert(e.response?.data?.detail || 'Eroare la editarea întrebării')
  }
}

// --- Load / Generate / Delete ---
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
