import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getFirearm, createFirearm, updateFirearm, deleteFirearm } from '../api/firearms'
import { getAmmunitionTypes } from '../api/ammunitionTypes'
import { useAuth } from '../context/AuthContext'

const FIREARM_TYPES = [
  { value: '',        label: 'Unspecified' },
  { value: 'carbine', label: 'Carbine' },
  { value: 'handgun', label: 'Handgun' },
  { value: 'rifle',   label: 'Rifle' },
  { value: 'shotgun', label: 'Shotgun' },
]

// Fields shown only when creating (identity fields — locked after creation)
const IDENTITY_FIELDS = [
  { name: 'make',          label: 'Make',          required: true },
  { name: 'model',         label: 'Model',         required: true },
  { name: 'serial_number', label: 'Serial Number', required: true },
]

// Fields always editable
const EDITABLE_FIELDS = [
  { name: 'calibre',        label: 'Calibre' },
  { name: 'license_number', label: 'Licence Number' },
  { name: 'description',    label: 'Description',  wide: true },
]

export default function FirearmDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const isNew = id === 'new'

  const [form, setForm] = useState({
    make: '', model: '', serial_number: '', calibre: '',
    license_number: '', description: '', type: '', ammunition_type_id: '', is_active: true,
  })
  const [ammoTypes, setAmmoTypes] = useState([])
  const [loading, setLoading] = useState(!isNew)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState('')
  const errorRef = useRef(null)
  const [success, setSuccess] = useState('')

  useEffect(() => {
    getAmmunitionTypes().then((res) => setAmmoTypes(res.data)).catch(() => {})
  }, [])

  useEffect(() => {
    if (!isNew) {
      getFirearm(id)
        .then((res) => {
          const fa = res.data
          setForm({
            make:               fa.make || '',
            model:              fa.model || '',
            serial_number:      fa.serial_number || '',
            calibre:            fa.calibre || '',
            license_number:     fa.license_number || '',
            description:        fa.description || '',
            type:               fa.type || '',
            ammunition_type_id: fa.ammunition_type_id || '',
            is_active:          fa.is_active,
          })
        })
        .catch(() => setError('Could not load this firearm. Please go back and try again.'))
        .finally(() => setLoading(false))
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

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      if (isNew) {
        await createFirearm({ ...form, type: form.type || null, ammunition_type_id: form.ammunition_type_id || null })
        navigate('/firearms')
      } else {
        const { make, model, serial_number, ...editableFields } = form
        await updateFirearm(id, {
          ...editableFields,
          type: editableFields.type || null,
          ammunition_type_id: editableFields.ammunition_type_id || null,
        })
        setSuccess('Firearm updated.')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save firearm')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!window.confirm(`Permanently delete ${form.make} ${form.model} (${form.serial_number})? This cannot be undone.`)) return
    setDeleting(true)
    try {
      await deleteFirearm(id)
      navigate('/firearms')
    } catch (err) {
      setError(err.response?.data?.detail || 'Delete failed')
      setDeleting(false)
    }
  }

  if (loading) return <div className="p-6 text-sm text-slate-500">Loading…</div>

  return (
    <div className="p-6 max-w-xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate('/firearms')} className="text-sm text-slate-400 hover:text-slate-100">
          ← Firearms
        </button>
        <h2 className="text-xl font-bold text-slate-100">
          {isNew ? 'Add Firearm' : 'Edit Firearm'}
        </h2>
      </div>

      <form onSubmit={handleSubmit} className="bg-slate-800/60 rounded-xl border border-slate-700 p-6">

        {error && <p ref={errorRef} className="mb-4 text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2">{error}</p>}

        {/* Identity fields — editable on create, read-only on edit */}
        {isNew ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {IDENTITY_FIELDS.map((field) => (
              <div key={field.name}>
                <label className="block text-xs font-medium text-slate-400 mb-1">{field.label}</label>
                <input
                  type="text"
                  name={field.name}
                  value={form[field.name]}
                  onChange={handleChange}
                  required
                  className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            ))}
          </div>
        ) : (
          <div className="mb-4 p-3 bg-slate-800/40 rounded-lg">
            <p className="text-xs text-slate-500 mb-0.5">Firearm (cannot be changed)</p>
            <p className="text-sm font-medium text-slate-100">{form.make} {form.model}</p>
            <p className="text-xs text-slate-400">S/N: {form.serial_number}</p>
          </div>
        )}

        {/* Type dropdown — always editable */}
        <div className="mb-4">
          <label className="block text-xs font-medium text-slate-400 mb-1">Firearm Type</label>
          <select
            name="type"
            value={form.type}
            onChange={handleChange}
            className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-800/60"
          >
            {FIREARM_TYPES.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        {/* Ammunition type — links the firearm to a managed ammunition type */}
        <div className="mb-4">
          <label className="block text-xs font-medium text-slate-400 mb-1">Ammunition Type</label>
          <select
            name="ammunition_type_id"
            value={form.ammunition_type_id}
            onChange={handleChange}
            className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-800/60"
          >
            <option value="">None</option>
            {ammoTypes.map((t) => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
          <p className="mt-1 text-xs text-slate-500">This ammunition type is linked to the firearm record.</p>
        </div>

        {/* Editable fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {EDITABLE_FIELDS.map((field) => (
            <div key={field.name} className={field.wide ? 'md:col-span-2' : ''}>
              <label className="block text-xs font-medium text-slate-400 mb-1">{field.label}</label>
              <input
                type="text"
                name={field.name}
                value={form[field.name]}
                onChange={handleChange}
                className="w-full border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          ))}
        </div>

        {!isNew && (
          <label className="flex items-center gap-2 mt-4 cursor-pointer text-sm text-slate-200">
            <input
              type="checkbox"
              name="is_active"
              checked={form.is_active}
              onChange={handleChange}
              className="rounded"
            />
            Active
          </label>
        )}

        {success && <p className="mt-4 text-sm text-green-400 bg-green-500/10 border border-green-500/30 rounded-lg px-3 py-2">{success}</p>}

        <div className="mt-5 flex items-center justify-between">
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={saving}
              className="bg-blue-600 text-white text-sm px-5 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {saving ? 'Saving…' : isNew ? 'Add Firearm' : 'Save Changes'}
            </button>
            <button type="button" onClick={() => navigate('/firearms')} className="text-sm text-slate-400 hover:text-slate-100">
              Cancel
            </button>
          </div>
          {!isNew && user?.is_admin && (
            <button
              type="button"
              onClick={handleDelete}
              disabled={deleting}
              className="text-xs text-red-400 hover:text-red-700 disabled:opacity-50 transition-colors"
            >
              {deleting ? 'Deleting…' : 'Delete Firearm'}
            </button>
          )}
        </div>
      </form>
    </div>
  )
}
