# # kakao.py (공식 가이드 반영 최종 버전)

# import json
# from fastapi import FastAPI
# from pydantic import BaseModel
# from typing import Dict, Any, Optional

# # 프로젝트의 다른 모듈에서 필요한 함수 가져오기
# from main import run_workflow

# # FastAPI 앱 초기화
# app = FastAPI()

# # --- Pydantic 모델 정의 ---

# # 1. 사용자의 첫 번째 요청('/skill/chat')을 위한 모델들 (기존과 동일)
# class Intent(BaseModel):
#     id: str
#     name: str

# class Block(BaseModel):
#     id: str
#     name: str

# class User(BaseModel):
#     id: str
#     type: str
#     properties: Dict[str, Any]

# class UserRequest(BaseModel):
#     timezone: str
#     params: Dict[str, Any]
#     block: Block
#     utterance: str
#     lang: Optional[str] = None
#     user: User

# class Bot(BaseModel):
#     id: str
#     name: str

# class Action(BaseModel):
#     name: str
#     clientExtra: Optional[Dict[str, Any]] = None
#     params: Dict[str, Any]
#     id: str
#     detailParams: Dict[str, Any]

# class KakaoRequest(BaseModel):
#     intent: Intent
#     userRequest: UserRequest
#     bot: Bot
#     action: Action

# # 👇 2. 콜백 요청('/skill/callback')을 위한 모델 (공식 가이드에 맞춰 수정)
# class UserRequestInCallback(BaseModel):
#     user: User
#     utterance: str # 콜백 요청 시에는 원본 발화도 함께 전달됩니다.

# class KakaoCallbackRequest(BaseModel):
#     userRequest: UserRequestInCallback
#     data: Dict[str, Any]


# # --- FastAPI 엔드포인트 정의 ---

# @app.post("/skill/chat")
# async def chat(request: KakaoRequest):
#     """
#     사용자의 첫 요청을 받는 메인 엔드포인트.
#     Callback을 요청하는 응답을 즉시 보냅니다. (공식 가이드와 일치)
#     """
#     user_message = request.userRequest.utterance
#     user_id = request.userRequest.user.id
    
#     print(f"🚀 요청 접수 (Callback 시작): '{user_message}' (사용자 ID: {user_id})")

#     # 콜백 시 다시 전달받을 데이터를 구성합니다.
#     # user_message만 전달해도 충분합니다. user_id는 콜백 요청에 기본적으로 포함되기 때문입니다.
#     callback_data = {
#         "user_message": user_message
#     }

#     # useCallback: true 응답
#     return {
#         "version": "2.0",
#         "useCallback": True,
#         "data": callback_data
#     }

# @app.post("/skill/callback")
# async def callback(request: KakaoCallbackRequest):
#     """
#     카카오의 백그라운드 시스템이 호출하는 콜백 엔드포인트.
#     여기서 시간이 오래 걸리는 AI 분석을 수행하고 최종 답변을 생성합니다.
#     """
#     # 👇 공식 가이드의 데이터 구조에 맞춰 데이터를 가져옵니다.
#     user_message = request.data.get("user_message")
#     user_id = request.userRequest.user.id # 👈 콜백 요청의 userRequest에서 id를 가져오는 것이 더 안정적입니다.

#     print(f"⏳ 콜백 수신, 백그라운드 작업 시작: '{user_message}' (사용자 ID: {user_id})")

#     try:
#         response_text = await run_workflow(user_message, thread_id=user_id)
#     except Exception as e:
#         print(f"❌ 백그라운드 작업 중 오류 발생: {e}")
#         response_text = "죄송합니다, 요청을 처리하는 중에 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        
#     # 최종 답변을 카카오 스킬 응답 형식으로 반환합니다.
#     # return {
#     #     "version": "2.0",
#     #     "data": {
#     #         "text": response_text
#     #     }
#     # }
#     return {
#         "version": "2.0",
#         "template": {
#             "outputs": [
#                 {
#                     "simpleText": {
#                         "text": response_text
#                     }
#                 }
#             ]
#         }
#     }

# @app.get("/health")
# async def health():
#     """서버 상태를 확인하기 위한 헬스 체크 엔드포인트입니다."""
#     return {"status": "OK"}

