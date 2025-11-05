import streamlit as st
import asyncio

# 1. 기존에 만든 AI 에이전트 워크플로우 함수를 가져옵니다.
from main import run_workflow 

# --- Streamlit 페이지 설정 ---
st.set_page_config(
    page_title="🚨 재난 대응 AI 에이전트",
    page_icon="🔥",
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("🔥 재난 대응 AI 에이전트")
st.caption("현재 위치를 기반으로 실시간 재난 정보를 분석합니다.")

# --- 채팅 메모리 관리 ---
# Streamlit의 세션 상태(st.session_state)를 사용하여 채팅 기록을 관리합니다.
if "messages" not in st.session_state:
    st.session_state.messages = []

# 각 사용자/세션별 고유 ID를 생성합니다. (메모리 기능에 사용)
# 여기서는 간단하게 세션 ID를 하나로 고정합니다.
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "streamlit-user-123" # 고정된 세션 ID

# --- 채팅 기록 표시 ---
# 이전 대화 내용을 순서대로 화면에 표시합니다.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 사용자 입력 처리 ---
# 사용자가 채팅 입력창에 메시지를 입력하고 엔터를 누르면...
if prompt := st.chat_input("궁금한 재난 상황을 입력하세요 (예: 강남역 근처 화재)"):
    
    # 1. 사용자 메시지를 채팅 기록에 추가하고 화면에 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. AI 응답 생성 (기다리는 동안 스피너 표시)
    with st.chat_message("assistant"):
        with st.spinner("AI 에이전트가 분석 중입니다... (최대 1분 소요)"):
            try:
                # 비동기 함수(run_workflow)를 Streamlit에서 실행
                # ⭐️ 중요: Streamlit은 asyncio 루프가 이미 실행 중일 수 있으므로 
                # asyncio.run() 대신 await을 사용하거나 새 루프를 관리해야 합니다.
                # 가장 간단한 방법은 asyncio.run()을 사용하는 것입니다.
                response = asyncio.run(
                    run_workflow(prompt, thread_id=st.session_state.thread_id)
                )
            except Exception as e:
                response = f"죄송합니다. 오류가 발생했습니다: {e}"
        
        # 3. AI 응답을 화면에 표시하고 채팅 기록에 추가
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})