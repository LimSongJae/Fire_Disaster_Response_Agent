import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from config import (
    PYTHON_EXECUTABLE_PATH,
    NEWS_MCP_SERVER_PATH,
    GPS_MCP_SERVER_PATH,
    DISASTER_MCP_SERVER_PATH,
    SNS_MCP_SERVER_PATH,
    SMITHERY_KEY,
    SMITHERY_PROFILE
)

class MCPClientManager:
    """
    MultiServerMCPClient 인스턴스를 싱글톤으로 관리하는 클래스입니다.
    애플리케이션 전체에서 단 하나의 클라이언트 연결을 유지합니다.
    """
    _instance = None
    client = None

    @classmethod
    async def get_client(cls):
        """
        MCP 클라이언트 인스턴스를 비동기적으로 생성하고 반환합니다.
        이미 인스턴스가 존재하면 기존 인스턴스를 반환합니다.
        """
        if cls.client is None:
            if not all([PYTHON_EXECUTABLE_PATH, NEWS_MCP_SERVER_PATH, GPS_MCP_SERVER_PATH, DISASTER_MCP_SERVER_PATH, SNS_MCP_SERVER_PATH]):
                 raise ValueError("MCP 서버 실행에 필요한 경로가 .env 파일에 올바르게 설정되지 않았습니다.")
            
            try:
                cls.client = await MultiServerMCPClient({
                    "news_mcp_server": {
                        "command": PYTHON_EXECUTABLE_PATH,
                        "args": [NEWS_MCP_SERVER_PATH],
                        "transport": "stdio",
                    },
                    "GPS_mcp_server": {
                        "command": PYTHON_EXECUTABLE_PATH,
                        "args": [GPS_MCP_SERVER_PATH],
                        "transport": "stdio",
                    },
                    "disaster_mcp_server": {
                        "command": PYTHON_EXECUTABLE_PATH,
                        "args": [DISASTER_MCP_SERVER_PATH],
                        "transport": "stdio",
                    },
                    "SNS_mcp_server": {
                        "command": PYTHON_EXECUTABLE_PATH,
                        "args": [SNS_MCP_SERVER_PATH],
                        "transport": "stdio",
                    },
                    "mcp-server-serper": {
                        "command": "npx",
                        "args": ["-y", "@smithery/cli@latest", "run", "@marcopesani/mcp-server-serper", "--key", SMITHERY_KEY, "--profile", SMITHERY_PROFILE],
                        "transport": "stdio",
                    },
                    "py-mcp-youtube-toolbox": {
                        "command": "npx",
                        "args": ["-y", "@smithery/cli@latest", "run", "@jikime/py-mcp-youtube-toolbox", "--key", SMITHERY_KEY, "--profile", SMITHERY_PROFILE],
                        "transport": "stdio",
                    },
                    "mcp-sequentialthinking-tools": {
                        "command": "npx",
                        "args": [
                            "-y",
                            "@smithery/cli@latest",
                            "run",
                            "@xinzhongyouhai/mcp-sequentialthinking-tools",
                            "--key",
                            SMITHERY_KEY
                        ],
                        "transport": "stdio",
                    },
                }).__aenter__()
            except Exception as e:
                print(f"MCP 클라이언트 초기화 오류: {e}")
                raise
        return cls.client

    @classmethod
    async def close(cls):
        """MCP 클라이언트 연결을 종료합니다."""
        if cls.client:
            await cls.client.__aexit__(None, None, None)
            cls.client = None