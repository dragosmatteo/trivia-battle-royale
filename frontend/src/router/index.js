import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/RegisterView.vue'),
  },
  // Professor routes
  {
    path: '/professor',
    name: 'ProfessorDashboard',
    component: () => import('../views/professor/DashboardView.vue'),
    meta: { requiresAuth: true, role: 'professor' },
  },
  {
    path: '/professor/course/:id',
    name: 'CourseDetail',
    component: () => import('../views/professor/CourseDetailView.vue'),
    meta: { requiresAuth: true, role: 'professor' },
  },
  {
    path: '/professor/game/:pin',
    name: 'GameControl',
    component: () => import('../views/professor/GameControlView.vue'),
    meta: { requiresAuth: true, role: 'professor' },
  },
  // Student routes
  {
    path: '/student',
    name: 'StudentDashboard',
    component: () => import('../views/student/DashboardView.vue'),
    meta: { requiresAuth: true, role: 'student' },
  },
  {
    path: '/join',
    name: 'JoinGame',
    component: () => import('../views/student/JoinGameView.vue'),
  },
  {
    path: '/play/:pin',
    name: 'GamePlay',
    component: () => import('../views/student/GamePlayView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || 'null')

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.meta.role && user?.role !== to.meta.role) {
    next(user?.role === 'professor' ? '/professor' : '/student')
  } else {
    next()
  }
})

export default router
