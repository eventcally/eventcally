<script setup lang="ts">
import { BButton, BOverlay, BSpinner } from "bootstrap-vue-next";
import { computed, nextTick, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import AppTypeahead from "@/shared/AppTypeahead.vue";
import { toFieldErrors } from "@/shared/fieldErrors";
import { manage } from "@/shared/legacy";

type RequestForm = components["schemas"]["EventReferenceRequestForm"];
type Ref = { id: number; name: string };

const props = defineProps<{ organizationId: number; eventId: number }>();

const { t } = useI18n();

const FIELDS = ["admin_unit_id"];

const loading = ref(true);
const loadError = ref<string | null>(null);
const saving = ref(false);
const saveError = ref<string | null>(null);
const requestForm = ref<RequestForm | null>(null);

const target = ref<Ref | null>(null);
const errors = ref<Record<string, string>>({});

const title = computed(() =>
  t("Create %(model_display_name)s", {
    model_display_name: t("Event reference request"),
  }),
);

async function load() {
  loading.value = true;
  const { data, error } = await api.GET(
    "/bff/manage/organizations/{id}/events/{event_id}/reference-request-form",
    { params: { path: { id: props.organizationId, event_id: props.eventId } } },
  );
  loading.value = false;

  if (!data) {
    loadError.value = error?.message ?? t("Error");
    return;
  }

  requestForm.value = data;
}

async function fetchOrganizations(keyword: string): Promise<Ref[]> {
  const { data } = await api.GET(
    "/bff/manage/organizations/{id}/events/{event_id}/reference-request-organizations",
    {
      params: {
        path: { id: props.organizationId, event_id: props.eventId },
        query: { keyword },
      },
    },
  );
  return data?.items ?? [];
}

async function scrollToFirstInvalid() {
  await nextTick();
  document.querySelector(".invalid-feedback")?.scrollIntoView({ block: "center" });
}

async function save() {
  if (saving.value || !requestForm.value) return;

  saving.value = true;
  saveError.value = null;
  errors.value = {};

  const { data, error } = await api.POST(
    "/bff/manage/organizations/{id}/events/{event_id}/reference-requests",
    {
      params: { path: { id: props.organizationId, event_id: props.eventId } },
      body: { admin_unit_id: target.value?.id ?? null },
    },
  );

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
    // E.g. the organization has already been asked for this event.
    saveError.value = error?.message ?? t("Error");
  }
}

onMounted(load);
</script>

<template>
  <div>
    <div v-if="saveError" class="alert alert-danger" role="alert" data-test="save-error">
      {{ saveError }}
    </div>

    <AppBreadcrumb
      :items="[
        {
          label: t('Outgoing reference requests'),
          href: manage.outgoingEventReferenceRequests(organizationId),
        },
        { label: title },
      ]"
    />

    <div v-if="loadError" class="alert alert-danger" role="alert">
      {{ loadError }}
    </div>

    <BOverlay :show="loading">
      <form v-if="requestForm" data-test="request-form" @submit.prevent="save">
        <p>
          {{ t("Ask another organization to reference your event on their calendar.") }}
        </p>

        <div class="mb-3">
          <label class="form-label" for="admin_unit">{{ t("Other organization") }} *</label>
          <AppTypeahead
            v-model="target"
            input-id="admin_unit"
            :fetch="fetchOrganizations"
            :placeholder="t('Other organization')"
          />
          <div
            v-if="errors.admin_unit_id"
            class="invalid-feedback d-block"
            data-test="target-error"
          >
            {{ errors.admin_unit_id }}
          </div>
        </div>

        <BButton id="submit" type="submit" variant="primary" :disabled="saving">
          <BSpinner v-if="saving" small />
          {{ t("Create") }}
        </BButton>
      </form>
    </BOverlay>
  </div>
</template>
