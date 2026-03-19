<template>
  <div class="page container" style="max-width: 700px; margin: 0 auto;">

    <!-- Connecting... -->
    <div v-if="!gameStore.isConnected && !connectionError" style="text-align: center; padding: 60px 0;">
      <div style="font-size: 48px; animation: pulse 1s infinite;">&#9876;</div>
      <p style="margin-top: 16px; color: var(--text-secondary);">Se conectează la sesiune<span class="waiting-dots"></span></p>
    </div>

    <!-- Connection Error -->
    <div v-else-if="connectionError" style="text-align: center; padding: 60px 0;">
      <div style="font-size: 48px;">&#10060;</div>
      <p style="margin-top: 16px; color: var(--danger);">{{ connectionError }}</p>
      <button class="btn btn-primary" style="margin-top: 16px;" @click="$router.push('/join')">Înapoi</button>
    </div>

    <!-- Waiting Room -->
    <div v-else-if="gameStore.status === 'waiting'" class="fade-in" style="text-align: center; padding: 40px 0;">
      <div style="font-size: 64px; margin-bottom: 16px;">&#128075;</div>
      <h2 style="font-weight: 800; margin-bottom: 8px;">Bun venit, {{ gameStore.nickname }}!</h2>
      <p style="color: var(--text-secondary); margin-bottom: 24px;">Așteptăm ca profesorul să pornească jocul<span class="waiting-dots"></span></p>

      <div class="card" style="text-align: left;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
          <h3 style="font-weight: 700;">Jucători conectați</h3>
          <span style="color: var(--accent); font-weight: 700;">{{ gameStore.players.length }}</span>
        </div>
        <div v-for="player in gameStore.players" :key="player.nickname"
          style="padding: 8px 0; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 8px;">
          <div style="width: 8px; height: 8px; border-radius: 50%; background: var(--success);"></div>
          <span :style="{ fontWeight: player.nickname === gameStore.nickname ? '700' : '400' }">
            {{ player.nickname }}
            <span v-if="player.nickname === gameStore.nickname" style="color: var(--accent);"> (tu)</span>
          </span>
        </div>
      </div>
    </div>

    <!-- Game Starting -->
    <div v-else-if="gameStore.status === 'playing' && !gameStore.currentQuestion" class="fade-in" style="text-align: center; padding: 60px 0;">
      <div style="font-size: 64px; animation: pulse 0.8s infinite;">&#9876;</div>
      <h2 style="font-weight: 800; margin-top: 16px;">Jocul începe!</h2>
      <p style="color: var(--text-secondary); margin-top: 8px;">Pregătește-te...</p>
    </div>

    <!-- Tier Assignment Notification -->
    <div v-if="tierNotification" class="overlay" style="z-index: 999;" @click="tierNotification = ''">
      <div class="overlay-content">
        <div style="font-size: 64px; margin-bottom: 16px;">{{ tierIcon }}</div>
        <h2 style="font-weight: 800; color: var(--accent);">{{ tierLabel }}</h2>
        <p style="color: var(--text-secondary); margin-top: 8px;">{{ tierNotification }}</p>
        <p style="color: var(--text-muted); margin-top: 16px; font-size: 13px;">Click pentru a continua</p>
      </div>
    </div>

    <!-- Active Question -->
    <div v-else-if="gameStore.status === 'round_active'" class="fade-in">
      <!-- Spectator banner -->
      <div v-if="gameStore.isSpectator" class="spectator-mode">
        <div class="spectator-label">Mod Spectator</div>
        <p style="color: var(--text-secondary); font-size: 13px; margin-top: 4px;">Ai fost eliminat. Urmărești jocul.</p>
      </div>

      <!-- Question header -->
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
          <span style="font-weight: 800; font-size: 14px; color: var(--text-muted);">
            {{ gameStore.questionIndex + 1 }} / {{ gameStore.totalQuestions }}
          </span>
          <span :class="['badge', `badge-${gameStore.currentQuestion.difficulty}`]">
            {{ gameStore.currentQuestion.difficulty }}
          </span>
          <span v-if="gameStore.currentQuestion.phase" class="badge" style="background: rgba(108,92,231,0.2); color: var(--accent);">
            {{ gameStore.currentQuestion.phase }}
          </span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="font-size: 13px; color: var(--text-muted);">{{ gameStore.aliveCount }} în viață</span>
          <span :style="{ fontSize: '20px', fontWeight: 800, color: timerColor }">{{ gameStore.timeLeft }}s</span>
        </div>
      </div>

      <!-- Timer bar -->
      <div class="timer-bar">
        <div class="timer-bar-fill" :class="timerClass" :style="{ width: timerPercent + '%' }"></div>
      </div>

      <!-- Your tier badge -->
      <div v-if="gameStore.currentQuestion.your_tier" style="margin-bottom: 12px; text-align: center;">
        <span class="badge" :style="gameStore.currentQuestion.your_tier === 'advanced' ? { background: 'rgba(255,215,0,0.15)', color: 'var(--gold)' } : { background: 'rgba(0,206,201,0.15)', color: 'var(--success)' }">
          {{ gameStore.currentQuestion.your_tier === 'advanced' ? 'Arena Avansata' : 'Arena Standard' }}
        </span>
      </div>

      <!-- Question text -->
      <div class="card" style="margin-bottom: 20px;">
        <p style="font-size: 18px; font-weight: 600; line-height: 1.5;">
          {{ gameStore.currentQuestion.question_text }}
        </p>
      </div>

      <!-- Answer options -->
      <div style="display: grid; gap: 12px;">
        <button v-for="(opt, i) in gameStore.currentQuestion.options" :key="i"
          :class="['option-btn', gameStore.selectedAnswer === i ? 'selected' : '']"
          :disabled="gameStore.answerLocked || gameStore.isSpectator"
          @click="selectAnswer(i)">
          <span class="option-letter" :style="gameStore.selectedAnswer === i ? { background: 'var(--accent)', color: 'white' } : {}">
            {{ ['A', 'B', 'C', 'D'][i] }}
          </span>
          <span>{{ opt }}</span>
          <span v-if="gameStore.selectedAnswer === i && gameStore.answerConfirmed"
            style="margin-left: auto; font-size: 12px; color: var(--success); font-weight: 600;">
            &#10003; Trimis
          </span>
        </button>
      </div>

      <!-- Answer status feedback -->
      <div v-if="gameStore.answerLocked" style="text-align: center; margin-top: 16px;">
        <p v-if="gameStore.answerConfirmed" style="color: var(--success); font-weight: 600; font-size: 14px;">
          &#10003; Răspunsul tău a fost înregistrat! Așteptăm ceilalți jucători<span class="waiting-dots"></span>
        </p>
        <p v-else style="color: var(--warning); font-size: 14px;">
          Se trimite răspunsul<span class="waiting-dots"></span>
        </p>
      </div>
    </div>

    <!-- Round Result -->
    <div v-else-if="gameStore.status === 'round_ended'" class="fade-in">
      <!-- Elimination overlay -->
      <div v-if="gameStore.myResult?.status === 'eliminated' || gameStore.myResult?.status === 'timeout_eliminated'" class="overlay">
        <div class="overlay-content">
          <div class="elimination-text shake">ELIMINAT!</div>
          <p style="color: var(--text-secondary); font-size: 18px;">
            {{ gameStore.myResult.status === 'timeout_eliminated' ? 'Nu ai răspuns la timp.' : 'Răspuns greșit în Sudden Death.' }}
          </p>
          <p style="color: var(--text-muted); margin-top: 12px;">Vei continua ca spectator.</p>
        </div>
      </div>

      <!-- Your result -->
      <div class="card" style="margin-bottom: 16px; text-align: center;">
        <div v-if="gameStore.myResult?.status === 'correct'" style="margin-bottom: 12px;">
          <div style="font-size: 48px;">&#10004;&#65039;</div>
          <h3 style="color: var(--success); font-weight: 800;">Corect!</h3>
          <p style="color: var(--accent); font-weight: 700; font-size: 20px;">+{{ gameStore.myResult.points_earned }} puncte</p>
          <p v-if="gameStore.myResult.streak >= 3" style="color: var(--gold); font-size: 13px;">
            &#128293; Serie de {{ gameStore.myResult.streak }}! (+50 bonus)
          </p>
        </div>
        <div v-else-if="gameStore.myResult?.status === 'wrong'" style="margin-bottom: 12px;">
          <div style="font-size: 48px;">&#10060;</div>
          <h3 style="color: var(--danger); font-weight: 800;">Greșit!</h3>
        </div>
        <div v-else-if="gameStore.isSpectator" style="margin-bottom: 12px;">
          <div style="font-size: 48px;">&#128064;</div>
          <h3 style="font-weight: 800;">Spectator</h3>
        </div>

        <!-- Your stats -->
        <div style="display: flex; justify-content: center; gap: 24px; margin-top: 12px; font-size: 13px; color: var(--text-secondary);">
          <div><strong style="color: var(--accent);">{{ gameStore.roundResult?.your_score || 0 }}</strong> puncte</div>
          <div><strong style="color: var(--success);">{{ gameStore.roundResult?.your_accuracy || 0 }}%</strong> acuratețe</div>
          <div>Serie: <strong style="color: var(--gold);">{{ gameStore.roundResult?.your_streak || 0 }}</strong></div>
        </div>

        <div v-if="gameStore.roundResult?.is_sudden_death" style="margin-top: 12px;">
          <span class="badge badge-hard" style="animation: pulse 1s infinite;">SUDDEN DEATH</span>
        </div>
      </div>

      <!-- Correct Answer Card -->
      <div class="card" style="margin-bottom: 16px; border-color: var(--success);">
        <h4 style="font-weight: 700; margin-bottom: 12px; color: var(--success);">&#10003; Răspunsul corect</h4>
        <div style="display: grid; gap: 8px;">
          <div v-for="(opt, i) in (gameStore.roundResult?.options || gameStore.currentQuestion?.options || [])" :key="i"
            :class="['option-btn', i === gameStore.roundResult?.correct_index ? 'correct' : (i === gameStore.selectedAnswer && i !== gameStore.roundResult?.correct_index ? 'wrong' : '')]"
            style="cursor: default; margin-bottom: 0;">
            <span class="option-letter" :style="i === gameStore.roundResult?.correct_index ? { background: 'var(--success)', color: '#fff' } : (i === gameStore.selectedAnswer && i !== gameStore.roundResult?.correct_index ? { background: 'var(--danger)', color: '#fff' } : {})">
              {{ ['A', 'B', 'C', 'D'][i] }}
            </span>
            <span>{{ opt }}</span>
            <span v-if="i === gameStore.roundResult?.correct_index" style="margin-left: auto; color: var(--success); font-weight: 700;">&#10003;</span>
            <span v-if="i === gameStore.selectedAnswer && i !== gameStore.roundResult?.correct_index" style="margin-left: auto; color: var(--danger); font-weight: 700;">&#10005;</span>
          </div>
        </div>
        <div v-if="gameStore.roundResult?.explanation" style="margin-top: 12px; padding: 12px; background: var(--bg-secondary); border-radius: 8px; font-size: 13px; color: var(--text-secondary);">
          <strong>Explicație:</strong> {{ gameStore.roundResult.explanation }}
        </div>
      </div>

      <!-- Round Statistics -->
      <div class="card" style="margin-bottom: 16px;">
        <h4 style="font-weight: 700; margin-bottom: 12px;">Statistici rundă</h4>
        <div class="stat-grid" style="grid-template-columns: repeat(4, 1fr);">
          <div class="stat-card">
            <div class="stat-value" style="color: var(--success);">{{ gameStore.roundResult?.round_stats?.accuracy_pct || 0 }}%</div>
            <div class="stat-label">Au nimerit</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" style="color: var(--accent);">{{ gameStore.roundResult?.round_stats?.correct_count || 0 }}/{{ gameStore.roundResult?.round_stats?.total_players || 0 }}</div>
            <div class="stat-label">Corecte</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" style="color: var(--warning);">{{ gameStore.roundResult?.round_stats?.avg_answer_time || 0 }}s</div>
            <div class="stat-label">Timp mediu</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" style="color: var(--gold); font-size: 16px;">
              {{ gameStore.roundResult?.round_stats?.fastest_player || '-' }}
            </div>
            <div class="stat-label">{{ gameStore.roundResult?.round_stats?.fastest_time ? gameStore.roundResult.round_stats.fastest_time + 's' : 'Cel mai rapid' }}</div>
          </div>
        </div>
      </div>

      <!-- Leaderboard -->
      <div class="card">
        <h3 style="font-weight: 700; margin-bottom: 8px;">Clasament</h3>
        <div v-if="gameStore.roundResult?.eliminated?.length" style="margin-bottom: 12px; font-size: 13px; color: var(--danger);">
          Eliminați: {{ gameStore.roundResult.eliminated.join(', ') }}
        </div>
        <div v-for="p in gameStore.leaderboard.slice(0, 10)" :key="p.nickname"
          :class="['leaderboard-item', !p.is_alive ? 'eliminated' : '']"
          :style="p.nickname === gameStore.nickname ? { background: 'rgba(108,92,231,0.1)', borderRadius: '8px' } : {}">
          <div :class="['leaderboard-rank', p.rank <= 3 ? `rank-${p.rank}` : '']"
            :style="p.rank > 3 ? { background: 'var(--bg-secondary)', color: 'var(--text-muted)' } : {}">
            {{ p.rank }}
          </div>
          <span class="leaderboard-name">
            {{ p.nickname }}
            <span v-if="p.nickname === gameStore.nickname" style="color: var(--accent);"> (tu)</span>
            <span v-if="p.tier" style="font-size: 10px; color: var(--text-muted); margin-left: 4px;">
              {{ p.tier === 'advanced' ? '★' : '○' }}
            </span>
          </span>
          <span style="font-size: 11px; color: var(--text-muted); margin-right: 8px;">{{ p.accuracy || 0 }}%</span>
          <span class="leaderboard-score">{{ p.score }}</span>
        </div>
      </div>

      <p style="text-align: center; color: var(--text-muted); margin-top: 16px; font-size: 13px;">
        Următoarea întrebare vine în curând<span class="waiting-dots"></span>
      </p>
    </div>

    <!-- Game Over -->
    <div v-else-if="gameStore.status === 'finished'" class="fade-in" style="text-align: center;">
      <div style="font-size: 80px; margin-bottom: 16px;">&#127942;</div>
      <h1 class="winner-text">{{ gameStore.winner }}</h1>
      <p style="font-size: 18px; color: var(--text-secondary); margin-bottom: 8px;">a câștigat Battle Royale!</p>

      <div v-if="gameStore.winner === gameStore.nickname" style="margin-bottom: 24px;">
        <p style="font-size: 24px; color: var(--gold); font-weight: 800;">&#127881; Felicitări! Ești campionul! &#127881;</p>
      </div>

      <div class="card" style="text-align: left; margin-bottom: 24px;">
        <h3 style="font-weight: 700; margin-bottom: 12px;">Clasament final</h3>
        <div v-for="p in gameStore.finalLeaderboard" :key="p.nickname" class="leaderboard-item"
          :style="p.nickname === gameStore.nickname ? { background: 'rgba(108,92,231,0.1)', borderRadius: '8px' } : {}">
          <div :class="['leaderboard-rank', p.rank <= 3 ? `rank-${p.rank}` : '']"
            :style="p.rank > 3 ? { background: 'var(--bg-secondary)', color: 'var(--text-muted)' } : {}">
            {{ p.rank }}
          </div>
          <span class="leaderboard-name">
            {{ p.nickname }}
            <span v-if="p.nickname === gameStore.nickname" style="color: var(--accent);"> (tu)</span>
          </span>
          <span style="font-size: 11px; color: var(--text-muted); margin-right: 8px;">{{ p.accuracy || 0 }}%</span>
          <span class="leaderboard-score">{{ p.score }} pts</span>
        </div>
      </div>

      <div style="display: flex; gap: 12px; justify-content: center;">
        <button class="btn btn-primary btn-lg" @click="$router.push('/join')">Joacă din nou</button>
        <button class="btn btn-outline btn-lg" @click="$router.push('/student')">Dashboard</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGameStore } from '../../stores/game'
