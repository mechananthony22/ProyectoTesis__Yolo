import axios from 'axios'
export const api = axios.create({baseURL: import.meta.env.VITE_API_URL || '/api/v1/',timeout:120000})
let access = ''
let refresh = ''
let refreshing: Promise<string> | null = null
export function setTokens(a:string,r:string) { access=a; refresh=r }
export function clearTokens() { access=''; refresh='' }
export function refreshToken() { return refresh }
api.interceptors.request.use(config=>{ if(access) config.headers.Authorization=`Bearer ${access}`; return config })
api.interceptors.response.use(r=>r,async error=>{
 const original=error.config
 if(error.response?.status===401 && refresh && original && !original._retried && !original.url?.startsWith('auth/')) {
  original._retried=true
  try {
   refreshing ||= axios.post(api.defaults.baseURL+'auth/refresh/',{refresh}).then(({data})=>{setTokens(data.access,data.refresh||refresh);return data.access}).finally(()=>{refreshing=null})
   await refreshing; return api(original)
  } catch { clearTokens(); window.dispatchEvent(new Event('session-expired')) }
 }
 return Promise.reject(error)
})
export function errorText(error:unknown):string {
 if(axios.isAxiosError(error)) {
  const data=error.response?.data
  if(data) return typeof data==='string' ? data.slice(0,200) : Object.entries(data).map(([key,value])=>`${key==='detail'?'':key+': '}${typeof value==='object'?JSON.stringify(value):value}`).join(' · ')
  return 'No se pudo conectar con el servidor. Verifica que Django esté ejecutándose.'
 }
 return error instanceof Error ? error.message : 'No se pudo completar la operación.'
}
export async function download(url:string,filename:string) {
 const {data}=await api.get(url,{responseType:'blob'}); const href=URL.createObjectURL(data); const a=document.createElement('a'); a.href=href;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(href),1000)
}
export async function allPages(url:string) {
 const items:any[]=[]; let next:string|null=url
 while(next) { const {data}: {data:any}=await api.get(next); if(Array.isArray(data)) return data; items.push(...data.results); next=data.next }
 return items
}
export const labels:Record<string,string>={pending:'Pendiente',healthy:'Sin lesiones anotadas',lesion:'Con roña',discarded:'Descartada',queued:'En cola',running:'En proceso',succeeded:'Completado',failed:'Fallido',confirmed:'Confirmada',corrected:'Corregida'}
export const fmtDate=(v:string)=>new Date(v).toLocaleString('es-PE',{dateStyle:'medium',timeStyle:'short'})
