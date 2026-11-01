const API = 'http://127.0.0.1:8000'

export async function analyzeImage(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API}/api/analyze`, {
    method: 'POST',
    body: formData
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.detail || 'Analysis failed')
  }

  return data
}

export async function generateReport(analysisId) {
  const response = await fetch(`${API}/api/report/${analysisId}`, {
    method: 'POST'
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.detail || 'Report generation failed')
  }

  return `${API}${data.download_url}`
}

export function resultUrl(path) {
  return path ? `${API}${path}` : null
}
