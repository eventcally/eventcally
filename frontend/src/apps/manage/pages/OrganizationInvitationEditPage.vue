<script setup lang="ts">
import { BButton, BFormCheckbox, BOverlay, BSpinner } from "bootstrap-vue-next";
import { computed, nextTick, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import AuditLine from "@/shared/AuditLine.vue";
import { toFieldErrors } from "@/shared/fieldErrors";

type InvitationForm = components["schemas"]["OrganizationInvitationForm"];

const props = defineProps<{ organizationId: number; id?: number }>();

const { t } = useI18n();

const FIELDS = ["email", "admin_unit_name"];

const loading = ref(true);
const loadError = ref<string | null>(null);
const saving = ref(false);
const saveError = ref<string | null>(null);
const invitationForm = ref<InvitationForm | null>(null);

const email = ref("");
const name = ref("");
const verify = ref(false);
const autoVerify = ref(false);
const errors = ref<Record<string, string>>({});

const isUpdate = computed(() => props.id !== undefined);
const modelName = computed(() => t("Organization invitation"));
const title = computed(() =>
  t(isUpdate.value ? "Update %(model_display_name)s" : "Create %(model_display_name)s", {
    model_display_name: modelName.value,
  }),
);

async function load() {
  loading.value = true;
  const path = { id: props.organizationId };
  const { data, error } = isUpdate.value
    ? await api.GET("/bff/manage/organizations/{id}/organization-invitations/{invitation_id}", {
        params: { path: { ...path, invitation_id: props.id! } },
      })
    : await api.GET("/bff/manage/organizations/{id}/organization-invitations/create-form", {
        params: { path },
      });
  loading.value = false;

  if (!data) {
    loadError.value = error?.message ?? t("Error");
    return;
  }

  invitationForm.value = data;
  email.value = data.email;
  name.value = data.admin_unit_name;
  verify.value = data.relation_verify;
  autoVerify.value = data.relation_auto_verify_event_reference_requests;
}

async function scrollToFirstInvalid() {
  await nextTick();
  document.querySelector(".is-invalid, .invalid-feedback")?.scrollIntoView({ block: "center" });
}

async function save() {
  if (saving.value || !invitationForm.value) return;

  saving.value = true;
  saveError.value = null;
  errors.value = {};

  const path = { id: props.organizationId };
  const fields = {
    admin_unit_name: name.value,
    relation_verify: verify.value,
    relation_auto_verify_event_reference_requests: autoVerify.value,
  };
  const { data, error } = isUpdate.value
    ? await api.PUT("/bff/manage/organizations/{id}/organization-invitations/{invitation_id}", {
        params: { path: { ...path, invitation_id: props.id! } },
        body: fields,
      })
    : await api.POST("/bff/manage/organizations/{id}/organization-invitations", {
        params: { path },
        body: { ...fields, email: email.value },
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
      :items="[
        {
          label: t('Organization invitations'),
          to: { name: 'organization-invitations', params: { organizationId } },
        },
        { label: title },
      ]"
    />

    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading">
      <form v-if="invitationForm" data-test="invitation-form" @submit.prevent="save">
        <div v-if="isUpdate" class="row mb-2" data-test="email-read">
          <div class="col-sm-3 fw-bold">{{ t("Email") }}</div>
          <div class="col-sm-9">{{ invitationForm.email }}</div>
        </div>
        <AuditLine v-if="isUpdate" :audit="invitationForm.audit" />

        <div v-if="!isUpdate" class="mb-3">
          <label class="form-label" for="email">{{ t("Email") }} *</label>
          <input
            id="email"
            v-model="email"
            type="email"
            class="form-control"
            :class="{ 'is-invalid': errors.email }"
            maxlength="255"
            required
          />
          <div class="form-text">{{ t("The invitation will be sent to this email address.") }}</div>
          <div v-if="errors.email" class="invalid-feedback d-block" data-test="email-error">
            {{ errors.email }}
          </div>
        </div>

        <div class="mb-3">
          <label class="form-label" for="admin_unit_name">{{ t("New organization's name") }} *</label>
          <input
            id="admin_unit_name"
            v-model="name"
            type="text"
            class="form-control"
            :class="{ 'is-invalid': errors.admin_unit_name }"
            maxlength="255"
            required
          />
          <div v-if="errors.admin_unit_name" class="invalid-feedback" data-test="name-error">
            {{ errors.admin_unit_name }}
          </div>
        </div>

        <div v-if="invitationForm.can_verify_other" class="mb-3">
          <label class="form-label d-block" for="relation_verify">{{
            t("Verify new organization")
          }}</label>
          <div class="form-text mt-0 mb-1">
            {{ t("If set, events of the new organization are publicly visible.") }}
          </div>
          <BFormCheckbox id="relation_verify" v-model="verify" switch />
        </div>

        <div class="mb-4">
          <label
            class="form-label d-block"
            for="relation_auto_verify_event_reference_requests"
            >{{ t("Verify reference requests automatically") }}</label
          >
          <div class="form-text mt-0 mb-1">
            {{
              t(
                "If set, all upcoming reference requests of the new organization are verified automatically.",
              )
            }}
          </div>
          <BFormCheckbox id="relation_auto_verify_event_reference_requests" v-model="autoVerify" switch />
        </div>

        <div v-if="saveError" class="alert alert-danger" role="alert">{{ saveError }}</div>

        <BButton id="submit" type="submit" variant="primary" :disabled="saving">
          <BSpinner v-if="saving" small />
          {{ isUpdate ? t("Update") : t("Create") }}
        </BButton>
      </form>
    </BOverlay>
  </div>
</template>
