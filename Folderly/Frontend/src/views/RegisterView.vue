<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import AlertMessage from '@/components/ui/AlertMessage.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import { errorMessage } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { PASSWORD_RULE, validateEmail, validatePassword } from '@/utils/validation'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const confirmation = ref('')

const emailError = ref<string | null>(null)
const passwordError = ref<string | null>(null)
const confirmationError = ref<string | null>(null)
const formError = ref<string | null>(null)
const submitting = ref(false)

function validate(): boolean {
  emailError.value = validateEmail(email.value)
  passwordError.value = validatePassword(password.value)
  confirmationError.value = confirmation.value === password.value ? null : 'Passwords do not match.'
  return !emailError.value && !passwordError.value && !confirmationError.value
}

async function submit() {
  formError.value = null
  if (!validate()) return

  submitting.value = true
  try {
    // Registering signs the user straight in, and the new account is inactive.
    await auth.register(email.value, password.value)
    await router.push({ name: 'activate' })
  } catch (caught) {
    formError.value = errorMessage(caught, 'Could not create the account.')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-sm py-10">
    <div class="mb-6 text-center">
      <span
        class="mx-auto mb-3 grid size-11 place-items-center rounded-xl bg-brand text-lg font-semibold text-white"
      >
        F
      </span>
      <h1 class="text-xl font-semibold">Create your account</h1>
      <p class="mt-1 text-sm text-muted">
        You will need an activation code from whoever runs this instance before you can store files.
      </p>
    </div>

    <form
      class="flex flex-col gap-4 rounded-xl border border-border-subtle bg-surface p-5"
      novalidate
      @submit.prevent="submit"
    >
      <AlertMessage v-if="formError">{{ formError }}</AlertMessage>

      <BaseInput
        v-model="email"
        label="Email"
        type="email"
        autocomplete="email"
        placeholder="you@example.com"
        :error="emailError"
        :disabled="submitting"
      />
      <BaseInput
        v-model="password"
        label="Password"
        type="password"
        autocomplete="new-password"
        :error="passwordError"
        :hint="PASSWORD_RULE"
        :disabled="submitting"
      />
      <BaseInput
        v-model="confirmation"
        label="Confirm password"
        type="password"
        autocomplete="new-password"
        :error="confirmationError"
        :disabled="submitting"
      />

      <BaseButton type="submit" variant="primary" :loading="submitting" class="w-full">
        Create account
      </BaseButton>
    </form>

    <p class="mt-4 text-center text-sm text-muted">
      Already have an account?
      <RouterLink :to="{ name: 'login' }" class="font-medium text-brand hover:underline">
        Sign in
      </RouterLink>
    </p>
  </div>
</template>
