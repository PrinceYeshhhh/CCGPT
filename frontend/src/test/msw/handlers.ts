import { rest } from 'msw'

const apiBase = (import.meta as any).env?.VITE_API_URL || 'http://localhost:5173/api/v1'

export const handlers = [
  // Documents listing
  rest.get(`${apiBase}/documents`, async (_req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        items: [
          { id: 'doc-1', name: 'Doc 1' },
          { id: 'doc-2', name: 'Doc 2' },
        ],
        total: 2,
      })
    )
  }),

  // Billing current plan
  rest.get(`${apiBase}/billing/plan`, async (_req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ plan: { name: 'pro', status: 'active' } })
    )
  }),

  // Analytics dataset
  rest.get(`${apiBase}/analytics/summary`, async (_req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ data: [{ x: 1, y: 2 }] })
    )
  }),
]


