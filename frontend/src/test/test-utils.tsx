import React, { ReactElement } from 'react'
import { BrowserRouter } from 'react-router-dom'
import { render as rtlRender, RenderOptions } from '@testing-library/react'

type ProvidersProps = { children: React.ReactNode }

function Providers({ children }: ProvidersProps) {
  return (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  )
}

export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  // Ensure a root container exists for React 18 createRoot
  let container = document.getElementById('root') as HTMLElement | null
  if (!container) {
    container = document.createElement('div')
    container.setAttribute('id', 'root')
    document.body.appendChild(container)
  }
  return rtlRender(ui, {
    wrapper: Providers,
    container,
    ...options,
  })
}

export * from '@testing-library/react'