"""LLMOps 모니터링 및 메트릭 로깅 시스템 (SQLite 기반).

각 질의마다 발생하는 프롬프트 토큰 수, 생성 토큰 수, 예상 과금액(USD), 응답 지연 시간(Latency)을
로컬 SQLite 데이터베이스에 기록하고 대시보드용 집계 데이터를 제공한다.
"""
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "metrics.db")

# ---------------------------------------------------------------------------
# [Gemini 3.5 Flash Lite 단가 기준 (USD)]
# 입력: $0.075 / 1,000,000 토큰 ($0.000000075 / token)
# 출력: $0.300 / 1,000,000 토큰 ($0.000000300 / token)
# ---------------------------------------------------------------------------
PRICE_PROMPT_PER_TOKEN = 0.075 / 1_000_000
PRICE_COMPLETION_PER_TOKEN = 0.300 / 1_000_000


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """메트릭 로깅 테이블 초기화."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS query_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER NOT NULL,
                completion_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                latency_ms REAL NOT NULL,
                action_type TEXT
            )
        """)
        conn.commit()


def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """토큰 수 기반 예상 비용(USD) 계산."""
    return (prompt_tokens * PRICE_PROMPT_PER_TOKEN) + (completion_tokens * PRICE_COMPLETION_PER_TOKEN)


def log_query_metric(
    query: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: float,
    action_type: Optional[str] = None,
) -> Dict[str, Any]:
    """질의 1건의 토큰/비용/지연시간 로깅."""
    init_db()
    total_tokens = prompt_tokens + completion_tokens
    cost = calculate_cost(prompt_tokens, completion_tokens)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        conn.execute("""
            INSERT INTO query_metrics (
                timestamp, query, model, prompt_tokens, completion_tokens,
                total_tokens, cost_usd, latency_ms, action_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ts, query, model, prompt_tokens, completion_tokens, total_tokens, cost, latency_ms, action_type))
        conn.commit()

    return {
        "timestamp": ts,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cost_usd": cost,
        "latency_ms": latency_ms,
        "action_type": action_type,
    }


def get_metrics_summary() -> Dict[str, Any]:
    """관리자 대시보드용 요약 지표 (총 호출수, 총 비용, 평균 속도, 총 토큰)."""
    init_db()
    with get_db() as conn:
        row = conn.execute("""
            SELECT 
                COUNT(*) as total_requests,
                COALESCE(SUM(total_tokens), 0) as total_tokens,
                COALESCE(SUM(cost_usd), 0.0) as total_cost_usd,
                COALESCE(AVG(latency_ms), 0.0) as avg_latency_ms
            FROM query_metrics
        """).fetchone()

        return {
            "total_requests": row["total_requests"],
            "total_tokens": row["total_tokens"],
            "total_cost_usd": round(row["total_cost_usd"], 6),
            "avg_latency_ms": round(row["avg_latency_ms"], 1),
        }


def get_daily_metrics() -> List[Dict[str, Any]]:
    """일별 호출 추이, 비용 및 평균 레이턴시 그래프용 데이터."""
    init_db()
    with get_db() as conn:
        rows = conn.execute("""
            SELECT 
                SUBSTR(timestamp, 1, 10) as date,
                COUNT(*) as calls,
                COALESCE(SUM(total_tokens), 0) as tokens,
                ROUND(COALESCE(SUM(cost_usd), 0.0), 6) as cost_usd,
                ROUND(COALESCE(AVG(latency_ms), 0.0), 1) as avg_latency_ms
            FROM query_metrics
            GROUP BY SUBSTR(timestamp, 1, 10)
            ORDER BY date ASC
            LIMIT 30
        """).fetchall()

        return [dict(r) for r in rows]


def get_recent_logs(limit: int = 20) -> List[Dict[str, Any]]:
    """최근 질의 감사 로그 목록."""
    init_db()
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, timestamp, query, model, prompt_tokens, completion_tokens,
                   total_tokens, cost_usd, latency_ms, action_type
            FROM query_metrics
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(r) for r in rows]
