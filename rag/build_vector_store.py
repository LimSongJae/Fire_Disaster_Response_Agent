import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from config import RAG_DOCUMENTS_PATH, CHROMA_DB_PATH, OPENAI_API_KEY

def build_and_save_vector_store():
    """
    지정된 디렉토리의 텍스트 파일을 로드하여 ChromaDB 벡터 스토어를 생성하고 저장합니다.
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
    
    print(f"1. '{RAG_DOCUMENTS_PATH}' 디렉토리에서 텍스트 파일을 로드합니다...")
    loader = DirectoryLoader(
        RAG_DOCUMENTS_PATH,
        glob="**/*.txt",
        loader_cls=TextLoader,
        show_progress=True
    )
    docs = loader.load()
    if not docs:
        print(f"경고: '{RAG_DOCUMENTS_PATH}' 디렉토리에서 문서를 찾을 수 없습니다.")
        return
    print(f"총 {len(docs)}개의 문서를 로드했습니다.\n")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    print("2. 텍스트를 청크 단위로 분할합니다...")
    splits = text_splitter.split_documents(docs)
    print(f"총 {len(splits)}개의 청크로 분할되었습니다.\n")

    embedding_model = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    
    print(f"3. 임베딩 및 ChromaDB 저장을 시작합니다... (저장 경로: {CHROMA_DB_PATH})")
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embedding_model,
        persist_directory=CHROMA_DB_PATH
    )
    print("ChromaDB에 성공적으로 저장했습니다.\n")

if __name__ == "__main__":
    # 이 스크립트를 직접 실행하면 벡터 DB를 생성/업데이트합니다.
    build_and_save_vector_store()