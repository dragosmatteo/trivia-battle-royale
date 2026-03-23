import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useGameStore = defineStore('game', () => {
  // Connection state
  const isConnected = ref(false)
  const pin = ref('')
  const nickname = ref('')

  // Game state
  const status = ref('idle') // idle, waiting, playing, round_active, round_ended, loading_next, finished
  const isAlive = ref(true)

  // Current question
  const currentQuestion = ref(null)
  const questionIndex = ref(-1)
  const totalQuestions = ref(0)
  const timeLimit = ref(30)
  const timeLeft = ref(30)
  const selectedAnswer = ref(null)
  const answerLocked = ref(false)
  const answerConfirmed = ref(false)

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

  // League system
  const hasLeagues = ref(false)
  const myLeague = ref('')
  const leagues = ref({ champions: [], challengers: [] })

  // Loading transition
  const loadingMessage = ref('')

  // Timer interval
  let timerInterval = null

  const isSpectator = computed(() => false) // No more spectators - everyone plays

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
        answerConfirmed.value = false
        roundResult.value = null
        myResult.value = null
        loadingMessage.value = ''
        startTimer()
        break

      case 'answer_confirmed':
        answerConfirmed.value = true
        break

      case 'round_result':
        status.value = 'round_ended'
        stopTimer()
        roundResult.value = data
        myResult.value = data.your_result
        leaderboard.value = data.leaderboard
        aliveCount.value = data.alive_count
        break

      case 'loading_next':
        status.value = 'loading_next'
        loadingMessage.value = data.message
        break

      case 'game_over':
        status.value = 'finished'
        stopTimer()
        winner.value = data.winner
        finalLeaderboard.value = data.leaderboard
        leaderboard.value = data.leaderboard
        hasLeagues.value = data.has_leagues || false
        leagues.value = data.leagues || { champions: [], challengers: [] }
        myLeague.value = data.your_league || ''
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
    answerConfirmed.value = false
    roundResult.value = null
    myResult.value = null
    leaderboard.value = []
    players.value = []
    aliveCount.value = 0
    winner.value = ''
    finalLeaderboard.value = []
    hasLeagues.value = false
    myLeague.value = ''
    leagues.value = { champions: [], challengers: [] }
    loadingMessage.value = ''
  }

  return {
    isConnected, pin, nickname, status, isAlive,
    currentQuestion, questionIndex, totalQuestions, timeLimit, timeLeft,
    selectedAnswer, answerLocked, answerConfirmed, roundResult, myResult,
    leaderboard, players, aliveCount, winner, finalLeaderboard,
    isSpectator, hasLeagues, myLeague, leagues, loadingMessage,
    handleMessage, startTimer, stopTimer, reset,
  }
})
