"""
관찰 일기 모델
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class DiaryBase(BaseModel):
    recorded_at: datetime
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    symptom_tags: Optional[List[str]] = []
    notes: Optional[str] = None
    condition: Optional[str] = None  # 'great', 'good', 'normal', 'bad', 'critical'


class DiaryCreate(DiaryBase):
    child_id: str


class DiaryUpdate(BaseModel):
    symptom_tags: Optional[List[str]] = None
    notes: Optional[str] = None
    condition: Optional[str] = None


class DiaryAIAnalysis(BaseModel):
    spasm_count: int = 0
    occurrence_times: List[datetime] = []
    patterns: Optional[str] = None
    severity: Optional[str] = None  # 'low', 'medium', 'high'
    recommendations: Optional[List[str]] = []


class Diary(DiaryBase):
    id: str
    child_id: str
    user_id: str
    ai_analysis: Optional[DiaryAIAnalysis] = None
    spasm_count: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DiaryListResponse(BaseModel):
    items: List[Diary]
    total: int
    page: int
    page_size: int
