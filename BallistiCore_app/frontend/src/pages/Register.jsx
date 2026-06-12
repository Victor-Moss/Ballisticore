import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getCurrentRegister } from '../api/register'
import { downloadRegisterExcel } from '../api/reports'
import { downloadPermit, downloadMiniPermit } from '../api/permits'

export default function Register() {
  const [register, setRegister] = useState([])
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)
  const [downloading, setDownloading] = useState(null)

  const handleDownload = async (id, type) => {
    setDownloading(`${id}-${type}`)
    try {
      if (type === 'full') await downloadPermit(id)
      else await downloadMiniPermit(id)
    } finally {
      setDownloading(null)
    }
  }

  const handleExport = async () => {
    setExporting(true)
    try { await downloadRegisterExcel() } finally { setExporting(false) }
  }

  useEffect(() => {
    getCurrentRegister()
      .then((res) => setRegister(res.data))
      .finally(() => setLoading(false))
  }, [])

  const formatDate = (value) =>
    new Date(value).toLocaleString('en-ZA', { dateStyle: 'medium', timeStyle: 'short' })

  const ammoCell = (entry) => (
    <>
      {entry.ammunition_issued != null ? entry.ammunition_issued : '—'}
      {entry.ammunition_type && (
        <p className="text-xs text-slate-500">{entry.ammunition_type}</p>
      )}
    </>
  )

  const permitActions = (entry) =>
    entry.permit_id ? (
      <div className="flex items-center gap-2">
        <button
          onClick={() => handleDownload(entry.permit_id, 'full')}
          disabled={downloading === `${entry.permit_id}-full`}
          className="text-xs text-blue-400 hover:underline disabled:opacity-50"
        >
          {downloading === `${entry.permit_id}-full` ? '…' : 'Full'}
        </button>
        <button
          onClick={() => handleDownload(entry.permit_id, 'mini')}
          disabled={downloading === `${entry.permit_id}-mini`}
          className="text-xs text-blue-400 hover:underline disabled:opacity-50"
        >
          {downloading === `${entry.permit_id}-mini` ? '…' : 'Mini'}
        </button>
      </div>
    ) : (
      <span className="text-xs text-slate-500">—</span>
    )

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Current Register</h2>
          <p className="text-sm text-slate-400 mt-0.5">Firearms currently issued</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleExport}
            disabled={exporting}
            className="bg-slate-800 text-slate-200 text-sm px-4 py-2 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
          >
            {exporting ? 'Exporting…' : 'Export Excel'}
          </button>
          <Link
            to="/issue"
            className="bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Issue
          </Link>
          <Link
            to="/return"
            className="bg-green-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
          >
            Return
          </Link>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : register.length === 0 ? (
        <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-10 text-center">
          <p className="text-slate-500 text-sm">All firearms are currently in the armoury</p>
          <Link to="/issue" className="mt-3 inline-block text-sm text-blue-400 hover:underline">
            Issue a firearm
          </Link>
        </div>
      ) : (
        <>
          {/* Desktop / tablet: table (md and up) */}
          <div className="hidden md:block bg-slate-800/60 rounded-xl border border-slate-700 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-800/40 border-b border-slate-700">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Guard</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Firearm</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Issued</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Ammo</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Permit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/60">
                {register.map((entry) => (
                  <tr key={entry.id} className="hover:bg-slate-800/50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-100">
                        {entry.guard?.first_name} {entry.guard?.last_name}
                      </p>
                      {entry.guard?.psira_number && (
                        <p className="text-xs text-slate-400">{entry.guard.psira_number}</p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-slate-100">{entry.firearm?.make} {entry.firearm?.model}</p>
                      <p className="text-xs text-slate-400">{entry.firearm?.serial_number}</p>
                    </td>
                    <td className="px-4 py-3 text-slate-400">{formatDate(entry.issued_at)}</td>
                    <td className="px-4 py-3 text-slate-400 text-sm">{ammoCell(entry)}</td>
                    <td className="px-4 py-3">{permitActions(entry)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile: stacked cards (below md) */}
          <div className="md:hidden space-y-3">
            {register.map((entry) => (
              <div key={entry.id} className="bg-slate-800/60 rounded-xl border border-slate-700 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium text-slate-100">
                      {entry.guard?.first_name} {entry.guard?.last_name}
                    </p>
                    {entry.guard?.psira_number && (
                      <p className="text-xs text-slate-400 mt-0.5">{entry.guard.psira_number}</p>
                    )}
                    <p className="text-sm text-slate-200 mt-1">
                      {entry.firearm?.make} {entry.firearm?.model}
                      <span className="ml-1 text-xs text-slate-500">{entry.firearm?.serial_number}</span>
                    </p>
                  </div>
                  <p className="text-xs text-slate-400 text-right shrink-0">{formatDate(entry.issued_at)}</p>
                </div>
                <div className="mt-3 pt-3 border-t border-slate-700/60 flex items-end justify-between gap-3">
                  <div className="text-sm text-slate-400">
                    <span className="text-xs text-slate-500">Ammo: </span>{ammoCell(entry)}
                  </div>
                  {permitActions(entry)}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
