<script setup lang="ts">
import { Map, TileLayer, Polygon, LatLng } from 'leaflet'
import { computed, onMounted, ref, useTemplateRef, watch } from 'vue'

import 'leaflet/dist/leaflet.css'

const travelTimeMinutes = ref(5)

const mapContainer = useTemplateRef<HTMLDivElement>('map')
let mymap: Map | undefined = undefined

const travelTimeSeconds = computed(() => travelTimeMinutes.value * 60)

const addedPolygons: Polygon[] = []

async function loadIso() {
  if (mymap) {
    addedPolygons.forEach((p) => mymap?.removeLayer(p))
    const { polygons: features } = (await (
      await fetch(
        `http://localhost:8989/isochrone?point=47.521889,9.252317&key=&profile=bike&time_limit=${travelTimeSeconds.value}`,
      )
    ).json()) as unknown as { polygons: { geometry: { coordinates: [number, number][][] } }[] }

    const polygons = features.map(
      (p) =>
        new Polygon(
          p.geometry.coordinates.map((ring) => ring.map((coord) => new LatLng(coord[1], coord[0]))),
          { color: 'red' },
        ),
    )
    polygons.forEach((p) => {
      if (mymap) {
        p.addTo(mymap)
        addedPolygons.push(p)
        console.log('polygon added: ', p)
        mymap.fitBounds(p.getBounds())
      }
    })
  }
}

watch(travelTimeMinutes, loadIso)

onMounted(async () => {
  if (mapContainer.value) {
    mymap = new Map(mapContainer.value, {
      center: [47.521889, 9.252317],
      zoom: 16,
    })
    const layer = new TileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    })
    layer.addTo(mymap)

    await loadIso()
  }
})
</script>

<template>
  <div class="fit flex justify-center">
    <div class="absolute row" style="z-index: 999; width: 50%">
      <q-input
        debounce="300"
        rounded
        color="accent"
        outlined
        v-model.number="travelTimeMinutes"
        name="travelTimeMinutes"
        type="number"
        label="Reisezeit in Minuten"
        class="q-mt-lg col-6 offset-3"
        bg-color="white"
      />
      <!--      <q-input-->
      <!--        debounce="300"-->
      <!--        rounded-->
      <!--        color="accent"-->
      <!--        outlined-->
      <!--        v-model.number="travelTimeMinutes"-->
      <!--        name="travelTimeMinutes"-->
      <!--        type="number"-->
      <!--        label="Reisezeit in Minuten"-->
      <!--        class="q-mt-lg col-6"-->
      <!--        bg-color="white"-->
      <!--      />-->
    </div>
    <div id="map" ref="map" class=""></div>
  </div>
</template>

<style scoped>
#map {
  width: 100vw;
  height: 100vh;
}
</style>
