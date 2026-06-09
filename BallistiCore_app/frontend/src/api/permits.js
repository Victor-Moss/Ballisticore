import api from './client'

export const getPermits = () => api.get('/api/permits/')
export const getPermit = (id) => api.get(`/api/permits/${id}`)
export const generatePermit = (id) => api.post(`/api/permits/${id}/generate`)
export const resendWhatsapp = (id, recipientNumber) =>
  api.post(`/api/permits/${id}/resend-whatsapp`, { recipient_number: recipientNumber })

function _triggerDownload(res, fallbackName) {
  const disposition = res.headers['content-disposition'] || ''
  const match = disposition.match(/filename="?([^"]+)"?/)
  const filename = match ? match[1] : fallbackName
  const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export const downloadPermit = async (id) => {
  const res = await api.get(`/api/permits/${id}/download`, { responseType: 'blob' })
  _triggerDownload(res, `permit_${id}.pdf`)
}

export const downloadMiniPermit = async (id) => {
  const res = await api.get(`/api/permits/${id}/download-mini`, { responseType: 'blob' })
  _triggerDownload(res, `permit_${id}_mini.pdf`)
}
