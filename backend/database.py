"""
HopeLink - Supabase 데이터베이스 연결
=====================================

Supabase 클라이언트 설정 및 헬퍼 함수
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Supabase 설정
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Supabase 클라이언트 (싱글톤)
_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Supabase 클라이언트 반환"""
    global _supabase_client
    
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError(
                "Supabase 환경 변수가 설정되지 않았습니다. "
                ".env 파일에 SUPABASE_URL과 SUPABASE_ANON_KEY를 설정하세요."
            )
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    return _supabase_client


# ============================================
# 헬퍼 함수들
# ============================================

async def fetch_one(table: str, filters: dict) -> dict | None:
    """단일 레코드 조회"""
    supabase = get_supabase()
    query = supabase.table(table).select("*")
    
    for key, value in filters.items():
        query = query.eq(key, value)
    
    result = query.limit(1).execute()
    return result.data[0] if result.data else None


async def fetch_all(table: str, filters: dict = None, order_by: str = None) -> list:
    """여러 레코드 조회"""
    supabase = get_supabase()
    query = supabase.table(table).select("*")
    
    if filters:
        for key, value in filters.items():
            query = query.eq(key, value)
    
    if order_by:
        desc = order_by.startswith("-")
        column = order_by.lstrip("-")
        query = query.order(column, desc=desc)
    
    result = query.execute()
    return result.data if result.data else []


async def insert_one(table: str, data: dict) -> dict:
    """레코드 삽입"""
    supabase = get_supabase()
    result = supabase.table(table).insert(data).execute()
    return result.data[0] if result.data else {}


async def update_one(table: str, record_id: str, data: dict) -> dict:
    """레코드 업데이트"""
    supabase = get_supabase()
    result = supabase.table(table).update(data).eq("id", record_id).execute()
    return result.data[0] if result.data else {}


async def delete_one(table: str, record_id: str) -> bool:
    """레코드 삭제"""
    supabase = get_supabase()
    result = supabase.table(table).delete().eq("id", record_id).execute()
    return len(result.data) > 0 if result.data else False
