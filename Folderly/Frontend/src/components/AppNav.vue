<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import BaseButton from '@/components/ui/BaseButton.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'
import { useAuthStore } from '@/stores/auth'
import { useBrowserStore } from '@/stores/browser'
import { useDiskStore } from '@/stores/disk'
import { useSpacesStore } from '@/stores/spaces'

const auth = useAuthStore()
const browser = useBrowserStore()
const disk = useDiskStore()
const spaces = useSpacesStore()
const router = useRouter()

const loggingOut = ref(false)

async function logout() {
  loggingOut.value = true
  try {
    await auth.logout()
    // Nothing of this account may carry over to whoever logs in next: share
    // tokens name other people's folders, and the listing is their files.
    browser.clear()
    spaces.clear()
    disk.clear()
    await router.push({ name: 'login' })
  } finally {
    loggingOut.value = false
  }
}

const linkBase =
  'shrink-0 rounded-lg px-2.5 py-1.5 text-sm font-medium whitespace-nowrap transition hover:bg-surface-sunken sm:px-3'
const linkActive = 'bg-surface-sunken text-strong'
const linkIdle = 'text-muted'
</script>

<template>
  <header class="border-b border-border-subtle bg-surface">
    <div class="mx-auto flex max-w-6xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
      <RouterLink :to="{ name: auth.isActive ? 'files' : 'activate' }" class="flex items-center gap-2 font-semibold">
        <span class="grid size-7 place-items-center rounded-lg bg-brand text-sm text-white">
          F
        </span>
        <span class="hidden text-strong sm:inline">Folderly</span>
      </RouterLink>

      <!-- Hidden until activation: the router would bounce the user back. -->
      <nav v-if="auth.isActive" class="flex items-center gap-1">
        <RouterLink :to="{ name: 'files' }" :class="[linkBase, $route.name === 'files' ? linkActive : linkIdle]">
          My files
        </RouterLink>
        <RouterLink :to="{ name: 'shared' }" :class="[linkBase, $route.name === 'shared' ? linkActive : linkIdle]">
          <span class="sm:hidden">Shared</span>
          <span class="hidden sm:inline">Shared with me</span>
        </RouterLink>
      </nav>

      <div class="ml-auto flex items-center gap-2">
        <RouterLink :to="{ name: 'account' }" :class="[
          linkBase,
          'hidden max-w-[32vw] truncate md:block',
          $route.name === 'account' ? linkActive : linkIdle,
        ]" :title="auth.user?.email">
          {{ auth.user?.email }}
        </RouterLink>
        <RouterLink :to="{ name: 'account' }"
          class="grid size-9 shrink-0 place-items-center rounded-lg border border-border-subtle bg-surface text-muted transition hover:bg-surface-sunken hover:text-strong active:scale-95 md:hidden"
          :class="$route.name === 'account' ? 'bg-surface-sunken text-strong' : ''" :title="auth.user?.email"
          :aria-label="`Account: ${auth.user?.email ?? ''}`">
          <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="12" cy="8" r="4" />
            <path d="M4 21a8 8 0 0 1 16 0" />
          </svg>
        </RouterLink>
        <ThemeToggle />
        <BaseButton size="sm"
          class="h-9 hover:border-red-300 hover:bg-red-50 hover:text-red-700 dark:hover:border-red-500/40 dark:hover:bg-red-500/10 dark:hover:text-red-300"
          :loading="loggingOut" @click="logout">
          Log out
        </BaseButton>
      </div>
    </div>
  </header>
</template>
