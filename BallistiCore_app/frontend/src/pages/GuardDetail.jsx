import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getGuard, createGuard, updateGuard, setGuardAccount, resetGuardPassword, deleteGuardAccount } from '../api/guards'
import { getFirearms } from '../api/firearms'
import { getPermissionsForGuard, setPermission, deletePermission } from '../api/permissions'
import api from '../api/client'

const WEAPON_TYPES = ['carbine', 'handgun', 'rifle', 'shotgun']

const BLANK_FORM = {
  first_name: '', last_name: '', id_number: '', psira_number: '',
  cell_phone: '', location_id: '', region: '', personnel_number: '',
  username: '', password: '',
  saps_comp_carbine: '', saps_expiry_carbine: '',
  saps_comp_handgun: '', saps_expiry_handgun: '',
  saps_comp_rifle:   '', saps_expiry_rifle: '',
  saps_comp_shotgun: '', saps_expiry_shotgun: '',
  permitted_carbine: false, permitted_handgun: false,
  permitted_rifle: false,   permitted_shotgun: false,
}

export default function GuardDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isNew = id === 'new'

  const [form, setForm] = useState(BLANK_FORM)
  const [firearms, setFirearms] = useState([])
  const [permissions, setPermissions] = useState([])
  const [citRoutes, setCitRoutes] = useState([])
  const [newRoute, setNewRoute] = useState({ route_name: '', cell_phone: '' })
  const [loading, setLoading] = useState(!isNew)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const errorRef = useRef(null)
  const [success, setSuccess] = useState('')

  // Sign-in account
  const [account, setAccount] = useState(null)  // { has_account, username, must_change_password }
  const [acct, setAcct] = useState({ username: '', password: '' })
  const [acctMsg, setAcctMsg] = useState('')
  const [acctBusy, setAcctBusy] = useState(false)
  const [tempPw, setTempPw] = useState('')

  useEffect(() => {
    getFirearms().then((res) => setFirearms(res.data)).catch(() => {})
    if (!isNew) {
      getGuard(id).then((res) => {
        const g = res.data
        setForm({
          first_name: g.first_name || '',
          last_name: g.last_name || '',
          id_number: g.id_number || '',
          psira_number: g.psira_number || '',
          cell_phone: g.cell_phone || '',
          location_id: g.location_id || '',
          region: g.region || '',
          personnel_number: g.personnel_number || '',
          saps_comp_carbine: g.saps_comp_carbine || '',
          saps_expiry_carbine: g.saps_expiry_carbine || '',
          saps_comp_handgun: g.saps_comp_handgun || '',
          saps_expiry_handgun: g.saps_expiry_handgun || '',
          saps_comp_rifle: g.saps_comp_rifle || '',
          saps_expiry_rifle: g.saps_expiry_rifle || '',
          saps_comp_shotgun: g.saps_comp_shotgun || '',
          saps_expiry_shotgun: g.saps_expiry_shotgun || '',
          permitted_carbine: g.permitted_carbine,
          permitted_handgun: g.permitted_handgun,
          permitted_rifle: g.permitted_rifle,
          permitted_shotgun: g.permitted_shotgun,
        })
        setCitRoutes(g.cit_routes || [])
        setAccount({ has_account: g.has_account, username: g.username, must_change_password: g.must_change_password })
        // Suggest a username (first initial + surname) when none exists yet
        const suggested = `${(g.first_name || '').charAt(0)}${g.last_name || ''}`.toLowerCase().replace(/\s+/g, '')
        setAcct((a) => ({ ...a, username: g.username || suggested }))
      })
        .catch(() => setError('Could not load this guard. Please go back and try again.'))
        .finally(() => setLoading(false))
      getPermissionsForGuard(id).then((res) => setPermissions(res.data)).catch(() => {})
    }
  }, [id, isNew])

  // Scroll the error banner into view whenever an error appears — submit
  // failures happen at the bottom of the form, where the top banner is hidden.
  useEffect(() => {
    if (error) errorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [error])

  const handleChange = (e) => {
    const val = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [e.target.name]: val }))
  }

  // For new guards, suggest a username (first initial + surname) until the
  // operator types their own. Only fills when the field is empty.
  useEffect(() => {
    if (!isNew) return
    setForm((f) => {
      if (f.username) return f
      const suggested = `${(f.first_name || '').charAt(0)}${f.last_name || ''}`.toLowerCase().replace(/\s+/g, '')
      return suggested ? { ...f, username: suggested } : f
    })
  }, [form.first_name, form.last_name, isNew])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      if (isNew) {
        await createGuard({
          ...form,
          location_id:         form.location_id         || null,
          saps_expiry_carbine: form.saps_expiry_carbine || null,
          saps_expiry_handgun: form.saps_expiry_handgun || null,
          saps_expiry_rifle:   form.saps_expiry_rifle   || null,
          saps_expiry_shotgun: form.saps_expiry_shotgun || null,
          username: form.username.trim(),
          password: form.password,
        })
        navigate('/guards')
      } else {
        // Account is managed via the dedicated Sign-in Account card, not here
        const { first_name, last_name, username, password, ...editableFields } = form
        await updateGuard(id, {
          ...editableFields,
          location_id: editableFields.location_id || null,
          saps_expiry_carbine: editableFields.saps_expiry_carbine || null,
          saps_expiry_handgun: editableFields.saps_expiry_handgun || null,
          saps_expiry_rifle: editableFields.saps_expiry_rifle || null,
          saps_expiry_shotgun: editableFields.saps_expiry_shotgun || null,
        })
        setSuccess('Guard updated.')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save guard')
    } finally {
      setSaving(false)
    }
  }

  const [permError, setPermError] = useState('')

  const togglePermission = async (firearmId) => {
    setPermError('')
    const existing = permissions.find((p) => p.firearm_id === firearmId)
    try {
      if (existing) {
        await deletePermission(existing.id)
        setPermissions((prev) => prev.filter((p) => p.id !== existing.id))
      } else {
        const res = await setPermission({ guard_id: id, firearm_id: firearmId, is_permitted: true })
        setPermissions((prev) => [...prev, res.data])
      }
    } catch (err) {
      setPermError(err.response?.data?.detail
        ? (typeof err.response.data.detail === 'string' ? err.response.data.detail : 'Could not update permission')
        : 'Could not update permission')
    }
  }

  const hasPermission = (firearmId) => permissions.some((p) => p.firearm_id === firearmId)

  const handleAddRoute = async (e) => {
    e.preventDefault()
    if (!newRoute.route_name.trim()) return
    const res = await api.post(`/api/guards/${id}/cit-routes`, newRoute)
    setCitRoutes((prev) => [...prev, res.data])
    setNewRoute({ route_name: '', cell_phone: '' })
  }

  const handleDeleteRoute = async (routeId) => {
    await api.delete(`/api/guards/${id}/cit-routes/${routeId}`)
    setCitRoutes((prev) => prev.filter((r) => r.id !== routeId))
  }

  const handleSaveAccount = async (e) => {
    e.preventDefault()
    setAcctBusy(true); setAcctMsg(''); setTempPw('')
    try {
      const res = await setGuardAccount(id, {
        username: acct.username.trim(),
        password: acct.password || null,
      })
      setAccount({ has_account: true, username: res.data.username, must_change_password: res.data.must_change_password })
      setAcct((a) => ({ ...a, password: '' }))
      if (res.data.temp_password) setTempPw(res.data.temp_password)
      setAcctMsg('Sign-in account saved.')
    } catch (err) {
      setAcctMsg(err.response?.data?.detail || 'Could not save account')
    } finally {
      setAcctBusy(false)
    }
  }

  const handleResetAccount = async () => {
    setAcctBusy(true); setAcctMsg(''); setTempPw('')
    try {
      const res = await resetGuardPassword(id)
      setAccount((acc) => ({ ...acc, must_change_password: true }))
      setTempPw(res.data.temp_password)
      setAcctMsg('Temporary password generated — give it to the guard.')
    } catch (err) {
      setAcctMsg(err.response?.data?.detail || 'Could not reset password')
    } finally {
      setAcctBusy(false)
    }
  }

  const handleRemoveAccount = async () => {
    if (!window.confirm('Remove this guard\'s sign-in account? They will be issued unsigned until a new account is created.')) return
    setAcctBusy(true); setAcctMsg(''); setTempPw('')
    try {
      await deleteGuardAccount(id)
      setAccount({ has_account: false, username: null, must_change_password: false })
      setAcctMsg('Sign-in account removed.')
    } catch (err) {
      setAcctMsg(err.response?.data?.detail || 'Could not remove account')
    } finally {
      setAcctBusy(false)
    }
  }

  if (loading) return <div className="p-6 text-sm text-slate-500">Loading…</div>

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate('/guards')} className="text-sm text-slate-400 hover:text-slate-100">
          ← Guards
        </button>
        <h2 className="text-xl font-bold text-slate-100">
          {isNew ? 'Add Guard' : 'Edit Guard'}
        </h2>
      </div>

      <form onSubmit={handleSubmit} className="bg-slate-800/60 rounded-xl border border-slate-700 p-6 mb-6 space-y-5">

        {error && <p ref={errorRef} className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2">{error}</p>}

        {/* Name */}
        {isNew ? (
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Name</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { name: 'first_name', label: 'First Name', required: true },
                { name: 'last_name',  label: 'Last Name',  required: true },
              ].map((field) => (
                <div key={field.name}>
                  <label className="block text-xs font-medium text-slate-400 mb-1">{field.label}</label>
                  <input type="text" name={field.name} value={form[field.name]}
                    onChange={handleChange} required
                    className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-3 bg-slate-800/40 rounded-lg">
            <p className="text-xs text-slate-500 mb-0.5">Guard Name (cannot be changed)</p>
            <p className="text-sm font-medium text-slate-100">{form.first_name} {form.last_name}</p>
          </div>
        )}

        {/* Sign-in Account — required when creating a guard */}
        {isNew && (
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
            <p className="text-xs font-semibold text-blue-300 uppercase tracking-wide mb-1">Sign-in Account</p>
            <p className="text-xs text-blue-300 mb-3">
              The guard uses these to electronically sign for their firearm. They can reset a forgotten
              password themselves via a WhatsApp code.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Username</label>
                <input type="text" name="username" value={form.username} onChange={handleChange} required
                  autoComplete="off"
                  className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-800/60"
                  placeholder="e.g. jsmith" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Password</label>
                <input type="text" name="password" value={form.password} onChange={handleChange} required minLength={6}
                  autoComplete="off"
                  className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-800/60"
                  placeholder="At least 6 characters" />
              </div>
            </div>
          </div>
        )}

        {/* Profile */}
        <div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Profile</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { name: 'id_number',        label: 'ID Number' },
              { name: 'psira_number',     label: 'PSIRA Number' },
              { name: 'personnel_number', label: 'Personnel Number' },
              { name: 'cell_phone',       label: 'Contact Number' },
              { name: 'region',           label: 'Region' },
            ].map((field) => (
              <div key={field.name}>
                <label className="block text-xs font-medium text-slate-400 mb-1">{field.label}</label>
                <input type="text" name={field.name} value={form[field.name]} onChange={handleChange}
                  className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            ))}
          </div>
        </div>

        {/* SAPS Competency */}
        <div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">SAPS Competency</p>
          <div className="space-y-3">
            {WEAPON_TYPES.map((wt) => (
              <div key={wt} className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1 capitalize">{wt} — Competency #</label>
                  <input type="text" name={`saps_comp_${wt}`} value={form[`saps_comp_${wt}`]} onChange={handleChange}
                    className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Expiry Date</label>
                  <input type="date" name={`saps_expiry_${wt}`} value={form[`saps_expiry_${wt}`]} onChange={handleChange}
                    className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Weapon-type clearance */}
        <div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Weapon Type Clearance</p>
          <div className="flex gap-6">
            {WEAPON_TYPES.map((wt) => (
              <label key={wt} className="flex items-center gap-2 text-sm text-slate-200 capitalize cursor-pointer">
                <input type="checkbox" name={`permitted_${wt}`} checked={form[`permitted_${wt}`]}
                  onChange={handleChange} className="rounded" />
                {wt}
              </label>
            ))}
          </div>
        </div>

        {success && <p className="text-sm text-green-400 bg-green-500/10 border border-green-500/30 rounded-lg px-3 py-2">{success}</p>}

        <div className="flex gap-3 pt-1">
          <button type="submit" disabled={saving}
            className="bg-blue-600 text-white text-sm px-5 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors">
            {saving ? 'Saving…' : isNew ? 'Create Guard' : 'Save Changes'}
          </button>
          <button type="button" onClick={() => navigate('/guards')} className="text-sm text-slate-400 hover:text-slate-100">
            Cancel
          </button>
        </div>
      </form>

      {/* Firearm Permissions */}
      {!isNew && (
        <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-6 mb-6">
          <h3 className="font-semibold text-slate-100 mb-4">Firearm Permissions</h3>
          {permError && (
            <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2 mb-3">{permError}</p>
          )}
          {firearms.length === 0 ? (
            <p className="text-sm text-slate-500">No firearms in the system</p>
          ) : (
            <div className="space-y-2">
              {firearms.map((fa) => (
                <label key={fa.id} className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" checked={hasPermission(fa.id)}
                    onChange={() => togglePermission(fa.id)} className="rounded" />
                  <span className="text-sm text-slate-200">
                    {fa.make} {fa.model} — <span className="text-slate-400">{fa.serial_number}</span>
                  </span>
                </label>
              ))}
            </div>
          )}
        </div>
      )}

      {/* CIT Routes */}
      {!isNew && (
        <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-6">
          <h3 className="font-semibold text-slate-100 mb-4">CIT Routes</h3>
          {citRoutes.length === 0 ? (
            <p className="text-sm text-slate-500 mb-4">No CIT routes assigned</p>
          ) : (
            <div className="space-y-2 mb-4">
              {citRoutes.map((r) => (
                <div key={r.id} className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0">
                  <div>
                    <p className="text-sm font-medium text-slate-100">{r.route_name}</p>
                    {r.cell_phone && <p className="text-xs text-slate-400">{r.cell_phone}</p>}
                  </div>
                  <button
                    onClick={() => handleDeleteRoute(r.id)}
                    className="text-xs text-slate-500 hover:text-red-400 transition-colors"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
          <form onSubmit={handleAddRoute} className="flex gap-2 items-end">
            <div className="flex-1">
              <label className="block text-xs font-medium text-slate-400 mb-1">Route Name</label>
              <input type="text" value={newRoute.route_name}
                onChange={(e) => setNewRoute((r) => ({ ...r, route_name: e.target.value }))}
                className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g. CBD Route 1" />
            </div>
            <div className="flex-1">
              <label className="block text-xs font-medium text-slate-400 mb-1">Cell Phone</label>
              <input type="text" value={newRoute.cell_phone}
                onChange={(e) => setNewRoute((r) => ({ ...r, cell_phone: e.target.value }))}
                className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g. 0821234567" />
            </div>
            <button type="submit"
              className="bg-slate-700 text-white text-sm px-4 py-2 rounded-lg hover:bg-slate-600 transition-colors whitespace-nowrap">
              + Add Route
            </button>
          </form>
        </div>
      )}

      {/* Sign-in Account — lets the guard electronically sign for firearms */}
      {!isNew && account && (
        <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-6 mt-6">
          <h3 className="font-semibold text-slate-100 mb-1">Sign-in Account</h3>
          <p className="text-xs text-slate-400 mb-4">
            The guard uses these credentials to electronically sign for their firearm at issue.
            They can reset a forgotten password themselves via a WhatsApp code{form.cell_phone ? '' : ' (a contact number is required for this)'}.
          </p>

          {tempPw && (
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg px-3 py-2 mb-4">
              <p className="text-xs text-green-300">
                Temporary password (shown once): <span className="font-mono font-semibold">{tempPw}</span>
                <br />Give this to the guard — they'll be asked to change it.
              </p>
            </div>
          )}

          {account.has_account ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-slate-800/40 rounded-lg">
                <div>
                  <p className="text-xs text-slate-500 mb-0.5">Username</p>
                  <p className="text-sm font-medium text-slate-100">{account.username}</p>
                </div>
                {account.must_change_password && (
                  <span className="text-xs text-amber-300 bg-amber-500/10 border border-amber-500/30 rounded px-2 py-1">
                    Must change password
                  </span>
                )}
              </div>
              <div className="flex gap-3">
                <button type="button" onClick={handleResetAccount} disabled={acctBusy}
                  className="bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50">
                  Reset password
                </button>
                <button type="button" onClick={handleRemoveAccount} disabled={acctBusy}
                  className="text-sm text-slate-400 hover:text-red-400">
                  Remove account
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSaveAccount} className="flex gap-2 items-end flex-wrap">
              <div className="flex-1 min-w-[140px]">
                <label className="block text-xs font-medium text-slate-400 mb-1">Username</label>
                <input type="text" value={acct.username}
                  onChange={(e) => setAcct((a) => ({ ...a, username: e.target.value }))} required
                  className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. jsmith" />
              </div>
              <div className="flex-1 min-w-[140px]">
                <label className="block text-xs font-medium text-slate-400 mb-1">Password (optional)</label>
                <input type="text" value={acct.password}
                  onChange={(e) => setAcct((a) => ({ ...a, password: e.target.value }))}
                  className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Leave blank to auto-generate" />
              </div>
              <button type="submit" disabled={acctBusy || !acct.username.trim()}
                className="bg-slate-700 text-white text-sm px-4 py-2 rounded-lg hover:bg-slate-600 disabled:opacity-50 whitespace-nowrap">
                Create account
              </button>
            </form>
          )}

          {acctMsg && <p className="text-xs text-slate-400 mt-3">{acctMsg}</p>}
        </div>
      )}
    </div>
  )
}
