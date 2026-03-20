import React, { useState, useEffect, useRef, useCallback } from 'react'
import { questionsAPI } from '../api.js'

const STATUS_LABELS = { draft: '초안', validated: '검증완료', approved: '승인' }
const STATUS_COLORS = { draft: '#6c757d', validated: '#ffc107', approved: '#28a745' }
const HISTORY_KEY = (id) => `q_history_${id}`
const MAX_HISTORY = 20

// 히스토리 유틸
const loadHistory = (id) => {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY(id)) || '[]') } catch { return [] }
}
const saveHistory = (id, snapshots) => {
  localStorage.setItem(HISTORY_KEY(id), JSON.stringify(snapshots.slice(0, MAX_HISTORY)))
}
const pushSnapshot = (id, data, label = '자동저장') => {
  const snapshots = loadHistory(id)
  const snapshot = {
    timestamp: new Date().toISOString(),
    label,
    data: { ...data },
  }
  // 직전과 내용이 같으면 저장 안 함
  if (snapshots.length > 0) {
    const prev = snapshots[0].data
    const fields = ['title', 'question_text', 'choice1', 'choice2', 'choice3', 'choice4', 'choice5', 'answer', 'explanation']
    const same = fields.every(f => prev[f] === data[f])
    if (same) return
  }
  saveHistory(id, [snapshot, ...snapshots])
}

