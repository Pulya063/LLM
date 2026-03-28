export default function DebugPanel({ debugState }) {
  return (
    <aside className="debug-panel">
      <h3>Debug Panel</h3>
      <dl>
        <dt>Trace ID</dt>
        <dd>{debugState.traceId || 'n/a'}</dd>
        <dt>Error</dt>
        <dd>{debugState.error || 'none'}</dd>
      </dl>
      <pre>{JSON.stringify(debugState.raw, null, 2)}</pre>
      <pre>{JSON.stringify(debugState.logs, null, 2)}</pre>
    </aside>
  )
}
