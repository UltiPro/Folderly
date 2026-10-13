<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import AlertMessage from '@/components/ui/AlertMessage.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import PromptDialog from '@/components/dialogs/PromptDialog.vue'
import { errorMessage } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useBrowserStore } from '@/stores/browser'
import { useDiskStore } from '@/stores/disk'
import { useSpacesStore } from '@/stores/spaces'
import { PASSWORD_RULE, validateEmail, validatePassword } from '@/utils/validation'

const auth = useAuthStore()
const browser = useBrowserStore()
const disk = useDiskStore()
const spaces = useSpacesStore()
const router = useRouter()

const email = ref(auth.user?.email ?? '')
const password = ref('')
const currentPassword = ref('')
const emailError = ref<string | null>(null)
const passwordError = ref<string | null>(null)
const currentError = ref<string | null>(null)
const formError = ref<string | null>(null)
const saved = ref(false)
const saving = ref(false)

async function save() {
  emailError.value = validateEmail(email.value)
  // A new password is required even when only the address is changing.
  passwordError.value = validatePassword(password.value)
  // Not checked against the policy: an existing password may predate it.
  currentError.value = currentPassword.value ? null : 'Enter your current password.'
  formError.value = null
  saved.value = false
  if (emailError.value || passwordError.value || currentError.value) return

  saving.value = true
  try {
    // Logs out every other session of this account, this one carries on,
    // because the store keeps the fresh tokens that come back.
    await auth.updateAccount(email.value, password.value, currentPassword.value)
    password.value = ''
    currentPassword.value = ''
    saved.value = true
  } catch (caught) {
    formError.value = errorMessage(caught, 'Could not update the account.')
  } finally {
    saving.value = false
  }
}

const deleteOpen = ref(false)
const deleting = ref(false)
const deleteError = ref<string | null>(null)

async function deleteAccount(confirmPassword: string) {
  deleting.value = true
  deleteError.value = null
  try {
    await auth.deleteAccount(confirmPassword)
    browser.clear()
    spaces.clear()
    disk.clear()
    await router.push({ name: 'login' })
  } catch (caught) {
    deleteError.value = errorMessage(caught, 'Could not delete the account.')
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="mx-auto flex max-w-lg flex-col gap-6">
    <div>
      <h1 class="text-lg font-semibold">Account</h1>
      <p class="mt-1 text-sm text-muted">
        <template v-if="auth.isActive">Your account is active.</template>
        <template v-else>
          Not activated yet -
          <RouterLink :to="{ name: 'activate' }" class="font-medium text-brand hover:underline">
            enter a code
          </RouterLink>
          to start storing files.
        </template>
      </p>
    </div>

    <form
      class="flex flex-col gap-4 rounded-xl border border-border-subtle bg-surface p-5"
      novalidate
      @submit.prevent="save"
    >
      <AlertMessage v-if="formError">{{ formError }}</AlertMessage>
      <AlertMessage v-else-if="saved" tone="success">
        Account updated. Any other device signed in to this account has been logged out.
      </AlertMessage>

      <BaseInput
        v-model="email"
        label="Email"
        type="email"
        autocomplete="email"
        :error="emailError"
        :disabled="saving"
      />
      <BaseInput
        v-model="password"
        label="New password"
        type="password"
        autocomplete="new-password"
        :hint="`Required to save any change. ${PASSWORD_RULE}`"
        :error="passwordError"
        :disabled="saving"
      />
      <BaseInput
        v-model="currentPassword"
        label="Current password"
        type="password"
        autocomplete="current-password"
        hint="Confirms it is really you."
        :error="currentError"
        :disabled="saving"
      />

      <div class="flex justify-end">
        <BaseButton type="submit" variant="primary" :loading="saving">Save changes</BaseButton>
      </div>
    </form>

    <section class="rounded-xl border border-red-200 bg-surface p-5 dark:border-red-500/30">
      <h2 class="text-sm font-semibold text-red-700 dark:text-red-300">Delete account</h2>
      <p class="mt-1 text-sm text-muted">
        Removes your account, every folder you own and all the files inside them. Folders other
        people shared with you are simply unshared, not deleted.
      </p>
      <div class="mt-4 flex justify-end">
        <BaseButton variant="danger" @click="deleteOpen = true">Delete account</BaseButton>
      </div>
    </section>

    <PromptDialog
      :open="deleteOpen"
      title="Delete your account?"
      description="Your files are deleted from disk and cannot be recovered. Enter your password to confirm."
      label="Current password"
      type="password"
      confirm-label="Delete everything"
      danger
      :submitting="deleting"
      :error="deleteError"
      @submit="deleteAccount"
      @close="deleteOpen = false"
    />
  </div>
</template>
