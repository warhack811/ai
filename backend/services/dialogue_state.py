"""
services/dialogue_state.py
--------------------------
Sohbetin durumunu (dialogue state) yöneten modül.

Amaç:
- intent + mood + profile + son mesajlara göre bir "state" üretmek
- LLM’e hangi yaklaşımın kullanılacağını belirlemek
- (örn: emotional_support / code_help / research / casual_chat)

State Machine:
  - greeting
  - general_chat
  - emotional_support
  - code_help
  - research
  - document_question
  - reminder
  - profile_related
  - unknown

Bu state, pipeline içinde LLM mode & prompt seçimini etkiler.

"""

from __future__ import annotations

from typing import Optional

from schemas.common import (
    IntentLabel,
    SentimentLabel,
    EmotionLabel,
    ChatMode,
)
from schemas.profile import UserProfile


class DialogueState:
    """
    Sohbetin anlık durumunu temsil eder.
    """

    def __init__(
        self,
        intent: IntentLabel,
        sentiment: SentimentLabel,
        emotion: EmotionLabel,
        mode: ChatMode,
        profile: Optional[UserProfile] = None,
    ):
        self.intent = intent
        self.sentiment = sentiment
        self.emotion = emotion
        self.mode = mode
        self.profile = profile

    @property
    def state_name(self) -> str:
        """
        Daha okunabilir sohbet durumu ismi.
        """
        if self.intent == IntentLabel.REMINDER_CREATE:
            return "reminder"

        if self.intent == IntentLabel.DOCUMENT_QUESTION:
            return "document_question"

        if self.intent == IntentLabel.CODE_HELP:
            return "code_help"

        if self.intent == IntentLabel.PROFILE_UPDATE:
            return "profile_related"

        if self.intent == IntentLabel.SUMMARIZE:
            return "summarization"

        if self.intent == IntentLabel.TRANSLATE:
            return "translation"

        if self.intent == IntentLabel.EXPLAIN:
            return "explanation"

        if self.intent == IntentLabel.RESEARCH:
            return "research"

        # Duygusal destek
        if self.emotion in (
            EmotionLabel.SAD,
            EmotionLabel.ANXIOUS,
            EmotionLabel.ANGRY,
            EmotionLabel.LONELY,
        ):
            return "emotional_support"

        if self.intent == IntentLabel.SMALL_TALK:
            return "casual_chat"

        return "general_chat"

    @property
    def is_emotional(self) -> bool:
        return self.state_name == "emotional_support"

    @property
    def requires_extended_context(self) -> bool:
        """
        Araştırma, kod ve doküman soruları daha fazla bağlam ister.
        """
        return self.state_name in (
            "research",
            "code_help",
            "document_question",
        )

    @property
    def recommended_llm(self) -> str:
        """
        Hangi modeli kullanmamız gerektiğine karar verir.
        """
        if self.state_name == "code_help":
            return "mistral"

        if self.state_name == "research":
            return "qwen"

        if self.state_name == "emotional_support":
            return "qwen"

        if self.state_name == "document_question":
            return "qwen"

        # Genel kullanım
        return "qwen"

    def to_dict(self):
        return {
            "intent": self.intent.value,
            "sentiment": self.sentiment.value,
            "emotion": self.emotion.value,
            "mode": self.mode.value,
            "profile_name": self.profile.display_name if self.profile else None,
            "state_name": self.state_name,
            "recommended_llm": self.recommended_llm,
        }


def determine_dialogue_state(
    *,
    intent: IntentLabel,
    sentiment: SentimentLabel,
    emotion: EmotionLabel,
    mode: ChatMode,
    profile: Optional[UserProfile],
) -> DialogueState:
    """
    Ana giriş fonksiyonu: tüm işleyiciler bunu kullanır.
    """
    return DialogueState(
        intent=intent,
        sentiment=sentiment,
        emotion=emotion,
        mode=mode,
        profile=profile,
    )
