<script setup lang="ts">
import { BButton, BFormCheckbox, BFormGroup, BOverlay, BSpinner } from "bootstrap-vue-next";
import { nextTick, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute } from "vue-router";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import { toFieldErrors } from "@/shared/fieldErrors";
import OrganizationFormFields from "../components/OrganizationFormFields.vue";
import {
  emptyOrganizationForm,
  ORGANIZATION_FORM_FIELDS,
  type OrganizationFormValue,
} from "../organizationForm";

type CreateForm = components["schemas"]["OrganizationCreateForm"];

const { t } = useI18n();
const route = useRoute();

const loading = ref(true);
const loadError = ref<string | null>(null);
const saving = ref(false);
const saveError = ref<string | null>(null);
const createForm = ref<CreateForm | null>(null);
const fields = ref<InstanceType<typeof OrganizationFormFields> | null>(null);

const form = ref<OrganizationFormValue>(emptyOrganizationForm());
const logoPreview = ref<string | null>(null);
const errors = ref<Record<string, string>>({});
// The verification is on by default (the organization's events are visible right away).
const relationVerify = ref(true);
const relationAutoVerify = ref(false);

async function load() {
  loading.value = true;
  const invitation = Number(route.query.invitation_id);
  const { data, error } = await api.GET("/bff/manage/organizations/create-form", {
    params: { query: { invitation_id: invitation > 0 ? invitation : undefined } },
  });
  loading.value = false;

  if (!data) {
    loadError.value = error?.message ?? t("Error");
    return;
  }

  createForm.value = data;
  form.value.name = data.name;

  if (data.name) {
    await nextTick();
    fields.value?.checkNames();
  }
}

async function scrollToFirstInvalid() {
  await nextTick();
  document.querySelector(".is-invalid, [data-test=image-error]")?.scrollIntoView({
    block: "center",
  });
}

async function save() {
  if (saving.value || !createForm.value) return;

  saving.value = true;
  saveError.value = null;
  errors.value = {};

  const { data, error } = await api.POST("/bff/manage/organizations", {
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
      invitation_id: createForm.value.invitation_id ?? null,
      relation_verify: !!createForm.value.relation?.can_verify && relationVerify.value,
      relation_auto_verify_event_reference_requests:
        !!createForm.value.relation?.can_auto_verify && relationAutoVerify.value,
    },
  });

  if (data) {
    // The server flashed the success message; both targets render it. Keep the spinner.
    location.assign(data.redirect_url);
    return;
  }

  saving.value = false;

  if (error && "errors" in error) {
    const mapped = toFieldErrors(error.errors, ORGANIZATION_FORM_FIELDS);
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
    <AppBreadcrumb :items="[{ label: t('Create organization') }]" />

    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading">
      <form v-if="createForm" data-test="create-form" @submit.prevent="save">
        <OrganizationFormFields
          ref="fields"
          v-model="form"
          v-model:errors="errors"
          v-model:logo-preview="logoPreview"
          :licenses="createForm.licenses"
          suggest-short-name
        />

        <div v-if="createForm.relation" class="card mb-4" data-test="relation">
          <div class="card-header">
            {{
              t("Relation to %(admin_unit_name)s", {
                admin_unit_name: createForm.relation.organization_name,
              })
            }}
          </div>
          <div class="card-body">
            <BFormGroup
              v-if="createForm.relation.can_verify"
              :description="t('If set, events of the new organization are publicly visible.')"
              class="mb-3"
            >
              <BFormCheckbox id="embedded_relation-verify" v-model="relationVerify">
                {{ t("Verify new organization") }}
              </BFormCheckbox>
            </BFormGroup>
            <BFormGroup
              v-if="createForm.relation.can_auto_verify"
              :description="
                t(
                  'If set, all upcoming reference requests of the new organization are verified automatically.',
                )
              "
              class="mb-3"
            >
              <BFormCheckbox
                id="embedded_relation-auto_verify_event_reference_requests"
                v-model="relationAutoVerify"
              >
                {{ t("Verify reference requests automatically") }}
              </BFormCheckbox>
            </BFormGroup>
          </div>
        </div>

        <div v-if="saveError" class="alert alert-danger" role="alert">{{ saveError }}</div>

        <BButton id="submit" type="submit" variant="primary" :disabled="saving">
          <BSpinner v-if="saving" small />
          {{ t("Create") }}
        </BButton>
      </form>
    </BOverlay>
  </div>
</template>
