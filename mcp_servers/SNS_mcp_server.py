# SNS_mcp_server.py (YouTube 도구 추가 버전)

import os
import json
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from typing import Dict, List, Any, Optional

# --- 새로운 Import ---
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi

# --- 경로 설정 및 .env 로드 ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

mcp = FastMCP("SNS_mcp_server")

# --- YouTube API 헬퍼 ---
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def get_youtube_service():
    """Google API 클라이언트 서비스 객체를 생성하여 반환합니다."""
    if not YOUTUBE_API_KEY:
        # API 키가 없으면 에러를 발생시키지 않고, 도구 사용 시 에러를 반환하도록 합니다.
        return None
    try:
        service = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY)
        return service
    except Exception as e:
        print(f"❌ YouTube 서비스 빌드 중 오류 발생: {e}")
        return None

# --- Threads 도구 (기존과 동일) ---
THREADS_BASE_URL = "https://graph.threads.net/v1.0"

def _get_replies_for_thread(media_id: str, access_token: str) -> List[Dict[str, Any]]:
    """주어진 게시물 ID에 대한 댓글(답글) 목록을 가져오는 헬퍼 함수입니다."""
    url = f"{THREADS_BASE_URL}/{media_id}/replies"
    params = {'access_token': access_token, 'fields': 'id,text,timestamp,author_id,permalink'}
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            return response.json().get('data', [])
    except requests.exceptions.RequestException:
        pass
    return []

# @mcp.tool()
# def get_fire_related_threads_with_replies() -> str:
#     """
#     '화재' TAG가 포함된 최신 Threads 게시물과 각 게시물의 댓글을 검색합니다.
#     지난 24시간 동안 작성된 최신 게시물 5개를 검색하고, 댓글과 함께 반환합니다.
#     """
#     ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
#     if not ACCESS_TOKEN:
#         error_message = {"error": "THREADS_ACCESS_TOKEN이 .env 파일에 설정되지 않았습니다."}
#         return json.dumps(error_message, indent=2, ensure_ascii=False)

#     until_time = datetime.now(timezone.utc)
#     since_time = until_time - timedelta(days=1)
    
#     search_url = f"{THREADS_BASE_URL}/keyword_search"
#     search_params = {
#         'q': '화재',
#         'search_mode': 'TAG',
#         # 'search_type': 'RECENT',
#         'access_token': ACCESS_TOKEN,
#         'fields': 'id,text,timestamp,author_id,permalink,media_type',
#         'since': int(since_time.timestamp()),
#         'until': int(until_time.timestamp())
#     }
    
#     final_result = []
#     try:
#         response = requests.get(search_url, params=search_params, timeout=10)
#         response.raise_for_status() # 오류 발생 시 예외
        
#         threads = response.json().get('data', [])
#         if not threads:
#             return json.dumps({"message": "'화재' 관련 게시물을 찾을 수 없습니다."}, indent=2, ensure_ascii=False)

#         for thread in threads[:5]: # 5개로 제한
#             thread_id = thread.get('id')
#             if thread_id:
#                 replies = _get_replies_for_thread(thread_id, ACCESS_TOKEN)
#                 thread['replies'] = replies
#             final_result.append(thread)

#     except requests.exceptions.RequestException as e:
#         error_message = {"error": f"Threads API 요청 실패: {e}", "details": e.response.text if e.response else "N/A"}
#         return json.dumps(error_message, indent=2, ensure_ascii=False)
    
#     return json.dumps(final_result, indent=2, ensure_ascii=False)

