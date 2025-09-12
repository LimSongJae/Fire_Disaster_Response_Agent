from langgraph.graph import StateGraph, START, END
from state import GraphState
from agents.user_interaction_agent import user_interaction_node
from agents.supervisor_agent import supervisor_node

# --- 분기 로직 ---
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

# --- 워크플로우 정의 ---
workflow = StateGraph(GraphState)

# 노드 추가
workflow.add_node("User_Interaction_Agent", user_interaction_node)
workflow.add_node("Supervisor", supervisor_node)

# 엣지(연결) 설정
workflow.set_entry_point("User_Interaction_Agent")

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

# 그래프 컴파일
app = workflow.compile()