import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  AreaChart,
  Area,
} from 'recharts';

const API = 'http://127.0.0.1:8000';

export default function Dashboard() {
  const [summary, setSummary] = useState({
    total_requests: 0,
    total_tokens: 0,
    total_cost_usd: 0,
    avg_latency_ms: 0,
  });
  const [dailyData, setDailyData] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const [sumRes, dailyRes, logsRes] = await Promise.all([
        axios.get(`${API}/api/metrics/summary`),
        axios.get(`${API}/api/metrics/daily`),
        axios.get(`${API}/api/metrics/recent?limit=15`),
      ]);
      setSummary(sumRes.data);
      setDailyData(dailyRes.data);
      setLogs(logsRes.data);
    } catch (err) {
      console.error('메트릭 조회 실패:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 8000); // 8초마다 자동 갱신
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard-container">
      <div className="dash-header">
        <div>
          <h2>📊 LLMOps 비용 &amp; 레이턴시 모니터링 대시보드</h2>
          <p className="dash-desc">실시간 API 호출량, 토큰 과금 추정액(USD), 응답 지연 시간(Latency) 감사 로그</p>
        </div>
        <button className="refresh-btn" onClick={fetchMetrics} disabled={loading}>
          {loading ? '새로고침 중...' : '🔄 실시간 새로고침'}
        </button>
      </div>

      {/* 4대 핵심 지표 카드 */}
      <div className="stat-cards-grid">
        <div className="stat-card">
          <div className="stat-label">📈 총 API 호출 수</div>
          <div className="stat-val">{summary.total_requests.toLocaleString()} <span className="stat-unit">건</span></div>
          <div className="stat-hint">전체 RAG 및 Action 누적</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">💰 누적 추정 비용</div>
          <div className="stat-val">${summary.total_cost_usd.toFixed(6)} <span className="stat-unit">USD</span></div>
          <div className="stat-hint">Gemini 3.5 Flash Lite 단가 기준</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">⚡ 평균 응답 속도</div>
          <div className="stat-val">{summary.avg_latency_ms.toLocaleString()} <span className="stat-unit">ms</span></div>
          <div className="stat-hint">검색 + LLM 생성 종합 지연시간</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">🔤 총 소비 토큰</div>
          <div className="stat-val">{summary.total_tokens.toLocaleString()} <span className="stat-unit">tokens</span></div>
          <div className="stat-hint">프롬프트 + 생성 토큰 합산</div>
        </div>
      </div>

      {/* 차트 영역 */}
      <div className="charts-grid">
        <div className="chart-panel">
          <div className="chart-title">일별 API 호출량 및 평균 응답 지연시간(ms)</div>
          <div style={{ width: '100%', height: 260 }}>
            {dailyData.length > 0 ? (
              <ResponsiveContainer>
                <BarChart data={dailyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
                  <YAxis yAxisId="left" stroke="#3b82f6" fontSize={11} />
                  <YAxis yAxisId="right" orientation="right" stroke="#10b981" fontSize={11} />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="calls" name="호출 수 (건)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  <Line yAxisId="right" type="monotone" dataKey="avg_latency_ms" name="평균속도 (ms)" stroke="#10b981" strokeWidth={2} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="no-data">차트 집계 데이터가 대기 중입니다.</div>
            )}
          </div>
        </div>

        <div className="chart-panel">
          <div className="chart-title">토큰 소비량 추이 (Area)</div>
          <div style={{ width: '100%', height: 260 }}>
            {dailyData.length > 0 ? (
              <ResponsiveContainer>
                <AreaChart data={dailyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#8b5cf6" fontSize={11} />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="tokens" name="사용 토큰" stroke="#8b5cf6" fill="#ede9fe" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="no-data">차트 집계 데이터가 대기 중입니다.</div>
            )}
          </div>
        </div>
      </div>

      {/* 최근 감사 로그 테이블 */}
      <div className="log-panel">
        <div className="log-header">
          <div className="chart-title">📋 최근 질의 실시간 감사 로그 (Audit Logs)</div>
          <span className="log-count">최근 {logs.length}건</span>
        </div>
        <div className="table-responsive">
          <table className="log-table">
            <thead>
              <tr>
                <th>일시</th>
                <th>사용자 질의 (Query)</th>
                <th>액션 구분</th>
                <th>토큰 (입력/출력)</th>
                <th>지연시간</th>
                <th>예상 비용</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id}>
                  <td className="col-time">{l.timestamp}</td>
                  <td className="col-query">{l.query}</td>
                  <td>
                    {l.action_type === 'apply_vacation_leave' ? (
                      <span className="badge-action">⚡ 연차 기안 (Tool)</span>
                    ) : l.action_type === 'disambiguation' ? (
                      <span className="badge-intent">💡 의도 분기</span>
                    ) : (
                      <span className="badge-rag">🔍 RAG 검색</span>
                    )}
                  </td>
                  <td className="col-tokens">
                    {l.total_tokens.toLocaleString()} <span className="sub-tokens">({l.prompt_tokens}/{l.completion_tokens})</span>
                  </td>
                  <td className="col-latency">{l.latency_ms.toFixed(0)} ms</td>
                  <td className="col-cost">${l.cost_usd.toFixed(6)}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '24px', color: '#94a3b8' }}>
                    기록된 질의 로그가 없습니다. 채팅 탭에서 질문을 시도해 보세요.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
