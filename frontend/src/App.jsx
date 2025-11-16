/**
 * App.jsx - PROFESSIONAL VERSION
 * -------------------------------
 * ✅ Modern, profesyonel UI
 * ✅ Uncensored mod desteği
 * ✅ Model bilgisi gösterimi
 * ✅ Response time display
 * ✅ Typing indicator
 * ✅ Auto-scroll
 */

import React, { useState, useEffect, useRef } from 'react';
import { useChat } from './hooks/useChat';
import SettingsPanel from './components/SettingsPanel';
import DocumentUpload from './components/DocumentUpload';
import SessionManager from './components/SessionManager';
import MessageBubble from './components/MessageBubble';
import { LoadingSpinner } from './components/LoadingSpinner';  // ✅ NAMED IMPORT
import './App.css';

function App() {
  const [input, setInput] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [showDocUpload, setShowDocUpload] = useState(false);
  const messagesEndRef = useRef(null);
  
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

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Load settings
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

  // Save settings
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
    if (window.confirm('Yeni sohbet başlatmak istediğinize emin misiniz? Mevcut sohbet silinecek.')) {
      clearMessages();
    }
  };

  // Get mode emoji
  const getModeEmoji = (mode) => {
    const emojis = {
      normal: '💼',
      research: '🔬',
      creative: '🎨',
      code: '💻',
      friend: '😊',
      uncensored: '🔥'
    };
    return emojis[mode] || '💼';
  };

  // Get mode display name
  const getModeName = (mode) => {
    const names = {
      normal: 'Normal',
      research: 'Araştırma',
      creative: 'Yaratıcı',
      code: 'Kod',
      friend: 'Arkadaş',
      uncensored: 'Sansürsüz'
    };
    return names[mode] || 'Normal';
  };

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif',
      overflow: 'hidden',
    }}>
      {/* Main Container */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        maxWidth: '1400px',
        margin: '0 auto',
        width: '100%',
        padding: '24px',
        gap: '20px',
      }}>
        {/* Header */}
        <header style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '20px 28px',
          background: 'linear-gradient(145deg, #1e293b 0%, #334155 100%)',
          borderRadius: '20px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.05)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{
              width: '48px',
              height: '48px',
              background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
              borderRadius: '14px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '24px',
              boxShadow: '0 10px 15px -3px rgba(59, 130, 246, 0.4)',
            }}>
              🤖
            </div>
            <div>
              <h1 style={{ 
                margin: 0, 
                color: '#f1f5f9',
                fontSize: '26px',
                fontWeight: '800',
                letterSpacing: '-0.5px',
              }}>
                AI Pro Asistan
              </h1>
              <div style={{ 
                fontSize: '13px', 
                color: '#94a3b8',
                marginTop: '4px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
              }}>
                <span style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '4px 10px',
                  background: 'rgba(59, 130, 246, 0.2)',
                  borderRadius: '8px',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                }}>
                  {getModeEmoji(settings.mode)} {getModeName(settings.mode)}
                </span>
                {settings.mode === 'uncensored' && (
                  <span style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '4px 10px',
                    background: 'rgba(239, 68, 68, 0.2)',
                    borderRadius: '8px',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#fca5a5',
                  }}>
                    ⚠️ Filtresiz
                  </span>
                )}
              </div>
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            {/* New Chat */}
            <button
              onClick={handleNewChat}
              style={{
                background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                border: 'none',
                color: '#ffffff',
                padding: '12px 20px',
                borderRadius: '12px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.2s',
                boxShadow: '0 4px 6px -1px rgba(99, 102, 241, 0.4)',
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 10px 15px -3px rgba(99, 102, 241, 0.5)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 6px -1px rgba(99, 102, 241, 0.4)';
              }}
            >
              ✨ Yeni Sohbet
            </button>

            {/* Document Upload */}
            <button
              onClick={() => setShowDocUpload(true)}
              style={{
                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                border: 'none',
                color: '#ffffff',
                padding: '12px 20px',
                borderRadius: '12px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.2s',
                boxShadow: '0 4px 6px -1px rgba(16, 185, 129, 0.4)',
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 10px 15px -3px rgba(16, 185, 129, 0.5)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 6px -1px rgba(16, 185, 129, 0.4)';
              }}
            >
              📄 Doküman
            </button>

            {/* Settings */}
            <button
              onClick={() => setShowSettings(true)}
              style={{
                background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                border: 'none',
                color: '#ffffff',
                padding: '12px 20px',
                borderRadius: '12px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.2s',
                boxShadow: '0 4px 6px -1px rgba(245, 158, 11, 0.4)',
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 10px 15px -3px rgba(245, 158, 11, 0.5)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 6px -1px rgba(245, 158, 11, 0.4)';
              }}
            >
              ⚙️ Ayarlar
            </button>
          </div>
        </header>

        {/* Messages Container */}
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          background: 'rgba(15, 23, 42, 0.6)',
          borderRadius: '20px',
          overflow: 'hidden',
          boxShadow: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.3)',
          border: '1px solid rgba(255, 255, 255, 0.05)',
        }}>
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '28px',
          }}>
            {messages.length === 0 ? (
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                textAlign: 'center',
                color: '#64748b',
              }}>
                <div style={{ 
                  fontSize: '80px', 
                  marginBottom: '24px',
                  filter: 'drop-shadow(0 10px 20px rgba(59, 130, 246, 0.3))',
                }}>
                  💬
                </div>
                <h2 style={{ 
                  color: '#cbd5e1', 
                  marginBottom: '12px',
                  fontSize: '28px',
                  fontWeight: '800',
                }}>
                  Merhaba! Size nasıl yardımcı olabilirim?
                </h2>
                <p style={{ 
                  maxWidth: '600px',
                  color: '#94a3b8',
                  fontSize: '16px',
                  lineHeight: '1.6',
                }}>
                  Bir soru sorun, doküman yükleyin veya ayarlardan modunuzu seçin.
                  {settings.mode === 'uncensored' && ' 🔥 Sansürsüz mod aktif - hiçbir konu yasak değil.'}
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
                    processingTime={msg.processingTime}
                    isError={msg.isError}
                  />
                ))}
                {isLoading && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '20px',
                    background: 'linear-gradient(145deg, #1e293b 0%, #334155 100%)',
                    borderRadius: '16px',
                    marginTop: '12px',
                    border: '1px solid rgba(255, 255, 255, 0.05)',
                  }}>
                    <LoadingSpinner />
                    <span style={{ color: '#94a3b8', fontSize: '14px', fontWeight: '600' }}>
                      AI düşünüyor...
                    </span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Sources */}
          {lastSources && lastSources.length > 0 && (
            <div style={{
              padding: '20px 28px',
              background: 'linear-gradient(145deg, #1e293b 0%, #334155 100%)',
              borderTop: '1px solid rgba(255, 255, 255, 0.05)',
            }}>
              <div style={{ 
                fontSize: '13px', 
                color: '#94a3b8', 
                marginBottom: '14px', 
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}>
                📚 Kaynaklar ({lastSources.length})
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                {lastSources.map((src, idx) => (
                  <div key={idx} style={{
                    fontSize: '12px',
                    color: '#cbd5e1',
                    padding: '8px 14px',
                    background: 'rgba(59, 130, 246, 0.15)',
                    borderRadius: '10px',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}>
                    <span>{src.type === 'web' ? '🌐' : '📄'}</span>
                    <strong style={{ color: '#60a5fa' }}>{src.title}</strong>
                    {src.url && (
                      <a 
                        href={src.url} 
                        target="_blank" 
                        rel="noreferrer"
                        style={{ 
                          color: '#60a5fa',
                          textDecoration: 'none',
                          fontSize: '16px',
                        }}
                      >
                        🔗
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div style={{
              padding: '16px 28px',
              background: 'linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%)',
              color: '#fca5a5',
              fontSize: '14px',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              borderTop: '1px solid #dc2626',
            }}>
              <span style={{ fontSize: '20px' }}>⚠️</span>
              {error}
            </div>
          )}

          {/* Input Form */}
          <form onSubmit={handleSubmit} style={{
            display: 'flex',
            gap: '14px',
            padding: '24px 28px',
            background: 'linear-gradient(145deg, #1e293b 0%, #334155 100%)',
            borderTop: '1px solid rgba(255, 255, 255, 0.05)',
          }}>
            <input
              type="text"
              placeholder={
                settings.mode === 'uncensored' 
                  ? '🔥 Sansürsüz mod - her şeyi sorabilirsiniz...'
                  : 'Mesajınızı yazın...'
              }
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
              style={{
                flex: 1,
                padding: '16px 22px',
                borderRadius: '14px',
                border: '2px solid #374151',
                background: '#0f172a',
                color: '#e5e7eb',
                fontSize: '15px',
                outline: 'none',
                transition: 'all 0.2s',
                fontWeight: '500',
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#3b82f6';
                e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#374151';
                e.target.style.boxShadow = 'none';
              }}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              style={{
                padding: '16px 32px',
                borderRadius: '14px',
                border: 'none',
                background: isLoading || !input.trim()
                  ? '#374151'
                  : 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                color: '#ffffff',
                cursor: isLoading || !input.trim() ? 'not-allowed' : 'pointer',
                fontWeight: '700',
                fontSize: '16px',
                transition: 'all 0.2s',
                boxShadow: isLoading || !input.trim() 
                  ? 'none' 
                  : '0 10px 15px -3px rgba(59, 130, 246, 0.4)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
              onMouseEnter={(e) => {
                if (!isLoading && input.trim()) {
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.boxShadow = '0 20px 25px -5px rgba(59, 130, 246, 0.5)';
                }
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = isLoading || !input.trim() 
                  ? 'none' 
                  : '0 10px 15px -3px rgba(59, 130, 246, 0.4)';
              }}
            >
              {isLoading ? '⏳' : '📤'} Gönder
            </button>
          </form>
        </div>
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
          setShowDocUpload(false);
        }}
      />
    </div>
  );
}

export default App;