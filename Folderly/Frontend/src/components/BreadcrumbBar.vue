<script setup lang="ts">
import { computed } from 'vue'

import { breadcrumbs } from '@/utils/path'
import type { SpacePath } from '@/types/api'

const props = defineProps<{
  path: SpacePath
  // Names the space itself: "My files", or the shared folder's own name.
  rootLabel: string
}>()

const emit = defineEmits<{ navigate: [path: SpacePath] }>()

const crumbs = computed(() => breadcrumbs(props.path, props.rootLabel))
</script>

<template>
  <nav aria-label="Breadcrumb" class="flex flex-wrap items-center gap-1 text-sm">
    <template v-for="(crumb, index) in crumbs" :key="crumb.path">
      <span v-if="index > 0" class="text-border-subtle" aria-hidden="true">/</span>

      <span v-if="index === crumbs.length - 1" aria-current="page"
        class="rounded px-1.5 py-0.5 font-medium text-strong">
        {{ crumb.label }}
      </span>
      <button v-else type="button"
        class="rounded px-1.5 py-0.5 text-muted transition hover:bg-surface-sunken hover:text-strong"
        @click="emit('navigate', crumb.path)">
        {{ crumb.label }}
      </button>
    </template>
  </nav>
</template>
