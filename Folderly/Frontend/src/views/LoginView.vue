<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import AlertMessage from '@/components/ui/AlertMessage.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import { errorMessage } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { validateEmail } from '@/utils/validation'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const email = ref('')
const password = ref('')
const emailError = ref<string | null>(null)
const formError = ref<string | null>(null)
const submitting = ref(false)

async function submit() {
  emailError.value = validateEmail(email.value)
  formError.value = null
  // The password rule is not enforced here: an account created before a rule
  // change must still be able to sign in.
  if (emailError.value) return

  submitting.value = true
  try {
    await auth.login(email.value, password.value)
    const redirect = route.query.redirect
    await router.push(typeof redirect === 'string' ? redirect : { name: 'files' })
  } catch (caught) {
    formError.value = errorMessage(caught, 'Could not sign in.')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-sm py-10">
    <div class="mb-6 text-center">
      <span class="mx-auto mb-3 grid size-11 place-items-center rounded-xl bg-brand text-lg font-semibold text-white">
        F
      </span>
      <h1 class="text-xl font-semibold">Sign in to Folderly</h1>
      <p class="mt-1 text-sm text-muted">Your files, wherever you are.</p>
    </div>

    <form class="flex flex-col gap-4 rounded-xl border border-border-subtle bg-surface p-5" novalidate
      @submit.prevent="submit">
      <AlertMessage v-if="formError">{{ formError }}</AlertMessage>

      <BaseInput v-model="email" label="Email" type="email" autocomplete="email" placeholder="you@example.com"
        :error="emailError" :disabled="submitting" />
      <BaseInput v-model="password" label="Password" type="password" autocomplete="current-password"
        :disabled="submitting" />

      <BaseButton type="submit" variant="primary" :loading="submitting" class="w-full">
        Sign in
      </BaseButton>
    </form>

    <p class="mt-4 text-center text-sm text-muted">
      No account yet?
      <RouterLink :to="{ name: 'register' }" class="font-medium text-brand hover:underline">
        Create one
      </RouterLink>
    </p>
  </div>
</template>
