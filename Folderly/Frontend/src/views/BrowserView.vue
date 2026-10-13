<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AlertMessage from '@/components/ui/AlertMessage.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BreadcrumbBar from '@/components/BreadcrumbBar.vue'
import EntryTable from '@/components/EntryTable.vue'
import RoleBadge from '@/components/RoleBadge.vue'
import StorageBar from '@/components/StorageBar.vue'
import UploadQueuePanel from '@/components/UploadQueuePanel.vue'
import ConfirmDialog from '@/components/dialogs/ConfirmDialog.vue'
import PromptDialog from '@/components/dialogs/PromptDialog.vue'
import PreviewDialog from '@/components/dialogs/PreviewDialog.vue'
import ShareDialog from '@/components/dialogs/ShareDialog.vue'
import * as filesApi from '@/api/files'
import * as foldersApi from '@/api/folders'
import { errorMessage } from '@/api/client'
import { useUploadQueue, type QueuedFile } from '@/composables/useUploadQueue'
import { useBrowserStore } from '@/stores/browser'
import { useDiskStore } from '@/stores/disk'
import { useSpacesStore } from '@/stores/spaces'
import {
  isFileEntry,
  type FileEntry,
  type FolderEntry,
  type ShareToken,
  type SpacePath,
} from '@/types/api'
import { join, normalize, parent } from '@/utils/path'
import { readDroppedFiles, relativeDirOf } from '@/utils/dropped'
import { canAdd, canShare, type Capability } from '@/utils/roles'
import { validateFileName, validateFolderName } from '@/utils/validation'

const route = useRoute()
const router = useRouter()
const browser = useBrowserStore()
const disk = useDiskStore()
const spaces = useSpacesStore()

onMounted(() => {
  void disk.refresh()
  // Needed to turn a `share` token in the URL into a name and a role.
  void spaces.ensureLoaded()
})

/* -------------------------------- the space -------------------------------- */

const currentPath = computed<SpacePath>(() => {
  const fromQuery = route.query.path
  return typeof fromQuery === 'string' && fromQuery ? normalize(fromQuery) : '/'
})

const shareToken = computed<ShareToken>(() => {
  const fromQuery = route.query.share
  return typeof fromQuery === 'string' && fromQuery ? fromQuery : null
})

const sharedFolder = computed(() =>
  shareToken.value ? spaces.byToken(shareToken.value) : undefined,
)

const role = computed<Capability>(() => {
  if (!shareToken.value) return 'owner'
  return sharedFolder.value?.role ?? 'read'
})

const spaceLabel = computed(() => sharedFolder.value?.name ?? 'My files')

// A token that is not in the list is not (or no longer) shared with us.
const unknownShare = computed(
  () => shareToken.value !== null && spaces.loaded && !sharedFolder.value,
)

const isAtRoot = computed(() => currentPath.value === '/')

function navigate(path: SpacePath) {
  const query: Record<string, string> = { path }
  if (shareToken.value) query.share = shareToken.value
  void router.push({ name: 'files', query })
}

// The URL is the source of truth, so back/forward and a pasted link all work.
watch(
  [currentPath, shareToken],
  ([path, share]) => {
    void browser.open(path, share)
  },
  { immediate: true },
)

/* -------------------------------- actions -------------------------------- */

// Page-level error for actions with no dialog of their own (download).
// Dialog-driven actions keep their own message so it shows next to the field.
const actionError = ref<string | null>(null)
const busyName = ref<string | null>(null)

/* ------------------------------ new folder ------------------------------ */

const creating = ref(false)
const createOpen = ref(false)
const createError = ref<string | null>(null)

async function createFolder(name: string) {
  creating.value = true
  createError.value = null
  try {
    await foldersApi.createFolder(join(currentPath.value, name), shareToken.value)
    createOpen.value = false
    await browser.reload()
  } catch (caught) {
    createError.value = errorMessage(caught, 'Could not create the folder.')
  } finally {
    creating.value = false
  }
}

/* -------------------------------- uploads -------------------------------- */

const fileInput = ref<HTMLInputElement | null>(null)
const folderInput = ref<HTMLInputElement | null>(null)
const draggingOver = ref(false)

const FULL_MESSAGE = 'Storage is full. Delete some files before uploading more.'

