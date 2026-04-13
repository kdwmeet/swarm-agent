from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# Pydantic 스키마 정의
class AgentOutput(BaseModel):
    content: str = Field(description="사용자에게 전달할 실제 답변 내용. 제어권을 넘길 경우 상황을 안내하는 짧은 메시지를 작성하십시오.")
    handoff: Literal["triage", "sales", "support", "none"] = Field(
        description="다른 에이전트의 도움이 필요할 경우 해당 에이전트를 선택하십시오. 자신이 충분히 답변했거나 대화를 이어가야 한다면 'none'을 선택하십시오."
    )

# 상태 정의
class SwarmState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    active_agent: str

# 노드 구현 (개별 에이전트)
def create_agent_node(agent_name: str, system_prompt: str):
    """각 에이전트 노드를 생성하는 팩토리 함수입니다."""
    def agent_node(state: SwarmState):
        llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
        structured_llm = llm.with_structured_output(AgentOutput)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages")
        ])

        messages = state.get("messages", [])
        response: AgentOutput = (prompt | structured_llm).invoke({"messages": messages})

        msg = AIMessage(content=response.content, name=agent_name)

        # 제어권 이관(handoff) 여부에 딸 ㅏ다음 활성 에이전트 상태를 업데이트
        next_agnet = response.handoff if response.handoff != "none" else "end"

        return {"messages": [msg], "active_agent": next_agnet}
    
    return agent_node

# 안내 데스크 에이전트 (초기 접수 및 라우팅 전담)
triage_prompt = """당신은 고객 센터의 '안내 데스크(triage)' 에이전트입니다.
사용자의 요청을 분석하여, 제품 구매나 가격 문의는 'sales'로, 제품 고장이나 기술 지원은 'support'로 제어권을 넘기십시오.
간단한 인사나 부서 안내는 직접 처리하고 'none'을 반환하십시오."""
triage_node = create_agent_node("triage", triage_prompt)

# 영업 에이전트
sales_prompt = """당신은 '영업(sales)' 에이전트입니다. 제품 추천, 가격, 할인 혜택에 대해 친절하게 안내하십시오.
만약 사용자가 이미 구매한 제품의 수리나 기술적 문제를 묻는다면 'support'로 제어권을 넘기십시오.
직접 답변을 제공했다면 'none'을 반환하십시오."""
sales_node = create_agent_node("sales", sales_prompt)

# 기술 지원 에이전트
support_prompt = """당신은 '기술 지원(support)' 에이전트입니다. 제품 고장, 설정 방법, 오류 해결에 대해 전문적으로 답변하십시오.
만약 사용자가 수리 불가를 이유로 새 제품 구매를 원한다면 'sales'로 제어권을 넘기십시오.
직접 답변을 제공했다면 'none'을 반환하십시오."""
support_node = create_agent_node("support", support_prompt)

# 라우팅 로직
def swarm_router(state: SwarmState):
    """현재 상태의 active_agent 값을 읽어 다음에 실행할 노드를 결정합니다."""
    target = state.get("active_agent", "end")
    if target == "end":
        return END
    return target

# 그래프 조립
workflow = StateGraph(SwarmState)

workflow.add_node("triage", triage_node)
workflow.add_node("sales", sales_node)
workflow.add_node("support", support_node)

# 무조건 안내 데스크부터 시작
workflow.add_edge(START, "triage")

# 각 에이전트는 발언 후 라우팅 로직을 거쳐 다른 에이전트로 이동하거나 대기(END)
workflow.add_conditional_edges("triage", swarm_router, {"sales": "sales", "support": "support", END: END})
workflow.add_conditional_edges("sales", swarm_router, {"triage": "triage", "support": "support", END: END})
workflow.add_conditional_edges("support", swarm_router, {"triage": "triage", "sales": "sales", END: END})

# 세션 유지를 위한 Checkpointer 적용
memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)