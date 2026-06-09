import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getFirearms, deleteFirearm } from '../api/firearms'
import { useAuth } from '../context/AuthContext'

export default function Firearms() {
  const { user } = useAuth()
  const [firearms, setFirearms] = useState([])
  const [includeInactive, setIncludeInactive] = useState(false)
  const [loading, setLoading] = useState(true)
  const [deletingId, setDeletingId] = useState(null)

  const load = () => {
    setLoading(true)
    getFirearms(includeInactive)
      .then((res) => setFirearms(res.data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [includeInactive])

  const handleDelete = async (fa) => {
    if (!window.confirm(`Permanently delete ${fa.make} ${fa.model} (${fa.serial_number})? This cannot be undone.`)) return
    setDeletingId(fa.id)
    try {
      await deleteFirearm(fa.id)
      load()
    } catch (err) {
      alert(err.response?.data?.detail || 'Delete failed')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-slate-100">Firearms</h2>
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
            to="/firearms/new"
            className="bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            + Add Firearm
          </Link>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : firearms.length === 0 ? (
        <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-8 text-center">
          <p className="text-slate-500 text-sm">No firearms found</p>
        </div>
      ) : (
        <div className="bg-slate-800/60 rounded-xl border border-slate-700 divide-y divide-slate-700/60">
          {firearms.map((fa) => (
            <div key={fa.id} className="flex items-center justify-between px-4 py-3">
              <div>
                <p className="text-sm font-medium text-slate-100">
                  {fa.make} {fa.model}
                  {!fa.is_active && (
                    <span className="ml-2 text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">
                      Inactive
                    </span>
                  )}
                </p>
                <p className="text-xs text-slate-400">
                  S/N: {fa.serial_number}
                  {fa.type && ` · ${fa.type.charAt(0).toUpperCase() + fa.type.slice(1)}`}
                  {fa.calibre && ` · ${fa.calibre}`}
                  {fa.license_number && ` · Lic: ${fa.license_number}`}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Link
                  to={`/firearms/${fa.id}`}
                  className="text-sm text-blue-400 hover:underline"
                >
                  Edit
                </Link>
                {user?.is_admin && (
                  <button
                    onClick={() => handleDelete(fa)}
                    disabled={deletingId === fa.id}
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
