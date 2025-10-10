import React, { ReactElement } from 'react'
import { render as rtlRender, RenderOptions } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

type ProvidersProps = { children: React.ReactNode }

function Providers({ children }: ProvidersProps) {
  return (
    <MemoryRouter>
      {children}
    </MemoryRouter>
  )
}

export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return rtlRender(ui, {
    wrapper: Providers,
    ...options,
  })
}

// Export the standard render function as well
export { render } from '@testing-library/react'
export * from '@testing-library/react'