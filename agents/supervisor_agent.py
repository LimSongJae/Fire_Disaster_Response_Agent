import asyncio
from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from state import GraphState
from llm_setup import llm
from mcp_client import MCPClientManager
from .news_agent import new_agent_node
from .sns_agent import sns_agent_node
from .disaster_agent import disaster_agent_node

class GPSResponse(BaseModel):
    address: str = Field(..., description="사용자의 현재 위치 주소")

async def supervisor_node(state: GraphState) -> GraphState:
    print("\n======= [Node] Supervisor 실행 시작 =======")
    
    mcp_client = await MCPClientManager.get_client()
    
    # 1. GPS 정보 수집
    print("--- 1. GPS 정보 수집 시작 ---")

    all_tools = await mcp_client.get_tools()
    gps_tool = [tool for tool in all_tools if tool.name == "get_latest_location"]

    gps_agent = create_react_agent(
        llm,
        tools=gps_tool, # 필터링된 gps_tool을 전달
        prompt="get_latest_location 도구를 사용해 사용자의 현재 GPS 기반 주소를 찾아주세요.",
        state_schema=GraphState,
        response_format=GPSResponse,
    )
    gps_response = await gps_agent.ainvoke(state)
    gps_data = {"address": gps_response["structured_response"].address}
    print(f"--- GPS 정보 수집 완료: {gps_data['address']} ---")
    
    # 현재 상태를 복사하고 수집된 GPS 정보를 추가
    current_state = state.copy()
    current_state['GPS'] = gps_data
    
    # 2. 하위 에이전트 병렬 실행
    print("\n--- 2. 하위 에이전트 병렬 실행 ---")
    parallel_results = await asyncio.gather(
        new_agent_node(current_state),
        sns_agent_node(current_state),
        disaster_agent_node(current_state),
        return_exceptions=True
    )
    print("--- 모든 하위 에이전트 병렬 실행 완료 ---\n")
    
    # 3. 모든 결과 병합
    print("--- 3. 모든 결과 병합 ---")
    for agent_result in parallel_results:
        
        if isinstance(agent_result, Exception):
            # 에러가 발생한 경우, 로그를 남기고 다음 결과로 넘어갑니다.
            print(f"🚨 [Supervisor] 하위 에이전트 실행 중 오류 발생: {agent_result}")
            continue
        
        # 상태 업데이트: 키가 존재하는 경우에만 값을 업데이트
        if agent_result.get("news") is not None:
            current_state['news'] = agent_result["news"]
        if agent_result.get("SNS") is not None:
            current_state['SNS'] = agent_result["SNS"]
        if agent_result.get("disaster") is not None:
            current_state['disaster'] = agent_result["disaster"]
        # messages는 LangGraph의 add_messages가 자동으로 처리하므로 직접 추가할 필요가 없습니다.

    current_state['agent_visited'] = True

    return current_state