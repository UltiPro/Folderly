<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import AlertMessage from '@/components/ui/AlertMessage.vue'
import RoleBadge from '@/components/RoleBadge.vue'
import { useSpacesStore } from '@/stores/spaces'
import type { SharedFolder } from '@/types/api'

const router = useRouter()
const spaces = useSpacesStore()

onMounted(() => void spaces.refresh())

// Opens a shared folder as its own space, where `/` is the folder itself.
function open(folder: SharedFolder) {
  void router.push({ name: 'files', query: { path: '/', share: folder.share } })
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div>
      <h1 class="text-lg font-semibold">Shared with me</h1>
      <p class="mt-1 text-sm text-muted">
        Folders other people have given you access to, and what you may do in each.
      </p>
    </div>

    <AlertMessage v-if="spaces.error">{{ spaces.error }}</AlertMessage>

    <section class="overflow-hidden rounded-xl border border-border-subtle bg-surface">
      <p v-if="spaces.loading" class="px-4 py-10 text-center text-sm text-muted">Loading...</p>

      <div v-else-if="!spaces.hasShares" class="px-4 py-12 text-center">
        <p class="text-sm font-medium text-soft">Nothing shared with you yet</p>
        <p class="mt-1 text-sm text-muted">When someone shares a folder, it shows up here.</p>
      </div>

      <ul v-else class="divide-y divide-border-subtle">
        <li v-for="folder in spaces.shares" :key="folder.share"
          class="flex items-center gap-3 px-4 py-3 transition hover:bg-surface-sunken">
          <span class="grid size-8 shrink-0 place-items-center rounded-lg bg-brand/10 text-brand" aria-hidden="true">
            <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 20a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2z" />
            </svg>
          </span>

          <div class="min-w-0 flex-1">
            <button type="button"
              class="block max-w-full truncate text-left text-sm font-medium text-strong hover:text-brand hover:underline"
              @click="open(folder)">
              {{ folder.name }}
            </button>
            <span class="text-xs text-muted">Shared by {{ folder.owner_email }}</span>
          </div>

          <RoleBadge :role="folder.role" />
        </li>
      </ul>
    </section>
  </div>
</template>
