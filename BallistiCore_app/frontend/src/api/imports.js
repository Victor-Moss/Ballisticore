import api from './client'

const XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

export const downloadTemplate = async () => {
  const res = await api.get('/api/import/template', { responseType: 'blob' })
  const disposition = res.headers['content-disposition'] || ''
  const match = disposition.match(/filename="?([^"]+)"?/)
  const filename = match ? match[1] : 'BallistiCore_Import_Template.xlsx'
  const url = URL.createObjectURL(new Blob([res.data], { type: XLSX }))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export const uploadImport = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/api/import/', form)
}
