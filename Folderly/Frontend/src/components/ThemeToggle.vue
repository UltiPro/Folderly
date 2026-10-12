<script setup lang="ts">
import { useTheme } from '@/composables/useTheme'

const { resolved, toggle } = useTheme()
</script>

<template>
  <button type="button"
    class="group relative grid size-9 shrink-0 place-items-center rounded-lg border border-border-subtle bg-surface text-muted transition hover:bg-surface-sunken hover:text-strong active:scale-95"
    :title="resolved === 'dark' ? 'Switch to the light theme' : 'Switch to the dark theme'"
    :aria-label="resolved === 'dark' ? 'Switch to the light theme' : 'Switch to the dark theme'" @click="toggle">
    <svg class="absolute size-4 transition-all duration-200" :class="resolved === 'dark' ? 'scale-50 rotate-90 opacity-0' : 'scale-100 rotate-0 opacity-100'
      " viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
      aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </svg>

    <svg class="absolute size-4 transition-all duration-200" :class="resolved === 'dark' ? 'scale-100 rotate-0 opacity-100' : 'scale-50 -rotate-90 opacity-0'
      " viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
      stroke-linejoin="round" aria-hidden="true">
      <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8" />
    </svg>
  </button>
</template>
