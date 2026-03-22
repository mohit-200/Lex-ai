import { Link } from 'react-router-dom'
import { FileText, Shield, GitCompare, Zap, ChevronRight, Scale } from 'lucide-react'

const features = [
  {
    icon: FileText,
    title: 'Smart Document Q&A',
    desc: 'Ask natural language questions about any clause, obligation, or term in your contract and get cited answers instantly.',
  },
  {
    icon: Shield,
    title: 'Automated Risk Detection',
    desc: 'Detect unlimited liability, auto-renewals, broad IP assignments, non-competes, and 6 more risk categories automatically.',
  },
  {
    icon: GitCompare,
    title: 'Contract Comparison',
    desc: 'Upload two versions of a contract and get a plain-English breakdown of every meaningful change and its legal significance.',
  },
  {
    icon: Zap,
    title: 'Confidence Scoring',
    desc: 'Every answer includes a confidence score. The system tells you when it\'s uncertain rather than guessing.',
  },
]

export default function Landing() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Navbar */}
      <nav className="fixed top-0 inset-x-0 z-50 glass border-b border-white/5">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Scale className="w-6 h-6 text-indigo-400" />
            <span className="font-bold text-lg tracking-tight gradient-text">LegalDoc AI</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm text-gray-400 hover:text-white transition-colors px-4 py-2">
              Sign in
            </Link>
            <Link
              to="/register"
              className="text-sm bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-colors font-medium"
            >
              Get started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative flex-1 flex items-center justify-center pt-16 overflow-hidden">
        {/* Background glow */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-indigo-600/10 rounded-full blur-3xl" />
          <div className="absolute top-1/3 left-1/3 w-[400px] h-[400px] bg-purple-600/10 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-4xl mx-auto px-6 py-24 text-center">
          <div className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full text-sm text-indigo-300 mb-8">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            Powered by local AI — no data leaves your machine
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold leading-tight mb-6">
            <span className="gradient-text">Legal Intelligence</span>
            <br />
            <span className="text-white">for Every Contract</span>
          </h1>

          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            Upload any legal PDF and instantly ask questions, detect risky clauses,
            and compare contract versions — all with AI that cites its sources.
          </p>

          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link
              to="/register"
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all hover:shadow-lg hover:shadow-indigo-500/25 hover:-translate-y-0.5"
            >
              Start for free <ChevronRight className="w-5 h-5" />
            </Link>
            <Link
              to="/login"
              className="flex items-center gap-2 glass glass-hover text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all"
            >
              Sign in
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <h2 className="text-3xl font-bold text-center mb-4 gradient-text">Everything you need</h2>
        <p className="text-gray-400 text-center mb-14 text-lg">One platform for all your legal document analysis needs.</p>

        <div className="grid md:grid-cols-2 gap-6">
          {features.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="glass glass-hover rounded-2xl p-8 transition-all group">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 flex items-center justify-center mb-5 group-hover:bg-indigo-500/20 transition-colors">
                <Icon className="w-6 h-6 text-indigo-400" />
              </div>
              <h3 className="font-semibold text-lg mb-2 text-white">{title}</h3>
              <p className="text-gray-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-indigo-900/20 to-purple-900/20 pointer-events-none" />
        <div className="relative max-w-2xl mx-auto px-6 text-center">
          <h2 className="text-4xl font-bold mb-4 text-white">Ready to get started?</h2>
          <p className="text-gray-400 mb-8 text-lg">Create a free account and upload your first document in seconds.</p>
          <Link
            to="/register"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all hover:shadow-lg hover:shadow-indigo-500/25"
          >
            Create free account <ChevronRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 text-center text-gray-600 text-sm">
        <div className="flex items-center justify-center gap-2 mb-1">
          <Scale className="w-4 h-4 text-indigo-500" />
          <span className="text-gray-400 font-medium">LegalDoc AI</span>
        </div>
        Built with FastAPI · Qdrant · Ollama · React
      </footer>
    </div>
  )
}
