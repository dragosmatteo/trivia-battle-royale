<template>
  <div class="page container">
    <h1 class="page-title">Panou Student</h1>
    <p class="page-subtitle">Bun venit, {{ authStore.user?.full_name }}!</p>

    <!-- Quick Join -->
    <div class="card" style="margin-bottom: 32px; text-align: center;">
      <h3 style="font-weight: 700; margin-bottom: 16px;">Intră într-un joc</h3>
      <p style="color: var(--text-secondary); margin-bottom: 20px;">Introdu codul PIN primit de la profesor</p>
      <form @submit.prevent="joinGame" style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
        <input v-model="pinCode" class="form-input" placeholder="Cod PIN (6 cifre)"
          style="width: 200px; text-align: center; font-size: 20px; font-weight: 700; letter-spacing: 4px;" maxlength="6" />
        <input v-model="nickname" class="form-input" placeholder="Nickname" style="width: 180px;" maxlength="20" />
        <button type="submit" class="btn btn-success btn-lg" :disabled="!pinCode || !nickname">
          Intră în joc
        </button>
      </form>
      <div v-if="joinError" style="margin-top: 12px; color: var(--danger); font-size: 13px;">{{ joinError }}</div>
    </div>

    <!-- Available Courses -->
    <h3 style="font-weight: 700; margin-bottom: 16px;">Cursurile disponibile</h3>
    <div v-if="courses.length === 0" style="color: var(--text-muted); padding: 40px; text-align: center;">
      Nu sunt cursuri disponibile momentan.
    </div>
    <div class="grid-2">
      <div v-for="course in courses" :key="course.id" class="card">
        <h4 style="font-weight: 700; margin-bottom: 8px;">{{ course.title }}</h4>
        <p style="color: var(--text-secondary); font-size: 13px;">{{ course.description || 'Fără descriere' }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import api from '../../services/api'

const router = useRouter()
const authStore = useAuthStore()

const courses = ref([])
const pinCode = ref('')
const nickname = ref(authStore.user?.username || '')
const joinError = ref('')

async function joinGame() {
  joinError.value = ''
  try {
    await api.get(`/game/check-pin/${pinCode.value}`)
    router.push(`/play/${pinCode.value}?nickname=${encodeURIComponent(nickname.value)}`)
  } catch (e) {
    joinError.value = e.response?.data?.detail || 'PIN invalid sau sesiunea nu este disponibilă'
  }
}

onMounted(async () => {
  try {
    const { data } = await api.get('/courses/')
    courses.value = data
  } catch {}
})
</script>
