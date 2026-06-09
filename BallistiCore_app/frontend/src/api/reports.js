/**
 * Reports / SAPS export API.
 * These endpoints return binary Excel files — we use window.open or
 * build an authenticated download via blob URL.
 */
import api from './client'

const buildQuery = (params) => {
  const q = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => { if (v) q.append(k, v) })
  const qs = q.toString()
  return qs ? `?${qs}` : ''
}

export const downloadRegisterExcel = async () => {
  const res = await api.get('/api/reports/register', { responseType: 'blob' })
  _triggerDownload(res)
}

export const downloadHistoryExcel = async (params = {}) => {
  const qs = buildQuery(params)
  const res = await api.get(`/api/reports/history${qs}`, { responseType: 'blob' })
  _triggerDownload(res)
}

export const downloadGuardActivityExcel = async (guardId) => {
  const res = await api.get(`/api/reports/guard/${guardId}`, { responseType: 'blob' })
  _triggerDownload(res)
}

function _triggerDownload(res) {
  const disposition = res.headers['content-disposition'] || ''
  const match = disposition.match(/filename="?([^"]+)"?/)
  const filename = match ? match[1] : 'BallistiCore_Export.xlsx'
  const url = URL.createObjectURL(new Blob([res.data]))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
