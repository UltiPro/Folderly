<script setup lang="ts">
import { useId } from 'vue'

defineProps<{
  label: string
  options: { value: string; label: string }[]
  hint?: string
  error?: string | null
  disabled?: boolean
}>()

const model = defineModel<string>({ required: true })

const id = useId()
const describedBy = `${id}-description`
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label :for="id" class="text-sm font-medium text-soft">{{ label }}</label>
    <select :id="id" v-model="model" :disabled="disabled" :aria-describedby="error || hint ? describedBy : undefined"
      class="w-full rounded-lg border bg-surface px-3 py-2 text-sm text-strong transition disabled:opacity-60"
      :class="error ? 'border-red-400 dark:border-red-500' : 'border-border-subtle'">
      <option v-for="option in options" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
    <p v-if="error" :id="describedBy" class="text-xs text-red-600 dark:text-red-400">{{ error }}</p>
    <p v-else-if="hint" :id="describedBy" class="text-xs text-muted">{{ hint }}</p>
  </div>
</template>
