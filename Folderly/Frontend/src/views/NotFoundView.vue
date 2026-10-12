<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="py-20 text-center">
    <p class="text-sm font-semibold text-brand">404</p>
    <h1 class="mt-2 text-xl font-semibold">Page not found</h1>
    <p class="mt-1 text-sm text-muted">That address does not lead anywhere in Folderly.</p>
    <RouterLink :to="{ name: 'files' }"
      class="mt-5 inline-block rounded-lg bg-brand px-3.5 py-2 text-sm font-medium text-white transition hover:bg-brand-strong">
      Back to my files
    </RouterLink>
  </div>
</template>
