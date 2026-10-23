<script setup lang="ts">
import { onBeforeUnmount, ref } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";

interface Suggestion {
  gmaps_id: string;
  text: string;
  main_text?: string | null;
}

const props = withDefaults(
  defineProps<{
    distances: { value: number; label: string }[];
    /** Which BFF area serves the place lookups: planning (session) or anonymous visitors. */
    scope?: "public" | "manage";
  }>(),
  { scope: "manage" },
);
const coordinate = defineModel<string>("coordinate", { default: "" });
const name = defineModel<string>("name", { default: "" });
const distance = defineModel<number | null>("distance", { default: null });

const { t } = useI18n();
const suggestions = ref<Suggestion[]>([]);
const active = ref(-1);
const searched = ref(false);
const failed = ref(false);
let timer: ReturnType<typeof setTimeout> | undefined;

const DEBOUNCE_MS = 250;
const canLocate = "geolocation" in navigator;

function onInput(event: Event) {
  const keyword = (event.target as HTMLInputElement).value;
  name.value = keyword;
  // Typing invalidates a picked place.
  coordinate.value = "";
  clearTimeout(timer);
  active.value = -1;

  if (!keyword.trim()) {
    suggestions.value = [];
    searched.value = false;
    return;
  }
  timer = setTimeout(() => search(keyword.trim()), DEBOUNCE_MS);
}

async function search(keyword: string) {
  const query = { params: { query: { keyword } } };
  const { data } =
    props.scope === "public"
      ? await api.GET("/bff/public/places", query)
      : await api.GET("/bff/manage/places", query);
  suggestions.value = data?.items ?? [];
  searched.value = true;
}

async function pick(suggestion: Suggestion) {
  suggestions.value = [];
  searched.value = false;
  failed.value = false;
  const path = { params: { path: { gmaps_id: suggestion.gmaps_id } } };
  const { data } =
    props.scope === "public"
      ? await api.GET("/bff/public/places/{gmaps_id}/coordinate", path)
      : await api.GET("/bff/manage/places/{gmaps_id}/coordinate", path);
  if (!data) {
    failed.value = true;
    return;
  }
  name.value = suggestion.text;
  coordinate.value = `${data.latitude},${data.longitude}`;
}

function clear() {
  clearTimeout(timer);
  suggestions.value = [];
  searched.value = false;
  name.value = "";
  coordinate.value = "";
  distance.value = null;
}

function locate() {
  navigator.geolocation.getCurrentPosition((position) => {
    name.value = t("Current location");
    coordinate.value = `${position.coords.latitude},${position.coords.longitude}`;
    suggestions.value = [];
  });
}

function onKeydown(event: KeyboardEvent) {
  if (!suggestions.value.length) return;
  if (event.key === "ArrowDown") {
    event.preventDefault();
    active.value = (active.value + 1) % suggestions.value.length;
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    active.value = (active.value - 1 + suggestions.value.length) % suggestions.value.length;
  } else if (event.key === "Enter" && active.value >= 0) {
    event.preventDefault();
    pick(suggestions.value[active.value]);
  } else if (event.key === "Escape") {
    event.stopPropagation();
    suggestions.value = [];
  }
}

onBeforeUnmount(() => clearTimeout(timer));
</script>

<template>
  <div class="location-filter">
    <div class="position-relative">
      <div class="input-group">
        <input
          :value="name"
          type="text"
          class="form-control"
          :placeholder="t('Location')"
          :aria-label="t('Location')"
          autocomplete="off"
          @input="onInput"
          @keydown="onKeydown"
        />
        <button
          v-if="canLocate"
          type="button"
          class="btn btn-outline-secondary"
          :title="t('Current location')"
          data-test="locate"
          @click="locate"
        >
          <i class="fa fa-location-arrow"></i>
        </button>
        <button
          v-if="name"
          type="button"
          class="btn btn-outline-secondary"
          :title="t('Reset')"
          data-test="clear"
          @click="clear"
        >
          <i class="fa fa-times"></i>
        </button>
      </div>
      <div
        v-if="suggestions.length"
        class="list-group position-absolute w-100 shadow"
        style="z-index: 1060"
        role="listbox"
      >
        <button
          v-for="(suggestion, index) in suggestions"
          :key="suggestion.gmaps_id"
          type="button"
          class="list-group-item list-group-item-action"
          :class="{ active: index === active }"
          role="option"
          data-test="suggestion"
          @click="pick(suggestion)"
        >
          {{ suggestion.text }}
        </button>
      </div>
      <div v-else-if="searched" class="form-text" data-test="no-results">
        {{ t("No results") }}
      </div>
      <div v-if="failed" class="form-text text-danger">{{ t("Error") }}</div>
    </div>
    <select
      v-model="distance"
      class="form-select mt-2"
      :aria-label="t('Distance')"
      :disabled="!coordinate"
    >
      <option :value="null">{{ t("Distance") }}</option>
      <option v-for="d in distances" :key="d.value" :value="d.value">{{ d.label }}</option>
    </select>
  </div>
</template>
