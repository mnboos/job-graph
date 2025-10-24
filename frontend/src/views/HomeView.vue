<script setup lang="ts">
import NiceMap from "@/components/NiceMap.vue";
import PlaceSearchItem from "@/components/PlaceSearchItem.vue";
import { QSelect } from "quasar";
import { computed, ref, toValue, useTemplateRef } from "vue";
import {
    symSharpDirectionsWalk,
    symSharpElectricBike,
    symSharpElectricCar,
    symSharpElectricMoped,
    symSharpPedalBike,
} from "@quasar/extras/material-symbols-sharp";
import { DefaultApi, type PlacesSearchResult } from "@/api";
import { useQuery } from "@tanstack/vue-query";

const placesDropdown = useTemplateRef<QSelect>("placesDropdown");
const filter = ref("");
const profile = ref("bike");
const travelTimeMinutes = ref(10);

const profiles = [
    { label: "Fuss", value: "foot", icon: symSharpDirectionsWalk },
    { label: "Velo", value: "bike", icon: symSharpPedalBike },
    { label: "E-Bike", value: "ebike", icon: symSharpElectricBike },
    { label: "S-Pedelec", value: "fast_ebike", icon: symSharpElectricMoped },
    { label: "Auto", value: "car", icon: symSharpElectricCar },
];

const abfahrtsort = ref<PlacesSearchResult>({
    type: "Feature",
    properties: {
        name: "Zihlschlacht-Sitterdorf",
        city: null,
        state: "Thurgau",
        countrycode: "CH",
        showCanton: false,
    },
    geometry: { type: "Point", coordinates: [9.259269150287928, 47.514206200000004] },
});

type NiceMapType = InstanceType<typeof NiceMap>;
const mapComponent = useTemplateRef<NiceMapType>("nicemap");
const leafletMap = computed(() => mapComponent.value?.mymap);
const mapReady = computed(() => !!leafletMap.value);
const api = new DefaultApi();

const { data: places, isFetching: isFetchingPlaces } = useQuery({
    queryKey: ["search", filter],
    enabled: () => mapReady.value,
    queryFn: () =>
        api.apiSearch({
            query: filter.value,
            zoom: leafletMap.value?.getZoom() ?? 16,
            lat: leafletMap.value?.getCenter().lat ?? 0,
            lon: leafletMap.value?.getCenter().lng ?? 0,
        }),
    initialData: [],
});

const { data: jobs } = useQuery({
    queryKey: ["jobs", abfahrtsort, profile, travelTimeMinutes],
    queryFn: () =>
        api.apiJobs({
            lat: abfahrtsort.value.geometry.coordinates[1] ?? 0,
            lon: abfahrtsort.value.geometry.coordinates[0] ?? 0,
            profile: profile.value,
            travelTimeMinutes: travelTimeMinutes.value,
        }),
    initialData: [],
});

function onFilter(val: string, doneFn: (callbackFn: () => void, afterFn?: (ref: QSelect) => void) => void) {
    if (!val.length) {
        console.log("ort: ", toValue(abfahrtsort));
        val = abfahrtsort.value.properties.name;
    }
    doneFn(
        () => {
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
</script>

<template>
    <q-page class="fit flex justify-center">
        <NiceMap
            :jobs="jobs"
            :profile="profile"
            ref="nicemap"
            :travel-time-minutes="travelTimeMinutes"
            :abfahrtsort="abfahrtsort"
        >
            <template #search>
                <div class="absolute" style="z-index: 999">
                    <q-card class="row q-pa-md q-mt-md">
                        <q-select
                            ref="placesDropdown"
                            v-model="abfahrtsort"
                            name="Start"
                            label="Abfahrtsort"
                            rounded
                            dense
                            hide-dropdown-icon
                            autocomplete="name"
                            options-selected-class="text-accent"
                            :input-debounce="100"
                            type="search"
                            :options="places"
                            outlined
                            use-input
                            class="col-12"
                            @filter="onFilter"
                            @keydown="onKeydown"
                        >
                            <template #loading></template>
                            <template #selected-item="props">
                                <PlaceSearchItem
                                    v-if="props.opt"
                                    :feature="props.opt"
                                    :show-canton="false"
                                    :focused="false"
                                    inline
                                    :clickable="false"
                                />
                            </template>
                            <template #option="props">
                                <PlaceSearchItem
                                    :feature="props.opt"
                                    :focused="props.focused"
                                    :inline="false"
                                    clickable
                                    @click="selectAbfahrtsort(props.opt)"
                                />
                            </template>
                        </q-select>

                        <div class="col-12 q-mt-md rounded-borders q-px-sm">Reisezeit</div>
                        <q-slider
                            v-model.number="travelTimeMinutes"
                            name="reisezeit"
                            label
                            :label-value="travelTimeMinutes + 'min'"
                            switch-label-side
                            class="col-12 q-mb-lg q-px-sm"
                            color="orange"
                            snap
                            :step="10"
                            :min="10"
                            :max="60"
                            :disable="mapComponent?.isFetchingIsochrone"
                            markers
                            label-always
                        ></q-slider>
                        <q-linear-progress
                            v-if="mapComponent?.isFetchingIsochrone || isFetchingPlaces"
                            class="absolute overlay no-border-radius"
                            indeterminate
                        />
                        <div class="col-12 q-mt-md">
                            <q-btn-toggle
                                v-model="profile"
                                name="profileSelection"
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
            </template>
        </NiceMap>
    </q-page>
</template>
