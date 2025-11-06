from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent
from state import GraphState
from llm_setup import llm
from mcp_client import MCPClientManager

async def new_agent_node(state: GraphState) -> GraphState:
    print("======= [Sub-agent] News Agent 실행 =======")
    mcp_client = await MCPClientManager.get_client()
    
    allowed_tool_names = {
        "get_naver_news",
        # "firecrawl_scrape",
        "get_yonhap_news",
        "scrape",
    }

    all_tools = await mcp_client.get_tools()
    filtered_tools = [tool for tool in all_tools if tool.name in allowed_tool_names]
    
    prompt = f"""
    당신은 화재 뉴스 데이터 분석가로서 국내 주요 언론사의 화재 재난 관련 최신 뉴스를 실시간으로 수집하고 분석합니다.
    사용자의 현재 위치: {state["GPS"]}
    사용자의 현재 위치를 기반으로 지난 24시간 동안 수집된 화재 재난 뉴스 데이터를 분석하여 화재 뉴스 분석 보고서를 작성해주세요.
    
    ## 뉴스데이터 수집 및 분석 지시사항
    1. 'get_naver_news' tool을 사용하여 한국의 화재 관련 네이버 뉴스를 2건 검색하세요.
    2. 검색 결과에서 나온 네이버 뉴스 2건의 URL(link)들을 'scrape' tool을 사용하여 전체 기사 내용을 추출하세요.
    3. 'get_yonhap_news' tool을 사용하여 한국의 화재 관련 연합 뉴스를 5건 검색하세요.
    4. 수집한 뉴스 기사들을 기반으로 분석하세요.
    """
    
    news_agent = create_react_agent(
        llm,
        tools=filtered_tools,
        prompt=prompt,
        state_schema=GraphState,
    )
    
    agent_response = await news_agent.ainvoke(state)
    news_content = agent_response["messages"][-1].content
    news_message = AIMessage(content=news_content, name="NewsAgent")
    
    print("--- News Agent 세부 분석 과정 ---")
    print(agent_response)
    
    print("--- News Agent 분석 완료 ---")
    return {"messages": [news_message], "news": news_content}