export default function QuestionValidator() {
  const [questions, setQuestions] = useState([])
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState({ status: '', difficulty: '', competency_no: '' })
  const [editing, setEditing] = useState(null)
  const [editData, setEditData] = useState({})
  const [selected, setSelected] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => { loadQuestions() }, [filters])

  const loadQuestions = async () => {
    setLoading(true)
    try {
      const res = await questionsAPI.list(filters)
      setQuestions(res.data.questions || [])
      setTotal(res.data.total || 0)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const handleEdit = (q) => {
    setEditing(q.id)
    setEditData({ ...q })
    // 편집 시작 시 원본 스냅샷 저장
    pushSnapshot(q.id, q, '편집 시작')
  }

  const handleSave = async () => {
    try {
      await questionsAPI.update(editing, editData)
      pushSnapshot(editing, editData, '저장됨')
      setEditing(null)
      loadQuestions()
    } catch (e) { alert('저장 실패: ' + e.message) }
  }

  const handleDelete = async (id) => {
    if (!confirm('문항을 삭제하시겠습니까?')) return
    try {
      await questionsAPI.delete(id)
      loadQuestions()
    } catch (e) { alert('삭제 실패') }
  }

  const handleStatusChange = async (id, status) => {
    try {
      await questionsAPI.update(id, { status })
      loadQuestions()
    } catch (e) { alert('상태 변경 실패') }
  }

  const handleExportSelected = async () => {
    if (!selected.length) { alert('문항을 선택해주세요.'); return }
    try {
      const res = await questionsAPI.exportSelected(selected)
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url; a.download = 'selected_questions.xlsx'; a.click()
      URL.revokeObjectURL(url)
    } catch (e) { alert('내보내기 실패') }
  }

  const toggleSelect = (id) => {
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }

  const toggleSelectAll = () => {
    setSelected(selected.length === questions.length ? [] : questions.map(q => q.id))
  }

  return (
    <div>
      <h2 style={styles.pageTitle}>✅ 문항 검증</h2>

      {/* 필터 */}
      <div style={styles.filterBar}>
        <select style={styles.filterSelect} value={filters.status} onChange={e => setFilters({ ...filters, status: e.target.value })}>
          <option value="">전체 상태</option>
          <option value="draft">초안</option>
          <option value="validated">검증완료</option>
          <option value="approved">승인</option>
        </select>
        <select style={styles.filterSelect} value={filters.difficulty} onChange={e => setFilters({ ...filters, difficulty: e.target.value })}>
          <option value="">전체 난이도</option>
          <option value="하">하</option>
          <option value="중">중</option>
          <option value="상">상</option>
        </select>
        <input
          style={{ ...styles.filterSelect, width: '140px' }}
          placeholder="역량번호"
          value={filters.competency_no}
          onChange={e => setFilters({ ...filters, competency_no: e.target.value })}
        />
        <span style={{ color: '#666', fontSize: '0.9rem' }}>총 {total}개</span>
        {selected.length > 0 && (
          <button style={styles.btnExport} onClick={handleExportSelected}>
            📥 선택({selected.length}) Excel
          </button>
        )}
      </div>

      {loading && <div style={styles.loading}>로딩 중...</div>}

      {questions.length > 0 && (
        <table style={styles.table}>
          <thead>
            <tr style={styles.thead}>
              <th style={{ width: '30px' }}>
                <input type="checkbox" checked={selected.length === questions.length} onChange={toggleSelectAll} />
              </th>
              <th>역량NO</th>
              <th>난이도</th>
              <th>유형</th>
              <th style={{ minWidth: '200px' }}>문항 제목</th>
              <th>오답률</th>
              <th>상태</th>
              <th>액션</th>
            </tr>
          </thead>
          <tbody>
            {questions.map(q => (
              <React.Fragment key={q.id}>
                <tr style={styles.tr}>
                  <td style={styles.td}>
                    <input type="checkbox" checked={selected.includes(q.id)} onChange={() => toggleSelect(q.id)} />
                  </td>
                  <td style={styles.td}>{q.competency_no}</td>
                  <td style={styles.td}>
                    <span style={{ background: { '하': '#d4edda', '중': '#fff3cd', '상': '#f8d7da' }[q.difficulty] || '#e9ecef', padding: '2px 8px', borderRadius: '4px', fontSize: '0.85rem' }}>
                      {q.difficulty}
                    </span>
                  </td>
                  <td style={styles.td}><span style={{ fontSize: '0.82rem' }}>{q.question_type}</span></td>
                  <td style={{ ...styles.td, maxWidth: '250px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{q.title}</td>
                  <td style={{ ...styles.td, color: '#dc3545', fontWeight: 'bold' }}>{q.expected_wrong_rate}</td>
                  <td style={styles.td}>
                    <select
                      value={q.status}
                      onChange={e => handleStatusChange(q.id, e.target.value)}
                      style={{ padding: '3px 6px', fontSize: '0.82rem', border: '1px solid #ddd', borderRadius: '4px', background: STATUS_COLORS[q.status] + '22' }}
                    >
                      {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                    </select>
                  </td>
                  <td style={styles.td}>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      <button style={styles.btnSmall} onClick={() => handleEdit(q)}>수정</button>
                      <button style={{ ...styles.btnSmall, background: '#dc3545' }} onClick={() => handleDelete(q.id)}>삭제</button>
                    </div>
                  </td>
                </tr>
                {editing === q.id && (
                  <tr>
                    <td colSpan={8} style={{ padding: 0 }}>
                      <EditForm
                        questionId={q.id}
                        data={editData}
                        onChange={setEditData}
                        onSave={handleSave}
                        onCancel={() => setEditing(null)}
                      />
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      )}

      {!loading && questions.length === 0 && (
        <div style={styles.empty}>생성된 문항이 없습니다. 먼저 문항을 생성해주세요.</div>
      )}
    </div>
  )
}

function EditForm({ questionId, data, onChange, onSave, onCancel }) {
  const [showHistory, setShowHistory] = useState(false)
  const [history, setHistory] = useState([])
  const autoSaveTimer = useRef(null)

  // 히스토리 패널 열릴 때 최신 로드
  useEffect(() => {
    if (showHistory) setHistory(loadHistory(questionId))
  }, [showHistory, questionId])

  const set = useCallback((key, val) => {
    onChange(prev => {
      const updated = { ...prev, [key]: val }
      // 자동저장: 2초 디바운스
      clearTimeout(autoSaveTimer.current)
      autoSaveTimer.current = setTimeout(() => {
        pushSnapshot(questionId, updated, '자동저장')
      }, 2000)
      return updated
    })
  }, [questionId, onChange])

  const handleRestore = (snapshot) => {
    if (!confirm(`${formatTime(snapshot.timestamp)} 버전으로 되돌리시겠습니까?`)) return
    onChange(prev => ({ ...prev, ...snapshot.data }))
    setShowHistory(false)
  }

  const handleClearHistory = () => {
    if (!confirm('전체 히스토리를 삭제하시겠습니까?')) return
    localStorage.removeItem(HISTORY_KEY(questionId))
    setHistory([])
  }

  return (
    <div style={styles.editForm}>
      {/* 히스토리 패널 */}
      {showHistory && (
        <div style={styles.historyPanel}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <b style={{ color: '#1F4E79' }}>📋 편집 히스토리</b>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button style={styles.btnHistoryClear} onClick={handleClearHistory}>전체 삭제</button>
              <button style={styles.btnHistoryClose} onClick={() => setShowHistory(false)}>✕ 닫기</button>
            </div>
          </div>
          {history.length === 0 ? (
            <div style={{ color: '#999', fontSize: '0.85rem' }}>저장된 히스토리가 없습니다.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '280px', overflowY: 'auto' }}>
              {history.map((snap, i) => (
                <div key={i} style={styles.historyItem}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{
                        ...styles.historyBadge,
                        background: snap.label === '저장됨' ? '#d4edda' : snap.label === '편집 시작' ? '#cce5ff' : '#fff3cd',
                        color: snap.label === '저장됨' ? '#155724' : snap.label === '편집 시작' ? '#004085' : '#856404',
                      }}>{snap.label}</span>
                      <span style={{ fontSize: '0.82rem', color: '#555', marginLeft: '8px' }}>{formatTime(snap.timestamp)}</span>
                    </div>
                    <button style={styles.btnRestore} onClick={() => handleRestore(snap)}>↩ 복원</button>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: '#777', marginTop: '4px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {snap.data.title || '(제목 없음)'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div style={styles.editGrid}>
        {['title', 'question_text', 'choice1', 'choice2', 'choice3', 'choice4', 'choice5', 'answer', 'explanation'].map(field => (
          <div key={field} style={{ gridColumn: ['question_text', 'explanation'].includes(field) ? '1 / -1' : undefined }}>
            <label style={styles.editLabel}>{field}</label>
            {['question_text', 'explanation'].includes(field) ? (
              <textarea style={styles.editTextarea} value={data[field] || ''} onChange={e => set(field, e.target.value)} rows={4} />
            ) : (
              <input style={styles.editInput} value={data[field] || ''} onChange={e => set(field, e.target.value)} />
            )}
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: '8px', marginTop: '12px', alignItems: 'center' }}>
        <button style={styles.btnPrimary} onClick={onSave}>💾 저장</button>
        <button style={styles.btnCancel} onClick={onCancel}>취소</button>
        <button style={styles.btnHistory} onClick={() => setShowHistory(v => !v)}>
          🕐 히스토리 {loadHistory(questionId).length > 0 ? `(${loadHistory(questionId).length})` : ''}
        </button>
      </div>
    </div>
  )
}

function formatTime(iso) {
  const d = new Date(iso)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getMonth()+1}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

const styles = {
  pageTitle: { margin: '0 0 16px', color: '#1F4E79' },
  filterBar: { display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '16px', background: 'white', padding: '12px 16px', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  filterSelect: { padding: '7px 10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '0.9rem' },
  table: { width: '100%', borderCollapse: 'collapse', background: 'white', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  thead: { background: '#1F4E79', color: 'white' },
  tr: { borderBottom: '1px solid #f0f0f0' },
  td: { padding: '10px 12px', fontSize: '0.88rem', color: '#333' },
  btnSmall: { padding: '4px 10px', background: '#1F4E79', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' },
  btnExport: { padding: '7px 14px', background: '#28a745', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '0.85rem', marginLeft: 'auto' },
  loading: { padding: '20px', textAlign: 'center', color: '#666' },
  empty: { padding: '40px', textAlign: 'center', color: '#999', background: 'white', borderRadius: '8px' },
  editForm: { background: '#f8f9fa', padding: '16px', borderTop: '2px solid #1F4E79' },
  editGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' },
  editLabel: { fontSize: '0.8rem', color: '#666', fontWeight: 'bold', display: 'block', marginBottom: '3px' },
  editInput: { width: '100%', padding: '7px 10px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '0.88rem', boxSizing: 'border-box' },
  editTextarea: { width: '100%', padding: '7px 10px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '0.88rem', boxSizing: 'border-box', resize: 'vertical' },
  btnPrimary: { padding: '8px 20px', background: '#1F4E79', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' },
  btnCancel: { padding: '8px 16px', background: '#6c757d', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' },
  btnHistory: { padding: '8px 16px', background: 'white', color: '#1F4E79', border: '1px solid #1F4E79', borderRadius: '6px', cursor: 'pointer', marginLeft: 'auto' },
  historyPanel: { background: 'white', border: '1px solid #dee2e6', borderRadius: '8px', padding: '14px', marginBottom: '14px' },
  historyItem: { background: '#f8f9fa', border: '1px solid #e9ecef', borderRadius: '6px', padding: '8px 12px' },
  historyBadge: { fontSize: '0.75rem', padding: '2px 7px', borderRadius: '10px', fontWeight: 'bold' },
  btnRestore: { padding: '3px 10px', background: '#1F4E79', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem', whiteSpace: 'nowrap' },
  btnHistoryClose: { padding: '3px 10px', background: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' },
  btnHistoryClear: { padding: '3px 10px', background: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' },
}
