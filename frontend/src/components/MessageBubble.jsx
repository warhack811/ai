/**
 * MessageBubble.jsx - UPDATED
 * ---------------------------
 * ✅ Model bilgisi
 * ✅ Response time
 * ✅ Timestamp
 * ✅ Code syntax highlighting
 */

import React from 'react';

const MessageBubble = ({ 
  role, 
  content, 
  timestamp, 
  model, 
  processingTime,
  isError 
}) => {
  const isUser = role === 'user';

  // Format time
  const formatTime = (date) => {
    if (!date) return '';
    const d = new Date(date);
    return d.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
  };

  // Format processing time
  const formatProcessingTime = (time) => {
    if (!time) return '';
    return time < 1 ? `${(time * 1000).toFixed(0)}ms` : `${time.toFixed(1)}s`;
  };

  // Parse code blocks
  const renderContent = (text) => {
    // Simple code block detection
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(text)) !== null) {
      // Text before code block
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: text.slice(lastIndex, match.index)
        });
      }

      // Code block
      parts.push({
        type: 'code',
        language: match[1] || 'text',
        content: match[2]
      });

      lastIndex = match.index + match[0].length;
    }

    // Remaining text
    if (lastIndex < text.length) {
      parts.push({
        type: 'text',
        content: text.slice(lastIndex)
      });
    }

    // If no code blocks found, return as text
    if (parts.length === 0) {
      return <div style={{ whiteSpace: 'pre-wrap' }}>{text}</div>;
    }

    return (
      <div>
        {parts.map((part, idx) => {
          if (part.type === 'code') {
            return (
              <div key={idx} style={{ marginTop: '12px', marginBottom: '12px' }}>
                <div style={{
                  fontSize: '11px',
                  color: '#94a3b8',
                  marginBottom: '6px',
                  fontWeight: '600',
                  textTransform: 'uppercase',
                }}>
                  {part.language}
                </div>
                <pre style={{
                  background: '#0f172a',
                  padding: '14px',
                  borderRadius: '10px',
                  overflow: 'auto',
                  fontSize: '13px',
                  lineHeight: '1.5',
                  border: '1px solid #334155',
                  margin: 0,
                }}>
                  <code style={{ color: '#e5e7eb', fontFamily: 'monospace' }}>
                    {part.content}
                  </code>
                </pre>
              </div>
            );
          } else {
            return (
              <div key={idx} style={{ whiteSpace: 'pre-wrap' }}>
                {part.content}
              </div>
            );
          }
        })}
      </div>
    );
  };

  return (
    <div style={{
      marginBottom: '20px',
      display: 'flex',
      flexDirection: isUser ? 'row-reverse' : 'row',
      gap: '12px',
      alignItems: 'flex-start',
    }}>
      {/* Avatar */}
      <div style={{
        width: '40px',
        height: '40px',
        borderRadius: '12px',
        background: isUser 
          ? 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'
          : 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '20px',
        flexShrink: 0,
        boxShadow: isUser
          ? '0 4px 6px -1px rgba(59, 130, 246, 0.3)'
          : '0 4px 6px -1px rgba(139, 92, 246, 0.3)',
      }}>
        {isUser ? '👤' : '🤖'}
      </div>

      {/* Message Container */}
      <div style={{
        flex: 1,
        maxWidth: '75%',
      }}>
        {/* Message Bubble */}
        <div style={{
          padding: '16px 20px',
          borderRadius: '16px',
          background: isUser 
            ? 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'
            : isError 
              ? 'linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%)'
              : 'linear-gradient(145deg, #1e293b 0%, #334155 100%)',
          color: '#ffffff',
          fontSize: '15px',
          lineHeight: '1.7',
          boxShadow: isUser
            ? '0 10px 15px -3px rgba(59, 130, 246, 0.3)'
            : '0 10px 15px -3px rgba(0, 0, 0, 0.3)',
          border: '1px solid rgba(255, 255, 255, 0.05)',
        }}>
          {renderContent(content)}
        </div>

        {/* Metadata */}
        {!isUser && (
          <div style={{
            display: 'flex',
            gap: '12px',
            marginTop: '8px',
            fontSize: '12px',
            color: '#64748b',
            fontWeight: '600',
            paddingLeft: '4px',
          }}>
            {timestamp && (
              <span style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}>
                🕒 {formatTime(timestamp)}
              </span>
            )}
            {model && (
              <span style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 8px',
                background: 'rgba(139, 92, 246, 0.15)',
                borderRadius: '6px',
                border: '1px solid rgba(139, 92, 246, 0.2)',
              }}>
                🤖 {model.split('-')[0]}
              </span>
            )}
            {processingTime && (
              <span style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 8px',
                background: processingTime < 5 
                  ? 'rgba(16, 185, 129, 0.15)'
                  : processingTime < 10
                    ? 'rgba(245, 158, 11, 0.15)'
                    : 'rgba(239, 68, 68, 0.15)',
                borderRadius: '6px',
                border: `1px solid ${
                  processingTime < 5 
                    ? 'rgba(16, 185, 129, 0.2)'
                    : processingTime < 10
                      ? 'rgba(245, 158, 11, 0.2)'
                      : 'rgba(239, 68, 68, 0.2)'
                }`,
              }}>
                ⚡ {formatProcessingTime(processingTime)}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;