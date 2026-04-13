# Swarm Architecture Agent (탈중앙화 Handoff 시스템)

## 1. 프로젝트 개요

이 프로젝트는 중앙 관리자(Supervisor)의 개입 없이 에이전트들이 동등한 위치에서 서로에게 직접 제어권을 넘겨주는 Swarm 아키텍처를 구현한 사례입니다.

종합 고객 센터 시나리오를 바탕으로 하며, 사용자의 요청이 자신의 전문 분야가 아닐 경우 적합한 다른 에이전트에게 대화 문맥과 실행 권한을 즉시 이관(Handoff)합니다. 이를 통해 중앙 병목 현상을 방지하고 에이전트 간의 유기적인 협업이 가능한 탈중앙화된 시스템을 구축합니다.

## 2. 시스템 아키텍처

본 시스템은 에이전트 간의 수평적 연결망을 가지며, 동적 라우팅을 통해 흐름이 결정됩니다.

1. State Definition: 전체 대화 기록(messages)과 현재 어떤 에이전트가 제어권을 가지고 있는지 나타내는 활성 에이전트 상태(active_agent)를 관리합니다.
2. Agent Nodes (Triage, Sales, Support):
   - 안내 데스크(Triage): 초기 접수 및 요청 분석 후 적절한 부서로 연결합니다.
   - 영업(Sales): 제품 구매 상담을 진행하며, 기술 문의 발생 시 지원 부서로 이관합니다.
   - 지원(Support): 고장 수리 상담을 진행하며, 재구매 의사 확인 시 영업 부서로 이관합니다.
3. P2P Handoff Logic: 각 에이전트는 답변 생성 시 Pydantic 스키마를 통해 다음에 제어권을 가질 에이전트를 명시합니다. 'none'을 반환하면 현재 에이전트가 대화를 유지하고, 다른 부서 이름을 반환하면 즉시 해당 노드로 제어권이 넘어갑니다.
4. Conditional Routing: Swarm Router가 상태의 active_agent 값을 읽어 다음에 실행될 노드를 실시간으로 결정합니다.

## 3. 기술 스택

* Language: Python 3.10+
* Package Manager: uv
* LLM: OpenAI gpt-5-mini
* Data Validation: Pydantic (v2) (에이전트 답변 및 이관 로직 구조화)
* Orchestration: LangGraph (수평적 순환 그래프, Checkpointer를 통한 세션 유지), LangChain
* Web Framework: Streamlit (실시간 에이전트 전환 모니터링)

## 4. 프로젝트 구조
```
swarm-agent/
├── .env                  
├── requirements.txt      
├── main.py               
└── app/
    ├── __init__.py
    └── graph.py          
```
## 5. 설치 및 실행 가이드

### 5.1. 환경 변수 설정
프로젝트 루트 경로에 .env 파일을 생성하고 API 키를 입력하십시오.

OPENAI_API_KEY=sk-your-api-key-here

### 5.2. 의존성 설치 및 앱 실행
독립된 가상환경을 구성하고 애플리케이션을 구동합니다.

uv venv
uv pip install -r requirements.txt
uv run streamlit run main.py

## 6. 테스트 시나리오 및 검증 방법

* 부서 연결 테스트: "안녕하세요, 제품 구매를 하고 싶습니다."라고 입력합니다. [TRIAGE] 에이전트가 요청을 분석하여 [SALES] 부서로 제어권을 즉시 넘기는지 확인합니다.
* 유기적 이관(Handoff) 테스트: 영업 상담 중 "그런데 이 제품 수리는 어떻게 하나요?"라고 질문합니다. [SALES] 에이전트가 [SUPPORT] 에이전트에게 대화 맥락을 이관하고, 지원 에이전트가 이어서 답변하는지 확인합니다.
* 컨텍스트 유지 검증: 여러 번의 이관이 발생하더라도 이전 대화 내용이 소실되지 않고 모든 에이전트가 전체 맥락을 공유하며 답변하는지 점검합니다.

## 7. 실행 화면
