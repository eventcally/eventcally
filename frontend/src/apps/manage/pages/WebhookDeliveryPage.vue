<script setup lang="ts">
import { BButton, BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { errorMessage } from "@/shared/apiError";
import AppPager from "@/shared/AppPager.vue";
import { boot } from "@/shared/boot";
import { formatDateTime } from "@/shared/format";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import { useNotify } from "@/shared/notify";
import ReadProps from "@/shared/ReadProps.vue";
import { usePagedList } from "@/shared/usePagedList";

type Delivery = components["schemas"]["WebhookDeliveryRead"];
type Attempts = components["schemas"]["WebhookDeliveryAttemptListPage"];

const props = defineProps<{ organizationId: number; appId: number; id: number }>();

const { t } = useI18n();
const notify = useNotify();

const path = computed(() => ({
  id: props.organizationId,
  app_id: props.appId,
  delivery_id: props.id,
}));

const delivery = ref<Delivery | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  const { data, error: err } = await api.GET(
    "/bff/manage/organizations/{id}/apps/{app_id}/webhook-deliveries/{delivery_id}",
    { params: { path: path.value } },
  );
  loading.value = false;

  if (data) delivery.value = data;
  else error.value = errorMessage(err, t("Error"));
});

// The attempts section: the list answer carries every attempt field, so a row needs no page.
const {
  page: attempts,
  loading: attemptsLoading,
  error: attemptsError,
  currentPage,
  load: loadAttempts,
} = usePagedList<Attempts>(
  (current) =>
    api.GET(
      "/bff/manage/organizations/{id}/apps/{app_id}/webhook-deliveries/{delivery_id}/attempts",
      { params: { path: path.value, query: { page: current } } },
    ),
  "webhook-delivery",
  t("Error"),
);

const delivering = ref(false);

async function deliverAgain() {
  if (delivering.value) return;
  delivering.value = true;

  const { data, error: err } = await api.POST(
    "/bff/manage/organizations/{id}/apps/{app_id}/webhook-deliveries/{delivery_id}/attempts",
    { params: { path: path.value } },
  );
  delivering.value = false;

  if (!data) {
    notify.error(errorMessage(err, t("Error")));
    return;
  }

  notify.success(data.message);
  await loadAttempts();
}

const title = computed(() => `${t("Webhook delivery")} ${props.id}`);

const fields = computed<TableFieldRaw[]>(() => [
  { key: "id", label: t("ID") },
  { key: "start_at", label: t("Start at") },
  { key: "end_at", label: t("End at") },
  { key: "url", label: t("URL") },
  { key: "status", label: t("Status") },
  { key: "status_code", label: t("Status code") },
]);
</script>

<template>
  <div>
    <ManageBreadcrumb
      :organization-id="organizationId"
      :items="[
        { label: t('Apps'), to: { name: 'apps', params: { organizationId } } },
        {
          label: delivery?.app_title ?? '…',
          to: { name: 'app', params: { organizationId, id: appId } },
        },
        {
          label: t('Webhook deliveries'),
          to: { name: 'webhook-deliveries', params: { organizationId, appId } },
        },
        { label: title },
      ]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <template v-if="delivery">
        <ReadProps
          :rows="[
            { label: t('Event Type'), value: delivery.event_type },
            { label: t('Timestamp'), value: formatDateTime(delivery.timestamp, boot.locale) },
            { label: t('Organization'), value: delivery.organization },
          ]"
        />

        <section class="mt-4" data-test="attempts">
          <h2 class="h5">{{ t("Webhook delivery attempts") }}</h2>

          <div v-if="delivery.can_attempt" class="my-3">
            <BButton
              variant="outline-secondary"
              :disabled="delivering"
              data-test="deliver-again"
              @click="deliverAgain"
            >
              <i class="fa fa-plus"></i>
              {{
                t("Create %(model_display_name)s", {
                  model_display_name: t("Webhook delivery attempt"),
                })
              }}
            </BButton>
          </div>

          <div v-if="attemptsError" class="alert alert-danger" role="alert">{{ attemptsError }}</div>

          <BOverlay :show="attemptsLoading">
            <BTable
              v-if="attempts && attempts.items.length"
              :items="attempts.items"
              :fields="fields"
              thead-class="fw-bold"
              responsive
              small
              striped
              bordered
              hover
            >
              <template #cell(start_at)="{ item }">{{
                formatDateTime(item.start_at, boot.locale)
              }}</template>
              <template #cell(end_at)="{ item }">{{
                formatDateTime(item.end_at, boot.locale)
              }}</template>
            </BTable>
          </BOverlay>

          <AppPager
            v-if="attempts && attempts.total > 0"
            v-model:page="currentPage"
            :pages="attempts.pages"
            :total="attempts.total"
          />
        </section>
      </template>
    </BOverlay>
  </div>
</template>
