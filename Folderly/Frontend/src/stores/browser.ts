import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import * as foldersApi from '@/api/folders'
import { errorMessage } from '@/api/client'
import { isFileEntry, type FolderEntry, type ShareToken, type SpacePath } from '@/types/api'
import { normalize } from '@/utils/path'

export const useBrowserStore = defineStore('browser', () => {
  const path = ref<SpacePath>('/')
  const share = ref<ShareToken>(null)
  const entries = ref<FolderEntry[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const folders = computed(() => entries.value.filter((entry) => !isFileEntry(entry)))
  const files = computed(() => entries.value.filter(isFileEntry))
  const isEmpty = computed(() => !loading.value && entries.value.length === 0)

  async function open(target: SpacePath, token: ShareToken = null): Promise<void> {
    path.value = normalize(target)
    share.value = token
    await reload()
  }

  async function reload(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      entries.value = await foldersApi.listFolder(path.value, share.value)
    } catch (caught) {
      entries.value = []
      error.value = errorMessage(caught, 'Could not open this folder.')
    } finally {
      loading.value = false
    }
  }

  function clear(): void {
    path.value = '/'
    share.value = null
    entries.value = []
    error.value = null
  }

  return {
    path,
    share,
    entries,
    loading,
    error,
    folders,
    files,
    isEmpty,
    open,
    reload,
    clear,
  }
})
