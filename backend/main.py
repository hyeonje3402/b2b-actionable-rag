"""FastAPI 엔트리포인트 (v2.0 Enterprise Action Agent + LLMOps Dashboard API)."""
import os
import shutil
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from document_loader import SUPPORTED_EXTENSIONS, load_file
from metrics_logger import get_daily_metrics, get_metrics_summary, get_recent_logs, init_db
from rag_agent import RAGAgent
from text_splitter import split_documents
from vector_db import VectorDB

load_dotenv()
init_db()

DATA_DIR = os.getenv("DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI(title="B2B 사내 지식 Q&A (Enterprise Action Agent v2.0)")

# 프론트엔드 통신 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_db = VectorDB()
agent = RAGAgent(vector_db)


class ChatMessage(BaseModel):
    role: str
    text: str


class ChatRequest(BaseModel):
    query: str
    history: Optional[List[ChatMessage]] = None


class Source(BaseModel):
    source: str
    page: Optional[int] = None
    chunk: Optional[int] = None
    preview: str
    doc_title: Optional[str] = None
    effective_date: Optional[str] = None
    target_audience: Optional[str] = None
    department: Optional[str] = None


class QuickReply(BaseModel):
    label: str
    query: Optional[str] = None
    info: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    quick_replies: Optional[List[QuickReply]] = None
    rewritten_query: Optional[str] = None
    action: Optional[Dict[str, Any]] = None


@app.get("/")
def health():
    return {"status": "ok", "version": "v2.0-actionable"}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    """PDF, TXT, 이미지(PNG/JPG) 업로드 -> Vision 분석 / 표 파싱 -> 메타데이터 태깅 -> ChromaDB 인덱싱"""
    name = os.path.basename(file.filename or "")
    ext = os.path.splitext(name)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(400, f"지원하지 않는 파일 형식입니다. (지원: {sorted(SUPPORTED_EXTENSIONS)})")

    path = os.path.join(DATA_DIR, name)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        raw_docs = load_file(path)
        chunks = split_documents(raw_docs)
        count = vector_db.add_documents(chunks)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(500, f"인덱싱 실패: {e}")

    return {
        "file_name": name,
        "chunks": count,
        "message": "인덱싱 완료 (표 보존 / Vision 분석 / 메타데이터 태깅)",
        "metadata": {
            "effective_date": chunks[0].metadata.get("effective_date") if chunks else None,
            "target_audience": chunks[0].metadata.get("target_audience") if chunks else None,
            "department": chunks[0].metadata.get("department") if chunks else None,
            "is_vision": chunks[0].metadata.get("is_vision") if chunks else False,
        },
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """행동하는 에이전트: 의도 분석 / Tool 실행 / 질의 재구성 / RAG 답변 / LLMOps 로깅"""
    if not req.query.strip():
        raise HTTPException(400, "질문을 입력해 주세요.")

    history_dicts = None
    if req.history:
        history_dicts = [{"role": m.role, "text": m.text} for m in req.history]

    try:
        return agent.answer(req.query.strip(), chat_history=history_dicts)
    except Exception as e:
        raise HTTPException(500, f"답변 생성 실패: {e}")


# ---------------------------------------------------------------------------
# [LLMOps 모니터링 대시보드 API 엔드포인트]
# ---------------------------------------------------------------------------
@app.get("/api/metrics/summary")
def metrics_summary():
    """총 질의 수, 총 누적 토큰, 총 예상 과금액(USD), 평균 레이턴시 반환."""
    return get_metrics_summary()


@app.get("/api/metrics/daily")
def metrics_daily():
    """일별 API 호출량, 토큰 사용량, 비용 및 평균 속도 추이 (차트용)."""
    return get_daily_metrics()


@app.get("/api/metrics/recent")
def metrics_recent(limit: int = 15):
    """최근 질의 감사 로그 목록."""
    return get_recent_logs(limit)
