import React, { useState } from 'react'
import { questionsAPI } from '../api.js'

const DIFFICULTY_PRESETS = [
  { label: '하 1개', value: '하 1' },
  { label: '중 1개', value: '중 1' },
  { label: '상 1개', value: '상 1' },
  { label: '하 2, 중 2, 상 1', value: '하 2, 중 2, 상 1' },
  { label: '중 2, 상 1', value: '중 2, 상 1' },
  { label: '직접 입력', value: 'custom' },
]

export default function QuestionGenerator() {
  const [form, setForm] = useState({
    competency_no: '',
    difficulty_spec: '중 1',
    difficulty_custom: '',
    methodology: 'Waterfall',
    count: 1,
  })
  const [mappingPreview, setMappingPreview] = useState(null)
  const [mappingChecked, setMappingChecked] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [results, setResults] = useState([])
  const [error, setError] = useState('')
  const [selectedDifficulty, setSelectedDifficulty] = useState('중 1')
  const [isCustomDifficulty, setIsCustomDifficulty] = useState(false)

  const difficultySpec = isCustomDifficulty ? form.difficulty_custom : selectedDifficulty

  const handlePreviewMapping = async () => {
    if (!form.competency_no.trim()) {
      setError('역량번호를 입력해주세요.')
      return
    }
    setError('')
    setMappingPreview(null)
    setMappingChecked(false)
    try {
      const res = await questionsAPI.previewMapping(form.competency_no)
      setMappingPreview(res.data)
    } catch (e) {
      setError('역량 매핑 조회 실패: ' + (e.response?.data?.detail || e.message))
    }
  }

  const handleGenerate = async () => {
    if (!form.competency_no.trim()) { setError('역량번호를 입력해주세요.'); return }
    if (!difficultySpec.trim()) { setError('난이도를 선택해주세요.'); return }
    setError('')
    setGenerating(true)
    setResults([])

    try {
      const res = await questionsAPI.generate({
        competency_no: form.competency_no,
        difficulty_spec: difficultySpec,
        methodology: form.methodology,
        count: form.count,
      })
      setResults(res.data.questions || [])
    } catch (e) {
      setError('문항 생성 실패: ' + (e.response?.data?.detail || e.message))
    } finally {
      setGenerating(false)
    }
  }

  const handleExportAll = async () => {
    try {
      const res = await questionsAPI.exportAll()
      downloadBlob(res.data, 'all_questions.xlsx')
    } catch (e) {
      setError('내보내기 실패: ' + e.message)
    }
  }

  const downloadBlob = (blob, filename) => {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <h2 style={styles.pageTitle}>📝 문항 생성</h2>

      {/* 입력 폼 */}
      <div style={styles.formCard}>
        <div style={styles.formGrid}>
          {/* 역량번호 */}
          <div style={styles.formGroup}>
            <label style={styles.label}>역량번호 *</label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                style={styles.input}
                placeholder="예: LG7.1, LG2.3"
                value={form.competency_no}
                onChange={e => { setForm({ ...form, competency_no: e.target.value }); setMappingPreview(null); setMappingChecked(false) }}
              />
              <button style={styles.btnSecondary} onClick={handlePreviewMapping}>
                🔍 매핑 확인
              </button>
            </div>
          </div>

          {/* 방법론 */}
          <div style={styles.formGroup}>
            <label style={styles.label}>방법론 *</label>
            <select
              style={styles.select}
              value={form.methodology}
              onChange={e => setForm({ ...form, methodology: e.target.value })}
            >
              <option value="Waterfall">Waterfall</option>
              <option value="Agile">Agile</option>
            </select>
          </div>

          {/* 난이도 */}
          <div style={{ ...styles.formGroup, gridColumn: '1 / -1' }}>
            <label style={styles.label}>난이도 구성 *</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
              {DIFFICULTY_PRESETS.map(p => (
                <button
                  key={p.value}
                  style={{
                    ...styles.presetBtn,
                    ...((!isCustomDifficulty && selectedDifficulty === p.value) ||
                       (isCustomDifficulty && p.value === 'custom') ? styles.presetBtnActive : {})
                  }}
                  onClick={() => {
                    if (p.value === 'custom') {
                      setIsCustomDifficulty(true)
                    } else {
                      setIsCustomDifficulty(false)
                      setSelectedDifficulty(p.value)
                    }
                  }}
                >
                  {p.label}
                </button>
              ))}
            </div>
            {isCustomDifficulty && (
              <input
                style={styles.input}
                placeholder="예: 하 2, 중 2, 상 1"
                value={form.difficulty_custom}
                onChange={e => setForm({ ...form, difficulty_custom: e.target.value })}
              />
            )}
            <div style={styles.hint}>현재 난이도: <strong>{difficultySpec}</strong></div>
          </div>
        </div>

        {/* 매핑 결과 */}
        {mappingPreview && (
          <div style={{ ...styles.mappingBox, background: mappingPreview.found ? '#e8f4fd' : '#fff3cd' }}>
            <h4 style={{ margin: '0 0 8px' }}>📋 사전 매핑 결과</h4>
            {mappingPreview.found ? (
              <>
                <div style={styles.mappingRow}><b>역량번호:</b> {mappingPreview.competency_no}</div>
                <div style={styles.mappingRow}><b>역량명:</b> {mappingPreview.competency}</div>
                <div style={styles.mappingRow}><b>수행목표:</b> {mappingPreview.sub_goal}</div>
                {mappingPreview.process && <div style={styles.mappingRow}><b>수행 프로세스:</b> {mappingPreview.process}</div>}
                <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span>위 매핑 정보가 정확한가요?</span>
                  <button style={styles.btnSuccess} onClick={() => { setMappingChecked(true); handleGenerate(); }}>
                    ✅ 예, 문항 생성 진행
                  </button>
                </div>
              </>
            ) : (
              <div>⚠️ {mappingPreview.message}</div>
            )}
          </div>
        )}

        {error && <div style={styles.errorBox}>{error}</div>}

        <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
          <button
            style={{ ...styles.btnPrimary, opacity: generating ? 0.6 : 1 }}
            onClick={handleGenerate}
            disabled={generating}
          >
            {generating ? '⏳ 문항 생성 중...' : '🚀 문항 생성'}
          </button>
          {results.length > 0 && (
            <button style={styles.btnSuccess} onClick={handleExportAll}>
              📥 전체 Excel 다운로드
            </button>
          )}
        </div>
      </div>

      {/* 생성 결과 */}
      {generating && (
        <div style={styles.loadingBox}>
          <div style={styles.spinner}></div>
          <span>Claude AI가 문항을 생성하고 있습니다... (약 30~60초 소요)</span>
        </div>
      )}

      {results.length > 0 && (
        <div>
          <h3 style={{ marginTop: '24px', color: '#1F4E79' }}>
            생성된 문항 ({results.length}개)
          </h3>
          {results.map((q, i) => (
            <QuestionCard key={i} question={q} index={i + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

function QuestionCard({ question: q, index }) {
  const [expanded, setExpanded] = useState(true)
  const diffColor = { '하': '#28a745', '중': '#ffc107', '상': '#dc3545' }[q.difficulty] || '#6c757d'

  return (
    <div style={styles.questionCard}>
      <div style={styles.questionHeader} onClick={() => setExpanded(!expanded)}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ ...styles.diffBadge, background: diffColor }}>
            {q.difficulty}
          </span>
          <span style={styles.questionTitle}>[{index}] {q.title || q.question_type}</span>
          <span style={styles.typeBadge}>{q.question_type}</span>
          <span style={styles.typeBadge}>{q.methodology}</span>
        </div>
        <span>{expanded ? '▲' : '▼'}</span>
      </div>

      {expanded && (
        <div style={styles.questionBody}>
          <div style={styles.metaRow}>
            <span>역량: <b>{q.competency}</b> ({q.competency_no})</span>
            <span>예상 오답률: <b style={{ color: '#dc3545' }}>{q.expected_wrong_rate}</b></span>
            <span>오답유형: <b>{q.wrong_type_tag}</b></span>
            {q._similarity_score !== undefined && (
              <span style={{
                background: q._similarity_score >= 0.5 ? '#fff3cd' : '#d4edda',
                padding: '2px 8px', borderRadius: '4px', fontSize: '0.8rem'
              }}>
                중복유사도: <b style={{ color: q._similarity_score >= 0.7 ? '#dc3545' : q._similarity_score >= 0.5 ? '#856404' : '#155724' }}>
                  {(q._similarity_score * 100).toFixed(1)}%
                </b>
              </span>
            )}
          </div>

          <div style={styles.questionText}>{q.question_text}</div>

          <div style={styles.choices}>
            {['choice1', 'choice2', 'choice3', 'choice4', 'choice5'].map((key, ci) => {
              if (!q[key] || q[key] === 'N.A') return null
              const num = ci + 1
              const isAnswer = String(q.answer).split(',').map(s => s.trim()).includes(String(num))
              return (
                <div key={key} style={{ ...styles.choice, background: isAnswer ? '#e8f4fd' : 'white', borderColor: isAnswer ? '#1F4E79' : '#e0e0e0' }}>
                  {isAnswer && <span style={styles.answerMark}>✓</span>}
                  {q[key]}
                </div>
              )
            })}
          </div>

          <div style={styles.explanation}>
            <b>📖 정답 해설:</b> {q.explanation}
          </div>

          <div style={styles.refs}>
            <div><b>교육 모듈:</b> {q.education_module}</div>
            <div><b>참고 문서:</b> {q.reference}</div>
            <div><b>검증 결과:</b> {q.validation_result}</div>
          </div>
        </div>
      )}
    </div>
  )
}

const styles = {
  pageTitle: { margin: '0 0 16px', color: '#1F4E79' },
  formCard: { background: 'white', borderRadius: '8px', padding: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', marginBottom: '20px' },
  formGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' },
  formGroup: { display: 'flex', flexDirection: 'column', gap: '6px' },
  label: { fontWeight: 'bold', fontSize: '0.9rem', color: '#333' },
  input: { padding: '9px 12px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '0.95rem', flex: 1 },
  select: { padding: '9px 12px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '0.95rem' },
  hint: { fontSize: '0.85rem', color: '#666' },
  presetBtn: { padding: '7px 14px', border: '1px solid #ccc', borderRadius: '20px', cursor: 'pointer', background: 'white', fontSize: '0.85rem' },
  presetBtnActive: { background: '#1F4E79', color: 'white', borderColor: '#1F4E79' },
  btnPrimary: { padding: '10px 24px', background: '#1F4E79', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '1rem', fontWeight: 'bold' },
  btnSecondary: { padding: '9px 16px', background: '#6c757d', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '0.9rem', whiteSpace: 'nowrap' },
  btnSuccess: { padding: '10px 20px', background: '#28a745', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '0.9rem' },
  mappingBox: { borderRadius: '8px', padding: '16px', marginBottom: '12px', border: '1px solid #bee5eb' },
  mappingRow: { marginBottom: '6px', fontSize: '0.95rem' },
  errorBox: { background: '#f8d7da', color: '#721c24', padding: '10px 14px', borderRadius: '6px', marginTop: '8px' },
  loadingBox: { display: 'flex', alignItems: 'center', gap: '12px', padding: '20px', background: 'white', borderRadius: '8px', marginBottom: '16px', color: '#555' },
  spinner: { width: '24px', height: '24px', border: '3px solid #f3f3f3', borderTop: '3px solid #1F4E79', borderRadius: '50%', animation: 'spin 1s linear infinite' },
  questionCard: { background: 'white', borderRadius: '8px', marginBottom: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', overflow: 'hidden' },
  questionHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px', cursor: 'pointer', backgroundColor: '#f8f9fa' },
  questionTitle: { fontWeight: 'bold', fontSize: '0.95rem' },
  diffBadge: { color: 'white', padding: '3px 10px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 'bold' },
  typeBadge: { background: '#e9ecef', padding: '3px 8px', borderRadius: '4px', fontSize: '0.78rem', color: '#495057' },
  questionBody: { padding: '16px 18px' },
  metaRow: { display: 'flex', gap: '20px', fontSize: '0.85rem', color: '#555', marginBottom: '12px', flexWrap: 'wrap' },
  questionText: { background: '#f8f9fa', padding: '14px', borderRadius: '6px', lineHeight: 1.7, marginBottom: '12px', whiteSpace: 'pre-wrap' },
  choices: { display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '12px' },
  choice: { padding: '10px 14px', borderRadius: '6px', border: '1px solid #e0e0e0', fontSize: '0.9rem', lineHeight: 1.5, display: 'flex', alignItems: 'flex-start', gap: '8px' },
  answerMark: { color: '#1F4E79', fontWeight: 'bold', flexShrink: 0 },
  explanation: { background: '#e8f4fd', padding: '12px 14px', borderRadius: '6px', fontSize: '0.9rem', lineHeight: 1.6, marginBottom: '10px' },
  refs: { fontSize: '0.82rem', color: '#666', display: 'flex', flexDirection: 'column', gap: '4px' },
}
