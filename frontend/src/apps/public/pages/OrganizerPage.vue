<script setup lang="ts">
import { BOverlay } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import IcalExportModal from "@/shared/IcalExportModal.vue";
import { publicPages } from "@/shared/legacy";

type PublicOrganizer = components["schemas"]["PublicOrganizer"];

const props = defineProps<{ id: number }>();

const { t } = useI18n();

const organizer = ref<PublicOrganizer | null>(null);
const loading = ref(false);
const loadError = ref<string | null>(null);
const icalVisible = ref(false);

const address = computed(() => {
  const l = organizer.value?.location;
  if (!l) return null;
  const city = [l.postal_code, l.city].filter(Boolean).join(" ");
  return [l.street, city].filter(Boolean).join(", ");
});

async function load() {
  loading.value = true;
  loadError.value = null;
  const { data, error } = await api.GET("/bff/public/organizers/{id}", {
    params: { path: { id: props.id } },
  });
  if (data) organizer.value = data;
  else loadError.value = error?.message ?? t("Error");
  loading.value = false;
}

onMounted(load);
</script>

<template>
  <div>
    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading">
      <div v-if="organizer" class="row mb-5">
        <div v-if="organizer.logo_url" class="col-12 col-sm-auto mb-3">
          <img
            :src="organizer.logo_url"
            class="img-fluid"
            style="max-width: 120px"
            alt="Logo"
          />
        </div>
        <div class="col-12 col-sm">
          <h1 class="my-0">{{ organizer.name }}</h1>

          <div v-if="organizer.url">
            <i class="fa fa-fw me-2 fa-link"></i>
            <a class="text-decoration-none" :href="organizer.url" target="_blank" rel="noopener noreferrer" style="word-break: break-all">{{
              organizer.url
            }}</a>
          </div>

          <div v-if="organizer.email">
            <i class="fa fa-fw me-2 fa-envelope"></i>
            <a class="text-decoration-none" :href="`mailto:${organizer.email}`">{{ organizer.email }}</a>
          </div>

          <div v-if="organizer.phone">
            <i class="fa fa-fw me-2 fa-phone"></i>
            <a class="text-decoration-none" :href="`tel:${organizer.phone}`">{{ organizer.phone }}</a>
          </div>

          <div v-if="organizer.fax">
            <i class="fa fa-fw me-2 fa-fax"></i>
            {{ organizer.fax }}
          </div>

          <div v-if="address">
            <i class="fa fa-fw me-2 fa-map-marker"></i>
            {{ address }}
          </div>

          <div>
            <a class="text-decoration-none" :href="publicPages.organization(organizer.organization.id)">{{
              organizer.organization.name
            }}</a>
          </div>

          <div class="list-group mt-4">
            <a class="list-group-item list-group-item-action" :href="publicPages.eventDates(organizer.id)">
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

          <IcalExportModal v-model="icalVisible" :url="organizer.ical_url" />
        </div>
      </div>
    </BOverlay>
  </div>
</template>
