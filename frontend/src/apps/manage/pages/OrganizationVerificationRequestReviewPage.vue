<script setup lang="ts">
import { BFormCheckbox, BOverlay } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import { manage } from "@/shared/legacy";
import ContactLines from "../components/ContactLines.vue";
import ReviewDecisionBar from "../components/ReviewDecisionBar.vue";

type Review = components["schemas"]["OrganizationVerificationRequestReview"];

const props = defineProps<{ organizationId: number; id: number }>();

const { t } = useI18n();

const loading = ref(true);
const loadError = ref<string | null>(null);
const busy = ref(false);
const error = ref<string | null>(null);
const review = ref<Review | null>(null);
const autoVerify = ref(false);

const title = computed(() =>
  t("Review %(model_display_name)s", {
    model_display_name: t("Organization verification request"),
  }),
);

async function load() {
  loading.value = true;
  loadError.value = null;
  const { data, error: err } = await api.GET(
    "/bff/manage/organizations/{id}/incoming-verification-requests/{request_id}/review",
    { params: { path: { id: props.organizationId, request_id: props.id } } },
  );
  if (data) review.value = data;
  else loadError.value = err?.message ?? t("Error");
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
    api.POST("/bff/manage/organizations/{id}/incoming-verification-requests/{request_id}/approve", {
      params: { path: path() },
      body: { auto_verify: autoVerify.value },
    }),
  );

const reject = (reason: number | null) =>
  decide(
    api.POST("/bff/manage/organizations/{id}/incoming-verification-requests/{request_id}/reject", {
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
        {
          label: t('Incoming verification requests'),
          href: manage.incomingVerificationRequests(organizationId),
        },
        { label: title },
      ]"
    />

    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading || busy">
      <div v-if="review" class="mt-3 w-normal" data-test="review">
        <div class="card mb-3" data-test="organization-card">
          <div class="card-header">{{ t("Organization") }}</div>
          <div class="card-body">
            <h5 class="card-title">
              {{ review.organization.name }}
              <i
                v-if="review.organization.is_verified"
                class="fa fa-check-circle text-primary"
                :title="t('Verified')"
              ></i>
            </h5>

            <div v-if="review.organization.logo_url" class="my-4">
              <img
                :src="review.organization.logo_url"
                class="img-fluid"
                style="max-width: 120px"
                alt="Logo"
              />
            </div>

            <div class="my-4">
              <ContactLines
                :url="review.organization.url"
                :email="review.organization.email"
                :phone="review.organization.phone"
                :fax="review.organization.fax"
                :address="review.organization.address"
              />
              <div v-if="review.organization.description" class="my-2" style="white-space: pre-wrap">
                {{ review.organization.description }}
              </div>
            </div>
          </div>
        </div>

        <div class="card mb-3" data-test="members-card">
          <div class="card-header">{{ t("Members") }}</div>
          <ul class="list-group list-group-flush">
            <li v-for="member in review.members" :key="member.email" class="list-group-item">
              <span>{{ member.email }}</span>
              <small class="text-secondary ms-1">{{ member.roles.join(", ") }}</small>
            </li>
          </ul>
        </div>

        <ReviewDecisionBar
          :accept-label="t('Accept verification request')"
          :reject-label="t('Reject verification request')"
          :rejection-reasons="review.rejection_reasons"
          :busy="busy"
          :error="error"
          @accept="accept"
          @reject="reject"
          @reset="error = null"
        >
          <template #accept-fields>
            <div class="mb-3">
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
