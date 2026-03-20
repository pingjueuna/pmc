import React, { useState } from 'react'
import QuestionGenerator from './pages/QuestionGenerator.jsx'
import QuestionValidator from './pages/QuestionValidator.jsx'
import ResultAnalysis from './pages/ResultAnalysis.jsx'
import FileManager from './pages/FileManager.jsx'
import SystemInfo from './pages/SystemInfo.jsx'

const tabs = [
  { id: 'generate', label: '📝 문항 생성' },
  { id: 'validate', label: '✅ 문항 검증' },
  { id: 'analysis', label: '📊 결과 분석' },
  { id: 'files', label: '📁 파일 관리' },
  { id: 'system', label: '🤖 시스템 정보' },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('generate')

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <h1 style={styles.title}>⚙️ SW PM 역량 인증 평가 시스템</h1>
        <p style={styles.subtitle}>문항 생성 → 검증 → 시험 → 분석 자동화 플랫폼</p>
      </header>

      <nav style={styles.nav}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            style={{ ...styles.navBtn, ...(activeTab === tab.id ? styles.navBtnActive : {}) }}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main style={styles.main}>
        {activeTab === 'generate' && <QuestionGenerator />}
        {activeTab === 'validate' && <QuestionValidator />}
        {activeTab === 'analysis' && <ResultAnalysis />}
        {activeTab === 'files' && <FileManager />}
        {activeTab === 'system' && <SystemInfo />}
      </main>
    </div>
  )
}

const styles = {
  app: { fontFamily: "'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif", minHeight: '100vh', backgroundColor: '#f0f2f5' },
  header: { backgroundColor: '#1F4E79', color: 'white', padding: '20px 30px' },
  title: { margin: 0, fontSize: '1.6rem' },
  subtitle: { margin: '4px 0 0', opacity: 0.8, fontSize: '0.9rem' },
  nav: { display: 'flex', gap: 0, backgroundColor: '#2D6AA0', padding: '0 30px' },
  navBtn: {
    padding: '12px 24px', border: 'none', background: 'transparent',
    color: 'rgba(255,255,255,0.7)', cursor: 'pointer', fontSize: '0.95rem',
    borderBottom: '3px solid transparent', transition: 'all 0.2s',
  },
  navBtnActive: {
    color: 'white', borderBottom: '3px solid #FFC000', fontWeight: 'bold',
  },
  main: { padding: '24px 30px', maxWidth: '1400px', margin: '0 auto' },
}
