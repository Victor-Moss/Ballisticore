import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getGuards, deactivateGuard, reactivateGuard, deleteGuard } from '../api/guards'
import { useAuth } from '../context/AuthContext'

export default function Guards() {
  const { user } = useAuth()
  const [guards, setGuards] = useState([])
  const [includeInactive, setIncludeInactive] = useState(false)
  const [loading, setLoading] = useState(true)
  const [actionId, setActionId] = useState(null)

  const load = () => {
    setLoading(true)
    getGuards(includeInactive)
      .then((res) => setGuards(res.data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [includeInactive])

  const toggleActive = async (guard) => {
    setActionId(guard.id)
    try {
      if (guard.is_active) await deactivateGuard(guard.id)
      else await reactivateGuard(guard.id)
      load()
    } finally {
      setActionId(null)
    }
  }

  const handleDelete = async (guard) => {
    if (!window.confirm(`Permanently delete ${guard.first_name} ${guard.last_name}? This cannot be undone.`)) return
    setActionId(guard.id)
    try {
      await deleteGuard(guard.id)
      load()
    } catch (err) {
      alert(err.response?.data?.detail || 'Delete failed')
    } finally {
      setActionId(null)
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-slate-100">Guards</h2>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
              className="rounded"
            />
            Show inactive
          </label>
          <Link
            to="/guards/new"
            className="bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            + Add Guard
          </Link>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : guards.length === 0 ? (
        <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-8 text-center">
          <p className="text-slate-500 text-sm">No guards found</p>
        </div>
      ) : (
        <div className="bg-slate-800/60 rounded-xl border border-slate-700 divide-y divide-slate-700/60">
          {guards.map((guard) => (
            <div key={guard.id} className="flex items-center justify-between px-4 py-3">
              <div>
                <p className="text-sm font-medium text-slate-100">
                  {guard.first_name} {guard.last_name}
                  {!guard.is_active && (
                    <span className="ml-2 text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">
                      Inactive
                    </span>
                  )}
                </p>
                <p className="text-xs text-slate-400">
                  {guard.psira_number && `PSIRA: ${guard.psira_number}`}
                  {guard.psira_number && guard.id_number && ' · '}
                  {guard.id_number && `ID: ${guard.id_number}`}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Link
                  to={`/guards/${guard.id}`}
                  className="text-sm text-blue-400 hover:underline"
                >
                  Edit
                </Link>
                <button
                  onClick={() => toggleActive(guard)}
                  disabled={actionId === guard.id}
                  className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${
                    guard.is_active
                      ? 'bg-red-500/10 text-red-400 hover:bg-red-100'
                      : 'bg-green-500/10 text-green-400 hover:bg-green-100'
                  } disabled:opacity-50`}
                >
                  {guard.is_active ? 'Deactivate' : 'Reactivate'}
                </button>
                {user?.is_admin && (
                  <button
                    onClick={() => handleDelete(guard)}
                    disabled={actionId === guard.id}
                    className="text-xs text-slate-500 hover:text-red-400 transition-colors disabled:opacity-50"
                  >
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
