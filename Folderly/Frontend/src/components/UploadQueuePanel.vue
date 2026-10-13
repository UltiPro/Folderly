<script setup lang="ts">
import { computed } from 'vue'

import BaseButton from '@/components/ui/BaseButton.vue'
import { formatSize } from '@/utils/format'
import type { UploadItem } from '@/composables/useUploadQueue'

const props = defineProps<{
  items: UploadItem[]
  overallProgress: number
  active: boolean
}>()

const emit = defineEmits<{ dismiss: [] }>()

const done = computed(() => props.items.filter((item) => item.status === 'done').length)
const failed = computed(() => props.items.filter((item) => item.status === 'failed'))

const heading = computed(() => {
  if (props.active) return `Uploading ${done.value + 1} of ${props.items.length}...`
  if (failed.value.length) return `${failed.value.length} of ${props.items.length} did not upload`
  return `Uploaded ${props.items.length === 1 ? 'the file' : `all ${props.items.length} files`}`
})
</script>

<template>
  <section
    v-if="items.length"
    class="rounded-xl border border-border-subtle bg-surface p-4"
    aria-live="polite"
  >
    <div class="flex items-center gap-3">
      <p class="flex-1 text-sm font-medium text-strong">{{ heading }}</p>
      <BaseButton v-if="!active" size="sm" variant="ghost" @click="emit('dismiss')">
        Dismiss
      </BaseButton>
    </div>

    <div v-if="active" class="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-sunken">
      <div
        class="h-full rounded-full bg-brand transition-[width] duration-200"
        :style="{ width: `${overallProgress}%` }"
      />
    </div>

    <ul class="mt-3 flex max-h-48 flex-col gap-1.5 overflow-y-auto text-sm">
      <li v-for="item in items" :key="item.id" class="flex items-center gap-2">
        <span
          class="size-1.5 shrink-0 rounded-full"
          :class="{
            'bg-slate-300': item.status === 'waiting',
            'bg-brand': item.status === 'uploading',
            'bg-emerald-500': item.status === 'done',
            'bg-red-500': item.status === 'failed',
          }"
          aria-hidden="true"
        />
        <span class="min-w-0 flex-1 truncate">{{ item.name }}</span>

        <span v-if="item.status === 'failed'" class="shrink-0 text-xs text-red-600">
          {{ item.error }}
        </span>
        <span v-else-if="item.status === 'uploading'" class="shrink-0 text-xs text-muted">
          {{ item.progress }}%
        </span>
        <span v-else-if="item.status === 'waiting'" class="shrink-0 text-xs text-muted">
          waiting
        </span>
        <span v-else class="shrink-0 text-xs text-muted">{{ formatSize(item.size) }}</span>
      </li>
    </ul>
  </section>
</template>
