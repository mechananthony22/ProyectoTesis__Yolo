<script setup lang="ts">defineProps<{error?:string;success?:string}>()</script>
<template><div v-if="error" role="alert" class="mb-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{{error}}</div><div v-if="success" role="status" class="mb-5 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{{success}}</div></template>
