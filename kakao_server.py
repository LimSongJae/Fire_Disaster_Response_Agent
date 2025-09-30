from fastapi import FastAPI
from __future__ import annotations # Python 3.7+ 에서 타입 힌트의 유연성을 위해 추가
from typing import Dict, Any, Optional
from pydantic import BaseModel
import asyncio
from main import run_workflow

app = FastAPI()

# intent, block 모델 (구조가 동일하지만 명확성을 위해 분리)∫
class Intent(BaseModel):
    id: str
    name: str

class Block(BaseModel):
    id: str
    name: str

# userRequest 내부의 user 모델
class User(BaseModel):
    id: str
    type: str
    properties: Dict[str, Any] # plusfriend_user_key, app_user_id 등이 포함될 수 있음

# userRequest 모델
class UserRequest(BaseModel):
    timezone: str
    params: Dict[str, Any]
    block: Block
    utterance: str
    lang: Optional[str] = None
    user: User

# bot 모델
class Bot(BaseModel):
    id: str
    name: str

# action 모델
class Action(BaseModel):
    name: str
    clientExtra: Optional[Dict[str, Any]] = None
    params: Dict[str, Any]
    id: str
    detailParams: Dict[str, Any]

# 전체 요청을 대표하는 메인 모델
class KakaoRequest(BaseModel):
    intent: Intent
    userRequest: UserRequest
    bot: Bot
    action: Action

@app.post("/skill/chat")
async def chat(request: KakaoRequest):
    # 사용자 메시지 받기
    user_message = request.userRequest.get("utterance", "")
    
    # 당신의 AI 에이전트 실행
    result = await run_workflow(user_message)
    
    # 응답 추출
    if result.get("messages"):
        response_text = result["messages"][-1].content
    else:
        response_text = "죄송합니다. 응답을 생성할 수 없습니다."
    
    # 카카오 형식으로 응답
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
    return {"status": "OK"}