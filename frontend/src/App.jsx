import { useMemo, useState } from 'react'
import ChatWindow from './components/ChatWindow'
import DebugPanel from './components/DebugPanel'
import IncidentPanel from './components/IncidentPanel'
import { analyzeIncident, fetchLogs, ingestDocument, sendChat, streamChat } from './lib/api'

let idCounter = 0

export default function App() {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [topK, setTopK] = useState(4)
  const [useLegacyMode, setUseLegacyMode] = useState(false)
  const [useStreaming, setUseStreaming] = useState(true)
  const [debugState, setDebugState] = useState({ raw: {}, logs: [], error: '', traceId: '' })
  const [docName, setDocName] = useState('incident_notes.txt')
  const [docContent, setDocContent] = useState('')
  const [incidentText, setIncidentText] = useState('')
  const [incidentLoading, setIncidentLoading] = useState(false)
  const [incidentResult, setIncidentResult] = useState(null)

  const canSend = useMemo(() => message.trim().length > 0 && !loading, [message, loading])

  async function onSend(e) {
    e.preventDefault()
    if (!canSend) return
    const userMessage = createMessage('user', message)
    setMessages((prev) => [...prev, userMessage])
    setLoading(true)
    setDebugState((prev) => ({ ...prev, error: '' }))

    if (useStreaming && !useLegacyMode) {
      const assistantId = ++idCounter
      setMessages((prev) => [...prev, { id: assistantId, role: 'assistant', text: '', sources: [] }])
      streamChat(
        message,
        topK,
        (token) => {
          setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, text: `${m.text}${token}` } : m)))
        },
        async (donePayload) => {
          let traceId = ''
          let sources = []
          try {
            const parsed = JSON.parse(donePayload)
            traceId = parsed.trace_id
            sources = (parsed.sources || []).map((s) => ({ source: s, snippet: '' }))
          } catch (err) {
            setDebugState((prev) => ({ ...prev, error: err.message }))
          }
          setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, sources } : m)))
          const logs = await fetchLogs()
          setDebugState({ raw: donePayload, logs: logs.logs || [], error: '', traceId })
          setLoading(false)
        },
        (errorMessage) => {
          setDebugState((prev) => ({ ...prev, error: errorMessage }))
          setLoading(false)
        }
      )
    } else {
      try {
        const result = await sendChat(message, topK, useLegacyMode)
        const assistantMessage = createMessage('assistant', result.answer, result.sources)
        setMessages((prev) => [...prev, assistantMessage])
        const logs = await fetchLogs()
        setDebugState({ raw: result.raw, logs: logs.logs || [], error: '', traceId: result.traceId })
      } catch (error) {
        setDebugState((prev) => ({ ...prev, error: error.message }))
      } finally {
        setLoading(false)
      }
    }
    setMessage('')
  }

  async function onIngest() {
    if (!docName.trim() || !docContent.trim()) return
    try {
      const result = await ingestDocument(docName, docContent)
      const logs = await fetchLogs()
      setDebugState({ raw: result, logs: logs.logs || [], error: '', traceId: debugState.traceId })
      setDocContent('')
    } catch (error) {
      setDebugState((prev) => ({ ...prev, error: error.message }))
    }
  }

  async function onAnalyzeIncident() {
    if (!incidentText.trim()) return
    setIncidentLoading(true)
    try {
      const result = await analyzeIncident(incidentText, topK)
      setIncidentResult(result)
      const logs = await fetchLogs()
      setDebugState({ raw: result.raw, logs: logs.logs || [], error: '', traceId: result.traceId })
    } catch (error) {
      setDebugState((prev) => ({ ...prev, error: error.message }))
    } finally {
      setIncidentLoading(false)
    }
  }

  return (
    <main className="layout">
      <section className="left-panel">
        <h2>Knowledge Base</h2>
        <input value={docName} onChange={(e) => setDocName(e.target.value)} placeholder="file name" />
        <textarea value={docContent} onChange={(e) => setDocContent(e.target.value)} placeholder="Paste troubleshooting notes" />
        <button onClick={onIngest}>Ingest Document</button>
        <h2>Incident Input</h2>
        <textarea
          value={incidentText}
          onChange={(e) => setIncidentText(e.target.value)}
          placeholder="Describe incident: error, timeline, affected users"
        />
        <button onClick={onAnalyzeIncident} disabled={incidentLoading}>Run Incident Analysis</button>
        <IncidentPanel result={incidentResult} loading={incidentLoading} />
      </section>

      <section className="chat-panel">
        <h1>Support Assistant</h1>
        <form onSubmit={onSend} className="controls">
          <textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Ask: why users get 500 after deploy?" />
          <div className="toggles">
            <label>
              Top K
              <input type="number" min="1" max="10" value={topK} onChange={(e) => setTopK(Number(e.target.value))} />
            </label>
            <label>
              Legacy Mode
              <input type="checkbox" checked={useLegacyMode} onChange={(e) => setUseLegacyMode(e.target.checked)} />
            </label>
            <label>
              Streaming
              <input type="checkbox" checked={useStreaming} onChange={(e) => setUseStreaming(e.target.checked)} disabled={useLegacyMode} />
            </label>
          </div>
          <button disabled={!canSend}>Send Message</button>
        </form>
        <ChatWindow messages={messages} loading={loading} />
      </section>

      <DebugPanel debugState={debugState} />
    </main>
  )
}

function createMessage(role, text, sources = []) {
  idCounter += 1
  return { id: idCounter, role, text, sources }
}
