"""
인증 API 라우터
===============

회원가입, 로그인, 토큰 관리
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from models.user import User, UserCreate, UserLogin, Token
from database import get_supabase

router = APIRouter()
security = HTTPBearer()

# 암호화 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "hopelink-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7일


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWT 토큰 생성"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """현재 로그인한 사용자 정보 반환"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="유효하지 않은 인증 정보입니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Supabase에서 사용자 조회
    supabase = get_supabase()
    result = supabase.table("users").select("*").eq("id", user_id).limit(1).execute()
    
    if not result.data:
        raise credentials_exception
    
    return result.data[0]


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate):
    """
    회원가입
    
    - **email**: 이메일 주소
    - **password**: 비밀번호 (8자 이상 권장)
    - **name**: 사용자 이름
    - **phone**: 전화번호 (선택)
    """
    supabase = get_supabase()
    
    # 이메일 중복 체크
    existing = supabase.table("users").select("id").eq("email", user_data.email).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다."
        )
    
    # 비밀번호 해싱 및 사용자 생성
    hashed_password = get_password_hash(user_data.password)
    
    new_user = {
        "email": user_data.email,
        "password_hash": hashed_password,
        "name": user_data.name,
        "phone": user_data.phone,
    }
    
    result = supabase.table("users").insert(new_user).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원가입에 실패했습니다."
        )
    
    user = result.data[0]
    
    # 토큰 생성
    access_token = create_access_token(data={"sub": user["id"]})
    
    return Token(
        access_token=access_token,
        user=User(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            phone=user.get("phone"),
            profile_image_url=user.get("profile_image_url"),
            created_at=user["created_at"]
        )
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    로그인
    
    - **email**: 이메일 주소
    - **password**: 비밀번호
    """
    supabase = get_supabase()
    
    # 사용자 조회
    result = supabase.table("users").select("*").eq("email", credentials.email).limit(1).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다."
        )
    
    user = result.data[0]
    
    # 비밀번호 검증
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다."
        )
    
    # 토큰 생성
    access_token = create_access_token(data={"sub": user["id"]})
    
    return Token(
        access_token=access_token,
        user=User(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            phone=user.get("phone"),
            profile_image_url=user.get("profile_image_url"),
            created_at=user["created_at"]
        )
    )


@router.get("/me", response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회"""
    return User(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        phone=current_user.get("phone"),
        profile_image_url=current_user.get("profile_image_url"),
        created_at=current_user["created_at"]
    )
