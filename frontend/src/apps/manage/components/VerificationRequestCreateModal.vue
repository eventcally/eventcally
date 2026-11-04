<script setup lang="ts">
import { BModal, BOverlay } from "bootstrap-vue-next";
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { errorMessage } from "@/shared/apiError";
import AppPager from "@/shared/AppPager.vue";
import { publicPages } from "@/shared/legacy";
import { useNotify } from "@/shared/notify";

type Page = components["schemas"]["VerifierOrganizationListPage"];
type Verifier = Page["items"][number];

// The two old pages "select a verifier" and "confirm the request" as the two steps of
// one modal on the outgoing verification requests list.
const props = defineProps<{ organizationId: number }>();
const show = defineModel<boolean>({ default: false });
const emit = defineEmits<{ created: [] }>();

const { t } = useI18n();
const notify = useNotify();

const page = ref<Page | null>(null);
const pageNumber = ref(1);
const loading = ref(false);
const busy = ref(false);
const error = ref<string | null>(null);
const target = ref<Verifier | null>(null);

async function load() {
  loading.value = true;
  error.value = null;
  const { data, error: err } = await api.GET(
    "/bff/manage/organizations/{id}/verifier-organizations",
    {
      params: {
        path: { id: props.organizationId },
        query: { page: pageNumber.value },
      },
    },
  );
  loading.value = false;

  if (data) page.value = data;
  else error.value = errorMessage(err, t("Error"));
}

// Every opening starts at the first page of verifiers.
watch(show, (open) => {
  if (!open) return;
  target.value = null;
  pageNumber.value = 1;
  load();
});

watch(pageNumber, () => show.value && load());

const title = computed(() =>
  target.value
    ? t('Request verification for organization "%(name)s"', {
        name: page.value?.organization_name ?? "",
      })
    : t("Verification requests"),
);

async function request() {
  if (busy.value || !target.value) return;
  busy.value = true;
  error.value = null;

  const { data, error: err } = await api.POST(
    "/bff/manage/organizations/{id}/outgoing-verification-requests",
    {
      params: { path: { id: props.organizationId } },
      body: { target_id: target.value.id },
    },
  );
  busy.value = false;

  if (!data) {
    error.value = errorMessage(err, t("Error"));
    return;
  }

  notify.success(data.message);
  show.value = false;
  emit("created");
}
</script>

<template>
  <BModal v-model="show" :title="title" size="lg" scrollable no-footer>
    <template v-if="show">
      <div
        v-if="error"
        class="alert alert-danger"
        role="alert"
        data-test="verification-error"
      >
        {{ error }}
      </div>

      <template v-if="target">
        <p>
          {{
            t('Ask "%(name)s" to verify your organization.', {
              name: target.name,
            })
          }}
        </p>
        <div class="card mb-3" data-test="verifier-card">
          <div class="card-body p-3">
            <h2 class="h5 mt-0">
              <a
                :href="publicPages.organization(target.id)"
                class="text-body text-decoration-none"
                >{{ target.name }}</a
              >
              <i
                v-if="target.is_verified"
                class="fa fa-check-circle text-primary ms-1"
                :title="t('Verified')"
              ></i>
            </h2>
            <div v-if="target.location">
              <i class="fa fa-fw fa-map-marker-alt"></i> {{ target.location }}
            </div>
            <p v-if="target.description" class="mb-2">
              {{ target.description }}
            </p>
            <p v-if="target.incoming_verification_requests_text" class="mb-0">
              {{ target.incoming_verification_requests_text }}
            </p>
          </div>
        </div>
        <button
          type="button"
          class="btn btn-primary me-2"
          data-test="verification-submit"
          :disabled="busy"
          @click="request"
        >
          {{ t("Request verification") }}
        </button>
        <button
          type="button"
          class="btn btn-outline-secondary"
          :disabled="busy"
          @click="target = null"
        >
          {{ t("Cancel") }}
        </button>
      </template>

      <BOverlay v-else :show="loading">
        <p class="text-muted">
          {{
            t(
              "Here you can find organizations that can verify other organizations.",
            )
          }}
        </p>

        <template v-if="page">
          <div
            v-for="verifier in page.items"
            :key="verifier.id"
            class="card mb-3"
            data-test="verifier-card"
          >
            <div class="card-body p-3">
              <div class="row">
                <div
                  v-if="verifier.logo_url"
                  class="col-12 col-sm-auto order-sm-last mb-2"
                >
                  <img
                    :src="verifier.logo_url"
                    alt="Logo"
                    style="max-width: 120px"
                  />
                </div>
                <div class="col-12 col-sm">
                  <h2 class="h5 mt-0">
                    <a
                      :href="publicPages.organization(verifier.id)"
                      class="text-body text-decoration-none"
                      >{{ verifier.name }}</a
                    >
                    <i
                      v-if="verifier.is_verified"
                      class="fa fa-check-circle text-primary ms-1"
                      :title="t('Verified')"
                    ></i>
                  </h2>
                  <div v-if="verifier.location">
                    <i class="fa fa-fw fa-map-marker-alt"></i>
                    {{ verifier.location }}
                  </div>
                  <p v-if="verifier.description" class="mb-2">
                    {{ verifier.description }}
                  </p>
                  <p
                    v-if="verifier.incoming_verification_requests_text"
                    class="mb-2"
                  >
                    {{ verifier.incoming_verification_requests_text }}
                  </p>
                  <button
                    type="button"
                    class="btn btn-primary btn-sm mt-2"
                    data-test="verifier-select"
                    :disabled="!verifier.can_request"
                    @click="target = verifier"
                  >
                    <i class="fa fa-plus"></i>
                    {{ t("Request verification") }}&hellip;
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div
            v-if="page.items.length === 0"
            class="alert alert-warning"
            role="alert"
          >
            {{
              t(
                "No organizations were found that can verify your organization with postal code %(postal_code)s.",
                { postal_code: page.postal_code ?? "" },
              )
            }}
          </div>

          <AppPager
            v-if="page.total > 0"
            v-model:page="pageNumber"
            :pages="page.pages"
            :total="page.total"
          />
        </template>
      </BOverlay>
    </template>
  </BModal>
</template>
