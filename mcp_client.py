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
                cls.client = MultiServerMCPClient({
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
                    # "mcp-server-serper": {
                    #     "command": "npx",
                    #     "args": [
                    #         "-y",
                    #         "@smithery/cli@latest",
                    #         "run",
                    #         "@marcopesani/mcp-server-serper",
                    #         "--key",
                    #         "484ebb5c-bd4f-4247-a1c6-e1223235a463",
                    #         "--profile",
                    #         "independent-ocelot-465lJ3"
                    #     ],
                    #     "transport": "stdio",
                    # },
                    # "firecrawl-mcp-server": { serper 사용, firecrawl 사용 x
                    #     "command": "npx",
                    #     "args": [
                    #         "-y",
                    #         "@smithery/cli@latest",
                    #         "run",
                    #         "@Krieg2065/firecrawl-mcp-server",
                    #         "--key",
                    #         "484ebb5c-bd4f-4247-a1c6-e1223235a463",
                    #         "--profile",
                    #         "independent-ocelot-465lJ3"
                    #     ],
                    #     "transport": "stdio",
                    # },
                    # "server-sequential-thinking": {
                    #     "command": "npx",
                    #     "args": [
                    #         "-y",
                    #         "@smithery/cli@latest",
                    #         "run",
                    #         "@smithery-ai/server-sequential-thinking",
                    #         "--key",
                    #         "484ebb5c-bd4f-4247-a1c6-e1223235a463",
                    #         "--profile",
                    #         "independent-ocelot-465lJ3"
                    #     ],
                    #     "transport": "stdio",
                    # },
                })
            except Exception as e:
                print(f"MCP 클라이언트 초기화 오류: {e}")
                raise
        return cls.client

    @classmethod
    async def close(cls):
        """MCP 클라이언트 연결을 종료합니다."""
        if cls.client:
            # 새로운 API에서는 별도의 종료 메서드가 필요할 수 있습니다
            cls.client = None