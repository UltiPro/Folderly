<script setup lang="ts">
import { useId } from 'vue'

defineProps<{
  label: string
  type?: string
  placeholder?: string
  error?: string | null
  hint?: string
  autocomplete?: string
  required?: boolean
  disabled?: boolean
}>()

const model = defineModel<string>({ required: true })

// Ties the label and the described-by text to this instance, so several inputs
// on one page do not share ids.
const id = useId()
const describedBy = `${id}-description`
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label :for="id" class="text-sm font-medium text-soft">{{ label }}</label>
    <input :id="id" v-model="model" :type="type ?? 'text'" :placeholder="placeholder" :autocomplete="autocomplete"
      :required="required" :disabled="disabled" :aria-invalid="error ? true : undefined"
      :aria-describedby="error || hint ? describedBy : undefined"
      class="w-full rounded-lg border bg-surface px-3 py-2 text-sm text-strong transition placeholder:text-muted disabled:opacity-60"
      :class="error ? 'border-red-400 dark:border-red-500' : 'border-border-subtle'" />
    <p v-if="error" :id="describedBy" class="text-xs text-red-600 dark:text-red-400">{{ error }}</p>
    <p v-else-if="hint" :id="describedBy" class="text-xs text-muted">{{ hint }}</p>
  </div>
</template>
