"""
HopeLink - FastAPI 백엔드 서버 (로컬 테스트용)
==============================================

Supabase 없이 기본 기능 테스트용
프론트엔드도 함께 제공 (모바일 접속용)
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# FastAPI 앱 생성
app = FastAPI(
    title="HopeLink API",
    description="희귀질환 환아 케어 플랫폼 REST API (테스트 모드)",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# 프론트엔드 정적 파일 제공 (모바일 접속용)
# ============================================
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/")
async def serve_frontend():
    """메인 페이지 - 프론트엔드 HTML 제공"""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"message": "🎀 HopeLink API에 오신 것을 환영합니다!", "docs": "/docs"}

@app.get("/manifest.json")
async def serve_manifest():
    """PWA 매니페스트"""
    manifest_path = os.path.join(frontend_path, "manifest.json")
    if os.path.exists(manifest_path):
        return FileResponse(manifest_path, media_type="application/json")
    return {}

@app.get("/sw.js")
async def serve_service_worker():
    """서비스 워커"""
    sw_path = os.path.join(frontend_path, "sw.js")
    if os.path.exists(sw_path):
        return FileResponse(sw_path, media_type="application/javascript")
    return ""


# ============================================
# 테스트용 인메모리 데이터
# ============================================
fake_users = {}
fake_children = {}
fake_diaries = []


# ============================================
# 모델 정의
# ============================================
class UserCreate(BaseModel):
    email: str
    password: str
    name: str

class ChildCreate(BaseModel):
    name: str
    birth_date: str
    disease_name: str

class DiaryCreate(BaseModel):
    child_id: str
    notes: str
    condition: str

class ChatMessage(BaseModel):
    content: str
    chat_type: str = "general"


# ============================================
# API 엔드포인트
# ============================================

@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "message": "🎀 HopeLink API에 오신 것을 환영합니다!",
        "version": "1.0.0 (테스트 모드)",
        "docs": "/docs",
        "status": "✅ 서버 정상 작동 중"
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "mode": "test"}


# ============================================
# 인증 API (이메일 OTP 방식 - 구글 스타일)
# ============================================

# 임시 인증 코드 저장소
verification_codes = {}

class EmailRequest(BaseModel):
    email: str

class VerifyCodeRequest(BaseModel):
    email: str
    code: str

class ProfileSetup(BaseModel):
    email: str
    name: str


@app.post("/api/auth/send-code")
async def send_verification_code(request: EmailRequest):
    """
    1단계: 이메일로 인증 코드 발송
    (테스트 모드에서는 코드를 바로 반환)
    """
    import random
    code = str(random.randint(100000, 999999))  # 6자리 코드
    verification_codes[request.email] = code
    
    # 실제로는 여기서 이메일 발송
    # send_email(request.email, f"인증 코드: {code}")
    
    return {
        "message": f"인증 코드가 {request.email}로 발송되었습니다.",
        "success": True,
        # 테스트 모드에서만 코드 노출 (프로덕션에서는 제거)
        "test_mode_code": code
    }


@app.post("/api/auth/verify-code")
async def verify_code(request: VerifyCodeRequest):
    """
    2단계: 인증 코드 확인 및 로그인
    """
    stored_code = verification_codes.get(request.email)
    
    if not stored_code or stored_code != request.code:
        return {
            "success": False,
            "message": "인증 코드가 올바르지 않습니다."
        }
    
    # 코드 사용 후 삭제
    del verification_codes[request.email]
    
    # 기존 사용자인지 확인
    existing_user = None
    for uid, user in fake_users.items():
        if user["email"] == request.email:
            existing_user = user
            break
    
    if existing_user:
        # 기존 사용자 로그인
        return {
            "success": True,
            "message": "로그인 성공!",
            "is_new_user": False,
            "user": existing_user,
            "access_token": f"token_{existing_user['id']}"
        }
    else:
        # 신규 사용자 - 프로필 설정 필요
        return {
            "success": True,
            "message": "인증 완료! 프로필을 설정해주세요.",
            "is_new_user": True,
            "email": request.email,
            "access_token": f"temp_token_{request.email}"
        }


@app.post("/api/auth/setup-profile")
async def setup_profile(profile: ProfileSetup):
    """
    3단계: 신규 사용자 프로필 설정 (회원가입 완료)
    """
    user_id = f"user_{len(fake_users) + 1}"
    fake_users[user_id] = {
        "id": user_id,
        "email": profile.email,
        "name": profile.name,
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "message": "회원가입이 완료되었습니다! 🎉",
        "user": fake_users[user_id],
        "access_token": f"token_{user_id}"
    }


# ============================================
# 환아 정보 API
# ============================================

@app.get("/api/children")
async def get_children():
    """환아 목록"""
    return {"children": list(fake_children.values())}


@app.post("/api/children")
async def create_child(child: ChildCreate):
    """환아 등록"""
    child_id = f"child_{len(fake_children) + 1}"
    fake_children[child_id] = {
        "id": child_id,
        "name": child.name,
        "birth_date": child.birth_date,
        "disease_name": child.disease_name,
        "created_at": datetime.now().isoformat()
    }
    return {"message": "환아 정보 등록 완료!", "child": fake_children[child_id]}


# ============================================
# 관찰 일기 API
# ============================================

@app.get("/api/diaries")
async def get_diaries():
    """일기 목록"""
    return {"diaries": fake_diaries}


@app.post("/api/diaries")
async def create_diary(diary: DiaryCreate):
    """일기 작성"""
    new_diary = {
        "id": f"diary_{len(fake_diaries) + 1}",
        "child_id": diary.child_id,
        "notes": diary.notes,
        "condition": diary.condition,
        "created_at": datetime.now().isoformat()
    }
    fake_diaries.append(new_diary)
    return {"message": "일기 저장 완료!", "diary": new_diary}


# ============================================
# AI 챗봇 API (OpenAI 연동)
# ============================================

import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 시스템 프롬프트
SYSTEM_PROMPT = """당신은 '호프 AI'입니다. 희귀질환(영아연축, 웨스트증후군 등) 환아 가족을 위한 케어 파트너입니다.

