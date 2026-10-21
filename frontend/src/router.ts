import {createRouter,createWebHistory} from 'vue-router'
import {useAuth} from './stores/auth'
const router=createRouter({history:createWebHistory(),routes:[
 {path:'/login',component:()=>import('./views/Login.vue'),meta:{title:'Bienvenido'}},
 {path:'/',component:()=>import('./views/Dashboard.vue'),meta:{title:'Vista general'}},
 {path:'/datasets',component:()=>import('./views/Datasets.vue'),meta:{title:'Mis datasets'}},
 {path:'/datasets/:id',component:()=>import('./views/DatasetDetail.vue'),meta:{title:'Explorador del dataset'}},
 {path:'/images/:id',component:()=>import('./views/Annotation.vue'),meta:{title:'Revisión de anotaciones'}},
 {path:'/preprocessing',component:()=>import('./views/Preprocessing.vue'),meta:{title:'Laboratorio de imágenes'}},
 {path:'/training',component:()=>import('./views/Training.vue'),meta:{title:'Entrenamiento'}},
 {path:'/models',component:()=>import('./views/Models.vue'),meta:{title:'Modelos de inteligencia artificial'}},
 {path:'/detection',component:()=>import('./views/Detection.vue'),meta:{title:'Nueva inspección'}},
 {path:'/inspections',component:()=>import('./views/Inspections.vue'),meta:{title:'Historial de inspecciones'}},
 {path:'/inspections/:id',component:()=>import('./views/InspectionDetail.vue'),meta:{title:'Detalle de inspección'}},
 {path:'/evaluations',component:()=>import('./views/Evaluations.vue'),meta:{title:'Evaluación experimental'}},
 {path:'/reports',component:()=>import('./views/Reports.vue'),meta:{title:'Reportes y evidencias'}},
 {path:'/jobs',component:()=>import('./views/Jobs.vue'),meta:{title:'Trabajos en segundo plano'}},
 {path:'/settings',component:()=>import('./views/Settings.vue'),meta:{title:'Configuración'}},
 {path:'/:pathMatch(.*)*',redirect:'/'}
]})
router.beforeEach(to=>{const auth=useAuth();if(!auth.user&&to.path!='/login')return '/login';if(auth.user&&to.path==='/login')return '/'})
export default router
