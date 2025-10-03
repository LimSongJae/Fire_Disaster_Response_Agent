import sqlite3
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from state import GraphState
from agents.user_interaction_agent import user_interaction_node
from agents.supervisor_agent import supervisor_node


def trim_messages(state: GraphState) -> GraphState:
    """
    메시지 기록이 너무 길어지면 가장 오래된 메시지를 잘라냅니다.
    여기서는 최근 10개의 메시지만 유지하도록 설정합니다.
    """
    stored_messages = state.get("messages", [])
    if len(stored_messages) > 10:
        print("--- 메시지 기록이 10개를 초과하여 오래된 기록을 삭제합니다. ---")
        # 가장 최근 10개의 메시지만 남깁니다.
        state["messages"] = stored_messages[-10:]
    return state

# --- 메모리 설정 ---
# 👈 2. MemorySaver 인스턴스를 생성합니다. 매우 간단합니다.
memory = MemorySaver()

# --- 분기 로직 (기존과 동일) ---
def user_interface_agent_path(state: GraphState) -> str:
    """
    User_Interaction_Agent의 결과에 따라 다음 노드를 결정합니다.
    """
    if state.get("agent_visited", False):
        print("모든 에이전트 분석 완료. 최종 답변 생성이 끝났으므로 워크플로우를 종료합니다.")
        return "FINISH"
    
    if state.get("use_agent", False):
        print("판단: AI 에이전트 시스템 사용이 필요합니다. Supervisor 노드로 이동합니다.")
        return "use"
    
    print("판단: AI 에이전트 시스템 사용이 필요하지 않습니다. 워크플로우를 종료합니다.")
    return "not_use"

# --- 워크플로우 정의 (기존과 동일) ---
workflow = StateGraph(GraphState)
workflow.add_node("trim_messages", trim_messages)
workflow.add_node("User_Interaction_Agent", user_interaction_node)
workflow.add_node("Supervisor", supervisor_node)
workflow.set_entry_point("trim_messages")
workflow.add_edge("trim_messages", "User_Interaction_Agent")
workflow.add_conditional_edges(
    "User_Interaction_Agent",
    user_interface_agent_path,
    {
        "use": "Supervisor",
        "not_use": END,
        "FINISH": END
    }
)
workflow.add_edge("Supervisor", "User_Interaction_Agent")

# --- 그래프 컴파일 (기존과 동일) ---
# 👈 3. checkpointer에 MemorySaver 인스턴스를 전달합니다.
app = workflow.compile(checkpointer=memory)
print("✅ LangGraph App이 MemorySaver와 함께 성공적으로 컴파일되었습니다.")