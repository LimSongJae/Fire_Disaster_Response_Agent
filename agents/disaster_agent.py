from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent
from state import GraphState
from llm_setup import llm
from mcp_client import MCPClientManager

async def disaster_agent_node(state: GraphState, tools) -> GraphState:
    print("======= [Sub-agent] Disaster Agent 실행 =======")
    
    prompt = f"""
    당신은 공공 화재 재난 데이터 분석가 입니다.
    지난 24시간 동안 수집된 화재 재난 관련 데이터를 분석하여 공공 화재 재난 데이터 분석 보고서를 작성해주세요.
    
    수집 및 분석할 데이터의 종류
    1. 긴급 재난 문자 (getDisasterMessage)
    2. 산불 정보 (getForestFires)
    3. 기상청 기상특보 (getKMAWeatherWarning)
    """
    
    disaster_agent = create_react_agent(
        llm,
        tools=tools,
        prompt=prompt,
        state_schema=GraphState,
    )
    
    agent_response = await disaster_agent.ainvoke(state)
    disaster_content = agent_response["messages"][-1].content
    disaster_message = AIMessage(content=disaster_content, name="DisasterAgent")
    
    print("--- Disaster Agent 세부 분석 과정 ---")
    print(agent_response)
    
    print("--- Disaster Agent 분석 완료 ---")
    return {"messages": [disaster_message], "disaster": disaster_content}