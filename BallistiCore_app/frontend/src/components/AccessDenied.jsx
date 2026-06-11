import { ShieldAlert } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function AccessDenied({ message }) {
  return (
    <div className="p-6 flex items-center justify-center min-h-[60vh]">
      <div className="text-center max-w-md">
        <div className="mx-auto mb-4 grid place-items-center h-14 w-14 rounded-full bg-red-500/10 ring-1 ring-red-500/30">
          <ShieldAlert size={28} className="text-red-400" />
        </div>
        <h2 className="text-lg font-bold text-slate-100 mb-1">Access denied</h2>
        <p className="text-sm text-slate-400 mb-5">
          {message || "You don't have permission to access this page. Contact your administrator if you believe this is a mistake."}
        </p>
        <Link
          to="/"
          className="inline-block bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Back to Dashboard
        </Link>
      </div>
    </div>
  )
}
