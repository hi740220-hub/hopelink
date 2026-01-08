"""
AI 챗봇 모델
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    content: str
    chat_type: Optional[str] = "general"  # 'general', 'record', 'emotion', 'welfare', 'medicine'
    attachments: Optional[List[str]] = []  # 이미지 URL 등


class ChatResponse(BaseModel):
    message: str
    intent: Optional[str] = None  # 감지된 의도
    confidence: Optional[float] = None
    suggestions: Optional[List[str]] = []  # 추천 후속 질문
    references: Optional[List[dict]] = []  # 참고 자료


class ChatHistory(BaseModel):
    id: str
    user_id: str
    session_id: str
    role: str  # 'user', 'assistant'
    content: str
    attachments: Optional[List[dict]] = None
    intent: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
