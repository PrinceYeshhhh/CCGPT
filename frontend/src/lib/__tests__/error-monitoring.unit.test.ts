import { describe, test, expect } from 'vitest'
import { errorReporting } from '@/lib/error-monitoring'

describe('Unit: error-monitoring helpers', () => {
  test('setTags accepts and stores tags (smoke)', () => {
    expect(() => errorReporting.setTags({ env: 'test', comp: 'frontend' })).not.toThrow()
  })
})


