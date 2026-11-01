"""텍스트 스플리터 (청킹): 조항 및 표(Table) 경계 보호."""
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ---------------------------------------------------------------------------
# [청크 분할 기준 및 표 보호 전략]
# chunk_size=1000, chunk_overlap=200
# separators 우선순위:
# 1) '제N조' 조항 구분 정규식
# 2) '[표 N]' 표 시작 경계 정규식 (표 구조가 중간에 절단되지 않도록 보호)
# 3) 문단 경계 (\n\n)
# 4) 줄바꿈 (\n)
# ---------------------------------------------------------------------------
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
SEPARATORS = [
    r"\n(?=제\s?\d+\s?조)",
    r"\n(?=\[표\s?\d+\])",
    "\n\n",
    "\n",
    ". ",
    "다. ",
    " ",
    "",
]


def split_documents(documents: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARATORS,
        is_separator_regex=True,
        keep_separator=True,
        length_function=len,
    )
    chunks = splitter.split_documents(documents)

    # 출처 표기를 위한 파일별 청크 번호 부여 (1부터)
    counters: dict = {}
    for chunk in chunks:
        src = chunk.metadata.get("source", "unknown")
        counters[src] = counters.get(src, 0) + 1
        chunk.metadata["chunk"] = counters[src]
    return chunks
