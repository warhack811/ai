/**
 * SessionManager.jsx - FAS 3
 * --------------------------
 * ✅ Sohbet geçmişi listesi
 * ✅ Yeni sohbet oluşturma
 * ✅ Session değiştirme
 * ✅ Session silme
 * ✅ LocalStorage persistence
 * 
 * Kullanım:
 * <SessionManager 
 *   currentSessionId={sessionId}
 *   onSessionChange={(newSessionId) => setSessionId(newSessionId)}
 *   onNewChat={() => startNewChat()}
 * />
 */

import React, { useState, useEffect } from 'react';

const SessionManager = ({ currentSessionId, onSessionChange, onNewChat }) => {
  const [sessions, setSessions] = useState([]);
  const [isOpen, setIsOpen] = useState(false);

  // LocalStorage'dan session'ları yükle
  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = () => {
    try {
      const stored = localStorage.getItem('chat_sessions');
      if (stored) {
        const parsed = JSON.parse(stored);
        setSessions(parsed);
      }
    } catch (err) {
      console.error('Sessions load error:', err);
    }
  };

  const saveSessions = (newSessions) => {
    try {
      localStorage.setItem('chat_sessions', JSON.stringify(newSessions));
      setSessions(newSessions);
    } catch (err) {
      console.error('Sessions save error:', err);
    }
  };

  // Session oluştur/güncelle
  const saveCurrentSession = (sessionId, firstMessage = '') => {
    const existingIndex = sessions.findIndex(s => s.id === sessionId);
    
    if (existingIndex >= 0) {
      // Güncelle
      const updated = [...sessions];
      updated[existingIndex].lastUpdated = new Date().toISOString();
      updated[existingIndex].messageCount = (updated[existingIndex].messageCount || 0) + 1;
      saveSessions(updated);
    } else {
      // Yeni session
      const newSession = {
        id: sessionId,
        title: firstMessage.substring(0, 50) || 'Yeni Sohbet',
        created: new Date().toISOString(),
        lastUpdated: new Date().toISOString(),
        messageCount: 1,
      };
      saveSessions([newSession, ...sessions]);
    }
  };

  // Bu fonksiyonu dışarıya export et (parent'tan çağrılacak)
  useEffect(() => {
    window.saveCurrentSession = saveCurrentSession;
  }, [sessions]);

  const handleNewChat = () => {
    const newSessionId = `session_${Date.now()}`;
    onNewChat();
    onSessionChange(newSessionId);
    setIsOpen(false);
  };

  const handleSessionClick = (sessionId) => {
    onSessionChange(sessionId);
    setIsOpen(false);
  };

  const handleDeleteSession = (sessionId, e) => {
    e.stopPropagation();
    
    if (!confirm('Bu sohbeti silmek istediğinize emin misiniz?')) return;

    const filtered = sessions.filter(s => s.id !== sessionId);
    saveSessions(filtered);

    // Eğer silinen session aktif ise yeni chat başlat
    if (sessionId === currentSessionId) {
      handleNewChat();
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Az önce';
    if (diffMins < 60) return `${diffMins} dk önce`;
    if (diffHours < 24) return `${diffHours} saat önce`;
    if (diffDays < 7) return `${diffDays} gün önce`;
    
    return date.toLocaleDateString('tr-TR', { 
      day: 'numeric', 
      month: 'short' 
    });
  };

  return (
    <div style={{ position: 'relative' }}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
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
          boxShadow: '0 4px 6px -1px rgba(99, 102, 241, 0.3)',
        }}
        onMouseEnter={(e) => e.target.style.transform = 'translateY(-2px)'}
        onMouseLeave={(e) => e.target.style.transform = 'translateY(0)'}
      >
        💬 Sohbetler
        {sessions.length > 0 && (
          <span style={{
            background: '#ffffff',
            color: '#4f46e5',
            padding: '2px 8px',
            borderRadius: '10px',
            fontSize: '12px',
            fontWeight: '700',
          }}>
            {sessions.length}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            onClick={() => setIsOpen(false)}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'transparent',
              zIndex: 999,
            }}
          />
          
          {/* Panel */}
          <div style={{
            position: 'absolute',
            top: '60px',
            left: 0,
            width: '350px',
            maxHeight: '500px',
            background: 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
            borderRadius: '12px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
            border: '1px solid #334155',
            zIndex: 1000,
            overflow: 'hidden',
          }}>
            {/* Header */}
            <div style={{
              padding: '16px',
              borderBottom: '1px solid #334155',
              background: '#1e293b',
            }}>
              <button
                onClick={handleNewChat}
                style={{
                  width: '100%',
                  padding: '12px',
                  borderRadius: '8px',
                  border: 'none',
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  color: '#ffffff',
                  fontSize: '14px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => e.target.style.transform = 'translateY(-1px)'}
                onMouseLeave={(e) => e.target.style.transform = 'translateY(0)'}
              >
                ✨ Yeni Sohbet
              </button>
            </div>

            {/* Sessions List */}
            <div style={{
              maxHeight: '420px',
              overflowY: 'auto',
              padding: '8px',
            }}>
              {sessions.length === 0 ? (
                <div style={{
                  padding: '32px',
                  textAlign: 'center',
                  color: '#64748b',
                  fontSize: '14px',
                }}>
                  <div style={{ fontSize: '48px', marginBottom: '12px' }}>💬</div>
                  Henüz sohbet yok
                </div>
              ) : (
                sessions.map((session) => (
                  <div
                    key={session.id}
                    onClick={() => handleSessionClick(session.id)}
                    style={{
                      padding: '14px',
                      marginBottom: '6px',
                      borderRadius: '8px',
                      background: session.id === currentSessionId ? '#334155' : '#1e293b',
                      border: `1px solid ${session.id === currentSessionId ? '#60a5fa' : '#334155'}`,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                    }}
                    onMouseEnter={(e) => {
                      if (session.id !== currentSessionId) {
                        e.currentTarget.style.background = '#334155';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (session.id !== currentSessionId) {
                        e.currentTarget.style.background = '#1e293b';
                      }
                    }}
                  >
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{
                        color: '#cbd5e1',
                        fontSize: '14px',
                        fontWeight: '600',
                        marginBottom: '4px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}>
                        {session.title}
                      </div>
                      <div style={{
                        color: '#64748b',
                        fontSize: '12px',
                        display: 'flex',
                        gap: '12px',
                      }}>
                        <span>{formatDate(session.lastUpdated)}</span>
                        <span>•</span>
                        <span>{session.messageCount} mesaj</span>
                      </div>
                    </div>
                    
                    <button
                      onClick={(e) => handleDeleteSession(session.id, e)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: '#ef4444',
                        cursor: 'pointer',
                        padding: '4px',
                        fontSize: '16px',
                        lineHeight: 1,
                        borderRadius: '4px',
                        transition: 'all 0.2s',
                      }}
                      onMouseEnter={(e) => {
                        e.target.style.background = '#7f1d1d';
                        e.stopPropagation();
                      }}
                      onMouseLeave={(e) => {
                        e.target.style.background = 'transparent';
                      }}
                    >
                      🗑️
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default SessionManager;