@mcp.tool()
def get_fire_related_threads_with_replies(start_date: str, end_date: str, max_results: int = 5) -> str:
    """
    '화재' TAG가 포함된 최신 Threads 게시물을 검색합니다.
    API에서 받아온 데이터를 'start_date'와 'end_date' 사이의 기간으로 필터링합니다.
    :param start_date: 검색 시작일 (YYYY-MM-DD 형식의 문자열)
    :param end_date: 검색 종료일 (YYYY-MM-DD 형식의 문자열)
    :param max_results: 반환할 최대 결과 수 (기본 5)
    """
    ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
    if not ACCESS_TOKEN:
        error_message = {"error": "THREADS_ACCESS_TOKEN이 .env 파일에 설정되지 않았습니다."}
        return json.dumps(error_message, indent=2, ensure_ascii=False)

    # 1. 입력받은 날짜 문자열을 timezone-aware datetime 객체로 변환
    try:
        # start_date는 해당 날짜의 00:00:00 UTC부터
        since_time_utc = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        # end_date는 해당 날짜의 23:59:59 UTC까지 포함
        until_time_utc = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)) - timedelta(seconds=1)
        until_time_utc = until_time_utc.replace(tzinfo=timezone.utc)
    except ValueError:
        return json.dumps({"error": "날짜 형식이 잘못되었습니다. 'YYYY-MM-DD' 형식을 사용하세요."}, indent=2, ensure_ascii=False)

    search_url = f"{THREADS_BASE_URL}/keyword_search"
    search_params = {
        'q': '화재',
        'search_mode': 'TAG',
        'search_type': 'RECENT', # API는 시간 필터를 무시하므로, 일단 최신순으로 받음
        'access_token': ACCESS_TOKEN,
        'fields': 'id,text,timestamp,author_id,permalink,media_type',
        'limit': 5 # 👈 필터링을 위해 API가 허용하는 최대치(5)까지 요청
    }
    
    final_result = []
    try:
        response = requests.get(search_url, params=search_params, timeout=10)
        response.raise_for_status() # 오류 발생 시 예외
        
        threads = response.json().get('data', [])
        if not threads:
            return json.dumps({"message": "'화재' 관련 게시물을 찾을 수 없습니다."}, indent=2, ensure_ascii=False)

        # --- 2. API가 시간 필터링을 안 해주므로, 여기서 직접 필터링 ---
        for thread in threads:
            if len(final_result) >= max_results: # 원하는 결과 수를 채우면 중단
                break
            
            try:
                # API에서 받은 timestamp (예: "2025-09-09T02:04:52+0000")를 datetime 객체로 변환
                post_time_utc = datetime.fromisoformat(thread['timestamp'])
                
                # 3. 게시물 시간이 우리가 지정한 기간 내에 있는지 확인
                if since_time_utc <= post_time_utc <= until_time_utc:
                    thread_id = thread.get('id')
                    if thread_id:
                        replies = _get_replies_for_thread(thread_id, ACCESS_TOKEN)
                        thread['replies'] = replies
                    final_result.append(thread)
                        
            except (KeyError, ValueError, TypeError):
                # timestamp 형식이 잘못되었거나 없는 경우 건너뜀
                continue 
        # --- 필터링 끝 ---

        if not final_result:
            return json.dumps({"message": f"'{start_date}'부터 '{end_date}' 사이의 '화재' 관련 게시물을 찾을 수 없습니다."}, indent=2, ensure_ascii=False)

    except requests.exceptions.RequestException as e:
        details = "N/A"
        if e.response:
            try:
                details = e.response.json() # JSON 에러가 있다면 포함
            except json.JSONDecodeError:
                details = e.response.text # JSON이 아니면 텍스트로
        error_message = {"error": f"Threads API 요청 실패: {e}", "details": details}
        return json.dumps(error_message, indent=2, ensure_ascii=False)
    
    return json.dumps(final_result, indent=2, ensure_ascii=False)

# --- (신규) YouTube 도구 4개 ---

