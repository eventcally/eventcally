<script setup lang="ts">
import { BOverlay } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { errorMessage } from "@/shared/apiError";
import AuditLine from "@/shared/AuditLine.vue";
import { publicPages } from "@/shared/legacy";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import ReviewStatusBadge from "../components/ReviewStatusBadge.vue";

type Request = components["schemas"]["OutgoingEventReferenceRequestRead"];

const props = defineProps<{ organizationId: number; id: number }>();

const { t } = useI18n();

const request = ref<Request | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  const { data, error: err } = await api.GET(
    "/bff/manage/organizations/{id}/outgoing-event-reference-requests/{request_id}",
    { params: { path: { id: props.organizationId, request_id: props.id } } },
  );
  loading.value = false;

  if (data) request.value = data;
  else error.value = errorMessage(err, t("Error"));
});

const objectTitle = computed(() => `${t("Event reference request")} ${props.id}`);
</script>

<template>
  <div>
    <ManageBreadcrumb
      :organization-id="organizationId"
      :items="[
        {
          label: t('Outgoing reference requests'),
          to: { name: 'outgoing-event-reference-requests', params: { organizationId } },
        },
        { label: objectTitle },
      ]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <template v-if="request">
        <dl class="row">
          <dt class="col-sm-3 fw-bold">{{ t("Event") }}</dt>
          <dd class="col-sm-9">
            <a :href="publicPages.event(request.event_id)">{{ request.event_name }}</a>
          </dd>
          <dt class="col-sm-3 fw-bold">{{ t("Review status") }}</dt>
          <dd class="col-sm-9">
            <ReviewStatusBadge :status="request.review_status" :label="request.review_status_label" />
          </dd>
          <template v-if="request.rejection_reason_label">
            <dt class="col-sm-3 fw-bold">{{ t("Rejection reason") }}</dt>
            <dd class="col-sm-9">{{ request.rejection_reason_label }}</dd>
          </template>
          <dt class="col-sm-3 fw-bold">{{ t("Organization") }}</dt>
          <dd class="col-sm-9">{{ request.organization_name }}</dd>
        </dl>
        <AuditLine :audit="request.audit" />
      </template>
    </BOverlay>
  </div>
</template>
