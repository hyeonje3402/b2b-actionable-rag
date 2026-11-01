"""문서 로더 + 표(Table) 보존 전처리 + 메타데이터 추출 + Vision RAG (멀티모달 이미지/다이어그램 처리).

1. 표(Table) 파싱: Markdown 표 형식(| Col | Col |) 및 ASCII 표 테두리를 보존/변환
2. 메타데이터 자동 추출: 시행일자, 적용대상, 담당부서, 규정명 자동 추출
3. Vision RAG: PNG, JPG, WEBP 또는 PDF 내 다이어그램/조직도/순서도 이미지를
   Multimodal LLM(Gemini Vision)으로 분석하여 구조화된 Markdown 텍스트로 변환 후 벡터 DB 색인
"""
import io
import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv
from google import genai
from google.genai import types
from langchain_core.documents import Document
from pypdf import PdfReader

load_dotenv()

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".png", ".jpg", ".jpeg", ".webp"}


def describe_image_with_vision(image_bytes: bytes, mime_type: str = "image/png") -> str:
    """Multimodal LLM을 호출하여 이미지/다이어그램/조직도를 Markdown 텍스트로 설명 및 구조화."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    prompt = (
        "당신은 사내 문서 및 조직도/결재 프로세스 분석 전문 AI입니다.\n"
        "제공된 이미지(조직도, 결재 프로세스 순서도, 표, 다이어그램, 아키텍처 등)의 모든 내용을 상세히 분석하여,\n"
        "사내 지식 검색(RAG)에 활용할 수 있도록 명확한 Markdown 텍스트(표, 번호 매기기, 단계별 설명)로 변환해 주세요.\n"
        "이미지에 표가 있다면 마크다운 표로 작성하고, 화살표나 흐름도가 있다면 '1단계 -> 2단계' 순서로 정리하세요."
    )
    try:
        response = client.models.generate_content(
            model=os.getenv("CHAT_MODEL", "gemini-3.5-flash-lite"),
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt,
            ],
        )
        return response.text.strip()
    except Exception as e:
        return f"[이미지 분석 실패: {e}]"


def normalize_tables(text: str) -> str:
    """표 데이터 구조 보존 및 Markdown 테이블 정규화."""
    lines = text.split("\n")
    processed_lines = []
    in_table = False

    for line in lines:
        stripped = line.strip()

        # 1. ASCII/Unicode 표 테두리
        if re.match(r"^[\+┌├└│━─┬┴┼═\-_|]{4,}$", stripped):
            if in_table:
                continue
            else:
                in_table = True
                continue

        # 2. 파이프(|)로 구분된 표 행
        if stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2:
            in_table = True
            cols = [c.strip() for c in stripped.split("|")]
            processed_lines.append("| " + " | ".join(cols[1:-1]) + " |")
            continue

        # 3. 탭(\t) 구분 TSV 표
        if "\t" in stripped and len(stripped.split("\t")) >= 3:
            cols = [c.strip() for c in stripped.split("\t") if c.strip()]
            if len(cols) >= 2:
                processed_lines.append("| " + " | ".join(cols) + " |")
                in_table = True
                continue

        in_table = False
        processed_lines.append(line)

    return "\n".join(processed_lines)


def clean_text(text: str) -> str:
    """텍스트 전처리: 제어문자 제거 + 표 보존 + 문단 보존."""
    text = text.replace("\ufffd", "")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = re.sub(r"^\s*(-\s*\d+\s*-|[Pp]age\s*\d+)\s*$", "", text, flags=re.MULTILINE)
    text = normalize_tables(text)

    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        if line.strip().startswith("|") and line.strip().endswith("|"):
            cleaned_lines.append(line.strip())
        else:
            cleaned_lines.append(re.sub(r"[ \t\u00a0]+", " ", line))

    res = "\n".join(cleaned_lines)
    res = re.sub(r"\n{3,}", "\n\n", res)
    return res.strip()


def extract_document_metadata(text: str, file_name: str) -> Dict[str, Any]:
    """문서 선두부에서 시행일자, 적용대상, 담당부서, 규정명 자동 추출 및 태깅."""
    meta = {
        "doc_title": os.path.splitext(file_name)[0],
        "effective_date": "2026-01-01",
        "target_audience": "전 임직원",
        "department": "인사총무팀",
    }

    m_date = re.search(r"(?:시행일자|시행일|제정일자|개정일자)[\s:：]+([12]\d{3}[.\-/]\d{1,2}[.\-/]\d{1,2})", text)
    if m_date:
        raw_date = m_date.group(1).replace(".", "-").replace("/", "-")
        parts = raw_date.split("-")
        if len(parts) == 3:
            meta["effective_date"] = f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"

    m_target = re.search(r"(?:적용대상|적용\s?범위|대상)[\s:：]+([^\n\r,]+)", text)
    if m_target:
        meta["target_audience"] = m_target.group(1).strip()

    m_dept = re.search(r"(?:담당부서|소관부서|주관부서)[\s:：]+([^\n\r(,]+)", text)
    if m_dept:
        meta["department"] = m_dept.group(1).strip()

    m_title = re.search(r"(?:규정명|문서명)[\s:：]+([^\n\r]+)", text)
    if m_title:
        meta["doc_title"] = m_title.group(1).strip()

    return meta


def load_file(file_path: str) -> List[Document]:
    """PDF, TXT 및 이미지 파일(PNG/JPG)을 로드하여 Document 리스트로 반환."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    file_name = os.path.basename(file_path)
    ext = os.path.splitext(file_name)[1].lower()
    docs: List[Document] = []

    # 1. 단독 이미지 파일 업로드 (Vision RAG)
    if ext in {".png", ".jpg", ".jpeg", ".webp"}:
        mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
        with open(file_path, "rb") as f:
            img_bytes = f.read()

        # Multimodal LLM으로 이미지 내 텍스트/도표/조직도 마크다운 추출
        vision_text = describe_image_with_vision(img_bytes, mime_map.get(ext, "image/png"))
        full_content = f"# [이미지/다이어그램 분석 자료: {file_name}]\n\n{vision_text}"

        meta = {
            "source": file_name,
            "page": 1,
            "doc_title": f"이미지 문서: {os.path.splitext(file_name)[0]}",
            "effective_date": "2026-01-01",
            "target_audience": "전 임직원",
            "department": "업무지원팀",
            "is_vision": True,
        }
        docs.append(Document(page_content=full_content, metadata=meta))

    # 2. PDF 문서 로드 및 임베디드 이미지 Vision 처리
    elif ext == ".pdf":
        reader = PdfReader(file_path)
        full_first_page = reader.pages[0].extract_text() if reader.pages else ""
        doc_meta = extract_document_metadata(full_first_page, file_name)

        for i, page in enumerate(reader.pages, start=1):
            text_content = clean_text(page.extract_text() or "")

            # 페이지 내 이미지 추출 및 Vision 분석
            vision_parts = []
            if hasattr(page, "images") and page.images:
                for img_idx, img_file in enumerate(page.images, start=1):
                    try:
                        v_desc = describe_image_with_vision(img_file.data, "image/png")
                        vision_parts.append(f"\n\n### [페이지 {i} 포함 다이어그램 #{img_idx}]\n{v_desc}")
                    except Exception:
                        pass

            combined_page_text = text_content + "".join(vision_parts)
            if combined_page_text.strip():
                meta = {
                    "source": file_name,
                    "page": i,
                    **doc_meta,
                    "is_vision": bool(vision_parts),
                }
                docs.append(Document(page_content=combined_page_text.strip(), metadata=meta))

    # 3. TXT 텍스트 파일 로드
    elif ext == ".txt":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="cp949", errors="ignore") as f:
                raw = f.read()

        cleaned = clean_text(raw)
        if cleaned:
            doc_meta = extract_document_metadata(raw[:2000], file_name)
            meta = {
                "source": file_name,
                "page": 1,
                **doc_meta,
                "is_vision": False,
            }
            docs.append(Document(page_content=cleaned, metadata=meta))
    else:
        raise ValueError(f"지원하지 않는 형식입니다: {ext} (지원: {sorted(SUPPORTED_EXTENSIONS)})")

    if not docs:
        raise ValueError("문서에서 추출 가능한 텍스트 또는 이미지가 없습니다.")
    return docs


def load_directory(dir_path: str) -> List[Document]:
    """폴더 내 모든 파일 로드."""
    os.makedirs(dir_path, exist_ok=True)
    docs: List[Document] = []
    for name in sorted(os.listdir(dir_path)):
        if os.path.splitext(name)[1].lower() in SUPPORTED_EXTENSIONS:
            docs.extend(load_file(os.path.join(dir_path, name)))
    return docs
