import asyncio
from langchain_core.messages import HumanMessage
from graph import app
from config import RECURSION_LIMIT

async def run_workflow(question: str, thread_id: str):
    """워크플로우를 실행하고 최종 결과를 반환합니다."""
    
    config = {
        "recursion_limit": RECURSION_LIMIT, 
        "configurable": {"thread_id": thread_id}
    }

    # initial_state = {
    #     "messages": [HumanMessage(content=question)],
    #     "question": question,
    #     "use_agent": False,
    #     "agent_visited": False,
    #     "news": "",
    #     "GPS": "",
    #     "disaster": "",
    #     "SNS": "",
    #     "rag_context": "",
    #     "structured_response": None,
    #     "remaining_steps": 15,
    # }
    
    # Checkpointer가 thread_id를 보고 이전 대화 기록을 알아서 불러옵니다.
    input_data = {"messages": [HumanMessage(content=question)]}
    
    print(f"\n🚀 [Thread ID: {thread_id}] 질문: '{question}'에 대한 분석을 시작합니다.")
    
    
    try:
        result = await app.ainvoke(input_data, config=config)
        
        if result.get("messages"):
            final_message = result.get("messages", [])[-1]
            return final_message.content
        else:
            return "응답을 생성할 수 없습니다."
    except Exception as e:
        print(f"❌ 워크플로우 실행 중 오류 발생: {e}")
        return f"오류 발생: {str(e)}"

def main():
    """메인 대화 루프"""
    print("="*50)
    print("🚨 재난 대응 AI 에이전트 🚨")
    print("="*50)
    print("종료하려면 'exit' 또는 'quit'를 입력하세요.\n")
    
    thread_id = "interactive-session"
    
    while True:
        try:
            user_question = input("\n👤 사용자: ").strip()
            
            if user_question.lower() in ['exit', 'quit', '종료']:
                print("\n👋 재난 대응 AI를 종료합니다. 안전한 하루 되세요!")
                # 정리 작업
                break
            
            if not user_question:
                print("⚠️  질문을 입력해주세요.")
                continue
            
            response = asyncio.run(run_workflow(user_question, thread_id))
            print(f"\n🤖 AI: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 프로그램을 종료합니다...")
            break
        except Exception as e:
            print(f"\n❌ 오류: {e}")
            print("다시 시도해주세요.")

if __name__ == "__main__":
    main()