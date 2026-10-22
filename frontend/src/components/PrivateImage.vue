<script setup lang="ts">
import {ref,watch,onBeforeUnmount} from 'vue';import {api} from '../services/api'
const emit=defineEmits<{loaded:[]}>();const props=defineProps<{src:string;alt?:string}>();const url=ref(''),failed=ref(false);let seq=0
watch(()=>props.src,async src=>{const current=++seq;failed.value=false;if(url.value)URL.revokeObjectURL(url.value);url.value='';if(!src)return;try{const {data}=await api.get(src,{responseType:'blob'});if(current===seq)url.value=URL.createObjectURL(data)}catch{if(current===seq)failed.value=true}},{immediate:true})
onBeforeUnmount(()=>{seq++;if(url.value)URL.revokeObjectURL(url.value)})
</script>
<template><img v-if="url" :src="url" :alt="alt||'Imagen de inspección'" loading="lazy" @load="emit('loaded')"/><div v-else class="flex min-h-24 items-center justify-center bg-slate-100 text-xs text-slate-400">{{failed?'Imagen no disponible':'Cargando imagen…'}}</div></template>
