import { useEffect, useState } from 'react'
import { getPermits, resendWhatsapp, downloadPermit, downloadMiniPermit } from '../api/permits'
import { useAuth } from '../context/AuthContext'
import { hasPerm } from '../utils/permissions'

export default function Permits() {
  const { user } = useAuth()
  const canSendWhatsapp = hasPerm(user, 'perm_send_whatsapp')
  const [permits, setPermits] = useState([])
  const [loading, setLoading] = useState(true)
  const [resending, setResending] = useState(null)
  const [resendMsg, setResendMsg] = useState({})
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

  const load = () => {
    setLoading(true)
    getPermits().then((res) => setPermits(res.data)).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleResend = async (permit) => {
    setResending(permit.id)
    setResendMsg((m) => ({ ...m, [permit.id]: '' }))
    try {
      await resendWhatsapp(permit.id)
      setResendMsg((m) => ({ ...m, [permit.id]: 'Sent!' }))
    } catch (err) {
      setResendMsg((m) => ({ ...m, [permit.id]: 'Failed' }))
    } finally {
      setResending(null)
    }
  }

  const formatDate = (value) =>
    new Date(value).toLocaleString('en-ZA', { dateStyle: 'short', timeStyle: 'short' })

  const signedBadge = (permit) =>
    permit.guard_signed ? (
      <span className="text-xs text-green-400"
        title={permit.guard_signed_at ? new Date(permit.guard_signed_at).toLocaleString('en-ZA') : ''}>
        ✓ E-signed
      </span>
    ) : (
      <span className="text-xs text-slate-500">Unsigned</span>
    )

  const waBadge = (permit) =>
    permit.whatsapp_sent ? (
      <span className="text-xs text-green-400">✓ Sent</span>
    ) : (
      <span className="text-xs text-slate-500">—</span>
    )

  const actions = (permit) => (
    <div className="flex items-center gap-3">
      <button
        onClick={() => handleDownload(permit.id, 'full')}
        disabled={downloading === `${permit.id}-full`}
        className="text-xs text-blue-400 hover:underline disabled:opacity-50"
      >
        {downloading === `${permit.id}-full` ? '…' : 'Full PDF'}
      </button>
      <button
        onClick={() => handleDownload(permit.id, 'mini')}
        disabled={downloading === `${permit.id}-mini`}
        className="text-xs text-blue-400 hover:underline disabled:opacity-50"
      >
        {downloading === `${permit.id}-mini` ? '…' : 'Mini'}
      </button>
      {canSendWhatsapp && (
        <button
          onClick={() => handleResend(permit)}
          disabled={resending === permit.id}
          className="text-xs text-purple-400 hover:underline disabled:opacity-50"
        >
          {resending === permit.id ? 'Sending…' : 'WhatsApp'}
        </button>
      )}
      {resendMsg[permit.id] && (
        <span className={`text-xs ${resendMsg[permit.id] === 'Sent!' ? 'text-green-400' : 'text-red-400'}`}>
          {resendMsg[permit.id]}
        </span>
      )}
    </div>
  )

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h2 className="text-xl font-bold text-slate-100 mb-6">Permits</h2>

      {loading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : permits.length === 0 ? (
        <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-8 text-center">
          <p className="text-slate-500 text-sm">No permits generated yet</p>
        </div>
      ) : (
        <>
          {/* Desktop / tablet: table (md and up) */}
          <div className="hidden md:block bg-slate-800/60 rounded-xl border border-slate-700 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-800/40 border-b border-slate-700">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Permit #</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Guard</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Firearm</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Generated</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Signed</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">WA</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/60">
                {permits.map((permit) => (
                  <tr key={permit.id} className="hover:bg-slate-800/50">
                    <td className="px-4 py-3 font-mono text-xs text-slate-200">{permit.permit_number}</td>
                    <td className="px-4 py-3 text-slate-100">
                      {permit.guard?.first_name} {permit.guard?.last_name}
                    </td>
                    <td className="px-4 py-3 text-slate-200">
                      {permit.firearm?.make} {permit.firearm?.model}
                      <span className="ml-1 text-xs text-slate-500">
                        {permit.firearm?.serial_number}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">{formatDate(permit.issued_at)}</td>
                    <td className="px-4 py-3">{signedBadge(permit)}</td>
                    <td className="px-4 py-3">{waBadge(permit)}</td>
                    <td className="px-4 py-3">{actions(permit)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile: stacked cards (below md) */}
          <div className="md:hidden space-y-3">
            {permits.map((permit) => (
              <div key={permit.id} className="bg-slate-800/60 rounded-xl border border-slate-700 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-slate-100 font-medium">
                      {permit.guard?.first_name} {permit.guard?.last_name}
                    </p>
                    <p className="font-mono text-xs text-slate-400 mt-0.5">{permit.permit_number}</p>
                  </div>
                  <p className="text-xs text-slate-400 text-right shrink-0">{formatDate(permit.issued_at)}</p>
                </div>

                <div className="mt-3 text-sm text-slate-200">
                  {permit.firearm?.make} {permit.firearm?.model}
                  <span className="ml-1 text-xs text-slate-500">{permit.firearm?.serial_number}</span>
                </div>

                <div className="mt-2 flex items-center gap-4">
                  <span className="text-xs text-slate-500">Signed: {signedBadge(permit)}</span>
                  <span className="text-xs text-slate-500">WA: {waBadge(permit)}</span>
                </div>

                <div className="mt-3 pt-3 border-t border-slate-700/60">
                  {actions(permit)}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
