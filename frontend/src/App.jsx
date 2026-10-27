import React, { useEffect, useMemo, useState } from 'react'

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

function App() {
  const [token, setToken] = useState(localStorage.getItem('dp_token') || '')
  const [authMode, setAuthMode] = useState('register')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [file, setFile] = useState(null)
  const [target, setTarget] = useState('')
  const [audit, setAudit] = useState(null)
  const [experiments, setExperiments] = useState([])
  const [trainFile, setTrainFile] = useState(null)
  const [trainTarget, setTrainTarget] = useState('label')
  const [trainModel, setTrainModel] = useState('logistic_regression')
  const [trainName, setTrainName] = useState('Real baseline run')
  const [trainSeed, setTrainSeed] = useState('42')
  const [trainingResult, setTrainingResult] = useState(null)
  const [form, setForm] = useState({
    name: '', model_name: 'RandomForestClassifier', dataset_name: '',
    dataset_fingerprint: '', target_column: '', random_seed: '42',
    preprocessing: 'Missing-value handling documented; stratified split where appropriate.',
    configuration: '{"n_estimators": 100, "max_depth": 8}',
    metrics: '{"accuracy": 0.90, "f1": 0.88}'
  })
  const [compareA, setCompareA] = useState('')
  const [compareB, setCompareB] = useState('')
  const [comparison, setComparison] = useState(null)

  const request = async (path, options = {}) => {
    const headers = { ...(options.headers || {}) }
    if (token) headers.Authorization = `Bearer ${token}`
    const response = await fetch(`${API}${path}`, { ...options, headers })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`)
    return data
  }

  const loadExperiments = async () => {
    try {
      const data = await request('/api/experiments')
      setExperiments(data)
      if (data.length >= 2) {
        setCompareA(String(data[1].id))
        setCompareB(String(data[0].id))
      }
    } catch (err) { setMessage(err.message) }
  }

  useEffect(() => { if (token) loadExperiments() }, [token])

  const authSubmit = async (e) => {
    e.preventDefault(); setBusy(true); setMessage('')
    try {
      const path = authMode === 'register' ? '/api/auth/register' : '/api/auth/login'
      const body = JSON.stringify({ email, password })
      if (authMode === 'register') {
        await request(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body })
        setAuthMode('login')
        setMessage('Account created. Log in to continue.')
      } else {
        const data = await request(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body })
        localStorage.setItem('dp_token', data.access_token)
        setToken(data.access_token)
        setMessage('Signed in successfully.')
      }
    } catch (err) { setMessage(err.message) }
    finally { setBusy(false) }
  }

  const signOut = () => {
    localStorage.removeItem('dp_token'); setToken(''); setAudit(null); setExperiments([])
    setComparison(null); setMessage('Signed out.')
  }

  const runAudit = async (e) => {
    e.preventDefault()
    if (!file) return setMessage('Choose a CSV file first.')
    setBusy(true); setMessage('Auditing dataset…'); setAudit(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      if (target.trim()) fd.append('target_column', target.trim())
      const data = await request('/api/datasets/audit', { method: 'POST', body: fd })
      setAudit(data)
      setForm(prev => ({ ...prev, dataset_name: data.filename, dataset_fingerprint: data.dataset_fingerprint, target_column: target }))
      setMessage('Audit completed. Review the warnings before saving an experiment.')
    } catch (err) { setMessage(err.message) }
    finally { setBusy(false) }
  }

  const runTraining = async (e) => {
    e.preventDefault()
    if (!trainFile) return setMessage('Choose a CSV file for model training.')
    if (!trainTarget.trim()) return setMessage('Enter the target column name.')
    setBusy(true); setMessage('Training model and evaluating held-out test rows…'); setTrainingResult(null)
    try {
      const fd = new FormData()
      fd.append('file', trainFile)
      fd.append('target_column', trainTarget.trim())
      fd.append('model_type', trainModel)
      fd.append('experiment_name', trainName.trim() || 'Trained classification run')
      fd.append('random_seed', trainSeed || '42')
      const data = await request('/api/ml/train', { method: 'POST', body: fd })
      setTrainingResult(data)
      setMessage(`Training completed. Measured metrics were saved as experiment #${data.id}.`)
      await loadExperiments()
    } catch (err) { setMessage(`Training failed: ${err.message}`) }
    finally { setBusy(false) }
  }

  const saveExperiment = async (e) => {
    e.preventDefault(); setBusy(true); setMessage('')
    try {
      const body = {
        name: form.name, model_name: form.model_name, dataset_name: form.dataset_name,
        dataset_fingerprint: form.dataset_fingerprint, target_column: form.target_column || null,
        random_seed: form.random_seed === '' ? null : Number(form.random_seed),
        preprocessing: form.preprocessing,
        configuration: JSON.parse(form.configuration),
        metrics: JSON.parse(form.metrics)
      }
      await request('/api/experiments', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      setMessage('Experiment saved.')
      await loadExperiments()
    } catch (err) { setMessage(`Could not save experiment: ${err.message}. Check that configuration and metrics are valid JSON.`) }
    finally { setBusy(false) }
  }

  const compare = async () => {
    setBusy(true); setMessage(''); setComparison(null)
    try {
      const data = await request('/api/experiments/compare', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ experiment_a_id: Number(compareA), experiment_b_id: Number(compareB) })
      })
      setComparison(data)
    } catch (err) { setMessage(err.message) }
    finally { setBusy(false) }
  }

  const prettyBytes = (n) => n < 1024 ? `${n} B` : `${(n / 1024 / 1024).toFixed(2)} MB`
  const labelClass = (level) => `pill ${level || 'info'}`

  if (!token) return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="brand-mark">DP</div>
        <p className="eyebrow">ML EXPERIMENT RELIABILITY</p>
        <h1>DatasetPassport</h1>
        <p className="muted">Know what changed. Understand why results moved. Keep experiments reproducible.</p>
        <div className="tabs">
          <button className={authMode === 'register' ? 'tab active' : 'tab'} onClick={() => setAuthMode('register')}>Create account</button>
          <button className={authMode === 'login' ? 'tab active' : 'tab'} onClick={() => setAuthMode('login')}>Log in</button>
        </div>
        <form onSubmit={authSubmit} className="stack">
          <label>Email<input type="email" required maxLength="254" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" /></label>
          <label>Password<input type="password" required minLength={authMode === 'register' ? 10 : 1} maxLength="128" value={password} onChange={e => setPassword(e.target.value)} placeholder="At least 10 characters to register" /></label>
          <button className="primary" disabled={busy}>{busy ? 'Please wait…' : authMode === 'register' ? 'Create account' : 'Log in'}</button>
        </form>
        {message && <p className="notice">{message}</p>}
        <p className="small muted">Educational MVP. Use synthetic or non-sensitive data.</p>
      </section>
    </main>
  )

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark small-mark">DP</span><span>DatasetPassport</span></div>
        <div className="side-label">WORKSPACE</div>
        <a href="#audit" className="nav-item selected">◈ Dataset audit</a>
        <a href="#training" className="nav-item">✦ Train a model</a>
        <a href="#experiments" className="nav-item">⌁ Experiments</a>
        <a href="#compare" className="nav-item">⇄ Compare runs</a>
        <div className="sidebar-bottom">
          <div className="user-chip"><div className="avatar">{email ? email[0].toUpperCase() : 'U'}</div><div><strong>Workspace</strong><span>{email || 'Signed in'}</span></div></div>
          <button className="secondary full" onClick={signOut}>Sign out</button>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar"><div><p className="eyebrow">EXPERIMENT WORKSPACE</p><h1>Dataset reliability overview</h1></div><span className="status"><i /> API-connected workspace</span></header>
        {message && <div className="notice global-notice">{message}</div>}

        <section className="hero-panel">
          <div><p className="eyebrow light">DATA IN · EVIDENCE OUT</p><h2>Every experiment should leave a trail.</h2><p>Audit dataset quality, fingerprint the exact file, and compare experiment metadata to investigate performance changes.</p></div>
          <div className="hero-orbit"><div className="orbit-core">DP</div><span className="orbit-node node-one">HASH</span><span className="orbit-node node-two">ML</span><span className="orbit-node node-three">QA</span></div>
        </section>

        <section id="audit" className="section">
          <div className="section-heading"><div><p className="eyebrow">01 / DATA QUALITY</p><h2>Audit a dataset</h2><p className="muted">CSV is processed in memory and is not saved by the audit endpoint.</p></div></div>
          <form onSubmit={runAudit} className="upload-panel">
            <label className="file-drop"><span className="file-icon">↑</span><strong>{file ? file.name : 'Choose a CSV dataset'}</strong><span className="muted">Maximum 10 MB · CSV only</span><input type="file" accept=".csv,text/csv" onChange={e => setFile(e.target.files?.[0] || null)} /></label>
            <div className="form-row"><label>Target column (optional)<input value={target} onChange={e => setTarget(e.target.value)} placeholder="e.g. label" /></label><button className="primary" disabled={busy}>{busy ? 'Working…' : 'Run dataset audit'}</button></div>
          </form>

          {audit && <div className="results">
            <div className="metric-grid">
              <Metric label="Rows" value={audit.rows.toLocaleString()} />
              <Metric label="Columns" value={audit.columns_count} />
              <Metric label="Duplicate rows" value={audit.duplicate_rows} />
              <Metric label="Missing cells" value={audit.missing_cells} />
            </div>
            <div className="panel fingerprint"><div><span className="eyebrow">SHA-256 DATASET FINGERPRINT</span><code>{audit.dataset_fingerprint}</code><p className="muted small">{prettyBytes(audit.file_bytes)} · {audit.filename}</p></div><button className="secondary" onClick={() => navigator.clipboard?.writeText(audit.dataset_fingerprint)}>Copy hash</button></div>
            <div className="panel"><h3>Audit findings</h3>{audit.warnings.map((w, i) => <div className="finding" key={i}><span className={labelClass(w.level)}>{w.level}</span><div><strong>{w.code.replaceAll('_', ' ')}</strong><p>{w.message}</p></div></div>)}</div>
            {audit.class_balance && <div className="panel"><h3>Target class distribution</h3>{audit.class_balance.map(c => <div className="bar-row" key={c.label}><span>{c.label}</span><div className="bar-track"><div className="bar-fill" style={{ width: `${Math.max(2, c.count / Math.max(...audit.class_balance.map(x => x.count)) * 100)}%` }} /></div><strong>{c.count}</strong></div>)}</div>}
            <div className="panel"><h3>Column profile</h3><div className="table-wrap"><table><thead><tr><th>Column</th><th>Type</th><th>Missing</th><th>Unique</th></tr></thead><tbody>{audit.columns.map(c => <tr key={c.name}><td>{c.name}</td><td>{c.dtype}</td><td>{c.missing_count} ({c.missing_percent}%)</td><td>{c.unique_count}</td></tr>)}</tbody></table></div></div>
            {audit.outlier_summary?.length > 0 && <div className="panel"><h3>Numeric anomaly indicators</h3><p className="muted small">Isolation Forest flags unusual values for review; flags do not prove data errors.</p><div className="table-wrap"><table><thead><tr><th>Column</th><th>Sample</th><th>Flagged</th><th>Rate</th></tr></thead><tbody>{audit.outlier_summary.map(x => <tr key={x.column}><td>{x.column}</td><td>{x.sample_size}</td><td>{x.flagged_count}</td><td>{x.flagged_percent}%</td></tr>)}</tbody></table></div></div>}
          </div>}
        </section>

        <section id="training" className="section">
          <div className="section-heading"><div><p className="eyebrow">02 / REAL MACHINE LEARNING</p><h2>Train and evaluate a model</h2><p className="muted">Trains a classifier on a training split, evaluates only on held-out rows, and saves measured metrics to your experiment history.</p></div></div>
          <form className="panel stack" onSubmit={runTraining}>
            <div className="form-grid">
              <label className="wide">CSV dataset<input type="file" accept=".csv,text/csv" required onChange={e => { setTrainFile(e.target.files?.[0] || null); setTrainingResult(null) }} /></label>
              <label>Target column<input required maxLength="180" value={trainTarget} onChange={e => setTrainTarget(e.target.value)} placeholder="e.g. label" /></label>
              <label>Classification model<select value={trainModel} onChange={e => setTrainModel(e.target.value)}><option value="logistic_regression">Logistic Regression</option><option value="decision_tree">Decision Tree (max depth 5)</option></select></label>
              <label>Experiment name<input required maxLength="120" value={trainName} onChange={e => setTrainName(e.target.value)} /></label>
              <label>Random seed<input type="number" min="0" max="2147483647" value={trainSeed} onChange={e => setTrainSeed(e.target.value)} /></label>
            </div>
            <p className="muted small">Rows with missing target labels are excluded. Numeric missing values are median-imputed; categorical missing values are filled with the most frequent value. Preprocessing is fitted on training rows only. Use a target with at least two classes and enough examples per class.</p>
            <button className="primary align-self-start" disabled={busy || !trainFile}>{busy ? 'Training…' : 'Train, evaluate and save run'}</button>
          </form>
          {trainingResult && <div className="panel">
            <div className="panel-heading"><h3>Measured held-out test metrics</h3><span className="pill success">Saved run #{trainingResult.id}</span></div>
            <p className="muted small">{trainingResult.model_name} · {trainingResult.dataset_name} · target: {trainingResult.target_column}</p>
            <div className="metric-grid">{Object.entries(trainingResult.metrics || {}).map(([key, value]) => <Metric key={key} label={key.replaceAll('_', ' ')} value={Number(value).toFixed(3)} />)}</div>
            <p className="muted small">Training rows: {trainingResult.configuration?.actual_train_rows} · Test rows: {trainingResult.configuration?.actual_test_rows} · Random seed: {trainingResult.random_seed}</p>
            <div className="panel fingerprint"><div><span className="eyebrow">DATASET SHA-256</span><code>{trainingResult.dataset_fingerprint}</code></div><button className="secondary" type="button" onClick={() => navigator.clipboard?.writeText(trainingResult.dataset_fingerprint)}>Copy hash</button></div>
          </div>}
        </section>

        <section id="experiments" className="section">
          <div className="section-heading"><div><p className="eyebrow">02 / REPRODUCIBILITY</p><h2>Register an experiment</h2><p className="muted">Save metadata manually, or use Train a model above to record metrics measured on held-out data.</p></div></div>
          <form className="panel stack" onSubmit={saveExperiment}>
            <div className="form-grid">
              <label>Experiment name<input required maxLength="120" value={form.name} onChange={e => setForm({...form, name:e.target.value})} placeholder="Baseline run" /></label>
              <label>Model name<input required maxLength="120" value={form.model_name} onChange={e => setForm({...form, model_name:e.target.value})} placeholder="RandomForestClassifier" /></label>
              <label>Dataset name<input required maxLength="180" value={form.dataset_name} onChange={e => setForm({...form, dataset_name:e.target.value})} placeholder="dataset.csv" /></label>
              <label>Random seed<input type="number" min="0" value={form.random_seed} onChange={e => setForm({...form, random_seed:e.target.value})} /></label>
              <label className="wide">Dataset fingerprint (SHA-256)<input required pattern="[a-fA-F0-9]{64}" value={form.dataset_fingerprint} onChange={e => setForm({...form, dataset_fingerprint:e.target.value})} placeholder="Run an audit to populate this" /></label>
              <label className="wide">Preprocessing and split notes<textarea rows="2" value={form.preprocessing} onChange={e => setForm({...form, preprocessing:e.target.value})} /></label>
              <label>Configuration JSON<textarea rows="4" required value={form.configuration} onChange={e => setForm({...form, configuration:e.target.value})} /></label>
              <label>Metrics JSON<textarea rows="4" required value={form.metrics} onChange={e => setForm({...form, metrics:e.target.value})} /></label>
            </div>
            <button className="primary align-self-start" disabled={busy}>Save experiment run</button>
          </form>
          <div className="panel">
            <div className="panel-heading"><h3>Saved experiment runs</h3><button className="secondary" onClick={loadExperiments}>Refresh</button></div>
            {experiments.length === 0 ? <p className="muted">No experiments yet. Audit a dataset and save your first run.</p> : <div className="table-wrap"><table><thead><tr><th>Name</th><th>Model</th><th>Dataset</th><th>Metrics</th><th>Created</th></tr></thead><tbody>{experiments.map(x => <tr key={x.id}><td><strong>{x.name}</strong><span className="subline">Run #{x.id}</span></td><td>{x.model_name}</td><td title={x.dataset_fingerprint}>{x.dataset_name}<span className="subline">{x.dataset_fingerprint.slice(0, 12)}…</span></td><td><code>{JSON.stringify(x.metrics)}</code></td><td>{x.created_at ? new Date(x.created_at).toLocaleString() : '—'}</td></tr>)}</tbody></table></div>}
          </div>
        </section>

        <section id="compare" className="section">
          <div className="section-heading"><div><p className="eyebrow">03 / CHANGE ANALYSIS</p><h2>Compare two runs</h2><p className="muted">Find recorded differences that may explain metric changes.</p></div></div>
          <div className="panel compare-panel">
            <div className="form-grid">
              <label>Baseline run<select value={compareA} onChange={e => setCompareA(e.target.value)}><option value="">Select a run</option>{experiments.map(x => <option key={x.id} value={x.id}>#{x.id} — {x.name}</option>)}</select></label>
              <label>Comparison run<select value={compareB} onChange={e => setCompareB(e.target.value)}><option value="">Select a run</option>{experiments.map(x => <option key={x.id} value={x.id}>#{x.id} — {x.name}</option>)}</select></label>
            </div>
            <button className="primary" disabled={busy || !compareA || !compareB || compareA === compareB} onClick={compare}>Compare experiments</button>
          </div>
          {comparison && <div className="panel"><h3>Metric deltas (comparison − baseline)</h3><div className="metric-grid">{Object.entries(comparison.metric_deltas_b_minus_a).map(([k,v]) => <Metric key={k} label={k} value={v > 0 ? `+${v}` : v} />)}</div><h3 className="mt">Diagnostic hints</h3>{comparison.diagnostic_hints.map((hint,i) => <div className="finding" key={i}><span className="pill warning">Review</span><p>{hint}</p></div>)}<p className="muted small">{comparison.interpretation_note}</p></div>}
        </section>
        <footer>DatasetPassport · Educational MVP · Results are diagnostic clues, not proof of causation.</footer>
      </main>
    </div>
  )
}

function Metric({ label, value }) {
  return <div className="metric-card"><span>{label}</span><strong>{value}</strong></div>
}

export default App
