"""
관찰 일기 API 라우터
====================

영상/사진 기록, 증상 태그, AI 분석
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, status, Query

from models.diary import Diary, DiaryCreate, DiaryUpdate, DiaryListResponse
from database import get_supabase
from routers.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=DiaryListResponse)
async def get_diaries(
    child_id: Optional[str] = Query(None, description="특정 환아의 일기만 조회"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    current_user: dict = Depends(get_current_user)
):
    """
    관찰 일기 목록 조회
    
    - **child_id**: 특정 환아의 일기만 필터링 (선택)
    - **page**: 페이지 번호 (기본: 1)
    - **page_size**: 페이지당 항목 수 (기본: 20)
    """
    supabase = get_supabase()
    
    query = supabase.table("observation_diaries").select("*", count="exact").eq("user_id", current_user["id"])
    
    if child_id:
        query = query.eq("child_id", child_id)
    
    # 페이지네이션
    offset = (page - 1) * page_size
    query = query.order("recorded_at", desc=True).range(offset, offset + page_size - 1)
    
    result = query.execute()
    
    diaries = []
    for diary_data in (result.data or []):
        diaries.append(Diary(
            id=diary_data["id"],
            child_id=diary_data["child_id"],
            user_id=diary_data["user_id"],
            recorded_at=diary_data["recorded_at"],
            video_url=diary_data.get("video_url"),
            thumbnail_url=diary_data.get("thumbnail_url"),
            duration_seconds=diary_data.get("duration_seconds"),
            symptom_tags=diary_data.get("symptom_tags") or [],
            notes=diary_data.get("notes"),
            ai_analysis=diary_data.get("ai_analysis"),
            spasm_count=diary_data.get("spasm_count"),
            created_at=diary_data["created_at"]
        ))
    
    return DiaryListResponse(
        items=diaries,
        total=result.count or len(diaries),
        page=page,
        page_size=page_size
    )


@router.post("/", response_model=Diary, status_code=status.HTTP_201_CREATED)
async def create_diary(
    diary_data: DiaryCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    관찰 일기 작성
    
    - **child_id**: 환아 ID
    - **recorded_at**: 기록 일시
    - **video_url**: 영상 URL (선택)
    - **symptom_tags**: 증상 태그 배열 (선택)
    - **notes**: 메모 (선택)
    """
    supabase = get_supabase()
    
    # 환아 소유권 확인
    child_check = supabase.table("children").select("id").eq("id", diary_data.child_id).eq("user_id", current_user["id"]).execute()
    if not child_check.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="환아 정보를 찾을 수 없습니다.")
    
    new_diary = {
        "child_id": diary_data.child_id,
        "user_id": current_user["id"],
        "recorded_at": diary_data.recorded_at.isoformat(),
        "video_url": diary_data.video_url,
        "thumbnail_url": diary_data.thumbnail_url,
        "duration_seconds": diary_data.duration_seconds,
        "symptom_tags": diary_data.symptom_tags,
        "notes": diary_data.notes,
    }
    
    result = supabase.table("observation_diaries").insert(new_diary).execute()
    
    if not result.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="일기 작성에 실패했습니다.")
    
    diary = result.data[0]
    
    return Diary(
        id=diary["id"],
        child_id=diary["child_id"],
        user_id=diary["user_id"],
        recorded_at=diary["recorded_at"],
        video_url=diary.get("video_url"),
        thumbnail_url=diary.get("thumbnail_url"),
        duration_seconds=diary.get("duration_seconds"),
        symptom_tags=diary.get("symptom_tags") or [],
        notes=diary.get("notes"),
        ai_analysis=diary.get("ai_analysis"),
        spasm_count=diary.get("spasm_count"),
        created_at=diary["created_at"]
    )


@router.get("/{diary_id}", response_model=Diary)
async def get_diary(
    diary_id: str,
    current_user: dict = Depends(get_current_user)
):
    """특정 관찰 일기 조회"""
    supabase = get_supabase()
    
    result = supabase.table("observation_diaries").select("*").eq("id", diary_id).eq("user_id", current_user["id"]).limit(1).execute()
    
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="일기를 찾을 수 없습니다.")
    
    diary = result.data[0]
    
    return Diary(
        id=diary["id"],
        child_id=diary["child_id"],
        user_id=diary["user_id"],
        recorded_at=diary["recorded_at"],
        video_url=diary.get("video_url"),
        thumbnail_url=diary.get("thumbnail_url"),
        duration_seconds=diary.get("duration_seconds"),
        symptom_tags=diary.get("symptom_tags") or [],
        notes=diary.get("notes"),
        ai_analysis=diary.get("ai_analysis"),
        spasm_count=diary.get("spasm_count"),
        created_at=diary["created_at"]
    )


@router.patch("/{diary_id}", response_model=Diary)
async def update_diary(
    diary_id: str,
    diary_data: DiaryUpdate,
    current_user: dict = Depends(get_current_user)
):
    """관찰 일기 수정"""
    supabase = get_supabase()
    
    # 권한 확인
    existing = supabase.table("observation_diaries").select("id").eq("id", diary_id).eq("user_id", current_user["id"]).execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="일기를 찾을 수 없습니다.")
    
    update_data = {k: v for k, v in diary_data.model_dump().items() if v is not None}
    
    result = supabase.table("observation_diaries").update(update_data).eq("id", diary_id).execute()
    
    diary = result.data[0]
    
    return Diary(
        id=diary["id"],
        child_id=diary["child_id"],
        user_id=diary["user_id"],
        recorded_at=diary["recorded_at"],
        video_url=diary.get("video_url"),
        thumbnail_url=diary.get("thumbnail_url"),
        duration_seconds=diary.get("duration_seconds"),
        symptom_tags=diary.get("symptom_tags") or [],
        notes=diary.get("notes"),
        ai_analysis=diary.get("ai_analysis"),
        spasm_count=diary.get("spasm_count"),
        created_at=diary["created_at"]
    )


@router.delete("/{diary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diary(
    diary_id: str,
    current_user: dict = Depends(get_current_user)
):
    """관찰 일기 삭제"""
    supabase = get_supabase()
    
    result = supabase.table("observation_diaries").delete().eq("id", diary_id).eq("user_id", current_user["id"]).execute()
    
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="일기를 찾을 수 없습니다.")


@router.post("/{diary_id}/analyze")
async def analyze_diary(
    diary_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    AI 분석 요청
    
    영상을 AI로 분석하여 연축 횟수, 패턴, 심각도를 판별합니다.
    (실제 AI 연동은 별도 구현 필요)
    """
    supabase = get_supabase()
    
    # 일기 조회
    result = supabase.table("observation_diaries").select("*").eq("id", diary_id).eq("user_id", current_user["id"]).limit(1).execute()
    
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="일기를 찾을 수 없습니다.")
    
    diary = result.data[0]
    
    # TODO: 실제 AI 분석 로직 구현
    # 현재는 더미 데이터 반환
    ai_analysis = {
        "spasm_count": 2,
        "patterns": "저녁 시간대 집중",
        "severity": "medium",
        "recommendations": [
            "다음 진료 시 영상 공유를 권장합니다.",
            "저녁 시간대 관찰을 더 자주 해주세요."
        ]
    }
    
    # 분석 결과 저장
    supabase.table("observation_diaries").update({
        "ai_analysis": ai_analysis,
        "spasm_count": ai_analysis["spasm_count"]
    }).eq("id", diary_id).execute()
    
    return {
        "message": "AI 분석이 완료되었습니다.",
        "analysis": ai_analysis
    }
