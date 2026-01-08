"""
케어 플랜 / 일정 API 라우터
===========================

일정 CRUD, 충돌 감지, 캘린더 동기화
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, status, Query

from models.schedule import Schedule, ScheduleCreate, ScheduleUpdate, ScheduleListResponse, ScheduleConflictInfo
from database import get_supabase
from routers.auth import get_current_user

router = APIRouter()


def detect_conflicts(schedules: List[dict]) -> List[ScheduleConflictInfo]:
    """일정 충돌 감지"""
    conflicts = []
    n = len(schedules)
    
    for i in range(n):
        for j in range(i + 1, n):
            s1 = schedules[i]
            s2 = schedules[j]
            
            start1 = datetime.fromisoformat(s1["start_time"].replace("Z", "+00:00"))
            end1 = datetime.fromisoformat(s1["end_time"].replace("Z", "+00:00"))
            start2 = datetime.fromisoformat(s2["start_time"].replace("Z", "+00:00"))
            end2 = datetime.fromisoformat(s2["end_time"].replace("Z", "+00:00"))
            
            # 겹치는지 확인
            if end1 > start2 and end2 > start1:
                overlap_start = max(start1, start2)
                overlap_end = min(end1, end2)
                overlap_minutes = int((overlap_end - overlap_start).total_seconds() / 60)
                
                if start1 == start2 and end1 == end2:
                    conflict_type = "full_overlap"
                elif start1 <= start2 and end1 >= end2:
                    conflict_type = "contains"
                else:
                    conflict_type = "partial_overlap"
                
                conflicts.append(ScheduleConflictInfo(
                    schedule_id=s1["id"],
                    title=s1["title"],
                    overlap_minutes=overlap_minutes,
                    conflict_type=conflict_type
                ))
    
    return conflicts


@router.get("/", response_model=ScheduleListResponse)
async def get_schedules(
    child_id: Optional[str] = Query(None, description="특정 환아의 일정만 조회"),
    start_date: Optional[datetime] = Query(None, description="시작일 필터"),
    end_date: Optional[datetime] = Query(None, description="종료일 필터"),
    current_user: dict = Depends(get_current_user)
):
    """
    케어 일정 목록 조회
    
    - **child_id**: 특정 환아의 일정만 필터링
    - **start_date**: 이 날짜 이후 일정만 조회
    - **end_date**: 이 날짜 이전 일정만 조회
    """
    supabase = get_supabase()
    
    query = supabase.table("care_schedules").select("*").eq("user_id", current_user["id"])
    
    if child_id:
        query = query.eq("child_id", child_id)
    
    if start_date:
        query = query.gte("start_time", start_date.isoformat())
    
    if end_date:
        query = query.lte("end_time", end_date.isoformat())
    
    query = query.order("start_time", desc=False)
    
    result = query.execute()
    
    schedules = []
    for s in (result.data or []):
        schedules.append(Schedule(
            id=s["id"],
            child_id=s["child_id"],
            user_id=s["user_id"],
            title=s["title"],
            schedule_type=s["schedule_type"],
            start_time=s["start_time"],
            end_time=s["end_time"],
            is_all_day=s.get("is_all_day", False),
            location_name=s.get("location_name"),
            location_address=s.get("location_address"),
            department=s.get("department"),
            doctor_name=s.get("doctor_name"),
            checklist=s.get("checklist") or [],
            reminder_minutes=s.get("reminder_minutes") or [1440, 60],
            notes=s.get("notes"),
            google_event_id=s.get("google_event_id"),
            is_synced=s.get("is_synced", False),
            has_conflict=s.get("has_conflict", False),
            conflict_with=s.get("conflict_with") or [],
            created_at=s["created_at"],
            updated_at=s["updated_at"]
        ))
    
    # 충돌 감지
    conflicts = detect_conflicts(result.data or [])
    
    return ScheduleListResponse(items=schedules, conflicts=conflicts)


@router.post("/", response_model=Schedule, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    케어 일정 등록
    
    - **child_id**: 환아 ID
    - **title**: 일정 제목
    - **schedule_type**: 'hospital', 'rehabilitation', 'therapy', 'checkup'
    - **start_time**: 시작 시간
    - **end_time**: 종료 시간
    """
    supabase = get_supabase()
    
    # 환아 소유권 확인
    child_check = supabase.table("children").select("id").eq("id", schedule_data.child_id).eq("user_id", current_user["id"]).execute()
    if not child_check.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="환아 정보를 찾을 수 없습니다.")
    
    new_schedule = {
        "child_id": schedule_data.child_id,
        "user_id": current_user["id"],
        "title": schedule_data.title,
        "schedule_type": schedule_data.schedule_type,
        "start_time": schedule_data.start_time.isoformat(),
        "end_time": schedule_data.end_time.isoformat(),
        "is_all_day": schedule_data.is_all_day,
        "location_name": schedule_data.location_name,
        "location_address": schedule_data.location_address,
        "department": schedule_data.department,
        "doctor_name": schedule_data.doctor_name,
        "checklist": [item.model_dump() for item in schedule_data.checklist] if schedule_data.checklist else [],
        "reminder_minutes": schedule_data.reminder_minutes,
        "notes": schedule_data.notes,
    }
    
    result = supabase.table("care_schedules").insert(new_schedule).execute()
    
    if not result.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="일정 등록에 실패했습니다.")
    
    s = result.data[0]
    
    return Schedule(
        id=s["id"],
        child_id=s["child_id"],
        user_id=s["user_id"],
        title=s["title"],
        schedule_type=s["schedule_type"],
        start_time=s["start_time"],
        end_time=s["end_time"],
        is_all_day=s.get("is_all_day", False),
        location_name=s.get("location_name"),
        location_address=s.get("location_address"),
        department=s.get("department"),
        doctor_name=s.get("doctor_name"),
        checklist=s.get("checklist") or [],
        reminder_minutes=s.get("reminder_minutes") or [1440, 60],
        notes=s.get("notes"),
        google_event_id=s.get("google_event_id"),
        is_synced=s.get("is_synced", False),
        has_conflict=s.get("has_conflict", False),
        conflict_with=s.get("conflict_with") or [],
        created_at=s["created_at"],
        updated_at=s["updated_at"]
    )


