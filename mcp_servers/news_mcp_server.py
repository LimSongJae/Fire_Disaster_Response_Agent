# news_mcp_server.py (scrape 도구 추가 완료)

import os
import json
import requests
import urllib3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from typing import Dict
from firecrawl import Firecrawl

# --- 경로 설정 및 .env 로드 ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

mcp = FastMCP("news_mcp_server")

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# --- 기존 도구 (get_naver_news) ---
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

# --- 기존 도구 (get_yonhap_news) ---
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

# --- (신규) Serper.dev 뉴스 검색 도구 ---
@mcp.tool()
def scrape(url: str) -> str:
    """
    뉴스 기사 본문만 JSON으로 추출 (가장 단순/안정 버전).
    - DOM 1차 필터: only_main_content / include_tags / exclude_tags
    - LLM 2차 정제: JSON 포맷 + 간단 스키마 + 가드레일 프롬프트
    - 항상 문자열(JSON)로 반환하여 MCP 호환
    """
    if not FIRECRAWL_API_KEY:
        return json.dumps(
            {"status": "error", "message": "FIRECRAWL_API_KEY가 .env 파일에 없습니다."},
            ensure_ascii=False, indent=2
        )

    try:
        firecrawl = Firecrawl(api_key=FIRECRAWL_API_KEY)

        # 최소 JSON 스키마 (Pydantic 불필요)
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": ["string", "null"]},
                "published_at": {"type": ["string", "null"]},
                "body": {"type": "string"},
                "paragraphs": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["body"]
        }

        guardrail = (
            "Return ONLY the news article's main body as JSON. "
            "Preserve original order and line breaks. "
            "Do NOT summarize, translate, or add text. "
            "Exclude headers, nav, footers, sidebars, ads, sponsored/related boxes, "
            "comments, author bio, newsletter/subscription, and paywalls. "
            "If title or published date are not obvious, set them to null."
        )

        doc = firecrawl.scrape(
            url=url,
            formats=[{"type": "json", "schema": schema, "prompt": guardrail}],
            # ↓↓↓ 파이썬 SDK는 스네이크 케이스 ↓↓↓
            only_main_content=True,
            include_tags=["article", "main"],
            exclude_tags=[
                "nav", "footer", "aside",
                ".ad", ".ads", ".advert", ".advertisement",
                ".sponsored", ".promo", ".related",
                ".comments", "#comments",
                ".newsletter", ".subscription", ".paywall"
            ],
            # 캐시 무시하고 최신이 필요하면 0, 아니면 생략
            max_age=0
            # 필요 시 위치/언어도 가능: location={"country":"KR","languages":["ko","en"]}
        )

        result = {
            "status": "ok",
            "url": url,
            "extracted": getattr(doc, "json", None)  # 본문은 여기로 반환됨
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps(
            {"status": "error", "message": f"Firecrawl 스크래핑 중 예외 발생: {e}"},
            ensure_ascii=False, indent=2
        )


if __name__ == "__main__":
    mcp.run(transport="stdio")