# kakao.py (사용자님이 작성하신, 공식 가이드에 부합하는 올바른 코드)

import asyncio
from typing import Dict, Any, Optional

import httpx
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

from main import run_workflow  # 오래 걸리는 작업

app = FastAPI()

CALLBACK_TIMEOUT_SEC = 55  # 1분 유효시간(60초)보다 여유 있게 마감

# --- Pydantic 모델 ---

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
    # ✅ 카카오가 1회용 콜백 URL을 여기에 담아 보냅니다.
    callbackUrl: Optional[str] = None
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


# --- 내부 유틸 ---

async def _post_callback(callback_url: str, payload: Dict[str, Any]) -> None:
    """
    카카오가 제공한 1회용 callbackUrl로 최종 응답을 POST로 전송합니다.
    이것은 우리가 "새로 보내는 요청"입니다.
    """
    print(f"✅ 작업 완료. Callback URL로 최종 답변 전송 시작...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.post(callback_url, json=payload)
            r.raise_for_status()  # 200 OK가 아니면 예외 발생
            print(f"✅ Callback 전송 성공. 응답: {r.text}")
        except httpx.HTTPStatusError as e:
            print(f"❌ Callback 전송 실패: {e.response.status_code} {e.response.text}")
        except Exception as e:
            print(f"❌ Callback 전송 중 알 수 없는 오류: {e}")


async def _do_heavy_and_callback(callback_url: str, user_message: str, user_id: str):
    """
    (백그라운드 실행)
    무거운 AI 작업을 실행한 뒤, _post_callback을 호출합니다.
    """
    try:
        # 오래 걸리는 작업은 45초 내 완료를 목표로
        response_text = await asyncio.wait_for(
            run_workflow(user_message, thread_id=user_id),
            timeout=CALLBACK_TIMEOUT_SEC,
        )
    except asyncio.TimeoutError:
        print(f"❌ 백그라운드 오류: 작업 시간 초과 ({CALLBACK_TIMEOUT_SEC}초)")
        response_text = f"죄송합니다. AI 에이전트가 {CALLBACK_TIMEOUT_SEC}초 내에 응답하지 못했습니다."
    except Exception as e:
        print(f"❌ 백그라운드 오류: {e}")
        response_text = "죄송합니다. 요청 처리 중 오류가 발생했습니다."

    # 카카오 스킬 "최종" 응답 포맷(JSON)으로 콜백
    payload = {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": response_text}}
            ]
        }
    }
    await _post_callback(callback_url, payload)


# --- FastAPI 엔드포인트 ---

@app.post("/skill/chat")
async def chat(request: KakaoRequest, background_tasks: BackgroundTasks):
    """
    (카카오 i 오픈빌더 스킬 URL에 등록될 단일 엔드포인트)
    1. 5초 내 즉시 응답 (useCallback=true, 대기 문구)
    2. 백그라운드에서 전달받은 callbackUrl로 최종 답변을 POST
    """
    user_message = request.userRequest.utterance
    user_id = request.userRequest.user.id
    callback_url = request.userRequest.callbackUrl  # ✅ 카카오가 여기에 URL을 줍니다.

    print(f"🚀 요청 접수: '{user_message}' (user_id={user_id})")
    
    # 카카오가 callbackUrl을 주지 않았다면, 비정상적인 요청임
    if not callback_url:
        print("❌ 'callbackUrl'이 없습니다. 카카오 i 오픈빌더에서 콜백이 활성화되었는지 확인하세요.")
        return {
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": "챗봇 설정에 오류가 발생했습니다. (콜백 URL 누락)"}}]}
        }

    # 무거운 작업 + 콜백 POST는 백그라운드로 넘김
    background_tasks.add_task(_do_heavy_and_callback, callback_url, user_message, user_id)

    # ✅ 1차 즉시 응답: useCallback=true (template는 사용하지 않음)
    return {
        "version": "2.0",
        "useCallback": True,
        "data": {
            # 이 text는 카카오 i 오픈빌더 시나리오의 '응답 대기 중' 메시지로 활용 가능
            "text": "AI 에이전트가 분석을 시작합니다. 잠시만 기다려주세요."
        }
    }


@app.get("/health")
async def health():
    return {"status": "OK"}