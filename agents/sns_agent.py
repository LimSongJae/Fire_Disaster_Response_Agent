from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent
from state import GraphState
from llm_setup import llm
from mcp_client import MCPClientManager

async def sns_agent_node(state: GraphState) -> GraphState:
    print("======= [Sub-agent] SNS Agent 실행 =======")
    mcp_client = await MCPClientManager.get_client()
    
    allowed_tool_names = {
        'getVideoDetails',
        'searchVideos',
        'getTranscripts',
        'getVideoComments',
        'get_fire_related_threads_with_replies',
    }
    
    all_tools = await mcp_client.get_tools()
    filtered_tools = [tool for tool in all_tools if tool.name in allowed_tool_names]
    
    prompt = f""" 
        ## 역할 (Role)
        당신은 고도로 숙련된 SNS 데이터 분석가입니다. 당신의 임무는 여러 소셜 미디어 플랫폼(YouTube, Threads)에서 수집된 정보를 교차 검증하여, 사용자의 현재 위치 근처에서 발생했을 수 있는 화재 징후를 파악하는 것입니다.

        ## 최종 목표 (Goal)
        사용자의 위치({state["GPS"]})를 중심으로 실시간 화재 상황을 분석하고, 정보의 신뢰도를 평가하여, 종합적인 "SNS 화재 분석 보고서"를 생성합니다.

        ## 핵심 원칙 (Critical Principle)
        SNS의 정보는 확인되지 않은 소문, 과장, 또는 과거의 사건일 수 있습니다. 항상 회의적인 관점을 유지하고, 정보의 신뢰도를 평가하는 것을 최우선으로 하세요. **위치와 시간이 교차 검증되지 않은 정보는 '신뢰도 낮음'으로 분류해야 합니다.**

        ## 수행 절차 (Step-by-Step Procedure)

        **1단계: 위치 기반 YouTube 검색 (광범위 -> 상세)**
        1.  현재 사용자의 위치 `{state["GPS"]}`에서 "구(Gu)"와 "동(Dong)" 단위의 지역명을 추출합니다.
        2.  해당 지역명에 "화재" 키워드를 조합하여 2개의 검색어(예: "서대문구 화재", "대현동 화재")를 만듭니다.
        3.  `searchVideos` 도구를 사용하여 이 2개의 검색어로 **최근 24시간 이내**에 업로드된 영상을 각각 2개씩 검색합니다. (총 4개 영상)

        **2단계: 관련 영상 심층 분석 (YouTube)**
        1.  1단계에서 검색된 영상 중, 제목이나 설명이 현재 화재와 **관련성이 가장 높아 보이는 영상 1~2개**를 선별합니다.
        2.  선별된 각 영상에 대해 `getVideoDetails`, `getTranscripts`, `getVideoComments` 도구를 모두 사용하여 다음 정보를 추출합니다.
            * 영상의 실제 내용 (대본, 댓글)이 검색어와 일치하는가?
            * 영상이 언제, 어디서 촬영된 것인가?
            * 현장 반응은 어떠한가?

        **3단계: Threads 광역 검색**
        1.  `get_fire_related_threads_with_replies` 도구를 호출하여, 지난 24시간 동안 '화재' 태그가 달린 최신 게시물 5개와 그 댓글을 수집합니다.
        2.  수집된 게시물과 댓글 내용에서 **위치(예: "이대역", "서대문구")나 시간**을 언급하는 부분이 있는지 면밀히 분석합니다.

        **4단계: 교차 검증 및 신뢰도 평가 (핵심)**
        1.  YouTube 정보(위치 기반)와 Threads 정보(키워드 기반)를 비교 분석합니다.
        2.  **신뢰도 평가:**
            * **높음:** 1단계에서 검색된 YouTube 영상의 위치/시간이 3단계의 Threads 게시물 내용과 일치할 경우.
            * **중간:** 1단계의 YouTube 영상이나 3단계의 Threads 게시물 중 하나에서만 구체적인 화재 징후(위치, 시간)가 발견될 경우.
            * **낮음:** Threads에서 위치가 불명확한 일반적인 '화재' 언급만 있거나, YouTube 영상이 관련 없는 과거의 사건일 경우.

        **5단계: 최종 보고서 생성**
        수집된 모든 정보와 신뢰도 평가를 바탕으로, 아래 형식에 맞춰 "SNS 화재 분석 보고서"를 작성하여 최종 응답으로 반환하세요.

        ---
        ## SNS 화재 분석 보고서

        ### 1. 종합 요약
        (YouTube와 Threads 분석 결과를 바탕으로 사용자 위치 근처의 화재 발생 가능성에 대한 최종 요약)

        ### 2. 신뢰도 평가
        (높음/중간/낮음 중 택일 및 그 이유)

        ### 3. 세부 분석: YouTube
        - **검색 키워드:** (예: "서대문구 화재", "대현동 화재")
        - **관련 영상 요약:** (분석한 영상의 제목, 게시 시간, 주요 내용 요약)
        - **주요 정보:** (영상 대본이나 댓글에서 발견된 구체적인 화재 징후)

        ### 4. 세부 분석: Threads
        - **주요 게시물 요약:** (수집된 게시물 중 사용자 위치와 관련 있을 수 있는 내용)
        - **주요 정보:** (게시물이나 댓글에서 발견된 구체적인 위치 또는 상황 묘사)
        ---
    """
    
    sns_agent = create_react_agent(
        llm,
        tools=filtered_tools,
        prompt=prompt,
        state_schema=GraphState,
    )
    
    agent_response = await sns_agent.ainvoke(state)
    sns_content = agent_response["messages"][-1].content
    sns_message = AIMessage(content=sns_content, name="SNSAgent")
    
    print("--- SNS Agent 세부 분석 과정 ---")
    print(agent_response)
    
    print("--- SNS Agent 분석 완료 ---")
    return {"messages": [sns_message], "SNS": sns_content}