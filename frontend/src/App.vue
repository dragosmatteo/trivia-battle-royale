<template>
  <div id="app">
    <nav class="navbar" v-if="authStore.isLoggedIn">
      <router-link to="/" class="navbar-brand">
        <span>&#9876;</span> Trivia Battle Royale
      </router-link>
      <div class="navbar-user">
        <span :class="['role-badge', authStore.isProfessor ? 'role-professor' : 'role-student']">
          {{ authStore.user?.role }}
        </span>
        <span>{{ authStore.user?.full_name }}</span>
        <button class="btn btn-outline" @click="handleLogout" style="padding: 6px 14px; font-size: 13px;">
          Deconectare
        </button>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>