역할:
1. 💊 의약품 정보 안내 (비가바트린, ACTH 등)
2. 🏛️ 복지혜택 안내 (산정특례, 발달재활 바우처 등)
3. 💚 정서 지원 (공감과 위로)
4. 📋 의료용어 해석

응답 규칙:
- 따뜻하고 공감하는 어조
- 이모지 적절히 사용
- 한국어로 짧게 (3-5문장)
- 의학적 조언 끝에는 "담당 주치의와 상담하세요" 추가"""

FALLBACK_RESPONSES = {
    "welfare": """📋 **희귀질환 환아 복지혜택 안내**

1. **산정특례제도**: 본인부담금 10%로 경감
2. **발달재활서비스 바우처**: 월 14~22만원 지원
3. **장애아동수당**: 월 2~22만원
4. **의료비 지원**: 희귀질환자 의료비 지원사업

더 자세한 정보가 필요하시면 말씀해주세요!""",
    "medicine": "💊 비가바트린, ACTH 등 약물 정보는 담당 주치의와 상담하시기 바랍니다. 부작용이나 복용법이 궁금하시면 알려주세요!",
    "emotion": """💚 **많이 힘드시군요...**

아이를 돌보시느라 정말 고생이 많으세요.
혼자 감당하지 마시고, 언제든 이야기 나눠요.

**상담 연락처:**
- 희귀질환지원센터: 02-2258-7472
- 정신건강위기상담: 1577-0199

항상 응원합니다! 💪""",
    "general": "안녕하세요! 저는 호프 AI예요. 😊 무엇을 도와드릴까요? 복지혜택, 약물 정보, 의료용어 해석 등 뭐든 물어보세요!"
}

@app.post("/api/ai/chat")
async def chat(message: ChatMessage):
    """AI 챗봇 (OpenAI GPT-4 연동)"""
    
    # OpenAI API 키가 있으면 사용
    if OPENAI_API_KEY and OPENAI_API_KEY.startswith("sk-"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            type_contexts = {
                "welfare": "복지혜택 문의입니다.",
                "medicine": "약물 정보 문의입니다.",
                "emotion": "정서적 지원이 필요합니다.",
                "general": "일반 대화입니다."
            }
            context = type_contexts.get(message.chat_type, "일반 대화입니다.")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + context},
                    {"role": "user", "content": message.content}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return {
                "response": response.choices[0].message.content,
                "chat_type": message.chat_type,
                "ai_model": "gpt-4o-mini"
            }
        except Exception as e:
            print(f"OpenAI 호출 실패: {e}")
    
    # Fallback 응답
    return {
        "response": FALLBACK_RESPONSES.get(message.chat_type, FALLBACK_RESPONSES["general"]),
        "chat_type": message.chat_type,
        "ai_model": "fallback"
    }


# ============================================
# 케어 플랜 API
# ============================================

@app.get("/api/schedules")
async def get_schedules():
    """일정 목록"""
    return {
        "schedules": [
            {
                "id": "1",
                "title": "서울대병원 신경과",
                "start_time": "2026-01-10T14:00:00",
                "end_time": "2026-01-10T15:30:00",
                "schedule_type": "hospital"
            },
            {
                "id": "2", 
                "title": "재활치료",
                "start_time": "2026-01-10T15:00:00",
                "end_time": "2026-01-10T16:00:00",
                "schedule_type": "rehabilitation"
            }
        ],
        "conflicts": [
            {
                "message": "⚠️ '서울대병원 신경과'와 '재활치료' 일정이 30분 겹칩니다."
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_test:app", host="0.0.0.0", port=8000, reload=True)
