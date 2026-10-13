<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{ tone?: 'error' | 'info' | 'success' }>(), {
  tone: 'error',
})

const TONES = {
  error:
    'border-red-200 bg-red-50 text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300',
  info: 'border-border-subtle bg-surface-sunken text-soft',
  success:
    'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300',
} as const

const classes = computed(() => TONES[props.tone])
</script>

<template>
  <p
    :role="tone === 'error' ? 'alert' : 'status'"
    class="rounded-lg border px-3 py-2 text-sm"
    :class="classes"
  >
    <slot />
  </p>
</template>
