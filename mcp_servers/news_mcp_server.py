import os
import requests
import urllib3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()
mcp = FastMCP("news_mcp_server")

@mcp.tool()
def get_naver_news(query: str, display: int = 10, start: int = 1, sort: str = "sim") -> dict:
    """네이버 검색 API를 사용하여 뉴스를 검색합니다."""
    url = "https://openapi.naver.com/v1/search/news.json"
    
    params = {'query': query, 'display': display, 'start': start, 'sort': sort}
    
    headers = {
        'X-Naver-Client-Id': os.getenv("NAVER_CLIENT_ID"),
        'X-Naver-Client-Secret': os.getenv("NAVER_CLIENT_SECRET")
    }
    
    if not headers['X-Naver-Client-Id'] or not headers['X-Naver-Client-Secret']:
        return {'status': 'error', 'message': '네이버 API 키가 .env 파일에 설정되지 않았습니다.'}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'status': 'error', 'message': str(e)}

@mcp.tool()
def get_yonhap_news() -> dict:
    """연합 뉴스를 검색합니다 (공공데이터포털)"""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    url = "https://www.safetydata.go.kr/V2/api/DSSP-IF-00051"
    serviceKey = os.getenv("YONHAP_NEWS_API_KEY")
    if not serviceKey:
        return {'status': 'error', 'message': '연합뉴스 API 키가 .env 파일에 설정되지 않았습니다.'}
        
    inquiry_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    
    payloads = {
        "serviceKey": serviceKey,
        "returnType": "json",
        "pageNo": "1",
        "numOfRows": "5",
        "inqDt": inquiry_date
    }

    try:
        response = requests.get(url, params=payloads, verify=False, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'status': 'error', 'message': str(e)}

if __name__ == "__main__":
    mcp.run(transport="stdio")