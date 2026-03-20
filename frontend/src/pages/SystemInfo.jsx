import React, { useState, useEffect } from 'react'
import api from '../api.js'

export default function SystemInfo() {
  const [info, setInfo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => { fetchInfo() }, [])

  const fetchInfo = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get('/system/info')
      setInfo(res.data)
    } catch (e) {
      setError('정보 조회 실패: ' + (e.response?.data?.detail || e.message))
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div style={styles.loading}>정보 불러오는 중...</div>
  if (error) return <div style={styles.error}>{error}</div>
  if (!info) return null

  const { claude, sdk, python, services } = info

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <h2 style={styles.pageTitle}>🤖 시스템 정보</h2>
        <button style={styles.btnRefresh} onClick={fetchInfo}>🔄 새로고침</button>
      </div>

      <div style={styles.grid}>

        {/* Claude AI */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>
            <span style={styles.cardIcon}>🧠</span>
            <span style={styles.cardTitle}>Claude AI</span>
          </div>
          <div style={styles.cardBody}>
            <Row label="모델" value={claude.model} highlight />
            <Row label="사고(Thinking)" value={claude.thinking} />
            <Row label="최대 턴수" value={`${claude.max_turns}회`} />
            <Row label="인증 방식" value={claude.auth} />
            <Row label="CLI 버전" value={claude.cli_version} />
          </div>
        </div>

        {/* SDK */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>
            <span style={styles.cardIcon}>📦</span>
            <span style={styles.cardTitle}>SDK / 런타임</span>
          </div>
          <div style={styles.cardBody}>
            <Row label="패키지" value={sdk.package} />
            <Row label="버전" value={sdk.version} highlight />
            <Row label="Python" value={python.version?.split(' ')[0]} />
            <Row label="실행 경로" value={python.executable} small />
          </div>
        </div>

        {/* 문항 현황 */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>
            <span style={styles.cardIcon}>📊</span>
            <span style={styles.cardTitle}>문항 현황</span>
          </div>
          <div style={styles.cardBody}>
            <Row label="전체 문항" value={`${services.total_questions ?? '-'}개`} highlight />
            <Row label="검증완료" value={`${services.validated_questions ?? '-'}개`} />
            <Row label="승인됨" value={`${services.approved_questions ?? '-'}개`} />
            <Row label="중복 판정 기준" value={services.duplicate_threshold} />
          </div>
        </div>

        {/* 참조 파일 */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>
            <span style={styles.cardIcon}>📁</span>
            <span style={styles.cardTitle}>참조 파일</span>
          </div>
          <div style={styles.cardBody}>
            {[
              { key: 'competency_file', label: '역량 정의서' },
              { key: 'item_bank_file', label: '문항 Bank' },
              { key: 'curriculum_file', label: '교육 커리큘럼' },
            ].map(({ key, label }) => {
              const f = services[key]
              if (!f) return null
              return (
                <div key={key} style={styles.fileRow}>
                  <div>
                    <div style={styles.fileLabel}>{label}</div>
                    <div style={styles.fileName}>{f.name}</div>
                  </div>
                  <span style={{ ...styles.fileBadge, background: f.loaded ? '#d4edda' : '#f8d7da', color: f.loaded ? '#155724' : '#721c24' }}>
                    {f.loaded ? '✅ 로드됨' : '⚠️ 미로드'}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

      </div>

      {/* 모델 설명 */}
      <div style={styles.descCard}>
        <h3 style={{ margin: '0 0 12px', color: '#1F4E79', fontSize: '1rem' }}>📖 현재 설정 설명</h3>
        <ul style={{ margin: 0, paddingLeft: '20px', lineHeight: 2, color: '#444', fontSize: '0.9rem' }}>
          <li><b>claude-sonnet-4-6</b>: Anthropic 최신 Sonnet 모델. 속도와 품질의 균형이 우수하며 문항 생성에 최적화.</li>
          <li><b>Thinking 활성화</b>: 내부 추론 과정(ThinkingBlock)을 거쳐 더 정확한 문항을 생성.</li>
          <li><b>claude-agent-sdk</b>: 별도 API 키 없이 현재 Claude Code 로그인 세션을 그대로 활용.</li>
          <li><b>중복 검사</b>: TF-IDF 코사인 유사도 70% 이상 시 자동 재생성 (최대 2회).</li>
          <li><b>max_turns=3</b>: Claude가 문항 생성 중 최대 3번의 내부 대화 턴을 허용.</li>
        </ul>
      </div>
    </div>
  )
}

function Row({ label, value, highlight, small }) {
  return (
    <div style={styles.row}>
      <span style={styles.rowLabel}>{label}</span>
      <span style={{
        ...styles.rowValue,
        ...(highlight ? styles.rowValueHighlight : {}),
        ...(small ? { fontSize: '0.75rem', wordBreak: 'break-all' } : {}),
      }}>
        {value ?? '-'}
      </span>
    </div>
  )
}

const styles = {
  pageTitle: { margin: 0, color: '#1F4E79' },
  loading: { padding: '40px', textAlign: 'center', color: '#666' },
  error: { background: '#f8d7da', color: '#721c24', padding: '12px 16px', borderRadius: '8px' },
  btnRefresh: { padding: '8px 16px', background: 'white', color: '#1F4E79', border: '1px solid #1F4E79', borderRadius: '6px', cursor: 'pointer', fontSize: '0.9rem' },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' },
  card: { background: 'white', borderRadius: '10px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', overflow: 'hidden' },
  cardHeader: { background: '#1F4E79', padding: '12px 18px', display: 'flex', alignItems: 'center', gap: '8px' },
  cardIcon: { fontSize: '1.1rem' },
  cardTitle: { color: 'white', fontWeight: 'bold', fontSize: '0.95rem' },
  cardBody: { padding: '14px 18px', display: 'flex', flexDirection: 'column', gap: '8px' },
  row: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', fontSize: '0.88rem' },
  rowLabel: { color: '#666', flexShrink: 0, minWidth: '90px' },
  rowValue: { color: '#222', textAlign: 'right', wordBreak: 'break-word' },
  rowValueHighlight: { color: '#1F4E79', fontWeight: 'bold', background: '#e8f4fd', padding: '1px 8px', borderRadius: '4px' },
  fileRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid #f0f0f0' },
  fileLabel: { fontSize: '0.82rem', color: '#666' },
  fileName: { fontSize: '0.85rem', color: '#333', fontWeight: 'bold' },
  fileBadge: { fontSize: '0.78rem', padding: '2px 8px', borderRadius: '10px', whiteSpace: 'nowrap' },
  descCard: { background: 'white', borderRadius: '10px', padding: '18px 20px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
}
