<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import AlertMessage from '@/components/ui/AlertMessage.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import { errorMessage } from '@/api/client'
import { fetchFileBlob } from '@/api/files'
import { previewKind } from '@/utils/filetypes'
import { formatSize } from '@/utils/format'
import type { FileEntry, ShareToken, SpacePath } from '@/types/api'

/*
  Shows a file without saving it first.

  An image or a PDF becomes an object URL, which is what lets an <img> or an
  <iframe> show a file the API only hands over with an Authorization header; it
  is revoked when the dialog closes so browsing does not accumulate whole files
  in memory. Text takes the other route and becomes a string in a <pre> - no
  object URL, no iframe, so someone else's .html is shown, never run.
*/
const props = defineProps<{
  open: boolean
  entry: FileEntry | null
  path: SpacePath
  share: ShareToken
}>()
const emit = defineEmits<{ close: []; download: [name: string] }>()

const url = ref<string | null>(null)
const text = ref<string | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const kind = computed(() =>
  props.entry ? previewKind(props.entry.extension, props.entry.size) : null,
)

function release() {
  if (url.value) {
    URL.revokeObjectURL(url.value)
    url.value = null
  }
  text.value = null
}

watch(
  () => [props.open, props.entry?.name] as const,
  async ([open]) => {
    release()
    error.value = null
    if (!open || !props.entry) return

    loading.value = true
    const wanted = props.entry.name
    const wantedKind = kind.value
    try {
      const blob = await fetchFileBlob(props.path, wanted, props.share)
      // The dialog may have moved on while this was in flight.
      if (props.entry?.name !== wanted) return
      if (wantedKind === 'text') {
        // Blob.text decodes as UTF-8 with no say in it, so a Windows-1250
        // file shows replacement characters. Not guessed at: sniffing an
        // encoding fails quietly, and Download opens it in a real editor.
        text.value = await blob.text()
      } else {
        url.value = URL.createObjectURL(blob)
      }
    } catch (caught) {
      error.value = errorMessage(caught, 'Could not load this file.')
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

onBeforeUnmount(release)
</script>

<template>
  <BaseModal
    :open="open"
    size="lg"
    :title="entry?.name ?? 'Preview'"
    :description="entry ? formatSize(entry.size) : undefined"
    @close="emit('close')"
  >
    <div class="grid min-h-64 place-items-center rounded-lg bg-surface-sunken p-2">
      <p v-if="loading" class="py-16 text-sm text-muted">Loading...</p>

      <AlertMessage v-else-if="error">{{ error }}</AlertMessage>

      <img
        v-else-if="url && kind === 'image'"
        :src="url"
        :alt="entry?.name"
        class="max-h-[65vh] w-auto rounded"
      />

      <iframe
        v-else-if="url && kind === 'pdf'"
        :src="url"
        :title="entry?.name"
        class="h-[65vh] w-full rounded border-0 bg-white"
      />

      <pre
        v-else-if="text !== null && kind === 'text'"
        class="max-h-[65vh] w-full overflow-auto rounded bg-surface p-3 text-left font-mono text-xs wrap-break-word whitespace-pre-wrap text-strong"
        >{{ text }}</pre>

      <p v-else class="py-16 text-sm text-muted">This file cannot be shown here.</p>
    </div>

    <template #actions>
      <BaseButton v-if="entry" variant="primary" @click="emit('download', entry.name)">
        Download
      </BaseButton>
      <BaseButton @click="emit('close')">Close</BaseButton>
    </template>
  </BaseModal>
</template>
