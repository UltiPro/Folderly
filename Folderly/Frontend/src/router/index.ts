import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: { name: 'files' } },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/activate',
      name: 'activate',
      component: () => import('@/views/ActivateView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/files',
      name: 'files',
      component: () => import('@/views/BrowserView.vue'),
      meta: { requiresAuth: true, requiresActive: true },
    },
    {
      path: '/shared',
      name: 'shared',
      component: () => import('@/views/SharedView.vue'),
      meta: { requiresAuth: true, requiresActive: true },
    },
    {
      path: '/account',
      name: 'account',
      component: () => import('@/views/AccountView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.guestOnly && auth.isAuthenticated) {
    return { name: auth.isActive ? 'files' : 'activate' }
  }

  if (to.meta.requiresActive && !auth.isActive) {
    return { name: 'activate' }
  }

  if (to.name === 'activate' && auth.isActive) {
    return { name: 'files' }
  }

  return true
})

export default router
