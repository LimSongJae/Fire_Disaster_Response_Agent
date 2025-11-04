# kakao.py (공식 가이드 반영 최종 버전)

import json
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, Optional

# 프로젝트의 다른 모듈에서 필요한 함수 가져오기
from main import run_workflow

# FastAPI 앱 초기화
app = FastAPI()

# --- Pydantic 모델 정의 ---

# 1. 사용자의 첫 번째 요청('/skill/chat')을 위한 모델들 (기존과 동일)
class Intent(BaseModel):
    id: str
    name: str

class Block(BaseModel):
    id: str
    name: str

class User(BaseModel):
    id: str
    type: str
    properties: Dict[str, Any]

class UserRequest(BaseModel):
    timezone: str
    params: Dict[str, Any]
    block: Block
    utterance: str
    lang: Optional[str] = None
    user: User

class Bot(BaseModel):
    id: str
    name: str

class Action(BaseModel):
    name: str
    clientExtra: Optional[Dict[str, Any]] = None
    params: Dict[str, Any]
    id: str
    detailParams: Dict[str, Any]

class KakaoRequest(BaseModel):
    intent: Intent
    userRequest: UserRequest
    bot: Bot
    action: Action

# 👇 2. 콜백 요청('/skill/callback')을 위한 모델 (공식 가이드에 맞춰 수정)
class UserRequestInCallback(BaseModel):
    user: User
    utterance: str # 콜백 요청 시에는 원본 발화도 함께 전달됩니다.

class KakaoCallbackRequest(BaseModel):
    userRequest: UserRequestInCallback
    data: Dict[str, Any]


# --- FastAPI 엔드포인트 정의 ---

@app.post("/skill/chat")
async def chat(request: KakaoRequest):
    """
    사용자의 첫 요청을 받는 메인 엔드포인트.
    Callback을 요청하는 응답을 즉시 보냅니다. (공식 가이드와 일치)
    """
    user_message = request.userRequest.utterance
    user_id = request.userRequest.user.id
    
    print(f"🚀 요청 접수 (Callback 시작): '{user_message}' (사용자 ID: {user_id})")

    # 콜백 시 다시 전달받을 데이터를 구성합니다.
    # user_message만 전달해도 충분합니다. user_id는 콜백 요청에 기본적으로 포함되기 때문입니다.
    callback_data = {
        "user_message": user_message
    }

    # useCallback: true 응답
    return {
        "version": "2.0",
        "useCallback": True,
        "data": callback_data
    }

@app.post("/skill/callback")
async def callback(request: KakaoCallbackRequest):
    """
    카카오의 백그라운드 시스템이 호출하는 콜백 엔드포인트.
    여기서 시간이 오래 걸리는 AI 분석을 수행하고 최종 답변을 생성합니다.
    """
    # 👇 공식 가이드의 데이터 구조에 맞춰 데이터를 가져옵니다.
    user_message = request.data.get("user_message")
    user_id = request.userRequest.user.id # 👈 콜백 요청의 userRequest에서 id를 가져오는 것이 더 안정적입니다.

    print(f"⏳ 콜백 수신, 백그라운드 작업 시작: '{user_message}' (사용자 ID: {user_id})")

    try:
        response_text = await run_workflow(user_message, thread_id=user_id)
    except Exception as e:
        print(f"❌ 백그라운드 작업 중 오류 발생: {e}")
        response_text = "죄송합니다, 요청을 처리하는 중에 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        
    # 최종 답변을 카카오 스킬 응답 형식으로 반환합니다.
    # return {
    #     "version": "2.0",
    #     "data": {
    #         "text": response_text
    #     }
    # }
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": response_text
                    }
                }
            ]
        }
    }

@app.get("/health")
async def health():
    """서버 상태를 확인하기 위한 헬스 체크 엔드포인트입니다."""
    return {"status": "OK"}