/**
 * SettingsPanel.jsx - UPDATED WITH UNCENSORED MODE
 * -------------------------------------------------
 * ✅ Uncensored mod eklendi
 * ✅ UI iyileştirildi
 */

import React, { useState } from 'react';

const SettingsPanel = ({ isOpen, onClose, settings, onSave }) => {
  const [localSettings, setLocalSettings] = useState(settings);

  if (!isOpen) return null;

  const handleSave = () => {
    onSave(localSettings);
    onClose();
  };

  const safetyLevelLabels = {
    0: 'Sansürsüz',
    1: 'Dengeli',
    2: 'Güvenli'
  };

  const modeOptions = [
    { value: 'normal', label: '💼 Normal', desc: 'Profesyonel asistan' },
    { value: 'research', label: '🔬 Araştırma', desc: 'Detaylı analiz' },
    { value: 'creative', label: '🎨 Yaratıcı', desc: 'İlham verici' },
    { value: 'code', label: '💻 Kod', desc: 'Yazılım geliştirme' },
    { value: 'friend', label: '😊 Arkadaş', desc: 'Samimi sohbet' },
    { value: 'uncensored', label: '🔥 Sansürsüz', desc: 'Tam özgürlük - Dolphin model' },
  ];

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0,0,0,0.85)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      backdropFilter: 'blur(8px)',
    }}>
      <div style={{
        background: 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
        borderRadius: '20px',
        padding: '36px',
        width: '90%',
        maxWidth: '650px',
        maxHeight: '90vh',
        overflow: 'auto',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6)',
        border: '1px solid #334155',
        animation: 'slideIn 0.3s ease-out',
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '32px',
          paddingBottom: '20px',
          borderBottom: '2px solid #334155',
        }}>
          <div>
            <h2 style={{ 
              margin: 0, 
              color: '#f1f5f9',
              fontSize: '28px',
              fontWeight: '800',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}>
              ⚙️ Ayarlar
            </h2>
            <p style={{
              margin: '6px 0 0 0',
              color: '#94a3b8',
              fontSize: '14px',
            }}>
              AI asistanınızı özelleştirin
            </p>
          </div>
          <button onClick={onClose} style={{
            background: '#374151',
            border: 'none',
            color: '#e5e7eb',
            fontSize: '24px',
            cursor: 'pointer',
            padding: '8px',
            width: '40px',
            height: '40px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '10px',
            transition: 'all 0.2s',
            fontWeight: '700',
          }}
          onMouseEnter={(e) => {
            e.target.style.background = '#ef4444';
            e.target.style.transform = 'rotate(90deg)';
          }}
          onMouseLeave={(e) => {
            e.target.style.background = '#374151';
            e.target.style.transform = 'rotate(0deg)';
          }}
          >×</button>
        </div>

        {/* Chat Mode - UPDATED */}
        <div style={{ marginBottom: '32px' }}>
          <label style={{ 
            color: '#cbd5e1', 
            fontSize: '15px', 
            fontWeight: '700',
            display: 'block', 
            marginBottom: '14px',
            letterSpacing: '0.5px',
          }}>
            💬 Sohbet Modu
          </label>
          
          {/* Mode Cards */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '12px',
          }}>
            {modeOptions.map(opt => (
              <div
                key={opt.value}
                onClick={() => setLocalSettings({ ...localSettings, mode: opt.value })}
                style={{
                  padding: '16px',
                  borderRadius: '12px',
                  border: localSettings.mode === opt.value 
                    ? '2px solid #3b82f6' 
                    : '2px solid #334155',
                  background: localSettings.mode === opt.value 
                    ? 'linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%)'
                    : '#1e293b',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  position: 'relative',
                }}
                onMouseEnter={(e) => {
                  if (localSettings.mode !== opt.value) {
                    e.currentTarget.style.borderColor = '#475569';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (localSettings.mode !== opt.value) {
                    e.currentTarget.style.borderColor = '#334155';
                    e.currentTarget.style.transform = 'translateY(0)';
                  }
                }}
              >
                <div style={{
                  fontSize: '16px',
                  fontWeight: '700',
                  color: localSettings.mode === opt.value ? '#ffffff' : '#e5e7eb',
                  marginBottom: '6px',
                }}>
                  {opt.label}
                </div>
                <div style={{
                  fontSize: '12px',
                  color: localSettings.mode === opt.value ? '#bfdbfe' : '#94a3b8',
                }}>
                  {opt.desc}
                </div>
                {localSettings.mode === opt.value && (
                  <div style={{
                    position: 'absolute',
                    top: '8px',
                    right: '8px',
                    fontSize: '16px',
                  }}>
                    ✓
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Safety Level Warning for Uncensored */}
        {localSettings.mode === 'uncensored' && (
          <div style={{
            padding: '16px',
            background: 'linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%)',
            borderRadius: '12px',
            marginBottom: '28px',
            border: '2px solid #dc2626',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'start',
              gap: '12px',
            }}>
              <span style={{ fontSize: '24px' }}>⚠️</span>
              <div>
                <div style={{
                  color: '#fef2f2',
                  fontSize: '14px',
                  fontWeight: '700',
                  marginBottom: '6px',
                }}>
                  Sansürsüz Mod Aktif
                </div>
                <div style={{
                  color: '#fca5a5',
                  fontSize: '13px',
                  lineHeight: '1.6',
                }}>
                  Bu modda AI hiçbir konu kısıtlaması olmadan cevap verir. 
                  Dolphin modeli kullanılır (tam özgürlük).
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Temperature */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '12px',
          }}>
            <label style={{ 
              color: '#cbd5e1', 
              fontSize: '15px', 
              fontWeight: '700',
            }}>
              🌡️ Yaratıcılık (Temperature)
            </label>
            <span style={{ 
              color: '#a78bfa', 
              fontSize: '15px',
              fontWeight: '700',
              background: 'linear-gradient(135deg, #4c1d95 0%, #5b21b6 100%)',
              padding: '6px 14px',
              borderRadius: '12px',
            }}>
              {localSettings.temperature.toFixed(1)}
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={localSettings.temperature}
            onChange={(e) => setLocalSettings({ ...localSettings, temperature: parseFloat(e.target.value) })}
            style={{ 
              width: '100%',
              height: '10px',
              borderRadius: '5px',
              outline: 'none',
              appearance: 'none',
              background: `linear-gradient(to right, #3b82f6 0%, #a78bfa ${localSettings.temperature * 100}%, #374151 ${localSettings.temperature * 100}%, #374151 100%)`,
              cursor: 'pointer',
            }}
          />
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            color: '#64748b', 
            fontSize: '12px', 
            marginTop: '10px',
            fontWeight: '600',
          }}>
            <span>🎯 Tutarlı</span>
            <span>⚖️ Dengeli</span>
            <span>🎨 Yaratıcı</span>
          </div>
        </div>

        {/* Max Tokens */}
        <div style={{ marginBottom: '32px' }}>
          <label style={{ 
            color: '#cbd5e1', 
            fontSize: '15px', 
            fontWeight: '700',
            display: 'block', 
            marginBottom: '12px',
          }}>
            📏 Maksimum Cevap Uzunluğu
          </label>
          <select
            value={localSettings.maxTokens}
            onChange={(e) => setLocalSettings({ ...localSettings, maxTokens: parseInt(e.target.value) })}
            style={{
              width: '100%',
              padding: '14px 18px',
              borderRadius: '12px',
              border: '2px solid #374151',
              background: '#0f172a',
              color: '#e5e7eb',
              fontSize: '15px',
              cursor: 'pointer',
              outline: 'none',
              fontWeight: '600',
              transition: 'all 0.2s',
            }}
            onFocus={(e) => e.target.style.borderColor = '#3b82f6'}
            onBlur={(e) => e.target.style.borderColor = '#374151'}
          >
            <option value="512">⚡ Kısa (512 token)</option>
            <option value="1024">📝 Orta (1024 token)</option>
            <option value="2048">📄 Uzun (2048 token)</option>
            <option value="4096">📚 Çok Uzun (4096 token)</option>
          </select>
        </div>

        {/* Web Search */}
        <div style={{ marginBottom: '32px' }}>
          <label style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            cursor: 'pointer',
            padding: '16px 20px',
            borderRadius: '12px',
            background: localSettings.useWebSearch 
              ? 'linear-gradient(135deg, #065f46 0%, #047857 100%)'
              : '#1e293b',
            border: localSettings.useWebSearch 
              ? '2px solid #10b981'
              : '2px solid #334155',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            if (!localSettings.useWebSearch) {
              e.currentTarget.style.borderColor = '#475569';
            }
          }}
          onMouseLeave={(e) => {
            if (!localSettings.useWebSearch) {
              e.currentTarget.style.borderColor = '#334155';
            }
          }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '24px' }}>🌐</span>
              <div>
                <div style={{
                  color: localSettings.useWebSearch ? '#ffffff' : '#e5e7eb',
                  fontSize: '15px',
                  fontWeight: '700',
                }}>
                  Web Araması
                </div>
                <div style={{
                  color: localSettings.useWebSearch ? '#d1fae5' : '#94a3b8',
                  fontSize: '12px',
                  marginTop: '2px',
                }}>
                  Güncel bilgiler için internetten arama yap
                </div>
              </div>
            </div>
            <input
              type="checkbox"
              checked={localSettings.useWebSearch}
              onChange={(e) => setLocalSettings({ ...localSettings, useWebSearch: e.target.checked })}
              style={{ 
                width: '24px', 
                height: '24px',
                cursor: 'pointer',
                accentColor: '#10b981',
              }}
            />
          </label>
        </div>

        {/* Max Sources */}
        {localSettings.useWebSearch && (
          <div style={{ marginBottom: '32px' }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '12px',
            }}>
              <label style={{ 
                color: '#cbd5e1', 
                fontSize: '15px', 
                fontWeight: '700',
              }}>
                📚 Maksimum Kaynak Sayısı
              </label>
              <span style={{ 
                color: '#34d399', 
                fontSize: '15px',
                fontWeight: '700',
                background: 'linear-gradient(135deg, #064e3b 0%, #065f46 100%)',
                padding: '6px 14px',
                borderRadius: '12px',
              }}>
                {localSettings.maxSources}
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              step="1"
              value={localSettings.maxSources}
              onChange={(e) => setLocalSettings({ ...localSettings, maxSources: parseInt(e.target.value) })}
              style={{ 
                width: '100%',
                height: '10px',
                borderRadius: '5px',
                outline: 'none',
                appearance: 'none',
                background: `linear-gradient(to right, #10b981 0%, #34d399 ${localSettings.maxSources * 10}%, #374151 ${localSettings.maxSources * 10}%, #374151 100%)`,
                cursor: 'pointer',
              }}
            />
          </div>
        )}

        {/* Save Button */}
        <button
          onClick={handleSave}
          style={{
            width: '100%',
            padding: '16px',
            borderRadius: '12px',
            border: 'none',
            background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
            color: '#ffffff',
            fontSize: '17px',
            fontWeight: '700',
            cursor: 'pointer',
            transition: 'all 0.2s',
            boxShadow: '0 10px 15px -3px rgba(37, 99, 235, 0.4)',
            letterSpacing: '0.5px',
          }}
          onMouseEnter={(e) => {
            e.target.style.transform = 'translateY(-2px)';
            e.target.style.boxShadow = '0 20px 25px -5px rgba(37, 99, 235, 0.5)';
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'translateY(0)';
            e.target.style.boxShadow = '0 10px 15px -3px rgba(37, 99, 235, 0.4)';
          }}
        >
          ✅ Ayarları Kaydet
        </button>
      </div>

      <style>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(-20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
};

export default SettingsPanel;