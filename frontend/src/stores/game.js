import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useGameStore = defineStore('game', () => {
  // Connection state
  const isConnected = ref(false)
  const pin = ref('')
  const nickname = ref('')

  // Game state
  const status = ref('idle') // idle, waiting, playing, round_active, round_ended, finished
  const isAlive = ref(true)

  // Current question
  const currentQuestion = ref(null)
  const questionIndex = ref(-1)
  const totalQuestions = ref(0)
  const timeLimit = ref(30)
  const timeLeft = ref(30)
  const selectedAnswer = ref(null)
  const answerLocked = ref(false)

  // Round result
  const roundResult = ref(null)
  const myResult = ref(null)

  // Leaderboard & players
  const leaderboard = ref([])
  const players = ref([])
  const aliveCount = ref(0)

  // Game over
  const winner = ref('')
  const finalLeaderboard = ref([])

  // Timer interval
  let timerInterval = null

  const isSpectator = computed(() => !isAlive.value && status.value !== 'finished')
  const isSuddenDeath = computed(() => roundResult.value?.is_sudden_death || false)

  function startTimer() {
    stopTimer()
    timeLeft.value = timeLimit.value
    timerInterval = setInterval(() => {
      if (timeLeft.value > 0) {
        timeLeft.value--
      } else {
        stopTimer()
      }
    }, 1000)
  }

  function stopTimer() {
    if (timerInterval) {
      clearInterval(timerInterval)
      timerInterval = null
    }
  }

  function handleMessage(data) {
    switch (data.type) {
      case 'joined':
        isConnected.value = true
        nickname.value = data.nickname
        status.value = 'waiting'
        break

      case 'room_created':
        isConnected.value = true
        pin.value = data.pin
        status.value = 'waiting'
        break

      case 'player_list':
        players.value = data.players
        break

      case 'game_started':
        status.value = 'playing'
        totalQuestions.value = data.total_questions
        timeLimit.value = data.time_per_question
        isAlive.value = true
        break

      case 'question':
        status.value = 'round_active'
        currentQuestion.value = data
        questionIndex.value = data.index
        aliveCount.value = data.alive_count
        selectedAnswer.value = null
        answerLocked.value = false
        roundResult.value = null
        myResult.value = null
        startTimer()
        break

      case 'round_result':
        status.value = 'round_ended'
        stopTimer()
        roundResult.value = data
        myResult.value = data.your_result
        leaderboard.value = data.leaderboard
        isAlive.value = data.is_alive !== undefined ? data.is_alive : isAlive.value
        aliveCount.value = data.alive_count
        break

      case 'game_over':
        status.value = 'finished'
        stopTimer()
        winner.value = data.winner
        finalLeaderboard.value = data.leaderboard
        leaderboard.value = data.leaderboard
        break

      case 'error':
        console.error('Game error:', data.message)
        break
    }
  }

  function reset() {
    stopTimer()
    isConnected.value = false
    pin.value = ''
    nickname.value = ''
    status.value = 'idle'
    isAlive.value = true
    currentQuestion.value = null
    questionIndex.value = -1
    totalQuestions.value = 0
    selectedAnswer.value = null
    answerLocked.value = false
    roundResult.value = null
    myResult.value = null
    leaderboard.value = []
    players.value = []
    aliveCount.value = 0
    winner.value = ''
    finalLeaderboard.value = []
  }

  return {
    isConnected, pin, nickname, status, isAlive,
    currentQuestion, questionIndex, totalQuestions, timeLimit, timeLeft,
    selectedAnswer, answerLocked, roundResult, myResult,
    leaderboard, players, aliveCount, winner, finalLeaderboard,
    isSpectator, isSuddenDeath,
    handleMessage, startTimer, stopTimer, reset,
  }
})
