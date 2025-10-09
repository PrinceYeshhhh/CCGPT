import { describe, it, expect, vi } from 'vitest'

describe('main.tsx bootstrap', () => {
  it('mounts React app into #root', async () => {
    const rootEl = document.createElement('div')
    rootEl.id = 'root'
    document.body.appendChild(rootEl)

    const mockRender = vi.fn()
    const mockCreateRoot = vi.fn(() => ({ render: mockRender }))

    vi.mock('react-dom/client', () => ({
      createRoot: mockCreateRoot,
    }))

    await import('../main')

    expect(mockCreateRoot).toHaveBeenCalled()
    expect(mockRender).toHaveBeenCalled()
  })
})


