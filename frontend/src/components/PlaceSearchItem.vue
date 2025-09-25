<script setup lang="ts">
import type { PhotonFeature } from "@/interfaces";
import { computed, toRefs } from "vue";

const props = defineProps<{
    feature: PhotonFeature;
    focused: boolean;
    inline: boolean;
    clickable: boolean;
}>();
const emit = defineEmits<{ (e: "click"): void }>();

const { feature, focused, inline, clickable } = toRefs(props);

const cantonAbbreviations: { [key: string]: string } = {
    Aargau: "AG",
    "Appenzell Innerrhoden": "AI",
    "Appenzell Ausserrhoden": "AR",
    Bern: "BE",
    "Basel-Landschaft": "BL",
    "Basel-Stadt": "BS",
    Fribourg: "FR",
    Genève: "GE",
    Glarus: "GL",
    Graubünden: "GR",
    Jura: "JU",
    Luzern: "LU",
    Neuchâtel: "NE",
    Nidwalden: "NW",
    Obwalden: "OW",
    "St. Gallen": "SG",
    Schaffhausen: "SH",
    Solothurn: "SO",
    Schwyz: "SZ",
    Thurgau: "TG",
    Ticino: "TI",
    Uri: "UR",
    Vaud: "VD",
    Valais: "VS",
    Zug: "ZG",
    Zürich: "ZH",
};

const classes = computed(() => (inline.value ? "q-mx-none q-px-none" : ""));

/**
 * The secondary line (caption) for the two-line display, based on the new rules.
 * e.g., "Thurgau" or "Sirnach (TG)"
 */
const secondaryLine = computed(() => {
    const { name, city, state } = props.feature.properties;

    // Rule 1: If the result IS a city (name === city), show the full canton name.
    if (name && name === city) {
        return state ?? "";
    }

    // Rule 2: If the result is WITHIN a city (name !== city), show "City (Abbr)".
    if (city) {
        const cantonAbbr = state ? cantonAbbreviations[state] : undefined;
        if (cantonAbbr) {
            return `${city} (${cantonAbbr})`;
        }
        return city; // Fallback
    }

    return ""; // No caption if there's no city context.
});

/**
 * The single-line inline representation, based on the new rules.
 * e.g., "Sirnach (TG)" or "Wasserwerk Sirnach, Sirnach (TG)"
 */
const inlineDisplay = computed(() => {
    const { name, city, state } = props.feature.properties;
    if (!name) return "Unknown Location";

    const cityLabel = city ?? "";
    const cantonAbbr = state ? cantonAbbreviations[state] : undefined;

    // Build the city part of the label, e.g., "Sirnach (TG)"
    let cityWithCanton = cityLabel;
    if (cityLabel && cantonAbbr) {
        cityWithCanton = `${cityLabel} (${cantonAbbr})`;
    }

    // Rule 1: If name and city are the same, we just need the combined version.
    if (name === city) {
        return cityWithCanton;
    }

    // Rule 2: If they are different, combine them with a comma.
    return cityWithCanton ? `${name}, ${cityWithCanton}` : name;
});
</script>

<template>
    <q-item :class="classes" :clickable="clickable" :focused="focused" @click="emit('click')">
        <q-item-section>
            <q-item-label v-if="inline">{{ inlineDisplay }}</q-item-label>
            <q-item-label v-else>{{ feature.properties.name }}</q-item-label>
            <q-item-label v-if="!inline" caption>{{ secondaryLine }}</q-item-label>
        </q-item-section>
    </q-item>
</template>

<style scoped></style>
