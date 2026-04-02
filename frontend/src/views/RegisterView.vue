<template>
  <div class="page" style="display: flex; align-items: center; justify-content: center; min-height: 100vh;">
    <div style="width: 100%; max-width: 420px;">
      <div style="text-align: center; margin-bottom: 32px;">
        <h1 style="font-size: 28px; font-weight: 900;">Creare cont</h1>
        <p style="color: var(--text-secondary); margin-top: 8px;">Înregistrează-te pentru Trivia Battle Royale</p>
      </div>

      <div class="card">
        <div v-if="inviteGroup" style="padding: 10px 14px; background: rgba(46,213,115,0.15); border-radius: 8px; color: var(--success, #2ed573); margin-bottom: 16px; font-size: 14px; text-align: center;">
          Te inscrii in clasa <strong>{{ inviteGroup }}</strong>
        </div>

        <div v-if="error" style="padding: 10px 14px; background: rgba(255,71,87,0.15); border-radius: 8px; color: var(--danger); margin-bottom: 16px; font-size: 13px;">
          {{ error }}
        </div>

        <form @submit.prevent="handleRegister">
          <div class="form-group">
            <label>Nume complet</label>
            <input v-model="form.full_name" class="form-input" placeholder="ex: Ion Popescu" required />
          </div>
          <div class="form-group">
            <label>Username</label>
            <input v-model="form.username" class="form-input" placeholder="ex: ion.popescu" required />
          </div>
          <div class="form-group">
            <label>Email</label>
            <input v-model="form.email" type="email" class="form-input" placeholder="ex: ion@tuiasi.ro" required />
          </div>
          <div class="form-group">
            <label>Parolă</label>
            <input v-model="form.password" type="password" class="form-input" placeholder="Minim 4 caractere" required />
          </div>
          <div class="form-group" v-if="!inviteGroup">
            <label>Rol</label>
            <select v-model="form.role" class="form-select" required>
              <option value="student">Student</option>
              <option value="professor">Profesor</option>
            </select>
          </div>
          <div class="form-group" v-if="form.role === 'student'">
            <label>Grupa</label>
            <input v-model="form.group_name" class="form-input" placeholder="ex: 1401A" :readonly="!!inviteGroup" :style="inviteGroup ? 'background: var(--bg-secondary, #f0f0f0); cursor: not-allowed;' : ''" />
          </div>
          <button type="submit" class="btn btn-primary btn-lg" style="width: 100%;" :disabled="loading">
            {{ loading ? 'Se creează contul...' : 'Înregistrare' }}
          </button>
        </form>

        <div style="text-align: center; margin-top: 20px; font-size: 14px;">
          <span style="color: var(--text-muted);">Ai deja cont?</span>
          <router-link to="/login"> Conectare</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const inviteCode = computed(() => route.query.class || '')
const inviteGroup = computed(() => route.query.group || '')

const form = reactive({
  full_name: '',
  username: '',
  email: '',
  password: '',
  role: 'student',
  group_name: inviteGroup.value || '',
})

// Lock role to student when arriving via invite link
if (inviteGroup.value) {
  form.role = 'student'
  form.group_name = inviteGroup.value
}

const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''
  loading.value = true
  try {
    const user = await authStore.register(form)
    router.push(user.role === 'professor' ? '/professor' : '/student')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Eroare la înregistrare'
  } finally {
    loading.value = false
  }
}
</script>
