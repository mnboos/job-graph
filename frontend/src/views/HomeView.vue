<script setup lang="ts">
import NiceMap from '@/components/NiceMap.vue'
import { ref } from 'vue'

const travelTimeMinutes = ref(5)
</script>

<template>
  <q-page class="fit flex justify-center">
    <NiceMap />
  </q-page>
</template>
