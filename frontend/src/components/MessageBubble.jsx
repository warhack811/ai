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
// MessageBubble.jsx - minimal update
const MessageBubble = ({ role, content, timestamp, model, isError }) => {
  return (
    <div style={{
      marginBottom: '16px',
      display: 'flex',
      flexDirection: role === 'user' ? 'row-reverse' : 'row',
    }}>
      <div style={{
        maxWidth: '70%',
        padding: '12px 16px',
        borderRadius: '12px',
        background: role === 'user' 
          ? 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'
          : isError 
            ? '#7f1d1d'
            : 'linear-gradient(145deg, #1e293b 0%, #334155 100%)',
        color: '#ffffff',
        fontSize: '15px',
        lineHeight: '1.6',
      }}>
        {content}
        {model && (
          <div style={{ 
            fontSize: '11px', 
            color: '#94a3b8', 
            marginTop: '6px',
            opacity: 0.7,
          }}>
            🤖 {model}
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;