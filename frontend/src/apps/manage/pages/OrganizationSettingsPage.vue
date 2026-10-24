<script setup lang="ts">
import {
  BButton,
  BFormCheckbox,
  BFormGroup,
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
import { manage } from "@/shared/legacy";
import { useNotify } from "@/shared/notify";
import OrganizationFormFields from "../components/OrganizationFormFields.vue";
import { setFlash, takeFlash } from "../flash";
import {
  emptyOrganizationForm,
  ORGANIZATION_FORM_FIELDS,
  type OrganizationFormValue,
} from "../organizationForm";

type Settings = components["schemas"]["OrganizationSettingsForm"];

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();
const notify = useNotify();

const FIELDS = [
  ...ORGANIZATION_FORM_FIELDS,
  "verification_requests.allowed",
  "verification_requests.text",
  "verification_requests.postal_codes",
];

const settings = ref<Settings | null>(null);
const loading = ref(true);
const loadError = ref<string | null>(null);
const saving = ref(false);
const saveError = ref<string | null>(null);

const form = ref<OrganizationFormValue>(emptyOrganizationForm());
const verification = reactive({ allowed: false, text: "", postal_codes: [] as string[] });
const logoPreview = ref<string | null>(null);
const errors = ref<Record<string, string>>({});
const originals = ref({ name: "", short_name: "" });

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
  form.value = {
    name: data.name,
    short_name: data.short_name,
    description: data.description ?? "",
    location: {
      street: data.location.street ?? "",
      postalCode: data.location.postalCode ?? "",
      city: data.location.city ?? "",
      state: data.location.state ?? "",
      latitude: data.location.latitude ?? null,
      longitude: data.location.longitude ?? null,
    },
    // The stored image stays on the server (`image_base64: null`); the preview shows it.
    logo: data.logo
      ? {
          image_base64: null,
          copyright_text: data.logo.copyright_text ?? null,
          license_id: data.logo.license_id ?? null,
        }
      : null,
    url: data.url ?? "",
    email: data.email ?? "",
    phone: data.phone ?? "",
    fax: data.fax ?? "",
  };
  logoPreview.value = data.logo?.image_base64 ?? null;
  if (data.verification_requests) {
    Object.assign(verification, {
      allowed: data.verification_requests.allowed,
      text: data.verification_requests.text ?? "",
      postal_codes: [...(data.verification_requests.postal_codes ?? [])],
    });
  }
  originals.value = { name: data.name, short_name: data.short_name };
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
      name: form.value.name,
      short_name: form.value.short_name,
      description: form.value.description,
      location: { ...form.value.location },
      logo: form.value.logo ? { ...form.value.logo } : null,
      url: form.value.url,
      email: form.value.email,
      phone: form.value.phone,
      fax: form.value.fax,
      verification_requests: settings.value.can_verify_other
        ? { ...verification, postal_codes: [...verification.postal_codes] }
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

        <OrganizationFormFields
          v-model="form"
          v-model:errors="errors"
          v-model:logo-preview="logoPreview"
          :licenses="settings.licenses"
          :exclude-id="organizationId"
          :original-names="originals"
        />

        <div v-if="settings.can_verify_other" class="card mb-4" data-test="verification-requests">
          <div class="card-header">{{ t("Verification requests") }}</div>
          <div class="card-body">
            <BFormGroup
              :description="t('If set, unverified organizations may ask you for verification.')"
              class="mb-3"
            >
              <BFormCheckbox id="verification-allowed" v-model="verification.allowed">
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
              <BFormTextarea id="verification-text" v-model="verification.text" rows="3" />
            </BFormGroup>
            <BFormGroup
              :label="t('Verification requests postal codes')"
              label-for="verification-postal-codes"
              :description="t('Limit verification requests to organizations with these postal codes.')"
              class="mb-3"
            >
              <BFormTags
                v-model="verification.postal_codes"
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
