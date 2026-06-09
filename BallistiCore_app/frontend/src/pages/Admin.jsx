import { useEffect, useState } from 'react'
import { getUsers, createUser, updateUser, deactivateUser, reactivateUser } from '../api/auth'
import { getBrandingFull, updateBranding } from '../api/branding'
import {
  getAmmunitionTypes, createAmmunitionType, updateAmmunitionType, deleteAmmunitionType,
} from '../api/ammunitionTypes'
import { useAuth } from '../context/AuthContext'
import { useBranding } from '../context/BrandingContext'

// ── User form defaults ────────────────────────────────────────────────────────
const BLANK_USER = {
  username: '', password: '', email: '', is_admin: false,
  personnel_number: '', psira_number: '', competency: '', phone_number: '', id_number: '',
  perm_new_permits: false, perm_return_permits: false, perm_manage_weapons: false,
  perm_manage_staff: false, perm_access_database: false, perm_send_whatsapp: false,
  perm_view_register_history: false, perm_system_admin: false, perm_add_user: false,
  perm_modify_user: false, perm_change_passwords: false, perm_clear_logs: false,
  perm_carbine: false, perm_handgun: false, perm_rifle: false, perm_shotgun: false,
}

const PERMISSION_LABELS = [
  { key: 'perm_new_permits',           label: 'Issue Permits' },
  { key: 'perm_return_permits',        label: 'Return Permits' },
  { key: 'perm_manage_weapons',        label: 'Manage Firearms' },
  { key: 'perm_manage_staff',          label: 'Manage Guards' },
  { key: 'perm_access_database',       label: 'Access Register' },
  { key: 'perm_send_whatsapp',         label: 'Send WhatsApp' },
  { key: 'perm_view_register_history', label: 'View History' },
  { key: 'perm_system_admin',          label: 'System Admin' },
  { key: 'perm_add_user',              label: 'Add Users' },
  { key: 'perm_modify_user',           label: 'Modify Users' },
  { key: 'perm_change_passwords',      label: 'Change Passwords' },
  { key: 'perm_clear_logs',            label: 'Clear Logs' },
]

const WEAPON_PERMS = [
  { key: 'perm_carbine', label: 'Carbine' },
  { key: 'perm_handgun', label: 'Handgun' },
  { key: 'perm_rifle',   label: 'Rifle' },
  { key: 'perm_shotgun', label: 'Shotgun' },
]

// ── Company details form defaults ─────────────────────────────────────────────
const BLANK_COMPANY = {
  company_name: '', company_reg: '',
  psira_number: '', company_address: '', permit_prefix: '',
  support_email: '', primary_color: '#1d4ed8',
}

