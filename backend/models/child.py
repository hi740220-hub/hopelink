"""
환아 정보 모델
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class ChildBase(BaseModel):
    name: str
    birth_date: date
    disease_code: str  # ICD-10 코드
    disease_name: Optional[str] = None
    symptoms: Optional[List[str]] = []
    current_hospital: Optional[str] = None
    attending_doctor: Optional[str] = None
    notes: Optional[str] = None


class ChildCreate(ChildBase):
    pass


class ChildUpdate(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[date] = None
    disease_code: Optional[str] = None
    disease_name: Optional[str] = None
    symptoms: Optional[List[str]] = None
    current_hospital: Optional[str] = None
    attending_doctor: Optional[str] = None
    notes: Optional[str] = None


class Child(ChildBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    # 계산된 필드
    age_months: Optional[int] = None
    
    class Config:
        from_attributes = True
