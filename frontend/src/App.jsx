import { useState, useRef, useEffect } from 'react';
import { ArrowUp, ArrowUpRight, ShieldCheck, ChevronRight } from 'lucide-react';
import './index.css';

const API_URL = `${import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000'}/api/chat`;

const SCHEMES = [
  { name: 'HDFC Large Cap Fund', short: 'Large Cap Fund', category: 'Equity', tile: 'L' },
  { name: 'HDFC Mid-Cap Opportunities Fund', short: 'Mid-Cap Opportunities', category: 'Equity', tile: 'M' },
  { name: 'HDFC Small Cap Fund', short: 'Small Cap Fund', category: 'Equity', tile: 'S' },
  { name: 'HDFC Gold ETF Fund of Fund', short: 'Gold ETF Fund of Fund', category: 'Commodity', tile: 'Au' },
  { name: 'HDFC Silver ETF Fund of Fund', short: 'Silver ETF Fund of Fund', category: 'Commodity', tile: 'Ag' },
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

const formatDate = (iso) => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
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

function Logo({ size = 32 }) {
  return (
    <span className="logo" style={{ width: size, height: size }} aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 16l5-5 4 4 7-8" />
      </svg>
    </span>
  );
}

// Twinkling starfield behind the whole app. Static when reduced motion is requested.
function Stars() {
  const ref = useRef(null);

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas.getContext('2d');
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let w = 0;
    let h = 0;
    let stars = [];
    let raf = 0;

    const draw = (t) => {
      ctx.clearRect(0, 0, w, h);
      for (const s of stars) {
        const tw = reduce ? 0.7 : 0.5 + 0.5 * Math.sin((t / 1000) * s.speed + s.phase);
        const a = s.base * (0.15 + 0.85 * tw);
        const rgb = s.green ? '0,208,156' : '236,239,243';
        ctx.fillStyle = `rgba(${rgb},${a})`;
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fill();
        if (s.r > 1.1) {
          ctx.fillStyle = `rgba(${rgb},${a * 0.14})`;
          ctx.beginPath();
          ctx.arc(s.x, s.y, s.r * 3.4, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      if (!reduce) raf = requestAnimationFrame(draw);
    };

    const init = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = window.innerWidth;
      h = window.innerHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.min(300, Math.round((w * h) / 6500));
      stars = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        r: Math.random() * 1.4 + 0.35,
        base: Math.random() * 0.55 + 0.45,
        speed: Math.random() * 1.6 + 0.4,
        phase: Math.random() * Math.PI * 2,
        green: Math.random() < 0.12,
      }));
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(draw);
    };

    init();
    window.addEventListener('resize', init);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', init);
    };
  }, []);

  return <canvas ref={ref} className="stars" aria-hidden="true" />;
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

  const schemeButton = (s) => (
    <button type="button" className="scheme" onClick={() => scope(s.name)}>
      <span className="tile">{s.tile}</span>
      <span className="scheme-text">
        <span className="scheme-name">{s.short}</span>
        <span className="scheme-cat">{s.category}</span>
      </span>
      <ChevronRight size={18} className="chev" aria-hidden="true" />
    </button>
  );

  return (
    <>
      <Stars />
      <div className="app">
        <header className="bar">
          <div className="bar-inner">
            <div className="brand">
              <Logo />
              <span className="wordmark">Fund Assistant</span>
            </div>
            <span className="badge">
              <ShieldCheck size={15} aria-hidden="true" />
              Facts only, no advice
            </span>
          </div>
        </header>

        <div className="frame">
          <aside className="rail" aria-label="Covered schemes">
            <h2 className="section-title">Covered schemes</h2>
            <ul className="rail-list">
              {SCHEMES.map((s) => (
                <li key={s.name}>{schemeButton(s)}</li>
              ))}
            </ul>
            <p className="rail-note">
              Tap a scheme to ask about it. Data comes from public fund pages and is refreshed daily.
            </p>
          </aside>

          <div className="content">
            <main className="stage">
              {empty ? (
                <section className="welcome">
                  <h1>What would you like to know about your HDFC fund?</h1>
                  <p className="lede">
                    Ask about NAV, exit load, expense ratio or minimum SIP. Every answer links to its source.
                  </p>

                  <div className="only-narrow">
                    <h2 className="section-title">Covered schemes</h2>
                    <ul className="schemes">
                      {SCHEMES.map((s, i) => (
                        <li key={s.name} style={{ '--i': i }}>{schemeButton(s)}</li>
                      ))}
                    </ul>
                  </div>

                  <h2 className="section-title">Popular questions</h2>
                  <ul className="asks">
                    {SUGGESTIONS.map((s, i) => (
                      <li key={s} style={{ '--i': i + 2 }}>
                        <button type="button" onClick={() => ask(s)}>
                          <span>{s}</span>
                          <ArrowUpRight size={18} aria-hidden="true" />
                        </button>
                      </li>
                    ))}
                  </ul>
                </section>
              ) : (
                <ol className="thread">
                  {turns.map((turn, i) => (
                    <li key={i} className="turn">
                      <div className="you"><p>{turn.query}</p></div>

                      <div className="bot">
                        <Logo size={28} />
                        {turn.reply ? (
                          <article className={`answer${turn.reply.type === 'ERROR' ? ' is-error' : ''}`}>
                            {NOTES[turn.reply.type] && <p className="note">{NOTES[turn.reply.type]}</p>}
                            <p className={`answer-text${turn.reply.answer.length <= 24 ? ' is-figure' : ''}`}>
                              <RichText text={turn.reply.answer} />
                            </p>
                            {(turn.reply.citation || turn.reply.lastUpdated) && (
                              <footer className="sources">
                                {turn.reply.citation && (
                                  <a href={turn.reply.citation} target="_blank" rel="noreferrer" className="source-pill">
                                    Source: Groww <ArrowUpRight size={14} aria-hidden="true" />
                                  </a>
                                )}
                                {turn.reply.lastUpdated && <span>Updated {formatDate(turn.reply.lastUpdated)}</span>}
                              </footer>
                            )}
                          </article>
                        ) : (
                          <div className="answer skeleton" role="status" aria-label="Checking the scheme pages">
                            <span /><span /><span />
                          </div>
                        )}
                      </div>
                    </li>
                  ))}
                  <li ref={endRef} aria-hidden="true" />
                </ol>
              )}
            </main>

            <div className="dock">
              <form className="composer" onSubmit={onSubmit}>
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
                  <ArrowUp size={20} strokeWidth={2.5} />
                </button>
              </form>
              <p className="fine">Answers can lag by a day. Not investment advice.</p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default App;
