import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  Scale, ArrowLeft, Send, Loader2, Shield, AlertTriangle,
  CheckCircle, FileText, ChevronDown, ChevronUp, MessageSquare, Info
} from 'lucide-react'
import api from '../api/client'

const SEVERITY_STYLE = {
  critical: 'border-red-500/30 bg-red-500/5',
  high:     'border-orange-500/30 bg-orange-500/5',
  medium:   'border-yellow-500/30 bg-yellow-500/5',
  low:      'border-blue-500/30 bg-blue-500/5',
}

const SEVERITY_BADGE = {
  critical: 'bg-red-500/20 text-red-400',
  high:     'bg-orange-500/20 text-orange-400',
  medium:   'bg-yellow-500/20 text-yellow-400',
  low:      'bg-blue-500/20 text-blue-400',
}

function RiskCard({ risk }) {
  const [open, setOpen] = useState(false)
  return (
    <div className={`border rounded-xl p-4 transition-all ${SEVERITY_STYLE[risk.severity]}`}>
      <div className="flex items-start justify-between gap-3 cursor-pointer" onClick={() => setOpen(!open)}>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${SEVERITY_BADGE[risk.severity]}`}>
              {risk.severity.toUpperCase()}
            </span>
            <span className="text-xs text-gray-400 bg-white/5 px-2 py-0.5 rounded-full">
              {risk.risk_type.replace(/_/g, ' ')}
            </span>
            <span className="text-xs text-gray-500">Page {risk.page}</span>
          </div>
          <p className="text-sm text-gray-300 line-clamp-2">{risk.explanation}</p>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-gray-500 flex-shrink-0 mt-1" /> : <ChevronDown className="w-4 h-4 text-gray-500 flex-shrink-0 mt-1" />}
      </div>
      {open && (
        <div className="mt-4 space-y-3 border-t border-white/5 pt-4">
          <div>
            <p className="text-xs text-gray-500 mb-1 font-medium uppercase tracking-wide">Clause</p>
            <p className="text-sm text-gray-300 bg-white/5 rounded-lg p-3 italic">"{risk.clause_text}"</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1 font-medium uppercase tracking-wide">Recommendation</p>
            <p className="text-sm text-gray-300">{risk.recommendation}</p>
          </div>
        </div>
      )}
    </div>
  )
}

function ConfidenceBadge({ confidence, is_confident }) {
  const pct = Math.round(confidence * 100)
  const color = is_confident ? 'text-green-400' : 'text-yellow-400'
  return (
    <span className={`text-xs flex items-center gap-1 ${color}`}>
      {is_confident
        ? <CheckCircle className="w-3 h-3" />
        : <AlertTriangle className="w-3 h-3" />
      }
      {pct}% confidence
    </span>
  )
}

export default function DocumentPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [doc, setDoc] = useState(null)
  const [risks, setRisks] = useState(null)
  const [messages, setMessages] = useState([])
  const [query, setQuery] = useState('')
  const [asking, setAsking] = useState(false)
  const [activeTab, setActiveTab] = useState('query')
  const bottomRef = useRef(null)

  useEffect(() => {
    api.get(`/documents/${id}/status`).then(({ data }) => setDoc(data)).catch(() => navigate('/dashboard'))
    api.get(`/documents/${id}/risks`).then(({ data }) => setRisks(data)).catch(() => {})
  }, [id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendQuery(e) {
    e.preventDefault()
    if (!query.trim() || asking) return
    const q = query.trim()
    setQuery('')
    setMessages((m) => [...m, { role: 'user', text: q }])
    setAsking(true)
    try {
      const { data } = await api.post(`/documents/${id}/query`, { query: q })
      setMessages((m) => [...m, { role: 'assistant', ...data }])
    } catch (err) {
      setMessages((m) => [...m, { role: 'error', text: 'Failed to get a response. Please try again.' }])
    } finally {
      setAsking(false)
    }
  }

  const riskScore = risks?.overall_risk_score
  const riskColor = !riskScore ? 'text-gray-400'
    : riskScore >= 7 ? 'text-red-400'
    : riskScore >= 4 ? 'text-yellow-400'
    : 'text-green-400'

  return (
    <div className="min-h-screen flex flex-col">
      {/* Navbar */}
      <nav className="glass border-b border-white/5 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center gap-4">
          <button onClick={() => navigate('/dashboard')} className="flex items-center gap-1 text-gray-400 hover:text-white transition-colors text-sm">
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
          <div className="h-4 w-px bg-white/10" />
          <Scale className="w-5 h-5 text-indigo-400" />
          <span className="font-bold gradient-text hidden sm:inline">LegalDoc AI</span>
          {doc && (
            <>
              <div className="h-4 w-px bg-white/10" />
              <span className="text-sm text-gray-400 truncate max-w-xs">{doc.filename}</span>
            </>
          )}
        </div>
      </nav>

      {!doc ? (
        <div className="flex-1 flex items-center justify-center text-gray-500">
          <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading…
        </div>
      ) : (
        <div className="flex-1 max-w-6xl mx-auto w-full px-6 py-8 flex flex-col gap-6">
          {/* Document meta */}
          <div className="glass rounded-2xl p-5 flex items-center gap-4 flex-wrap">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center flex-shrink-0">
              <FileText className="w-5 h-5 text-indigo-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-white truncate">{doc.filename}</p>
              <p className="text-xs text-gray-500">{doc.page_count} pages · {doc.chunk_count} clauses indexed</p>
            </div>
            {risks && risks.overall_risk_score != null && (
              <div className="text-right">
                <p className="text-xs text-gray-500 mb-0.5">Risk Score</p>
                <p className={`text-2xl font-bold ${riskColor}`}>{risks.overall_risk_score.toFixed(1)}<span className="text-sm font-normal text-gray-500">/10</span></p>
              </div>
            )}
          </div>

          {/* Tabs */}
          <div className="flex gap-1 glass rounded-xl p-1 w-fit">
            {['query', 'risks'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-medium transition-all
                  ${activeTab === tab ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white'}`}
              >
                {tab === 'query' ? <MessageSquare className="w-4 h-4" /> : <Shield className="w-4 h-4" />}
                {tab === 'query' ? 'Ask a Question' : `Risks ${risks ? `(${risks.risk_count})` : ''}`}
              </button>
            ))}
          </div>

          {/* Q&A Tab */}
          {activeTab === 'query' && (
            <div className="flex flex-col flex-1 glass rounded-2xl overflow-hidden" style={{ minHeight: '500px' }}>
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-5">
                {messages.length === 0 && (
                  <div className="h-full flex flex-col items-center justify-center text-center py-10 text-gray-500">
                    <MessageSquare className="w-10 h-10 mb-3 opacity-30" />
                    <p className="text-lg font-medium text-gray-400">Ask anything about this document</p>
                    <p className="text-sm mt-1">Try: "What are the payment terms?" or "Is there an auto-renewal clause?"</p>
                  </div>
                )}
                {messages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    {msg.role === 'user' ? (
                      <div className="bg-indigo-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 max-w-lg text-sm">
                        {msg.text}
                      </div>
                    ) : msg.role === 'error' ? (
                      <div className="bg-red-500/10 border border-red-500/20 text-red-400 rounded-2xl px-4 py-3 max-w-lg text-sm">
                        {msg.text}
                      </div>
                    ) : (
                      <div className="glass rounded-2xl rounded-tl-sm px-4 py-3 max-w-2xl">
                        <p className="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">{msg.answer}</p>
                        <div className="flex items-center gap-3 mt-3 pt-3 border-t border-white/5 flex-wrap">
                          <ConfidenceBadge confidence={msg.confidence} is_confident={msg.is_confident} />
                          <span className="text-xs text-gray-600">{msg.sources?.length} sources · {msg.latency_ms}ms</span>
                        </div>
                        {msg.sources?.length > 0 && (
                          <details className="mt-2">
                            <summary className="text-xs text-indigo-400 cursor-pointer hover:text-indigo-300 flex items-center gap-1">
                              <Info className="w-3 h-3" /> View source clauses
                            </summary>
                            <div className="mt-2 space-y-2">
                              {msg.sources.map((s, si) => (
                                <div key={si} className="bg-white/5 rounded-lg p-3 text-xs text-gray-400">
                                  <span className="text-indigo-400 font-medium">Page {s.page}</span>
                                  {s.clause_number && <span className="text-gray-600"> · {s.clause_number}</span>}
                                  <p className="mt-1 line-clamp-3 italic">"{s.text}"</p>
                                </div>
                              ))}
                            </div>
                          </details>
                        )}
                      </div>
                    )}
                  </div>
                ))}
                {asking && (
                  <div className="flex justify-start">
                    <div className="glass rounded-2xl rounded-tl-sm px-4 py-3">
                      <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>

              {/* Input */}
              <div className="border-t border-white/5 p-4">
                <form onSubmit={sendQuery} className="flex gap-3">
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ask a question about this document…"
                    className="flex-1 bg-white/5 border border-white/10 text-white placeholder-gray-600 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
                  />
                  <button
                    type="submit"
                    disabled={!query.trim() || asking}
                    className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white px-4 py-3 rounded-xl transition-colors flex items-center gap-2"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* Risks Tab */}
          {activeTab === 'risks' && (
            <div className="space-y-4">
              {!risks || risks.status === 'pending' ? (
                <div className="glass rounded-2xl p-12 text-center text-gray-500">
                  <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3 text-indigo-400" />
                  <p className="font-medium text-gray-400">Risk analysis in progress…</p>
                  <p className="text-sm mt-1">This runs in the background. Refresh in a minute.</p>
                </div>
              ) : risks.risks.length === 0 ? (
                <div className="glass rounded-2xl p-12 text-center text-gray-500">
                  <CheckCircle className="w-10 h-10 text-green-400 mx-auto mb-3" />
                  <p className="font-medium text-gray-300">No risks detected</p>
                  <p className="text-sm mt-1">This document looks clean across all 10 risk categories.</p>
                </div>
              ) : (
                <>
                  <div className="glass rounded-xl p-4 flex items-center gap-3">
                    <Shield className={`w-6 h-6 ${riskColor}`} />
                    <div>
                      <p className="text-sm font-medium text-white">{risks.risk_count} risk{risks.risk_count !== 1 ? 's' : ''} found</p>
                      <p className="text-xs text-gray-500">Overall score: <span className={`font-semibold ${riskColor}`}>{risks.overall_risk_score?.toFixed(1)}/10</span></p>
                    </div>
                  </div>
                  {risks.risks.map((risk, i) => <RiskCard key={i} risk={risk} />)}
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
