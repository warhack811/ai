/**
 * useChat.js - FAS 3 UPDATED
 * ---------------------------
 * ✅ Session persistence (localStorage)
 * ✅ Message history restoration
 * ✅ Settings integration
 * ✅ Better error handling
 */

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

export const useChat = (initialSessionId = null) => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(initialSessionId || `session_${Date.now()}`);
  const [lastSources, setLastSources] = useState([]);

  // Session değiştiğinde mesajları yükle
  useEffect(() => {
    loadSessionMessages(sessionId);
  }, [sessionId]);

  // LocalStorage'dan session mesajlarını yükle
  const loadSessionMessages = useCallback((sid) => {
    try {
      const stored = localStorage.getItem(`chat_messages_${sid}`);
      if (stored) {
        const parsed = JSON.parse(stored);
        setMessages(parsed);
      } else {
        setMessages([]);
      }
    } catch (err) {
      console.error('Message load error:', err);
      setMessages([]);
    }
  }, []);

  // Mesajları localStorage'a kaydet
  const saveSessionMessages = useCallback((sid, msgs) => {
    try {
      localStorage.setItem(`chat_messages_${sid}`, JSON.stringify(msgs));
    } catch (err) {
      console.error('Message save error:', err);
    }
  }, []);

  const sendMessage = async (text, settings = {}) => {
    if (!text.trim()) return;

    // User message
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    // Mesajları güncelle
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    saveSessionMessages(sessionId, updatedMessages);

    // Session'ı güncelle (SessionManager için)
    if (window.saveCurrentSession) {
      window.saveCurrentSession(sessionId, text);
    }

    setIsLoading(true);
    setError(null);

    try {
      // API request
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        message: text,
        mode: settings.mode || 'normal',
        use_web_search: settings.useWebSearch !== undefined ? settings.useWebSearch : true,
        max_sources: settings.maxSources || 5,
        temperature: settings.temperature || 0.7,
        max_tokens: settings.maxTokens || 2048,
        safety_level: settings.safetyLevel || 0,
        user_id: 'default',
        session_id: sessionId,
      });

      // Assistant message
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString(),
        model: response.data.used_model,
        sources: response.data.sources,
      };

      // Mesajları güncelle
      const finalMessages = [...updatedMessages, assistantMessage];
      setMessages(finalMessages);
      saveSessionMessages(sessionId, finalMessages);

      // Sources'ı kaydet
      if (response.data.sources) {
        setLastSources(response.data.sources);
      }

      // Session'ı güncelle
      if (window.saveCurrentSession) {
        window.saveCurrentSession(sessionId);
      }

    } catch (err) {
      console.error('Chat error:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Bir hata oluştu';
      setError(errorMsg);

      // Error message ekle
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `❌ Hata: ${errorMsg}`,
        timestamp: new Date().toISOString(),
        isError: true,
      };

      const finalMessages = [...updatedMessages, errorMessage];
      setMessages(finalMessages);
      saveSessionMessages(sessionId, finalMessages);
    } finally {
      setIsLoading(false);
    }
  };

  const clearMessages = useCallback(() => {
    setMessages([]);
    setLastSources([]);
    saveSessionMessages(sessionId, []);
  }, [sessionId, saveSessionMessages]);

  const changeSession = useCallback((newSessionId) => {
    setSessionId(newSessionId);
    setLastSources([]);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sessionId,
    lastSources,
    sendMessage,
    clearMessages,
    changeSession,
  };
};