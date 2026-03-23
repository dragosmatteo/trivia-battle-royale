<template>
  <div class="page container" style="max-width: 700px; margin: 0 auto;">

    <!-- Connecting... -->
    <div v-if="!gameStore.isConnected && !connectionError" style="text-align: center; padding: 60px 0;">
      <div style="font-size: 48px; animation: pulse 1s infinite;">&#9876;</div>
      <p style="margin-top: 16px; color: var(--text-secondary);">Se conecteaza la sesiune<span class="waiting-dots"></span></p>
    </div>

    <!-- Connection Error -->
    <div v-else-if="connectionError" style="text-align: center; padding: 60px 0;">
      <div style="font-size: 48px;">&#10060;</div>
      <p style="margin-top: 16px; color: var(--danger);">{{ connectionError }}</p>
      <button class="btn btn-primary" style="margin-top: 16px;" @click="$router.push('/join')">Inapoi</button>
    </div>

    <!-- Waiting Room -->
    <div v-else-if="gameStore.status === 'waiting'" class="fade-in" style="text-align: center; padding: 40px 0;">
      <div style="font-size: 64px; margin-bottom: 16px;">&#128075;</div>
      <h2 style="font-weight: 800; margin-bottom: 8px;">Bun venit, {{ gameStore.nickname }}!</h2>
      <p style="color: var(--text-secondary); margin-bottom: 24px;">Asteptam ca profesorul sa porneasca jocul<span class="waiting-dots"></span></p>

      <div class="card" style="text-align: left;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
          <h3 style="font-weight: 700;">Jucatori conectati</h3>
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
      <h2 style="font-weight: 800; margin-top: 16px;">Jocul incepe!</h2>
      <p style="color: var(--text-secondary); margin-top: 8px;">Pregateste-te...</p>
    </div>

    <!-- Loading Next Question -->
    <div v-else-if="gameStore.status === 'loading_next'" class="fade-in" style="text-align: center; padding: 60px 0;">
      <div class="loading-spinner"></div>
      <h2 style="font-weight: 800; margin-top: 24px; color: var(--accent);">Urmatoarea intrebare...</h2>
      <p style="color: var(--text-secondary); margin-top: 8px;">{{ gameStore.loadingMessage }}</p>
      <div style="margin-top: 20px; display: flex; justify-content: center; gap: 16px; font-size: 14px; color: var(--text-muted);">
        <span>Scorul tau: <strong style="color: var(--accent);">{{ gameStore.roundResult?.your_score || 0 }}</strong></span>
        <span>Acuratete: <strong style="color: var(--success);">{{ gameStore.roundResult?.your_accuracy || 0 }}%</strong></span>
      </div>
    </div>

    <!-- Active Question -->
    <div v-else-if="gameStore.status === 'round_active'" class="fade-in">
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
          <span style="font-size: 13px; color: var(--text-muted);">{{ gameStore.aliveCount }} jucatori</span>
          <span :style="{ fontSize: '20px', fontWeight: 800, color: timerColor }">{{ gameStore.timeLeft }}s</span>
        </div>
      </div>

      <!-- Timer bar -->
      <div class="timer-bar">
        <div class="timer-bar-fill" :class="timerClass" :style="{ width: timerPercent + '%' }"></div>
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
          :disabled="gameStore.answerLocked"
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
          &#10003; Raspunsul tau a fost inregistrat! Asteptam ceilalti jucatori<span class="waiting-dots"></span>
        </p>
        <p v-else style="color: var(--warning); font-size: 14px;">
          Se trimite raspunsul<span class="waiting-dots"></span>
        </p>
      </div>
    </div>

    <!-- Round Result -->
    <div v-else-if="gameStore.status === 'round_ended'" class="fade-in">
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
          <h3 style="color: var(--danger); font-weight: 800;">Gresit!</h3>
          <p style="color: var(--text-muted); font-size: 14px;">0 puncte in aceasta runda</p>
        </div>
        <div v-else-if="gameStore.myResult?.status === 'timeout'" style="margin-bottom: 12px;">
          <div style="font-size: 48px;">&#9200;</div>
          <h3 style="color: var(--warning); font-weight: 800;">Timpul a expirat!</h3>
          <p style="color: var(--text-muted); font-size: 14px;">Nu ai raspuns la timp - 0 puncte</p>
        </div>

        <!-- Your stats -->
        <div style="display: flex; justify-content: center; gap: 24px; margin-top: 12px; font-size: 13px; color: var(--text-secondary);">
          <div><strong style="color: var(--accent);">{{ gameStore.roundResult?.your_score || 0 }}</strong> puncte</div>
          <div><strong style="color: var(--success);">{{ gameStore.roundResult?.your_accuracy || 0 }}%</strong> acuratete</div>
          <div>Serie: <strong style="color: var(--gold);">{{ gameStore.roundResult?.your_streak || 0 }}</strong></div>
        </div>
      </div>

      <!-- Correct Answer Card -->
      <div class="card" style="margin-bottom: 16px; border-color: var(--success);">
        <h4 style="font-weight: 700; margin-bottom: 12px; color: var(--success);">&#10003; Raspunsul corect</h4>
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
          <strong>Explicatie:</strong> {{ gameStore.roundResult.explanation }}
        </div>
      </div>

      <!-- Round Statistics -->
      <div class="card" style="margin-bottom: 16px;">
        <h4 style="font-weight: 700; margin-bottom: 12px;">Statistici runda</h4>
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
        <div v-for="p in gameStore.leaderboard.slice(0, 10)" :key="p.nickname"
          class="leaderboard-item"
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
          <span class="leaderboard-score">{{ p.score }}</span>
        </div>
      </div>

      <p v-if="!gameStore.roundResult?.is_last_question" style="text-align: center; color: var(--text-muted); margin-top: 16px; font-size: 13px;">
        Urmatoarea intrebare vine in curand<span class="waiting-dots"></span>
      </p>
    </div>

    <!-- Game Over -->
    <div v-else-if="gameStore.status === 'finished'" class="fade-in" style="text-align: center;">
      <div style="font-size: 80px; margin-bottom: 16px;">&#127942;</div>
      <h1 class="winner-text">{{ gameStore.winner }}</h1>
      <p style="font-size: 18px; color: var(--text-secondary); margin-bottom: 8px;">a castigat jocul!</p>

      <div v-if="gameStore.winner === gameStore.nickname" style="margin-bottom: 24px;">
        <p style="font-size: 24px; color: var(--gold); font-weight: 800;">&#127881; Felicitari! Esti campionul! &#127881;</p>
      </div>

      <!-- League Assignment -->
      <div v-if="gameStore.hasLeagues" class="card" style="margin-bottom: 24px; text-align: center;">
        <div v-if="gameStore.myLeague === 'champions'">
          <div style="font-size: 56px; margin-bottom: 8px;">&#11088;</div>
          <h2 style="font-weight: 800; color: var(--gold);">Liga Campionilor</h2>
          <p style="color: var(--text-secondary); margin-top: 8px;">Felicitari! Esti in top si mergi mai departe cu cei mai buni!</p>
          <div style="margin-top: 12px; padding: 8px 16px; background: rgba(255,215,0,0.1); border-radius: 8px; display: inline-block;">
            <span style="font-size: 13px; color: var(--gold);">{{ gameStore.leagues.champions.join(', ') }}</span>
          </div>
        </div>
        <div v-else-if="gameStore.myLeague === 'challengers'">
          <div style="font-size: 56px; margin-bottom: 8px;">&#128170;</div>
          <h2 style="font-weight: 800; color: var(--accent);">Liga Provocarii</h2>
          <p style="color: var(--text-secondary); margin-top: 8px;">Continui sa te antrenezi! Data viitoare vei fi in top!</p>
          <div style="margin-top: 12px; padding: 8px 16px; background: rgba(108,92,231,0.1); border-radius: 8px; display: inline-block;">
            <span style="font-size: 13px; color: var(--accent);">{{ gameStore.leagues.challengers.join(', ') }}</span>
          </div>
        </div>
      </div>

      <!-- Final Leaderboard -->
      <div class="card" style="text-align: left; margin-bottom: 24px;">
        <h3 style="font-weight: 700; margin-bottom: 12px;">Clasament final</h3>

        <!-- League divider -->
        <template v-if="gameStore.hasLeagues">
          <div style="text-align: center; margin-bottom: 8px; font-size: 12px; color: var(--gold); font-weight: 700;">
            &#11088; Liga Campionilor
          </div>
        </template>

        <div v-for="(p, idx) in gameStore.finalLeaderboard" :key="p.nickname">
          <!-- League divider between champions and challengers -->
          <div v-if="gameStore.hasLeagues && p.league === 'challengers' && (idx === 0 || gameStore.finalLeaderboard[idx-1]?.league === 'champions')"
            style="border-top: 2px dashed var(--border); margin: 12px 0; padding-top: 8px; text-align: center; font-size: 12px; color: var(--accent); font-weight: 700;">
            &#128170; Liga Provocarii
          </div>

          <div class="leaderboard-item"
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
      </div>

      <div style="display: flex; gap: 12px; justify-content: center;">
        <button class="btn btn-primary btn-lg" @click="$router.push('/join')">Joaca din nou</button>
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
  if (gameStore.answerLocked) return
  gameStore.selectedAnswer = index
  gameStore.answerLocked = true
  ws.send({ action: 'answer', selected_option: index })
}

onMounted(async () => {
  gameStore.reset()
  ws.on('*', (data) => {
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
