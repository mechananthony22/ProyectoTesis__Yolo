import {defineStore} from 'pinia'
import {ref} from 'vue'
import {api,setTokens,clearTokens,refreshToken} from '../services/api'
export const useAuth=defineStore('auth',()=>{
 const user=ref<any>(null)
 async function login(username:string,password:string) {const {data}=await api.post('auth/token/',{username,password});setTokens(data.access,data.refresh);try{user.value=(await api.get('users/me/')).data}catch(e){clearTokens();throw e}}
 async function logout(){try{if(refreshToken())await api.post('auth/logout/',{refresh:refreshToken()})}finally{clearTokens();user.value=null}}
 return {user,login,logout}
})
