<script setup lang="ts">
import { Map, TileLayer, Polygon, LatLng } from 'leaflet'
import { computed, onMounted, type Ref, ref, useTemplateRef, watch } from 'vue'

import 'leaflet/dist/leaflet.css'
import { queryOptions, useQuery } from '@tanstack/vue-query'
import { QSelect } from 'quasar'
import {
  symSharpPedalBike,
  symSharpElectricBike,
  symSharpElectricCar,
  symSharpDirectionsWalk,
  symSharpElectricMoped,
} from '@quasar/extras/material-symbols-sharp'

const travelTimeMinutes = ref(10)
const abfahrtsort = ref('47.521889,9.252317')

const mapContainer = useTemplateRef<HTMLDivElement>('map')
let mymap: Ref<Map | undefined> = ref(undefined)

const addedPolygons: Polygon[] = []

const profile = ref('bike')
const profiles = [
  { label: 'Fuss', value: 'foot', icon: symSharpDirectionsWalk },
  { label: 'Velo', value: 'bike', icon: symSharpPedalBike },
  { label: 'E-Bike (25 km/h)', value: 'ebike', icon: symSharpElectricBike },
  { label: 'S-Pedelec', value: 'fast_ebike', icon: symSharpElectricMoped },
  { label: 'Auto', value: 'car', icon: symSharpElectricCar },
]

const hasMap = computed(() => !!mymap.value)

const isochroneQueryOptions = queryOptions({
  queryKey: ['isochrone', abfahrtsort, profile, travelTimeMinutes],
  enabled: hasMap,
  queryFn: () =>
    fetch(
      `http://localhost:8000/api/generate_isochrone?point=${abfahrtsort.value}&key=&profile=${profile.value}&travel_time_minutes=${travelTimeMinutes.value}`,
    ).then(
      (r) =>
        r.json() as unknown as { polygons: { geometry: { coordinates: [number, number][][] } }[] },
    ),
  select: (data) => {
    console.log('map data: ', data)
    return data['polygons'].map(
      (p) =>
        new Polygon(
          p.geometry.coordinates.map((ring) => ring.map((coord) => new LatLng(coord[1], coord[0]))),
          { color: 'red' },
        ),
    )
  },
  staleTime: Infinity,
})

const { data: polygons, isFetching: isFetchingIsochrone } = useQuery(isochroneQueryOptions)

watch(
  polygons,
  () => {
    if (polygons.value) {
      console.log('watch polygons: ', { ...polygons.value })
      addedPolygons.forEach((p) => mymap.value?.removeLayer(p))
      polygons.value?.forEach((p) => {
        const map = mymap.value
        if (map instanceof Map) {
          p.addTo(map)
          p.on('click', function () {
            map.fitBounds(p.getBounds())
          })
          addedPolygons.push(p)
          console.log('polygon added: ', p)
          if (!map.getBounds().contains(p.getBounds())) {
            map.fitBounds(p.getBounds())
          }
        }
      })
    }
  },
  { immediate: true },
)

onMounted(async () => {
  if (mapContainer.value) {
    const map = new Map('map', {
      center: [47.521889, 9.252317],
      zoom: 16,
    })

    const layer = new TileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    })
    layer.addTo(map)
    mymap.value = map
  }
})

const filter = ref('')

const placesDropdown = useTemplateRef<QSelect>('placesDropdown')
const { data: places, isFetching: isFetchingPlaces } = useQuery({
  queryKey: ['search', filter],
  enabled: hasMap,
  queryFn: async () =>
    fetch(
      `http://localhost:8000/api/search?query=${filter.value}&zoom=${mymap.value?.getZoom()}&lat=${mymap.value?.getCenter().lat}&lon=${mymap.value?.getCenter().lng}`,
    ).then((r) => r.json() as unknown as []),
  initialData: [],
})

const options = computed(() =>
  places.value.map((place) => {
    const { properties } = place
    return { label: properties['name'], value: properties['extent'] }
  }),
)

async function onFilter(
  val: string,
  doneFn: (callbackFn: () => void, afterFn?: (ref: QSelect) => void) => void,
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
    <div class="absolute" style="z-index: 999; width: 20%">
      <q-card class="row q-pa-md q-mt-md">
        <q-select
          ref="placesDropdown"
          name="Start"
          label="Abfahrtsort"
          rounded
          dense
          autocomplete="label"
          :input-debounce="100"
          :options="options"
          outlined
          :model-value="abfahrtsort"
          @filter="onFilter"
          use-input
          class="col-12"
        />

        <div class="col-12 q-mt-md rounded-borders q-px-sm">Reisezeit</div>
        <q-slider
          name="reisezeit"
          label
          :label-value="travelTimeMinutes + 'min'"
          v-model.number="travelTimeMinutes"
          switch-label-side
          class="col-12 q-mb-lg q-px-sm"
          color="orange"
          snap
          :step="10"
          :min="10"
          :max="60"
          :disable="isFetchingIsochrone"
          markers
          label-always
        >
        </q-slider>
        <q-linear-progress
          class="absolute overlay no-border-radius"
          v-if="isFetchingIsochrone || isFetchingPlaces"
          indeterminate
        />
        <div class="col-12 q-mt-md">
          <q-btn-toggle
            name="profileSelection"
            v-model="profile"
            unelevated
            class="custom-toggle-border"
            text-color="primary"
            no-caps
            spread
            dense
            :options="profiles"
            rounded
          />
        </div>
      </q-card>
    </div>
    <div id="map" ref="map" class=""></div>
  </div>
</template>

<style scoped>
#map {
  width: 100vw;
  height: 100vh;
}

.overlay {
  top: 0;
  left: 0;
}

.custom-toggle-border {
  border: 1px solid #027be3;
}
</style>
