<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import AlertMessage from '@/components/ui/AlertMessage.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import BaseSelect from '@/components/ui/BaseSelect.vue'
import * as foldersApi from '@/api/folders'
import { errorMessage } from '@/api/client'
import { ROLES, type FolderMember, type Role, type SpacePath } from '@/types/api'
import { basename } from '@/utils/path'
import { roleDescription, roleLabel } from '@/utils/roles'
import { validateEmail } from '@/utils/validation'

const props = defineProps<{ open: boolean; path: SpacePath }>()
const emit = defineEmits<{ close: [] }>()

const roleOptions = ROLES.map((role) => ({ value: role, label: roleLabel(role) }))

const members = ref<FolderMember[]>([])
const loading = ref(false)
const listError = ref<string | null>(null)

const email = ref('')
const role = ref<Role>('read')
const emailError = ref<string | null>(null)
const inviteError = ref<string | null>(null)
const inviting = ref(false)
const busyEmail = ref<string | null>(null)

const chosenRoleHint = computed(() => roleDescription(role.value))

async function loadMembers() {
  loading.value = true
  listError.value = null
  try {
    members.value = await foldersApi.listMembers(props.path)
  } catch (caught) {
    members.value = []
    listError.value = errorMessage(caught, 'Could not load who has access.')
  } finally {
    loading.value = false
  }
}

watch(
  () => props.open,
  (open) => {
    if (!open) return
    email.value = ''
    role.value = 'read'
    emailError.value = null
    inviteError.value = null
    void loadMembers()
  },
  { immediate: true },
)

async function invite() {
  emailError.value = validateEmail(email.value)
  inviteError.value = null
  if (emailError.value) return

  inviting.value = true
  try {
    await foldersApi.shareFolder(props.path, email.value, role.value)
    email.value = ''
    await loadMembers()
  } catch (caught) {
    inviteError.value = errorMessage(caught, 'Could not share the folder.')
  } finally {
    inviting.value = false
  }
}

async function changeRole(member: FolderMember, next: string) {
  busyEmail.value = member.email
  inviteError.value = null
  try {
    await foldersApi.shareFolder(props.path, member.email, next as Role)
    await loadMembers()
  } catch (caught) {
    inviteError.value = errorMessage(caught, 'Could not change the role.')
    await loadMembers()
  } finally {
    busyEmail.value = null
  }
}

async function revoke(member: FolderMember) {
  busyEmail.value = member.email
  inviteError.value = null
  try {
    await foldersApi.revokeShare(props.path, member.email)
    await loadMembers()
  } catch (caught) {
    inviteError.value = errorMessage(caught, 'Could not revoke access.')
  } finally {
    busyEmail.value = null
  }
}
</script>

<template>
  <BaseModal
    :open="open"
    :title="`Share ${basename(path) || 'all my files'}`"
    description="A share covers everything inside this folder. Only you can share it - the people you add cannot pass access on."
    @close="emit('close')"
  >
    <div class="flex flex-col gap-4">
      <form class="flex flex-col gap-3" novalidate @submit.prevent="invite">
        <BaseInput
          v-model="email"
          label="Invite by email"
          type="email"
          placeholder="teammate@example.com"
          :error="emailError"
          :disabled="inviting"
        />
        <div class="flex flex-col gap-1.5">
          <div class="flex items-end gap-2">
            <BaseSelect
              v-model="role"
              label="They may"
              :options="roleOptions"
              :disabled="inviting"
              class="min-w-0 flex-1"
            />
            <BaseButton type="submit" variant="primary" :loading="inviting">Share</BaseButton>
          </div>
          <p class="text-xs text-muted">{{ chosenRoleHint }}</p>
        </div>
      </form>

      <AlertMessage v-if="inviteError">{{ inviteError }}</AlertMessage>
      <AlertMessage v-else-if="listError">{{ listError }}</AlertMessage>

      <div>
        <h3 class="mb-2 text-xs font-semibold tracking-wide text-muted uppercase">
          Who has access
        </h3>

        <p v-if="loading" class="text-sm text-muted">Loading...</p>
        <p v-else-if="!members.length" class="text-sm text-muted">
          Only you. Share it with someone to collaborate.
        </p>

        <ul v-else class="divide-y divide-border-subtle rounded-lg border border-border-subtle">
          <li
            v-for="member in members"
            :key="member.email"
            class="flex items-center gap-2 px-3 py-2"
            :class="{ 'opacity-50': busyEmail === member.email }"
          >
            <span class="min-w-0 flex-1 truncate text-sm">{{ member.email }}</span>

            <select
              :value="member.role"
              :disabled="busyEmail === member.email"
              aria-label="Role"
              class="rounded-lg border border-border-subtle bg-surface px-2 py-1 text-xs"
              @change="changeRole(member, ($event.target as HTMLSelectElement).value)"
            >
              <option v-for="option in roleOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>

            <BaseButton
              size="sm"
              variant="ghost"
              :disabled="busyEmail === member.email"
              @click="revoke(member)"
            >
              Remove
            </BaseButton>
          </li>
        </ul>
      </div>
    </div>

    <template #actions>
      <BaseButton @click="emit('close')">Done</BaseButton>
    </template>
  </BaseModal>
</template>
