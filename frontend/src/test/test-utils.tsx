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
    container.id = 'root'
    document.body.appendChild(container)
  }
  
  // Clear any existing content but don't remove the container
  container.innerHTML = ''
  
  // Ensure the container is properly attached to document.body
  if (!document.body.contains(container)) {
    document.body.appendChild(container)
  }
  
  // Ensure the container is a proper HTMLElement
  if (!(container instanceof HTMLElement)) {
    throw new Error('Container is not a valid HTMLElement')
  }
  
  return rtlRender(ui, {
    wrapper: Providers,
    container,
    ...options,
  })
}

export * from '@testing-library/react'