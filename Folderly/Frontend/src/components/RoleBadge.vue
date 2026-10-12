<script setup lang="ts">
import { computed } from 'vue'

import { roleLabel, type Capability } from '@/utils/roles'

const props = defineProps<{ role: Capability }>()

const TONES: Record<Capability, string> = {
  read: 'bg-surface-sunken text-muted',
  add: 'bg-brand/10 text-brand',
  edit: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  owner: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300',
}

const tone = computed(() => TONES[props.role])
</script>

<template>
  <span class="shrink-0 rounded-full px-2 py-0.5 text-xs font-medium" :class="tone">
    {{ roleLabel(role) }}
  </span>
</template>
