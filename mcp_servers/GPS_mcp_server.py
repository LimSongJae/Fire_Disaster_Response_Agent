import os
import json
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from typing import Dict

# .env 파일에서 환경 변수를 로드
load_dotenv()

mcp = FastMCP("GPS_mcp_server")

def get_address_from_coords(latitude: float, longitude: float, rest_api_key: str) -> str:
    """카카오 지도 API를 통해 좌표를 주소로 변환합니다."""
    url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
    headers = {"Authorization": f"KakaoAK {rest_api_key}"}
    params = {"x": longitude, "y": latitude}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status() # 200 OK가 아니면 예외 발생
        
        documents = response.json().get('documents', [])
        if documents:
            return documents[0]['address']['address_name']
        else:
            return "주소 정보를 찾을 수 없습니다."
    except requests.exceptions.RequestException as e:
        return f"API 요청 실패: {e}"

@mcp.tool()
def get_latest_location() -> Dict:
    """최신 사용자 위치 정보와 카카오 주소 반환"""
    try:
        with open("mcp_servers/location.json", "r") as f:
            data = json.load(f)
        latitude = data['latitude']
        longitude = data['longitude']
    except FileNotFoundError:
        return {"success": False, "message": "위치 데이터 파일(location.json)을 찾을 수 없습니다."}
    except (json.JSONDecodeError, KeyError) as e:
        return {"success": False, "message": f"위치 데이터 파일 형식 오류: {e}"}

    KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
    if not KAKAO_REST_API_KEY:
        return {"success": False, "message": "KAKAO_REST_API_KEY가 .env 파일에 설정되지 않았습니다."}

    address = get_address_from_coords(latitude, longitude, KAKAO_REST_API_KEY)
    return {"address": address}

if __name__ == "__main__":
    mcp.run(transport="stdio")