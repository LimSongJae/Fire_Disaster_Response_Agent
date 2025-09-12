from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage
from mcp_client import MCPClientManager

from state import GraphState
from llm_setup import llm
from rag.vector_store import retriever

class UserInteractionResponse(BaseModel):
    use_agent: bool = Field(..., description="사용자 질문에 대해 화재 재난대응 Agent System 사용이 필요한지 여부를 판단")

async def user_interaction_node(state: GraphState) -> GraphState:
    """
    사용자의 초기 질문을 분석하거나, 모든 정보가 수집된 후 최종 답변을 생성합니다.
    agent_visited 상태에 따라 두 가지 다른 작업을 수행합니다.
    """
    if state.get("agent_visited", False):
        return await _generate_final_response(state)
    else:
        return await _initial_analysis(state)

async def _initial_analysis(state: GraphState) -> GraphState:
    """초기 사용자 질문을 분석하여 에이전트 시스템 사용 여부를 결정합니다."""
    print("\n======= [Node] User Interaction Agent (초기 분석) 실행 =======")
    
    prompt = f"""당신은 화재 재난 분석 시스템의 사용자 인터페이스 에이전트입니다.
    
    사용자의 질문을 분석하여 다음 두 가지를 수행하세요:
    1. 재난 대응 Agent System 사용 필요 여부 판단
    2. 적절한 응답 생성
    
    ### 재난 대응 Agent System 개요
    - SNS, GPS, 재난 공공 데이터, 뉴스 데이터들을 수집하여 현 재난재해 상황을 분석함
    - 사용자의 위치를 고려하여 어떻게 대응해야하는지에 대한 중요한 정보를 수집하고 분석하여 제공
    
    현재 사용자 질문: "{state.get('question', '')}"
    """

    user_interaction_agent = create_react_agent(
        llm,
        tools=[],
        state_modifier=prompt,
        state_schema=GraphState,
        response_format=UserInteractionResponse,
    )
    
    agent_response = await user_interaction_agent.ainvoke(state)
    structured_response = agent_response["structured_response"]
    
    print("--- User Interaction Agent 세부 분석 과정 ---")
    print(agent_response)
    
    final_message = AIMessage(
        content=agent_response["messages"][-1].content,
        name="UserInterfaceAgent"
    )
    
    return {
        "messages": [final_message],
        "use_agent": structured_response.use_agent
    }

async def _generate_final_response(state: GraphState) -> GraphState:
    """모든 에이전트의 분석 결과를 종합하고 RAG 검색을 통해 최종 답변을 생성합니다."""
    print("\n======= [Node] User Interaction Agent (최종 답변 생성) 실행 =======")
    print("재난 분석 완료. RAG 시스템을 조회하여 최종 답변을 생성합니다...")
    
    mcp_client = await MCPClientManager.get_client()
    
    allowed_tool_names = {
        'sequentialthinking_tools',
    }
    
    all_tools = mcp_client.get_tools()
    filtered_tools = [tool for tool in all_tools if tool.name in allowed_tool_names]

    refined_query = f"""
    현재 상황: {state.get('news', '')} {state.get('disaster', '')}
    사용자 위치: {state.get('GPS', '')}
    질문: "{state.get('question', '')}"
    이 상황과 위치를 고려했을 때 가장 적절한 행동 요령이나 참고할 만한 과거 화재 사례를 알려줘.
    """

    retrieved_docs = await retriever.ainvoke(refined_query)
    rag_context = "\n\n---\n\n".join([doc.page_content for doc in retrieved_docs])
    
    print("\n--- RAG 검색 결과 일부 ---")
    print(rag_context[:500] + "...")
    print("--------------------------\n")

    final_prompt = f"""
    당신은 대한민국 최고의 화재 재난 대응 전문가입니다.
    아래에 주어진 모든 정보를 종합하여, 사용자의 질문에 대해 가장 안전하고 실행 가능한 구체적인 행동 방안을 단계별로 명확하게 제시하세요.
    Let's think step by step using mcp-sequentialthinking-tools.
    
    ## 최종 임무
    **현재 재난 상황**과 **사용자의 위치**를 최우선으로 고려하여, **RAG 시스템이 제공한 전문 지식**을 바탕으로 맞춤형 대응 방안을 생성해야 합니다. 단순히 정보를 나열하지 말고, 사용자가 지금 당장 무엇을 해야 하는지 명확히 알려주세요.

    ## 사용자 질문
    "{state.get('question', '')}"

    ## 실시간 분석 데이터
    - **사용자 GPS 정보**: {state.get('GPS', '위치 정보 없음')}
    - **뉴스 데이터 분석**: {state.get('news', '수집된 정보 없음')}
    - **재난 공공 데이터 분석**: {state.get('disaster', '수집된 정보 없음')}
    - **SNS 데이터 분석**: {state.get('SNS', '수집된 정보 없음')}
    
    ## RAG 시스템 검색 결과 (화재 대응 매뉴얼 및 과거 사례)
    {rag_context}
    """

    final_agent = create_react_agent(
        llm,
        tools=filtered_tools,
        state_modifier=final_prompt,
        state_schema=GraphState,
    )
    
    final_response = await final_agent.ainvoke(state)
    final_content = final_response["messages"][-1].content
    final_message = AIMessage(content=final_content, name="FinalResponseAgent")
    
    print("--- FinalResponseAgent 세부 분석 과정 ---")
    print(final_response)

    return {
        "messages": [final_message],
        "rag_context": rag_context,
    }