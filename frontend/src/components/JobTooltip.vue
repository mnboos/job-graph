<script setup lang="ts">
import { DefaultApi, type JobOpeningOut } from "@/api";
import { computed, toRefs } from "vue";
import {
    symSharpOpenInBrowser,
    symSharpBattery3Bar,
    symSharpBottomPanelClose,
    symSharpNearMe,
    symSharpMenuOpen,
} from "@quasar/extras/material-symbols-sharp";
import { useQuery } from "@tanstack/vue-query";

const props = defineProps<{ job: JobOpeningOut; from_lat: number; from_lon: number; profile: string }>();

const { job, from_lat, from_lon, profile } = toRefs(props);

const addressDisplay = computed(() => `${job.value.address}, ${job.value.city}`);

const api = new DefaultApi();

const { data: distance, isFetching: isFetchingDistance } = useQuery({
    queryKey: ["routeTo", job.value.id, from_lat, from_lon, profile],
    queryFn: () =>
        api.apiCalcDistance({
            distanceCalculation: {
                jobId: job.value.id,
                abfahrtsort: { lat: from_lat.value, lon: from_lon.value },
                profile: profile.value,
            },
        }),
    initialData: 0,
});
</script>

<template>
    <q-card flat bordered class="fit">
        <q-bar dense>
            <q-item-label class="">{{ job.title }}</q-item-label>
            <q-space />
            <div class="flex">
                <q-icon :name="symSharpNearMe" class="q-my-auto" />
                <div class="q-ml-sm">
                    <q-circular-progress v-if="isFetchingDistance" indeterminate />
                    <template v-else>
                        {{ distance }}
                        km
                    </template>
                </div>
                <q-tooltip class="text-subtitle2">{{ addressDisplay }}</q-tooltip>
            </div>
        </q-bar>

        <q-card-section>
            <q-item-label caption>
                {{ job.companyName }}
            </q-item-label>
            <!--            <q-item-label caption>-->
            <!--                {{ job.address }}-->
            <!--            </q-item-label>-->
        </q-card-section>
        <q-card-section>
            <q-item-label>{{ job.description }}</q-item-label>
        </q-card-section>
    </q-card>
</template>

<style scoped></style>
