<script setup lang="ts">
import AlertMessage from '@/components/ui/AlertMessage.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseModal from '@/components/ui/BaseModal.vue'

withDefaults(
  defineProps<{
    open: boolean
    title: string
    description?: string
    confirmLabel?: string
    danger?: boolean
    submitting?: boolean
    error?: string | null
  }>(),
  { confirmLabel: 'Confirm', danger: true, submitting: false, error: null },
)

const emit = defineEmits<{ confirm: []; close: [] }>()
</script>

<template>
  <BaseModal :open="open" :title="title" :description="description" @close="emit('close')">
    <AlertMessage v-if="error">{{ error }}</AlertMessage>

    <template #actions>
      <BaseButton :disabled="submitting" @click="emit('close')">Cancel</BaseButton>
      <BaseButton
        :variant="danger ? 'danger' : 'primary'"
        :loading="submitting"
        @click="emit('confirm')"
      >
        {{ confirmLabel }}
      </BaseButton>
    </template>
  </BaseModal>
</template>
