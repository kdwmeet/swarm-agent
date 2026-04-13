import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import app_graph

st.set_page_config(page_title="Swarm 아키텍처", layout="wide")

st.title("중앙 통제가 없는 Swarm 아키텍처 (Handoff)")
st.markdown("에이전트들이 동등한 위치에서 대화 문맥을 파악하고, 필요에 따라 다른 전문 에이전트에게 제어권을 직접 넘겨줍니다.")
st.divider()

# 세션 ID 설정
config = {"configurable": {"thread_id": "swarm_session_1"}}

# 현재 상태으 ㅣ대화 기록 불러오기
try:
    current_state = app_graph.get_state(config)
    chat_history = current_state.values.get("messages", []) if current_state and hasattr(current_state, 'values') else []
except Exception:
    chat_history = []

col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("에이전트 네트워크 구성")
    st.markdown("- **안내 데스크(Triage):** 초기 접수 및 부서 연결")
    st.markdown("- **영업(Sales):** 제품 추천 및 구매 상담")
    st.markdown("- **지원(Support):** 고장 수리 및 기술 상담")

    if st.button("대화 세션 초기화", use_container_width=True):
        import uuid
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

with col1:
    st.subheader("고객 센터 채팅")

    # 이전 대화 출력
    for msg in chat_history:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.write(msg.content)
        elif isinstance(msg, AIMessage):
            agent_name = msg.name.upper() if msg.name else "SYSTEM"
            with st.chat_message("assistant"):
                st.markdown(f"**[{agent_name}]**")
                st.write(msg.content)
        
    user_input = st.chat_input("메시지를 입력하십시오.")
    
    if user_input:
        with st.chat_message("user"):
            st.write(user_input)

        with st.spinner("에이전트 네트워크가 응답을 처리 중입니다..."):
            input_date = {"messages": [HumanMessage(content=user_input)]}

            # 스트리밍 결과 순회
            for output in app_graph.stream(input_date, config, stream_mode="updates"):
                # 방어 로직: Null Check 적용
                if not output:
                    continue

                for node_name, state_update in output.items():
                    if not state_update:
                        continue

                    messages = state_update.get("messages", [])
                    if messages:
                        latest_msg = messages[-1]
                        with st.chat_message("assistant"):
                            st.markdown(f"**[{node_name.upper()}]**")
                            st.write(latest_msg.content)

        st.rerun()