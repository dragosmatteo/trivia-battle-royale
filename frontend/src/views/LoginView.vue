<template>
  <div class="page" style="display: flex; align-items: center; justify-content: center; min-height: 100vh;">
    <div style="width: 100%; max-width: 420px;">
      <div style="text-align: center; margin-bottom: 40px;">
        <div style="font-size: 48px; margin-bottom: 12px;">&#9876;</div>
        <h1 style="font-size: 32px; font-weight: 900;">Trivia Battle Royale</h1>
        <p style="color: var(--text-secondary); margin-top: 8px;">Platformă educațională cu quiz-uri AI</p>
      </div>

      <div class="card">
        <h2 style="font-size: 20px; font-weight: 700; margin-bottom: 24px;">Autentificare</h2>

        <div v-if="error" style="padding: 10px 14px; background: rgba(255,71,87,0.15); border-radius: 8px; color: var(--danger); margin-bottom: 16px; font-size: 13px;">
          {{ error }}
        </div>

        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label>Username</label>
            <input v-model="username" class="form-input" placeholder="Introduceți username-ul" required />
          </div>
          <div class="form-group">
            <label>Parolă</label>
            <input v-model="password" type="password" class="form-input" placeholder="Introduceți parola" required />
          </div>
          <button type="submit" class="btn btn-primary btn-lg" style="width: 100%;" :disabled="loading">
            {{ loading ? 'Se conectează...' : 'Conectare' }}
          </button>
        </form>

        <div style="text-align: center; margin-top: 20px; font-size: 14px;">
          <span style="color: var(--text-muted);">Nu ai cont?</span>
          <router-link to="/register"> Înregistrare</router-link>
        </div>

        <div style="border-top: 1px solid var(--border); margin-top: 24px; padding-top: 20px; text-align: center;">
          <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">Sau intră direct într-un joc:</p>
          <router-link to="/join" class="btn btn-success" style="width: 100%;">
            Intră cu PIN
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    const user = await authStore.login(username.value, password.value)
    router.push(user.role === 'professor' ? '/professor' : '/student')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Eroare la autentificare'
  } finally {
    loading.value = false
  }
}
</script>
