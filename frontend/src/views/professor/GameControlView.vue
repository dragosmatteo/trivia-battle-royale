<template>
  <div class="page container">
    <!-- Waiting Room -->
    <div v-if="gameStore.status === 'waiting' || gameStore.status === 'idle'" class="fade-in" style="text-align: center; max-width: 600px; margin: 0 auto;">
      <h1 class="page-title" style="margin-bottom: 24px;">Camera de Asteptare</h1>
      <p class="page-subtitle">Distribuiti acest cod PIN studentilor</p>

      <div class="pin-display" style="margin-bottom: 32px;">{{ pin }}</div>

      <div class="stat-grid" style="margin-bottom: 32px;">
        <div class="stat-card">
          <div class="stat-value">{{ gameStore.players.length }}</div>
          <div class="stat-label">Jucatori conectati</div>
        </div>
      </div>

      <!-- Connected players -->
      <div class="card" style="margin-bottom: 24px; text-align: left;">
        <h3 style="font-weight: 700; margin-bottom: 12px;">Jucatori conectati</h3>
        <div v-if="gameStore.players.length === 0" style="color: var(--text-muted); padding: 20px; text-align: center;">
          Se asteapta jucatori<span class="waiting-dots"></span>
        </div>
        <div v-for="player in gameStore.players" :key="player.nickname" style="display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border);">
          <div style="width: 8px; height: 8px; border-radius: 50%; background: var(--success);"></div>
          <span style="font-weight: 500;">{{ player.nickname }}</span>
        </div>
      </div>

      <button class="btn btn-success btn-lg" style="width: 100%;"
        @click="startGame"
        :disabled="gameStore.players.length < 1">
        Porneste Jocul ({{ gameStore.players.length }} jucatori)
      </button>
    </div>

    <!-- Loading Next Question -->
    <div v-else-if="gameStore.status === 'loading_next'" class="fade-in" style="text-align: center; max-width: 600px; margin: 0 auto; padding: 60px 0;">
      <div class="loading-spinner"></div>
      <h2 style="font-weight: 800; margin-top: 24px; color: var(--accent);">Urmatoarea intrebare...</h2>
      <p style="color: var(--text-secondary); margin-top: 8px;">{{ gameStore.loadingMessage }}</p>
    </div>

    <!-- Game In Progress -->
    <div v-else-if="gameStore.status !== 'finished'" style="max-width: 800px; margin: 0 auto;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h2 style="font-weight: 700;">
          Intrebarea {{ gameStore.questionIndex + 1 }} / {{ gameStore.totalQuestions }}
        </h2>
        <div style="display: flex; gap: 12px; align-items: center;">
          <span class="badge badge-alive">{{ gameStore.aliveCount }} jucatori</span>
        </div>
      </div>

      <!-- Timer -->
      <div class="timer-bar">
        <div class="timer-bar-fill" :class="timerClass" :style="{ width: timerPercent + '%' }"></div>
      </div>

      <!-- Question (professor sees correct answer) -->
      <div v-if="gameStore.currentQuestion" class="card" style="margin-bottom: 24px;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
          <span :class="['badge', `badge-${gameStore.currentQuestion.difficulty}`]">
            {{ gameStore.currentQuestion.difficulty }}
          </span>
          <span v-if="gameStore.currentQuestion.phase" class="badge" style="background: rgba(108,92,231,0.2); color: var(--accent);">
            {{ gameStore.currentQuestion.phase }}
          </span>
          <span style="font-size: 13px; color: var(--text-muted);">Timp: {{ gameStore.timeLeft }}s</span>
        </div>
        <p style="font-size: 18px; font-weight: 600; margin-bottom: 20px;">
          {{ gameStore.currentQuestion.question_text }}
        </p>
        <div style="display: grid; gap: 10px;">
          <div v-for="(opt, i) in gameStore.currentQuestion.options" :key="i"
            :class="['option-btn', showResults && i === gameStore.currentQuestion.correct_index ? 'correct' : '']"
            style="cursor: default;">
            <span class="option-letter">{{ ['A', 'B', 'C', 'D'][i] }}</span>
            <span>{{ opt }}</span>
            <span v-if="i === gameStore.currentQuestion.correct_index" style="margin-left: auto; font-size: 12px; color: var(--success);">&#10003; Corect</span>
          </div>
        </div>
      </div>

      <!-- Round Results -->
      <div v-if="gameStore.roundResult" class="card" style="margin-bottom: 24px;">
        <h3 style="font-weight: 700; margin-bottom: 8px;">Rezultate runda</h3>
        <p v-if="gameStore.roundResult.explanation" style="font-size: 13px; color: var(--text-secondary); margin-bottom: 12px;">
          <strong>Explicatie:</strong> {{ gameStore.roundResult.explanation }}
        </p>
        <!-- Round stats -->
        <div class="stat-grid" style="grid-template-columns: repeat(3, 1fr); margin-top: 12px;">
          <div class="stat-card">
            <div class="stat-value" style="color: var(--success);">{{ gameStore.roundResult?.round_stats?.correct_count || 0 }}</div>
            <div class="stat-label">Corecte</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" style="color: var(--danger);">{{ gameStore.roundResult?.round_stats?.wrong_count || 0 }}</div>
            <div class="stat-label">Gresite</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" style="color: var(--warning);">{{ gameStore.roundResult?.round_stats?.timeout_count || 0 }}</div>
            <div class="stat-label">Fara raspuns</div>
          </div>
        </div>
      </div>

      <!-- Leaderboard -->
      <div class="card">
        <h3 style="font-weight: 700; margin-bottom: 12px;">Clasament</h3>
        <div v-for="p in gameStore.leaderboard" :key="p.nickname" class="leaderboard-item">
          <div :class="['leaderboard-rank', p.rank <= 3 ? `rank-${p.rank}` : '']"
            :style="p.rank > 3 ? { background: 'var(--bg-secondary)', color: 'var(--text-muted)' } : {}">
            {{ p.rank }}
          </div>
          <span class="leaderboard-name">{{ p.nickname }}</span>
          <span style="font-size: 11px; color: var(--text-muted); margin-right: 8px;">{{ p.accuracy || 0 }}%</span>
          <span class="leaderboard-score">{{ p.score }} pts</span>
        </div>
      </div>
    </div>

    <!-- Game Over -->
    <div v-else style="text-align: center; max-width: 700px; margin: 0 auto;" class="fade-in">
      <div style="font-size: 64px; margin-bottom: 16px;">&#127942;</div>
      <h1 class="winner-text">{{ gameStore.winner }}</h1>
      <p style="font-size: 18px; color: var(--text-secondary); margin-bottom: 32px;">a castigat jocul!</p>

      <!-- League Results -->
      <div v-if="gameStore.hasLeagues" style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
        <div class="card" style="text-align: center; border-color: var(--gold);">
          <div style="font-size: 32px; margin-bottom: 8px;">&#11088;</div>
          <h3 style="font-weight: 800; color: var(--gold); margin-bottom: 12px;">Liga Campionilor</h3>
          <div v-for="name in gameStore.leagues.champions" :key="name" style="padding: 6px 0; font-size: 14px; border-bottom: 1px solid var(--border);">
            {{ name }}
          </div>
        </div>
        <div class="card" style="text-align: center; border-color: var(--accent);">
          <div style="font-size: 32px; margin-bottom: 8px;">&#128170;</div>
          <h3 style="font-weight: 800; color: var(--accent); margin-bottom: 12px;">Liga Provocarii</h3>
          <div v-for="name in gameStore.leagues.challengers" :key="name" style="padding: 6px 0; font-size: 14px; border-bottom: 1px solid var(--border);">
            {{ name }}
          </div>
        </div>
      </div>

      <div class="card" style="text-align: left; margin-bottom: 24px;">
        <h3 style="font-weight: 700; margin-bottom: 12px;">Clasament final</h3>
        <div v-for="p in gameStore.finalLeaderboard" :key="p.nickname" class="leaderboard-item">
          <div :class="['leaderboard-rank', p.rank <= 3 ? `rank-${p.rank}` : '']"
            :style="p.rank > 3 ? { background: 'var(--bg-secondary)', color: 'var(--text-muted)' } : {}">
            {{ p.rank }}
          </div>
          <span class="leaderboard-name">{{ p.nickname }}</span>
          <span v-if="gameStore.hasLeagues" style="font-size: 10px; margin-right: 4px;">
            {{ p.league === 'champions' ? '&#11088;' : '&#128170;' }}
          </span>
          <span style="font-size: 11px; color: var(--text-muted); margin-right: 8px;">{{ p.accuracy || 0 }}%</span>
          <span class="leaderboard-score">{{ p.score }} pts</span>
        </div>
      </div>

      <button class="btn btn-primary btn-lg" @click="$router.push('/professor')">Inapoi la panou</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useGameStore } from '../../stores/game'
import { GameWebSocket } from '../../services/websocket'

const route = useRoute()
const pin = route.params.pin
const gameStore = useGameStore()

const ws = new GameWebSocket()
const showResults = computed(() => gameStore.status === 'round_ended')

const timerPercent = computed(() => {
  if (!gameStore.timeLimit) return 100
  return (gameStore.timeLeft / gameStore.timeLimit) * 100
})

const timerClass = computed(() => {
  if (timerPercent.value > 50) return 'timer-green'
  if (timerPercent.value > 25) return 'timer-yellow'
  return 'timer-red'
})

function startGame() {
  ws.send({ action: 'start_game' })
}

onMounted(async () => {
  gameStore.reset()
  ws.on('*', (data) => gameStore.handleMessage(data))

  try {
    await ws.connect(`/ws/professor/${pin}`)
  } catch (e) {
    console.error('WebSocket connection failed:', e)
  }
})

onUnmounted(() => {
  ws.disconnect()
})
</script>

<style scoped>
.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
