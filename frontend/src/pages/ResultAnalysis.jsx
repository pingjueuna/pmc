import React, { useState, useEffect } from 'react'
import { analysisAPI } from '../api.js'

export default function ResultAnalysis() {
  const [examList, setExamList] = useState([])
  const [selectedExam, setSelectedExam] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [examName, setExamName] = useState('')
  const [message, setMessage] = useState(null)

  useEffect(() => { loadList() }, [])

  const loadList = async () => {
    try {
      const res = await analysisAPI.list()
      setExamList(res.data)
    } catch (e) { console.error(e) }
  }

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    setMessage(null)
    try {
      const res = await analysisAPI.upload(file, examName || file.name)
      setMessage({ type: 'success', text: '✅ 분석 완료!' })
      await loadList()
      setSelectedExam(res.data.analysis)
    } catch (err) {
      setMessage({ type: 'error', text: '❌ 업로드 실패: ' + (err.response?.data?.detail || err.message) })
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const handleSelectExam = async (id) => {
    try {
      const res = await analysisAPI.get(id)
      setSelectedExam(res.data.analysis)
    } catch (e) { console.error(e) }
  }

  return (
    <div>
      <h2 style={styles.pageTitle}>📊 시험 결과 업로드 및 분석</h2>

      <div style={styles.uploadCard}>
        <h3 style={{ marginTop: 0, color: '#1F4E79' }}>시험 결과 업로드</h3>
        <div style={styles.uploadRow}>
          <input
            style={styles.input}
            placeholder="시험명 (예: 2025 SW PM 역량 인증 시험)"
            value={examName}
            onChange={e => setExamName(e.target.value)}
          />
          <label style={{ ...styles.uploadBtn, opacity: uploading ? 0.6 : 1 }}>
            {uploading ? '분석 중...' : '📤 결과 파일 업로드 (CSV/Excel)'}
            <input type="file" accept=".csv,.xlsx,.xls" style={{ display: 'none' }} onChange={handleUpload} disabled={uploading} />
          </label>
        </div>
        <div style={styles.formatHint}>
          파일 형식: 행=응시자, 열=문항별 정답여부(0/1) 또는 점수 컬럼 포함
        </div>
        {message && (
          <div style={{ ...styles.alert, background: message.type === 'success' ? '#d4edda' : '#f8d7da', color: message.type === 'success' ? '#155724' : '#721c24' }}>
            {message.text}
          </div>
        )}
      </div>

      <div style={styles.layout}>
        {/* 시험 목록 */}
        <div style={styles.examList}>
          <h3 style={{ margin: '0 0 12px', color: '#1F4E79' }}>과거 분석 결과</h3>
          {examList.length === 0 && <div style={styles.empty}>업로드된 시험 결과가 없습니다.</div>}
          {examList.map(exam => (
            <div
              key={exam.id}
              style={{ ...styles.examItem, borderLeft: selectedExam ? '3px solid #1F4E79' : '3px solid #dee2e6' }}
              onClick={() => handleSelectExam(exam.id)}
            >
              <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>{exam.exam_name}</div>
              <div style={{ fontSize: '0.82rem', color: '#666' }}>
                응시자 {exam.total_participants}명 · 평균 {exam.avg_score}점 · 합격률 {exam.pass_rate}%
              </div>
              <div style={{ fontSize: '0.78rem', color: '#999' }}>{exam.created_at?.slice(0, 10)}</div>
            </div>
          ))}
        </div>

        {/* 분석 결과 */}
        {selectedExam && (
          <div style={styles.analysisPanel}>
            <h3 style={{ margin: '0 0 16px', color: '#1F4E79' }}>📈 분석 결과</h3>

            <div style={styles.statsGrid}>
              <StatBox label="총 응시자" value={selectedExam.total_participants} unit="명" />
              <StatBox label="평균 점수" value={selectedExam.avg_score} unit="점" color="#1F4E79" />
              <StatBox label="합격률" value={selectedExam.pass_rate} unit="%" color={selectedExam.pass_rate >= 70 ? '#28a745' : '#dc3545'} />
              <StatBox label="합격자" value={selectedExam.pass_count} unit="명" color="#28a745" />
              <StatBox label="불합격자" value={selectedExam.fail_count} unit="명" color="#dc3545" />
              <StatBox label="표준편차" value={selectedExam.std_score} unit="점" />
            </div>

            {selectedExam.warning && (
              <div style={styles.warning}>⚠️ {selectedExam.warning}</div>
            )}

            {/* 점수 분포 */}
            {selectedExam.score_distribution && (
              <div style={styles.section}>
                <h4>점수 분포</h4>
                <div style={styles.barChart}>
                  {selectedExam.score_distribution.map(d => {
                    const max = Math.max(...selectedExam.score_distribution.map(x => x.count), 1)
                    return (
                      <div key={d.range} style={styles.barItem}>
                        <div style={styles.barLabel}>{d.range}</div>
                        <div style={styles.barTrack}>
                          <div style={{ ...styles.barFill, width: `${(d.count / max) * 100}%` }} />
                        </div>
                        <div style={styles.barCount}>{d.count}</div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* 문항별 정답률 */}
            {selectedExam.question_analysis?.length > 0 && (
              <div style={styles.section}>
                <h4>문항별 정답률 (하위 10개)</h4>
                <table style={styles.qTable}>
                  <thead>
                    <tr><th>문항</th><th>정답률</th><th>오답률</th></tr>
                  </thead>
                  <tbody>
                    {selectedExam.question_analysis
                      .sort((a, b) => a.correct_rate - b.correct_rate)
                      .slice(0, 10)
                      .map(q => (
                        <tr key={q.question}>
                          <td>{q.question}</td>
                          <td style={{ color: q.correct_rate >= 60 ? '#28a745' : '#dc3545' }}>{q.correct_rate}%</td>
                          <td style={{ color: '#dc3545' }}>{q.wrong_rate}%</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function StatBox({ label, value, unit, color = '#333' }) {
  return (
    <div style={styles.statBox}>
      <div style={styles.statLabel}>{label}</div>
      <div style={{ ...styles.statValue, color }}>{value ?? '-'}<span style={styles.statUnit}>{unit}</span></div>
    </div>
  )
}

const styles = {
  pageTitle: { margin: '0 0 16px', color: '#1F4E79' },
  uploadCard: { background: 'white', borderRadius: '8px', padding: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', marginBottom: '20px' },
  uploadRow: { display: 'flex', gap: '10px', alignItems: 'center' },
  input: { flex: 1, padding: '9px 12px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '0.95rem' },
  uploadBtn: { padding: '9px 18px', background: '#1F4E79', color: 'white', borderRadius: '6px', cursor: 'pointer', whiteSpace: 'nowrap', display: 'inline-block' },
  formatHint: { fontSize: '0.82rem', color: '#888', marginTop: '8px' },
  alert: { marginTop: '10px', padding: '10px 14px', borderRadius: '6px', fontWeight: 'bold' },
  layout: { display: 'grid', gridTemplateColumns: '280px 1fr', gap: '16px' },
  examList: { background: 'white', borderRadius: '8px', padding: '16px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', height: 'fit-content' },
  examItem: { padding: '12px', marginBottom: '8px', borderRadius: '6px', cursor: 'pointer', background: '#f8f9fa', transition: 'background 0.2s' },
  empty: { color: '#999', fontSize: '0.9rem', textAlign: 'center', padding: '20px' },
  analysisPanel: { background: 'white', borderRadius: '8px', padding: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '20px' },
  statBox: { background: '#f8f9fa', borderRadius: '8px', padding: '14px', textAlign: 'center' },
  statLabel: { fontSize: '0.82rem', color: '#666', marginBottom: '4px' },
  statValue: { fontSize: '1.6rem', fontWeight: 'bold' },
  statUnit: { fontSize: '0.85rem', marginLeft: '3px', fontWeight: 'normal' },
  section: { marginTop: '20px' },
  barChart: { display: 'flex', flexDirection: 'column', gap: '6px' },
  barItem: { display: 'flex', alignItems: 'center', gap: '8px' },
  barLabel: { width: '60px', fontSize: '0.82rem', color: '#555', textAlign: 'right' },
  barTrack: { flex: 1, background: '#e9ecef', borderRadius: '4px', height: '18px', overflow: 'hidden' },
  barFill: { background: '#1F4E79', height: '100%', borderRadius: '4px', transition: 'width 0.5s' },
  barCount: { width: '30px', fontSize: '0.82rem', color: '#555' },
  warning: { background: '#fff3cd', padding: '10px 14px', borderRadius: '6px', fontSize: '0.88rem', marginBottom: '12px' },
  qTable: { width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' },
}
