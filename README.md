# B2B 사내 지식 Q&A·업무 자동화 에이전트

사내 규정 문서를 검색해 출처와 함께 답변하고, 문서 업로드·Vision RAG·질의 재작성·LLMOps 지표 화면을 제공하는 로컬 개발용 RAG PoC입니다.

## 프로젝트 개요

| 항목 | 내용 |
|---|---|
| 주요 기능 | 규정 문서 Q&A, 파일 업로드·색인, 표·이미지 분석, 후속 질문 재작성, 메트릭 대시보드 |
| Frontend | React 18, Axios, Recharts |
| Backend | Python 3.11 기준, FastAPI, Pydantic, LangChain |
| Vector DB | ChromaDB 로컬 영구 디렉터리 |
| 메트릭 DB | SQLite 로컬 파일 |
| 모델 | Google Gemini chat·embedding 연동 코드 |
| 배포 | 로컬 실행 중심. CI/CD·클라우드 배포 설정은 확인되지 않음 |

## 전체 아키텍처

~~~mermaid
flowchart LR
    U[사용자] --> F[React 채팅·대시보드]
    F --> A[FastAPI]
    D[PDF/TXT/이미지] --> L[텍스트·표·Vision 처리]
    L --> S[청킹·메타데이터]
    S --> E[Gemini Embeddings]
    E --> V[(로컬 ChromaDB)]
    A --> R[검색·질의 재작성·응답 생성]
    V --> R
    R --> G[Gemini LLM]
    R --> M[(SQLite 질의 메트릭)]
    M --> F
~~~

## 문서

- [아키텍처와 데이터 흐름](docs/architecture/README.md)
- [설치·실행·환경 변수](docs/development/README.md)
- [운영·연동 경계](docs/operations/README.md)
- [개선 로드맵 제안](docs/roadmap/README.md)

## 빠른 시작

백엔드와 프런트엔드는 각자 터미널에서 실행합니다.

~~~bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
~~~

~~~bash
cd frontend
npm install
npm start
~~~

현재 저장소의 **backend/.env.example**은 OpenAI 변수를 예시로 들지만, 백엔드 RAG·임베딩 구현은 Google Gemini API 키를 읽습니다. 실행 전 키 설정은 [개발 문서](docs/development/README.md)를 확인하세요.

> 전자결재 도구는 현재 샘플 데이터를 반환하는 시뮬레이션입니다. 실제 그룹웨어에 휴가 신청을 전송하지 않습니다.

## 검증 상태

2026-11-26 백엔드 Python 파일의 \`compileall\` 검사는 통과했습니다. 저장소에서 자동화 테스트를 확인하지 못했으며 Gemini API 호출, 브라우저 전체 흐름, 배포 환경은 검증하지 않았습니다. 따라서 문법 검사는 핵심 기능의 end-to-end 정상 동작을 보장하지 않습니다.
