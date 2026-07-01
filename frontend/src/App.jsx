import React, { useState, useRef, useEffect } from 'react';
import { Send, TrendingUp, Info, ExternalLink, Bot, User, Clock, AlertTriangle } from 'lucide-react';
import './index.css';

const API_URL = 'http://127.0.0.1:8000/api/chat';

const GalaxyBackground = () => {
  // Generate a random set of stars only once on mount
  const stars = React.useMemo(() => {
    return Array.from({ length: 150 }).map((_, i) => {
      const size = Math.random() * 2 + 1; // 1px to 3px
      return {
        id: i,
        size: size,
        top: `${Math.random() * 100}%`,
        left: `${Math.random() * 100}%`,
        delay: `${Math.random() * 5}s`,
        duration: `${Math.random() * 3 + 2}s`,
        maxOpacity: Math.random() * 0.5 + 0.3,
      };
    });
  }, []);

  return (
    <div className="galaxy-container">
      {stars.map((star) => (
        <div
          key={star.id}
          className="star"
          style={{
            width: `${star.size}px`,
            height: `${star.size}px`,
            top: star.top,
            left: star.left,
            '--delay': star.delay,
            '--duration': star.duration,
            '--max-opacity': star.maxOpacity,
          }}
        />
      ))}
    </div>
  );
};

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = { role: 'user', content: inputValue };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage.content })
      });

      if (!response.ok) {
        if (response.status === 503) {
          throw new Error('Our servers are currently experiencing high traffic. Please try again in a few moments.');
        }
        throw new Error('Failed to connect to the RAG server.');
      }

      const data = await response.json();
      
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          citation: data.citation,
          last_updated: data.last_updated,
          query_type: data.query_type
        }
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: error.message,
          query_type: 'ERROR',
          isError: true
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <GalaxyBackground />
      <div className={`app-container ${messages.length === 0 ? 'is-empty' : ''}`}>
      <header className="header">
        <div className="logo-container">
          <TrendingUp color="white" size={24} />
        </div>
        <div>
          <h1>HDFC Mutual Fund Assistant</h1>
          <p>Factual, precise answers for 5 exclusive HDFC schemes.</p>
        </div>
      </header>

      <div className="chat-container">
        {messages.length > 0 && messages.map((msg, idx) => (
            <div key={idx} className={`message-wrapper ${msg.role}`}>
              <div className={`message ${msg.role}`}>
                {msg.role === 'assistant' && (
                  <div className="bot-header">
                    <Bot size={16} /> HDFC Agent
                    {msg.query_type && (
                      <span className={`badge ${msg.query_type.toLowerCase()}`}>
                        {msg.query_type}
                      </span>
                    )}
                  </div>
                )}
                
                <div className="message-content">{msg.content}</div>
                
                {msg.role === 'assistant' && msg.citation && (
                  <div className="message-meta">
                    <a href={msg.citation} target="_blank" rel="noreferrer" className="citation-link">
                      <ExternalLink size={12} /> Source on Groww
                    </a>
                    {msg.last_updated && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={12} /> Data as of: {msg.last_updated}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        }

        {isLoading && (
          <div className="message-wrapper bot">
            <div className="message bot">
              <div className="bot-header">
                <Bot size={16} /> HDFC Agent
              </div>
              <div className="typing-indicator">
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="input-container" onSubmit={handleSubmit}>
        <div className="input-wrapper">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask about NAV, exit loads, expense ratio, or minimum SIP..."
            disabled={isLoading}
          />
          <button type="submit" disabled={!inputValue.trim() || isLoading}>
            <Send size={18} />
          </button>
        </div>
      </form>
    </div>
    </>
  );
}

export default App;
