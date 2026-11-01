import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import './App.css';
import Dashboard from './Dashboard';

const API = 'http://127.0.0.1:8000';

/** 출처 박스: 문서명, 메타데이터(시행일/대상/부서/Vision 여부), 페이지, 청크 뱃지 */
function SourceBox({ sources }) {
  if (!sources || sources.length === 0) return null;
  return (
    <div className="source-box">
      <div className="source-title">📎 참고한 사내 규정 및 다이어그램 출처 (Source)</div>
      {sources.map((s, i) => (
        <div className="source-item" key={i}>
          <div className="badges">
            <span className="badge file">{s.source}</span>
            {s.source.endsWith('.png') || s.source.endsWith('.jpg') ? (
              <span className="badge vision">🖼️ Vision RAG (다이어그램 분석)</span>
            ) : null}
            {s.effective_date && <span className="badge meta">📅 시행일: {s.effective_date}</span>}
            {s.target_audience && <span className="badge meta">👥 대상: {s.target_audience}</span>}
            {s.department && <span className="badge meta">🏢 {s.department}</span>}
            {s.page != null && <span className="badge">p.{s.page}</span>}
            {s.chunk != null && <span className="badge">청크 #{s.chunk}</span>}
          </div>
          <div className="preview">{s.preview}</div>
        </div>
      ))}
    </div>
  );
}

/** 행동하는 에이전트: 전자결재 기안 완료 Action Card */
function ActionCard({ action }) {
  if (!action) return null;
  return (
    <div className="action-card">
      <div className="action-header">
        <div className="action-badge-wrap">
          <span className="action-badge">✅ 전자결재 자동 기안 완료</span>
          <span className="action-status-pill">임시저장 (상신 대기)</span>
        </div>
        <span className="action-docno">{action.doc_no}</span>
      </div>
      <div className="action-body">
        <h4 className="action-title">{action.title}</h4>
        <div className="action-grid">
          <div className="action-field">
            <span className="field-name">신청자:</span>
            <span className="field-val">{action.applicant}</span>
          </div>
          <div className="action-field">
            <span className="field-name">지정 결재선:</span>
            <span className="field-val highlight">{action.approver}</span>
          </div>
          <div className="action-field">
            <span className="field-name">사용 시작일:</span>
            <span className="field-val">{action.start_date}</span>
          </div>
          <div className="action-field">
            <span className="field-name">신청 일수:</span>
            <span className="field-val">{action.days}일간</span>
          </div>
          <div className="action-field full">
            <span className="field-name">신청 사유:</span>
            <span className="field-val">{action.reason}</span>
          </div>
        </div>
        <div className="action-footer">
          <span className="action-notice">💡 사내 취업규칙 제10조 제3항 규정에 부합하여 자동 작성되었습니다.</span>
          <a
            href={action.gw_link}
            target="_blank"
            rel="noopener noreferrer"
            className="action-link-btn"
            onClick={(e) => {
              e.preventDefault();
              alert(`[가상 사내 그룹웨어 전자결재 시스템]\n문서번호 ${action.doc_no} 상세 기안 페이지로 연결됩니다.`);
            }}
          >
            🔗 그룹웨어 결재함 열기
          </a>
        </div>
      </div>
    </div>
  );
}

/** 인터랙티브 빠른 선택지 및 되묻기 옵션 버튼 */
function QuickReplyBox({ replies, onSelect }) {
  if (!replies || replies.length === 0) return null;
  return (
    <div className="quick-reply-box">
      <div className="quick-reply-title">💡 선택하여 상세 규정 확인하기 (되묻기 옵션):</div>
      <div className="quick-reply-list">
        {replies.map((r, i) => (
          <button
            key={i}
            type="button"
            className="quick-chip"
            onClick={() => onSelect(r)}
          >
            {r.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'dashboard'
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: '안녕하세요! 사내 취업규칙 및 업무 자동화 에이전트(Actionable Agent v2.0)입니다.\n\n⚡ "나 다음 주 월요일부터 3일간 연차 쓸래"와 같이 말씀하시면 사내 그룹웨어에 연차 기안을 자동으로 작성해 드립니다.\n또한 복잡한 표(Table)와 다이어그램 이미지(Vision RAG) 질의도 지원합니다.',
      sources: [],
      quick_replies: [
        { label: '⚡ 연차 자동 기안 신청 (Action 테스트)', query: '나 다음 주 월요일부터 3일간 연차 신청해줘' },
        { label: '🖼️ 전자결재 승인 순서도 (Vision RAG 테스트)', query: '전자결재 휴가 승인 프로세스 순서가 어떻게 돼?' },
        { label: '📊 근속연수별 연차 일수 산정표 (5년차)', query: '근속연수 5년 차 직원의 연차휴가 일수는 며칠인가요?' },
        { label: '💍 경조사별 휴가 일수 (되묻기 테스트)', query: '경조사 휴가 며칠 쓸 수 있어?' },
      ],
      action: null,
    },
  ]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState('');
  const endRef = useRef(null);
  const fileRef = useRef(null);

  useEffect(() => {
    if (activeTab === 'chat') {
      endRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading, activeTab]);

  const upload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    setUploadMsg('문서/이미지 분석 중...');
    try {
      const { data } = await axios.post(`${API}/api/upload`, form);
      const isVision = file.name.match(/\.(png|jpg|jpeg|webp)$/i);
      const label = isVision ? '🖼️ Vision 분석 완료' : '📄 문서 색인 완료';
      setUploadMsg(`✅ ${label}: ${data.file_name} (${data.chunks}청크)`);
    } catch (err) {
      setUploadMsg(`❌ ${err.response?.data?.detail || '업로드 실패'}`);
    }
    fileRef.current.value = '';
  };

  const executeQuery = async (userQuery) => {
    const q = userQuery.trim();
    if (!q || loading) return;

    const historyPayload = messages
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .slice(-6)
      .map((m) => ({ role: m.role, text: m.text }));

    setMessages((m) => [...m, { role: 'user', text: q, sources: [] }]);
    setQuery('');
    setLoading(true);

    try {
      const { data } = await axios.post(`${API}/api/chat`, {
        query: q,
        history: historyPayload,
      });

      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          text: data.answer,
          sources: data.sources || [],
          quick_replies: data.quick_replies || null,
          rewritten_query: data.rewritten_query || null,
          action: data.action || null,
        },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          text: err.response?.data?.detail || '서버 오류가 발생했습니다.',
          sources: [],
          action: null,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickSelect = (reply) => {
    if (reply.info) {
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          text: reply.info,
          sources: [],
          quick_replies: null,
          action: null,
        },
      ]);
    } else if (reply.query) {
      executeQuery(reply.query);
    }
  };

  const send = (e) => {
    e.preventDefault();
    executeQuery(query);
  };

  return (
    <div className="app">
      <header>
        <div className="header-left">
          <span className="logo-icon">🏢</span>
          <div>
            <h1>사내 지식 Q&amp;A 에이전트 v2.0</h1>
            <p className="subtitle">행동하는 업무 자동화 (Action Agent) · Vision RAG · LLMOps 대시보드</p>
          </div>
        </div>

        {/* 네비게이션 탭 & 업로드 버튼 */}
        <div className="header-actions">
          <div className="nav-tabs">
            <button
              className={`nav-tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveTab('chat')}
            >
              💬 채팅 에이전트
            </button>
            <button
              className={`nav-tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveTab('dashboard')}
            >
              📊 LLMOps 대시보드
            </button>
          </div>

          <div className="upload">
            <input type="file" accept=".pdf,.txt,.png,.jpg,.jpeg,.webp" ref={fileRef} onChange={upload} hidden />
            <button className="upload-btn" onClick={() => fileRef.current.click()}>
              📎 문서/이미지 업로드
            </button>
            {uploadMsg && <span className="upload-status">{uploadMsg}</span>}
          </div>
        </div>
      </header>

      {/* 탭 1: 채팅 에이전트 화면 */}
      {activeTab === 'chat' && (
        <>
          <main>
            {messages.map((m, i) => (
              <div key={i} className={`row ${m.role}`}>
                <div className="bubble">
                  {/* 질의 재구성 뱃지 */}
                  {m.rewritten_query && (
                    <div className="rewritten-chip">
                      <span className="rewritten-icon">🔄</span>
                      <span className="rewritten-label">대화 맥락 반영 검색어:</span>
                      <span className="rewritten-text">"{m.rewritten_query}"</span>
                    </div>
                  )}

                  {/* 행동 완료 액션 카드 (연차 기안 등) */}
                  {m.action && <ActionCard action={m.action} />}

                  <div className="text">{m.text}</div>

                  {/* 출처 박스 */}
                  {m.role === 'assistant' && <SourceBox sources={m.sources} />}

                  {/* 되묻기 / 추천 칩 */}
                  {m.role === 'assistant' && (
                    <QuickReplyBox
                      replies={m.quick_replies}
                      onSelect={handleQuickSelect}
                    />
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="row assistant">
                <div className="bubble muted">
                  <span className="spinner">⏳</span> 업무 에이전트가 사내 규정을 검색하고 액션을 수행 중입니다...
                </div>
              </div>
            )}
            <div ref={endRef} />
          </main>

          <form onSubmit={send}>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="예: '다음 주 월요일부터 3일간 연차 신청해줘', '전자결재 승인 순서도 알려줘'..."
              disabled={loading}
            />
            <button type="submit" disabled={loading || !query.trim()}>전송</button>
          </form>
        </>
      )}

      {/* 탭 2: LLMOps 관리자 대시보드 화면 */}
      {activeTab === 'dashboard' && <Dashboard />}
    </div>
  );
}
