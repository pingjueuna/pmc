import React, { useState, useEffect } from 'react'
import { filesAPI } from '../api.js'

const FILE_TYPES = [
  { key: 'competency', label: '역량 정의서', filename: 'LG SW PMCompetency_v1.2.xlsx', required: true },
  { key: 'item_bank', label: '문항 Bank', filename: 'PM Competency Item Bank.xlsx', required: true },
  { key: 'curriculum', label: '교육 커리큘럼', filename: 'Project_Management_Course_Curriculum_ver2025.xlsx', required: false },
]

export default function FileManager() {
  const [fileStatus, setFileStatus] = useState(null)
  const [uploading, setUploading] = useState({})
  const [message, setMessage] = useState(null)

  useEffect(() => { loadStatus() }, [])

  const loadStatus = async () => {
    try {
      const res = await filesAPI.status()
      setFileStatus(res.data)
    } catch (e) {
      console.error(e)
    }
  }

  const handleUpload = async (fileType, e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(prev => ({ ...prev, [fileType]: true }))
    setMessage(null)
    try {
      await filesAPI.upload(fileType, file)
      setMessage({ type: 'success', text: `✅ ${file.name} 업로드 완료` })
      await loadStatus()
    } catch (err) {
      setMessage({ type: 'error', text: `❌ 업로드 실패: ${err.response?.data?.detail || err.message}` })
    } finally {
      setUploading(prev => ({ ...prev, [fileType]: false }))
      e.target.value = ''
    }
  }

  const refFiles = fileStatus?.reference_files || {}
  const itemBank = fileStatus?.item_bank_summary || {}

  return (
    <div>
      <h2 style={styles.pageTitle}>📁 참조 파일 관리</h2>
      <p style={styles.desc}>문항 생성에 사용할 참조 파일을 업로드하세요. 구글 드라이브에서 다운로드 후 업로드할 수 있습니다.</p>

      {message && (
        <div style={{ ...styles.alert, background: message.type === 'success' ? '#d4edda' : '#f8d7da', color: message.type === 'success' ? '#155724' : '#721c24' }}>
          {message.text}
        </div>
      )}

      <div style={styles.grid}>
        {FILE_TYPES.map(ft => {
          const status = refFiles[ft.key] || {}
          const loaded = status.exists
          return (
            <div key={ft.key} style={{ ...styles.card, borderLeft: `4px solid ${loaded ? '#28a745' : ft.required ? '#dc3545' : '#ffc107'}` }}>
              <div style={styles.cardHeader}>
                <span style={styles.fileLabel}>{ft.label}</span>
                {ft.required && <span style={styles.requiredBadge}>필수</span>}
                <span style={{ ...styles.statusBadge, background: loaded ? '#28a745' : '#dc3545' }}>
                  {loaded ? '✅ 로드됨' : '❌ 미로드'}
                </span>
              </div>
              <div style={styles.filename}>{ft.filename}</div>
              {loaded && (
                <div style={styles.fileInfo}>
                  크기: {(status.size_bytes / 1024).toFixed(1)} KB
                  {ft.key === 'item_bank' && itemBank.total > 0 && (
                    <span> · 문항 {itemBank.total}개</span>
                  )}
                </div>
              )}
              <label style={{ ...styles.uploadBtn, opacity: uploading[ft.key] ? 0.6 : 1 }}>
                {uploading[ft.key] ? '업로드 중...' : loaded ? '🔄 재업로드' : '📤 업로드'}
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  style={{ display: 'none' }}
                  onChange={e => handleUpload(ft.key, e)}
                  disabled={uploading[ft.key]}
                />
              </label>
            </div>
          )
        })}

        {/* 기타 파일 업로드 */}
        <div style={{ ...styles.card, borderLeft: '4px solid #6c757d' }}>
          <div style={styles.cardHeader}>
            <span style={styles.fileLabel}>기타 참조 파일</span>
          </div>
          <div style={styles.filename}>PMBOK, Agile Guide, Udemy 자료 등</div>
          <div style={styles.fileInfo}>PDF, Excel, Word 파일 업로드 가능</div>
          <label style={styles.uploadBtn}>
            📤 파일 업로드
            <input
              type="file"
              accept=".xlsx,.xls,.pdf,.doc,.docx"
              style={{ display: 'none' }}
              onChange={e => handleUpload('custom', e)}
            />
          </label>
        </div>
      </div>

      {fileStatus?.other_files?.length > 0 && (
        <div style={styles.otherFiles}>
          <h3>기타 업로드된 파일</h3>
          {fileStatus.other_files.map(f => (
            <div key={f.filename} style={styles.otherFileItem}>
              📄 {f.filename} ({(f.size_bytes / 1024).toFixed(1)} KB)
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const styles = {
  pageTitle: { margin: '0 0 8px', color: '#1F4E79' },
  desc: { color: '#666', marginBottom: '20px' },
  alert: { padding: '12px 16px', borderRadius: '6px', marginBottom: '16px', fontWeight: 'bold' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' },
  card: { background: 'white', borderRadius: '8px', padding: '16px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  cardHeader: { display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' },
  fileLabel: { fontWeight: 'bold', fontSize: '1rem', flex: 1 },
  requiredBadge: { background: '#dc3545', color: 'white', fontSize: '0.7rem', padding: '2px 6px', borderRadius: '4px' },
  statusBadge: { color: 'white', fontSize: '0.75rem', padding: '3px 8px', borderRadius: '4px' },
  filename: { color: '#555', fontSize: '0.85rem', marginBottom: '6px', fontFamily: 'monospace' },
  fileInfo: { color: '#888', fontSize: '0.8rem', marginBottom: '12px' },
  uploadBtn: {
    display: 'inline-block', padding: '8px 16px', background: '#1F4E79', color: 'white',
    borderRadius: '6px', cursor: 'pointer', fontSize: '0.9rem', transition: 'opacity 0.2s',
  },
  otherFiles: { marginTop: '24px' },
  otherFileItem: { padding: '6px 0', color: '#555', borderBottom: '1px solid #eee' },
}
