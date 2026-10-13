<script setup lang="ts">
import { computed } from 'vue'

import BaseButton from '@/components/ui/BaseButton.vue'
import FileTypeIcon from '@/components/FileTypeIcon.vue'
import { isFileEntry, type FileEntry, type FolderEntry } from '@/types/api'
import { previewKind } from '@/utils/filetypes'
import { formatSize, pluralize } from '@/utils/format'
import { canEdit, canShare, type Capability } from '@/utils/roles'

const props = defineProps<{
  entries: FolderEntry[]
  busyName?: string | null
  // What the viewer may do in this folder. Buttons follow it so nobody is
  // offered an action that would only be refused.
  role: Capability
}>()

const emit = defineEmits<{
  open: [name: string]
  preview: [entry: FileEntry]
  download: [name: string]
  rename: [entry: FolderEntry]
  remove: [entry: FolderEntry]
  share: [name: string]
}>()

const mayChange = computed(() => canEdit(props.role))
const mayShare = computed(() => canShare(props.role))

const sorted = computed(() =>
  [...props.entries].sort((a, b) => {
    if (isFileEntry(a) !== isFileEntry(b)) return isFileEntry(a) ? 1 : -1
    return a.name.localeCompare(b.name)
  }),
)

function summary(entry: FolderEntry): string {
  if (isFileEntry(entry)) return formatSize(entry.size)
  return `${pluralize(entry.folders, 'folder')}, ${pluralize(entry.files, 'file')}`
}

function canPreview(entry: FileEntry): boolean {
  return previewKind(entry.extension, entry.size) !== null
}
</script>

<template>
  <ul class="divide-y divide-border-subtle">
    <li
      v-for="entry in sorted"
      :key="`${entry.type}:${entry.name}`"
      class="group flex flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2.5 transition hover:bg-surface-sunken"
      :class="{ 'opacity-50': busyName === entry.name }"
    >
      <FileTypeIcon
        :folder="!isFileEntry(entry)"
        :extension="isFileEntry(entry) ? entry.extension : undefined"
      />

      <div class="min-w-0 flex-1">
        <button
          v-if="!isFileEntry(entry)"
          type="button"
          class="block max-w-full truncate text-left text-sm font-medium text-strong hover:text-brand hover:underline"
          @click="emit('open', entry.name)"
        >
          {{ entry.name }}
        </button>
        <button
          v-else-if="canPreview(entry)"
          type="button"
          class="block max-w-full truncate text-left text-sm font-medium text-strong hover:text-brand hover:underline"
          title="Open a preview"
          @click="emit('preview', entry)"
        >
          {{ entry.name }}
        </button>
        <span v-else class="block max-w-full truncate text-sm font-medium text-strong">
          {{ entry.name }}
        </span>
        <span class="text-xs text-muted">{{ summary(entry) }}</span>
      </div>

      <div
        class="flex w-full shrink-0 items-center justify-end gap-1 transition focus-within:opacity-100 sm:w-auto sm:opacity-0 sm:group-hover:opacity-100"
      >
        <BaseButton
          v-if="isFileEntry(entry)"
          size="sm"
          variant="ghost"
          @click="emit('download', entry.name)"
        >
          Download
        </BaseButton>
        <BaseButton
          v-else-if="mayShare"
          size="sm"
          variant="ghost"
          @click="emit('share', entry.name)"
        >
          Share
        </BaseButton>
        <template v-if="mayChange">
          <BaseButton size="sm" variant="ghost" @click="emit('rename', entry)">Rename</BaseButton>
          <BaseButton size="sm" variant="ghost" @click="emit('remove', entry)">Delete</BaseButton>
        </template>
      </div>
    </li>
  </ul>
</template>
