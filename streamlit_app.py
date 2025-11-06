import streamlit as st
import asyncio
from main import run_workflow

st.set_page_config(page_title="🚨 재난 대응 AI 에이전트", page_icon="🔥", layout="centered")
st.title("🔥 재난 대응 AI 에이전트")
st.caption("현재 위치를 기반으로 실시간 재난 정보를 분석합니다.")

# --- 상태 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "streamlit-user-1234"

# --- 입력 ---
prompt = st.chat_input("궁금한 재난 상황을 입력하세요 (예: 강남역 근처 화재)")
if prompt:
    # (1) 새 유저 메시지
    st.session_state.messages.append({"role": "user", "content": prompt})
    # (2) 어시스턴트 '빈 슬롯' (펜딩 표시)
    st.session_state.messages.append({"role": "assistant", "content": None})
    st.rerun()

msgs = st.session_state.messages

# 펜딩 여부: 맨 끝이 assistant(None)
has_pending = (
    len(msgs) >= 1 and msgs[-1]["role"] == "assistant" and msgs[-1]["content"] is None
)

# --- 렌더링 ---
def render_message(m):
    with st.chat_message(m["role"], avatar=("👤" if m["role"]=="user" else "🤖")):
        st.markdown(m["content"])

if not has_pending:
    # 평상시: 전체 히스토리 렌더
    for m in msgs:
        render_message(m)
else:
    # 펜딩 시: "직전 어시스턴트"를 임시로 숨기고(중복/회색 유령 방지)
    # 전체 -2까지(직전 assistant 이전까지) 렌더
    for m in msgs[:-2]:
        render_message(m)

    # 방금 입력한 유저 메시지만 보여줌
    with st.chat_message("user", avatar="👤"):
        st.markdown(msgs[-2]["content"])

    # 펜딩 말풍선(아바타 다르게 해서 재조합 위험 더 낮춤)
    with st.chat_message("assistant", avatar="⏳"):
        with st.spinner("AI 에이전트가 분석 중입니다..."):
            try:
                response = asyncio.run(
                    run_workflow(msgs[-2]["content"], thread_id=st.session_state.thread_id)
                )
            except Exception as e:
                response = f"죄송합니다. 오류가 발생했습니다: {e}"
        st.markdown(response)

    # 빈 슬롯을 실제 응답으로 치환
    st.session_state.messages[-1]["content"] = response
    # (선택) 다음 런에서 정상 아바타(🤖)로 히스토리 정렬하고 싶으면:
    st.rerun()