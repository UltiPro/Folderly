import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { errorMessage } from '@/api/client'
import * as foldersApi from '@/api/folders'
import type { SharedFolder } from '@/types/api'

export const useSpacesStore = defineStore('spaces', () => {
  const shares = ref<SharedFolder[]>([])
  const loading = ref(false)
  const loaded = ref(false)
  const error = ref<string | null>(null)

  const hasShares = computed(() => shares.value.length > 0)

  async function refresh(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      shares.value = await foldersApi.listSharedWithMe()
      loaded.value = true
    } catch (caught) {
      error.value = errorMessage(caught, 'Could not load shared folders.')
    } finally {
      loading.value = false
    }
  }

  async function ensureLoaded(): Promise<void> {
    if (!loaded.value && !loading.value) await refresh()
  }

  function byToken(token: string): SharedFolder | undefined {
    return shares.value.find((share) => share.share === token)
  }

  function clear(): void {
    shares.value = []
    loaded.value = false
    error.value = null
  }

  return { shares, loading, loaded, error, hasShares, refresh, ensureLoaded, byToken, clear }
})
