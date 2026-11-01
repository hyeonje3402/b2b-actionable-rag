"""사내 전자결재 및 업무 자동화 액션 도구 (Function Calling & Tools)."""
import random
from datetime import datetime
from typing import Any, Dict


def apply_vacation_leave(start_date: str, days: int, reason: str = "개인 사유") -> Dict[str, Any]:
    """사내 그룹웨어(ERP) 근태 결재 시스템에 연차 기안을 임시저장(상신 대기)하는 전자결재 연동 도구.
    
    Args:
        start_date: 연차 시작 일자 (예: 2026-11-09)
        days: 연차 사용 일수 (예: 3)
        reason: 연차 사용 사유
    """
    doc_no = f"GW-VAC-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    return {
        "status": "success",
        "action_type": "vacation_draft_created",
        "doc_no": doc_no,
        "title": f"연차 유급휴가 신청서 ({days}일간)",
        "start_date": start_date,
        "days": days,
        "reason": reason,
        "applicant": "김철수 (개발팀 / 사원)",
        "approver": "박팀장 (개발팀 / 팀장)",
        "message": "사내 그룹웨어 전자결재 시스템에 연차 기안이 성공적으로 임시저장(상신 대기)되었습니다.",
        "gw_link": f"https://gw.sampletech.internal/approval/draft/{doc_no}",
    }
