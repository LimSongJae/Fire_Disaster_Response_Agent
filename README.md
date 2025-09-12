# 재난 대응 AI 에이전트 (Disaster Response AI Agent)

LangGraph를 활용한 실시간 정보 분석 및 맞춤형 대응 가이드 시스템

## 📖 프로젝트 소개

본 프로젝트는 화재와 같은 긴급 재난 상황에서 사용자의 안전을 지키기 위해 설계된 지능형 AI 에이전트 시스템입니다. LangGraph를 기반으로 한 멀티 에이전트 아키텍처를 통해, 실시간으로 뉴스, SNS, 공공 재난 데이터를 수집 및 분석하고 사용자의 위치에 맞는 최적의 행동 요령을 제공합니다.
RAG(Retrieval-Augmented Generation) 기술을 접목하여 과거 재난 사례와 공식 대응 매뉴얼을 기반으로 답변을 생성함으로써, 신뢰도 높은 맞춤형 안전 가이드를 제공하는 것을 목표로 합니다.

## ✨ 주요 기술 스택

Orchestration: LangChain, LangGraph
LLM: OpenAI GPT-4o
Vector Database (RAG): ChromaDB
Tool Servers: Multi-Server MCP Client, Python Scripts
Configuration: python-dotenv

## 🚀 핵심 기능

🤖 멀티 에이전트 협업: 각기 다른 전문성을 가진 에이전트(뉴스, SNS, 공공 데이터)가 병렬로 정보를 수집하고 분석하여 신속한 의사결정을 지원합니다.
📍 위치 기반 맞춤형 정보: 사용자의 GPS 정보를 바탕으로 가장 관련성 높은 재난 정보를 필터링하고 지역 맞춤형 대응 방안을 제시합니다.
⏱️ 실시간 데이터 분석: 최신 뉴스, SNS 게시물, 정부 재난문자 등을 실시간으로 분석하여 급변하는 재난 상황을 정확하게 판단합니다.
📚 RAG 기반 전문 지식: 사전 구축된 재난 대응 매뉴얼 DB를 활용하여, LLM의 환각(Hallucination) 현상을 최소화하고 답변의 신뢰성과 전문성을 확보합니다.
🔐 안전한 키 관리: 모든 API 키는 .env 파일로 분리하여 관리하므로, 코드의 보안성이 높습니다.

## ⚙️ 시스템 작동 흐름

본 시스템은 Supervisor-Worker 패턴을 따르며, 다음과 같은 단계로 작동합니다.
초기 분석: User Interaction Agent가 사용자의 질문 의도를 파악하여 재난 대응 시스템의 필요성을 판단합니다.
정보 수집 (병렬 처리): Supervisor Agent가 GPS 정보를 확보한 뒤, News, SNS, Disaster 에이전트를 동시에 실행하여 각 분야의 정보를 신속하게 수집 및 분석합니다.
정보 종합 및 최종 답변: 모든 정보가 취합되면, User Interaction Agent가 RAG 시스템을 통해 전문 지식을 조회하고, 수집된 모든 실시간 정보를 종합하여 최종적인 맞춤형 대응 가이드를 생성합니다.

## 🛠️ 시작하기

1. 프로젝트 복제
   git clone [https://github.com/your-username/Disaster_Response_Agent.git](https://github.com/your-username/Disaster_Response_Agent.git)
   cd Disaster_Response_Agent

2. 의존성 설치
   Python 가상 환경을 생성하고, 필요한 라이브러리를 설치합니다.
   python -m venv venv
   source venv/bin/activate # macOS/Linux

# venv\Scripts\activate # Windows

pip install -r requirements.txt

3. 환경 변수 설정
   .env.example 파일을 복사하여 .env 파일을 생성하고, 파일 내부에 본인의 API 키와 경로를 입력합니다.
   cp .env.example .env

⚠️ 경고: .env 파일은 민감한 정보를 담고 있으므로 절대 Git에 커밋하지 마세요. .gitignore에 이미 포함되어 있습니다. 4. RAG 벡터 데이터베이스 구축
프로젝트에 사용할 매뉴얼, 사례집 등 .txt 파일을 rag/documents/ 디렉토리에 넣은 후, 아래 명령어를 실행하여 벡터 DB를 생성합니다.
python -m rag.build_vector_store

5. 프로젝트 실행
   모든 설정이 완료되면, 메인 파일을 실행하여 에이전트를 시작합니다.
   python main.py

main.py 파일 내의 user_question 변수를 수정하여 다양한 시나리오를 테스트할 수 있습니다.

## 📂 프로젝트 구조

.
├── agents/ # 각 에이전트의 로직 정의
├── mcp_servers/ # 도구로 사용될 MCP 서버 스크립트
├── rag/ # RAG 관련 파일 (DB 생성, 로드, 문서)
├── .env.example # 환경 변수 견본 파일
├── .gitignore # Git 추적 제외 목록
├── README.md # 프로젝트 설명서
├── config.py # 설정 및 환경 변수 로드
├── graph.py # LangGraph 워크플로우 정의
├── llm_setup.py # LLM 모델 초기화
├── main.py # 메인 실행 파일
├── mcp_client.py # MCP 클라이언트 관리
├── requirements.txt # Python 의존성 목록
└── state.py # LangGraph 상태 정의

## 💡 향후 개선 방향

웹 UI 적용: Streamlit 또는 Gradio를 활용하여 사용자와 상호작용할 수 있는 인터페이스 개발
에이전트 기능 확장: 교통 정보, 대피소 정보 등 새로운 도구를 추가하여 에이전트 능력 강화
결과 캐싱: 동일한 질문이나 상황에 대해 LLM 호출을 최소화하기 위한 캐싱 시스템 도입
