<script setup lang="ts">
import { computed } from 'vue'

import { formatSize } from '@/utils/format'
import type { DiskUsage } from '@/types/api'

const props = defineProps<{ usage: DiskUsage | null }>()

const tone = computed(() => {
  const usage = props.usage
  if (!usage) return 'normal'
  if (usage.uploads_blocked) return 'blocked'
  if (usage.percent_used >= usage.limit_percent - 5) return 'warning'
  return 'normal'
})

const barColor = computed(
  () => ({ normal: 'bg-brand', warning: 'bg-amber-500', blocked: 'bg-red-500' })[tone.value],
)

const textColor = computed(
  () =>
    ({
      normal: 'text-muted',
      warning: 'text-amber-700 dark:text-amber-300',
      blocked: 'text-red-700 dark:text-red-300',
    })[tone.value],
)

const width = computed(() => {
  if (!props.usage) return 0
  return Math.min(100, Math.max(props.usage.percent_used, props.usage.used > 0 ? 1 : 0))
})

const message = computed(() => {
  const usage = props.usage
  if (!usage) return ''
  if (usage.uploads_blocked) {
    return `Storage is full - uploads are paused above ${usage.limit_percent}%. Delete some files to free space.`
  }
  if (tone.value === 'warning') {
    return `Almost full - uploads stop at ${usage.limit_percent}%.`
  }
  return `${formatSize(usage.free)} free`
})
</script>

<template>
  <div v-if="usage" class="flex flex-col gap-1.5">
    <div class="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5 text-xs">
      <span class="font-medium text-soft">
        {{ formatSize(usage.used) }} of {{ formatSize(usage.total) }} used
      </span>
      <span :class="textColor">{{ message }}</span>
    </div>

    <div class="h-1.5 w-full overflow-hidden rounded-full bg-surface-sunken" role="progressbar"
      :aria-valuenow="Math.round(usage.percent_used)" aria-valuemin="0" aria-valuemax="100"
      :aria-label="`Storage used: ${Math.round(usage.percent_used)}%`">
      <div class="h-full rounded-full transition-[width] duration-300" :class="barColor"
        :style="{ width: `${width}%` }" />
    </div>
  </div>
</template>
