"""
AI 케어 파트너 API 라우터
=========================

AI 챗봇, 의무기록 해석, 복지혜택 안내
"""

import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status

from models.chat import ChatMessage, ChatResponse
from database import get_supabase
from routers.auth import get_current_user

router = APIRouter()

# OpenAI 설정 (선택적)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


# 기본 응답 템플릿 (AI 연동 전 사용)
DEFAULT_RESPONSES = {
    "general": "안녕하세요! 저는 호프 AI예요. 무엇을 도와드릴까요? 😊",
    "record": "의무기록지를 업로드해주시면 쉽게 설명해드릴게요. 📋",
    "emotion": "힘드시군요... 언제든 이야기 들을 준비가 되어있어요. 💚 지금 어떤 마음이신가요?",
    "welfare": "복지혜택에 대해 알려드릴게요. 현재 이용 가능한 지원제도를 안내해드립니다. 🏛️",
    "medicine": "약물 정보를 안내해드릴게요. 복용 중인 약 이름을 알려주시겠어요? 💊",
}

WELFARE_INFO = """
📋 **희귀질환 환아 복지혜택 안내**

1. **산정특례제도**
   - 희귀질환 등록 시 본인부담금 10%로 경감
   - 신청: 건강보험공단 또는 병원 원무과

2. **발달재활서비스 바우처**
   - 만 18세 미만 장애아동
   - 월 14~22만원 지원
   - 신청: 주민센터

3. **장애아동수당**
   - 만 18세 미만 장애아동
   - 월 2~22만원 (중증도별 차등)
   - 신청: 주민센터

4. **의료비 지원**
   - 희귀질환자 의료비 지원사업
   - 본인부담금 지원
   - 신청: 보건소

더 자세한 정보가 필요하시면 말씀해주세요!
"""

MEDICINE_INFO = {
    "비가바트린": """
💊 **비가바트린 (Vigabatrin)**

- **적응증**: 영아연축(웨스트증후군), 부분발작
- **용법**: 1일 2회 복용, 음식과 무관
- **주의사항**: 
  - 정기적 시야검사 필요 (3개월마다)
  - 급작스러운 복용 중단 금지
  - 졸음, 피로감 발생 가능

⚠️ 복용 관련 구체적 상담은 담당 주치의와 상의하세요.
""",
    "default": "해당 약물 정보를 찾지 못했어요. 약 이름을 정확히 입력해주시겠어요?"
}


