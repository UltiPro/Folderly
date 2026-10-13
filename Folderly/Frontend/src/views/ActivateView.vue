<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import AlertMessage from '@/components/ui/AlertMessage.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import { errorMessage } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

// Without this screen the only symptom was every request coming back 403.
const auth = useAuthStore()
const router = useRouter()

const code = ref('')
const fieldError = ref<string | null>(null)
const formError = ref<string | null>(null)
const submitting = ref(false)

async function submit() {
  // Only checked for emptiness: formatting is normalised server-side.
  fieldError.value = code.value.trim() ? null : 'Enter the code you were given.'
  formError.value = null
  if (fieldError.value) return

  submitting.value = true
  try {
    await auth.activate(code.value)
    await router.push({ name: 'files' })
  } catch (caught) {
    formError.value = errorMessage(caught, 'Could not activate the account.')
  } finally {
    submitting.value = false
  }
}

const loggingOut = ref(false)

async function logout() {
  loggingOut.value = true
  try {
    await auth.logout()
    await router.push({ name: 'login' })
  } finally {
    loggingOut.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-md py-10">
    <div class="mb-6 text-center">
      <span
        class="mx-auto mb-3 grid size-11 place-items-center rounded-xl bg-brand text-lg font-semibold text-white"
      >
        F
      </span>
      <h1 class="text-xl font-semibold">One more step</h1>
      <p class="mt-1 text-sm text-muted">
        Your account exists, but it needs an activation code before you can store anything.
      </p>
    </div>

    <form
      class="flex flex-col gap-4 rounded-xl border border-border-subtle bg-surface p-5"
      novalidate
      @submit.prevent="submit"
    >
      <AlertMessage v-if="formError">{{ formError }}</AlertMessage>

      <BaseInput
        v-model="code"
        label="Activation code"
        placeholder="K7M2-PX94-TB3H-QR8F"
        autocomplete="off"
        hint="Case, dashes and spaces do not matter."
        :error="fieldError"
        :disabled="submitting"
      />

      <BaseButton type="submit" variant="primary" :loading="submitting" class="w-full">
        Activate
      </BaseButton>
    </form>

    <div
      class="mt-4 rounded-xl border border-border-subtle bg-surface-sunken p-4 text-sm text-muted"
    >
      <p class="font-medium text-soft">Where does a code come from?</p>
      <p class="mt-1">
        Whoever runs this instance generates them, and each one works once. Ask them for yours -
        they will see your email address in their own list once you have used it.
      </p>
    </div>

    <p class="mt-4 text-center text-sm text-muted">
      Signed in as {{ auth.user?.email }} ·
      <button
        type="button"
        class="font-medium text-brand hover:underline disabled:opacity-60"
        :disabled="loggingOut"
        @click="logout"
      >
        Log out
      </button>
    </p>
  </div>
</template>
