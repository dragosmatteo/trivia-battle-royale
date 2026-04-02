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

        <div style="border-top: 1px solid var(--border); margin-top: 24px; padding-top: 16px;">
          <button
            @click="showChangePassword = !showChangePassword"
            type="button"
            style="background: none; border: none; cursor: pointer; color: var(--text-muted); font-size: 13px; width: 100%; text-align: center; padding: 4px 0;"
          >
            {{ showChangePassword ? '▲ Ascunde' : '▼ Schimbă parola' }}
          </button>

          <div v-if="showChangePassword" style="margin-top: 16px;">
            <div v-if="cpError" style="padding: 10px 14px; background: rgba(255,71,87,0.15); border-radius: 8px; color: var(--danger); margin-bottom: 12px; font-size: 13px;">
              {{ cpError }}
            </div>
            <div v-if="cpSuccess" style="padding: 10px 14px; background: rgba(46,213,115,0.15); border-radius: 8px; color: var(--success); margin-bottom: 12px; font-size: 13px;">
              {{ cpSuccess }}
            </div>

            <form @submit.prevent="handleChangePassword">
              <div class="form-group">
                <label>Parolă curentă</label>
                <input v-model="cpCurrent" type="password" class="form-input" placeholder="Parola curentă" required />
              </div>
              <div class="form-group">
                <label>Parolă nouă</label>
                <input v-model="cpNew" type="password" class="form-input" placeholder="Min. 6 caractere, literă + cifră" required />
              </div>
              <div class="form-group">
                <label>Confirmare parolă nouă</label>
                <input v-model="cpConfirm" type="password" class="form-input" placeholder="Repetați parola nouă" required />
              </div>
              <button type="submit" class="btn btn-primary" style="width: 100%;" :disabled="cpLoading">
                {{ cpLoading ? 'Se salvează...' : 'Schimbă parola' }}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

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

// Change password section
const showChangePassword = ref(false)
const cpCurrent = ref('')
const cpNew = ref('')
const cpConfirm = ref('')
const cpError = ref('')
const cpSuccess = ref('')
const cpLoading = ref(false)

async function handleChangePassword() {
  cpError.value = ''
  cpSuccess.value = ''

  if (cpNew.value !== cpConfirm.value) {
    cpError.value = 'Parolele noi nu coincid'
    return
  }

  if (!authStore.token) {
    cpError.value = 'Trebuie să fii autentificat pentru a schimba parola'
    return
  }

  cpLoading.value = true
  try {
    await axios.put('/api/auth/change-password', {
      current_password: cpCurrent.value,
      new_password: cpNew.value,
    }, {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    cpSuccess.value = 'Parola a fost schimbată cu succes!'
    cpCurrent.value = ''
    cpNew.value = ''
    cpConfirm.value = ''
  } catch (e) {
    cpError.value = e.response?.data?.detail || 'Eroare la schimbarea parolei'
  } finally {
    cpLoading.value = false
  }
}
</script>
