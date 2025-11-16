/**
 * useChat.js - UPDATED WITH PROCESSING TIME
 * ------------------------------------------
 * ✅ Processing time tracking
 * ✅ Model info
 * ✅ Better error handling
 */

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const useChat = (initialSessionId = null) => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(initialSessionId || `session_${Date.now()}`);
  const [lastSources, setLastSources] = useState([]);

  // Load messages on session change
  useEffect(() => {
    loadSessionMessages(sessionId);
  }, [sessionId]);

  const loadSessionMessages = useCallback((sid) => {
    try {
      const stored = localStorage.getItem(`chat_messages_${sid}`);
      if (stored) {
        setMessages(JSON.parse(stored));
      } else {
        setMessages([]);
      }
    } catch (err) {
      console.error('Message load error:', err);
      setMessages([]);
    }
  }, []);

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

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    saveSessionMessages(sessionId, updatedMessages);

    setIsLoading(true);
    setError(null);

    try {
      // Track request time
      const startTime = Date.now();

      const response = await axios.post(`${API_URL}/chat`, {
        message: text,
        mode: settings.mode || 'normal',
        use_web_search: settings.useWebSearch || false,
        max_sources: settings.maxSources || 5,
        temperature: settings.temperature || 0.7,
        max_tokens: settings.maxTokens || 2048,
        safety_level: settings.safetyLevel || 0,
        user_id: 'default',
        session_id: sessionId,
        conversation_history: updatedMessages.slice(-6), // Last 6 messages
      });

      const endTime = Date.now();
      const clientTime = (endTime - startTime) / 1000; // seconds

      // Assistant message
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString(),
        model: response.data.model_used,
        processingTime: response.data.processing_time || clientTime,
        qualityScore: response.data.quality_score,
        intent: response.data.intent,
        sources: response.data.sources,
      };

      const finalMessages = [...updatedMessages, assistantMessage];
      setMessages(finalMessages);
      saveSessionMessages(sessionId, finalMessages);

      // Update sources
      if (response.data.sources) {
        setLastSources(response.data.sources);
      }

    } catch (err) {
      console.error('Chat error:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Bilinmeyen hata';
      setError(errorMsg);

      // Error message
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