import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getGuards, guardRequestReset, guardResetPassword } from '../api/guards'
import { getFirearms } from '../api/firearms'
import { issueFirearm } from '../api/register'
import { useAuth } from '../context/AuthContext'
import { useBranding } from '../context/BrandingContext'

export default function IssueFirearm() {
  const { user } = useAuth()
  const { cit_enabled } = useBranding()
  const navigate = useNavigate()
  const [guards, setGuards] = useState([])
  const [firearms, setFirearms] = useState([])
  const [form, setForm] = useState({
    guard_id: '', firearm_id: '', notes: '',
    rounds_issued: '', period_from_time: '', valid_until_time: '',
    cit_cell_route: '', witness: '', saps_competency_number: '',
    ammunition_issued: '', firearm_inspected_correct: '',
    cit_id: '', responsible_person_name: '', guard_password: '',
  })
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const errorRef = useRef(null)
  // Inline "guard forgot password" reset, driven from the issue screen
  const [reset, setReset] = useState({ open: false, sent: false, otp: '', newPassword: '', msg: '', busy: false })

  const selectedGuard = guards.find((g) => g.id === form.guard_id)
  const selectedFirearm = firearms.find((f) => f.id === form.firearm_id)

  useEffect(() => {
    Promise.all([getGuards(), getFirearms()])
      .then(([gRes, fRes]) => {
        setGuards(gRes.data.filter((g) => g.is_active))
        setFirearms(fRes.data.filter((f) => f.is_active && f.is_available !== false))
      })
      .catch(() => setError('Could not load guards and firearms. Please refresh to try again.'))
      .finally(() => setLoading(false))
  }, [])

  // Scroll the error banner into view whenever an error appears — submit
  // failures happen at the bottom of the form, where the top banner is hidden.
  useEffect(() => {
    if (error) errorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [error])

  // Auto-fill SAPS competency when guard + firearm type are both selected
  useEffect(() => {
    if (!form.guard_id || !form.firearm_id) return
    const guard = guards.find((g) => g.id === form.guard_id)
    const firearm = firearms.find((f) => f.id === form.firearm_id)
    if (!guard || !firearm?.type) return
    const compField = `saps_comp_${firearm.type}`
    const compValue = guard[compField] || ''
    setForm((f) => ({ ...f, saps_competency_number: compValue }))
  }, [form.guard_id, form.firearm_id, guards, firearms])

  const handleChange = (e) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  }

  // Clear any typed signature / reset state when the guard changes
  useEffect(() => {
    setForm((f) => ({ ...f, guard_password: '' }))
    setReset({ open: false, sent: false, otp: '', newPassword: '', msg: '', busy: false })
  }, [form.guard_id])

  const sendOtp = async () => {
    if (!selectedGuard?.username) return
    setReset((r) => ({ ...r, busy: true, msg: '' }))
    try {
      const res = await guardRequestReset(selectedGuard.username)
      setReset((r) => ({ ...r, sent: true, busy: false, msg: res.data.message }))
    } catch {
      setReset((r) => ({ ...r, busy: false, msg: 'Could not send the code. Try again.' }))
    }
  }

  const doReset = async () => {
    if (!selectedGuard?.username) return
    setReset((r) => ({ ...r, busy: true, msg: '' }))
    try {
      await guardResetPassword(selectedGuard.username, reset.otp, reset.newPassword)
      // Auto-fill the new password so the guard can sign straight away
      setForm((f) => ({ ...f, guard_password: reset.newPassword }))
      setReset({ open: false, sent: false, otp: '', newPassword: '', msg: '', busy: false })
    } catch (err) {
      const detail = err.response?.data?.detail
      setReset((r) => ({ ...r, busy: false, msg: typeof detail === 'string' ? detail : 'Reset failed.' }))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await issueFirearm({
        guard_id: form.guard_id,
        firearm_id: form.firearm_id,
        issued_by: user.id,
        notes: form.notes || null,
        rounds_issued: form.rounds_issued ? parseInt(form.rounds_issued) : null,
        period_from_time: form.period_from_time || null,
        valid_until_time: form.valid_until_time || null,
        cit_cell_route: form.cit_cell_route || null,
        witness: form.witness || null,
        saps_competency_number: form.saps_competency_number || null,
        ammunition_issued: form.ammunition_issued ? parseInt(form.ammunition_issued) : null,
        firearm_inspected_correct: form.firearm_inspected_correct !== '' ? form.firearm_inspected_correct === 'true' : null,
        cit_id: form.cit_id || null,
        responsible_person_name: form.responsible_person_name || null,
        guard_password: form.guard_password || null,
      })
      navigate('/register')
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Failed to issue firearm')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="p-6 text-sm text-slate-500">Loading…</div>

  return (
    <div className="p-6 max-w-lg mx-auto">
      <h2 className="text-xl font-bold text-slate-100 mb-6">Issue Firearm</h2>

      <form onSubmit={handleSubmit} className="bg-slate-800/60 rounded-xl border border-slate-700 p-6 space-y-5">

        {error && (
          <p ref={errorRef} className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2">{error}</p>
        )}

        {/* Core selection */}
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Guard</label>
            <select name="guard_id" value={form.guard_id} onChange={handleChange} required
              className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-800/60">
              <option value="">Select a guard…</option>
              {guards.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.first_name} {g.last_name}{g.psira_number ? ` (${g.psira_number})` : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Firearm</label>
            <select name="firearm_id" value={form.firearm_id} onChange={handleChange} required
              className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-800/60">
              <option value="">Select a firearm…</option>
              {firearms.map((fa) => (
                <option key={fa.id} value={fa.id}>
                  {fa.make} {fa.model} — {fa.serial_number}{fa.type ? ` (${fa.type})` : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Ammunition type — auto-populated from the selected firearm */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Ammunition Type</label>
            <input
              type="text"
              value={selectedFirearm?.ammunition_type_name || ''}
              readOnly
              placeholder={selectedFirearm ? 'No ammunition type linked to this firearm' : 'Select a firearm…'}
              className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm bg-slate-800/40 text-slate-300 cursor-not-allowed focus:outline-none"
            />
          </div>
        </div>

        {/* Period */}
        <div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Period</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">From Time</label>
              <input type="time" name="period_from_time" value={form.period_from_time} onChange={handleChange}
                className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Until Time</label>
              <input type="time" name="valid_until_time" value={form.valid_until_time} onChange={handleChange}
                className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
        </div>

        {/* Issuance details */}
        <div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Issuance Details</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Rounds Issued</label>
              <input type="number" min="0" name="rounds_issued" value={form.rounds_issued} onChange={handleChange}
                className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="0" />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Ammunition Issued</label>
              <input type="number" min="0" name="ammunition_issued" value={form.ammunition_issued} onChange={handleChange}
                className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="0" />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Firearm Inspected Correct</label>
              <select name="firearm_inspected_correct" value={form.firearm_inspected_correct} onChange={handleChange}
                className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-800/60">
                <option value="">—</option>
                <option value="true">Yes</option>
                <option value="false">No</option>
              </select>
            </div>
            {cit_enabled && (
              <>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">CIT Route</label>
                  <input type="text" name="cit_cell_route" value={form.cit_cell_route} onChange={handleChange}
                    className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">CIT ID</label>
                  <input type="text" name="cit_id" value={form.cit_id} onChange={handleChange}
                    className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
              </>
            )}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Responsible Person</label>
              <input type="text" name="responsible_person_name" value={form.responsible_person_name} onChange={handleChange}
                className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Witness</label>
              <input type="text" name="witness" value={form.witness} onChange={handleChange}
                className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">SAPS Competency #</label>
              <input type="text" name="saps_competency_number" value={form.saps_competency_number} onChange={handleChange}
                className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
        </div>

        {/* Electronic signature */}
        {selectedGuard && (
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Guard Signature</p>
            {selectedGuard.has_account ? (
              <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 space-y-3">
                <p className="text-xs text-blue-300">
                  <span className="font-semibold">{selectedGuard.first_name} {selectedGuard.last_name}</span> must
                  sign for this firearm. Hand them the keyboard to enter their password.
                </p>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Guard password</label>
                  <input type="password" name="guard_password" value={form.guard_password} onChange={handleChange}
                    autoComplete="off"
                    className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Guard enters their password to sign" />
                </div>

                {!reset.open ? (
                  <button type="button" onClick={() => setReset((r) => ({ ...r, open: true }))}
                    className="text-xs text-blue-300 hover:underline">
                    Guard forgot their password?
                  </button>
                ) : (
                  <div className="border-t border-blue-500/30 pt-3 space-y-2">
                    {!reset.sent ? (
                      <button type="button" onClick={sendOtp} disabled={reset.busy}
                        className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-50">
                        {reset.busy ? 'Sending…' : `Send reset code to guard's WhatsApp`}
                      </button>
                    ) : (
                      <div className="space-y-2">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          <input type="text" inputMode="numeric" value={reset.otp}
                            onChange={(e) => setReset((r) => ({ ...r, otp: e.target.value }))}
                            placeholder="6-digit code"
                            className="border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                          <input type="password" value={reset.newPassword}
                            onChange={(e) => setReset((r) => ({ ...r, newPassword: e.target.value }))}
                            placeholder="New password"
                            className="border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                        </div>
                        <button type="button" onClick={doReset} disabled={reset.busy || !reset.otp || reset.newPassword.length < 6}
                          className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-50">
                          {reset.busy ? 'Saving…' : 'Set new password & sign'}
                        </button>
                      </div>
                    )}
                    {reset.msg && <p className="text-xs text-blue-300">{reset.msg}</p>}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
                <p className="text-xs text-amber-300">
                  This guard has no sign-in account yet, so the firearm will be issued <span className="font-semibold">unsigned</span>.
                  Create an account on the guard's profile to require an electronic signature.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Notes */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">Notes (optional)</label>
          <textarea name="notes" value={form.notes} onChange={handleChange} rows={2}
            className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none" />
        </div>

        <div className="flex gap-3 pt-1">
          <button type="submit"
            disabled={submitting || (selectedGuard?.has_account && !form.guard_password)}
            className="bg-blue-600 text-white text-sm px-6 py-2.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors">
            {submitting ? 'Issuing…' : selectedGuard?.has_account ? 'Sign & Issue Firearm' : 'Issue Firearm'}
          </button>
          <button type="button" onClick={() => navigate('/register')} className="text-sm text-slate-400 hover:text-slate-100">
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
