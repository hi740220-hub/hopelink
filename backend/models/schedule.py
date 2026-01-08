"""
케어 플랜 / 일정 모델
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChecklistItem(BaseModel):
    item: str
    checked: bool = False


class ScheduleBase(BaseModel):
    title: str
    schedule_type: str  # 'hospital', 'rehabilitation', 'therapy', 'checkup'
    start_time: datetime
    end_time: datetime
    is_all_day: bool = False
    location_name: Optional[str] = None
    location_address: Optional[str] = None
    department: Optional[str] = None
    doctor_name: Optional[str] = None
    checklist: Optional[List[ChecklistItem]] = []
    reminder_minutes: Optional[List[int]] = [1440, 60]  # 1일 전, 1시간 전
    notes: Optional[str] = None


class ScheduleCreate(ScheduleBase):
    child_id: str


class ScheduleUpdate(BaseModel):
    title: Optional[str] = None
    schedule_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location_name: Optional[str] = None
    location_address: Optional[str] = None
    department: Optional[str] = None
    doctor_name: Optional[str] = None
    checklist: Optional[List[ChecklistItem]] = None
    notes: Optional[str] = None


class Schedule(ScheduleBase):
    id: str
    child_id: str
    user_id: str
    google_event_id: Optional[str] = None
    is_synced: bool = False
    has_conflict: bool = False
    conflict_with: Optional[List[str]] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ScheduleConflictInfo(BaseModel):
    schedule_id: str
    title: str
    overlap_minutes: int
    conflict_type: str  # 'full_overlap', 'partial_overlap', 'contains'


class ScheduleListResponse(BaseModel):
    items: List[Schedule]
    conflicts: List[ScheduleConflictInfo]
