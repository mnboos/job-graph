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

type PhotonResponse = {
  name: string
  postcode?: number
  city?: string
  extent?: [number, number] | [number, number, number, number]
}

const travelTimeMinutes = ref(10)
const abfahrtsort = ref<PhotonResponse>({ name: 'Zihlschlacht', extent: [47.521889, 9.252317] })

const mapContainer = useTemplateRef<HTMLDivElement>('map')
let mymap: Ref<Map | undefined> = ref(undefined)

const addedPolygons: Polygon[] = []

const profile = ref('bike')
const profiles = [
  { label: 'Fuss', value: 'foot', icon: symSharpDirectionsWalk },
  { label: 'Velo', value: 'bike', icon: symSharpPedalBike },
  { label: 'E-Bike', value: 'ebike', icon: symSharpElectricBike },
  { label: 'Mofa', value: 'fast_ebike', icon: symSharpElectricMoped },
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
    return properties
  }),
)

async function onFilter(
  val: string,
  doneFn: (callbackFn: () => void, afterFn?: (ref: QSelect) => void) => void,
) {
  if (!val.length && abfahrtsort.value) {
    val = abfahrtsort.value.name
  }
  doneFn(
    async () => {
      filter.value = val
    },
    (ref) => {
      if (val !== '' && !!ref.options?.length && ref.getOptionIndex() === -1) {
        ref.moveOptionSelection(1, true) // focus the first selectable option and do not update the input-value
        // ref.toggleOption(ref.options[ref.getOptionIndex()], true) // toggle the focused option
      }
    },
  )
}

function onKeydown(e: KeyboardEvent) {
  console.log('on keydown: ', e)
  if (e.key === 'Backspace') {
    if (filter.value.length) {
      filter.value = filter.value.slice(0, -1)
      console.log('new filter: ', filter.value)
    }
  }
}

function getCaption(opt: PhotonResponse) {
  if (opt.postcode && opt.city) {
    return [opt.postcode, opt.city].join(', ')
  }
  return ''
}

function selectAbfahrtsort(ort: PhotonResponse) {
  abfahrtsort.value = ort
  filter.value = ''
  placesDropdown.value?.updateInputValue('', true)
}
</script>

<template>
  <div class="fit flex justify-center">
    <div class="absolute" style="z-index: 999">
      <q-card class="row q-pa-md q-mt-md">
        <q-select
          ref="placesDropdown"
          name="Start"
          label="Abfahrtsort"
          autofocus
          rounded
          dense
          hide-dropdown-icon
          option-label="name"
          option-value="extent"
          autocomplete="name"
          options-selected-class="text-accent"
          :input-debounce="100"
          type="search"
          :options="options"
          outlined
          v-model="abfahrtsort"
          @filter="onFilter"
          use-input
          class="col-12"
          @keydown="onKeydown"
        >
          <template #loading></template>
          <template #option="props">
            <q-item clickable :focused="props.focused" @click="selectAbfahrtsort(props.opt)">
              {{ props }}
              <q-item-section>
                <q-item-label>{{ props.opt.name }}</q-item-label>
                <q-item-label v-if="getCaption(props.opt)" caption>{{
                  getCaption(props.opt)
                }}</q-item-label>
              </q-item-section>
            </q-item>
          </template>
        </q-select>

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
