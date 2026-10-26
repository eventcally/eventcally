<script setup lang="ts">
import { BButton, BFormGroup, BFormInput, BOverlay, BSpinner } from "bootstrap-vue-next";
import { computed, nextTick, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import { toFieldErrors } from "@/shared/fieldErrors";
import ImageField, { type ImageValue } from "@/shared/ImageField.vue";
import { manage } from "@/shared/legacy";
import LocationFields, { type LocationValue } from "@/shared/LocationFields.vue";

type OrganizerForm = components["schemas"]["EventOrganizerForm"];

const props = defineProps<{ organizationId: number; id?: number }>();

const { t } = useI18n();

const FIELDS = [
  "name",
  "url",
  "email",
  "phone",
  "fax",
  "location.street",
  "location.postalCode",
  "location.city",
  "location.state",
  "location.latitude",
  "location.longitude",
  "logo.image_base64",
  "logo.copyright_text",
  "logo.license_id",
];
const CHECK_DELAY_MS = 300;

const loading = ref(true);
const loadError = ref<string | null>(null);
const saving = ref(false);
const saveError = ref<string | null>(null);
const organizerForm = ref<OrganizerForm | null>(null);

const name = ref("");
const url = ref("");
const email = ref("");
const phone = ref("");
const fax = ref("");
const organizerLocation = ref<LocationValue>(emptyLocation());
const logo = ref<ImageValue | null>(null);
const logoPreview = ref<string | null>(null);
const errors = ref<Record<string, string>>({});
const originalName = ref("");
// Live availability of the name: the message when taken, "" when free, `null` unchecked.
const nameTaken = ref<string | null>(null);
let checkTimer: ReturnType<typeof setTimeout> | undefined;

const isUpdate = computed(() => props.id !== undefined);
const title = computed(() =>
  t(isUpdate.value ? "Update %(model_display_name)s" : "Create %(model_display_name)s", {
    model_display_name: t("Event organizer"),
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
    ? await api.GET("/bff/manage/organizations/{id}/event-organizers/{organizer_id}", {
        params: { path: { id: props.organizationId, organizer_id: props.id! } },
      })
    : await api.GET("/bff/manage/organizations/{id}/event-organizers/create-form", {
        params: { path: { id: props.organizationId } },
      });
  loading.value = false;

  if (!data) {
    loadError.value = error?.message ?? t("Error");
    return;
  }

  organizerForm.value = data;
  name.value = data.name;
  originalName.value = data.name;
  url.value = data.url ?? "";
  email.value = data.email ?? "";
  phone.value = data.phone ?? "";
  fax.value = data.fax ?? "";
  organizerLocation.value = {
    street: data.location.street ?? "",
    postalCode: data.location.postalCode ?? "",
    city: data.location.city ?? "",
    state: data.location.state ?? "",
    latitude: data.location.latitude ?? null,
    longitude: data.location.longitude ?? null,
  };
  // The stored image stays on the server (`image_base64: null`); the preview shows it.
  logo.value = data.logo
    ? {
        image_base64: null,
        copyright_text: data.logo.copyright_text ?? null,
        license_id: data.logo.license_id ?? null,
      }
    : null;
  logoPreview.value = data.logo?.image_base64 ?? null;
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
    const { data } = await api.GET("/bff/manage/organizations/{id}/event-organizers/name-availability", {
      params: {
        path: { id: props.organizationId },
        query: { name: value, exclude_id: props.id },
      },
    });
    // The field changed while the request was in flight.
    if (!data || name.value.trim() !== value) return;
    nameTaken.value = data.name_taken ? t("An organizer already exists with this name.") : "";
  }, CHECK_DELAY_MS);
}

async function scrollToFirstInvalid() {
  await nextTick();
  document.querySelector(".is-invalid, [data-test=image-error]")?.scrollIntoView({
    block: "center",
  });
}

async function save() {
  if (saving.value || !organizerForm.value) return;

  saving.value = true;
  saveError.value = null;
  errors.value = {};

  const body = {
    name: name.value,
    url: url.value,
    email: email.value,
    phone: phone.value,
    fax: fax.value,
    location: { ...organizerLocation.value },
    logo: logo.value ? { ...logo.value } : null,
  };
  const path = { id: props.organizationId };
  const { data, error } = isUpdate.value
    ? await api.PUT("/bff/manage/organizations/{id}/event-organizers/{organizer_id}", {
        params: { path: { ...path, organizer_id: props.id! } },
        body,
      })
    : await api.POST("/bff/manage/organizations/{id}/event-organizers", {
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
      :items="[{ label: t('Event organizers'), href: manage.eventOrganizers(organizationId) }, { label: title }]"
    />

    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading">
      <form v-if="organizerForm" data-test="organizer-form" @submit.prevent="save">
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
              v-model="organizerLocation"
              :errors="fieldErrors('location')"
              :required="false"
            />
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header">{{ t("Logo") }}</div>
          <div class="card-body">
            <ImageField
              v-model="logo"
              v-model:preview="logoPreview"
              :licenses="organizerForm.licenses"
              :errors="fieldErrors('logo')"
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

        <BFormGroup
          :label="t('Email')"
          label-for="email"
          :state="errors.email ? false : null"
          :invalid-feedback="errors.email"
          class="mb-3"
        >
          <BFormInput
            id="email"
            v-model="email"
            type="email"
            maxlength="255"
            :state="errors.email ? false : null"
          />
        </BFormGroup>

        <BFormGroup
          :label="t('Phone')"
          label-for="phone"
          :state="errors.phone ? false : null"
          :invalid-feedback="errors.phone"
          class="mb-3"
        >
          <BFormInput
            id="phone"
            v-model="phone"
            type="tel"
            maxlength="255"
            :state="errors.phone ? false : null"
          />
        </BFormGroup>

        <BFormGroup
          :label="t('Fax')"
          label-for="fax"
          :state="errors.fax ? false : null"
          :invalid-feedback="errors.fax"
          class="mb-3"
        >
          <BFormInput
            id="fax"
            v-model="fax"
            type="tel"
            maxlength="255"
            :state="errors.fax ? false : null"
          />
        </BFormGroup>

        <div v-if="saveError" class="alert alert-danger" role="alert">{{ saveError }}</div>

        <BButton id="submit" type="submit" variant="primary" :disabled="saving">
          <BSpinner v-if="saving" small />
          {{ isUpdate ? t("Update organizer") : t("Create organizer") }}
        </BButton>
      </form>
    </BOverlay>
  </div>
</template>
