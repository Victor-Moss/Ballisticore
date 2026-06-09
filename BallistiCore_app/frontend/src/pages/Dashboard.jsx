import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getCurrentRegister } from '../api/register'
import { getFirearms } from '../api/firearms'
import { getGuards } from '../api/guards'
import {
  Crosshair, CircleCheck, Archive, Shield, Undo2, ArrowRight, Loader2,
} from 'lucide-react'

const ACCENTS = {
  red:   { icon: 'text-red-400',   ring: 'bg-red-500/10 ring-red-500/20' },
  green: { icon: 'text-green-400', ring: 'bg-green-500/10 ring-green-500/20' },
  blue:  { icon: 'text-blue-400',  ring: 'bg-blue-500/10 ring-blue-500/20' },
  amber: { icon: 'text-amber-400', ring: 'bg-amber-500/10 ring-amber-500/20' },
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
        <p className="text-3xl font-bold text-white leading-tight mt-0.5">{value}</p>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [register, setRegister] = useState([])
  const [firearms, setFirearms] = useState([])
  const [guards, setGuards] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getCurrentRegister(),
      getFirearms(),
      getGuards(),
    ]).then(([regRes, faRes, gRes]) => {
      setRegister(regRes.data)
      setFirearms(faRes.data)
      setGuards(gRes.data)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400 text-sm gap-2">
        <Loader2 size={16} className="animate-spin" /> Loading…
      </div>
    )
  }

  const issued = register.length
  const totalFirearms = firearms.length
  const available = totalFirearms - issued
  const activeGuards = guards.filter((g) => g.is_active).length

  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto">
      <div className="mb-7">
        <h2 className="text-2xl font-bold text-white tracking-tight">Dashboard</h2>
        <p className="text-sm text-slate-400 mt-0.5">Overview of your firearms register.</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Firearms Out" value={issued} icon={Crosshair} color="red" />
        <StatCard label="Available" value={available} icon={CircleCheck} color="green" />
        <StatCard label="Total Firearms" value={totalFirearms} icon={Archive} color="blue" />
        <StatCard label="Active Guards" value={activeGuards} icon={Shield} color="amber" />
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <Link
          to="/issue"
          className="group bc-card p-5 flex items-center gap-4 hover:border-blue-500/50 hover:bg-[#243044] transition-colors"
        >
          <div className="grid place-items-center h-12 w-12 rounded-xl bg-blue-600 shadow-lg shadow-blue-600/30">
            <Crosshair size={22} className="text-white" />
          </div>
          <div className="flex-1">
            <p className="font-semibold text-white">Issue Firearm</p>
            <p className="text-xs text-slate-400">Assign a firearm to a guard</p>
          </div>
          <ArrowRight size={18} className="text-slate-500 group-hover:text-blue-400 group-hover:translate-x-0.5 transition-all" />
        </Link>
        <Link
          to="/return"
          className="group bc-card p-5 flex items-center gap-4 hover:border-green-500/50 hover:bg-[#243044] transition-colors"
        >
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

      {/* Current register snapshot */}
      {register.length > 0 ? (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-white">Currently Issued</h3>
            <Link to="/register" className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1">
              View all <ArrowRight size={14} />
            </Link>
          </div>
          <div className="bc-card divide-y divide-slate-700/60">
            {register.slice(0, 5).map((entry) => (
              <div key={entry.id} className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-3">
                  <div className="grid place-items-center h-9 w-9 rounded-lg bg-slate-700/50">
                    <Shield size={16} className="text-slate-300" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-100">
                      {entry.guard?.first_name} {entry.guard?.last_name}
                    </p>
                    <p className="text-xs text-slate-400">{entry.firearm?.make} {entry.firearm?.model} — {entry.firearm?.serial_number}</p>
                  </div>
                </div>
                <span className="text-xs text-slate-500">
                  {new Date(entry.issued_at).toLocaleDateString('en-ZA')}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="bc-card p-10 text-center">
          <CircleCheck size={28} className="mx-auto text-slate-600 mb-2" />
          <p className="text-slate-400 text-sm">No firearms currently issued</p>
        </div>
      )}
    </div>
  )
}
