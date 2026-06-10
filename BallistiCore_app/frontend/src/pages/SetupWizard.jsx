import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Building2, Crosshair, Shield, UserCog, CheckCircle2,
  Check, Plus, Trash2, ArrowLeft, ArrowRight, Loader2, Rocket, Wifi, Copy,
} from 'lucide-react'
import { useBranding } from '../context/BrandingContext'
import { getBrandingFull, updateBranding, completeSetup } from '../api/branding'
import { createFirearm } from '../api/firearms'
import { createGuard } from '../api/guards'
import { createUser } from '../api/auth'
import { getNetworkInfo } from '../api/network'

const STEPS = [
  { n: 1, label: 'Company',  icon: Building2 },
  { n: 2, label: 'Firearms', icon: Crosshair },
  { n: 3, label: 'Guards',   icon: Shield },
  { n: 4, label: 'Admins',   icon: UserCog },
  { n: 5, label: 'Finish',   icon: CheckCircle2 },
]

const FIREARM_TYPES = ['', 'carbine', 'handgun', 'rifle', 'shotgun']

const inputCls =
  'w-full border border-slate-700 rounded-lg px-3 py-2 text-sm bg-slate-800/60 ' +
  'focus:outline-none focus:ring-2 focus:ring-blue-500'
const labelCls = 'block text-xs font-medium text-slate-400 mb-1'

function Field({ label, required, children }) {
  return (
    <div>
      <label className={labelCls}>{label}{required && ' *'}</label>
      {children}
    </div>
  )
}

