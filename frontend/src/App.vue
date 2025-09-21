<script setup lang="ts">
import HomeView from '@/views/HomeView.vue'
</script>

<template>
    <q-layout view="hhh lpr fFf" class="fit full-width">
      <q-page-container class="full-width">
        <HomeView></HomeView>
      </q-page-container>
  </q-layout>
</template>

<style scoped>
.full-width {
  width: 100vw;
}
</style>
