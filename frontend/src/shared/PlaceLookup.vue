<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import AppTypeahead from "@/shared/AppTypeahead.vue";
import type { LocationValue } from "./LocationFields.vue";

const emit = defineEmits<{
  picked: [place: { address: LocationValue; main_text: string | null }];
}>();

const { t } = useI18n();
const place = ref<{ id: number; name: string } | null>(null);
const lookupError = ref<string | null>(null);
// The typeahead only knows numeric ids: remember which Google place each one stands for.
let gmapsIds: string[] = [];
let mainTexts: (string | null)[] = [];

async function fetchPlaces(keyword: string) {
  const { data } = await api.GET("/bff/manage/places", { params: { query: { keyword } } });
  gmapsIds = (data?.items ?? []).map((item) => item.gmaps_id);
  mainTexts = (data?.items ?? []).map((item) => item.main_text ?? null);
  return (data?.items ?? []).map((item, index) => ({ id: index, name: item.text }));
}

async function onPick(option: { id: number; name: string } | null) {
  place.value = option;
  if (!option) return;

  lookupError.value = null;
  const { data } = await api.GET("/bff/manage/places/{gmaps_id}/address", {
    params: { path: { gmaps_id: gmapsIds[option.id] } },
  });
  if (!data) {
    lookupError.value = t("Error");
    return;
  }
  emit("picked", { address: { ...data }, main_text: mainTexts[option.id] });
}
</script>

<template>
  <div data-test="place-lookup">
    <div class="google-place d-flex mb-3">
      <span class="input-group-text rounded-end-0"><i class="fab fa-google"></i></span>
      <div class="flex-grow-1">
        <AppTypeahead
          :model-value="place"
          :fetch="fetchPlaces"
          :placeholder="t('Search location on Google')"
          input-id="location-google_place"
          @update:model-value="onPick"
        />
      </div>
    </div>
    <div v-if="lookupError" class="text-danger small mb-2">{{ lookupError }}</div>
  </div>
</template>

<style scoped>
/* Join the Google icon and the typeahead input like one input group. */
.google-place :deep(.form-control) {
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
  border-left: 0;
}
</style>
