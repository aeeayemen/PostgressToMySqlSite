import { useState, useCallback, useRef } from 'react'
import './App.css'

// ─── Icons (Font Awesome) ─────────────────────────────────────
const Icons = {
  Upload: () => <i className="fa-solid fa-cloud-arrow-up fa-2x"></i>,
  File: () => <i className="fa-solid fa-file-code"></i>,
  Download: () => <i className="fa-solid fa-download"></i>,
  Check: () => <i className="fa-solid fa-circle-check"></i>,
  Database: () => <i className="fa-solid fa-database"></i>,
  Arrow: () => <i className="fa-solid fa-arrow-right-long"></i>,
  Sparkle: () => <i className="fa-solid fa-wand-magic-sparkles"></i>,
  AlertCircle: () => <i className="fa-solid fa-triangle-exclamation"></i>,
  Success: () => <i className="fa-solid fa-check"></i>,
}

// ─── Format file size ─────────────────────────────────────────
function formatSize(bytes) {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0) + ' ' + units[i]
}

// ─── Main App ─────────────────────────────────────────────────
function App() {
  const [file, setFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [status, setStatus] = useState('idle') // idle | uploading | done | error
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && droppedFile.name.endsWith('.sql')) {
      setFile(droppedFile)
      setStatus('idle')
      setResult(null)
      setError(null)
    } else {
      setError('يرجى رفع ملف بامتداد .sql فقط')
    }
  }, [])

  const handleFileSelect = useCallback((e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      setStatus('idle')
      setResult(null)
      setError(null)
    }
  }, [])

  const handleConvert = useCallback(async () => {
    if (!file) return
    setStatus('uploading')
    setProgress(0)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      // Simulate progress during upload
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + Math.random() * 15
        })
      }, 300)

      const response = await fetch('/api/convert', {
        method: 'POST',
        body: formData,
      })

      clearInterval(progressInterval)
      setProgress(100)

      const data = await response.json()

      if (data.success) {
        setStatus('done')
        setResult(data)
      } else {
        setStatus('error')
        setError(data.error || 'حدث خطأ أثناء التحويل')
      }
    } catch (err) {
      setStatus('error')
      setError('فشل الاتصال بالخادم. تأكد من تشغيل السيرفر.')
    }
  }, [file])

  const handleReset = useCallback(() => {
    setFile(null)
    setStatus('idle')
    setProgress(0)
    setResult(null)
    setError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [])

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <div className="logo-icon">
              <Icons.Database />
            </div>
            <div className="logo-text">
              <h1>SQL Converter</h1>
              <p className="logo-subtitle">PostgreSQL → MySQL</p>
            </div>
          </div>
          <div className="header-badge">
            <Icons.Sparkle />
            <span>تحويل آلي وذكي</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main">
        {/* Hero Section */}
        <section className="hero">
          <div className="hero-glow"></div>
          <h2 className="hero-title">
            حوّل ملفات <span className="gradient-text">PostgreSQL</span> إلى <span className="gradient-text">MySQL</span>
          </h2>
          <p className="hero-desc">
            رفع الملف • تحويل تلقائي • تحميل النتيجة
          </p>
        </section>

        {/* Features */}
        <div className="features">
          <div className="feature-pill">
            <span className="feature-dot"></span>
            إصلاح أسماء الأعمدة المحجوزة
          </div>
          <div className="feature-pill">
            <span className="feature-dot"></span>
            تحويل Boolean → 0/1
          </div>
          <div className="feature-pill">
            <span className="feature-dot"></span>
            حماية بيانات JSON
          </div>
          <div className="feature-pill">
            <span className="feature-dot"></span>
            استخراج البيانات فقط
          </div>
        </div>

        {/* Converter Card */}
        <div className="converter-card">
          {/* Upload Zone */}
          {status !== 'done' && (
            <div
              className={`dropzone ${isDragging ? 'dropzone-active' : ''} ${file ? 'dropzone-has-file' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => !file && fileInputRef.current?.click()}
            >
              <input
                id="file-input"
                ref={fileInputRef}
                type="file"
                accept=".sql"
                onChange={handleFileSelect}
                className="file-input-hidden"
              />
              {!file ? (
                <div className="dropzone-content">
                  <div className="dropzone-icon">
                    <Icons.Upload />
                  </div>
                  <p className="dropzone-title">اسحب ملف SQL هنا</p>
                  <p className="dropzone-subtitle">أو اضغط لاختيار ملف</p>
                  <span className="dropzone-badge">.sql</span>
                </div>
              ) : (
                <div className="file-info">
                  <div className="file-icon-wrapper">
                    <Icons.File />
                  </div>
                  <div className="file-details">
                    <p className="file-name">{file.name}</p>
                    <p className="file-size">{formatSize(file.size)}</p>
                  </div>
                  <button
                    className="file-remove"
                    onClick={(e) => { e.stopPropagation(); handleReset() }}
                    title="إزالة الملف"
                  >
                    ✕
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Progress Bar */}
          {status === 'uploading' && (
            <div className="progress-section">
              <div className="progress-header">
                <span className="progress-label">جارِ التحويل...</span>
                <span className="progress-percent">{Math.round(progress)}%</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${progress}%` }}></div>
              </div>
              <div className="progress-steps">
                <span className={progress > 10 ? 'step-active' : ''}>تحليل الملف</span>
                <span className={progress > 40 ? 'step-active' : ''}>إصلاح الصياغة</span>
                <span className={progress > 70 ? 'step-active' : ''}>تحويل البيانات</span>
                <span className={progress > 95 ? 'step-active' : ''}>تم!</span>
              </div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="error-banner">
              <Icons.AlertCircle />
              <span>{error}</span>
            </div>
          )}

          {/* Action Button */}
          {file && status !== 'done' && status !== 'uploading' && (
            <button id="convert-btn" className="convert-btn" onClick={handleConvert}>
              <span className="btn-content">
                <Icons.Arrow />
                <span>بدء التحويل</span>
              </span>
              <div className="btn-shine"></div>
            </button>
          )}

          {/* Results Section */}
          {status === 'done' && result && (
            <div className="results">
              <div className="results-header">
                <div className="results-check">
                  <Icons.Check />
                </div>
                <h3>اكتمل التحويل بنجاح!</h3>
              </div>

              {/* Stats */}
              <div className="stats-grid">
                <div className="stat-card">
                  <span className="stat-value">{formatSize(result.stats.original_size)}</span>
                  <span className="stat-label">حجم الملف الأصلي</span>
                </div>
                <div className="stat-card">
                  <span className="stat-value">{result.stats.insert_statements.toLocaleString()}</span>
                  <span className="stat-label">عدد عبارات INSERT</span>
                </div>
              </div>

              {/* Download Cards */}
              <div className="download-grid">
                <a
                  id="download-full"
                  href={result.files.full_converted.download_url}
                  className="download-card"
                  download
                >
                  <div className="download-card-icon full">
                    <Icons.Database />
                  </div>
                  <div className="download-card-info">
                    <h4>الملف الكامل المحوّل</h4>
                    <p>يحتوي على الهيكل والبيانات</p>
                    <span className="download-size">{formatSize(result.files.full_converted.size)}</span>
                  </div>
                  <div className="download-card-action">
                    <Icons.Download />
                    <span>تحميل</span>
                  </div>
                </a>

                <a
                  id="download-data"
                  href={result.files.data_only.download_url}
                  className="download-card"
                  download
                >
                  <div className="download-card-icon data">
                    <Icons.File />
                  </div>
                  <div className="download-card-info">
                    <h4>البيانات فقط</h4>
                    <p>INSERT فقط بدون هيكل الجداول</p>
                    <span className="download-size">{formatSize(result.files.data_only.size)}</span>
                  </div>
                  <div className="download-card-action">
                    <Icons.Download />
                    <span>تحميل</span>
                  </div>
                </a>
              </div>

              {/* Convert Another */}
              <button className="reset-btn" onClick={handleReset}>
                تحويل ملف آخر
              </button>
            </div>
          )}
        </div>

        {/* What We Fix Section */}
        <section className="fixes-section">
          <h3 className="fixes-title">ماذا يتم إصلاحه تلقائياً؟</h3>
          <div className="fixes-grid">
            <div className="fix-card">
              <div className="fix-icon">🔤</div>
              <h4>الكلمات المحجوزة</h4>
              <p>تحويل المعرّفات مثل "order" إلى <code>`order`</code></p>
            </div>
            <div className="fix-card">
              <div className="fix-icon">✓✗</div>
              <h4>القيم المنطقية</h4>
              <p>تحويل <code>true/false</code> إلى <code>1/0</code></p>
            </div>
            <div className="fix-card">
              <div className="fix-icon">{'{}'}</div>
              <h4>بيانات JSON</h4>
              <p>حماية علامات الاقتباس داخل JSON</p>
            </div>
            <div className="fix-card">
              <div className="fix-icon">🕐</div>
              <h4>المناطق الزمنية</h4>
              <p>إزالة <code>+03</code> من الطوابع الزمنية</p>
            </div>
            <div className="fix-card">
              <div className="fix-icon">⚡</div>
              <h4>INSERT IGNORE</h4>
              <p>تحويل إلى INSERT IGNORE لتجنب التكرار</p>
            </div>
            <div className="fix-card">
              <div className="fix-icon">📄</div>
              <h4>استخراج البيانات</h4>
              <p>ملف منفصل بعبارات INSERT فقط</p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>PostgreSQL → MySQL Converter &bull; Built with Python + React</p>
      </footer>
    </div>
  )
}

export default App
