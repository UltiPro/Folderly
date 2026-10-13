import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

async function loadTheme() {
  vi.resetModules()
  const module = await import('../useTheme')
  return module.useTheme()
}

function chromeColor(): string | null {
  return document.querySelector('meta[name="theme-color"]')?.getAttribute('content') ?? null
}

describe('useTheme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.head.innerHTML = ''
    document.documentElement.removeAttribute('data-theme')
    vi.stubGlobal(
      'matchMedia',
      vi.fn<(query: string) => MediaQueryList>(
        () =>
          ({
            matches: false,
            addEventListener: () => {},
            removeEventListener: () => {},
          }) as unknown as MediaQueryList,
      ),
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('writes data-theme and the chrome colour as it loads', async () => {
    await loadTheme()

    expect(document.documentElement.dataset.theme).toBe('light')
    expect(chromeColor()).toBe('#ffffff')
  })

  it('moves the chrome colour with the toggle', async () => {
    const theme = await loadTheme()

    theme.toggle()
    await Promise.resolve()
    expect(document.documentElement.dataset.theme).toBe('dark')
    expect(chromeColor()).toBe('#191d23')

    theme.toggle()
    await Promise.resolve()
    expect(document.documentElement.dataset.theme).toBe('light')
    expect(chromeColor()).toBe('#ffffff')
  })

  it('creates the meta tag when the document has none', async () => {
    expect(chromeColor()).toBeNull()

    await loadTheme()

    expect(document.querySelectorAll('meta[name="theme-color"]')).toHaveLength(1)
  })

  it('reuses the meta tag index.html already ships', async () => {
    const meta = document.createElement('meta')
    meta.setAttribute('name', 'theme-color')
    meta.setAttribute('content', '#156CDD')
    document.head.appendChild(meta)

    const theme = await loadTheme()
    theme.set('dark')
    await Promise.resolve()

    expect(document.querySelectorAll('meta[name="theme-color"]')).toHaveLength(1)
    expect(chromeColor()).toBe('#191d23')
  })

  it('remembers the choice across a reload', async () => {
    const theme = await loadTheme()
    theme.set('dark')
    await Promise.resolve()

    const reloaded = await loadTheme()

    expect(reloaded.choice.value).toBe('dark')
    expect(chromeColor()).toBe('#191d23')
  })
})
