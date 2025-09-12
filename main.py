import asyncio
from langchain_core.messages import HumanMessage
from graph import app
from config import RECURSION_LIMIT

async def run_workflow(question: str):
    """워크플로우를 실행하고 최종 결과를 반환합니다."""

    config = {"recursion_limit": RECURSION_LIMIT, "configurable": {"thread_id": "test-thread"}}

    # 그래프의 초기 상태 정의
    initial_state = {
        "messages": [HumanMessage(content=question)],
        "question": question,
        "use_agent": False,
        "agent_visited": False,
        "news": "",
        "GPS": "",
        "disaster": "",
        "SNS": "",
        "rag_context": "",
        "structured_response": None,
        # ❗❗❗ 이 부분이 반드시 존재해야 합니다 ❗❗❗
        "remaining_steps": 15,
    }
    
    print(f"🚀 질문: '{question}'에 대한 재난 분석을 시작합니다.")

    result = await app.ainvoke(initial_state, config=config)

    print("\n✅ 최종 분석 결과:")
    if result.get("messages"):
        final_message = result.get("messages", [])[-1]
        print(final_message.content)
    else:
        print("최종 메시지를 찾을 수 없습니다.")

    return result

if __name__ == "__main__":
    user_question = "화재가 난 것 같은데 무슨 상황인가요?"
    result = asyncio.run(run_workflow(user_question))
    print(result)