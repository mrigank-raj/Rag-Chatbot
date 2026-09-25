import { useState, useRef, useEffect } from 'react';
import { ArrowUp, ArrowUpRight } from 'lucide-react';
import './index.css';

const API_URL = `${import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000'}/api/chat`;

const SCHEMES = [
  { name: 'HDFC Large Cap Fund', category: 'Equity' },
  { name: 'HDFC Mid-Cap Opportunities Fund', category: 'Equity' },
  { name: 'HDFC Small Cap Fund', category: 'Equity' },
  { name: 'HDFC Gold ETF Fund of Fund', category: 'Commodity' },
  { name: 'HDFC Silver ETF Fund of Fund', category: 'Commodity' },
];

const SUGGESTIONS = [
  'What is the exit load of HDFC Small Cap Fund?',
  'Minimum SIP amount for HDFC Mid-Cap Opportunities Fund',
  'Expense ratio of HDFC Gold ETF Fund of Fund',
  'What is the NAV of HDFC Large Cap Fund?',
];

const NOTES = {
  ADVISORY: 'Not investment advice',
  OUT_OF_SCOPE: 'Outside the five covered schemes',
};

// Renders [label](url) markdown links inside otherwise plain text.
function RichText({ text }) {
  const parts = text.split(/(\[[^\]]+\]\(https?:\/\/[^)\s]+\))/g);
  return parts.map((part, i) => {
    const m = part.match(/^\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)$/);
    return m ? (
      <a key={i} href={m[2]} target="_blank" rel="noreferrer">{m[1]}</a>
    ) : (
      part
    );
  });
}

function Mark() {
  return (
    <svg className="mark" viewBox="0 0 24 24" aria-hidden="true">
      <rect x="3" y="14" width="4" height="7" />
      <rect x="10" y="9" width="4" height="12" />
      <rect x="17" y="3" width="4" height="18" className="mark-peak" />
    </svg>
  );
}

function App() {
  const [turns, setTurns] = useState([]);
  const [value, setValue] = useState('');
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);
  const endRef = useRef(null);

  useEffect(() => {
    if (turns.length) endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [turns, loading]);

  const ask = async (text) => {
    const query = text.trim();
    if (query.length < 3 || loading) return;

    setTurns((t) => [...t, { query }]);
    setValue('');
    setLoading(true);

    let reply;
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      if (!res.ok) {
        throw new Error(
          res.status === 503
            ? 'The assistant is busy right now. Try again in a moment.'
            : "Couldn't reach the assistant. Check your connection and try again."
        );
      }
      const data = await res.json();
      reply = {
        answer: data.answer,
        citation: data.citation,
        lastUpdated: data.last_updated,
        type: data.query_type,
      };
    } catch (err) {
      reply = { answer: err.message, type: 'ERROR' };
    }

    setTurns((t) => t.map((turn, i) => (i === t.length - 1 ? { ...turn, reply } : turn)));
    setLoading(false);
  };

  const onSubmit = (e) => {
    e.preventDefault();
    ask(value);
  };

  const scope = (name) => {
    setValue(`${name}: `);
    inputRef.current?.focus();
  };

  const empty = turns.length === 0;

  return (
    <div className={`shell${empty ? ' is-empty' : ''}`}>
      <header className="top">
        <div className="brand">
          <Mark />
          <span className="wordmark">Fund Assistant</span>
        </div>
        <p className="disclaimer">Facts from public fund pages. Not investment advice.</p>
      </header>

      <nav className="index" aria-label="Covered schemes">
        {SCHEMES.map((s) => (
          <button key={s.name} type="button" className="scheme" onClick={() => scope(s.name)}>
            <span className="scheme-name">{s.name.replace('HDFC ', '')}</span>
            <span className="scheme-cat">{s.category}</span>
          </button>
        ))}
      </nav>

      <main className="main">
        {empty ? (
          <section className="intro">
            <h1>
              <span className="line"><span>Ask a fact about</span></span>
              <span className="line"><span>an HDFC fund.</span></span>
            </h1>
            <p className="lede">
              NAV, exit load, expense ratio, minimum SIP. Every answer links to the page it came from.
            </p>
            <ul className="suggestions">
              {SUGGESTIONS.map((s) => (
                <li key={s}>
                  <button type="button" onClick={() => ask(s)}>{s}</button>
                </li>
              ))}
            </ul>
          </section>
        ) : (
          <ol className="thread">
            {turns.map((turn, i) => (
              <li key={i} className="turn">
                <h2 className="question">{turn.query}</h2>

                {turn.reply ? (
                  <article className={`answer${turn.reply.type === 'ERROR' ? ' is-error' : ''}`}>
                    {NOTES[turn.reply.type] && <p className="note">{NOTES[turn.reply.type]}</p>}
                    <p className="answer-text"><RichText text={turn.reply.answer} /></p>
                    {(turn.reply.citation || turn.reply.lastUpdated) && (
                      <footer className="sources">
                        {turn.reply.citation && (
                          <a href={turn.reply.citation} target="_blank" rel="noreferrer">
                            Source: Groww <ArrowUpRight size={14} aria-hidden="true" />
                          </a>
                        )}
                        {turn.reply.lastUpdated && <span>Data as of {turn.reply.lastUpdated}</span>}
                      </footer>
                    )}
                  </article>
                ) : (
                  <p className="reading" role="status">Checking the scheme pages</p>
                )}
              </li>
            ))}
            <li ref={endRef} aria-hidden="true" />
          </ol>
        )}
      </main>

      <form className={`console${loading ? ' is-busy' : ''}`} onSubmit={onSubmit}>
        <span className="trace" aria-hidden="true" />
        <input
          ref={inputRef}
          type="text"
          value={value}
          maxLength={500}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Ask about NAV, exit load or SIP"
          aria-label="Your question"
          disabled={loading}
          autoFocus
        />
        <button type="submit" aria-label="Send question" disabled={value.trim().length < 3 || loading}>
          <ArrowUp size={20} strokeWidth={2.25} />
        </button>
      </form>
    </div>
  );
}

export default App;
