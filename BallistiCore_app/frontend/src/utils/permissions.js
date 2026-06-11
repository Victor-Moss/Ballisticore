// Central place for client-side permission checks.
//
// These mirror the backend `require_permission` rules in
// `app/core/auth.py`. The frontend uses them to hide navigation and show an
// Access Denied page; the backend enforces the same rules on mutating
// endpoints so the gate cannot be bypassed by hitting the API directly.

// A super admin bypasses every granular permission check — either the legacy
// `is_admin` flag or the explicit System Admin permission.
export function isSuperAdmin(user) {
  return !!(user && (user.is_admin || user.perm_system_admin))
}

// True if the user is a super admin or holds at least one of the given
// permission keys. Pass a single key or an array. A falsy/empty `keys`
// means "no specific permission required" → allowed for any logged-in user.
export function hasPerm(user, keys) {
  if (!user) return false
  if (isSuperAdmin(user)) return true
  if (!keys) return true
  const list = Array.isArray(keys) ? keys : [keys]
  if (list.length === 0) return true
  return list.some((k) => !!user[k])
}

// The granular permissions that, on their own, grant access to *some* part of
// the Admin section (Users tab). Super admins also reach it via isSuperAdmin.
export const ADMIN_SECTION_PERMS = [
  'perm_add_user',
  'perm_modify_user',
  'perm_change_passwords',
  'perm_clear_logs',
]

// True if the user can reach the Admin section at all.
export function canAccessAdmin(user) {
  return hasPerm(user, ADMIN_SECTION_PERMS)
}
