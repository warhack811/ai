// src/components/MessageBubble.jsx
import React from 'react';

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
        wordBreak: 'break-word',
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
        {timestamp && (
          <div style={{ 
            fontSize: '10px', 
            color: '#64748b', 
            marginTop: '4px',
            opacity: 0.6,
          }}>
            {new Date(timestamp).toLocaleTimeString('tr-TR')}
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;