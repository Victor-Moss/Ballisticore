import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCurrentRegister, returnFirearm } from '../api/register'
import { useAuth } from '../context/AuthContext'

export default function ReturnFirearm() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [register, setRegister] = useState([])
  const [form, setForm] = useState({
    firearm_id: '', notes: '', rounds_returned: '',
    firearm_returned_correct: '', in_order: '', remarks: '',
    ammunition_returned: '', permit_returned: '',
    guard_password: '', staff_password: '',
  })
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const selectedEntry = register.find((e) => e.firearm_id === form.firearm_id)
  const selectedGuard = selectedEntry?.guard

  useEffect(() => {
    getCurrentRegister()
      .then((res) => setRegister(res.data))
      .finally(() => setLoading(false))
  }, [])

  // Clear any typed signatures when the firearm being returned changes.
  useEffect(() => {
    setForm((f) => ({ ...f, guard_password: '', staff_password: '' }))
  }, [form.firearm_id])

  const handleChange = (e) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await returnFirearm({
        firearm_id: form.firearm_id,
        actioned_by: user.id,
        notes: form.notes || null,
        rounds_returned: form.rounds_returned !== '' ? parseInt(form.rounds_returned) : null,
        firearm_returned_correct: form.firearm_returned_correct !== '' ? form.firearm_returned_correct === 'true' : null,
        in_order: form.in_order !== '' ? form.in_order === 'true' : null,
        remarks: form.remarks || null,
        ammunition_returned: form.ammunition_returned !== '' ? parseInt(form.ammunition_returned) : null,
        permit_returned: form.permit_returned !== '' ? form.permit_returned === 'true' : null,
        guard_password: form.guard_password || null,
        staff_password: form.staff_password || null,
      })
      navigate('/register')
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Failed to record return')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="p-6 text-sm text-slate-500">Loading…</div>

  return (
    <div className="p-6 max-w-lg mx-auto">
      <h2 className="text-xl font-bold text-slate-100 mb-6">Return Firearm</h2>

      {register.length === 0 ? (
        <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-8 text-center">
          <p className="text-slate-500 text-sm">No firearms currently issued</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="bg-slate-800/60 rounded-xl border border-slate-700 p-6 space-y-5">

          {/* Firearm selection */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Firearm being returned</label>
            <select name="firearm_id" value={form.firearm_id} onChange={handleChange} required
              className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-800/60">
              <option value="">Select…</option>
              {register.map((entry) => (
                <option key={entry.firearm_id} value={entry.firearm_id}>
                  {entry.firearm?.make} {entry.firearm?.model} ({entry.firearm?.serial_number}) — {entry.guard?.first_name} {entry.guard?.last_name}
                </option>
              ))}
            </select>
          </div>

          {/* Return inspection */}
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Return Inspection</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Rounds Returned</label>
                <input type="number" min="0" name="rounds_returned" value={form.rounds_returned} onChange={handleChange}
                  className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Ammunition Returned</label>
                <input type="number" min="0" name="ammunition_returned" value={form.ammunition_returned} onChange={handleChange}
                  className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Firearm Returned Correct</label>
                <select name="firearm_returned_correct" value={form.firearm_returned_correct} onChange={handleChange}
                  className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-800/60">
                  <option value="">—</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">In Order</label>
                <select name="in_order" value={form.in_order} onChange={handleChange}
                  className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-800/60">
                  <option value="">—</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Permit Returned</label>
                <select name="permit_returned" value={form.permit_returned} onChange={handleChange}
                  className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-800/60">
                  <option value="">—</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>
            </div>
          </div>

          {/* Remarks */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Remarks</label>
            <textarea name="remarks" value={form.remarks} onChange={handleChange} rows={2}
              className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none" />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Notes (optional)</label>
            <textarea name="notes" value={form.notes} onChange={handleChange} rows={2}
              className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none" />
          </div>

          {/* Returning guard signature — required when the guard has an account */}
          {selectedGuard && (
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Guard Signature (Returning)</p>
              {selectedGuard.has_account ? (
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 space-y-3">
                  <p className="text-xs text-green-300">
                    <span className="font-semibold">{selectedGuard.first_name} {selectedGuard.last_name}</span> must
                    sign to return this firearm. Hand them the keyboard to enter their password.
                  </p>
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Guard password</label>
                    <input type="password" name="guard_password" value={form.guard_password} onChange={handleChange}
                      autoComplete="off"
                      className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="Guard enters their password to sign" />
                  </div>
                </div>
              ) : (
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
                  <p className="text-xs text-amber-300">
                    This guard has no sign-in account, so the return will be recorded <span className="font-semibold">unsigned</span> on their side.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Receiving staff signature — the logged-in operator signs */}
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Your Signature (Received by)</p>
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 space-y-3">
              <p className="text-xs text-blue-300">
                You (<span className="font-semibold">{user.username}</span>) must sign to receive this return. Enter your account password.
              </p>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Your password</label>
                <input type="password" name="staff_password" value={form.staff_password} onChange={handleChange}
                  autoComplete="off"
                  className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter your password to sign" />
              </div>
            </div>
          </div>

          {error && (
            <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2">{error}</p>
          )}

          <div className="flex gap-3 pt-1">
            <button type="submit"
              disabled={submitting || !form.staff_password || (selectedGuard?.has_account && !form.guard_password)}
              className="bg-green-600 text-white text-sm px-6 py-2.5 rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors">
              {submitting ? 'Recording…' : 'Sign & Record Return'}
            </button>
            <button type="button" onClick={() => navigate('/register')} className="text-sm text-slate-400 hover:text-slate-100">
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
