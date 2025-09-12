from langchain_openai import ChatOpenAI
from config import MODEL_NAME, OPENAI_API_KEY

def initialize_llm():
    """
    ChatOpenAI 모델을 초기 설정과 함께 반환합니다.
    자동 재시도 기능이 활성화되어 있습니다.
    """
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API 키가 설정되지 않았습니다.")

    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0,
        max_retries=6,  # 오류 발생 시 6번까지 자동 재시도
        request_timeout=50,
        api_key=OPENAI_API_KEY
    )
    return llm

# 모듈 로드 시 LLM 인스턴스 생성
llm = initialize_llm()