// ── Progress stepper ──────────────────────────────────────────────────────────
function Stepper({ step }) {
  return (
    <div className="flex items-center justify-between mb-8">
      {STEPS.map((s, i) => {
        const done = step > s.n
        const active = step === s.n
        const Icon = done ? Check : s.icon
        return (
          <div key={s.n} className="flex items-center flex-1 last:flex-none">
            <div className="flex flex-col items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors ${
                  active
                    ? 'border-blue-500 bg-blue-600 text-white'
                    : done
                    ? 'border-blue-500 bg-blue-500/20 text-blue-300'
                    : 'border-slate-700 bg-slate-800 text-slate-500'
                }`}
              >
                <Icon size={18} />
              </div>
              <span className={`mt-2 text-xs ${active ? 'text-blue-300 font-medium' : done ? 'text-slate-300' : 'text-slate-500'}`}>
                {s.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`h-0.5 flex-1 mx-2 -mt-6 ${step > s.n ? 'bg-blue-500' : 'bg-slate-700'}`} />
            )}
          </div>
        )
      })}
    </div>
  )
}

// ── Reusable "add several rows" list used by the Firearms/Guards/Admins steps ─
function AddedList({ items, render, onRemove, empty }) {
  if (items.length === 0) {
    return <p className="text-xs text-slate-500 italic py-2">{empty}</p>
  }
  return (
    <ul className="divide-y divide-slate-700/60 border border-slate-700 rounded-lg overflow-hidden">
      {items.map((it, i) => (
        <li key={it.id || i} className="flex items-center justify-between px-3 py-2 bg-slate-800/40">
          <span className="text-sm text-slate-200">{render(it)}</span>
          <button type="button" onClick={() => onRemove(i)} className="text-slate-500 hover:text-red-400">
            <Trash2 size={15} />
          </button>
        </li>
      ))}
    </ul>
  )
}

// ── Step 1: Company Details (+ CIT toggle) ───────────────────────────────────
function CompanyStep({ onNext }) {
  const { refresh } = useBranding()
  const [form, setForm] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getBrandingFull()
      .then((res) => setForm({
        company_name: res.data.company_name === 'Your Company Name' ? '' : (res.data.company_name || ''),
        company_reg: res.data.company_reg || '',
        psira_number: res.data.psira_number || '',
        company_address: res.data.company_address || '',
        permit_prefix: res.data.permit_prefix || 'BC',
        support_email: res.data.support_email || '',
        primary_color: res.data.primary_color || '#1d4ed8',
        cit_enabled: !!res.data.cit_enabled,
      }))
      .catch(() => setForm({
        company_name: '', company_reg: '', psira_number: '', company_address: '',
        permit_prefix: 'BC', support_email: '', primary_color: '#1d4ed8', cit_enabled: false,
      }))
  }, [])

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const handleNext = async () => {
    if (!form.company_name.trim()) { setError('Company name is required.'); return }
    if (form.permit_prefix.trim().length < 1) { setError('Permit prefix is required.'); return }
    setSaving(true); setError('')
    try {
      await updateBranding({ ...form, permit_prefix: form.permit_prefix.toUpperCase() })
      await refresh()
      onNext()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save company details.')
    } finally { setSaving(false) }
  }

  if (!form) return <p className="text-sm text-slate-500 py-8">Loading…</p>

  return (
    <div className="space-y-5">
      <p className="text-sm text-slate-400">
        These details appear on the login screen, the sidebar, and every printed permit.
      </p>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Company Name" required>
          <input className={inputCls} value={form.company_name} onChange={(e) => set('company_name', e.target.value)} />
        </Field>
        <Field label="Company Registration No.">
          <input className={inputCls} value={form.company_reg} onChange={(e) => set('company_reg', e.target.value)} />
        </Field>
        <Field label="PSIRA Number">
          <input className={inputCls} value={form.psira_number} onChange={(e) => set('psira_number', e.target.value)} />
        </Field>
        <Field label="Contact Email">
          <input type="email" className={inputCls} value={form.support_email} onChange={(e) => set('support_email', e.target.value)} />
        </Field>
        <div className="col-span-2">
          <Field label="Company Address">
            <input className={inputCls} value={form.company_address} onChange={(e) => set('company_address', e.target.value)} />
          </Field>
        </div>
        <Field label="Permit Number Prefix (e.g. BC → BC-00001)" required>
          <input className={`${inputCls} font-mono`} maxLength={4} value={form.permit_prefix}
            onChange={(e) => set('permit_prefix', e.target.value.toUpperCase().slice(0, 4))} />
        </Field>
        <Field label="Primary Colour">
          <div className="flex items-center gap-2">
            <input type="color" value={form.primary_color} onChange={(e) => set('primary_color', e.target.value)}
              className="h-9 w-14 rounded border border-slate-700 cursor-pointer p-0.5" />
            <input className={`${inputCls} font-mono`} maxLength={7} value={form.primary_color}
              onChange={(e) => set('primary_color', e.target.value)} />
          </div>
        </Field>
      </div>

      {/* CIT toggle */}
      <label className="flex items-start gap-3 p-4 rounded-lg border border-slate-700 bg-slate-800/40 cursor-pointer">
        <input type="checkbox" checked={form.cit_enabled} onChange={(e) => set('cit_enabled', e.target.checked)}
          className="mt-0.5 rounded" />
        <span>
          <span className="block text-sm font-medium text-slate-100">Enable Cash-in-Transit (CIT)</span>
          <span className="block text-xs text-slate-400">
            Adds CIT route &amp; vehicle fields when issuing firearms. Turn this on if your operation does CIT work.
          </span>
        </span>
      </label>

      {error && <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2">{error}</p>}

      <WizardNav onNext={handleNext} nextLabel="Save & Continue" saving={saving} />
    </div>
  )
}

// ── Step 2: Firearms ─────────────────────────────────────────────────────────
function FirearmsStep({ onNext, onBack }) {
  const blank = { serial_number: '', make: '', model: '', type: '', calibre: '' }
  const [form, setForm] = useState(blank)
  const [items, setItems] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const add = async () => {
    if (!form.serial_number.trim() || !form.make.trim()) { setError('Serial number and make are required.'); return }
    setBusy(true); setError('')
    try {
      const res = await createFirearm({ ...form, type: form.type || null })
      setItems((x) => [...x, res.data]); setForm(blank)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not add firearm.')
    } finally { setBusy(false) }
  }

  return (
    <div className="space-y-5">
      <p className="text-sm text-slate-400">Add the firearms in your inventory. You can add more later — this step is optional.</p>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Serial Number" required>
          <input className={inputCls} value={form.serial_number} onChange={(e) => set('serial_number', e.target.value)} />
        </Field>
        <Field label="Make" required>
          <input className={inputCls} value={form.make} onChange={(e) => set('make', e.target.value)} />
        </Field>
        <Field label="Model">
          <input className={inputCls} value={form.model} onChange={(e) => set('model', e.target.value)} />
        </Field>
        <Field label="Type">
          <select className={inputCls} value={form.type} onChange={(e) => set('type', e.target.value)}>
            {FIREARM_TYPES.map((t) => <option key={t} value={t}>{t ? t[0].toUpperCase() + t.slice(1) : 'Unspecified'}</option>)}
          </select>
        </Field>
        <Field label="Calibre">
          <input className={inputCls} value={form.calibre} onChange={(e) => set('calibre', e.target.value)} />
        </Field>
      </div>
      {error && <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2">{error}</p>}
      <button type="button" onClick={add} disabled={busy}
        className="inline-flex items-center gap-2 text-sm bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg disabled:opacity-50">
        <Plus size={15} /> {busy ? 'Adding…' : 'Add firearm'}
      </button>

      <div>
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Added ({items.length})</p>
        <AddedList items={items} empty="No firearms added yet."
          render={(f) => `${f.make} ${f.model || ''} — ${f.serial_number}${f.type ? ` (${f.type})` : ''}`}
          onRemove={(i) => setItems((x) => x.filter((_, j) => j !== i))} />
      </div>

      <WizardNav onBack={onBack} onNext={onNext} nextLabel={items.length ? 'Continue' : 'Skip for now'} />
    </div>
  )
}

// ── Step 3: Guards ───────────────────────────────────────────────────────────
function GuardsStep({ onNext, onBack }) {
  const blank = { first_name: '', last_name: '', id_number: '', psira_number: '', cell_phone: '' }
  const [form, setForm] = useState(blank)
  const [items, setItems] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const add = async () => {
    if (!form.first_name.trim() || !form.last_name.trim()) { setError('First and last name are required.'); return }
    setBusy(true); setError('')
    try {
      const res = await createGuard({ ...form })
      setItems((x) => [...x, res.data]); setForm(blank)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not add guard.')
    } finally { setBusy(false) }
  }

  return (
    <div className="space-y-5">
      <p className="text-sm text-slate-400">Add your security officers. You can add more later — this step is optional.</p>
      <div className="grid grid-cols-2 gap-4">
        <Field label="First Name" required>
          <input className={inputCls} value={form.first_name} onChange={(e) => set('first_name', e.target.value)} />
        </Field>
        <Field label="Last Name" required>
          <input className={inputCls} value={form.last_name} onChange={(e) => set('last_name', e.target.value)} />
        </Field>
        <Field label="ID Number">
          <input className={inputCls} value={form.id_number} onChange={(e) => set('id_number', e.target.value)} />
        </Field>
        <Field label="PSIRA Number">
          <input className={inputCls} value={form.psira_number} onChange={(e) => set('psira_number', e.target.value)} />
        </Field>
        <Field label="Cell Phone">
          <input className={inputCls} value={form.cell_phone} onChange={(e) => set('cell_phone', e.target.value)} />
        </Field>
      </div>
      {error && <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2">{error}</p>}
      <button type="button" onClick={add} disabled={busy}
        className="inline-flex items-center gap-2 text-sm bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg disabled:opacity-50">
        <Plus size={15} /> {busy ? 'Adding…' : 'Add guard'}
      </button>

      <div>
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Added ({items.length})</p>
        <AddedList items={items} empty="No guards added yet."
          render={(g) => `${g.first_name} ${g.last_name}${g.psira_number ? ` (${g.psira_number})` : ''}`}
          onRemove={(i) => setItems((x) => x.filter((_, j) => j !== i))} />
      </div>

      <WizardNav onBack={onBack} onNext={onNext} nextLabel={items.length ? 'Continue' : 'Skip for now'} />
    </div>
  )
}

// ── Step 4: Admin Users ──────────────────────────────────────────────────────
function AdminsStep({ onNext, onBack }) {
  const blank = { username: '', password: '', email: '', is_admin: true }
  const [form, setForm] = useState(blank)
  const [items, setItems] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const add = async () => {
    if (!form.username.trim()) { setError('Username is required.'); return }
    if (form.password.length < 6) { setError('Password must be at least 6 characters.'); return }
    setBusy(true); setError('')
    try {
      const res = await createUser({ ...form })
      setItems((x) => [...x, res.data]); setForm(blank)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not add user.')
    } finally { setBusy(false) }
  }

  return (
    <div className="space-y-5">
      <p className="text-sm text-slate-400">
        Add the people who will operate BallistiCore. You're already signed in as <span className="text-slate-200 font-medium">admin</span> — add any colleagues here. Optional.
      </p>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Username" required>
          <input className={inputCls} value={form.username} onChange={(e) => set('username', e.target.value)} />
        </Field>
        <Field label="Password (min 6 chars)" required>
          <input type="password" className={inputCls} value={form.password} onChange={(e) => set('password', e.target.value)} />
        </Field>
        <Field label="Email">
          <input type="email" className={inputCls} value={form.email} onChange={(e) => set('email', e.target.value)} />
        </Field>
        <div className="flex items-center pt-6">
          <label className="flex items-center gap-2 text-sm text-slate-200 cursor-pointer">
            <input type="checkbox" checked={form.is_admin} onChange={(e) => set('is_admin', e.target.checked)} className="rounded" />
            System Administrator
          </label>
        </div>
      </div>
      {error && <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2">{error}</p>}
      <button type="button" onClick={add} disabled={busy}
        className="inline-flex items-center gap-2 text-sm bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg disabled:opacity-50">
        <Plus size={15} /> {busy ? 'Adding…' : 'Add user'}
      </button>

      <div>
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Added ({items.length})</p>
        <AddedList items={items} empty="No additional users added yet."
          render={(u) => `${u.username}${u.is_admin ? ' — Admin' : ' — Operator'}`}
          onRemove={(i) => setItems((x) => x.filter((_, j) => j !== i))} />
      </div>

      <WizardNav onBack={onBack} onNext={onNext} nextLabel="Continue" />
    </div>
  )
}

// ── Step 5: Completion ───────────────────────────────────────────────────────
function FinishStep({ onBack }) {
  const navigate = useNavigate()
  const { refresh } = useBranding()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [net, setNet] = useState(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    getNetworkInfo().then((r) => setNet(r.data)).catch(() => {})
  }, [])

  // The address other devices use = this server's LAN IP + the port the app is
  // served on (8000 for the installed app).
  const port = window.location.port || '8000'
  const lanIp = net?.lan_ip || ''
  const netUrl = lanIp ? `http://${lanIp}:${port}` : ''

  const copyUrl = () => {
    if (!netUrl) return
    navigator.clipboard?.writeText(netUrl)
      .then(() => { setCopied(true); setTimeout(() => setCopied(false), 1500) })
      .catch(() => {})
  }

  const finish = async () => {
    setBusy(true); setError('')
    try {
      await completeSetup()
      await refresh()
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not finish setup.')
      setBusy(false)
    }
  }

  return (
    <div className="text-center py-6 space-y-5">
      <div className="mx-auto w-16 h-16 rounded-full bg-green-500/15 border border-green-500/40 flex items-center justify-center">
        <CheckCircle2 size={34} className="text-green-400" />
      </div>
      <h3 className="text-xl font-bold text-slate-100">You're all set!</h3>
      <p className="text-sm text-slate-400 max-w-md mx-auto">
        BallistiCore is configured and ready to use. You can manage company details, firearms,
        guards and users any time from the sidebar. This setup wizard won't appear again.
      </p>

      {/* How other devices on the same network can reach this server */}
      <div className="text-left bg-slate-900/50 border border-slate-700 rounded-xl p-4 max-w-md mx-auto space-y-2">
        <div className="flex items-center gap-2 text-slate-100 font-medium text-sm">
          <Wifi size={16} className="text-blue-400" /> Access from other devices
        </div>
        <p className="text-xs text-slate-400">
          BallistiCore runs on this PC. Other computers, tablets and phones on the same
          network can use it by opening this address in their web browser:
        </p>
        <div className="flex items-center gap-2">
          <code className="flex-1 font-mono text-sm text-blue-300 bg-slate-800/70 border border-slate-700 rounded-lg px-3 py-2 break-all">
            {netUrl || `http://<this-PC-IP>:${port}`}
          </code>
          <button type="button" onClick={copyUrl} disabled={!netUrl} title="Copy address"
            className="shrink-0 p-2 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-700 disabled:opacity-40">
            {copied ? <Check size={15} className="text-green-400" /> : <Copy size={15} />}
          </button>
        </div>
        <p className="text-xs text-slate-500">
          {lanIp && (
            <>This PC's network address is <span className="font-mono text-slate-300">{lanIp}</span>
            {net?.hostname ? ` (${net.hostname})` : ''}. </>
          )}
          If a device can't connect, make sure BallistiCore is allowed through Windows
          Firewall and that network access is enabled — see the installation README.
        </p>
      </div>

      {error && <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2 inline-block">{error}</p>}
      <div className="flex items-center justify-center gap-3 pt-2">
        <button type="button" onClick={onBack} className="text-sm text-slate-400 hover:text-slate-100">← Back</button>
        <button type="button" onClick={finish} disabled={busy}
          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-6 py-2.5 rounded-lg disabled:opacity-50">
          {busy ? <Loader2 size={16} className="animate-spin" /> : <Rocket size={16} />}
          {busy ? 'Finishing…' : 'Go to Dashboard'}
        </button>
      </div>
    </div>
  )
}

// ── Shared nav (Back / Next) ──────────────────────────────────────────────────
function WizardNav({ onBack, onNext, nextLabel = 'Continue', saving }) {
  return (
    <div className="flex items-center justify-between pt-2">
      {onBack
        ? <button type="button" onClick={onBack} className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-100"><ArrowLeft size={15} /> Back</button>
        : <span />}
      <button type="button" onClick={onNext} disabled={saving}
        className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-5 py-2.5 rounded-lg disabled:opacity-50">
        {saving ? <Loader2 size={16} className="animate-spin" /> : null}
        {saving ? 'Saving…' : nextLabel} {!saving && <ArrowRight size={15} />}
      </button>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function SetupWizard() {
  const { company_name, app_name } = useBranding()
  const [step, setStep] = useState(1)
  const next = () => setStep((s) => Math.min(5, s + 1))
  const back = () => setStep((s) => Math.max(1, s - 1))

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center px-4 py-10">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-slate-100">Welcome to {app_name}</h1>
          <p className="text-sm text-slate-400 mt-1">Let's get {company_name && company_name !== 'Your Company' ? company_name : 'your company'} set up — it only takes a few minutes.</p>
        </div>

        <div className="bg-slate-800/60 rounded-2xl border border-slate-700 p-6 sm:p-8 shadow-xl">
          <Stepper step={step} />
          {step === 1 && <CompanyStep onNext={next} />}
          {step === 2 && <FirearmsStep onNext={next} onBack={back} />}
          {step === 3 && <GuardsStep onNext={next} onBack={back} />}
          {step === 4 && <AdminsStep onNext={next} onBack={back} />}
          {step === 5 && <FinishStep onBack={back} />}
        </div>

        <p className="text-center text-xs text-slate-600 mt-6">Step {step} of 5</p>
      </div>
    </div>
  )
}
