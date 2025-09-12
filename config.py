import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# --- API Keys ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")

# --- Public Data API Keys ---
YONHAP_NEWS_API_KEY = os.getenv("YONHAP_NEWS_API_KEY")
DISASTER_MESSAGE_API_KEY = os.getenv("DISASTER_MESSAGE_API_KEY")
FOREST_FIRES_API_KEY = os.getenv("FOREST_FIRES_API_KEY")
KMA_WEATHER_API_KEY = os.getenv("KMA_WEATHER_API_KEY")

# --- Smithery (MCP) ---
SMITHERY_KEY = os.getenv("SMITHERY_KEY")
SMITHERY_PROFILE = os.getenv("SMITHERY_PROFILE")

# --- Model & LangGraph Settings ---
MODEL_NAME = "gpt-4o"
RECURSION_LIMIT = 50

# --- File Paths & Directories ---
PYTHON_EXECUTABLE_PATH = os.getenv("PYTHON_EXECUTABLE_PATH")
MCP_SERVER_SCRIPT_DIR = os.getenv("MCP_SERVER_SCRIPT_DIR")
CHROMA_DB_PATH = 'rag/chroma_db'
RAG_DOCUMENTS_PATH = 'rag/documents'

# --- MCP Server Script Paths ---
# MCP_SERVER_SCRIPT_DIR가 정의되지 않았을 경우를 대비한 예외 처리
if MCP_SERVER_SCRIPT_DIR:
    NEWS_MCP_SERVER_PATH = os.path.join(MCP_SERVER_SCRIPT_DIR, "news_mcp_server.py")
    GPS_MCP_SERVER_PATH = os.path.join(MCP_SERVER_SCRIPT_DIR, "GPS_mcp_server.py")
    DISASTER_MCP_SERVER_PATH = os.path.join(MCP_SERVER_SCRIPT_DIR, "public_disaster_mcp_server.py")
    SNS_MCP_SERVER_PATH = os.path.join(MCP_SERVER_SCRIPT_DIR, "SNS_mcp_server.py")
else:
    print("경고: MCP_SERVER_SCRIPT_DIR 환경변수가 설정되지 않았습니다. MCP 클라이언트가 정상 동작하지 않을 수 있습니다.")
    NEWS_MCP_SERVER_PATH, GPS_MCP_SERVER_PATH, DISASTER_MCP_SERVER_PATH, SNS_MCP_SERVER_PATH = [None] * 4

# 환경 변수 로드 확인
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다. .env 파일을 확인해주세요.")