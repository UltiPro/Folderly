import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'

import BreadcrumbBar from '../BreadcrumbBar.vue'

describe('BreadcrumbBar', () => {
  it('walks back up its own space', async () => {
    const bar = mount(BreadcrumbBar, { props: { path: '/Photos/Vacation', rootLabel: 'My files' } })
    expect(bar.text()).toContain('My files')

    await bar.get('button').trigger('click')
    expect(bar.emitted('navigate')?.[0]).toEqual(['/'])
    expect(bar.emitted('leave')).toBeUndefined()
  })

  it('offers no way out of a space that has no origin', () => {
    const bar = mount(BreadcrumbBar, { props: { path: '/', rootLabel: 'My files' } })
    expect(bar.findAll('button')).toHaveLength(0)
  })

  it('leads back to where a shared space came from', async () => {
    const bar = mount(BreadcrumbBar, {
      props: { path: '/', rootLabel: 'Photos', origin: 'Shared with me' },
    })
    expect(bar.text()).toContain('Shared with me')

    await bar.get('button').trigger('click')
    expect(bar.emitted('leave')).toHaveLength(1)
    expect(bar.emitted('navigate')).toBeUndefined()
  })
})
