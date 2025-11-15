// src/components/ChatWindow.jsx

import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../hooks/useChat';
import { MessageBubble } from './MessageBubble';
import { LoadingSpinner } from './LoadingSpinner';

export function ChatWindow() {
  const { messages, isLoading, error, sendMessage, lastSources } = useChat();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    sendMessage(input, {
      mode: 'normal',
      useWebSearch: false,
    });
    setInput('');
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        borderRadius: '12px',
        border: '1px solid #1f2933',
        background: '#020617',
      }}
    >
      <div
        style={{
          padding: '10px 14px',
          borderBottom: '1px solid #1f2933',
          fontWeight: 600,
          color: '#e5e7eb',
        }}
      >
        AI Pro Asistan
      </div>

      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
        }}
      >
        {messages.map((msg) => (
          <MessageBubble key={msg.id} role={msg.role} content={msg.content} />
        ))}

        {isLoading && <LoadingSpinner />}

        {error && (
          <div style={{ color: '#f97373', fontSize: '0.85rem', marginTop: '4px' }}>
            Hata: {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Kaynaklar paneli (son cevabın kaynakları) */}
      {lastSources && lastSources.length > 0 && (
        <div
          style={{
            borderTop: '1px solid #1f2933',
            padding: '8px 10px',
            maxHeight: '160px',
            overflowY: 'auto',
            background: '#020617',
          }}
        >
          <div style={{ fontSize: '0.85rem', color: '#9ca3af', marginBottom: '4px' }}>
            Kaynaklar:
          </div>
          {lastSources.map((src, idx) => (
            <div
              key={idx}
              style={{
                fontSize: '0.8rem',
                color: '#d1d5db',
                marginBottom: '4px',
              }}
            >
              <strong>[{src.type}]</strong>{' '}
              {src.url ? (
                <a
                  href={src.url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: '#60a5fa' }}
                >
                  {src.title}
                </a>
              ) : (
                <span>{src.title}</span>
              )}
              {src.snippet && (
                <div style={{ color: '#9ca3af', marginTop: '2px' }}>{src.snippet}</div>
              )}
            </div>
          ))}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        style={{
          display: 'flex',
          padding: '8px',
          borderTop: '1px solid #1f2933',
          gap: '8px',
        }}
      >
        <input
          type="text"
          placeholder="Mesaj yaz..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          style={{
            flex: 1,
            padding: '8px 10px',
            borderRadius: '999px',
            border: '1px solid #374151',
            background: '#020617',
            color: '#e5e7eb',
            outline: 'none',
          }}
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          style={{
            padding: '8px 16px',
            borderRadius: '999px',
            border: 'none',
            background: isLoading ? '#4b5563' : '#2563eb',
            color: '#f9fafb',
            cursor: isLoading ? 'default' : 'pointer',
          }}
        >
          Gönder
        </button>
      </form>
    </div>
  );
}
