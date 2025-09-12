from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent
from state import GraphState
from llm_setup import llm
from mcp_client import MCPClientManager

async def disaster_agent_node(state: GraphState) -> GraphState:
    print("======= [Sub-agent] Disaster Agent 실행 =======")
    mcp_client = await MCPClientManager.get_client()
    
    allowed_tool_names = {
        'getDisasterMessage',
        'getForestFires',
        'getKMAWeatherWarning',
    }
    
    all_tools = mcp_client.get_tools()
    filtered_tools = [tool for tool in all_tools if tool.name in allowed_tool_names]
    
    prompt = f"""
    [역할] 당신은 재난 데이터를 분석하는 데이터 사이언티스트입니다.
    [목표] 지난 24시간 동안 수집된 재난 관련 데이터의 패턴을 분석하고, 데이터 간의 연관성을 파악하여 위험 요소를 도출하고자 합니다.
    [데이터]
    1. 긴급 재난 문자 (getDisasterMessage)
    2. 산불 정보 (getForestFires)
    3. 기상청 기상특보 (getKMAWeatherWarning)
    
    [분석 요청]
    모든 도구를 사용하여 데이터를 수집한 후, 아래 분석을 수행해주세요.
    
    1. 개별 데이터 심층 분석:
    - 재난 문자: 유형별(실종, 호우, 안전안내 등) 발송 빈도와 주요 발송 지역(시/군/구 단위)을 분석해주세요.
    - 산불 정보: 발생 시간대별 분포와 지역별 발생 건수를 분석하고, '진화 완료'와 '진행 중' 상태를 구분하여 요약해주세요.
    - 기상 특보: 특보 종류(호우, 건조, 강풍 등)별 발효 지역의 면적 또는 수를 기준으로 위험 순위를 매겨주세요.
    
    2. 융합 분석 및 결과:
    - 상관관계 분석: 특정 기상특보(예: 건조주의보)가 발효된 지역에서 산불 발생 빈도가 유의미하게 높은지 분석해주세요.
    - 공간 분석: 위 3가지 재난 데이터가 특정 지역에 중첩되어 나타나는 '위험 핫스팟'이 있는지 분석해주세요.
    
    3. 종합 결론:
    - 분석 결과를 종합하여, 현재 가장 시급하게 대응해야 할 재난 유형과 그에 따른 위험 지역을 구체적으로 명시해주세요.
    """
    
    disaster_agent = create_react_agent(
        llm,
        tools=filtered_tools,
        state_modifier=prompt,
        state_schema=GraphState,
    )
    
    agent_response = await disaster_agent.ainvoke(state)
    disaster_content = agent_response["messages"][-1].content
    disaster_message = AIMessage(content=disaster_content, name="DisasterAgent")
    
    print("--- Disaster Agent 세부 분석 과정 ---")
    print(agent_response)
    
    print("--- Disaster Agent 분석 완료 ---")
    return {"messages": [disaster_message], "disaster": disaster_content}