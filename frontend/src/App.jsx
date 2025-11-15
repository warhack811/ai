/**
 * App.jsx - FAS 3 COMPLETE VERSION
 * ---------------------------------
 * ✅ Tüm componentler entegre
 * ✅ Settings, DocumentUpload, SessionManager
 * ✅ Full responsive layout
 */

import React, { useState, useEffect } from 'react';
import { useChat } from './hooks/useChat';
import SettingsPanel from './components/SettingsPanel';
import DocumentUpload from './components/DocumentUpload';
import SessionManager from './components/SessionManager';
import MessageBubble from './components/MessageBubble';
import { LoadingSpinner } from './components/LoadingSpinner';
import './App.css';

function App() {
  const [input, setInput] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [showDocUpload, setShowDocUpload] = useState(false);
  
  // Settings
  const [settings, setSettings] = useState({
    mode: 'normal',
    safetyLevel: 0,
    temperature: 0.7,
    maxTokens: 2048,
    useWebSearch: false,
    maxSources: 5,
  });

  // Chat hook
  const { 
    messages, 
    isLoading, 
    error, 
    sessionId,
    lastSources,
    sendMessage, 
    clearMessages,
    changeSession 
  } = useChat();

  // Load settings from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('chat_settings');
    if (stored) {
      try {
        setSettings(JSON.parse(stored));
      } catch (err) {
        console.error('Settings load error:', err);
      }
    }
  }, []);

  // Save settings to localStorage
  const handleSaveSettings = (newSettings) => {
    setSettings(newSettings);
    localStorage.setItem('chat_settings', JSON.stringify(newSettings));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    
    sendMessage(input, settings);
    setInput('');
  };

  const handleNewChat = () => {
    clearMessages();
  };

  const handleSessionChange = (newSessionId) => {
    changeSession(newSessionId);
  };

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    }}>
      {/* Main Chat Area */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        maxWidth: '1200px',
        margin: '0 auto',
        width: '100%',
        padding: '20px',
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
          padding: '16px 24px',
          background: 'linear-gradient(145deg, #1e293b 0%, #334155 100%)',
          borderRadius: '16px',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3)',
          border: '1px solid #334155',
        }}>
          <div>
            <h1 style={{ 
              margin: 0, 
              color: '#f1f5f9',
              fontSize: '24px',
              fontWeight: '800',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}>
              🤖 AI Pro Asistan
            </h1>
            <div style={{ 
              fontSize: '13px', 
              color: '#94a3b8',
              marginTop: '4px',
              fontWeight: '500',
            }}>
              Mod: {settings.mode} • Sansür: {['Kapalı', 'Dengeli', 'Aktif'][settings.safetyLevel]}
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            {/* Session Manager */}
            <SessionManager
              currentSessionId={sessionId}
              onSessionChange={handleSessionChange}
              onNewChat={handleNewChat}
            />

            {/* Document Upload Button */}
            <button
              onClick={() => setShowDocUpload(true)}
              style={{
                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                border: 'none',
                color: '#ffffff',
                padding: '10px 16px',
                borderRadius: '10px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.2s',
                boxShadow: '0 4px 6px -1px rgba(16, 185, 129, 0.3)',
              }}
              onMouseEnter={(e) => e.target.style.transform = 'translateY(-2px)'}
              onMouseLeave={(e) => e.target.style.transform = 'translateY(0)'}
            >
              📄 Doküman
            </button>

            {/* Settings Button */}
            <button
              onClick={() => setShowSettings(true)}
              style={{
                background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                border: 'none',
                color: '#ffffff',
                padding: '10px 16px',
                borderRadius: '10px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.2s',
                boxShadow: '0 4px 6px -1px rgba(245, 158, 11, 0.3)',
              }}
              onMouseEnter={(e) => e.target.style.transform = 'translateY(-2px)'}
              onMouseLeave={(e) => e.target.style.transform = 'translateY(0)'}
            >
              ⚙️ Ayarlar
            </button>
          </div>
        </div>

        {/* Messages */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          background: 'rgba(15, 23, 42, 0.5)',
          borderRadius: '16px',
          marginBottom: '20px',
          border: '1px solid #334155',
        }}>
          {messages.length === 0 ? (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: '#64748b',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: '64px', marginBottom: '20px' }}>💬</div>
              <h2 style={{ color: '#cbd5e1', marginBottom: '10px' }}>
                Merhaba! Size nasıl yardımcı olabilirim?
              </h2>
              <p style={{ maxWidth: '500px' }}>
                Bir soru sorun, doküman yükleyin veya ayarlardan sansür seviyenizi belirleyin.
              </p>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <MessageBubble 
                  key={msg.id} 
                  role={msg.role} 
                  content={msg.content}
                  timestamp={msg.timestamp}
                  model={msg.model}
                  isError={msg.isError}
                />
              ))}
              {isLoading && <LoadingSpinner />}
            </>
          )}
        </div>

        {/* Sources */}
        {lastSources && lastSources.length > 0 && (
          <div style={{
            padding: '16px 20px',
            background: 'linear-gradient(145deg, #1e293b 0%, #334155 100%)',
            borderRadius: '12px',
            marginBottom: '16px',
            border: '1px solid #334155',
          }}>
            <div style={{ 
              fontSize: '13px', 
              color: '#94a3b8', 
              marginBottom: '12px', 
              fontWeight: '700',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}>
              📚 Kaynaklar ({lastSources.length})
            </div>
            {lastSources.map((src, idx) => (
              <div key={idx} style={{
                fontSize: '12px',
                color: '#cbd5e1',
                marginBottom: '8px',
                paddingLeft: '12px',
                borderLeft: '3px solid #3b82f6',
                padding: '6px 12px',
                background: 'rgba(59, 130, 246, 0.1)',
                borderRadius: '6px',
              }}>
                <strong style={{ color: '#60a5fa' }}>
                  [{src.type === 'web' ? '🌐' : '📄'} {src.title}]
                </strong>
                {src.url && (
                  <a 
                    href={src.url} 
                    target="_blank" 
                    rel="noreferrer"
                    style={{ 
                      color: '#60a5fa', 
                      marginLeft: '8px',
                      textDecoration: 'none',
                    }}
                  >
                    🔗
                  </a>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{
            padding: '12px 20px',
            background: '#7f1d1d',
            color: '#fca5a5',
            borderRadius: '10px',
            marginBottom: '16px',
            fontSize: '14px',
            border: '1px solid #991b1b',
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* Input */}
        <form onSubmit={handleSubmit} style={{
          display: 'flex',
          gap: '12px',
          padding: '20px',
          background: 'linear-gradient(145deg, #1e293b 0%, #334155 100%)',
          borderRadius: '16px',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3)',
          border: '1px solid #334155',
        }}>
          <input
            type="text"
            placeholder="Mesajınızı yazın..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            style={{
              flex: 1,
              padding: '14px 20px',
              borderRadius: '12px',
              border: '1px solid #475569',
              background: '#0f172a',
              color: '#e5e7eb',
              fontSize: '15px',
              outline: 'none',
              transition: 'all 0.2s',
            }}
            onFocus={(e) => e.target.style.borderColor = '#3b82f6'}
            onBlur={(e) => e.target.style.borderColor = '#475569'}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            style={{
              padding: '14px 28px',
              borderRadius: '12px',
              border: 'none',
              background: isLoading || !input.trim()
                ? '#475569'
                : 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
              color: '#ffffff',
              cursor: isLoading || !input.trim() ? 'not-allowed' : 'pointer',
              fontWeight: '700',
              fontSize: '15px',
              transition: 'all 0.2s',
              boxShadow: isLoading || !input.trim() 
                ? 'none' 
                : '0 4px 6px -1px rgba(59, 130, 246, 0.3)',
            }}
            onMouseEnter={(e) => {
              if (!isLoading && input.trim()) {
                e.target.style.transform = 'translateY(-2px)';
              }
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
            }}
          >
            {isLoading ? '⏳' : '📤'} Gönder
          </button>
        </form>
      </div>

      {/* Modals */}
      <SettingsPanel
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        settings={settings}
        onSave={handleSaveSettings}
      />

      <DocumentUpload
        isOpen={showDocUpload}
        onClose={() => setShowDocUpload(false)}
        onUploadSuccess={(data) => {
          alert(`✅ Başarılı! ${data.chunks_count} parça öğrenildi.`);
        }}
      />
    </div>
  );
}

export default App;