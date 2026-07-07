import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Clock } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useBranding } from '../context/BrandingContext'

// Show the warning this many ms before the hard logout.
const WARN_BEFORE_MS = 30_000
// Passive events (e.g. mousemove) fire constantly — only act on them once per
// second while idle. When the warning is up we respond immediately so it clears.
const THROTTLE_MS = 1000

const ACTIVITY_EVENTS = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll', 'click']

// Logs the user out after a configurable period of inactivity, with a 30-second
// warning first. Mounted inside Layout, so it runs only for authenticated app
// pages — never on the login screen. Any mouse/keyboard/touch event resets it.
export default function IdleTimer() {
  const { session_timeout_minutes } = useBranding()
  const { logout } = useAuth()
  const navigate = useNavigate()

  const [warning, setWarning] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState(Math.round(WARN_BEFORE_MS / 1000))

  // Minimum 1 minute; falls back to 5 if the value is missing/invalid.
  const timeoutMs = Math.max(1, Number(session_timeout_minutes) || 5) * 60_000

  const warnTimer = useRef(null)
  const logoutTimer = useRef(null)
  const lastReset = useRef(0)
  const warningRef = useRef(false)

  const doLogout = useCallback(() => {
    logout()
    navigate('/login', { replace: true })
  }, [logout, navigate])

  // Schedule the warning + logout timers. Deliberately no synchronous setState
  // so it's safe to call from an effect body; state changes happen later inside
  // the timer callbacks.
  const scheduleTimers = useCallback(() => {
    clearTimeout(warnTimer.current)
    clearTimeout(logoutTimer.current)
    warnTimer.current = setTimeout(() => {
      warningRef.current = true
      setSecondsLeft(Math.round(WARN_BEFORE_MS / 1000))
      setWarning(true)
    }, Math.max(0, timeoutMs - WARN_BEFORE_MS))
    logoutTimer.current = setTimeout(doLogout, timeoutMs)
  }, [timeoutMs, doLogout])

  // Reset the countdown — used by activity and the "Stay logged in" button
  // (both event handlers, so setState here is fine).
  const reset = useCallback(() => {
    warningRef.current = false
    setWarning(false)
    scheduleTimers()
  }, [scheduleTimers])

  // Start the timers and wire up activity listeners. Re-runs (e.g. when an admin
  // changes the timeout) restart the countdown cleanly.
  useEffect(() => {
    scheduleTimers()
    const onActivity = () => {
      const now = Date.now()
      // Ignore rapid passive events unless the warning is showing.
      if (!warningRef.current && now - lastReset.current < THROTTLE_MS) return
      lastReset.current = now
      reset()
    }
    ACTIVITY_EVENTS.forEach((e) => window.addEventListener(e, onActivity, { passive: true }))
    return () => {
      clearTimeout(warnTimer.current)
      clearTimeout(logoutTimer.current)
      ACTIVITY_EVENTS.forEach((e) => window.removeEventListener(e, onActivity))
    }
  }, [scheduleTimers, reset])

  // Live countdown shown in the warning modal (display only — logoutTimer is
  // authoritative).
  useEffect(() => {
    if (!warning) return
    const id = setInterval(() => setSecondsLeft((s) => (s > 0 ? s - 1 : 0)), 1000)
    return () => clearInterval(id)
  }, [warning])

  if (!warning) return null

  return (
    <div className="fixed inset-0 z-[70] bg-black/50 flex items-center justify-center p-4">
      <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl w-full max-w-md p-6 text-center space-y-3">
        <div className="mx-auto w-12 h-12 rounded-full bg-amber-500/15 border border-amber-500/40 grid place-items-center">
          <Clock size={22} className="text-amber-400" />
        </div>
        <h3 className="text-lg font-semibold text-slate-100">Still there?</h3>
        <p className="text-sm text-slate-400">
          You'll be logged out in {secondsLeft} second{secondsLeft === 1 ? '' : 's'} due to inactivity.
        </p>
        <div className="flex justify-center gap-3 pt-1">
          <button
            onClick={doLogout}
            className="text-sm text-slate-300 hover:text-white px-4 py-2 rounded-lg"
          >
            Log out now
          </button>
          <button
            onClick={reset}
            className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-5 py-2 rounded-lg"
          >
            Stay logged in
          </button>
        </div>
      </div>
    </div>
  )
}
