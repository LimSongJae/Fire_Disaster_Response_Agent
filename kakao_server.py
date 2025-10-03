import json
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
import httpx

# 프로젝트의 다른 모듈에서 필요한 함수 및 설정값 가져오기
from main import run_workflow
from config import KAKAO_ADMIN_KEY

# FastAPI 앱 초기화
app = FastAPI()

# --- Pydantic 모델 정의 (기존과 동일) ---
class Intent(BaseModel):
    id: str; name: str
class Block(BaseModel):
    id: str; name: str
class User(BaseModel):
    id: str; type: str; properties: Dict[str, Any]
class UserRequest(BaseModel):
    timezone: str; params: Dict[str, Any]; block: Block; utterance: str; lang: Optional[str] = None; user: User
class Bot(BaseModel):
    id: str; name: str
class Action(BaseModel):
    name: str; clientExtra: Optional[Dict[str, Any]] = None; params: Dict[str, Any]; id: str; detailParams: Dict[str, Any]
class KakaoRequest(BaseModel):
    intent: Intent; userRequest: UserRequest; bot: Bot; action: Action


# --- 핵심 로직: 비동기 처리 및 답변 푸시 ---

async def push_kakao_message(user_id: str, response_text: str):
    """
    분석이 완료된 후 카카오 채널 메시지 API를 호출하여 사용자에게 답변을 보냅니다.
    """
    print(f"✅ 작업 완료. 사용자({user_id})에게 답변 푸시 시작.")
    
    url = "https://kapi.kakao.com/v1/api/talk/friends/message/default/send"
    headers = {"Authorization": f"KakaoAK {KAKAO_ADMIN_KEY}"}
    template_object = {
        "object_type": "text",
        "text": response_text,
        "link": {"web_url": "https://developers.kakao.com", "mobile_web_url": "https://developers.kakao.com"}
    }
    data = {
        "receiver_uuids": json.dumps([user_id]),
        "template_object": json.dumps(template_object)
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, data=data)
            response.raise_for_status()
            print(f"✅ 성공: 사용자({user_id})에게 메시지 전송 완료. 응답: {response.json()}")
        except httpx.HTTPStatusError as e:
            print(f"❌ 실패: 카카오 API 에러. 상태코드: {e.response.status_code}, 내용: {e.response.text}")
        except Exception as e:
            print(f"❌ 실패: 메시지 전송 중 알 수 없는 오류 발생: {e}")


# --- FastAPI 엔드포인트 정의 ---

@app.post("/skill/chat")
async def chat(request: KakaoRequest, background_tasks: BackgroundTasks):
    """
    카카오 i 오픈빌더 스킬의 메인 엔드포인트입니다.
    사용자 요청을 받으면 즉시 응답하고, 실제 작업은 백그라운드로 넘깁니다.
    """
    user_message = request.userRequest.utterance
    user_id = request.userRequest.user.id
    
    print(f"🚀 요청 접수: '{user_message}' (사용자 ID: {user_id})")

    # 👇 별도의 함수 대신, 백그라운드에서 실행할 작업을 직접 정의합니다.
    async def background_task(message: str, u_id: str):
        print(f"⏳ 백그라운드 작업 시작: '{message}' (사용자 ID: {u_id})")
        # 사용자 ID를 thread_id로 전달하여 AI 에이전트 실행
        response_text = await run_workflow(message, thread_id=u_id)
        # 최종 답변을 사용자에게 푸시
        await push_kakao_message(u_id, response_text)

    # 시간이 오래 걸리는 작업을 백그라운드 태스크로 등록
    background_tasks.add_task(background_task, user_message, user_id)
    
    # 5초 제한을 통과하기 위한 즉각적인 응답
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": "(🥺⏳)"}}
            ]
        }
    }

@app.get("/health")
async def health():
    """서버 상태를 확인하기 위한 헬스 체크 엔드포인트입니다."""
    return {"status": "OK"}