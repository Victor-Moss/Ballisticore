import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard } from '../api/dashboard'
import {
  Crosshair, CircleCheck, Archive, Shield, Undo2, ArrowRight, Loader2,
  FileText, CalendarClock,
} from 'lucide-react'

const ACCENTS = {
  red:    { icon: 'text-red-400',    ring: 'bg-red-500/10 ring-red-500/20' },
  green:  { icon: 'text-green-400',  ring: 'bg-green-500/10 ring-green-500/20' },
  blue:   { icon: 'text-blue-400',   ring: 'bg-blue-500/10 ring-blue-500/20' },
  amber:  { icon: 'text-amber-400',  ring: 'bg-amber-500/10 ring-amber-500/20' },
  purple: { icon: 'text-purple-400', ring: 'bg-purple-500/10 ring-purple-500/20' },
}

function StatCard({ label, value, icon: Icon, color = 'blue' }) {
  const a = ACCENTS[color]
  return (
    <div className="bc-card p-5 flex items-center gap-4">
      <div className={`grid place-items-center h-12 w-12 rounded-xl ring-1 ${a.ring}`}>
        <Icon size={22} className={a.icon} />
      </div>
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
        <p className="text-3xl font-bold text-white leading-tight mt-0.5">{value ?? '—'}</p>
      </div>
    </div>
  )
}

// Relative "x ago" with a clean absolute fallback.
function timeAgo(iso) {
  const then = new Date(iso)
  const secs = Math.round((Date.now() - then.getTime()) / 1000)
  if (secs < 60) return 'just now'
  const mins = Math.round(secs / 60)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.round(hrs / 24)
  if (days < 7) return `${days}d ago`
  return then.toLocaleDateString('en-ZA', { day: 'numeric', month: 'short' })
}

function ActivityTimeline({ items }) {
  if (!items.length) {
    return (
      <div className="bc-card p-10 text-center">
        <CircleCheck size={28} className="mx-auto text-slate-600 mb-2" />
        <p className="text-slate-400 text-sm">No firearm activity yet</p>
      </div>
    )
  }
  return (
    <ol className="bc-card p-5">
      {items.map((it, i) => {
        const issued = it.action === 'ISSUED'
        const Icon = issued ? Crosshair : Undo2
        const a = ACCENTS[issued ? 'red' : 'green']
        const last = i === items.length - 1
        return (
          <li key={it.id} className="relative flex gap-4 pb-5 last:pb-0">
            {/* connector line down to the next dot */}
            {!last && <span className="absolute left-[19px] top-10 -bottom-0 w-px bg-slate-700/70" />}
            <div className={`relative z-10 grid place-items-center h-10 w-10 shrink-0 rounded-full ring-1 ${a.ring}`}>
              <Icon size={18} className={a.icon} />
            </div>
            <div className="flex-1 min-w-0 pt-0.5">
              <p className="text-sm text-slate-100">
                <span className="font-medium">{it.guard_name}</span>
                <span className="text-slate-400">{issued ? ' was issued ' : ' returned '}</span>
                <span className="font-medium">{it.firearm}</span>
              </p>
              <div className="flex items-center gap-2 mt-0.5">
                <span className={`text-[11px] font-medium px-1.5 py-0.5 rounded ${issued ? 'bg-red-500/10 text-red-300' : 'bg-green-500/10 text-green-300'}`}>
                  {issued ? 'Issued' : 'Returned'}
                </span>
                <span className="text-xs text-slate-500" title={new Date(it.at).toLocaleString('en-ZA')}>
                  {timeAgo(it.at)}
                </span>
              </div>
            </div>
          </li>
        )
      })}
    </ol>
  )
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDashboard()
      .then((res) => setData(res.data))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400 text-sm gap-2">
        <Loader2 size={16} className="animate-spin" /> Loading…
      </div>
    )
  }

  const s = data?.stats || {}
  const activity = data?.recent_activity || []

  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto">
      <div className="mb-7">
        <h2 className="text-2xl font-bold text-white tracking-tight">Dashboard</h2>
        <p className="text-sm text-slate-400 mt-0.5">Overview of your firearms register.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        <StatCard label="Total Firearms"    value={s.total_firearms}     icon={Archive}       color="blue" />
        <StatCard label="Currently Issued"  value={s.issued_firearms}    icon={Crosshair}     color="red" />
        <StatCard label="Available"         value={s.available_firearms} icon={CircleCheck}   color="green" />
        <StatCard label="Active Guards"     value={s.active_guards}      icon={Shield}        color="amber" />
        <StatCard label="Permits Generated" value={s.total_permits}      icon={FileText}      color="purple" />
        <StatCard label="Permits Today"     value={s.permits_today}      icon={CalendarClock} color="amber" />
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <Link to="/issue"
          className="group bc-card p-5 flex items-center gap-4 hover:border-blue-500/50 hover:bg-[#243044] transition-colors">
          <div className="grid place-items-center h-12 w-12 rounded-xl bg-blue-600 shadow-lg shadow-blue-600/30">
            <Crosshair size={22} className="text-white" />
          </div>
          <div className="flex-1">
            <p className="font-semibold text-white">Issue Firearm</p>
            <p className="text-xs text-slate-400">Assign a firearm to a guard</p>
          </div>
          <ArrowRight size={18} className="text-slate-500 group-hover:text-blue-400 group-hover:translate-x-0.5 transition-all" />
        </Link>
        <Link to="/return"
          className="group bc-card p-5 flex items-center gap-4 hover:border-green-500/50 hover:bg-[#243044] transition-colors">
          <div className="grid place-items-center h-12 w-12 rounded-xl bg-green-600 shadow-lg shadow-green-600/30">
            <Undo2 size={22} className="text-white" />
          </div>
          <div className="flex-1">
            <p className="font-semibold text-white">Return Firearm</p>
            <p className="text-xs text-slate-400">Record a firearm being handed back</p>
          </div>
          <ArrowRight size={18} className="text-slate-500 group-hover:text-green-400 group-hover:translate-x-0.5 transition-all" />
        </Link>
      </div>

      {/* Recent activity */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-white">Recent Activity</h3>
        <Link to="/history" className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1">
          View history <ArrowRight size={14} />
        </Link>
      </div>
      <ActivityTimeline items={activity} />
    </div>
  )
}
