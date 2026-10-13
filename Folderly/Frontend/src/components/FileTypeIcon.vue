<script setup lang="ts">
import { computed } from 'vue'

import { fileKind, kindLabel, kindTone } from '@/utils/filetypes'

const props = defineProps<{ extension?: string; folder?: boolean }>()

const label = computed(() => (props.folder ? null : kindLabel(props.extension ?? '')))
const tone = computed(() =>
  props.folder ? 'bg-brand/10 text-brand' : kindTone(fileKind(props.extension ?? '')),
)
</script>

<template>
  <span
    class="grid size-8 shrink-0 place-items-center rounded-lg transition"
    :class="tone"
    aria-hidden="true"
  >
    <svg
      v-if="folder"
      class="size-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
    >
      <path d="M4 20a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2z" />
    </svg>

    <span
      v-else-if="label"
      class="font-semibold leading-none"
      :class="label.length > 3 ? 'text-[9px] tracking-tighter' : 'text-[10px] tracking-tight'"
    >
      {{ label }}
    </span>

    <svg
      v-else
      class="size-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path d="M14 2v6h6" />
    </svg>
  </span>
</template>
