<script setup lang="ts">
import {
  BButton,
  BFormCheckbox,
  BFormGroup,
  BFormInput,
  BFormTags,
  BFormTextarea,
  BOverlay,
  BSpinner,
} from "bootstrap-vue-next";
import { nextTick, onMounted, reactive, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import { toFieldErrors } from "@/shared/fieldErrors";
import ImageField, { type ImageValue } from "@/shared/ImageField.vue";
import LocationFields, { type LocationValue } from "@/shared/LocationFields.vue";
import { manage } from "@/shared/legacy";
import { useNotify } from "@/shared/notify";
import { setFlash, takeFlash } from "../flash";

type Settings = components["schemas"]["OrganizationSettingsForm"];

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();
const notify = useNotify();

const FIELDS = [
  "name",
  "short_name",
  "description",
  "location.street",
  "location.postalCode",
  "location.city",
  "location.state",
  "location.latitude",
  "location.longitude",
  "logo.image_base64",
  "logo.copyright_text",
  "logo.license_id",
  "url",
  "email",
  "phone",
  "fax",
  "verification_requests.allowed",
  "verification_requests.text",
  "verification_requests.postal_codes",
];

const settings = ref<Settings | null>(null);
const loading = ref(true);
const loadError = ref<string | null>(null);
const saving = ref(false);
const saveError = ref<string | null>(null);

const form = reactive({
  name: "",
  short_name: "",
  description: "",
  location: { street: "", postalCode: "", city: "", state: "", latitude: null, longitude: null } as LocationValue,
  logo: null as ImageValue | null,
  url: "",
  email: "",
  phone: "",
  fax: "",
  verification: { allowed: false, text: "", postal_codes: [] as string[] },
});
const logoPreview = ref<string | null>(null);
const errors = ref<Record<string, string>>({});

// Live availability of the name fields (`null`: not checked).
const taken = reactive<{ name: string | null; short_name: string | null }>({
  name: null,
  short_name: null,
});
let originals = { name: "", short_name: "" };
const checkTimers: Partial<Record<"name" | "short_name", ReturnType<typeof setTimeout>>> = {};
const CHECK_DELAY_MS = 300;

const SHORT_NAME_PATTERN = /^\w+$/;

function fieldErrors(prefix: string): Record<string, string | undefined> {
  const result: Record<string, string | undefined> = {};
  for (const [key, message] of Object.entries(errors.value)) {
    if (key.startsWith(`${prefix}.`)) result[key.slice(prefix.length + 1)] = message;
  }
  return result;
}

function nameState(field: "name" | "short_name"): boolean | null {
  if (errors.value[field] || taken[field]) return false;
  const value = form[field].trim();
  if (value && value === originals[field]) return null;
  return value && taken[field] === "" ? true : null;
}

function nameMessage(field: "name" | "short_name") {
  return errors.value[field] ?? taken[field] ?? undefined;
}

function checkName(field: "name" | "short_name") {
  clearTimeout(checkTimers[field]);
  const value = form[field].trim();
  delete errors.value[field];
  taken[field] = null;

  const valid =
    field === "name" ? value.length >= 5 : value.length >= 5 && SHORT_NAME_PATTERN.test(value);
  if (!valid || value === originals[field]) return;

  checkTimers[field] = setTimeout(async () => {
    const { data } = await api.GET("/bff/manage/organizations/{id}/settings/name-availability", {
      params: { path: { id: props.organizationId }, query: { [field]: value } },
    });
    // The field changed while the request was in flight.
    if (!data || form[field].trim() !== value) return;
    const isTaken = field === "name" ? data.name_taken : data.short_name_taken;
    taken[field] = isTaken
      ? field === "name"
        ? t("Name is already taken")
        : t("Short name is already taken")
      : "";
  }, CHECK_DELAY_MS);
}

async function load() {
  loading.value = true;
  const { data, error } = await api.GET("/bff/manage/organizations/{id}/settings", {
    params: { path: { id: props.organizationId } },
  });
  loading.value = false;

  if (!data) {
    loadError.value = error?.message ?? t("Error");
    return;
  }

  settings.value = data;
  form.name = data.name;
  form.short_name = data.short_name;
  form.description = data.description ?? "";
  form.location = {
    street: data.location.street ?? "",
    postalCode: data.location.postalCode ?? "",
    city: data.location.city ?? "",
    state: data.location.state ?? "",
    latitude: data.location.latitude ?? null,
    longitude: data.location.longitude ?? null,
  };
  // The stored image stays on the server (`image_base64: null`); the preview shows it.
  logoPreview.value = data.logo?.image_base64 ?? null;
  form.logo = data.logo
    ? {
        image_base64: null,
        copyright_text: data.logo.copyright_text ?? null,
        license_id: data.logo.license_id ?? null,
      }
    : null;
  form.url = data.url ?? "";
  form.email = data.email ?? "";
  form.phone = data.phone ?? "";
  form.fax = data.fax ?? "";
  if (data.verification_requests) {
    form.verification = {
      allowed: data.verification_requests.allowed,
      text: data.verification_requests.text ?? "",
      postal_codes: [...(data.verification_requests.postal_codes ?? [])],
    };
  }
  originals = { name: data.name, short_name: data.short_name };
}

async function scrollToFirstInvalid() {
  await nextTick();
  document.querySelector(".is-invalid, [data-test=image-error]")?.scrollIntoView({
    block: "center",
  });
}

async function save() {
  if (saving.value || !settings.value) return;

  saving.value = true;
  saveError.value = null;
  errors.value = {};

  const { response, error } = await api.PUT("/bff/manage/organizations/{id}/settings", {
    params: { path: { id: props.organizationId } },
    body: {
      name: form.name,
      short_name: form.short_name,
      description: form.description,
      location: { ...form.location },
      logo: form.logo ? { ...form.logo } : null,
      url: form.url,
      email: form.email,
      phone: form.phone,
      fax: form.fax,
      verification_requests: settings.value.can_verify_other
        ? { ...form.verification, postal_codes: [...form.verification.postal_codes] }
        : null,
    },
  });
  saving.value = false;

  if (!error && response.ok) {
    // The navbar shows the organization name: reload for fresh data and show the message after.
    setFlash(t("Organization successfully updated"));
    location.reload();
    return;
  }

  if (error && "errors" in error) {
    const mapped = toFieldErrors(error.errors, FIELDS);
    errors.value = mapped.byKey;
    if (mapped.unmatched.length) saveError.value = mapped.unmatched.join(" ");
    await scrollToFirstInvalid();
  } else {
    saveError.value = error?.message ?? t("Error");
  }
}

onMounted(() => {
  const message = takeFlash();
  if (message) notify.success(message);
  load();
});
</script>

<template>
  <div>
    <AppBreadcrumb :items="[{ label: t('Settings') }]" />

    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading">
      <form v-if="settings" data-test="settings-form" @submit.prevent="save">
        <div v-if="settings.deletion_requested_at" class="alert alert-danger" role="alert">
          {{ t("The organization is scheduled for deletion.") }}
          <a class="alert-link" :href="manage.cancelDeletion(organizationId)">{{
            t("Cancel deletion")
          }}</a>
        </div>

        <BFormGroup
          :label="`${t('Name of organization')} *`"
          label-for="name"
          :description="t('The full name of the organization')"
          :state="nameState('name')"
          :invalid-feedback="nameMessage('name')"
          class="mb-3"
        >
          <BFormInput
            id="name"
            v-model="form.name"
            required
            minlength="5"
            maxlength="255"
            autocomplete="off"
            :state="nameState('name')"
            @update:model-value="checkName('name')"
          />
        </BFormGroup>

        <BFormGroup
          :label="`${t('Short name for organization')} *`"
          label-for="short_name"
          :description="t('The short name is used to create a unique identifier for your events')"
          :state="nameState('short_name')"
          :invalid-feedback="nameMessage('short_name')"
          class="mb-3"
        >
          <BFormInput
            id="short_name"
            v-model="form.short_name"
            required
            minlength="5"
            maxlength="100"
            pattern="\w+"
            :title="t('Short name must contain only letters numbers or underscore')"
            autocomplete="off"
            :state="nameState('short_name')"
            @update:model-value="checkName('short_name')"
          />
        </BFormGroup>

        <BFormGroup
          :label="t('Description')"
          label-for="description"
          :description="t('Describe the organization in a few words')"
          class="mb-3"
        >
          <BFormTextarea id="description" v-model="form.description" rows="2" />
        </BFormGroup>

        <div class="card mb-4">
          <div class="card-header">{{ t("Location") }}</div>
          <div class="card-body">
            <LocationFields v-model="form.location" :errors="fieldErrors('location')" />
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header">{{ t("Logo") }}</div>
          <div class="card-body">
            <ImageField
              v-model="form.logo"
              v-model:preview="logoPreview"
              :licenses="settings.licenses"
              :errors="fieldErrors('logo')"
            />
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header">{{ t("Additional information") }}</div>
          <div class="card-body">
            <BFormGroup :label="t('Link URL')" label-for="additional_information-url" class="mb-3"
              :state="errors.url ? false : null" :invalid-feedback="errors.url">
              <BFormInput id="additional_information-url" v-model="form.url" type="url" maxlength="255"
                :state="errors.url ? false : null" />
            </BFormGroup>
            <BFormGroup :label="t('Email')" label-for="additional_information-email" class="mb-3"
              :state="errors.email ? false : null" :invalid-feedback="errors.email">
              <BFormInput id="additional_information-email" v-model="form.email" type="email" maxlength="255"
                :state="errors.email ? false : null" />
            </BFormGroup>
            <BFormGroup :label="t('Phone')" label-for="additional_information-phone" class="mb-3"
              :state="errors.phone ? false : null" :invalid-feedback="errors.phone">
              <BFormInput id="additional_information-phone" v-model="form.phone" type="tel" maxlength="255"
                :state="errors.phone ? false : null" />
            </BFormGroup>
            <BFormGroup :label="t('Fax')" label-for="additional_information-fax" class="mb-3"
              :state="errors.fax ? false : null" :invalid-feedback="errors.fax">
              <BFormInput id="additional_information-fax" v-model="form.fax" type="tel" maxlength="255"
                :state="errors.fax ? false : null" />
            </BFormGroup>
          </div>
        </div>

        <div v-if="settings.can_verify_other" class="card mb-4" data-test="verification-requests">
          <div class="card-header">{{ t("Verification requests") }}</div>
          <div class="card-body">
            <BFormGroup
              :description="t('If set, unverified organizations may ask you for verification.')"
              class="mb-3"
            >
              <BFormCheckbox id="verification-allowed" v-model="form.verification.allowed">
                {{ t("Allow verification requests") }}
              </BFormCheckbox>
            </BFormGroup>
            <BFormGroup
              :label="t('Verification requests information')"
              label-for="verification-text"
              :description="
                t(
                  'This text is shown to unverified organizations to help them decide whether they ask you for verification.',
                )
              "
              class="mb-3"
            >
              <BFormTextarea id="verification-text" v-model="form.verification.text" rows="3" />
            </BFormGroup>
            <BFormGroup
              :label="t('Verification requests postal codes')"
              label-for="verification-postal-codes"
              :description="t('Limit verification requests to organizations with these postal codes.')"
              class="mb-3"
            >
              <BFormTags
                v-model="form.verification.postal_codes"
                input-id="verification-postal-codes"
                class="postal-codes"
                :placeholder="t('Add postal code')"
                :duplicate-tag-text="t('Duplicate postal code(s)')"
                :invalid-tag-text="t('Invalid postal code(s)')"
                :tag-remove-label="t('Remove postal code')"
                :tag-removed-label="t('Postal code removed')"
                separator=" ,;"
                :tag-validator="(tag: string) => tag.length <= 10"
                no-outer-focus
              />
            </BFormGroup>
          </div>
        </div>

        <div v-if="saveError" class="alert alert-danger" role="alert">{{ saveError }}</div>

        <BButton id="submit" type="submit" variant="primary" :disabled="saving">
          <BSpinner v-if="saving" small />
          {{ t("Update") }}
        </BButton>

        <div v-if="!settings.deletion_requested_at" class="my-4">
          <a class="btn btn-danger" :href="manage.requestDeletion(organizationId)" data-test="delete">
            {{ t("Delete organization") }}&hellip;
          </a>
        </div>
      </form>
    </BOverlay>
  </div>
</template>

<style scoped>
/* Same height as a single-line input; the tags otherwise make the field taller. */
.postal-codes {
  padding-top: 0.25rem;
  padding-bottom: 0.25rem;
}
.postal-codes :deep(.b-form-tags-list) {
  margin-top: 0;
}
.postal-codes :deep(.b-form-tag),
.postal-codes :deep(.b-from-tags-field) {
  margin-top: 0;
  margin-bottom: 0;
}
.postal-codes :deep(.b-from-tags-field),
.postal-codes :deep(.b-from-tags-field > div),
.postal-codes :deep(.b-form-tags-input) {
  height: 24px;
  min-height: 0;
}
/* Enter, comma or space adds a tag; the button only overflows the field. */
.postal-codes :deep(.b-form-tags-button) {
  display: none;
}

/* The tag's close button is dark on the dark tag: make it white. */
.postal-codes :deep(.btn-close) {
  filter: invert(1) grayscale(100%) brightness(200%);
  opacity: 1;
}
</style>
