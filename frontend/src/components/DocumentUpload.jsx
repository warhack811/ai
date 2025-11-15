/**
 * DocumentUpload.jsx - FAS 3
 * --------------------------
 * ✅ PDF & TXT upload
 * ✅ Drag & drop support
 * ✅ Progress indicator
 * ✅ Document list
 * ✅ Delete functionality
 * 
 * Kullanım:
 * <DocumentUpload 
 *   isOpen={showUpload}
 *   onClose={() => setShowUpload(false)}
 *   onUploadSuccess={(data) => console.log('Uploaded:', data)}
 * />
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

const DocumentUpload = ({ isOpen, onClose, onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  // Dokümanları yükle
  useEffect(() => {
    if (isOpen) {
      loadDocuments();
    }
  }, [isOpen]);

  const loadDocuments = async () => {
    setLoadingDocs(true);
    try {
      const response = await axios.get('http://localhost:8000/api/documents');
      setDocuments(response.data.documents || []);
    } catch (err) {
      console.error('Documents load error:', err);
    } finally {
      setLoadingDocs(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    validateAndSetFile(selectedFile);
  };

  const validateAndSetFile = (selectedFile) => {
    if (!selectedFile) return;

    // Sadece txt ve pdf
    if (!selectedFile.name.match(/\.(txt|pdf)$/i)) {
      setError('Sadece .txt ve .pdf dosyaları desteklenir');
      return;
    }

    // Max 10MB
    if (selectedFile.size > 10 * 1024 * 1024) {
      setError('Dosya boyutu maksimum 10MB olabilir');
      return;
    }

    setFile(selectedFile);
    setError('');
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
  if (!file) return;

  setUploading(true);
  setError('');

  try {
    const reader = new FileReader();
    
    reader.onload = async (e) => {
      let content = e.target.result;
      
      // PDF ise base64'e çevir
      const isPDF = file.name.toLowerCase().endsWith('.pdf');
      
      if (isPDF) {
        // ArrayBuffer'ı base64'e çevir
        const base64 = btoa(
          new Uint8Array(content)
            .reduce((data, byte) => data + String.fromCharCode(byte), '')
        );
        content = base64;
      }

      // Send to backend
      const response = await axios.post('http://localhost:8000/api/upload-document', {
        content: content,
        filename: file.name,
        user_id: 'default',
        metadata: {
          size: file.size,
          type: file.type || (isPDF ? 'application/pdf' : 'text/plain'),
        }
      });

      if (response.data.status === 'success') {
        onUploadSuccess(response.data);
        setFile(null);
        loadDocuments();
      } else {
        setError(response.data.error || 'Upload failed');
      }
    };

    reader.onerror = () => {
      setError('Dosya okunamadı');
    };

    // PDF için ArrayBuffer, TXT için text
    if (file.name.toLowerCase().endsWith('.pdf')) {
      reader.readAsArrayBuffer(file);
    } else {
      reader.readAsText(file);
    }
    
  } catch (err) {
    console.error('Upload error:', err);
    setError(err.response?.data?.detail || 'Yükleme hatası');
  } finally {
    setUploading(false);
  }
};

  const handleDelete = async (docId) => {
    if (!confirm('Bu dokümanı silmek istediğinize emin misiniz?')) return;

    try {
      await axios.delete(`http://localhost:8000/api/documents/${docId}`);
      loadDocuments(); // Listeyi yenile
    } catch (err) {
      console.error('Delete error:', err);
      alert('Silme hatası: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (!isOpen) return null;

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
        maxWidth: '700px',
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
          marginBottom: '24px',
        }}>
          <h2 style={{ 
            margin: 0, 
            color: '#f1f5f9',
            fontSize: '24px',
            fontWeight: '700',
          }}>
            📄 Doküman Yükle
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

        {/* Upload Area */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          style={{
            border: dragActive ? '2px dashed #3b82f6' : '2px dashed #475569',
            borderRadius: '12px',
            padding: '32px',
            textAlign: 'center',
            cursor: 'pointer',
            background: dragActive ? '#1e3a8a' : '#0f172a',
            marginBottom: '24px',
            transition: 'all 0.3s',
          }}
        >
          <input
            type="file"
            accept=".txt,.pdf"
            onChange={handleFileChange}
            style={{ display: 'none' }}
            id="file-input"
          />
          <label htmlFor="file-input" style={{ cursor: 'pointer' }}>
            <div style={{ color: '#94a3b8', marginBottom: '12px', fontSize: '48px' }}>
              📁
            </div>
            <div style={{ color: '#cbd5e1', fontSize: '16px', marginBottom: '8px', fontWeight: '600' }}>
              Dosya seç veya sürükle
            </div>
            <div style={{ color: '#64748b', fontSize: '13px' }}>
              .txt veya .pdf (maksimum 10MB)
            </div>
          </label>
        </div>

        {/* Selected File */}
        {file && (
          <div style={{
            marginBottom: '20px',
            padding: '16px',
            background: '#1e293b',
            borderRadius: '10px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            border: '1px solid #334155',
          }}>
            <div style={{ flex: 1 }}>
              <div style={{ color: '#cbd5e1', fontSize: '15px', fontWeight: '600', marginBottom: '4px' }}>
                {file.name}
              </div>
              <div style={{ color: '#64748b', fontSize: '13px' }}>
                {(file.size / 1024).toFixed(1)} KB
              </div>
            </div>
            <button
              onClick={() => setFile(null)}
              style={{
                background: '#7f1d1d',
                border: 'none',
                color: '#fca5a5',
                padding: '8px 16px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => e.target.style.background = '#991b1b'}
              onMouseLeave={(e) => e.target.style.background = '#7f1d1d'}
            >
              ✕ Kaldır
            </button>
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{ 
            color: '#fca5a5', 
            background: '#7f1d1d',
            padding: '12px 16px',
            borderRadius: '8px',
            fontSize: '14px', 
            marginBottom: '16px',
            border: '1px solid #991b1b',
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* Upload Button */}
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          style={{
            width: '100%',
            padding: '14px',
            borderRadius: '10px',
            border: 'none',
            background: uploading || !file 
              ? '#475569' 
              : 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            color: '#ffffff',
            cursor: uploading || !file ? 'not-allowed' : 'pointer',
            fontWeight: '700',
            fontSize: '16px',
            marginBottom: '32px',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            if (!uploading && file) {
              e.target.style.transform = 'translateY(-2px)';
            }
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'translateY(0)';
          }}
        >
          {uploading ? '⏳ Yükleniyor...' : '📤 Yükle ve Öğret'}
        </button>

        {/* Documents List */}
        <div>
          <h3 style={{ 
            color: '#cbd5e1', 
            fontSize: '16px', 
            fontWeight: '700',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}>
            📚 Yüklenmiş Dokümanlar
            {loadingDocs && <span style={{ fontSize: '14px', color: '#64748b' }}>⏳</span>}
          </h3>
          
          <div style={{ maxHeight: '300px', overflow: 'auto' }}>
            {documents.length === 0 ? (
              <div style={{ 
                color: '#64748b', 
                fontSize: '14px', 
                textAlign: 'center',
                padding: '24px',
                background: '#0f172a',
                borderRadius: '8px',
                border: '1px dashed #334155',
              }}>
                Henüz doküman yüklenmemiş
              </div>
            ) : (
              documents.map((doc) => (
                <div key={doc.doc_id} style={{
                  padding: '16px',
                  background: '#1e293b',
                  borderRadius: '10px',
                  marginBottom: '12px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  border: '1px solid #334155',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#334155'}
                onMouseLeave={(e) => e.currentTarget.style.background = '#1e293b'}
                >
                  <div style={{ flex: 1 }}>
                    <div style={{ 
                      color: '#cbd5e1', 
                      fontSize: '14px', 
                      fontWeight: '600',
                      marginBottom: '4px',
                    }}>
                      📄 {doc.filename}
                    </div>
                    <div style={{ color: '#64748b', fontSize: '12px' }}>
                      {doc.total_chunks} parça • {doc.type}
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(doc.doc_id)}
                    style={{
                      background: '#7f1d1d',
                      border: 'none',
                      color: '#fca5a5',
                      padding: '6px 12px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: '600',
                      transition: 'all 0.2s',
                    }}
                    onMouseEnter={(e) => e.target.style.background = '#991b1b'}
                    onMouseLeave={(e) => e.target.style.background = '#7f1d1d'}
                  >
                    🗑️ Sil
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;