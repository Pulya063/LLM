export default function IncidentPanel({ result, loading }) {
  return (
    <section className="incident-panel">
      <h3>Incident Analyzer</h3>
      {loading ? <p>Analyzing...</p> : null}
      {!result ? <p>Paste incident details and run analysis.</p> : null}
      {result ? (
        <>
          <h4>Summary</h4>
          <p>{result.summary}</p>
          <h4>Root cause</h4>
          <p>{result.rootCause}</p>
          <h4>Impact</h4>
          <p>{result.impact}</p>
          <h4>Actions</h4>
          <ul>
            {result.actions.map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </>
      ) : null}
    </section>
  )
}