// ── Tab button ────────────────────────────────────────────────────────────────
function Tab({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${
        active
          ? 'border-blue-600 text-blue-400'
          : 'border-transparent text-slate-400 hover:text-slate-100'
      }`}
    >
      {label}
    </button>
  )
}

// ── Users tab ─────────────────────────────────────────────────────────────────
function UsersTab({ currentUser }) {
  const [users, setUsers]         = useState([])
  const [loading, setLoading]     = useState(true)
  const [editingUser, setEditing] = useState(null)
  const [form, setForm]           = useState(BLANK_USER)
  const [saving, setSaving]       = useState(false)
  const [error, setError]         = useState('')
  const [success, setSuccess]     = useState('')

  const load = () => {
    setLoading(true)
    getUsers().then((res) => setUsers(res.data)).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const openNew = () => {
    setEditing({})
    setForm(BLANK_USER)
    setError('')
    setSuccess('')
  }

  const openEdit = (u) => {
    setEditing(u)
    setForm({
      username: u.username, password: '', email: u.email || '',
      is_admin: u.is_admin,
      personnel_number: u.personnel_number || '',
      psira_number: u.psira_number || '',
      competency: u.competency || '',
      phone_number: u.phone_number || '',
      id_number: u.id_number || '',
      perm_new_permits: u.perm_new_permits,
      perm_return_permits: u.perm_return_permits,
      perm_manage_weapons: u.perm_manage_weapons,
      perm_manage_staff: u.perm_manage_staff,
      perm_access_database: u.perm_access_database,
      perm_send_whatsapp: u.perm_send_whatsapp,
      perm_view_register_history: u.perm_view_register_history,
      perm_system_admin: u.perm_system_admin,
      perm_add_user: u.perm_add_user,
      perm_modify_user: u.perm_modify_user,
      perm_change_passwords: u.perm_change_passwords,
      perm_clear_logs: u.perm_clear_logs,
      perm_carbine: u.perm_carbine,
      perm_handgun: u.perm_handgun,
      perm_rifle: u.perm_rifle,
      perm_shotgun: u.perm_shotgun,
    })
    setError('')
    setSuccess('')
  }

  const close = () => { setEditing(null); setError(''); setSuccess('') }

  const handleChange = (e) => {
    const val = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [e.target.name]: val }))
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const isNew = !editingUser?.id
      if (isNew) {
        await createUser(form)
        setSuccess(`User "${form.username}" created.`)
      } else {
        const payload = { ...form }
        if (!payload.password) delete payload.password
        delete payload.username
        await updateUser(editingUser.id, payload)
        setSuccess(`User "${editingUser.username}" updated.`)
      }
      load()
      close()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save user')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleActive = async (u) => {
    if (!window.confirm(`${u.is_active ? 'Deactivate' : 'Reactivate'} ${u.username}?`)) return
    if (u.is_active) await deactivateUser(u.id)
    else await reactivateUser(u.id)
    load()
  }

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-slate-400">{users.length} user{users.length !== 1 ? 's' : ''}</p>
        <button onClick={openNew}
          className="bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
          + Add User
        </button>
      </div>

      {success && !editingUser && (
        <p className="mb-4 text-sm text-green-400 bg-green-500/10 border border-green-500/30 rounded-lg px-3 py-2">{success}</p>
      )}

      <div className="bg-slate-800/60 rounded-xl border border-slate-700 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-800/40 border-b border-slate-700">
            <tr>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Username</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Personnel #</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Role</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Status</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/60">
            {loading ? (
              <tr><td colSpan={5} className="px-4 py-6 text-center text-sm text-slate-500">Loading…</td></tr>
            ) : users.map((u) => (
              <tr key={u.id} className="hover:bg-slate-800/50">
                <td className="px-4 py-3 font-medium text-slate-100">{u.username}</td>
                <td className="px-4 py-3 text-slate-400 text-xs">{u.personnel_number || '—'}</td>
                <td className="px-4 py-3">
                  {u.is_admin
                    ? <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">Admin</span>
                    : <span className="text-xs text-slate-400">Operator</span>}
                </td>
                <td className="px-4 py-3">
                  {u.is_active
                    ? <span className="text-xs text-green-400">Active</span>
                    : <span className="text-xs text-slate-500">Inactive</span>}
                </td>
                <td className="px-4 py-3 text-right flex items-center justify-end gap-3">
                  <button onClick={() => openEdit(u)} className="text-sm text-blue-400 hover:underline">Edit</button>
                  {u.id !== currentUser?.id && (
                    <button onClick={() => handleToggleActive(u)}
                      className={`text-xs px-2 py-1 rounded transition-colors ${
                        u.is_active
                          ? 'bg-red-500/10 text-red-400 hover:bg-red-100'
                          : 'bg-green-500/10 text-green-400 hover:bg-green-100'
                      }`}>
                      {u.is_active ? 'Deactivate' : 'Reactivate'}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add / Edit dialog */}
      {editingUser !== null && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800/60 rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
              <h3 className="font-semibold text-slate-100">
                {editingUser?.id ? `Edit User — ${editingUser.username}` : 'Add User'}
              </h3>
              <button onClick={close} className="text-slate-500 hover:text-slate-200 text-lg leading-none">&times;</button>
            </div>

            <form onSubmit={handleSave} className="px-6 py-5 space-y-5">
              {/* Account */}
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Account</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Username{!editingUser?.id && ' *'}</label>
                    {editingUser?.id ? (
                      <p className="text-sm text-slate-200 py-2">{editingUser.username}</p>
                    ) : (
                      <input type="text" name="username" value={form.username} onChange={handleChange} required
                        className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    )}
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">
                      Password{editingUser?.id ? ' (leave blank to keep)' : ' *'}
                    </label>
                    <input type="password" name="password" value={form.password} onChange={handleChange}
                      required={!editingUser?.id} minLength={editingUser?.id ? 0 : 6}
                      className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Email</label>
                    <input type="email" name="email" value={form.email} onChange={handleChange}
                      className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div className="flex items-center pt-5">
                    <label className="flex items-center gap-2 text-sm text-slate-200 cursor-pointer">
                      <input type="checkbox" name="is_admin" checked={form.is_admin} onChange={handleChange} className="rounded" />
                      System Administrator
                    </label>
                  </div>
                </div>
              </div>

              {/* Profile */}
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Profile</p>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { name: 'personnel_number', label: 'Personnel Number' },
                    { name: 'psira_number',      label: 'PSIRA Number' },
                    { name: 'competency',        label: 'Competency' },
                    { name: 'phone_number',      label: 'Phone Number' },
                    { name: 'id_number',         label: 'ID Number' },
                  ].map((f) => (
                    <div key={f.name}>
                      <label className="block text-xs font-medium text-slate-400 mb-1">{f.label}</label>
                      <input type="text" name={f.name} value={form[f.name]} onChange={handleChange}
                        className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    </div>
                  ))}
                </div>
              </div>

              {/* Permissions */}
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Permissions</p>
                <div className="grid grid-cols-2 gap-y-2 gap-x-6">
                  {PERMISSION_LABELS.map(({ key, label }) => (
                    <label key={key} className="flex items-center gap-2 text-sm text-slate-200 cursor-pointer">
                      <input type="checkbox" name={key} checked={form[key]} onChange={handleChange} className="rounded" />
                      {label}
                    </label>
                  ))}
                </div>
              </div>

              {/* Weapon categories */}
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Weapon Categories</p>
                <div className="flex gap-6">
                  {WEAPON_PERMS.map(({ key, label }) => (
                    <label key={key} className="flex items-center gap-2 text-sm text-slate-200 cursor-pointer">
                      <input type="checkbox" name={key} checked={form[key]} onChange={handleChange} className="rounded" />
                      {label}
                    </label>
                  ))}
                </div>
              </div>

              {error && <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2">{error}</p>}

              <div className="flex gap-3 pt-1">
                <button type="submit" disabled={saving}
                  className="bg-blue-600 text-white text-sm px-5 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors">
                  {saving ? 'Saving…' : editingUser?.id ? 'Save Changes' : 'Create User'}
                </button>
                <button type="button" onClick={close} className="text-sm text-slate-400 hover:text-slate-100">Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}

// ── Company Details tab ───────────────────────────────────────────────────────
function CompanyTab() {
  const { refresh: refreshBranding } = useBranding()
  const [form, setForm]   = useState(BLANK_COMPANY)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving]   = useState(false)
  const [success, setSuccess] = useState('')
  const [error, setError]     = useState('')

  useEffect(() => {
    getBrandingFull()
      .then((res) => setForm({ ...BLANK_COMPANY, ...res.data }))
      .finally(() => setLoading(false))
  }, [])

  const handleChange = (e) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
    setSuccess('')
    setError('')
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      await updateBranding(form)
      await refreshBranding()   // update sidebar/login/title immediately
      setSuccess('Company details saved.')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p className="text-sm text-slate-500 py-6">Loading…</p>

  return (
    <form onSubmit={handleSave} className="max-w-2xl space-y-6">
      <p className="text-sm text-slate-400">
        These details appear on the login screen, sidebar, and all printed permits.
      </p>

      {/* Identity */}
      <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-5 space-y-4">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Identity</p>
        <div className="grid grid-cols-2 gap-4">
          {[
            { name: 'company_name',  label: 'Company Name',            required: true },
            { name: 'company_reg',   label: 'Company Registration No.' },
            { name: 'psira_number',  label: 'PSIRA Number' },
          ].map((f) => (
            <div key={f.name}>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                {f.label}{f.required ? ' *' : ''}
              </label>
              <input
                type="text"
                name={f.name}
                value={form[f.name]}
                onChange={handleChange}
                required={f.required}
                className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          ))}
          <div className="col-span-2">
            <label className="block text-xs font-medium text-slate-400 mb-1">Company Address</label>
            <input
              type="text"
              name="company_address"
              value={form.company_address}
              onChange={handleChange}
              className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* System settings */}
      <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-5 space-y-4">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">System Settings</p>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              Permit Number Prefix *
              <span className="ml-1 text-slate-500 font-normal">(e.g. BC → BC-00001)</span>
            </label>
            <input
              type="text"
              name="permit_prefix"
              value={form.permit_prefix}
              onChange={(e) => setForm((f) => ({ ...f, permit_prefix: e.target.value.toUpperCase().slice(0, 4) }))}
              required
              maxLength={4}
              className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              Contact Email
              <span className="ml-1 text-slate-500 font-normal">(printed on permits)</span>
            </label>
            <input
              type="email"
              name="support_email"
              value={form.support_email}
              onChange={handleChange}
              className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              Primary Colour
              <span className="ml-1 text-slate-500 font-normal">(sidebar & buttons)</span>
            </label>
            <div className="flex items-center gap-2">
              <input
                type="color"
                name="primary_color"
                value={form.primary_color}
                onChange={handleChange}
                className="h-9 w-14 rounded border border-slate-700 cursor-pointer p-0.5"
              />
              <input
                type="text"
                name="primary_color"
                value={form.primary_color}
                onChange={handleChange}
                maxLength={7}
                className="flex-1 border border-slate-700 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      </div>

      {error   && <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2">{error}</p>}
      {success && <p className="text-sm text-green-400 bg-green-500/10 border border-green-500/30 rounded-lg px-3 py-2">{success}</p>}

      <button type="submit" disabled={saving}
        className="bg-blue-600 text-white text-sm px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors">
        {saving ? 'Saving…' : 'Save Company Details'}
      </button>
    </form>
  )
}

// ── Ammunition Types tab ──────────────────────────────────────────────────────
const BLANK_AMMO = { name: '', description: '' }

function AmmunitionTypesTab() {
  const [types, setTypes]         = useState([])
  const [loading, setLoading]     = useState(true)
  const [editing, setEditing]     = useState(null)   // null = closed, {} = new, {…} = edit
  const [form, setForm]           = useState(BLANK_AMMO)
  const [saving, setSaving]       = useState(false)
  const [error, setError]         = useState('')
  const [success, setSuccess]     = useState('')

  const load = () => {
    setLoading(true)
    getAmmunitionTypes(true)
      .then((res) => setTypes(res.data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const openNew  = () => { setEditing({}); setForm(BLANK_AMMO); setError('') }
  const openEdit = (t) => { setEditing(t); setForm({ name: t.name, description: t.description || '' }); setError('') }
  const close    = () => { setEditing(null); setError('') }

  const handleChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = { name: form.name, description: form.description || null }
      if (editing?.id) {
        await updateAmmunitionType(editing.id, payload)
        setSuccess(`Ammunition type "${form.name}" updated.`)
      } else {
        await createAmmunitionType(payload)
        setSuccess(`Ammunition type "${form.name}" created.`)
      }
      load()
      close()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save ammunition type')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleActive = async (t) => {
    if (t.is_active) {
      if (!window.confirm(`Deactivate "${t.name}"? It will no longer be selectable on firearms.`)) return
      await deleteAmmunitionType(t.id)
    } else {
      await updateAmmunitionType(t.id, { is_active: true })
    }
    load()
  }

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-slate-400">{types.length} ammunition type{types.length !== 1 ? 's' : ''}</p>
        <button onClick={openNew}
          className="bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
          + Add Ammunition Type
        </button>
      </div>

      {success && editing === null && (
        <p className="mb-4 text-sm text-green-400 bg-green-500/10 border border-green-500/30 rounded-lg px-3 py-2">{success}</p>
      )}

      <div className="bg-slate-800/60 rounded-xl border border-slate-700 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-800/40 border-b border-slate-700">
            <tr>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Name</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Description</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">Status</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/60">
            {loading ? (
              <tr><td colSpan={4} className="px-4 py-6 text-center text-sm text-slate-500">Loading…</td></tr>
            ) : types.length === 0 ? (
              <tr><td colSpan={4} className="px-4 py-6 text-center text-sm text-slate-500">No ammunition types yet</td></tr>
            ) : types.map((t) => (
              <tr key={t.id} className="hover:bg-slate-800/50">
                <td className="px-4 py-3 font-medium text-slate-100">{t.name}</td>
                <td className="px-4 py-3 text-slate-400 text-xs">{t.description || '—'}</td>
                <td className="px-4 py-3">
                  {t.is_active
                    ? <span className="text-xs text-green-400">Active</span>
                    : <span className="text-xs text-slate-500">Inactive</span>}
                </td>
                <td className="px-4 py-3 text-right flex items-center justify-end gap-3">
                  <button onClick={() => openEdit(t)} className="text-sm text-blue-400 hover:underline">Edit</button>
                  <button onClick={() => handleToggleActive(t)}
                    className={`text-xs px-2 py-1 rounded transition-colors ${
                      t.is_active
                        ? 'bg-red-500/10 text-red-400 hover:bg-red-100'
                        : 'bg-green-500/10 text-green-400 hover:bg-green-100'
                    }`}>
                    {t.is_active ? 'Deactivate' : 'Reactivate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add / Edit dialog */}
      {editing !== null && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800/60 rounded-xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
              <h3 className="font-semibold text-slate-100">
                {editing?.id ? `Edit Ammunition Type` : 'Add Ammunition Type'}
              </h3>
              <button onClick={close} className="text-slate-500 hover:text-slate-200 text-lg leading-none">&times;</button>
            </div>

            <form onSubmit={handleSave} className="px-6 py-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Name *</label>
                <input type="text" name="name" value={form.name} onChange={handleChange} required autoFocus
                  placeholder="e.g. 9mm Parabellum"
                  className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Description</label>
                <textarea name="description" value={form.description} onChange={handleChange} rows={2}
                  className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none" />
              </div>

              {error && <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2">{error}</p>}

              <div className="flex gap-3 pt-1">
                <button type="submit" disabled={saving}
                  className="bg-blue-600 text-white text-sm px-5 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors">
                  {saving ? 'Saving…' : editing?.id ? 'Save Changes' : 'Create'}
                </button>
                <button type="button" onClick={close} className="text-sm text-slate-400 hover:text-slate-100">Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function Admin() {
  const { user: currentUser } = useAuth()
  const [tab, setTab] = useState('users')

  if (!currentUser?.is_admin) {
    return (
      <div className="p-6">
        <p className="text-sm text-red-400">Access denied — admin only.</p>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h2 className="text-xl font-bold text-slate-100 mb-4">Administration</h2>

      {/* Tabs */}
      <div className="flex border-b border-slate-700 mb-6">
        <Tab label="Users"            active={tab === 'users'}   onClick={() => setTab('users')} />
        <Tab label="Ammunition Types" active={tab === 'ammo'}    onClick={() => setTab('ammo')} />
        <Tab label="Company Details"  active={tab === 'company'} onClick={() => setTab('company')} />
      </div>

      {tab === 'users'   && <UsersTab currentUser={currentUser} />}
      {tab === 'ammo'    && <AmmunitionTypesTab />}
      {tab === 'company' && <CompanyTab />}
    </div>
  )
}
