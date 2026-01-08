"""
환아 정보 API 라우터
====================

환아 프로필 CRUD 및 나이 계산
"""

from datetime import date
from typing import List

from fastapi import APIRouter, HTTPException, Depends, status

from models.child import Child, ChildCreate, ChildUpdate
from database import get_supabase
from routers.auth import get_current_user

router = APIRouter()


def calculate_age_months(birth_date: date) -> int:
    """생년월일로부터 개월 수 계산"""
    today = date.today()
    months = (today.year - birth_date.year) * 12 + (today.month - birth_date.month)
    return max(0, months)


@router.get("/", response_model=List[Child])
async def get_children(current_user: dict = Depends(get_current_user)):
    """
    내 환아 목록 조회
    
    등록된 모든 환아 정보를 반환합니다.
    """
    supabase = get_supabase()
    
    result = supabase.table("children").select("*").eq("user_id", current_user["id"]).execute()
    
    children = []
    for child_data in (result.data or []):
        birth_date = date.fromisoformat(child_data["birth_date"])
        children.append(Child(
            id=child_data["id"],
            user_id=child_data["user_id"],
            name=child_data["name"],
            birth_date=birth_date,
            disease_code=child_data["disease_code"],
            disease_name=child_data.get("disease_name"),
            symptoms=child_data.get("symptoms") or [],
            current_hospital=child_data.get("current_hospital"),
            attending_doctor=child_data.get("attending_doctor"),
            notes=child_data.get("notes"),
            created_at=child_data["created_at"],
            updated_at=child_data["updated_at"],
            age_months=calculate_age_months(birth_date)
        ))
    
    return children


@router.post("/", response_model=Child, status_code=status.HTTP_201_CREATED)
async def create_child(
    child_data: ChildCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    환아 정보 등록
    
    - **name**: 아이 이름
    - **birth_date**: 생년월일 (YYYY-MM-DD)
    - **disease_code**: ICD-10 질병 코드
    - **disease_name**: 질환명 (선택)
    """
    supabase = get_supabase()
    
    new_child = {
        "user_id": current_user["id"],
        "name": child_data.name,
        "birth_date": child_data.birth_date.isoformat(),
        "disease_code": child_data.disease_code,
        "disease_name": child_data.disease_name,
        "symptoms": child_data.symptoms,
        "current_hospital": child_data.current_hospital,
        "attending_doctor": child_data.attending_doctor,
        "notes": child_data.notes,
    }
    
    result = supabase.table("children").insert(new_child).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="환아 정보 등록에 실패했습니다."
        )
    
    child = result.data[0]
    birth_date = date.fromisoformat(child["birth_date"])
    
    return Child(
        id=child["id"],
        user_id=child["user_id"],
        name=child["name"],
        birth_date=birth_date,
        disease_code=child["disease_code"],
        disease_name=child.get("disease_name"),
        symptoms=child.get("symptoms") or [],
        current_hospital=child.get("current_hospital"),
        attending_doctor=child.get("attending_doctor"),
        notes=child.get("notes"),
        created_at=child["created_at"],
        updated_at=child["updated_at"],
        age_months=calculate_age_months(birth_date)
    )


@router.get("/{child_id}", response_model=Child)
async def get_child(
    child_id: str,
    current_user: dict = Depends(get_current_user)
):
    """특정 환아 정보 조회"""
    supabase = get_supabase()
    
    result = supabase.table("children").select("*").eq("id", child_id).eq("user_id", current_user["id"]).limit(1).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="환아 정보를 찾을 수 없습니다."
        )
    
    child = result.data[0]
    birth_date = date.fromisoformat(child["birth_date"])
    
    return Child(
        id=child["id"],
        user_id=child["user_id"],
        name=child["name"],
        birth_date=birth_date,
        disease_code=child["disease_code"],
        disease_name=child.get("disease_name"),
        symptoms=child.get("symptoms") or [],
        current_hospital=child.get("current_hospital"),
        attending_doctor=child.get("attending_doctor"),
        notes=child.get("notes"),
        created_at=child["created_at"],
        updated_at=child["updated_at"],
        age_months=calculate_age_months(birth_date)
    )


@router.patch("/{child_id}", response_model=Child)
async def update_child(
    child_id: str,
    child_data: ChildUpdate,
    current_user: dict = Depends(get_current_user)
):
    """환아 정보 수정"""
    supabase = get_supabase()
    
    # 권한 확인
    existing = supabase.table("children").select("id").eq("id", child_id).eq("user_id", current_user["id"]).execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="환아 정보를 찾을 수 없습니다.")
    
    # 업데이트할 필드만 추출
    update_data = {k: v for k, v in child_data.model_dump().items() if v is not None}
    if "birth_date" in update_data:
        update_data["birth_date"] = update_data["birth_date"].isoformat()
    
    result = supabase.table("children").update(update_data).eq("id", child_id).execute()
    
    child = result.data[0]
    birth_date = date.fromisoformat(child["birth_date"])
    
    return Child(
        id=child["id"],
        user_id=child["user_id"],
        name=child["name"],
        birth_date=birth_date,
        disease_code=child["disease_code"],
        disease_name=child.get("disease_name"),
        symptoms=child.get("symptoms") or [],
        current_hospital=child.get("current_hospital"),
        attending_doctor=child.get("attending_doctor"),
        notes=child.get("notes"),
        created_at=child["created_at"],
        updated_at=child["updated_at"],
        age_months=calculate_age_months(birth_date)
    )


@router.delete("/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_child(
    child_id: str,
    current_user: dict = Depends(get_current_user)
):
    """환아 정보 삭제"""
    supabase = get_supabase()
    
    result = supabase.table("children").delete().eq("id", child_id).eq("user_id", current_user["id"]).execute()
    
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="환아 정보를 찾을 수 없습니다.")