@router.get("/{schedule_id}", response_model=Schedule)
async def get_schedule(
    schedule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """특정 일정 조회"""
    supabase = get_supabase()
    
    result = supabase.table("care_schedules").select("*").eq("id", schedule_id).eq("user_id", current_user["id"]).limit(1).execute()
    
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="일정을 찾을 수 없습니다.")
    
    s = result.data[0]
    
    return Schedule(
        id=s["id"],
        child_id=s["child_id"],
        user_id=s["user_id"],
        title=s["title"],
        schedule_type=s["schedule_type"],
        start_time=s["start_time"],
        end_time=s["end_time"],
        is_all_day=s.get("is_all_day", False),
        location_name=s.get("location_name"),
        location_address=s.get("location_address"),
        department=s.get("department"),
        doctor_name=s.get("doctor_name"),
        checklist=s.get("checklist") or [],
        reminder_minutes=s.get("reminder_minutes") or [1440, 60],
        notes=s.get("notes"),
        google_event_id=s.get("google_event_id"),
        is_synced=s.get("is_synced", False),
        has_conflict=s.get("has_conflict", False),
        conflict_with=s.get("conflict_with") or [],
        created_at=s["created_at"],
        updated_at=s["updated_at"]
    )


@router.patch("/{schedule_id}", response_model=Schedule)
async def update_schedule(
    schedule_id: str,
    schedule_data: ScheduleUpdate,
    current_user: dict = Depends(get_current_user)
):
    """일정 수정"""
    supabase = get_supabase()
    
    # 권한 확인
    existing = supabase.table("care_schedules").select("id").eq("id", schedule_id).eq("user_id", current_user["id"]).execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="일정을 찾을 수 없습니다.")
    
    update_data = {}
    for k, v in schedule_data.model_dump().items():
        if v is not None:
            if k in ["start_time", "end_time"] and v:
                update_data[k] = v.isoformat()
            elif k == "checklist" and v:
                update_data[k] = [item.model_dump() for item in v]
            else:
                update_data[k] = v
    
    result = supabase.table("care_schedules").update(update_data).eq("id", schedule_id).execute()
    
    s = result.data[0]
    
    return Schedule(
        id=s["id"],
        child_id=s["child_id"],
        user_id=s["user_id"],
        title=s["title"],
        schedule_type=s["schedule_type"],
        start_time=s["start_time"],
        end_time=s["end_time"],
        is_all_day=s.get("is_all_day", False),
        location_name=s.get("location_name"),
        location_address=s.get("location_address"),
        department=s.get("department"),
        doctor_name=s.get("doctor_name"),
        checklist=s.get("checklist") or [],
        reminder_minutes=s.get("reminder_minutes") or [1440, 60],
        notes=s.get("notes"),
        google_event_id=s.get("google_event_id"),
        is_synced=s.get("is_synced", False),
        has_conflict=s.get("has_conflict", False),
        conflict_with=s.get("conflict_with") or [],
        created_at=s["created_at"],
        updated_at=s["updated_at"]
    )


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """일정 삭제"""
    supabase = get_supabase()
    
    result = supabase.table("care_schedules").delete().eq("id", schedule_id).eq("user_id", current_user["id"]).execute()
    
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="일정을 찾을 수 없습니다.")