const queue = useUploadQueue((item, onProgress) =>
  filesApi.uploadFile(item.destination, item.file, {
    share: item.share,
    onProgress,
  }),
)

queue.onDrained.value = () => {
  void browser.reload()
  // Also after failures, a refused upload is exactly when the readout matters.
  void disk.refresh()
}

function enqueue(entries: { file: File; relativeDir: string }[]) {
  if (!entries.length) return

  // Checked here as well as on the button, so a drag-and-drop gets the same
  // answer without a round trip.
  if (disk.uploadsBlocked) {
    actionError.value = FULL_MESSAGE
    return
  }

  actionError.value = null
  const queued: QueuedFile[] = entries.map(({ file, relativeDir }) => ({
    file,
    destination: relativeDir ? join(currentPath.value, relativeDir) : currentPath.value,
    share: shareToken.value,
  }))
  queue.enqueue(queued)
}

function onPicked(input: HTMLInputElement | null) {
  const files = Array.from(input?.files ?? [])
  enqueue(files.map((file) => ({ file, relativeDir: relativeDirOf(file) })))
  if (input) input.value = ''
}

async function onDrop(event: DragEvent) {
  draggingOver.value = false
  if (!canAdd(role.value)) return
  const dropped = await readDroppedFiles(event.dataTransfer)
  enqueue(dropped)
}

/* -------------------------------- rename -------------------------------- */

const renameTarget = ref<FolderEntry | null>(null)
const renaming = ref(false)
const renameError = ref<string | null>(null)

function openRename(entry: FolderEntry) {
  renameTarget.value = entry
  renameError.value = null
}

async function submitRename(name: string) {
  const entry = renameTarget.value
  if (!entry) return

  renaming.value = true
  renameError.value = null
  try {
    await (isFileEntry(entry)
      ? filesApi.renameFile(currentPath.value, entry.name, name, shareToken.value)
      : foldersApi.renameFolder(join(currentPath.value, entry.name), name, shareToken.value))
    renameTarget.value = null
    await browser.reload()
  } catch (caught) {
    renameError.value = errorMessage(caught, 'Could not rename it.')
  } finally {
    renaming.value = false
  }
}

/* -------------------------------- delete -------------------------------- */

const deleteTarget = ref<FolderEntry | null>(null)
const deleting = ref(false)
const deleteError = ref<string | null>(null)

async function confirmDelete() {
  const entry = deleteTarget.value
  if (!entry) return

  deleting.value = true
  deleteError.value = null
  try {
    await (isFileEntry(entry)
      ? filesApi.deleteFile(currentPath.value, entry.name, shareToken.value)
      : foldersApi.deleteFolder(join(currentPath.value, entry.name), shareToken.value))
    deleteTarget.value = null
    await browser.reload()
  } catch (caught) {
    deleteError.value = errorMessage(caught, 'Could not delete it.')
  } finally {
    deleting.value = false
    void disk.refresh()
  }
}

/* ------------------------------- download ------------------------------- */

async function download(name: string) {
  busyName.value = name
  actionError.value = null
  try {
    await filesApi.downloadFile(currentPath.value, name, shareToken.value)
  } catch (caught) {
    actionError.value = errorMessage(caught, 'Could not download the file.')
  } finally {
    busyName.value = null
  }
}

/* -------------------------------- preview -------------------------------- */

// Held as the entry rather than the name, the dialog needs the size and the
// extension to decide whether it can render the file at all.
const previewEntry = ref<FileEntry | null>(null)

/* --------------------------------- share --------------------------------- */

