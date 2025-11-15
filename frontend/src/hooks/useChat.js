// src/hooks/useChat.js

import { useState, useCallback } from 'react';
import { sendChatMessage } from '../api/chatApi';

export function useChat() {
  const [messages, setMessages] = useState([]); // {id, role, content, sources?}
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastSources, setLastSources] = useState([]);
  const [error, setError] = useState(null);

  const sendMessage = useCallback(
    async (text, options = {}) => {
      if (!text?.trim()) return;
      setError(null);

      // UI'ya anında user mesajını ekle
      const userMessage = {
        id: Date.now(),
        role: 'user',
        content: text,
      };
      setMessages((prev) => [...prev, userMessage]);

      setIsLoading(true);
      try {
        const response = await sendChatMessage({
          message: text,
          mode: options.mode || 'normal',
          useWebSearch: options.useWebSearch ?? true,
          maxSources: options.maxSources ?? 5,
          temperature: options.temperature ?? 0.5,
          maxTokens: options.maxTokens ?? 512,
          userId: options.userId || 'frontend_user',
          sessionId,
        });

        // Backend yeni session_id üretebilir → state'i güncelle
        if (response.session_id && response.session_id !== sessionId) {
          setSessionId(response.session_id);
        }

        const assistantMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: response.response,
          sources: response.sources || [],
          raw: response,
        };

        setMessages((prev) => [...prev, assistantMessage]);
        setLastSources(response.sources || []);
      } catch (err) {
        console.error(err);
        setError(err?.response?.data?.detail || 'Bir hata oluştu.');
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId]
  );

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    lastSources,
    sessionId,
  };
}