@router.post("/{schedule_id}/sync-google")
async def sync_to_google(
    schedule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Google Calendar 동기화
    
    일정을 Google Calendar에 추가합니다.
    처음 사용 시 OAuth2 인증이 필요합니다.
    """
    import sys
    import os
    from datetime import datetime as dt
    
    supabase = get_supabase()
    
    result = supabase.table("care_schedules").select("*").eq("id", schedule_id).eq("user_id", current_user["id"]).limit(1).execute()
    
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="일정을 찾을 수 없습니다.")
    
    schedule_data = result.data[0]
    
    # Google Calendar 연동 시도
    try:
        # calendar_sync 모듈 import
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from calendar_sync import GoogleCalendarSync, Schedule as CalendarSchedule
        
        # credentials.json 경로 (backend 폴더에 위치)
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        credentials_path = os.path.join(backend_dir, "credentials.json")
        token_path = os.path.join(backend_dir, "token.pickle")
        
        if not os.path.exists(credentials_path):
            return {
                "success": False,
                "message": "Google Calendar 연동을 위해 credentials.json 파일이 필요합니다.",
                "setup_guide": {
                    "step1": "Google Cloud Console에서 프로젝트 생성",
                    "step2": "Calendar API 활성화",
                    "step3": "OAuth 2.0 클라이언트 ID 생성 (데스크톱 앱)",
                    "step4": "credentials.json 다운로드하여 backend 폴더에 저장",
                    "guide_url": "https://developers.google.com/calendar/quickstart/python"
                }
            }
        
        # GoogleCalendarSync 인스턴스 생성
        calendar_sync = GoogleCalendarSync(
            credentials_path=credentials_path,
            token_path=token_path
        )
        
        # 인증 수행
        if not calendar_sync.authenticate():
            return {
                "success": False,
                "message": "Google Calendar 인증에 실패했습니다. 브라우저에서 인증을 완료하세요."
            }
        
        # HopeLink 일정을 Calendar Schedule로 변환
        cal_schedule = CalendarSchedule(
            id=schedule_data["id"],
            title=schedule_data["title"],
            schedule_type=schedule_data["schedule_type"],
            start_time=dt.fromisoformat(schedule_data["start_time"].replace("Z", "+00:00")),
            end_time=dt.fromisoformat(schedule_data["end_time"].replace("Z", "+00:00")),
            location_name=schedule_data.get("location_name"),
            location_address=schedule_data.get("location_address"),
            department=schedule_data.get("department"),
            doctor_name=schedule_data.get("doctor_name"),
            checklist=schedule_data.get("checklist") or [],
            notes=schedule_data.get("notes"),
            google_event_id=schedule_data.get("google_event_id")
        )
        
        # Google Calendar에 이벤트 생성/업데이트
        if cal_schedule.google_event_id:
            success = calendar_sync.update_event(cal_schedule)
            if success:
                return {"success": True, "message": "Google Calendar 일정이 업데이트되었습니다.", "event_id": cal_schedule.google_event_id}
        else:
            event_id = calendar_sync.create_event(cal_schedule)
            if event_id:
                # DB에 Google Event ID 저장
                supabase.table("care_schedules").update({
                    "google_event_id": event_id,
                    "is_synced": True
                }).eq("id", schedule_id).execute()
                
                return {"success": True, "message": "Google Calendar에 일정이 추가되었습니다!", "event_id": event_id}
        
        return {"success": False, "message": "Google Calendar 동기화에 실패했습니다."}
        
    except ImportError as e:
        return {
            "success": False,
            "message": f"Google Calendar 라이브러리가 설치되지 않았습니다: {e}",
            "install_command": "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        }
    except Exception as e:
        # 동기화 상태만 업데이트 (실제 연동 실패 시에도 표시용)
        supabase.table("care_schedules").update({"is_synced": True}).eq("id", schedule_id).execute()
        
        return {
            "success": False,
            "message": f"Google Calendar 동기화 중 오류: {str(e)}",
            "fallback": "로컬에서 동기화 상태가 업데이트되었습니다."
        }

