/**
 * SettingsPanel.jsx - FAS 3
 * -------------------------
 * ✅ Sansür seviyesi slider (0-2)
 * ✅ Temperature control
 * ✅ Max tokens
 * ✅ Chat mode seçimi
 * ✅ Web search toggle
 * 
 * Kullanım:
 * <SettingsPanel 
 *   isOpen={showSettings}
 *   onClose={() => setShowSettings(false)}
 *   settings={settings}
 *   onSave={(newSettings) => setSettings(newSettings)}
 * />
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
    { value: 'normal', label: 'Normal' },
    { value: 'research', label: 'Araştırma' },
    { value: 'creative', label: 'Yaratıcı' },
    { value: 'code', label: 'Kod' },
    { value: 'friend', label: 'Arkadaş' },
    { value: 'turkish_teacher', label: 'Türkçe Öğretmen' },
  ];

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0,0,0,0.8)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        background: 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
        borderRadius: '16px',
        padding: '32px',
        width: '90%',
        maxWidth: '600px',
        maxHeight: '85vh',
        overflow: 'auto',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        border: '1px solid #334155',
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '32px',
        }}>
          <h2 style={{ 
            margin: 0, 
            color: '#f1f5f9',
            fontSize: '24px',
            fontWeight: '700',
          }}>
            ⚙️ Ayarlar
          </h2>
          <button onClick={onClose} style={{
            background: 'transparent',
            border: 'none',
            color: '#94a3b8',
            fontSize: '28px',
            cursor: 'pointer',
            padding: '0',
            width: '32px',
            height: '32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '8px',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => e.target.style.background = '#334155'}
          onMouseLeave={(e) => e.target.style.background = 'transparent'}
          >×</button>
        </div>

        {/* Chat Mode */}
        <div style={{ marginBottom: '28px' }}>
          <label style={{ 
            color: '#cbd5e1', 
            fontSize: '14px', 
            fontWeight: '600',
            display: 'block', 
            marginBottom: '10px',
          }}>
            💬 Sohbet Modu
          </label>
          <select
            value={localSettings.mode}
            onChange={(e) => setLocalSettings({ ...localSettings, mode: e.target.value })}
            style={{
              width: '100%',
              padding: '12px 16px',
              borderRadius: '10px',
              border: '1px solid #374151',
              background: '#0f172a',
              color: '#e5e7eb',
              fontSize: '15px',
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            {modeOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        {/* Safety Level */}
        <div style={{ marginBottom: '28px' }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '10px',
          }}>
            <label style={{ 
              color: '#cbd5e1', 
              fontSize: '14px', 
              fontWeight: '600',
            }}>
              🛡️ Sansür Seviyesi
            </label>
            <span style={{ 
              color: '#60a5fa', 
              fontSize: '14px',
              fontWeight: '700',
              background: '#1e3a8a',
              padding: '4px 12px',
              borderRadius: '12px',
            }}>
              {safetyLevelLabels[localSettings.safetyLevel]}
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="2"
            step="1"
            value={localSettings.safetyLevel}
            onChange={(e) => setLocalSettings({ ...localSettings, safetyLevel: parseInt(e.target.value) })}
            style={{ 
              width: '100%',
              height: '8px',
              borderRadius: '4px',
              outline: 'none',
              background: `linear-gradient(to right, #ef4444 0%, #f59e0b ${localSettings.safetyLevel * 50}%, #10b981 100%)`,
            }}
          />
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            color: '#64748b', 
            fontSize: '12px', 
            marginTop: '8px',
          }}>
            <span>🔥 Sansürsüz</span>
            <span>⚖️ Dengeli</span>
            <span>🔒 Güvenli</span>
          </div>
        </div>

        {/* Temperature */}
        <div style={{ marginBottom: '28px' }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '10px',
          }}>
            <label style={{ 
              color: '#cbd5e1', 
              fontSize: '14px', 
              fontWeight: '600',
            }}>
              🌡️ Yaratıcılık (Temperature)
            </label>
            <span style={{ 
              color: '#a78bfa', 
              fontSize: '14px',
              fontWeight: '700',
              background: '#4c1d95',
              padding: '4px 12px',
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
              height: '8px',
              borderRadius: '4px',
              outline: 'none',
            }}
          />
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            color: '#64748b', 
            fontSize: '12px', 
            marginTop: '8px',
          }}>
            <span>🎯 Tutarlı</span>
            <span>🎨 Yaratıcı</span>
          </div>
        </div>

        {/* Max Tokens */}
        <div style={{ marginBottom: '28px' }}>
          <label style={{ 
            color: '#cbd5e1', 
            fontSize: '14px', 
            fontWeight: '600',
            display: 'block', 
            marginBottom: '10px',
          }}>
            📏 Maksimum Cevap Uzunluğu
          </label>
          <select
            value={localSettings.maxTokens}
            onChange={(e) => setLocalSettings({ ...localSettings, maxTokens: parseInt(e.target.value) })}
            style={{
              width: '100%',
              padding: '12px 16px',
              borderRadius: '10px',
              border: '1px solid #374151',
              background: '#0f172a',
              color: '#e5e7eb',
              fontSize: '15px',
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            <option value="512">Kısa (512 token)</option>
            <option value="1024">Orta (1024 token)</option>
            <option value="2048">Uzun (2048 token)</option>
            <option value="4096">Çok Uzun (4096 token)</option>
          </select>
        </div>

        {/* Web Search */}
        <div style={{ marginBottom: '28px' }}>
          <label style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            cursor: 'pointer',
            color: '#cbd5e1',
            fontSize: '15px',
            fontWeight: '600',
            padding: '12px 16px',
            borderRadius: '10px',
            background: '#1e293b',
            border: '1px solid #334155',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = '#334155'}
          onMouseLeave={(e) => e.currentTarget.style.background = '#1e293b'}
          >
            <input
              type="checkbox"
              checked={localSettings.useWebSearch}
              onChange={(e) => setLocalSettings({ ...localSettings, useWebSearch: e.target.checked })}
              style={{ 
                width: '20px', 
                height: '20px',
                cursor: 'pointer',
              }}
            />
            🌐 Web Araması Kullan
          </label>
        </div>

        {/* Max Sources */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '10px',
          }}>
            <label style={{ 
              color: '#cbd5e1', 
              fontSize: '14px', 
              fontWeight: '600',
            }}>
              📚 Maksimum Kaynak Sayısı
            </label>
            <span style={{ 
              color: '#34d399', 
              fontSize: '14px',
              fontWeight: '700',
              background: '#064e3b',
              padding: '4px 12px',
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
              height: '8px',
              borderRadius: '4px',
              outline: 'none',
            }}
          />
        </div>

        {/* Save Button */}
        <button
          onClick={handleSave}
          style={{
            width: '100%',
            padding: '14px',
            borderRadius: '10px',
            border: 'none',
            background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
            color: '#ffffff',
            fontSize: '16px',
            fontWeight: '700',
            cursor: 'pointer',
            transition: 'all 0.2s',
            boxShadow: '0 4px 6px -1px rgba(37, 99, 235, 0.3)',
          }}
          onMouseEnter={(e) => e.target.style.transform = 'translateY(-2px)'}
          onMouseLeave={(e) => e.target.style.transform = 'translateY(0)'}
        >
          ✅ Kaydet
        </button>
      </div>
    </div>
  );
};

export default SettingsPanel;