<script setup lang="ts">
import { BButton, BOverlay, BSpinner } from "bootstrap-vue-next";
import { nextTick, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import { toFieldErrors } from "@/shared/fieldErrors";
import RoleCheckboxes from "../components/RoleCheckboxes.vue";

type InvitationForm = components["schemas"]["MemberInvitationForm"];

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();

const FIELDS = ["email", "roles"];

const loading = ref(true);
const loadError = ref<string | null>(null);
const saving = ref(false);
const saveError = ref<string | null>(null);
const invitationForm = ref<InvitationForm | null>(null);

const email = ref("");
const roles = ref<string[]>([]);
const errors = ref<Record<string, string>>({});

async function load() {
  loading.value = true;
  const { data, error } = await api.GET(
    "/bff/manage/organizations/{id}/member-invitations/create-form",
    { params: { path: { id: props.organizationId } } },
  );
  loading.value = false;

  if (!data) {
    loadError.value = error?.message ?? t("Error");
    return;
  }

  invitationForm.value = data;
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

  const { data, error } = await api.POST("/bff/manage/organizations/{id}/member-invitations", {
    params: { path: { id: props.organizationId } },
    body: { email: email.value, roles: roles.value },
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
          label: t('Organization member invitations'),
          to: { name: 'organization-member-invitations', params: { organizationId } },
        },
        {
          label: t('Create %(model_display_name)s', {
            model_display_name: t('Organization member invitation'),
          }),
        },
      ]"
    />

    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading">
      <form v-if="invitationForm" data-test="invitation-form" @submit.prevent="save">
        <div class="mb-3">
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
          <div v-if="errors.email" class="invalid-feedback" data-test="email-error">
            {{ errors.email }}
          </div>
        </div>

        <RoleCheckboxes v-model="roles" :choices="invitationForm.role_choices" :error="errors.roles" />

        <div v-if="saveError" class="alert alert-danger" role="alert">{{ saveError }}</div>

        <BButton id="submit" type="submit" variant="primary" class="mt-4" :disabled="saving">
          <BSpinner v-if="saving" small />
          {{ t("Create") }}
        </BButton>
      </form>
    </BOverlay>
  </div>
</template>
