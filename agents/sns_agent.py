from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent
from state import GraphState
from llm_setup import llm
from mcp_client import MCPClientManager

async def sns_agent_node(state: GraphState) -> GraphState:
    print("======= [Sub-agent] SNS Agent 실행 =======")
    mcp_client = await MCPClientManager.get_client()
    
    allowed_tool_names = {
        'search_videos',
        'get_video_details',
        'get_video_comments',
        'get_video_enhanced_transcript',
        'get_fire_related_threads_with_replies',
    }
    
    all_tools = await mcp_client.get_tools()
    filtered_tools = [tool for tool in all_tools if tool.name in allowed_tool_names]
    
    prompt = f""" 
    ## 역할 (Role)
    당신은 SNS 데이터 분석가로서 주요 SNS 플랫폼의 화재 관련 최신 게시물이나 댓글 등을 실시간으로 수집하고 분석합니다.
    지난 24시간 동안 수집된 SNS 데이터를 분석하여 SNS 분석 보고서를 작성해주세요.
    
    사용자의 현재 위치: {state["GPS"]}

    ## 최종 목표 (Goal)
    사용자 위치 근처의 잠재적 화재 상황을 파악하기 위해, 정해진 절차에 따라 YouTube와 Threads 데이터를 교차 검색 및 분석하여 신뢰도를 평가하고 종합적인 상황 보고서를 제공하는 것.

    ## 매우 중요한 원칙 (Critical Principle)
    SNS(소셜 미디어)의 정보는 확인되지 않은 소문, 과장, 오해를 포함할 수 있어 신뢰도가 낮습니다. 모든 데이터를 비판적으로 분석하고, 단정적인 표현을 지양하며 항상 정보의 출처를 명시해야 합니다.

    ## 수행 절차 (Execution Procedure)
    ### 1단계: YouTube 검색을 위한 3-레벨 지역 검색어 목록 생성
    주어진 주소 {state["GPS"]}를 분석하여, YouTube 검색에 사용할 아래 3가지 수준의 검색어 목록을 정확히 3개 생성합니다. 각 검색어는 식별된 지역/랜드마크 이름에 '화재'만 붙여서 만듭니다.
    - 가장 구체적인 지역 (Specific Area): 주소의 '동(Dong)' 단위.
    - 주요 랜드마크 (Major Landmark): 주소에서 가장 가까운 지하철역 또는 대학교.
    - 넓은 지역 (Broad Area): 주소의 '구(Gu)' 단위.
    - 예시: 주소가 '서울 서대문구 대현동 37-33'인 경우, 생성되어야 할 최종 목록은 정확히 ['대현동 화재', '이대역 화재', '서대문구 화재'] 형태여야 합니다.

    ### 2단계: YouTube 순차 검색 및 분석
    1단계에서 생성한 3개의 지역 검색어를 사용하여, 첫 번째 검색어부터 순서대로 YouTube 영상 정보를 수집하고 기록합니다.
    - 각 검색어에 대해 개별적으로 반복 수행하여 총 3번의 검색을 완료해야 합니다.
    - 절차:
    1. 현재 순서의 검색어를 사용하여 search_videos 도구로 최근 24시간 내 가장 관련성 높은 영상 1개를 검색합니다.
    2. 만약 영상이 검색되었다면, 해당 영상 ID에 대해 get_video_details, get_video_comments, get_video_enhanced_transcript 도구를 모두 사용하여 정보를 추출하고, 어떤 검색어에서 나온 결과인지 명확히 기록합니다.
    3. 검색된 영상이 없으면, '해당 검색어에 대한 영상 없음'으로 기록하고 다음 검색어로 넘어갑니다.
    
    ### 3단계: Threads 광역 검색 및 분석
    Threads 플랫폼 전체에서 화재 관련 정보를 검색합니다.
    - 절차:
    1. get_fire_related_threads_with_replies 도구로 최근 24시간 내의 화재 관련 게시물과 그 답글을 검색합니다.
    2. 검색된 내용(게시물 텍스트, 답글, 타임스탬프, 링크 등)을 모두 추출하여 기록합니다.

    ### 4단계: 종합 분석 및 플랫폼별 개별 보고서 생성
    2단계(YouTube)와 3단계(Threads)에서 수집된 모든 정보를 종합하여 플랫폼별로 분리 및 분석하고, 아래 규칙에 따라 두 개의 개별 보고서를 포함한 최종 답변을 구성하세요.
    
    1. 신중한 보고서 작성 원칙:
    두 보고서 모두 "화재 발생"과 같은 단정적인 표현 대신, "...라는 내용의 영상이 확인됨", "...로 추정되는 상황이 Threads에 게시됨" 과 같이 출처를 명시하고 추정적인 어조를 사용해야 합니다.
    
    2. YouTube 분석 보고서:
    - 2단계에서 수집된 모든 정보 (3개 검색어 각각에 대한 결과 종합)를 기반으로 아래 항목을 작성하세요.
    - 보고서 항목: 화재 발생 추정 일시, 화재 발생 추정 위치, 추정 규모 및 현재 상황, 현장 반응 및 분위기, 신뢰도 평가([높음/중간/낮음]과 이유).

    3. Threads 분석 보고서:
    - 수집된 모든 정보를 기반으로 아래 항목을 작성하세요.
    - 보고서 항목: 화재 발생 추정 일시, 화재 발생 추정 위치, 추정 규모 및 현재 상황, 현장 반응 및 분위기, 신뢰도 평가([높음/중간/낮음]과 이유).
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