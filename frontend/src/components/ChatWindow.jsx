export default function ChatWindow({ messages, loading }) {
  return (
    <section className="chat-window">
      {messages.map((msg) => (
        <article key={msg.id} className={`message ${msg.role}`}>
          <h4>{msg.role === 'user' ? 'You' : 'Assistant'}</h4>
          <p>{msg.text}</p>
          {msg.sources?.length ? (
            <ul>
              {msg.sources.map((src, idx) => (
                <li key={`${msg.id}-${idx}`}>{src.source}</li>
              ))}
            </ul>
          ) : null}
        </article>
      ))}
      {loading ? <div className="loading">Thinking...</div> : null}
    </section>
  )
}
