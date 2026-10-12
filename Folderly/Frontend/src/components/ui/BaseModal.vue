<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    open: boolean
    title: string
    description?: string
    size?: 'md' | 'lg'
  }>(),
  { size: 'md' },
)
const emit = defineEmits<{ close: [] }>()

const panel = ref<HTMLElement | null>(null)

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') emit('close')
}

/* Move focus into the dialog when it opens, so keyboard users land inside it
   instead of continuing from wherever they were on the page behind. */
watch(
  () => props.open,
  async (open) => {
    if (!open) return
    await nextTick()
    const focusable = panel.value?.querySelector<HTMLElement>(
      'input:not([type="hidden"]), textarea, select, button:not([tabindex="-1"])',
    )
    focusable?.focus()
  },
  { immediate: true },
)

onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <Transition enter-active-class="transition duration-150" enter-from-class="opacity-0"
      leave-active-class="transition duration-100" leave-to-class="opacity-0">
      <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
        @click.self="emit('close')">
        <div ref="panel" role="dialog" aria-modal="true" :aria-label="title"
          class="flex max-h-[90vh] w-full flex-col rounded-xl border border-border-subtle bg-surface p-5 shadow-xl"
          :class="size === 'lg' ? 'max-w-4xl' : 'max-w-md'">
          <h2 class="text-base font-semibold text-strong">{{ title }}</h2>
          <p v-if="description" class="mt-1 text-sm text-muted">{{ description }}</p>

          <div class="-mx-1 mt-4 min-h-0 flex-1 overflow-auto px-1">
            <slot />
          </div>

          <div v-if="$slots.actions" class="mt-5 flex justify-end gap-2">
            <slot name="actions" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
