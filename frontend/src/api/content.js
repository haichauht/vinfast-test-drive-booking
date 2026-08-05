import { apiGet } from './client'

const allowedPages = new Set(['home', 'charging', 'after-sales'])

export function getPageContent(page, options = {}) {
  if (!allowedPages.has(page)) throw new Error(`Unsupported content page: ${page}`)
  return apiGet(`/content/${page}`, { ...options, cacheKey: `content:${page}` })
}
