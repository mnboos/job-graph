<script setup lang="ts">
import { Map, TileLayer, Polygon, LatLng } from 'leaflet'
import { computed, onMounted, type Ref, ref, useTemplateRef, watch } from 'vue'

import 'leaflet/dist/leaflet.css'
import { useQuery } from '@tanstack/vue-query'
import { QSelect } from 'quasar'

const travelTimeMinutes = ref(5)
const abfahrtsort = ref('')

const mapContainer = useTemplateRef<HTMLDivElement>('map')
let mymap: Map | undefined = undefined

const addedPolygons: Polygon[] = []

async function loadIso() {
  if (mymap) {
    addedPolygons.forEach((p) => mymap?.removeLayer(p))
    const { polygons: features } = (await (
      await fetch(
        `http://localhost:8000/api/generate_isochrone?point=47.521889,9.252317&key=&profile=bike&travel_time_minutes=${travelTimeMinutes.value}`,
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
      const map = mymap
      if (map instanceof Map) {
        p.addTo(map)
        addedPolygons.push(p)
        console.log('polygon added: ', p)
        map.fitBounds(p.getBounds())
      }
    })
  }
}

watch(travelTimeMinutes, loadIso)

onMounted(async () => {
  if (mapContainer.value) {
    const map = new Map('map', {
      center: [47.521889, 9.252317],
      zoom: 16,
    })

    const layer = new TileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    })
    layer.addTo(map)
    mymap = map

    await loadIso()
  }
})

// const places = ref([
//   { label: 'Amriswil', value: '123,456' },
//   { label: 'Sulgen', value: '123,456' },
//   { label: 'Weinfelden', value: '123,456' },
//   { label: 'Zihlschlacht', value: '123,456' },
// ])

const filter = ref('')

const placesDropdown = useTemplateRef<QSelect>('placesDropdown')
const { data: places, isFetching } = useQuery({
  queryKey: ['search', filter],
  queryFn: () =>
    fetch(
      `http://localhost:8000/api/search?query=${filter.value}&zoom=${mymap?.getZoom()}&lat=${mymap?.getCenter().lat}&lon=${mymap?.getCenter().lng}`,
    ).then((r) => r.json() as unknown as []),
  initialData: [],
})

let callback: undefined | ((callbackFn: () => void, afterFn: (o: Ref) => void) => void)
const options = computed(() =>
  places.value.map((place) => {
    const { properties } = place
    return { label: properties['name'], value: properties['extent'] }
  }),
)

watch(options, () => {
  if (callback) {
    // const cb = callback
    // callback = undefined
    // cb()
  }
  // if (placesDropdown.value) {
  //   console.log('refreshing dropdown now!')
  //   placesDropdown.value.refresh()
  // }
})

async function onFilter(
  val: string,
  doneFn: (callbackFn: () => void, afterFn?: (ref: QSelect) => void) => void,
  abortFn: () => void,
) {
  if (filter.value !== val && val.length) {
    doneFn(async () => {
      filter.value = val
    })
  }
}
</script>

<template>
  <div class="fit flex justify-center">
    <div class="absolute row" style="z-index: 999; width: 30%">
      <q-card class="col-12 q-pa-md q-mt-md">
        <q-select
          ref="placesDropdown"
          name="Start"
          label="Abfahrtsort"
          rounded
          dense
          autocomplete=""
          :input-debounce="100"
          :options="options"
          outlined
          :model-value="abfahrtsort"
          @filter="onFilter"
          use-input
        ></q-select>

        <label>
          <div class="q-mt-md rounded-borders">Reisezeit</div>
          <q-slider
            name="reisezeit"
            label
            :label-value="travelTimeMinutes + 'min'"
            v-model.number="travelTimeMinutes"
            switch-label-side
            color="orange"
            class="col-6 offset-3 q-mb-lg"
            snap
            :step="5"
            :min="15"
            :max="45"
            markers
            label-always
        /></label>
      </q-card>
      <!--      <q-input-->
      <!--        debounce="300"-->
      <!--        rounded-->
      <!--        color="accent"-->
      <!--        outlined-->
      <!--        v-model.number="travelTimeMinutes"-->
      <!--        name="travelTimeMinutes"-->
      <!--        type="number"-->
      <!--        label="Reisezeit in Minuten"-->
      <!--        class="q-mt-lg col-6 offset-3"-->
      <!--        bg-color="white"-->
      <!--      />-->
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
