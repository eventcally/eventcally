<script setup lang="ts">
import { BButton, BFormGroup, BFormInput, BFormTextarea, BOverlay, BSpinner } from "bootstrap-vue-next";
import { computed, nextTick, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import { toFieldErrors } from "@/shared/fieldErrors";
import ImageField, { type ImageValue } from "@/shared/ImageField.vue";
import { manage } from "@/shared/legacy";
import LocationFields, { type LocationValue } from "@/shared/LocationFields.vue";
import PlaceLookup from "@/shared/PlaceLookup.vue";

type PlaceForm = components["schemas"]["EventPlaceForm"];

const props = defineProps<{ organizationId: number; id?: number }>();

const { t } = useI18n();

const FIELDS = [
  "name",
  "url",
  "description",
  "location.street",
  "location.postalCode",
  "location.city",
  "location.state",
  "location.latitude",
  "location.longitude",
  "photo.image_base64",
  "photo.copyright_text",
  "photo.license_id",
];
const CHECK_DELAY_MS = 300;

const loading = ref(true);
const loadError = ref<string | null>(null);
const saving = ref(false);
const saveError = ref<string | null>(null);
const placeForm = ref<PlaceForm | null>(null);

const name = ref("");
const url = ref("");
const description = ref("");
const placeLocation = ref<LocationValue>(emptyLocation());
const photo = ref<ImageValue | null>(null);
const photoPreview = ref<string | null>(null);
const errors = ref<Record<string, string>>({});
const originalName = ref("");
// Live availability of the name: the message when taken, "" when free, `null` unchecked.
const nameTaken = ref<string | null>(null);
let checkTimer: ReturnType<typeof setTimeout> | undefined;

const isUpdate = computed(() => props.id !== undefined);
const title = computed(() =>
  t(isUpdate.value ? "Update %(model_display_name)s" : "Create %(model_display_name)s", {
    model_display_name: t("Place"),
  }),
);
const nameState = computed(() => {
  if (errors.value.name || nameTaken.value) return false;
  return name.value.trim() && nameTaken.value === "" ? true : null;
});

function emptyLocation(): LocationValue {
  return { street: "", postalCode: "", city: "", state: "", latitude: null, longitude: null };
}

function fieldErrors(prefix: string): Record<string, string | undefined> {
  const result: Record<string, string | undefined> = {};
  for (const [key, message] of Object.entries(errors.value)) {
    if (key.startsWith(`${prefix}.`)) result[key.slice(prefix.length + 1)] = message;
  }
  return result;
}

async function load() {
  loading.value = true;
  const { data, error } = isUpdate.value
    ? await api.GET("/bff/manage/organizations/{id}/event-places/{place_id}", {
        params: { path: { id: props.organizationId, place_id: props.id! } },
      })
    : await api.GET("/bff/manage/organizations/{id}/event-places/create-form", {
        params: { path: { id: props.organizationId } },
      });
  loading.value = false;

  if (!data) {
    loadError.value = error?.message ?? t("Error");
    return;
  }

  placeForm.value = data;
  name.value = data.name;
  originalName.value = data.name;
  url.value = data.url ?? "";
  description.value = data.description ?? "";
  placeLocation.value = {
    street: data.location.street ?? "",
    postalCode: data.location.postalCode ?? "",
    city: data.location.city ?? "",
    state: data.location.state ?? "",
    latitude: data.location.latitude ?? null,
    longitude: data.location.longitude ?? null,
  };
  // The stored image stays on the server (`image_base64: null`); the preview shows it.
  photo.value = data.photo
    ? {
        image_base64: null,
        copyright_text: data.photo.copyright_text ?? null,
        license_id: data.photo.license_id ?? null,
      }
    : null;
  photoPreview.value = data.photo?.image_base64 ?? null;
}

function checkName() {
  clearTimeout(checkTimer);
  const value = name.value.trim();
  const rest = { ...errors.value };
  delete rest.name;
  errors.value = rest;
  nameTaken.value = null;

  if (!value || value === originalName.value) return;

  checkTimer = setTimeout(async () => {
    const { data } = await api.GET("/bff/manage/organizations/{id}/event-places/name-availability", {
      params: {
        path: { id: props.organizationId },
        query: { name: value, exclude_id: props.id },
      },
    });
    // The field changed while the request was in flight.
    if (!data || name.value.trim() !== value) return;
    nameTaken.value = data.name_taken ? t("A place already exists with this name.") : "";
  }, CHECK_DELAY_MS);
}

function onPicked(place: { address: LocationValue; main_text: string | null }) {
  placeLocation.value = place.address;
  // Picking a place always overwrites the name.
  if (place.main_text) {
    name.value = place.main_text;
    checkName();
  }
}

async function scrollToFirstInvalid() {
  await nextTick();
  document.querySelector(".is-invalid, [data-test=image-error]")?.scrollIntoView({
    block: "center",
  });
}

async function save() {
  if (saving.value || !placeForm.value) return;

  saving.value = true;
  saveError.value = null;
  errors.value = {};

  const body = {
    name: name.value,
    url: url.value,
    description: description.value,
    location: { ...placeLocation.value },
    photo: photo.value ? { ...photo.value } : null,
  };
  const path = { id: props.organizationId };
  const { data, error } = isUpdate.value
    ? await api.PUT("/bff/manage/organizations/{id}/event-places/{place_id}", {
        params: { path: { ...path, place_id: props.id! } },
        body,
      })
    : await api.POST("/bff/manage/organizations/{id}/event-places", {
        params: { path },
        body,
      });

  if (data) {
    // The server flashed the success message; the list renders it. Keep the spinner.
    location.assign(data.redirect_url);
    return;
  }

  saving.value = false;

  if (error && "errors" in error) {
    const mapped = toFieldErrors(error.errors, FIELDS);
    errors.value = mapped.byKey;
    if (mapped.unmatched.length) saveError.value = mapped.unmatched.join(" ");
    await scrollToFirstInvalid();
  } else {
    saveError.value = error?.message ?? t("Error");
  }
}

onMounted(load);
</script>

<template>
  <div>
    <AppBreadcrumb
      :items="[{ label: t('Places'), href: manage.eventPlaces(organizationId) }, { label: title }]"
    />

    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading">
      <form v-if="placeForm" data-test="place-form" @submit.prevent="save">
        <PlaceLookup @picked="onPicked" />

        <BFormGroup
          :label="`${t('Name')} *`"
          label-for="name"
          :state="nameState"
          :invalid-feedback="errors.name ?? nameTaken ?? undefined"
          class="mb-3"
        >
          <BFormInput
            id="name"
            v-model="name"
            required
            maxlength="255"
            autocomplete="off"
            :state="nameState"
            @update:model-value="checkName"
          />
        </BFormGroup>

        <div class="card mb-4">
          <div class="card-header">{{ t("Location") }}</div>
          <div class="card-body">
            <LocationFields
              v-model="placeLocation"
              :errors="fieldErrors('location')"
              :lookup="false"
              :required="false"
            />
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header">{{ t("Photo") }}</div>
          <div class="card-body">
            <ImageField
              v-model="photo"
              v-model:preview="photoPreview"
              :licenses="placeForm.licenses"
              :errors="fieldErrors('photo')"
            />
          </div>
        </div>

        <BFormGroup
          :label="t('Link URL')"
          label-for="url"
          :state="errors.url ? false : null"
          :invalid-feedback="errors.url"
          class="mb-3"
        >
          <BFormInput
            id="url"
            v-model="url"
            type="url"
            maxlength="255"
            :state="errors.url ? false : null"
          />
        </BFormGroup>

        <BFormGroup :label="t('Description')" label-for="description" class="mb-3">
          <BFormTextarea id="description" v-model="description" rows="2" />
        </BFormGroup>

        <div v-if="saveError" class="alert alert-danger" role="alert">{{ saveError }}</div>

        <BButton id="submit" type="submit" variant="primary" :disabled="saving">
          <BSpinner v-if="saving" small />
          {{ isUpdate ? t("Update place") : t("Create place") }}
        </BButton>
      </form>
    </BOverlay>
  </div>
</template>
