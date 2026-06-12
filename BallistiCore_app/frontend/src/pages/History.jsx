import { useEffect, useState } from 'react'
import { getHistory } from '../api/register'
import { getGuards } from '../api/guards'
import { getFirearms } from '../api/firearms'
import { downloadHistoryExcel, downloadGuardActivityExcel } from '../api/reports'

export default function History() {
  const [history, setHistory] = useState([])
  const [guards, setGuards] = useState([])
  const [firearms, setFirearms] = useState([])
  const [filters, setFilters] = useState({
    guard_id: '', firearm_id: '', from_date: '', to_date: '',
  })
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)

  const handleExportHistory = async () => {
    setExporting(true)
    try {
      await downloadHistoryExcel({
        from_date: filters.from_date,
        to_date: filters.to_date,
        guard_id: filters.guard_id,
        firearm_id: filters.firearm_id,
      })
    } finally { setExporting(false) }
  }

  const handleExportGuard = async () => {
    if (!filters.guard_id) return
    setExporting(true)
    try { await downloadGuardActivityExcel(filters.guard_id) } finally { setExporting(false) }
  }

  useEffect(() => {
    Promise.all([getGuards(true), getFirearms(true)]).then(([gRes, fRes]) => {
      setGuards(gRes.data)
      setFirearms(fRes.data)
    }).catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    const params = {}
    if (filters.guard_id) params.guard_id = filters.guard_id
    if (filters.firearm_id) params.firearm_id = filters.firearm_id
    if (filters.from_date) params.from_date = filters.from_date
    if (filters.to_date) params.to_date = filters.to_date
    getHistory(params)
      .then((res) => setHistory(res.data))
      .finally(() => setLoading(false))
  }, [filters])

  const handleFilter = (e) => {
    setFilters((f) => ({ ...f, [e.target.name]: e.target.value }))
  }

  const clearFilters = () => {
    setFilters({ guard_id: '', firearm_id: '', from_date: '', to_date: '' })
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-slate-100">Register History</h2>
        <div className="flex gap-2">
          {filters.guard_id && (
            <button
              onClick={handleExportGuard}
              disabled={exporting}
              className="bg-purple-50 text-purple-700 text-sm px-3 py-2 rounded-lg hover:bg-purple-100 disabled:opacity-50 transition-colors"
            >
              {exporting ? '…' : 'Guard Report'}
            </button>
          )}
          <button
            onClick={handleExportHistory}
            disabled={exporting}
            className="bg-slate-800 text-slate-200 text-sm px-4 py-2 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
          >
            {exporting ? 'Exporting…' : 'Export Excel'}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-4 mb-5 grid grid-cols-1 md:grid-cols-4 gap-3">
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">Guard</label>
          <select
            name="guard_id"
            value={filters.guard_id}
            onChange={handleFilter}
            className="w-full border border-slate-700 rounded-lg px-2 py-1.5 text-sm"
          >
            <option value="">All guards</option>
            {guards.map((g) => (
              <option key={g.id} value={g.id}>
                {g.first_name} {g.last_name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">Firearm</label>
          <select
            name="firearm_id"
            value={filters.firearm_id}
            onChange={handleFilter}
            className="w-full border border-slate-700 rounded-lg px-2 py-1.5 text-sm"
          >
            <option value="">All firearms</option>
            {firearms.map((fa) => (
              <option key={fa.id} value={fa.id}>
                {fa.make} {fa.model} ({fa.serial_number})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">From</label>
          <input
            type="date"
            name="from_date"
            value={filters.from_date}
            onChange={handleFilter}
            className="w-full border border-slate-700 rounded-lg px-2 py-1.5 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">To</label>
          <input
            type="date"
            name="to_date"
            value={filters.to_date}
            onChange={handleFilter}
            className="w-full border border-slate-700 rounded-lg px-2 py-1.5 text-sm"
          />
        </div>
        <div className="md:col-span-4 flex justify-end">
          <button onClick={clearFilters} className="text-xs text-slate-500 hover:text-slate-200">
            Clear filters
          </button>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : history.length === 0 ? (
        <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-8 text-center">
          <p className="text-slate-500 text-sm">No records found</p>
        </div>
      ) : (
        <div className="bg-slate-800/60 rounded-xl border border-slate-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-800/40 border-b border-slate-700">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Guard</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Firearm</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Action</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Ammo</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Date/Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/60">
              {history.map((entry) => (
                <tr key={entry.id} className="hover:bg-slate-800/50">
                  <td className="px-4 py-3">
                    <p className="text-slate-100">{entry.guard?.first_name} {entry.guard?.last_name}</p>
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-slate-100">{entry.firearm?.make} {entry.firearm?.model}</p>
                    <p className="text-xs text-slate-400">{entry.firearm?.serial_number}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      entry.action.toLowerCase() === 'issued'
                        ? 'bg-blue-100 text-blue-300'
                        : 'bg-green-100 text-green-300'
                    }`}>
                      {entry.action.toLowerCase() === 'issued' ? 'Issued' : 'Returned'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-400 text-xs">
                    {entry.action.toLowerCase() === 'issued' && entry.ammunition_issued != null
                      ? `${entry.ammunition_issued} issued`
                      : entry.action.toLowerCase() === 'returned' && entry.ammunition_returned != null
                      ? `${entry.ammunition_returned} returned`
                      : '—'}
                    {entry.ammunition_type && (
                      <p className="text-slate-500">{entry.ammunition_type}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-400 text-xs">
                    {new Date(entry.actioned_at).toLocaleString('en-ZA', {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
