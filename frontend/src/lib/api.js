const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_KEY = import.meta.env.VITE_API_KEY || 'debug-assistant-key'

const headers = {
  'Content-Type': 'application/json',
  'x-api-key': API_KEY
}

export async function sendChat(message, topK, useLegacyMode) {
  const endpoint = useLegacyMode ? '/api/chat/legacy' : '/api/chat'
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ message, top_k: topK })
  })
  const raw = await response.json()
  if (!response.ok) {
    throw new Error(raw.detail || 'Backend request failed')
  }
  return normalizeChatResponse(raw)
}

export async function ingestDocument(fileName, content) {
  const response = await fetch(`${BASE_URL}/api/documents/ingest`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ file_name: fileName, content })
  })
  return response.json()
}

export async function fetchLogs() {
  const response = await fetch(`${BASE_URL}/api/debug/logs`, {
    headers
  })
  return response.json()
}

export function streamChat(message, topK, onToken, onDone, onError) {
  const url = `${BASE_URL}/api/chat/stream`
  fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ message, top_k: topK })
  })
    .then(async (res) => {
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const chunks = buffer.split('\n\n')
        buffer = chunks.pop() || ''
        chunks.forEach((chunk) => {
          const event = parseSse(chunk)
          if (!event) return
          if (event.event === 'token') onToken(event.data)
          if (event.event === 'done') onDone(event.data)
        })
      }
    })
    .catch((err) => onError(err.message))
}

function parseSse(chunk) {
  const lines = chunk.split('\n')
  const event = {}
  lines.forEach((line) => {
    if (line.startsWith('event: ')) event.event = line.replace('event: ', '')
    if (line.startsWith('data: ')) event.data = line.replace('data: ', '')
  })
  return event.event ? event : null
}

function normalizeChatResponse(raw) {
  if (raw.answer && raw.trace_id) {
    return {
      answer: raw.answer,
      sources: raw.sources || [],
      traceId: raw.trace_id,
      debug: raw.debug || {},
      raw
    }
  }
  if (raw.response && raw.request_id) {
    return {
      answer: raw.response,
      sources: raw.source_items || [],
      traceId: raw.request_id,
      debug: { ...(raw.meta || {}), normalized_from_legacy: true },
      raw
    }
  }
  throw new Error('Unexpected response schema from backend')
}
