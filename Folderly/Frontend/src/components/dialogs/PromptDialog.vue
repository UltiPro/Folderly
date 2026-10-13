<script setup lang="ts">
import { ref, watch } from 'vue'

import AlertMessage from '@/components/ui/AlertMessage.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseModal from '@/components/ui/BaseModal.vue'

const props = withDefaults(
  defineProps<{
    open: boolean
    title: string
    description?: string
    label: string
    initial?: string
    type?: string
    hint?: string
    confirmLabel?: string
    danger?: boolean
    submitting?: boolean
    error?: string | null
    validate?: (value: string) => string | null
  }>(),
  { confirmLabel: 'Save', danger: false, submitting: false, error: null },
)

const emit = defineEmits<{ submit: [value: string]; close: [] }>()

const value = ref(props.initial ?? '')
const localError = ref<string | null>(null)

watch(
  () => props.open,
  (open) => {
    if (open) {
      value.value = props.initial ?? ''
      localError.value = null
    }
  },
)

function submit() {
  localError.value = props.validate?.(value.value) ?? null
  if (!localError.value) emit('submit', value.value)
}
</script>

<template>
  <BaseModal :open="open" :title="title" :description="description" @close="emit('close')">
    <form class="flex flex-col gap-3" novalidate @submit.prevent="submit">
      <AlertMessage v-if="error">{{ error }}</AlertMessage>
      <BaseInput
        v-model="value"
        :label="label"
        :type="type"
        :hint="hint"
        :error="localError"
        :disabled="submitting"
      />
      <button type="submit" class="hidden" aria-hidden="true" tabindex="-1" />
    </form>

    <template #actions>
      <BaseButton :disabled="submitting" @click="emit('close')">Cancel</BaseButton>
      <BaseButton :variant="danger ? 'danger' : 'primary'" :loading="submitting" @click="submit">
        {{ confirmLabel }}
      </BaseButton>
    </template>
  </BaseModal>
</template>
