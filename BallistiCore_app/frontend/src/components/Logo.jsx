import { Crosshair } from 'lucide-react'

/**
 * Brand mark — a crosshair badge (ballistics) in a steel-blue gradient.
 * Used on the login screen and sidebar.
 */
export default function Logo({ size = 40, className = '' }) {
  return (
    <div
      className={`grid place-items-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-700
                  ring-1 ring-white/10 shadow-lg shadow-blue-600/30 ${className}`}
      style={{ width: size, height: size }}
    >
      <Crosshair className="text-white" size={Math.round(size * 0.56)} strokeWidth={2.25} />
    </div>
  )
}
