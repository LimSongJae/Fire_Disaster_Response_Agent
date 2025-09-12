from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent
from state import GraphState
from llm_setup import llm
from mcp_client import MCPClientManager

async def new_agent_node(state: GraphState) -> GraphState:
    print("======= [Sub-agent] News Agent 실행 =======")
    mcp_client = await MCPClientManager.get_client()
    
    # ❗ [수정] News Agent가 사용할 도구 목록을 명확하게 정의합니다.
    allowed_tool_names = {
        "get_naver_news",
        "scrape", # get_naver_news 결과의 URL을 스크레이핑하기 위해 필요
        "get_yonhap_news"
    }

    # ❗ [수정] 전체 도구에서 필요한 도구만 필터링합니다.
    all_tools = mcp_client.get_tools()
    filtered_tools = [tool for tool in all_tools if tool.name in allowed_tool_names]
    
    prompt = f"""
    당신은 '화재 재난 대응을 위한 뉴스 데이터 수집 및 분석 에이전트'입니다.
    사용자의 현재 위치: {state["GPS"]}
    
    ## 당신의 핵심 임무
    사용자의 현재 위치를 기반으로 긴급한 화재 재난 상황에 즉시 대응할 수 있는 맞춤형 정보를 신속하게 제공하는 것입니다.
    국내 주요 언론사의 화재 재난 관련 최신 뉴스를 실시간으로 수집하고 분석합니다.
    분석할때 요약하지 말고 최대한 세부적인 사항까지 분석해주세요.
    
    ## 뉴스데이터 수집 및 분석 지시사항
    1. 'get_naver_news' tool을 사용하여 한국의 화재 관련 네이버 뉴스를 2건 검색하세요.
    2. 검색 결과에서 나온 네이버 뉴스 2건의 URL(link)들을 'scrape' tool을 사용하여 전체 기사 내용을 추출하세요.
    3. 'get_yonhap_news' tool을 사용하여 한국의 화재 관련 연합 뉴스를 5건 검색하세요.
    4. 수집한 뉴스 기사들을 기반으로 '답변 구성 원칙'에 따라 분석하세요. 단, 재난 상황으로 판단되지 않을 경우, '답변 구성 원칙'을 적용하지 않고 "현재 재난 상황으로 판단되지 않습니다."라고 답변합니다.
    
    ## 답변 구성 원칙 (재난 상황에만 적용)
    ### 의도 이해 및 핵심 답변
    - 사용자의 질문에서 드러나는 긴급한 재난 상황과 내포된 구체적인 필요사항을 정확히 파악합니다.
    - 가장 중요한 핵심 답변부터 명료하게 제시하여, 사용자가 혼란스러운 상황에서도 정보를 즉시 인지하고 활용할 수 있도록 합니다.
    ### 객관적이고 신뢰할 수 있는 데이터 기반
    - 제공하는 모든 정보는 수집된 뉴스 데이터 등 구체적인 사실 데이터에 근거합니다.
    - 추측이나 일반론적인 내용은 배제하고, 검증된 사실만을 바탕으로 답변을 구성합니다.
    - 정보의 출처와 업데이트 시각을 명확히 명시합니다.
    ### 즉시 실행 가능한 맞춤형 행동 지침
    - 사용자의 현재 위치와 재난 상황에 가장 적합한, 당장 취할 수 있는 구체적인 행동 단계와 조언을 명확하고 단계별로 제시합니다.
    ### 포괄적이고 완결성 있는 정보 제공
    - 재난 상황에서 사용자가 필요로 할 만한 모든 관련 정보를 빠짐없이, 한 번에 제공합니다.
    ### 환각 방지 및 최신성 확보
    - 사실에 기반하지 않은 정보, 유추된 내용, 잘못된 경로는 절대 제공하지 않습니다.
    - 데이터가 불충분하여 답변이 어려울 경우, 정보의 한계를 명확히 밝힙니다.
    """
    
    news_agent = create_react_agent(
        llm,
        tools=filtered_tools,
        state_modifier=prompt,
        state_schema=GraphState,
    )
    
    agent_response = await news_agent.ainvoke(state)
    news_content = agent_response["messages"][-1].content
    news_message = AIMessage(content=news_content, name="NewsAgent")
    
    print("--- News Agent 세부 분석 과정 ---")
    print(agent_response)
    
    print("--- News Agent 분석 완료 ---")
    return {"messages": [news_message], "news": news_content}