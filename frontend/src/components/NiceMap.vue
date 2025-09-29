<script setup lang="ts">
import { Map as LeafletMap, TileLayer, Polygon, LatLng } from "leaflet";
import { computed, onMounted, type Ref, ref, toValue, useTemplateRef, watch } from "vue";

import "leaflet/dist/leaflet.css";
import { queryOptions, useQuery } from "@tanstack/vue-query";
import { QSelect } from "quasar";
import {
    symSharpPedalBike,
    symSharpElectricBike,
    symSharpElectricCar,
    symSharpDirectionsWalk,
    symSharpElectricMoped,
} from "@quasar/extras/material-symbols-sharp";
import PlaceSearchItem from "@/components/PlaceSearchItem.vue";
import { DefaultApi, type PlacesSearchResult } from "@/api";

const travelTimeMinutes = ref(10);
const abfahrtsort = ref<PlacesSearchResult>({
    properties: { name: "Zihlschlacht" },
    geometry: { type: "Point", coordinates: [47.521889, 9.252317] },
    showCanton: false,
});

const mapContainer = useTemplateRef<HTMLDivElement>("map");
const mymap: Ref<LeafletMap | undefined> = ref(undefined);

const addedPolygons: Polygon[] = [];

const profile = ref("bike");
const profiles = [
    { label: "Fuss", value: "foot", icon: symSharpDirectionsWalk },
    { label: "Velo", value: "bike", icon: symSharpPedalBike },
    { label: "E-Bike", value: "ebike", icon: symSharpElectricBike },
    { label: "Mofa", value: "fast_ebike", icon: symSharpElectricMoped },
    { label: "Auto", value: "car", icon: symSharpElectricCar },
];

const hasMap = computed(() => !!mymap.value);
const filter = ref("");

const api = new DefaultApi();

const isochroneQueryOptions = queryOptions({
    queryKey: ["isochrone", abfahrtsort, profile, travelTimeMinutes],
    enabled: hasMap,
    queryFn: () =>
        api.apiGenerateIsochrone({
            lat: abfahrtsort.value.geometry.coordinates[0],
            lon: abfahrtsort.value.geometry.coordinates[1],
            profile: profile.value,
            travelTimeMinutes: travelTimeMinutes.value,
        }),
    select: isochrone => {
        return isochrone.polygons.map(
            p =>
                new Polygon(
                    p.rings.map(ring => ring.map(coord => new LatLng(coord[1], coord[0]))),
                    { color: "red" },
                ),
        );
    },
    staleTime: Infinity,
});

const placesDropdown = useTemplateRef<QSelect>("placesDropdown");
const { data: features, isFetching: isFetchingPlaces } = useQuery({
    queryKey: ["search", filter],
    enabled: hasMap,
    // queryFn: async () =>
    //     fetch(
    //         `http://localhost:8000/api/search?query=${filter.value}&zoom=${mymap.value?.getZoom()}&lat=${mymap.value?.getCenter().lat}&lon=${mymap.value?.getCenter().lng}`,
    //     ).then(r => r.json() as unknown as PhotonFeature[]),
    queryFn: () =>
        api.apiSearch({
            query: filter.value,
            zoom: mymap.value?.getZoom() ?? 16,
            lat: mymap.value?.getCenter().lat ?? 0,
            lon: mymap.value?.getCenter().lng ?? 0,
        }),
    initialData: [],
});

const { data: polygons, isFetching: isFetchingIsochrone } = useQuery(isochroneQueryOptions);

const isochroneLoaded = computed(() => !!polygons.value?.length);
const { data: jobs } = useQuery({
    queryKey: ["jobs", abfahrtsort, profile, travelTimeMinutes],
    queryFn: () =>
        api.apiJobs({
            lat: abfahrtsort.value.geometry.coordinates[0],
            lon: abfahrtsort.value.geometry.coordinates[1],
            profile: profile.value,
            travelTimeMinutes: travelTimeMinutes.value,
        }),
    enabled: isochroneLoaded,
    initialData: [],
});

watch(jobs, () => console.log("jobs: ", jobs));

