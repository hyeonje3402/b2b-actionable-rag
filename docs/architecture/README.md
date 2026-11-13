# 아키텍처와 데이터 흐름

[메인 README](../../README.md)

## 문서 색인 흐름

1. FastAPI의 업로드 API가 TXT, PDF, PNG, JPG, WEBP 파일을 backend/data 경로에 저장합니다.
2. PDF/TXT는 텍스트로 추출하고, 이미지나 PDF 속 도식은 Gemini Vision으로 설명 텍스트를 생성하도록 구현되어 있습니다.
3. 표 구조와 문서 메타데이터를 보존·추출한 뒤 조항과 표 경계를 고려해 청크로 나눕니다.
4. Gemini 임베딩으로 벡터를 만들고 로컬 영구 디렉터리의 ChromaDB에 저장합니다.
5. 같은 source 파일을 다시 올리면 이전 source 청크를 지운 뒤 교체 색인합니다.

## 질문 응답 흐름

1. 사용자의 질문과 대화 이력을 FastAPI로 보냅니다.
2. 모호한 질문에는 선택지를 제공하고, 후속 질문은 독립 검색어로 재구성합니다.
3. ChromaDB에서 관련 문서 청크를 검색합니다.
4. 검색 문맥을 기반으로 Gemini가 답변과 출처 정보를 생성합니다.
5. 질의의 모델·토큰·지연시간 메트릭을 SQLite 파일에 기록하고 대시보드 API가 집계값을 제공합니다.

## 저장소 역할

| 저장소 | 데이터 | 위치 |
|---|---|---|
| ChromaDB | 문서 청크와 임베딩 | CHROMA_PERSIST_DIR, 기본값 ./chroma_db |
| SQLite | 질의 토큰·비용 추정·지연시간 로그 | backend/metrics.db |
| 로컬 파일 | 업로드 원본 및 샘플 문서 | DATA_DIR, 기본값 ./data |

별도 운영 PostgreSQL이나 클라우드 Vector DB 연결은 저장소에서 확인되지 않았습니다.

## 기능과 연동 경계

휴가 기안 Function Calling은 **tools.py**에서 샘플 문서번호·신청자·결재자 데이터를 생성해 반환합니다. 실제 사내 ERP/그룹웨어 API 호출이나 결재 저장은 구현되어 있지 않습니다. 현재 README의 “임시저장 완료”는 데모 응답입니다.