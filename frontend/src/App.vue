<script setup lang="ts">
import HomeView from '@/views/HomeView.vue'
import { VueQueryDevtools } from '@tanstack/vue-query-devtools'
</script>

<template>
  <q-layout view="hhh lpr fFf" class="fit full-width">
    <q-page-container class="full-width">
      <HomeView></HomeView>
      <VueQueryDevtools />
    </q-page-container>
  </q-layout>
</template>

<style scoped>
.full-width {
  width: 100vw;
}
</style>