@mcp.tool()
def searchVideos(query: str, max_results: int = 5, order: str = "date") -> dict:
    """
    쿼리 문자열을 기반으로 YouTube 동영상을 검색합니다. (search.list)
    최근 24시간 이내의 영상을 검색하려면 'publishedAfter'를 사용하세요.
    :param query: 검색할 키워드 (예: "서울역 화재")
    :param max_results: 반환할 최대 결과 수 (기본 5)
    :param order: 정렬 순서 (기본 'date', 'relevance', 'viewCount' 등)
    """
    youtube = get_youtube_service()
    if not youtube:
        return {"error": "YOUTUBE_API_KEY가 설정되지 않았거나 서비스 초기화에 실패했습니다."}
    
    try:
        # 24시간 이내 검색을 위한 시간 계산
        twenty_four_hours_ago = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

        search_response = youtube.search().list(
            q=query,
            part="snippet",
            maxResults=max_results,
            order=order,
            type="video",
            publishedAfter=twenty_four_hours_ago # 24시간 이내로 제한
        ).execute()
        return search_response
    except HttpError as e:
        return {"error": f"YouTube API 오류: {e.resp.status} {e.content.decode()}"}
    except Exception as e:
        return {"error": f"searchVideos 실행 중 알 수 없는 오류: {str(e)}"}

@mcp.tool()
def getVideoDetails(video_ids: List[str]) -> dict:
    """
    하나 이상의 video ID 목록을 받아, 해당 동영상들의 세부 정보(통계, 콘텐츠 세부정보 포함)를 반환합니다. (videos.list)
    :param video_ids: YouTube 비디오 ID의 리스트 (예: ["videoId1", "videoId2"])
    """
    youtube = get_youtube_service()
    if not youtube:
        return {"error": "YOUTUBE_API_KEY가 설정되지 않았거나 서비스 초기화에 실패했습니다."}
        
    try:
        video_response = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=",".join(video_ids) # API는 콤마로 구분된 문자열을 받음
        ).execute()
        return video_response
    except HttpError as e:
        return {"error": f"YouTube API 오류: {e.resp.status} {e.content.decode()}"}
    except Exception as e:
        return {"error": f"getVideoDetails 실행 중 알 수 없는 오류: {str(e)}"}

@mcp.tool()
def getVideoComments(video_id: str, max_results: int = 10) -> dict:
    """
    특정 YouTube 동영상의 댓글(최상위 댓글)을 검색합니다. (commentThreads.list)
    :param video_id: 댓글을 수집할 비디오의 ID
    :param max_results: 반환할 최대 댓글 수 (기본 10)
    """
    youtube = get_youtube_service()
    if not youtube:
        return {"error": "YOUTUBE_API_KEY가 설정되지 않았거나 서비스 초기화에 실패했습니다."}
        
    try:
        comment_response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_results,
            textFormat="plainText",
            order="relevance" # 관련성 순 (또는 'time'으로 최신순)
        ).execute()
        return comment_response
    except HttpError as e:
        # 403 에러는 댓글이 비활성화된 경우가 많음
        if e.resp.status == 403:
            return {"error": "이 동영상은 댓글이 비활성화되어 있습니다.", "items": []}
        return {"error": f"YouTube API 오류: {e.resp.status} {e.content.decode()}"}
    except Exception as e:
        return {"error": f"getVideoComments 실행 중 알 수 없는 오류: {str(e)}"}

@mcp.tool()
def getTranscripts(video_id: str) -> dict:
    """
    YouTube 동영상의 자막(transcript)을 수집합니다. 한국어를 우선 시도하고, 없으면 영어로 대체합니다.
    (YouTube Data API가 아닌 'youtube-transcript-api' 라이브러리 사용)
    :param video_id: 자막을 수집할 비디오의 ID
    """
    try:
        # 한국어를 먼저 시도, 없으면 영어, 둘 다 없으면 자동 생성된 한국어 시도
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en', 'a.ko'])
        # 모든 자막 텍스트를 하나의 긴 문자열로 합칩니다.
        full_transcript = " ".join([item['text'] for item in transcript_list])
        return {"videoId": video_id, "transcript": full_transcript}
    except Exception as e:
        # (예: TranscriptsDisabled, NoTranscriptFound, VideoUnavailable 등)
        return {"videoId": video_id, "error": f"자막을 가져올 수 없습니다: {str(e)}"}


if __name__ == "__main__":
    mcp.run(transport="stdio")