async def get_ai_response(message: str, chat_type: str) -> str:
    """AI 응답 생성 (OpenAI GPT-4 연동, 없으면 규칙 기반)"""
    
    # OpenAI API 키가 있으면 GPT-4 사용
    if OPENAI_API_KEY and OPENAI_API_KEY.startswith("sk-"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            # 시스템 프롬프트 (희귀질환 환아 케어 전문가)
            system_prompt = """당신은 '호프 AI'입니다. 희귀질환(영아연축, 웨스트증후군 등) 환아 가족을 위한 
케어 파트너로서 다음 역할을 수행합니다:

1. 💊 의약품 정보: 비가바트린, ACTH 등 항경련제 정보를 쉽게 설명
2. 🏛️ 복지혜택 안내: 산정특례, 발달재활 바우처, 장애아동수당 등 안내
3. 💚 정서 지원: 부모의 마음을 공감하며 위로와 격려 제공
4. 📋 의료용어 해석: EEG, MRI, Hypsarrhythmia 등 의료 용어를 쉽게 풀이

응답 시 주의사항:
- 따뜻하고 공감하는 어조 사용
- 의학적 조언은 "담당 주치의와 상담하세요"로 마무리
- 이모지를 적절히 사용하여 친근하게
- 한국어로 응답
- 짧고 명확하게 (3-5문장)"""

            # 대화 유형별 추가 컨텍스트
            type_contexts = {
                "welfare": "사용자가 복지혜택에 대해 문의합니다. 산정특례, 발달재활 바우처, 장애아동수당 등을 안내하세요.",
                "medicine": "사용자가 약물 정보를 문의합니다. 비가바트린, ACTH 등의 정보를 쉽게 설명하세요.",
                "emotion": "사용자가 힘든 마음을 표현합니다. 공감하고 위로하며, 필요시 상담 연락처를 안내하세요.",
                "record": "사용자가 의무기록/검사 결과 해석을 원합니다. 의료 용어를 쉽게 풀어 설명하세요.",
                "general": "일반적인 대화입니다. 친절하게 도와주세요."
            }
            
            context = type_contexts.get(chat_type, type_contexts["general"])
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # 비용 효율적인 모델
                messages=[
                    {"role": "system", "content": system_prompt + "\n\n" + context},
                    {"role": "user", "content": message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            print("OpenAI 라이브러리가 설치되지 않았습니다. pip install openai")
        except Exception as e:
            print(f"OpenAI API 호출 실패: {e}")
    
    # Fallback: 기존 규칙 기반 응답
    message_lower = message.lower()
    
    # 복지혜택 관련
    if chat_type == "welfare" or any(word in message for word in ["산정특례", "바우처", "지원금", "복지", "혜택"]):
        return WELFARE_INFO
    
    # 약물 정보
    if chat_type == "medicine" or "약" in message or "복용" in message:
        for drug_name, info in MEDICINE_INFO.items():
            if drug_name in message:
                return info
        return MEDICINE_INFO["default"]
    
    # 정서 상담
    if chat_type == "emotion" or any(word in message for word in ["힘들", "지치", "우울", "불안", "걱정"]):
        return """
💚 **마음이 많이 지치셨군요...**

아이를 돌보며 힘드신 마음 충분히 이해해요. 
혼자 감당하려 하지 마시고, 잠시 쉬어가셔도 괜찮아요.

**도움받을 수 있는 곳:**
- 희귀질환지원센터 상담: 02-2258-7472
- 정신건강 위기상담: 1577-0199

언제든 이야기 나누고 싶으시면 말해주세요. 💪
"""
    
    # 의무기록 해석
    if chat_type == "record" or any(word in message for word in ["의무기록", "검사결과", "소견서", "MRI", "EEG"]):
        return """
📋 **의무기록 해석 도우미**

의무기록지나 검사 결과지를 사진으로 찍어 올려주시면,
어려운 의학 용어를 쉽게 풀어서 설명해드릴게요.

**자주 묻는 용어:**
- **EEG (뇌파 검사)**: 뇌의 전기 활동을 측정
- **MRI**: 뇌 구조를 자세히 촬영
- **Spasm**: 연축 (근육의 갑작스러운 수축)

이미지를 업로드해주시거나, 궁금한 용어를 알려주세요!
"""
    
    # 기본 응답
    return DEFAULT_RESPONSES.get(chat_type, DEFAULT_RESPONSES["general"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    current_user: dict = Depends(get_current_user)
):
    """
    AI 케어 파트너와 대화
    
    - **content**: 메시지 내용
    - **chat_type**: 대화 유형 ('general', 'record', 'emotion', 'welfare', 'medicine')
    """
    supabase = get_supabase()
    
    # 세션 ID 생성 (또는 기존 세션 사용)
    session_id = str(uuid.uuid4())
    
    # 사용자 메시지 저장
    supabase.table("chat_conversations").insert({
        "user_id": current_user["id"],
        "session_id": session_id,
        "role": "user",
        "content": message.content,
        "intent": message.chat_type,
    }).execute()
    
    # AI 응답 생성
    response_text = await get_ai_response(message.content, message.chat_type)
    
    # AI 응답 저장
    supabase.table("chat_conversations").insert({
        "user_id": current_user["id"],
        "session_id": session_id,
        "role": "assistant",
        "content": response_text,
        "intent": message.chat_type,
    }).execute()
    
    # 후속 질문 추천
    suggestions = []
    if message.chat_type == "welfare":
        suggestions = ["산정특례 신청 방법", "발달재활 바우처 신청", "의료비 지원 안내"]
    elif message.chat_type == "medicine":
        suggestions = ["비가바트린 부작용", "약 복용 시간", "약 상호작용"]
    elif message.chat_type == "emotion":
        suggestions = ["지금 기분이 어떤가요?", "상담센터 연결", "다른 가족들 이야기"]
    
    return ChatResponse(
        message=response_text,
        intent=message.chat_type,
        confidence=0.9,
        suggestions=suggestions
    )


@router.get("/history")
async def get_chat_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """최근 AI 대화 기록 조회"""
    supabase = get_supabase()
    
    result = supabase.table("chat_conversations").select("*").eq("user_id", current_user["id"]).order("created_at", desc=True).limit(limit).execute()
    
    return {"history": result.data or []}


@router.post("/interpret-record")
async def interpret_medical_record(
    image_url: str,
    current_user: dict = Depends(get_current_user)
):
    """
    의무기록지 이미지 해석
    
    (OCR + AI 분석 연동 필요)
    """
    # TODO: 실제 OCR 및 AI 해석 구현
    return {
        "message": "의무기록 해석 기능은 준비 중입니다.",
        "image_received": image_url,
        "interpretation": None
    }