watch(
    polygons,
    () => {
        if (polygons.value) {
            console.log("watch polygons: ", { ...polygons.value });
            addedPolygons.forEach(p => mymap.value?.removeLayer(p));
            polygons.value?.forEach(p => {
                const map = mymap.value;
                if (map instanceof LeafletMap) {
                    p.addTo(map);
                    p.on("click", function () {
                        map.fitBounds(p.getBounds());
                    });
                    addedPolygons.push(p);
                    console.log("polygon added: ", p);
                    if (!map.getBounds().contains(p.getBounds())) {
                        // map.fitBounds(p.getBounds());
                    }
                }
            });
        }
    },
    { immediate: true },
);

/**
 * A computed property that takes the raw `features` from useQuery and processes them.
 * It determines for each feature whether its canton should be displayed to resolve ambiguity.
 * This automatically re-runs whenever the `features` data changes.
 */
const processedFeatures = computed(() => {
    const currentFeatures = features.value;
    if (!currentFeatures || currentFeatures.length === 0) {
        return [];
    }

    // Step 1: Group all features by their city name.
    const cityGroups = new Map<string, PlacesSearchResult[]>();
    for (const feature of currentFeatures) {
        const cityName = feature.properties.city || feature.properties.name;
        if (!cityName) continue;

        if (!cityGroups.has(cityName)) {
            cityGroups.set(cityName, []);
        }
        cityGroups.get(cityName)!.push(feature);
    }

    // Step 2: Identify which city names are ambiguous (appear in multiple cantons).
    const ambiguousCityNames = new Set<string>();
    for (const [cityName, featuresInGroup] of cityGroups.entries()) {
        const cantonsInGroup = new Set(featuresInGroup.map(f => f.properties.state));
        if (cantonsInGroup.size > 1) {
            ambiguousCityNames.add(cityName);
        }
    }

    // Step 3: Map the original features list to a new list that includes the `showCanton` flag.
    return currentFeatures.map(feature => {
        const cityName = feature.properties.city || feature.properties.name;
        return {
            feature: feature,
            showCanton: !!cityName && ambiguousCityNames.has(cityName), // todo: refactor: move to backend
        };
    });
});

async function onFilter(val: string, doneFn: (callbackFn: () => void, afterFn?: (ref: QSelect) => void) => void) {
    if (!val.length && abfahrtsort.value) {
        console.log("ort: ", toValue(abfahrtsort));
        val = abfahrtsort.value?.properties.name ?? "foobar";
    }
    doneFn(
        async () => {
            filter.value = val;
        },
        ref => {
            if (val !== "" && !!ref.options?.length && ref.getOptionIndex() === -1) {
                ref.moveOptionSelection(1, true); // focus the first selectable option and do not update the input-value
                // ref.toggleOption(ref.options[ref.getOptionIndex()], true) // toggle the focused option
            }
        },
    );
}

function onKeydown(e: KeyboardEvent) {
    console.log("on keydown: ", e);
    if (e.key === "Backspace") {
        if (filter.value.length) {
            filter.value = filter.value.slice(0, -1);
            console.log("new filter: ", filter.value);
        }
    }
}

function selectAbfahrtsort(ort: PlacesSearchResult) {
    abfahrtsort.value = ort;
    filter.value = "";
    placesDropdown.value?.updateInputValue("", true);
}

onMounted(async () => {
    if (mapContainer.value) {
        const map = new LeafletMap("map", {
            center: [47.521889, 9.252317],
            zoom: 16,
        });

        const layer = new TileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        });
        layer.addTo(map);
        mymap.value = map;
    }
});
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
                    autocomplete="name"
                    options-selected-class="text-accent"
                    :input-debounce="100"
                    type="search"
                    :options="processedFeatures"
                    outlined
                    v-model="abfahrtsort"
                    @filter="onFilter"
                    use-input
                    class="col-12"
                    @keydown="onKeydown"
                >
                    <template #loading></template>
                    <template #selected-item="props">
                        <PlaceSearchItem
                            v-if="props.opt && props.opt.feature"
                            :feature="props.opt.feature"
                            :show-canton="false"
                            :focused="false"
                            inline
                            :clickable="false"
                        />
                    </template>
                    <template #option="props">
                        <PlaceSearchItem
                            :feature="props.opt.feature"
                            :show-canton="props.opt.showCanton"
                            :focused="props.focused"
                            @click="selectAbfahrtsort(props.opt)"
                            :inline="false"
                            clickable
                        />
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
                ></q-slider>
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
