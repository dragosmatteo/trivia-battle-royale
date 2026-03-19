// In production, VITE_WS_URL points to the Render backend WebSocket
// In development, Vite proxy handles /ws -> ws://localhost:8000
const WS_BASE = import.meta.env.VITE_WS_URL || ''

export class GameWebSocket {
  constructor() {
    this.ws = null
    this.listeners = {}
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
  }

  connect(url) {
    return new Promise((resolve, reject) => {
      let wsUrl
      if (WS_BASE) {
        // Production: use explicit backend URL
        wsUrl = WS_BASE + url
      } else {
        // Development: use same host (Vite proxy)
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        wsUrl = `${wsProtocol}//${window.location.host}${url}`
      }

      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        this.reconnectAttempts = 0
        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          const type = data.type
          if (this.listeners[type]) {
            this.listeners[type].forEach((cb) => cb(data))
          }
          if (this.listeners['*']) {
            this.listeners['*'].forEach((cb) => cb(data))
          }
        } catch (e) {
          console.error('WebSocket parse error:', e)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        reject(error)
      }

      this.ws.onclose = () => {
        if (this.listeners['disconnect']) {
          this.listeners['disconnect'].forEach((cb) => cb())
        }
      }
    })
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = []
    }
    this.listeners[event].push(callback)
  }

  off(event) {
    delete this.listeners[event]
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.listeners = {}
  }
}
