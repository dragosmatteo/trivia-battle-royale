<template>
  <div class="page container">
    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 8px;">
      <button class="btn btn-outline" @click="$router.push('/professor')" style="padding: 8px 14px; font-size: 13px;">
        &larr; Inapoi
      </button>
      <h1 class="page-title" style="margin-bottom: 0;">Istoric Jocuri</h1>
    </div>
    <p class="page-subtitle">Vezi toate sesiunile de joc finalizate si rezultatele detaliate</p>

    <!-- Filter -->
    <div class="card" style="margin-bottom: 24px; padding: 16px 24px;">
      <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
        <label style="font-size: 13px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase;">Filtreaza dupa curs:</label>
        <select v-model="selectedCourse" class="form-select" style="min-width: 220px;" @change="loadHistory">
          <option :value="null">Toate cursurile</option>
          <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.title }}</option>
        </select>
        <span style="color: var(--text-muted); font-size: 13px;">{{ sessions.length }} sesiuni gasite</span>
      </div>
    </div>

    <!-- Sessions Table -->
    <div v-if="loading" style="text-align: center; padding: 60px; color: var(--text-muted);">
      Se incarca...
    </div>

    <div v-else-if="sessions.length === 0" style="text-align: center; padding: 60px; color: var(--text-muted);">
      Nu exista sesiuni finalizate.
    </div>

    <div v-else class="card" style="padding: 0; overflow: hidden;">
      <table class="data-table">
        <thead>
          <tr>
            <th>Data</th>
            <th>Curs</th>
            <th>PIN</th>
            <th>Jucatori</th>
            <th>Castigator</th>
            <th>Actiuni</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in sessions" :key="s.id" @click="viewDetail(s.id)" style="cursor: pointer;">
            <td>{{ formatDate(s.created_at) }}</td>
            <td>{{ s.course_title }}</td>
            <td><code style="color: var(--accent);">{{ s.pin_code }}</code></td>
            <td>{{ s.player_count }}</td>
            <td>
              <span v-if="s.winner !== '-'" style="color: var(--gold); font-weight: 600;">{{ s.winner }}</span>
              <span v-else style="color: var(--text-muted);">-</span>
            </td>
            <td>
              <button class="btn btn-outline" style="font-size: 11px; padding: 4px 12px;" @click.stop="viewDetail(s.id)">
                Detalii
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Detail Modal -->
    <div v-if="detailSession" class="overlay" @click.self="detailSession = null">
      <div class="card fade-in" style="max-width: 700px; width: 90%; max-height: 80vh; overflow-y: auto;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
          <h3 style="font-weight: 700;">Detalii Sesiune #{{ detailSession.id }}</h3>
          <button class="btn btn-outline" style="padding: 6px 12px; font-size: 12px;" @click="detailSession = null">Inchide</button>
        </div>

        <div class="stat-grid" style="margin-bottom: 20px;">
          <div class="stat-card">
            <div class="stat-value">{{ detailSession.player_count }}</div>
            <div class="stat-label">Jucatori</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" style="color: var(--gold);">{{ detailSession.winner }}</div>
            <div class="stat-label">Castigator</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ detailSession.course_title }}</div>
            <div class="stat-label">Curs</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ formatDate(detailSession.created_at) }}</div>
            <div class="stat-label">Data</div>
          </div>
        </div>

        <!-- Players list -->
        <h4 style="font-weight: 600; margin-bottom: 12px; color: var(--text-secondary);">Clasament Final</h4>
        <div style="border: 1px solid var(--border); border-radius: var(--radius-sm); overflow: hidden;">
          <div
            v-for="(p, idx) in detailSession.players"
            :key="p.id"
            class="leaderboard-item"
            :class="{ eliminated: !p.is_alive }"
          >
            <div
              class="leaderboard-rank"
              :class="{ 'rank-1': idx === 0, 'rank-2': idx === 1, 'rank-3': idx === 2 }"
            >
              {{ idx + 1 }}
            </div>
            <div class="leaderboard-name">
              {{ p.player_name }}
              <span v-if="p.is_alive" class="badge badge-alive" style="margin-left: 8px;">Supravietuitor</span>
              <span v-else class="badge badge-eliminated" style="margin-left: 8px;">Eliminat R{{ p.eliminated_at_round || '?' }}</span>
            </div>
            <div class="leaderboard-score">{{ p.score }} pts</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../services/api'

const sessions = ref([])
const courses = ref([])
const selectedCourse = ref(null)
const loading = ref(true)
const detailSession = ref(null)

function formatDate(dateStr) {
  if (!dateStr || dateStr === 'None') return '-'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString('ro-RO', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function loadHistory() {
  loading.value = true
  try {
    const params = selectedCourse.value ? { course_id: selectedCourse.value } : {}
    const { data } = await api.get('/admin/game-history', { params })
    sessions.value = data
  } catch (e) {
    console.error('Failed to load game history:', e)
  } finally {
    loading.value = false
  }
}

async function viewDetail(sessionId) {
  try {
    const { data } = await api.get(`/admin/game-history/${sessionId}`)
    detailSession.value = data
  } catch (e) {
    console.error('Failed to load session detail:', e)
  }
}

onMounted(async () => {
  try {
    const { data } = await api.get('/courses/')
    courses.value = data
  } catch {}
  await loadHistory()
})
</script>

<style scoped>
.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-muted);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
}

.data-table td {
  padding: 12px 16px;
  font-size: 14px;
  border-bottom: 1px solid var(--border);
}

.data-table tr:hover td {
  background: var(--bg-card-hover);
}

.data-table tr:last-child td {
  border-bottom: none;
}
</style>
