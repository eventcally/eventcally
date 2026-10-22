<script setup lang="ts">
import { BOverlay } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import IcalExportModal from "@/shared/IcalExportModal.vue";
import { publicPages } from "@/shared/legacy";

type PublicOrganization = components["schemas"]["PublicOrganization"];

const props = defineProps<{ id: number }>();

const { t } = useI18n();

const organization = ref<PublicOrganization | null>(null);
const loading = ref(false);
const loadError = ref<string | null>(null);
const icalVisible = ref(false);

const address = computed(() => {
  const l = organization.value?.location;
  if (!l) return null;
  const city = [l.postal_code, l.city].filter(Boolean).join(" ");
  return [l.street, city].filter(Boolean).join(", ");
});

async function load() {
  loading.value = true;
  loadError.value = null;
  const { data, error } = await api.GET("/bff/public/organizations/{id}", {
    params: { path: { id: props.id } },
  });
  if (data) organization.value = data;
  else loadError.value = error?.message ?? t("Error");
  loading.value = false;
}

onMounted(load);
</script>

<template>
  <div>
    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading">
      <div v-if="organization" class="row mb-5">
        <div v-if="organization.logo_url" class="col-12 col-sm-auto mb-3">
          <img
            :src="organization.logo_url"
            class="img-fluid"
            style="max-width: 120px"
            alt="Logo"
          />
        </div>
        <div class="col-12 col-sm">
          <h1 class="my-0">
            {{ organization.name }}
            <i v-if="organization.is_verified" class="fa fa-check-circle text-primary"></i>
          </h1>
          <div v-if="organization.short_name" class="mb-3 text-muted">
            @{{ organization.short_name }}
          </div>

          <div v-if="organization.url">
            <i class="fa fa-fw me-2 fa-link"></i>
            <a class="text-decoration-none" :href="organization.url" target="_blank" rel="noopener noreferrer" style="word-break: break-all">{{
              organization.url
            }}</a>
          </div>

          <div v-if="organization.email">
            <i class="fa fa-fw me-2 fa-envelope"></i>
            <a class="text-decoration-none" :href="`mailto:${organization.email}`">{{ organization.email }}</a>
          </div>

          <div v-if="organization.phone">
            <i class="fa fa-fw me-2 fa-phone"></i>
            <a class="text-decoration-none" :href="`tel:${organization.phone}`">{{ organization.phone }}</a>
          </div>

          <div v-if="organization.fax">
            <i class="fa fa-fw me-2 fa-fax"></i>
            {{ organization.fax }}
          </div>

          <div v-if="address">
            <i class="fa fa-fw me-2 fa-map-marker"></i>
            {{ address }}
          </div>

          <div v-if="organization.description" class="mt-3">
            <span style="white-space: pre-wrap">{{ organization.description }}</span>
          </div>

          <div v-if="organization.relation" class="mt-3" data-testid="relation">
            <div v-if="organization.relation.relation_id" class="card">
              <div class="card-body">
                <div v-if="organization.relation.verify">
                  <i class="fa fa-fw fa-check-circle"></i>
                  {{
                    t("%(source)s verifies %(target)s", {
                      source: organization.relation.source.name,
                      target: organization.name,
                    })
                  }}
                </div>
                <div v-if="organization.relation.auto_verify_event_reference_requests">
                  <i class="fa fa-fw fa-check-circle"></i>
                  {{
                    t("%(source)s verifies reference requests from %(target)s automatically", {
                      source: organization.relation.source.name,
                      target: organization.name,
                    })
                  }}
                </div>
                <a :href="organization.relation.edit_url ?? undefined">{{ t("Edit relation") }}</a>
              </div>
            </div>

            <div v-else-if="organization.is_verified" class="card">
              <div class="card-body">
                <p class="card-text">
                  {{
                    t("There is no relation from %(source)s to %(target)s", {
                      source: organization.relation.source.name,
                      target: organization.name,
                    })
                  }}
                </p>
                <a :href="organization.relation.create_url ?? undefined">{{ t("Create relation") }}</a>
              </div>
            </div>

            <div v-else class="card border-warning">
              <div class="card-body">
                <p class="card-text">
                  {{ t("%(organization)s is not verified", { organization: organization.name }) }}
                </p>
                <a :href="organization.relation.create_url ?? undefined">{{
                  t("Verify %(organization)s", { organization: organization.name })
                }}</a>
              </div>
            </div>
          </div>

          <div class="list-group mt-4">
            <a class="list-group-item list-group-item-action" :href="publicPages.organizationEventDates(organization.id)">
              <i class="fa fa-fw me-2 fa-list"></i>
              {{ t("Events") }}
            </a>
            <button
              type="button"
              class="list-group-item list-group-item-action"
              @click="icalVisible = true"
            >
              <i class="fa fa-fw me-2 fa-calendar"></i>
              {{ t("iCal calendar") }}
            </button>
          </div>

          <IcalExportModal v-model="icalVisible" :url="organization.ical_url" />
        </div>
      </div>
    </BOverlay>
  </div>
</template>
