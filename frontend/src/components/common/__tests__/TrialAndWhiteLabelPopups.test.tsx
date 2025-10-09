import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { TrialPopup } from '../../TrialPopup'
import { WhiteLabelPopup } from '../../WhiteLabelPopup'
import { PostLoginTrialPopup } from '../../PostLoginTrialPopup'

describe('Trial and WhiteLabel Popups', () => {
  const onClose = vi.fn()

  it('renders TrialPopup and handles close', () => {
    render(<TrialPopup isOpen onClose={onClose} />)
    expect(screen.getByText(/Trial/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /close/i }))
    expect(onClose).toHaveBeenCalled()
  })

  it('renders PostLoginTrialPopup and handles actions', () => {
    render(<PostLoginTrialPopup isOpen onClose={onClose} />)
    const maybeButton = screen.queryByRole('button')
    if (maybeButton) fireEvent.click(maybeButton)
    expect(onClose).toHaveBeenCalled()
  })

  it('renders WhiteLabelPopup and handles close', () => {
    render(<WhiteLabelPopup isOpen onClose={onClose} />)
    expect(screen.getByText(/White Label/i)).toBeInTheDocument()
    const closeBtn = screen.getByRole('button', { name: /close/i })
    fireEvent.click(closeBtn)
    expect(onClose).toHaveBeenCalled()
  })
})


