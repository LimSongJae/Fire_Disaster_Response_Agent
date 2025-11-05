import os
import json
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from typing import Dict, List, Any

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

mcp = FastMCP("SNS_mcp_server")

BASE_URL = "https://graph.threads.net/v1.0"

def _get_replies_for_thread(media_id: str, access_token: str) -> List[Dict[str, Any]]:
    """주어진 게시물 ID에 대한 댓글(답글) 목록을 가져오는 헬퍼 함수입니다."""
    url = f"{BASE_URL}/{media_id}/replies"
    params = {
        'access_token': access_token,
        'fields': 'id,text,timestamp,author_id,permalink'
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            return response.json().get('data', [])
    except requests.exceptions.RequestException:
        pass
    return []

@mcp.tool()
def get_fire_related_threads_with_replies() -> str:
    """
    '화재' TAG가 포함된 최신 Threads 게시물과 각 게시물의 댓글을 검색합니다.
    지난 24시간 동안 작성된 최신 게시물 5개를 검색하고, 댓글과 함께 반환합니다.
    """
    ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
    if not ACCESS_TOKEN:
        error_message = {"error": "THREADS_ACCESS_TOKEN이 .env 파일에 설정되지 않았습니다."}
        return json.dumps(error_message, indent=2, ensure_ascii=False)

    until_time = datetime.now(timezone.utc)
    since_time = until_time - timedelta(days=1)
    since_timestamp = int(since_time.timestamp())
    until_timestamp = int(until_time.timestamp())

    search_url = f"{BASE_URL}/keyword_search"
    search_params = {
        'q': '화재',
        'search_mode': 'TAG',
        'search_type': 'RECENT',
        'access_token': ACCESS_TOKEN,
        'fields': 'id,text,timestamp,author_id,permalink,media_type',
        'since': since_timestamp,
        'until': until_timestamp
    }
    
    final_result = []
    try:
        response = requests.get(search_url, params=search_params, timeout=10)
        
        if response.status_code != 200:
            error_details = response.json()
            error_message = {"error": f"API 요청 실패 (상태 코드: {response.status_code})", "details": error_details}
            return json.dumps(error_message, indent=2, ensure_ascii=False)

        threads = response.json().get('data', [])
        if not threads:
            return json.dumps({"message": "'화재' 관련 게시물을 찾을 수 없습니다."}, indent=2, ensure_ascii=False)

        for thread in threads[:5]:
            thread_id = thread.get('id')
            if thread_id:
                replies = _get_replies_for_thread(thread_id, ACCESS_TOKEN)
                thread['replies'] = replies
            final_result.append(thread)

    except requests.exceptions.RequestException as e:
        error_message = {"error": "네트워크 오류", "details": str(e)}
        return json.dumps(error_message, indent=2, ensure_ascii=False)
    
    return json.dumps(final_result, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    mcp.run(transport="stdio")