// src/components/LoadingSpinner.jsx

import React from 'react';

export function LoadingSpinner() {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '24px',
    }}>
      <div style={{
        width: '48px',
        height: '48px',
        border: '5px solid rgba(37, 99, 235, 0.1)',
        borderTop: '5px solid #2563eb',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
      }} />
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
      <span style={{
        marginLeft: '16px',
        color: '#94a3b8',
        fontSize: '14px',
        fontWeight: '500',
      }}>
        Yanıt bekleniyor...
      </span>
    </div>
  );
}
