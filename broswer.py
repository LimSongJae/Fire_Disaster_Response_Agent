#!/usr/bin/env python3
"""
웹 서버 - 위치 수집하여 파일 저장
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import json
import uuid
import uvicorn

app = FastAPI()

class LocationData(BaseModel):
    latitude: float
    longitude: float
    accuracy: float

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>위치 수집</title>
    <meta charset="UTF-8">
</head>
<body>
    <h1>위치 수집 시스템</h1>
    <button onclick="getLocation()">위치 가져오기</button>
    <div id="status"></div>
    <div id="result"></div>

    <script>
        function getLocation() {
            document.getElementById('status').innerHTML = '위치 수집 중...';
            
            navigator.geolocation.getCurrentPosition(async (position) => {
                const data = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy
                };
                
                const response = await fetch('/save-location', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                document.getElementById('status').innerHTML = '완료!';
                document.getElementById('result').innerHTML = 
                    `위도: ${data.latitude}<br>경도: ${data.longitude}<br>ID: ${result.id}`;
            });
        }
    </script>
</body>
</html>
    """

@app.post("/save-location")
async def save_location(location: LocationData):
    # 파일에 저장
    data = {
        "id": str(uuid.uuid4()),
        "latitude": location.latitude,
        "longitude": location.longitude,
        "accuracy": location.accuracy,
    }
    
    with open("location.json", "w") as f:
        json.dump(data, f)
    
    print(f"위치 저장: {data['latitude']}, {data['longitude']}")
    return {"success": True, "id": data["id"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)