import { useEffect, useRef, useState } from 'react'
import { ArrowLeft, ArrowUpRight, FileText, Play, Upload } from 'lucide-react'
import './company-review.css'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
type CompanyDoc = { id: string; title: string; filename: string; document_type: string; chunks_count: number; created_at: string }
type Evidence = { evidence_id: string; title: string; section: string | null; excerpt: string; source_url: string | null }
type Finding = { status: string; issue: string; analysis: string; recommended_action: string; legal_evidence_ids: string[]; company_evidence_ids: string[]; human_review_required: boolean }
type Review = { summary: string; findings: Finding[]; legal_evidence: Evidence[]; company_evidence: Evidence[]; analysis_generated: boolean; disclaimer: string }

export default function CompanyReview({ onBack }: { onBack: () => void }) {
  const [documents, setDocuments] = useState<CompanyDoc[]>([])
  const [question, setQuestion] = useState('Compare G Inc employee and customer privacy practices with the indexed Indian DPDP requirements.')
  const [review, setReview] = useState<Review | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)
  const load = () => fetch(`${API}/company/documents`).then(r => { if (!r.ok) throw Error('Could not load G Inc documents'); return r.json() }).then(setDocuments).catch(e => setError(e instanceof Error ? e.message : 'Request failed'))
  useEffect(() => { load() }, [])

  async function upload(file?: File) {
    if (!file) return
    setBusy(true); setError('')
    const form = new FormData(); form.append('file', file)
    try {
      const response = await fetch(`${API}/company/documents/upload`, { method: 'POST', body: form })
      const data = await response.json()
      if (!response.ok) throw Error(data.detail || 'Policy upload failed')
      await load()
    } catch (e) { setError(e instanceof Error ? e.message : 'Upload failed') }
    finally { setBusy(false); if (fileRef.current) fileRef.current.value = '' }
  }

  async function runReview() {
    setBusy(true); setError(''); setReview(null)
    try {
      const response = await fetch(`${API}/company/review`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question, top_k: 5 }) })
      const data = await response.json()
      if (!response.ok) throw Error(data.detail || 'Review failed')
      setReview(data)
    } catch (e) { setError(e instanceof Error ? e.message : 'Review failed') }
    finally { setBusy(false) }
  }

  return <main className="company-review-page">
    <header className="company-review-header"><button className="secondary" onClick={onBack}><ArrowLeft size={15}/> Workspace</button><div><div className="eyebrow">LOCAL DEMO · G INC</div><h1>Company policy review</h1><p>Retrieve G Inc policy evidence separately from Indian legal sources.</p></div></header>
    <div className="company-demo-warning"><b>Single-company demo mode.</b> This local feature has no login or multi-tenant authorization and is disabled when <code>APP_ENV=production</code>. Do not expose it to a network or use confidential documents.</div>
    <section className="company-review-grid">
      <div className="panel company-doc-panel"><div className="panel-heading"><div><h3>G Inc company evidence</h3><p>Stored separately from legal authorities</p></div><button className="secondary" disabled={busy} onClick={() => fileRef.current?.click()}><Upload size={14}/> Add policy</button></div>
        <input ref={fileRef} type="file" accept=".md,text/markdown" hidden onChange={e => upload(e.target.files?.[0])}/>
        <div className="company-doc-list">{documents.length === 0 ? <div className="table-empty"><FileText size={22}/><b>No company drafts indexed</b><span>Upload the fictional G Inc Markdown files from data/company/g-inc.</span></div> : documents.map(doc => <div className="recent-item" key={doc.id}><div className="file-icon"><FileText size={16}/></div><div><b>{doc.title}</b><small>{doc.filename} · {doc.chunks_count} sections</small></div><span className="status-pill">Company</span></div>)}</div>
      </div>
      <div className="panel company-question-panel"><div className="panel-heading"><div><h3>Review question</h3><p>Both evidence collections are searched independently</p></div></div>
        <textarea className="company-question" value={question} onChange={e => setQuestion(e.target.value)} aria-label="Company review question"/>
        <button className="primary" disabled={busy || !question.trim()} onClick={runReview}><Play size={14}/>{busy ? 'Working…' : 'Retrieve and compare'}</button>
        <small className="company-review-help">A generated comparison requires OPENAI_API_KEY. Without it, the API only returns retrieved excerpts.</small>
      </div>
    </section>
    {error && <div className="error-banner">{error}</div>}
    {review && <section className="review-results"><div className="panel"><div className="eyebrow">REVIEW RESULT</div><h2>{review.analysis_generated ? 'Evidence-based draft analysis' : 'Evidence retrieval status'}</h2><p>{review.summary}</p><div className="review-counts"><span>Legal excerpts <b>{review.legal_evidence.length}</b></span><span>G Inc excerpts <b>{review.company_evidence.length}</b></span><span>Findings <b>{review.findings.length}</b></span></div>{review.findings.map((finding, i) => <article className="review-finding" key={i}><div className="finding-head"><b>{finding.issue}</b><span className="status-pill">{finding.status.replaceAll('_', ' ')}</span></div><p>{finding.analysis}</p><p><b>Suggested follow-up:</b> {finding.recommended_action}</p><small>Human review required · Evidence: {[...finding.legal_evidence_ids, ...finding.company_evidence_ids].join(', ') || 'none validated'}</small></article>)}<small className="review-disclaimer">{review.disclaimer}</small></div>
      <div className="review-evidence-grid"><EvidenceList title="Legal evidence" items={review.legal_evidence}/><EvidenceList title="G Inc company evidence" items={review.company_evidence}/></div>
    </section>}
  </main>
}

function EvidenceList({ title, items }: { title: string; items: Evidence[] }) {
  return <div className="panel evidence-list"><h3>{title}</h3>{items.map(item => <article className="citation" key={item.evidence_id}><div className="citation-title"><b>{item.evidence_id} · {item.title}</b><span>{item.section || 'Section not identified'}</span></div><blockquote>{item.excerpt}</blockquote>{item.source_url && <a className="evidence-link" href={item.source_url} target="_blank" rel="noreferrer">Open legal source <ArrowUpRight size={12}/></a>}</article>)}{items.length === 0 && <p className="empty-evidence">No matching evidence was retrieved.</p>}</div>
}
