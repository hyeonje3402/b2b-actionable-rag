# 설치·실행·환경 변수

[메인 README](../../README.md)

## 준비물

- Python 3.11 권장
- Node.js와 npm
- Google Gemini API 키
- 문서 Q&A를 시험할 TXT/PDF 또는 이미지 파일

## 백엔드 설정

~~~bash
cd backend
python -m venv .venv
~~~

Windows PowerShell:

~~~powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
~~~

백엔드 코드에서 사용되는 환경 변수 예시는 다음과 같습니다.

~~~env
GOOGLE_API_KEY=발급한_Gemini_API_키
GEMINI_API_KEY=선택적_Gemini_API_키
CHAT_MODEL=gemini-3.5-flash-lite
EMBEDDING_MODEL=models/text-embedding-004
CHROMA_PERSIST_DIR=./chroma_db
DATA_DIR=./data
~~~

Google 키는 현재 문서 색인, 임베딩, 채팅·Vision 흐름에서 필요합니다. 저장소의 backend/.env.example은 OpenAI API 키와 모델을 적어 두어 현재 코드와 맞지 않습니다. 값을 그대로 복사하지 말고 위의 Google Gemini 설정과 코드 기본값을 기준으로 실행 환경을 맞추세요. 비밀 키는 Git에 커밋하지 않습니다.

## 서버 실행

백엔드:

~~~bash
uvicorn main:app --reload --port 8000
~~~

Swagger API 문서: **http://127.0.0.1:8000/docs**

프런트엔드의 새 터미널에서:

~~~bash
cd frontend
npm install
npm start
~~~

React 개발 서버는 일반적으로 **http://localhost:3000**에서 실행됩니다.

## API 개요

| 경로 | 용도 |
|---|---|
| POST /api/upload | 규정 파일 업로드와 색인 |
| POST /api/chat | 문서 검색 기반 Q&A |
| GET /api/metrics/summary | 메트릭 요약 |
| GET /api/metrics/daily | 날짜별 지표 |
| GET /api/metrics/recent | 최근 질의 로그 |

요청 형식은 실행 중인 Swagger 문서를 기준으로 확인하세요.