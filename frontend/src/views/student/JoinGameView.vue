<template>
  <div class="page" style="display: flex; align-items: center; justify-content: center; min-height: 100vh;">
    <div style="width: 100%; max-width: 420px; text-align: center;">
      <div style="font-size: 48px; margin-bottom: 12px;">&#9876;</div>
      <h1 style="font-size: 28px; font-weight: 900; margin-bottom: 8px;">Trivia Battle Royale</h1>
      <p style="color: var(--text-secondary); margin-bottom: 32px;">Introdu codul PIN pentru a te alătura jocului</p>

      <div class="card">
        <form @submit.prevent="joinGame">
          <div class="form-group">
            <label>Cod PIN</label>
            <input v-model="pinCode" class="form-input" placeholder="000000"
              style="text-align: center; font-size: 28px; font-weight: 900; letter-spacing: 8px;"
              maxlength="6" pattern="[0-9]*" inputmode="numeric" required />
          </div>
          <div class="form-group">
            <label>Nickname</label>
            <input v-model="nickname" class="form-input" placeholder="Numele tău în joc" maxlength="20" required />
          </div>
          <button type="submit" class="btn btn-success btn-lg" style="width: 100%;" :disabled="!pinCode || !nickname || loading">
            {{ loading ? 'Se conectează...' : 'Intră în joc' }}
          </button>
        </form>
        <div v-if="error" style="margin-top: 12px; color: var(--danger); font-size: 13px;">{{ error }}</div>

        <div style="margin-top: 20px; font-size: 13px; color: var(--text-muted);">
          <router-link to="/login">Sau conectează-te cu un cont</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../services/api'

const router = useRouter()
const pinCode = ref('')
const nickname = ref('')
const error = ref('')
const loading = ref(false)

async function joinGame() {
  error.value = ''
  loading.value = true
  try {
    await api.get(`/game/check-pin/${pinCode.value}`)
    router.push(`/play/${pinCode.value}?nickname=${encodeURIComponent(nickname.value)}`)
  } catch (e) {
    error.value = e.response?.data?.detail || 'PIN invalid'
  } finally {
    loading.value = false
  }
}
</script>
