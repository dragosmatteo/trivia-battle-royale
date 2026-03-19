<template>
  <div class="page container">
    <!-- Waiting Room -->
    <div v-if="gameStore.status === 'waiting' || gameStore.status === 'idle'" class="fade-in" style="text-align: center; max-width: 600px; margin: 0 auto;">
      <h1 class="page-title" style="margin-bottom: 24px;">Camera de Așteptare</h1>
      <p class="page-subtitle">Distribuiți acest cod PIN studenților</p>

      <div class="pin-display" style="margin-bottom: 32px;">{{ pin }}</div>

      <div class="stat-grid" style="margin-bottom: 32px;">
        <div class="stat-card">
          <div class="stat-value">{{ gameStore.players.length }}</div>
          <div class="stat-label">Jucători conectați</div>
        </div>
      </div>

      <!-- Connected players -->
      <div class="card" style="margin-bottom: 24px; text-align: left;">
        <h3 style="font-weight: 700; margin-bottom: 12px;">Jucători conectați</h3>
        <div v-if="gameStore.players.length === 0" style="color: var(--text-muted); padding: 20px; text-align: center;">
          Se așteaptă jucători<span class="waiting-dots"></span>
        </div>
        <div v-for="player in gameStore.players" :key="player.nickname" style="display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border);">
          <div style="width: 8px; height: 8px; border-radius: 50%; background: var(--success);"></div>
          <span style="font-weight: 500;">{{ player.nickname }}</span>
        </div>
      </div>

      <button class="btn btn-success btn-lg" style="width: 100%;"
        @click="startGame"
        :disabled="gameStore.players.length < 1">
        Pornește Jocul ({{ gameStore.players.length }} jucători)
      </button>
    </div>

    <!-- Game In Progress -->
    <div v-else-if="gameStore.status !== 'finished'" style="max-width: 800px; margin: 0 auto;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h2 style="font-weight: 700;">
          Întrebarea {{ gameStore.questionIndex + 1 }} / {{ gameStore.totalQuestions }}
        </h2>
        <div style="display: flex; gap: 12px; align-items: center;">
          <span class="badge badge-alive">{{ gameStore.aliveCount }} în viață</span>
          <span v-if="gameStore.roundResult?.is_sudden_death" class="badge badge-hard" style="animation: pulse 1s infinite;">
            SUDDEN DEATH
          </span>
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
          <strong>Explicație:</strong> {{ gameStore.roundResult.explanation }}
        </p>
        <div v-if="gameStore.roundResult.eliminated?.length" style="margin-bottom: 12px;">
          <span style="color: var(--danger); font-weight: 600;">Eliminați: </span>
          <span>{{ gameStore.roundResult.eliminated.join(', ') }}</span>
        </div>
      </div>

      <!-- Leaderboard -->
      <div class="card">
        <h3 style="font-weight: 700; margin-bottom: 12px;">Clasament</h3>
        <div v-for="p in gameStore.leaderboard" :key="p.nickname" :class="['leaderboard-item', !p.is_alive ? 'eliminated' : '']">
          <div :class="['leaderboard-rank', p.rank <= 3 ? `rank-${p.rank}` : '']"
            :style="p.rank > 3 ? { background: 'var(--bg-secondary)', color: 'var(--text-muted)' } : {}">
            {{ p.rank }}
          </div>
          <span class="leaderboard-name">{{ p.nickname }}</span>
          <span v-if="!p.is_alive" class="badge badge-eliminated" style="margin-right: 8px;">Eliminat</span>
          <span class="leaderboard-score">{{ p.score }} pts</span>
        </div>
      </div>
    </div>

    <!-- Game Over -->
    <div v-else style="text-align: center; max-width: 600px; margin: 0 auto;" class="fade-in">
      <div style="font-size: 64px; margin-bottom: 16px;">&#127942;</div>
      <h1 class="winner-text">{{ gameStore.winner }}</h1>
      <p style="font-size: 18px; color: var(--text-secondary); margin-bottom: 32px;">a câștigat Battle Royale!</p>

      <div class="card" style="text-align: left; margin-bottom: 24px;">
        <h3 style="font-weight: 700; margin-bottom: 12px;">Clasament final</h3>
        <div v-for="p in gameStore.finalLeaderboard" :key="p.nickname" class="leaderboard-item">
          <div :class="['leaderboard-rank', p.rank <= 3 ? `rank-${p.rank}` : '']"
            :style="p.rank > 3 ? { background: 'var(--bg-secondary)', color: 'var(--text-muted)' } : {}">
            {{ p.rank }}
          </div>
          <span class="leaderboard-name">{{ p.nickname }}</span>
          <span class="leaderboard-score">{{ p.score }} pts</span>
        </div>
      </div>

      <button class="btn btn-primary btn-lg" @click="$router.push('/professor')">Înapoi la panou</button>
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
