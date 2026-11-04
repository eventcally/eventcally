<script setup lang="ts">
import { BOverlay } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { errorMessage } from "@/shared/apiError";
import AuditLine from "@/shared/AuditLine.vue";
import ConfirmModal from "@/shared/ConfirmModal.vue";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import ReadActions from "@/shared/ReadActions.vue";
import type { RowAction } from "@/shared/RowActions.vue";
import { useConfirmAction } from "@/shared/useConfirmAction";
import ReviewStatusBadge from "../components/ReviewStatusBadge.vue";

type Request = components["schemas"]["OutgoingVerificationRequestRead"];

const props = defineProps<{ organizationId: number; id: number }>();

const { t } = useI18n();

const request = ref<Request | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  const { data, error: err } = await api.GET(
    "/bff/manage/organizations/{id}/outgoing-verification-requests/{request_id}",
    { params: { path: { id: props.organizationId, request_id: props.id } } },
  );
  loading.value = false;

  if (data) request.value = data;
  else error.value = errorMessage(err, t("Error"));
});

const modelName = computed(() => t("Organization verification request"));
const objectTitle = computed(() => `${modelName.value} ${props.id}`);

// Withdrawing leaves the page: the server flashes the text for the list (a full page load,
// so the Flask frame shows the flash).
const listUrl = computed(
  () => `/manage/admin_unit/${props.organizationId}/outgoing_organization_verification_requests`,
);

const confirm = useConfirmAction<Request>({
  call: (item) =>
    api.POST("/bff/manage/organizations/{id}/outgoing-verification-requests/{request_id}/withdraw", {
      params: { path: { id: props.organizationId, request_id: item.id } },
      body: { inline: false },
    }),
  onDone: () => window.location.assign(listUrl.value),
});

const actions = computed<RowAction[]>(() =>
  request.value?.can_write
    ? [{ title: t("Delete"), onClick: () => request.value && confirm.open(request.value) }]
    : [],
);
</script>

<template>
  <div>
    <ManageBreadcrumb
      :organization-id="organizationId"
      :items="[
        {
          label: t('Outgoing verification requests'),
          to: { name: 'outgoing-verification-requests', params: { organizationId } },
        },
        { label: objectTitle },
      ]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <template v-if="request">
        <ReadActions :actions="actions" />

        <dl class="row">
          <dt class="col-sm-3 fw-bold">{{ t("Organization") }}</dt>
          <dd class="col-sm-9">{{ request.organization_name }}</dd>
          <dt class="col-sm-3 fw-bold">{{ t("Review status") }}</dt>
          <dd class="col-sm-9">
            <ReviewStatusBadge :status="request.review_status" :label="request.review_status_label" />
          </dd>
          <template v-if="request.rejection_reason_label">
            <dt class="col-sm-3 fw-bold">{{ t("Rejection reason") }}</dt>
            <dd class="col-sm-9">{{ request.rejection_reason_label }}</dd>
          </template>
        </dl>
        <AuditLine :audit="request.audit" />

        <ConfirmModal
          v-model="confirm.show.value"
          :title="t('Delete %(model_display_name)s', { model_display_name: modelName })"
          :confirm-title="t('Delete')"
          :instruction="t('Do you want to delete \'%(object_title)s\'?', { object_title: objectTitle })"
          :busy="confirm.busy.value"
          :error="confirm.error.value"
          @submit="confirm.submit"
        />
      </template>
    </BOverlay>
  </div>
</template>
