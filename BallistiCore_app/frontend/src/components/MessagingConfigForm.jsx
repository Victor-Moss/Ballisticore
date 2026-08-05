import { useEffect, useState } from 'react'
import { Send, MessageSquare, Ban, Loader2, CheckCircle2, XCircle } from 'lucide-react'
import { getMessagingConfig, updateMessagingConfig, testMessaging } from '../api/messaging'

const inputCls =
  'w-full border border-slate-700 rounded-lg px-3 py-2 text-sm bg-slate-800/60 ' +
  'focus:outline-none focus:ring-2 focus:ring-blue-500'
const labelCls = 'block text-xs font-medium text-slate-400 mb-1'

const BLANK = {
  provider: 'none',
  telegram_bot_token: '',
  whatsapp_account_sid: '',
  whatsapp_auth_token: '',
  whatsapp_from_number: '',
}

const PROVIDERS = [
  {
    id: 'telegram', label: 'Telegram', icon: Send,
    blurb: 'Create a bot via @BotFather and paste its token. Permits are delivered as a PDF in chat.',
  },
  {
    id: 'whatsapp', label: 'WhatsApp (Twilio)', icon: MessageSquare,
    blurb: 'Use a Twilio WhatsApp sender. Permits are sent to each guard\'s cell number.',
  },
  {
    id: 'none', label: 'None / Manual', icon: Ban,
    blurb: 'Permits are generated but not delivered automatically. Download and hand them out manually.',
  },
]

