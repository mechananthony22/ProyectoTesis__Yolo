import {ref} from 'vue'
import {errorText} from './api'
export function usePage(){
 const error=ref(''),success=ref(''),busy=ref(false)
 async function act(fn:()=>Promise<unknown>,message=''){error.value='';success.value='';busy.value=true;try{await fn();success.value=message}catch(e){error.value=errorText(e)}finally{busy.value=false}}
 return {error,success,busy,act}
}
