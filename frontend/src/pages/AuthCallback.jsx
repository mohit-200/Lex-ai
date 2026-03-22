import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'

export default function AuthCallback() {
  const navigate = useNavigate()

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    const user_id = params.get('user_id')
    const name = params.get('name')
    const email = params.get('email')
    const error = params.get('error')

    if (error || !token) {
      navigate('/login?error=google_failed')
      return
    }

    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify({ id: user_id, name, email }))
    navigate('/dashboard')
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center text-gray-400">
      <Loader2 className="w-6 h-6 animate-spin mr-2" /> Signing you in…
    </div>
  )
}
