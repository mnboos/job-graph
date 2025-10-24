<script setup lang="ts">
import { Map as LeafletMap, TileLayer, Polygon, LatLng, LayerGroup, Marker } from "leaflet";
import {
    computed,
    onMounted,
    type Ref,
    ref,
    useTemplateRef,
    watch,
    h,
    render,
    getCurrentInstance,
    type AppContext,
    toRefs,
} from "vue";

import "leaflet/dist/leaflet.css";
import { queryOptions, useQuery } from "@tanstack/vue-query";
import JobTooltip from "@/components/JobTooltip.vue";
import { DefaultApi, type JobOpeningOut, type PlacesSearchResult } from "@/api";

const props = defineProps<{
    jobs: JobOpeningOut[];
    profile: string;
    abfahrtsort: PlacesSearchResult;
    travelTimeMinutes: number;
}>();

const { jobs, profile, abfahrtsort, travelTimeMinutes } = toRefs(props);

const emit = defineEmits<{
    (e: "ready", map: LeafletMap): void;
    (e: "fetchingIsochrone", isFetching: boolean): void;
}>();

function zoomTo(place: PlacesSearchResult) {
    console.log("zoom to: ", place);
    if (mymap.value) {
        mymap.value.flyTo(new LatLng(place.geometry.coordinates[1] ?? 0, place.geometry.coordinates[0] ?? 0));
    }
}

watch(abfahrtsort, (ortNeu, ortAlt) => {
    if (ortNeu !== ortAlt) {
        zoomTo(ortNeu);
    }
});

const mapContainer = useTemplateRef<HTMLDivElement>("map");
const mymap: Ref<LeafletMap | undefined> = ref(undefined);
let appContext: AppContext | undefined = undefined;

watch(mymap, map => {
    if (map) {
        emit("ready", map);
    }
});

const hasMap = computed(() => !!mymap.value);
const isochroneLayerGroup = new LayerGroup();
const jobsLayerGroup = new LayerGroup();

const api = new DefaultApi();

const isochroneQueryOptions = queryOptions({
    queryKey: ["isochrone", abfahrtsort, profile, travelTimeMinutes],
    enabled: hasMap,
    queryFn: () =>
        api.apiGenerateIsochrone({
            lat: abfahrtsort.value.geometry.coordinates[1] ?? 0,
            lon: abfahrtsort.value.geometry.coordinates[0] ?? 0,
            profile: profile.value,
            travelTimeMinutes: travelTimeMinutes.value,
        }),
    select: isochrone => {
        return isochrone.polygons.map(
            p =>
                new Polygon(
                    p.rings.map(ring => ring.map(coord => new LatLng(coord[1] ?? 0, coord[0] ?? 0))),
                    { color: "red" },
                ),
        );
    },
    staleTime: Infinity,
});

const { data: polygons, isFetching: isFetchingIsochrone } = useQuery(isochroneQueryOptions);

watch(isFetchingIsochrone, fetching => emit("fetchingIsochrone", fetching));

watch(jobs, newJobs => {
    jobsLayerGroup.clearLayers();
    newJobs.forEach((job: JobOpeningOut) => {
        if (job.location?.length) {
            const popupContainerId = `$job-${job.id}`;
            const lat = job.location[1] ?? 0;
            const lon = job.location[0] ?? 0;

            new Marker(new LatLng(lat, lon))
                .addTo(jobsLayerGroup)
                .bindTooltip(() => job.title + "<br>" + job.companyName)
                .bindPopup(() => `<div id="${popupContainerId}" class="fit" style="min-width: 33vw"></div>`, {
                    className: "quasar-popup", // This is our custom class hook
                })
                .on("popupopen", () => {
                    const vnode = h(
                        JobTooltip, // type
                        {
                            job: job,
                            startLocation: abfahrtsort.value.geometry.coordinates,
                            profile: profile.value,
                        },
                        [],
                    );
                    if (appContext) {
                        vnode.appContext = appContext;
                    }
                    const popupContainer = document.getElementById(popupContainerId);
                    if (popupContainer) {
                        render(vnode, popupContainer);
                    }
                })
                .on("popupclose", () => {
                    const popupContainer = document.getElementById(popupContainerId);
                    if (popupContainer) {
                        render(null, popupContainer);
                    }
                });
        }
    });
});

watch(
    polygons,
    newPolygons => {
        if (polygons.value) {
            isochroneLayerGroup.clearLayers();
            newPolygons?.forEach(p => {
                p.addTo(isochroneLayerGroup).on("click", () => {
                    mymap.value?.fitBounds(p.getBounds());
                });
                if (!mymap.value?.getBounds().contains(p.getBounds())) {
                    mymap.value?.fitBounds(p.getBounds());
                }
            });
        }
    },
    { immediate: true },
);

onMounted(() => {
    const instance = getCurrentInstance();
    appContext = instance?.appContext;

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
        isochroneLayerGroup.addTo(map);
        jobsLayerGroup.addTo(map);
        mymap.value = map;
    }
});

defineExpose({
    mymap,
    isFetchingIsochrone,
});
</script>

<template>
    <div class="fit flex justify-center">
        <slot name="search"></slot>
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

<!--suppress CssUnusedSymbol -->
<style>
.quasar-popup .leaflet-popup-content-wrapper {
    background: none;
    box-shadow: none;
    border-radius: 0;
    padding: 0;
}

.quasar-popup .leaflet-popup-content {
    margin: 0;
}

.quasar-popup .leaflet-popup-close-button {
    top: 5px;
    right: 5px;
    color: white;
    background-color: rgba(0, 0, 0, 0.5);
    border-radius: 50%;
    width: 24px;
    height: 24px;
    line-height: 24px;
    text-align: center;
    display: none;
}

.quasar-popup .leaflet-popup-close-button:hover {
    background-color: rgba(0, 0, 0, 0.7);
    display: none;
}
</style>
