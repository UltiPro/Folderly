import { createApp } from 'vue'
import { createPinia } from 'pinia'

import './assets/main.css'
import App from './App.vue'
import router from './router'
import { setSessionExpiredHandler } from './api/client'
// Side-effect import: writes data-theme on <html> before the first paint.
import './composables/useTheme'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
app.use(createPinia())

const auth = useAuthStore()

// So an expired refresh token lands on login, not on failing requests.
setSessionExpiredHandler(() => {
  auth.forget()
  router.push({ name: 'login' })
})

// Before mounting, so the guard sees real auth state and login does not flash.
auth.restore().finally(() => {
  app.use(router)
  app.mount('#app')
})
