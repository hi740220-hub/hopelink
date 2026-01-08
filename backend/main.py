"""
HopeLink - FastAPI 백엔드 서버
==============================

희귀질환 환아 케어 플랫폼을 위한 REST API 서버
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers import auth, children, diaries, schedules, ai_chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 이벤트"""
    print("🚀 HopeLink API 서버가 시작되었습니다!")
    yield
    print("👋 HopeLink API 서버가 종료됩니다.")


# FastAPI 앱 생성
app = FastAPI(
    title="HopeLink API",
    description="희귀질환 환아 케어 플랫폼 REST API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["인증"])
app.include_router(children.router, prefix="/api/children", tags=["환아 정보"])
app.include_router(diaries.router, prefix="/api/diaries", tags=["관찰 일기"])
app.include_router(schedules.router, prefix="/api/schedules", tags=["케어 플랜"])
app.include_router(ai_chat.router, prefix="/api/ai", tags=["AI 케어"])


@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "message": "🎀 HopeLink API에 오신 것을 환영합니다!",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "service": "hopelink-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
