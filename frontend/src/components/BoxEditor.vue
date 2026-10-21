<script setup lang="ts">
import {ref} from 'vue';import PrivateImage from './PrivateImage.vue'
export type Box={class_id:number;x:number;y:number;w:number;h:number;confidence?:number}
const props=defineProps<{src:string;boxes:Box[];width:number;height:number;readonly?:boolean}>();const emit=defineEmits<{change:[boxes:Box[]]}>();const start=ref<[number,number]|null>(null),draft=ref<Box|null>(null)
function point(e:PointerEvent):[number,number]{const r=(e.currentTarget as SVGSVGElement).getBoundingClientRect();return [Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)),Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))]}
function down(e:PointerEvent){if(props.readonly)return;(e.currentTarget as Element).setPointerCapture(e.pointerId);start.value=point(e)}
function move(e:PointerEvent){if(!start.value)return;const [x,y]=point(e),[a,b]=start.value;draft.value={class_id:0,x:(x+a)/2,y:(y+b)/2,w:Math.abs(x-a),h:Math.abs(y-b)}}
function up(){if(draft.value&&draft.value.w>0.005&&draft.value.h>0.005)emit('change',[...props.boxes,{...draft.value}]);start.value=null;draft.value=null}
</script>
<template><div class="relative mx-auto w-full overflow-hidden rounded-xl bg-slate-100" :style="{aspectRatio:width+'/'+height}"><PrivateImage :src="src" class="absolute inset-0 h-full w-full object-fill"/><svg class="absolute inset-0 h-full w-full touch-none" :class="readonly?'':'cursor-crosshair'" viewBox="0 0 1000 1000" preserveAspectRatio="none" @pointerdown="down" @pointermove="move" @pointerup="up" @pointercancel="start=null;draft=null"><g v-for="(box,i) in [...boxes,...(draft?[draft]:[])]" :key="i"><rect :x="(box.x-box.w/2)*1000" :y="(box.y-box.h/2)*1000" :width="box.w*1000" :height="box.h*1000" fill="rgba(239,68,68,.12)" stroke="#e44d40" stroke-width="2" vector-effect="non-scaling-stroke"/><text :x="(box.x-box.w/2)*1000+6" :y="(box.y-box.h/2)*1000+24" fill="#e44d40" font-size="22">{{i+1}} · roña</text></g></svg></div></template>