import { GameWebSocket } from '../../services/websocket'

const route = useRoute()
const router = useRouter()
const gameStore = useGameStore()
const ws = new GameWebSocket()
const connectionError = ref('')
const tierNotification = ref('')
const tierLabel = ref('')
const tierIcon = ref('')

const pin = route.params.pin
const nickname = route.query.nickname || 'Player'

const timerPercent = computed(() => {
  if (!gameStore.timeLimit) return 100
  return (gameStore.timeLeft / gameStore.timeLimit) * 100
})

const timerColor = computed(() => {
  if (timerPercent.value > 50) return 'var(--success)'
  if (timerPercent.value > 25) return 'var(--warning)'
  return 'var(--danger)'
})

const timerClass = computed(() => {
  if (timerPercent.value > 50) return 'timer-green'
  if (timerPercent.value > 25) return 'timer-yellow'
  return 'timer-red'
})

function selectAnswer(index) {
  if (gameStore.answerLocked || gameStore.isSpectator) return
  gameStore.selectedAnswer = index
  gameStore.answerLocked = true
  ws.send({ action: 'answer', selected_option: index })
}

onMounted(async () => {
  gameStore.reset()
  ws.on('*', (data) => {
    if (data.type === 'tier_assigned') {
      tierNotification.value = data.message
      tierLabel.value = data.tier_label
      tierIcon.value = data.tier === 'advanced' ? '⭐' : '🎯'
      setTimeout(() => { tierNotification.value = '' }, 4000)
      return
    }
    gameStore.handleMessage(data)
  })
  ws.on('error', (data) => {
    connectionError.value = data.message
  })

  try {
    await ws.connect(`/ws/player/${pin}/${encodeURIComponent(nickname)}`)
  } catch (e) {
    connectionError.value = 'Nu s-a putut conecta la sesiune'
  }
})

onUnmounted(() => {
  ws.disconnect()
  gameStore.reset()
})
</script>
