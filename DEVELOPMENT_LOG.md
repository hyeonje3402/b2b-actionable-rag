# DEVELOPMENT_LOG

## 2026-11-26 — 공개 문서 및 백엔드 정적 검증

- 목적: 문서상 기능·환경 설정 설명을 현재 구현과 비교하고 공개 관리 상태를 기록했다.
- 확인: \`main\`과 \`develop\`이 같은 기준 커밋에서 시작했다. README는 FastAPI/React 기반 로컬 RAG PoC와 Gemini 연동을 설명한다.
- 검증: \`python -m compileall -q backend\` 통과. 확인 가능한 자동화 테스트는 찾지 못했으며, 외부 Gemini API 및 브라우저 end-to-end 흐름은 실행하지 않았다.
- 변경: README에 검증 범위와 미검증 외부 연동을 명시하고 이 기록을 추가했다. 핵심 기능 코드는 변경하지 않았다.
- 판단: 문법 검사는 전체 기능 검증을 대체하지 않으므로 이 작업에서는 \`main\` 승격하지 않는다.
