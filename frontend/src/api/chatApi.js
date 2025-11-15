// src/api/chatApi.js (veya .jsx)

import { apiClient } from '../utils/api';

export async function sendChatMessage({
  message,
  mode = 'normal',
  useWebSearch = true,
  maxSources = 5,
  temperature = 0.5,
  maxTokens = 1500,
  userId,
  sessionId,
}) {
  const payload = {
    message,
    mode,
    use_web_search: useWebSearch,
    max_sources: maxSources,
    temperature,
    max_tokens: maxTokens,
    user_id: userId ?? 'frontend_user',
    session_id: sessionId ?? null,
  };

  // BURASI ÖNEMLİ: 'chat' olacak
  const { data } = await apiClient.post('chat', payload);
  return data; // ChatResponse
}
