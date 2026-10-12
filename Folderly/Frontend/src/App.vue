<script setup lang="ts">
import { RouterView } from 'vue-router'

import AppNav from '@/components/AppNav.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <div class="min-h-screen bg-surface-sunken text-strong">
    <AppNav v-if="auth.isAuthenticated" />
    <main class="mx-auto max-w-6xl px-4 py-6">
      <RouterView />
    </main>
  </div>
</template>
