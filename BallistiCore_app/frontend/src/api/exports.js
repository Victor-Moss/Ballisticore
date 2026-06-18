import api from './client'

const ZIP = 'application/zip'

// Download the full data export (Excel + CSV bundle + PDF summary) as one ZIP.
export const downloadFullExport = async () => {
  const res = await api.get('/api/export/all', { responseType: 'blob' })
  const disposition = res.headers['content-disposition'] || ''
  const match = disposition.match(/filename="?([^"]+)"?/)
  const filename = match ? match[1] : 'BallistiCore_Export.zip'
  const url = URL.createObjectURL(new Blob([res.data], { type: ZIP }))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
