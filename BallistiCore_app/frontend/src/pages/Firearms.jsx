import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getFirearms, deleteFirearm } from '../api/firearms'
import {
  getAmmunitionTypes,
  createAmmunitionType,
  updateAmmunitionType,
  deleteAmmunitionType,
} from '../api/ammunitionTypes'
import { useAuth } from '../context/AuthContext'
import { useLicense } from '../context/LicenseContext'
import { isSuperAdmin } from '../utils/permissions'

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

// ── Firearms tab ──────────────────────────────────────────────────────────────
function FirearmsTab() {
  const { user } = useAuth()
  const { read_only } = useLicense()
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
    <>
      <div className="flex items-center justify-end gap-3 mb-4">
        <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
          <input
            type="checkbox"
            checked={includeInactive}
            onChange={(e) => setIncludeInactive(e.target.checked)}
            className="rounded"
          />
          Show inactive
        </label>
        {read_only ? (
          <span title="Subscription expired — read-only mode"
            className="bg-blue-600 text-white text-sm px-4 py-2 rounded-lg opacity-50 cursor-not-allowed">
            + Add Firearm
          </span>
        ) : (
          <Link
            to="/firearms/new"
            className="bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            + Add Firearm
          </Link>
        )}
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
    </>
  )
}

// ── Ammunition Types tab ──────────────────────────────────────────────────────
const BLANK_AMMO = { name: '', description: '' }

function AmmunitionTypesTab() {
  const { read_only } = useLicense()
  const [types, setTypes]             = useState([])
  const [includeInactive, setInc]     = useState(false)
  const [loading, setLoading]         = useState(true)
  const [editing, setEditing]         = useState(null)   // null = dialog closed
  const [form, setForm]               = useState(BLANK_AMMO)
  const [saving, setSaving]           = useState(false)
  const [busyId, setBusyId]           = useState(null)
  const [error, setError]             = useState('')
  const [success, setSuccess]         = useState('')

  const load = () => {
    setLoading(true)
    getAmmunitionTypes(includeInactive)
      .then((res) => setTypes(res.data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [includeInactive])

  const openNew = () => {
    setEditing({})
    setForm(BLANK_AMMO)
    setError('')
    setSuccess('')
  }

  const openEdit = (t) => {
    setEditing(t)
    setForm({ name: t.name, description: t.description || '' })
    setError('')
    setSuccess('')
  }

  const close = () => { setEditing(null); setError('') }

  const handleChange = (e) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = { name: form.name.trim(), description: form.description.trim() || null }
      if (editing?.id) {
        await updateAmmunitionType(editing.id, payload)
        setSuccess(`Ammunition type "${payload.name}" updated.`)
      } else {
        await createAmmunitionType(payload)
        setSuccess(`Ammunition type "${payload.name}" added.`)
      }
      load()
      close()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save ammunition type')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (t) => {
    if (!window.confirm(`Delete ammunition type "${t.name}"? It will no longer be available for new firearms.`)) return
    setBusyId(t.id)
    setSuccess('')
    try {
      await deleteAmmunitionType(t.id)
      load()
    } catch (err) {
      alert(err.response?.data?.detail || 'Delete failed')
    } finally {
      setBusyId(null)
    }
  }

  const handleReactivate = async (t) => {
    setBusyId(t.id)
    setSuccess('')
    try {
      await updateAmmunitionType(t.id, { is_active: true })
      load()
    } catch (err) {
      alert(err.response?.data?.detail || 'Reactivate failed')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-slate-400">
          {types.length} ammunition type{types.length !== 1 ? 's' : ''}
        </p>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setInc(e.target.checked)}
              className="rounded"
            />
            Show inactive
          </label>
          <button onClick={openNew} disabled={read_only}
            title={read_only ? 'Subscription expired — read-only mode' : undefined}
            className="bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            + Add Ammunition Type
          </button>
        </div>
      </div>

      {success && (
        <p className="mb-4 text-sm text-green-400 bg-green-500/10 border border-green-500/30 rounded-lg px-3 py-2">{success}</p>
      )}

      {loading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : types.length === 0 ? (
        <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-8 text-center">
          <p className="text-slate-500 text-sm">No ammunition types found</p>
        </div>
      ) : (
        <div className="bg-slate-800/60 rounded-xl border border-slate-700 divide-y divide-slate-700/60">
          {types.map((t) => (
            <div key={t.id} className="flex items-center justify-between px-4 py-3">
              <div>
                <p className="text-sm font-medium text-slate-100">
                  {t.name}
                  {!t.is_active && (
                    <span className="ml-2 text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">
                      Inactive
                    </span>
                  )}
                </p>
                {t.description && <p className="text-xs text-slate-400">{t.description}</p>}
              </div>
              <div className="flex items-center gap-3">
                {t.is_active ? (
                  <>
                    <button
                      onClick={() => openEdit(t)}
                      disabled={read_only}
                      className="text-sm text-blue-400 hover:underline disabled:opacity-50 disabled:no-underline"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(t)}
                      disabled={busyId === t.id || read_only}
                      className="text-xs text-slate-500 hover:text-red-400 transition-colors disabled:opacity-50"
                    >
                      Delete
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => handleReactivate(t)}
                    disabled={busyId === t.id || read_only}
                    className="text-xs px-2 py-1 rounded bg-green-500/10 text-green-400 hover:bg-green-100 transition-colors disabled:opacity-50"
                  >
                    Reactivate
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add / Edit dialog */}
      {editing !== null && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800/60 rounded-xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
              <h3 className="font-semibold text-slate-100">
                {editing?.id ? `Edit Ammunition Type — ${editing.name}` : 'Add Ammunition Type'}
              </h3>
              <button onClick={close} className="text-slate-500 hover:text-slate-200 text-lg leading-none">&times;</button>
            </div>

            <form onSubmit={handleSave} className="px-6 py-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Name *</label>
                <input type="text" name="name" value={form.name} onChange={handleChange} required autoFocus
                  className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Description</label>
                <textarea name="description" value={form.description} onChange={handleChange} rows={3}
                  className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>

              {error && <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2">{error}</p>}

              <div className="flex gap-3 pt-1">
                <button type="submit" disabled={saving}
                  className="bg-blue-600 text-white text-sm px-5 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors">
                  {saving ? 'Saving…' : editing?.id ? 'Save Changes' : 'Add Ammunition Type'}
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
export default function Firearms() {
  const { user } = useAuth()
  const [tab, setTab] = useState('firearms')

  // Managing ammunition types maps to the backend's require_admin (super admin)
  // gate on the create/update/delete endpoints — match it here so the tab is
  // only shown to operators who can actually use it.
  const superAdmin = isSuperAdmin(user)

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-xl font-bold text-slate-100 mb-4">Firearms</h2>

      {/* Tabs */}
      <div className="flex border-b border-slate-700 mb-6">
        <Tab label="Firearms"         active={tab === 'firearms'} onClick={() => setTab('firearms')} />
        {superAdmin && (
          <Tab label="Ammunition Types" active={tab === 'ammo'} onClick={() => setTab('ammo')} />
        )}
      </div>

      {tab === 'firearms'           && <FirearmsTab />}
      {tab === 'ammo' && superAdmin  && <AmmunitionTypesTab />}
    </div>
  )
}
