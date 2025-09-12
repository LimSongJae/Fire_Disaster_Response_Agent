from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from config import CHROMA_DB_PATH, OPENAI_API_KEY

def initialize_vector_store():
    """
    저장된 ChromaDB를 로드하여 Retriever 객체를 생성하고 반환합니다.
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")

    embedding_model = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    
    try:
        vectorstore = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=embedding_model
        )
        print("RAG Retriever가 성공적으로 준비되었습니다.")
        return vectorstore.as_retriever(search_kwargs={"k": 5})
    except Exception as e:
        print(f"ChromaDB 로드 중 오류 발생: {e}")
        print(f"'{CHROMA_DB_PATH}' 경로에 DB 파일이 존재하는지 확인하거나, 'build_vector_store.py'를 실행하여 DB를 생성해주세요.")
        return None

# 모듈 로드 시 Retriever 인스턴스 생성
retriever = initialize_vector_store()