const sharePath = ref<SpacePath | null>(null)
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-wrap items-center gap-3">
      <button
        type="button"
        class="group inline-flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-muted transition hover:bg-surface-sunken hover:text-strong active:scale-95 disabled:pointer-events-none disabled:opacity-40"
        :disabled="isAtRoot"
        :title="isAtRoot ? 'This is the top of the space' : 'Go up one level'"
        @click="navigate(parent(currentPath))"
      >
        <svg
          class="size-4 transition-transform duration-150 group-hover:-translate-y-0.5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="m14 9-5-5-5 5" />
          <path d="M20 20h-7a4 4 0 0 1-4-4V4" />
        </svg>
        Up
      </button>

      <BreadcrumbBar :path="currentPath" :root-label="spaceLabel" @navigate="navigate" />

      <RoleBadge v-if="shareToken" :role="role" />

      <div class="ml-auto flex flex-wrap items-center gap-2">
        <template v-if="canAdd(role)">
          <BaseButton size="sm" @click="createOpen = true">New folder</BaseButton>
          <BaseButton
            size="sm"
            variant="primary"
            :disabled="disk.uploadsBlocked"
            @click="fileInput?.click()"
          >
            Upload files
          </BaseButton>
          <BaseButton
            size="sm"
            :disabled="disk.uploadsBlocked"
            title="Upload a folder with everything inside it"
            @click="folderInput?.click()"
          >
            Upload folder
          </BaseButton>
        </template>
        <BaseButton v-if="canShare(role)" size="sm" @click="sharePath = currentPath">
          Share
        </BaseButton>
      </div>
    </div>

    <input ref="fileInput" type="file" multiple class="hidden" @change="onPicked(fileInput)" />
    <input
      ref="folderInput"
      type="file"
      webkitdirectory
      multiple
      class="hidden"
      @change="onPicked(folderInput)"
    />

    <StorageBar :usage="disk.usage" />

    <AlertMessage v-if="unknownShare"> This folder is not shared with you any more. </AlertMessage>
    <AlertMessage v-else-if="actionError">{{ actionError }}</AlertMessage>
    <AlertMessage v-else-if="browser.error">{{ browser.error }}</AlertMessage>

    <UploadQueuePanel
      :items="queue.items.value"
      :overall-progress="queue.overallProgress.value"
      :active="queue.active.value"
      @dismiss="queue.reset"
    />

    <section
      class="overflow-hidden rounded-xl border bg-surface transition"
      :class="draggingOver ? 'border-brand bg-brand/5' : 'border-border-subtle'"
      @dragover.prevent="draggingOver = canAdd(role)"
      @dragleave.prevent="draggingOver = false"
      @drop.prevent="onDrop"
    >
      <p v-if="browser.loading" class="px-4 py-10 text-center text-sm text-muted">Loading...</p>

      <div v-else-if="browser.isEmpty && !browser.error" class="px-4 py-12 text-center">
        <p class="text-sm font-medium text-soft">This folder is empty</p>
        <p v-if="canAdd(role)" class="mt-1 text-sm text-muted">
          Drop files or a folder here, or use the buttons above.
        </p>
        <p v-else class="mt-1 text-sm text-muted">You have view-only access to this folder.</p>
      </div>

      <EntryTable
        v-else-if="!browser.error"
        :entries="browser.entries"
        :busy-name="busyName"
        :role="role"
        @open="navigate(join(currentPath, $event))"
        @preview="previewEntry = $event"
        @download="download"
        @rename="openRename"
        @remove="deleteTarget = $event"
        @share="sharePath = join(currentPath, $event)"
      />
    </section>

    <!-- dialogs -->

    <PromptDialog
      :open="createOpen"
      title="New folder"
      label="Folder name"
      hint="Letters, digits, dashes and underscores."
      confirm-label="Create"
      :submitting="creating"
      :error="createError"
      :validate="validateFolderName"
      @submit="createFolder"
      @close="createOpen = false"
    />

    <PromptDialog
      :open="renameTarget !== null"
      title="Rename"
      label="New name"
      :initial="renameTarget?.name"
      :submitting="renaming"
      :error="renameError"
      :validate="renameTarget && isFileEntry(renameTarget) ? validateFileName : validateFolderName"
      @submit="submitRename"
      @close="renameTarget = null"
    />

    <ConfirmDialog
      :open="deleteTarget !== null"
      :title="`Delete ${deleteTarget?.name}?`"
      :description="
        deleteTarget && !isFileEntry(deleteTarget)
          ? 'The folder and everything inside it will be removed. This cannot be undone.'
          : 'This file will be removed. This cannot be undone.'
      "
      confirm-label="Delete"
      :submitting="deleting"
      :error="deleteError"
      @confirm="confirmDelete"
      @close="deleteTarget = null"
    />

    <PreviewDialog
      :open="previewEntry !== null"
      :entry="previewEntry"
      :path="currentPath"
      :share="shareToken"
      @download="download"
      @close="previewEntry = null"
    />

    <ShareDialog
      v-if="sharePath !== null"
      :open="sharePath !== null"
      :path="sharePath"
      @close="sharePath = null"
    />
  </div>
</template>
