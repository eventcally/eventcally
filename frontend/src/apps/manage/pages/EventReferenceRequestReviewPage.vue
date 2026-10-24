<script setup lang="ts">
import { BFormCheckbox, BOverlay } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import { manage } from "@/shared/legacy";
import ReviewDecisionBar from "../components/ReviewDecisionBar.vue";
import ReviewEventCards from "../components/ReviewEventCards.vue";

type Review = components["schemas"]["EventReferenceRequestReview"];

const props = defineProps<{ organizationId: number; id: number }>();

const { t } = useI18n();

const loading = ref(true);
const loadError = ref<string | null>(null);
const busy = ref(false);
const error = ref<string | null>(null);
const review = ref<Review | null>(null);
const rating = ref(50);
const autoVerify = ref(false);

const title = computed(() =>
  t("Review %(model_display_name)s", { model_display_name: t("Event reference request") }),
);

async function load() {
  loading.value = true;
  loadError.value = null;
  const { data, error: err } = await api.GET(
    "/bff/manage/organizations/{id}/incoming-event-reference-requests/{request_id}/review",
    { params: { path: { id: props.organizationId, request_id: props.id } } },
  );
  if (data) {
    review.value = data;
    rating.value = data.default_rating;
  } else {
    loadError.value = err?.message ?? t("Error");
  }
  loading.value = false;
}

async function decide(result: Promise<{ data?: { redirect_url: string }; error?: { message?: string } }>) {
  busy.value = true;
  error.value = null;
  const { data, error: err } = await result;
  if (data) {
    // The server flashed the success message; the list renders it. Keep the spinner.
    location.assign(data.redirect_url);
    return;
  }
  busy.value = false;
  error.value = err?.message ?? t("Error");
}

const path = () => ({ id: props.organizationId, request_id: props.id });

const accept = () =>
  decide(
    api.POST("/bff/manage/organizations/{id}/incoming-event-reference-requests/{request_id}/verify", {
      params: { path: path() },
      body: { rating: rating.value, auto_verify: autoVerify.value },
    }),
  );

const reject = (reason: number | null) =>
  decide(
    api.POST("/bff/manage/organizations/{id}/incoming-event-reference-requests/{request_id}/reject", {
      params: { path: path() },
      body: { rejection_reason: reason },
    }),
  );

onMounted(load);
</script>

<template>
  <div>
    <AppBreadcrumb
      :items="[
        { label: t('Incoming reference requests'), href: manage.incomingEventReferenceRequests(organizationId) },
        { label: title },
      ]"
    />

    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading || busy">
      <div v-if="review" class="mt-3 w-normal" data-test="review">
        <ReviewEventCards :event="review.event" :dates="review.dates" />

        <ReviewDecisionBar
          :accept-label="t('Accept reference request')"
          :reject-label="t('Reject reference request')"
          :rejection-reasons="review.rejection_reasons"
          :busy="busy"
          :error="error"
          @accept="accept"
          @reject="reject"
          @reset="error = null"
        >
          <template #accept-fields>
            <div v-if="review.rating_choices.length > 1" class="mb-3">
              <label class="form-label" for="rating">{{ t("Rating") }}</label>
              <div class="text-body-secondary mb-1">
                {{
                  t(
                    "Choose how relevant the event is to your organization. The value is not visible and is used for sorting.",
                  )
                }}
              </div>
              <select id="rating" v-model.number="rating" class="form-select">
                <option v-for="choice in review.rating_choices" :key="choice.value" :value="choice.value">
                  {{ choice.label }}
                </option>
              </select>
            </div>

            <div v-if="!review.auto_verify" class="mb-3">
              <label class="form-label" for="auto_verify">{{
                t("Verify reference requests automatically")
              }}</label>
              <div class="text-body-secondary mb-1">{{ review.auto_verify_description }}</div>
              <BFormCheckbox id="auto_verify" v-model="autoVerify" switch />
            </div>
          </template>
        </ReviewDecisionBar>
      </div>
    </BOverlay>
  </div>
</template>
