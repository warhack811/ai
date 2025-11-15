// src/App.js

import React from 'react';
import { ChatWindow } from './components/ChatWindow';

function App() {
  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#020617',
        color: '#e5e7eb',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'stretch',
        padding: '16px',
      }}
    >
      <div style={{ width: '100%', maxWidth: '960px', height: '90vh' }}>
        <ChatWindow />
      </div>
    </div>
  );
}

export default App;
