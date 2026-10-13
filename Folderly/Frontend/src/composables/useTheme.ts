import { computed, ref, watch } from 'vue'

export type ThemeChoice = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'folderly.theme'

function stored(): ThemeChoice {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'light' || saved === 'dark' || saved === 'system') return saved
  } catch {
    // Private windows and blocked site data throw, the default is fine.
  }
  return 'system'
}

const choice = ref<ThemeChoice>(stored())
const systemDark = ref(false)

const query =
  typeof window !== 'undefined' ? window.matchMedia('(prefers-color-scheme: dark)') : null
if (query) {
  systemDark.value = query.matches
  query.addEventListener('change', (event) => {
    systemDark.value = event.matches
  })
}

const resolved = computed<'light' | 'dark'>(() =>
  choice.value === 'system' ? (systemDark.value ? 'dark' : 'light') : choice.value,
)

// Mirrors `--color-surface` from assets/main.css.
const CHROME_COLOR: Record<'light' | 'dark', string> = {
  light: '#ffffff',
  dark: '#191d23',
}

function paintBrowserChrome(theme: 'light' | 'dark') {
  let meta = document.querySelector('meta[name="theme-color"]')
  if (!meta) {
    meta = document.createElement('meta')
    meta.setAttribute('name', 'theme-color')
    document.head.appendChild(meta)
  }
  meta.setAttribute('content', CHROME_COLOR[theme])
}

watch(
  resolved,
  (theme) => {
    document.documentElement.dataset.theme = theme
    paintBrowserChrome(theme)
  },
  { immediate: true },
)

watch(choice, (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, value)
  } catch {
    // The theme still applies for this visit, only remembering it fails.
  }
})

export function useTheme() {
  function set(value: ThemeChoice) {
    choice.value = value
  }

  function toggle() {
    set(resolved.value === 'dark' ? 'light' : 'dark')
  }

  return { choice, resolved, set, toggle }
}