// Reusable provider picker + credential fields + Test/Save buttons. Used by both
// the Setup Wizard messaging step and Settings → Messaging.
export default function MessagingConfigForm({ onSaved, saveLabel = 'Save', showSave = true }) {
  const [form, setForm] = useState(null)
  const [testRecipient, setTestRecipient] = useState('')
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null) // { ok, message }
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    getMessagingConfig()
      .then((res) => setForm({ ...BLANK, ...res.data }))
      .catch(() => setForm({ ...BLANK }))
  }, [])

  const set = (k, v) => { setForm((f) => ({ ...f, [k]: v })); setTestResult(null); setSuccess('') }
  const pick = (provider) => { setForm((f) => ({ ...f, provider })); setTestResult(null); setSuccess(''); setError('') }

  const handleTest = async () => {
    setTesting(true); setTestResult(null)
    try {
      const res = await testMessaging({ ...form, recipient: testRecipient })
      setTestResult(res.data)
    } catch (err) {
      setTestResult({ ok: false, message: err.response?.data?.detail || 'Test failed.' })
    } finally {
      setTesting(false)
    }
  }

  const save = async () => {
    setSaving(true); setError(''); setSuccess('')
    try {
      await updateMessagingConfig(form)
      setSuccess('Messaging settings saved.')
      onSaved?.(form)
      return true
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not save messaging settings.')
      return false
    } finally {
      setSaving(false)
    }
  }

  const testPlaceholder =
    form?.provider === 'telegram' ? 'Telegram Chat ID to test (e.g. 123456789)'
      : form?.provider === 'whatsapp' ? 'WhatsApp number to test (e.g. 0821234567)'
        : ''

  if (!form) return <p className="text-sm text-slate-500 py-8">Loading…</p>

  return (
    <div className="space-y-5">
      {/* Provider selector */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {PROVIDERS.map((p) => {
          const Icon = p.icon
          const active = form.provider === p.id
          return (
            <button type="button" key={p.id} onClick={() => pick(p.id)}
              className={`text-left rounded-xl border p-4 transition-colors ${
                active
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-slate-700 bg-slate-800/40 hover:border-slate-600'
              }`}>
              <div className="flex items-center gap-2 mb-1">
                <Icon size={18} className={active ? 'text-blue-300' : 'text-slate-400'} />
                <span className={`text-sm font-medium ${active ? 'text-blue-200' : 'text-slate-200'}`}>{p.label}</span>
              </div>
              <p className="text-xs text-slate-400 leading-snug">{p.blurb}</p>
            </button>
          )
        })}
      </div>

      {/* Telegram config */}
      {form.provider === 'telegram' && (
        <div className="bg-slate-800/40 border border-slate-700 rounded-xl p-4 space-y-3">
          <div>
            <label className={labelCls}>Telegram Bot Token *</label>
            <input className={`${inputCls} font-mono`} value={form.telegram_bot_token}
              onChange={(e) => set('telegram_bot_token', e.target.value)}
              placeholder="123456789:AAExampleTokenFromBotFather" />
          </div>
          <p className="text-xs text-slate-400">
            In Telegram, message <span className="text-slate-200 font-mono">@BotFather</span>, send{' '}
            <span className="text-slate-200 font-mono">/newbot</span>, follow the prompts, and paste the token it
            gives you. Each guard must send <span className="text-slate-200 font-mono">/start</span> to your bot
            once so it can obtain their Chat ID.
          </p>
        </div>
      )}

      {/* WhatsApp config */}
      {form.provider === 'whatsapp' && (
        <div className="bg-slate-800/40 border border-slate-700 rounded-xl p-4 grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className={labelCls}>Account SID *</label>
            <input className={`${inputCls} font-mono`} value={form.whatsapp_account_sid}
              onChange={(e) => set('whatsapp_account_sid', e.target.value)} placeholder="ACxxxxxxxx" />
          </div>
          <div>
            <label className={labelCls}>Auth Token *</label>
            <input type="password" className={`${inputCls} font-mono`} value={form.whatsapp_auth_token}
              onChange={(e) => set('whatsapp_auth_token', e.target.value)} placeholder="••••••••" />
          </div>
          <div className="md:col-span-2">
            <label className={labelCls}>From Number *</label>
            <input className={`${inputCls} font-mono`} value={form.whatsapp_from_number}
              onChange={(e) => set('whatsapp_from_number', e.target.value)} placeholder="whatsapp:+14155238886" />
            <p className="text-xs text-slate-500 mt-1">Your Twilio WhatsApp sender (sandbox or purchased number).</p>
          </div>
        </div>
      )}

      {/* None */}
      {form.provider === 'none' && (
        <div className="bg-slate-800/40 border border-slate-700 rounded-xl p-4">
          <p className="text-sm text-slate-300">
            Automatic delivery is off. Permits are still generated — download and distribute them manually
            from the Permits screen.
          </p>
        </div>
      )}

      {/* Test */}
      {form.provider !== 'none' && (
        <div className="bg-slate-900/40 border border-slate-700 rounded-xl p-4 space-y-2">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Send a test</p>
          <div className="flex gap-2">
            <input className={inputCls} value={testRecipient}
              onChange={(e) => setTestRecipient(e.target.value)} placeholder={testPlaceholder} />
            <button type="button" onClick={handleTest} disabled={testing}
              className="inline-flex items-center gap-2 shrink-0 bg-slate-700 hover:bg-slate-600 text-white text-sm px-4 py-2 rounded-lg disabled:opacity-50">
              {testing ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
              {testing ? 'Sending…' : 'Test'}
            </button>
          </div>
          {testResult && (
            <p className={`flex items-center gap-1.5 text-sm ${testResult.ok ? 'text-green-400' : 'text-red-400'}`}>
              {testResult.ok ? <CheckCircle2 size={15} /> : <XCircle size={15} />}
              {testResult.message}
            </p>
          )}
        </div>
      )}

      {error && <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2">{error}</p>}
      {success && <p className="text-sm text-green-400 bg-green-500/10 border border-green-500/30 rounded-lg px-3 py-2">{success}</p>}

      {showSave && (
        <button type="button" onClick={save} disabled={saving}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-6 py-2.5 rounded-lg disabled:opacity-50">
          {saving ? 'Saving…' : saveLabel}
        </button>
      )}
    </div>
  )
}
