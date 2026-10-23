<script setup lang="ts">
import { BFormGroup, BFormInput } from "bootstrap-vue-next";
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import AppTypeahead from "@/shared/AppTypeahead.vue";

export interface LocationValue {
  street: string;
  postalCode: string;
  city: string;
  state: string;
  latitude: number | null;
  longitude: number | null;
}

defineProps<{ errors?: Record<string, string | undefined> }>();
const model = defineModel<LocationValue>({ required: true });

const { t } = useI18n();
const place = ref<{ id: number; name: string } | null>(null);
const lookupError = ref<string | null>(null);
// The typeahead only knows numeric ids: remember which Google place each one stands for.
let gmapsIds: string[] = [];

async function fetchPlaces(keyword: string) {
  const { data } = await api.GET("/bff/manage/places", { params: { query: { keyword } } });
  gmapsIds = (data?.items ?? []).map((item) => item.gmaps_id);
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
  model.value = { ...data };
}

function set<K extends keyof LocationValue>(key: K, value: LocationValue[K]) {
  model.value = { ...model.value, [key]: value };
}

function toNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}
</script>

<template>
  <div data-test="location-fields">
    <div class="input-group mb-3">
      <span class="input-group-text"><i class="fab fa-google"></i></span>
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

    <BFormGroup :label="t('Street')" label-for="location-street" class="mb-3"
      :state="errors?.street ? false : null" :invalid-feedback="errors?.street">
      <BFormInput id="location-street" :model-value="model.street" maxlength="255"
        :state="errors?.street ? false : null" @update:model-value="set('street', $event as string)" />
    </BFormGroup>
    <BFormGroup :label="t('State')" label-for="location-state" class="mb-3"
      :state="errors?.state ? false : null" :invalid-feedback="errors?.state">
      <BFormInput id="location-state" :model-value="model.state" maxlength="255"
        :state="errors?.state ? false : null" @update:model-value="set('state', $event as string)" />
    </BFormGroup>
    <BFormGroup :label="t('Latitude')" label-for="location-latitude" class="mb-3"
      :state="errors?.latitude ? false : null" :invalid-feedback="errors?.latitude">
      <BFormInput id="location-latitude" type="number" step="any" :model-value="model.latitude ?? ''"
        :state="errors?.latitude ? false : null" @update:model-value="set('latitude', toNumber($event))" />
    </BFormGroup>
    <BFormGroup :label="t('Longitude')" label-for="location-longitude" class="mb-3"
      :state="errors?.longitude ? false : null" :invalid-feedback="errors?.longitude">
      <BFormInput id="location-longitude" type="number" step="any" :model-value="model.longitude ?? ''"
        :state="errors?.longitude ? false : null" @update:model-value="set('longitude', toNumber($event))" />
    </BFormGroup>
    <BFormGroup :label="`${t('Postal code')} *`" label-for="location-postalCode" class="mb-3"
      :state="errors?.postalCode ? false : null" :invalid-feedback="errors?.postalCode">
      <BFormInput id="location-postalCode" :model-value="model.postalCode" maxlength="10" required
        :state="errors?.postalCode ? false : null" @update:model-value="set('postalCode', $event as string)" />
    </BFormGroup>
    <BFormGroup :label="`${t('City')} *`" label-for="location-city" class="mb-3"
      :state="errors?.city ? false : null" :invalid-feedback="errors?.city">
      <BFormInput id="location-city" :model-value="model.city" maxlength="255" required
        :state="errors?.city ? false : null" @update:model-value="set('city', $event as string)" />
    </BFormGroup>
  </div>
</template>
