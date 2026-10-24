<script setup lang="ts">
import { BButton, BFormCheckbox, BOverlay, BSpinner } from "bootstrap-vue-next";
import { computed, nextTick, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import AppTypeahead from "@/shared/AppTypeahead.vue";
import { toFieldErrors } from "@/shared/fieldErrors";
import { manage } from "@/shared/legacy";

type RelationForm = components["schemas"]["OrganizationRelationForm"];
type Ref = { id: number; name: string };

const props = defineProps<{ organizationId: number; id?: number }>();

const { t } = useI18n();

const FIELDS = ["target_admin_unit_id"];

const loading = ref(true);
const loadError = ref<string | null>(null);
const saving = ref(false);
const saveError = ref<string | null>(null);
const relationForm = ref<RelationForm | null>(null);

const target = ref<Ref | null>(null);
const verify = ref(false);
const autoVerify = ref(false);
const errors = ref<Record<string, string>>({});

const isUpdate = computed(() => props.id !== undefined);
const title = computed(() =>
  t(isUpdate.value ? "Update %(model_display_name)s" : "Create %(model_display_name)s", {
    model_display_name: t("Outgoing organization relation"),
  }),
);

function intParam(name: string): number | undefined {
  const value = Number(new URLSearchParams(location.search).get(name));
  return Number.isInteger(value) && value > 0 ? value : undefined;
}

async function load() {
  loading.value = true;
  const path = { id: props.organizationId };
  // The create form is prefilled from `?target=<id>&verify=1` (e.g. from the organization page).
  const { data, error } = isUpdate.value
    ? await api.GET(
        "/bff/manage/organizations/{id}/outgoing-organization-relations/{relation_id}",
        {
          params: { path: { ...path, relation_id: props.id! } },
        },
      )
    : await api.GET("/bff/manage/organizations/{id}/outgoing-organization-relations/create-form", {
        params: {
          path,
          query: { target: intParam("target"), verify: intParam("verify") },
        },
      });
  loading.value = false;

  if (!data) {
    loadError.value = error?.message ?? t("Error");
    return;
  }

  relationForm.value = data;
  target.value = data.target ?? null;
  verify.value = data.verify;
  autoVerify.value = data.auto_verify_event_reference_requests;
}

async function fetchOrganizations(keyword: string): Promise<Ref[]> {
  const { data } = await api.GET(
    "/bff/manage/organizations/{id}/outgoing-organization-relations/organizations",
    { params: { path: { id: props.organizationId }, query: { keyword } } },
  );
  return data?.items ?? [];
}

async function scrollToFirstInvalid() {
  await nextTick();
  document.querySelector(".is-invalid, .invalid-feedback")?.scrollIntoView({ block: "center" });
}

async function save() {
  if (saving.value || !relationForm.value) return;

  saving.value = true;
  saveError.value = null;
  errors.value = {};

  const path = { id: props.organizationId };
  const flags = {
    verify: verify.value,
    auto_verify_event_reference_requests: autoVerify.value,
  };
  const { data, error } = isUpdate.value
    ? await api.PUT(
        "/bff/manage/organizations/{id}/outgoing-organization-relations/{relation_id}",
        {
          params: { path: { ...path, relation_id: props.id! } },
          body: flags,
        },
      )
    : await api.POST("/bff/manage/organizations/{id}/outgoing-organization-relations", {
        params: { path },
        body: { ...flags, target_admin_unit_id: target.value?.id ?? null },
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
          label: t('Outgoing organization relations'),
          href: manage.outgoingOrganizationRelations(organizationId),
        },
        { label: title },
      ]"
    />

    <div v-if="loadError" class="alert alert-danger" role="alert">
      {{ loadError }}
    </div>

    <BOverlay :show="loading">
      <form v-if="relationForm" data-test="relation-form" @submit.prevent="save">
        <div v-if="isUpdate" class="row mb-4" data-test="target-name">
          <div class="col-sm-3 fw-bold">{{ t("Organization") }}</div>
          <div class="col-sm-9">{{ target?.name }}</div>
        </div>
        <div v-else class="mb-3">
          <label class="form-label" for="target_admin_unit">{{ t("Other organization") }} *</label>
          <AppTypeahead
            v-model="target"
            input-id="target_admin_unit"
            :fetch="fetchOrganizations"
            :placeholder="t('Other organization')"
          />
          <div
            v-if="errors.target_admin_unit_id"
            class="invalid-feedback d-block"
            data-test="target-error"
          >
            {{ errors.target_admin_unit_id }}
          </div>
        </div>

        <div v-if="relationForm.can_verify_other" class="mb-3">
          <label class="form-label d-block" for="verify">{{
            t("Verify other organization")
          }}</label>
          <div class="form-text mt-0 mb-1">
            {{ t("If set, events of the other organization are publicly visible.") }}
          </div>
          <BFormCheckbox id="verify" v-model="verify" switch />
        </div>

        <div class="mb-4">
          <label class="form-label d-block" for="auto_verify_event_reference_requests">
            {{ t("Verify reference requests automatically") }}
          </label>
          <div class="form-text mt-0 mb-1">
            {{
              t(
                "If set, all upcoming reference requests of the other organization are verified automatically.",
              )
            }}
          </div>
          <BFormCheckbox id="auto_verify_event_reference_requests" v-model="autoVerify" switch />
        </div>

        <div v-if="saveError" class="alert alert-danger" role="alert">
          {{ saveError }}
        </div>

        <BButton id="submit" type="submit" variant="primary" :disabled="saving">
          <BSpinner v-if="saving" small />
          {{ isUpdate ? t("Update") : t("Create") }}
        </BButton>
      </form>
    </BOverlay>
  </div>
</template>
