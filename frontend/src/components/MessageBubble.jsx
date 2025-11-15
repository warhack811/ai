// src/components/MessageBubble.jsx

import React from 'react';

export function MessageBubble({ role, content }) {
  const isUser = role === 'user';

  return (
    <div
      className={`message-bubble ${isUser ? 'message-bubble-user' : 'message-bubble-assistant'}`}
      style={{
        alignSelf: isUser ? 'flex-end' : 'flex-start',
        maxWidth: '75%',
        padding: '8px 12px',
        borderRadius: '12px',
        marginBottom: '6px',
        background: isUser ? '#2563eb' : '#111827',
        color: '#f9fafb',
        whiteSpace: 'pre-wrap',
      }}
    >
      {content}
    </div>
  );
}
