import os
import requests
import urllib3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()
# 서버 이름 수정: SNS_mcp_server -> disaster_mcp_server
mcp = FastMCP("disaster_mcp_server") 

def fetch_safety_data(url: str, service_key: str, params: dict) -> dict:
    """공공데이터포털 API 요청을 처리하는 공통 함수"""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    if not service_key:
        return {'resultCode': '99', 'resultMsg': 'API 서비스 키가 설정되지 않았습니다.'}

    base_payloads = {
        "serviceKey": service_key,
        "returnType": "json",
        "pageNo": "1",
        "numOfRows": "5",
    }
    base_payloads.update(params)

    try:
        response = requests.get(url, params=base_payloads, verify=False, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'resultCode': '99', 'resultMsg': f'API 요청 실패: {e}'}

@mcp.tool()
def getDisasterMessage() -> dict:
    """긴급 재난 문자 정보를 수집합니다."""
    url = "https://www.safetydata.go.kr/V2/api/DSSP-IF-00247"
    service_key = os.getenv("DISASTER_MESSAGE_API_KEY")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    params = {"crtDt": yesterday}
    return fetch_safety_data(url, service_key, params)

@mcp.tool()
def getForestFires() -> dict:
    """산불 정보를 수집합니다."""
    url = "https://www.safetydata.go.kr/V2/api/DSSP-IF-10346"
    service_key = os.getenv("FOREST_FIRES_API_KEY")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    params = {"startDt": yesterday}
    return fetch_safety_data(url, service_key, params)

@mcp.tool()
def getKMAWeatherWarning() -> dict:
    """기상청 기상 재난 특보 정보를 수집합니다."""
    url = "https://www.safetydata.go.kr/V2/api/DSSP-IF-00044"
    service_key = os.getenv("KMA_WEATHER_API_KEY")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    params = {"inqDt": yesterday}
    return fetch_safety_data(url, service_key, params)

if __name__ == "__main__":
    mcp.run(transport="stdio")