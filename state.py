from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class GraphState(TypedDict):
    """
    LangGraph의 각 노드 간에 전달되는 상태를 정의합니다.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    question: str
    news: str
    GPS: Dict[str, Any]
    SNS: str
    disaster: str
    use_agent: bool
    agent_visited: bool
    rag_context: str
    remaining_steps: int
    structured_response: Any